# CAPI && CAPV Controller를 통한 VKS Cluster 생성 과정

VMware VKS(vSphere Kubernetes Service, 구 TKGS/Tanzu Kubernetes Grid Service)에서
워크로드 클러스터가 생성될 때 내부적으로 어떤 컨트롤러들이 동작하는지 정리합니다.
Supervisor 배포 후 워크로드 클러스터를 생성할 때 내부에서 일어나는 동작 원리에 해당합니다.

관련 매니페스트는 `manifests/cluster/` 디렉토리를 참조하세요.

---

## 1. 개념 정리

### 1-1. Cluster API (CAPI)

Cluster API는 **쿠버네티스로 쿠버네티스 클러스터를 관리**하는 선언적 클러스터
라이프사이클 관리 프로젝트입니다. Management Cluster(VKS에서는 Supervisor Cluster)에
CRD와 컨트롤러가 설치되고, 워크로드 클러스터를 리소스로 선언하면 컨트롤러가
실제 인프라를 조정(Reconcile)합니다.

| CAPI 리소스 | 역할 |
|---|---|
| Cluster | 클러스터 전체의 논리적 표현 (네트워크 CIDR, 토폴로지 등) |
| KubeadmControlPlane (KCP) | Control Plane 노드 수/버전 관리, kubeadm init/join 오케스트레이션 |
| MachineDeployment | Worker 노드 그룹 (Deployment처럼 롤링 업데이트 지원) |
| MachineSet | MachineDeployment의 특정 버전 스냅샷 (ReplicaSet에 대응) |
| Machine | 노드 1대의 논리적 표현 (Pod에 대응) |
| KubeadmConfig | 노드 부트스트랩용 cloud-init 데이터 생성 |

### 1-2. CAPV (Cluster API Provider vSphere)

CAPI는 인프라 중립적이므로, 실제 VM 생성은 **Infrastructure Provider**가 담당합니다.
vSphere 환경의 Provider가 CAPV이며, CAPI의 논리 리소스를 vSphere 리소스로 매핑합니다.

| CAPI 리소스 | CAPV 리소스 | 실제 vSphere 객체 |
|---|---|---|
| Cluster | VSphereCluster | Control Plane Endpoint (VIP/LB) |
| Machine | VSphereMachine | 가상머신 (VM) |
| (템플릿) | VSphereMachineTemplate | VM 스펙 (VM Class, Storage Class, TKR 이미지) |

> **참고**: Supervisor 환경의 CAPV는 `vmware.infrastructure.cluster.x-k8s.io` API 그룹의
> Supervisor 모드로 동작하며, VM을 vCenter API로 직접 만들지 않고 **VM Operator**
> (`vmoperator.vmware.com`의 VirtualMachine CR)에게 위임합니다. 독립형(TKGm/OSS) CAPV는
> govmomi 모드로 vCenter에 직접 VM Clone을 요청합니다.

### 1-3. Supervisor Cluster 내 컨트롤러 배치

```
[root@pkyungjin-k8s-master home]# k get pods -n vmware-system-capw     # CAPI/CAPV 컨트롤러
NAME                                        READY   STATUS    AGE
capi-controller-manager-xxx                 2/2     Running   162d    # CAPI Core
capi-kubeadm-bootstrap-controller-xxx       2/2     Running   162d    # Bootstrap Provider
capi-kubeadm-control-plane-controller-xxx   2/2     Running   162d    # Control Plane Provider
capw-controller-manager-xxx                 2/2     Running   162d    # Infra Provider (CAPV Supervisor 모드)

[root@pkyungjin-k8s-master home]# k get pods -n vmware-system-vmop    # VM Operator
[root@pkyungjin-k8s-master home]# k get pods -n vmware-system-tkg     # TKG/VKS 컨트롤러 (TKR, 애드온)
```

---

## 2. 클러스터 생성 흐름 (End-to-End)

```
 사용자          VKS/TKG        CAPI          KCP/Bootstrap      CAPV           VM Operator      vCenter
(kubectl)      Controller    Controller      Controller       Controller       (vmop)
    |               |             |               |               |               |               |
[1] |-- Cluster --->|             |               |               |               |               |
    |  (apply)      |             |               |               |               |               |
    |               |             |               |               |               |               |
[2] |               |-- Topology 렌더링 --------->|               |               |               |
    |               |   Cluster / KCP / MachineDeployment /      |               |               |
    |               |   VSphereMachineTemplate 생성              |               |               |
    |               |             |               |               |               |               |
[3] |               |             |-- VSphereCluster Reconcile ->|               |               |
    |               |             |               |               |-- Control Plane VIP 확보     |
    |               |             |               |               |   (NSX LB / NSX ALB)         |
    |               |             |               |               |               |               |
[4] |               |             |<-- 첫 번째 CP Machine 생성    |               |               |
    |               |             |               |-- KubeadmConfig 렌더링       |               |
    |               |             |               |   cloud-init Secret 생성     |               |
    |               |             |               |   (kubeadm init)             |               |
    |               |             |               |               |               |               |
[5] |               |             |-- Machine → VSphereMachine ->|               |               |
    |               |             |               |               |-- VirtualMachine CR 생성 --->|
    |               |             |               |               |   (bootstrap data 전달)      |
    |               |             |               |               |               |-- VM Clone ->|
    |               |             |               |               |               |   (Content Library
    |               |             |               |               |               |    TKR 이미지, 전원 On)
    |               |             |               |               |               |<-- VM IP ----|
    |               |             |               |               |               |   (DHCP/NSX) |
    |               |             |               |               |               |               |
[6] |               |             |               |          [VM 내부] 부팅 → cloud-init 실행 →  |
    |               |             |               |          kubeadm init → API Server 기동      |
    |               |             |               |               |               |               |
    |               |             |-- Node 등록 확인 → Machine: Running          |               |
    |               |             |<-- 나머지 CP Machine 순차 join (KCP)         |               |
    |               |             |-- Worker Machine 병렬 생성 (kubeadm join) → [5]~[6] 반복     |
    |               |             |               |               |               |               |
[7] |               |-- 애드온 배포 (CNI/CSI/CPI, kapp-controller) → 워크로드 클러스터           |
    |               |             |               |               |               |               |
[8] |<- Cluster Ready (Phase: Provisioned) -------|               |               |               |
    |               |             |               |               |               |               |
```

### 단계별 상세

**① 사용자 요청**
사용자가 vSphere Namespace에 `Cluster`(ClusterClass 기반, v1beta1) 또는 레거시
`TanzuKubernetesCluster` CR을 apply 합니다. (레거시 TKC API는 VKS 3.7에서 제거) (`manifests/cluster/cluster-v1beta1.yaml` 참조)

**② Topology 렌더링 (CAPI Topology Controller)**
`spec.topology`에 선언된 내용(버전, 노드 수, VM Class, TKR)을 ClusterClass
ClusterClass 템플릿(vSphere 7/8: `tanzukubernetescluster`, VKS 3.x/VCF 9.x: `builtin-generic-v3.x.0`)과
결합하여 하위 CAPI 리소스 트리를 생성합니다.

```
Cluster
 ├── VSphereCluster                      # Infra: Control Plane Endpoint
 ├── KubeadmControlPlane
 │    └── Machine (x N)
 │         ├── KubeadmConfig            # cloud-init (kubeadm init/join)
 │         └── VSphereMachine
 │              └── VirtualMachine      # VM Operator CR → 실제 VM
 └── MachineDeployment (node pool 별)
      └── MachineSet
           └── Machine (x N)  →  KubeadmConfig / VSphereMachine / VirtualMachine
```

**③ 인프라 준비 (CAPV)**
CAPV가 `VSphereCluster`를 Reconcile 하여 Control Plane Endpoint(VIP)를 확보합니다.
NSX-T 환경은 NSX Load Balancer, VDS 환경은 NSX ALB(Avi)가 VIP를 제공하며,
준비 완료 시 `VSphereCluster`의 `status.ready=true`가 됩니다.

**④ Control Plane 부트스트랩 (KCP + Bootstrap Controller)**
KCP는 첫 Machine 1대를 먼저 생성합니다. Kubeadm Bootstrap Controller(CABPK)가
`KubeadmConfig`를 렌더링하여 **cloud-init 데이터를 Secret으로 생성**하고, 이 Secret
참조가 Machine의 `spec.bootstrap.dataSecretName`에 연결됩니다.
첫 노드는 `kubeadm init`, 이후 노드는 `kubeadm join` 스크립트를 받습니다.

**⑤ VM 생성 (CAPV → VM Operator → vCenter)**
CAPV가 `Machine`에 대응하는 `VSphereMachine`을 만들고, Supervisor 모드에서는 이를
VM Operator의 `VirtualMachine` CR로 변환합니다. VM Operator는 vSphere Namespace에
연결된 **Content Library의 TKR(Tanzu Kubernetes Release) 이미지**로 VM을 Clone하고,
VM Class(CPU/메모리), Storage Class(스토리지 정책)를 적용해 전원을 켭니다.
bootstrap Secret은 VM의 metadata(cloud-init userdata)로 주입됩니다.

**⑥ 노드 기동 && 등록**
VM이 부팅되면 cloud-init이 kubeadm을 실행하여 Control Plane을 구성하거나 join 합니다.
CAPI Machine Controller는 워크로드 클러스터의 Node 객체와 Machine의 `providerID`를
매칭하여 확인되면 Machine을 `Running`으로 전환합니다.
Control Plane이 정족수를 채우면 MachineDeployment의 Worker들이 병렬로 생성됩니다.

**⑦ 애드온 배포 (VKS Controller)**
API Server가 기동되면 VKS의 애드온 컨트롤러가 `ClusterBootstrap`에 정의된 패키지
(CNI: Antrea/Calico, vSphere CSI, Cloud Provider(CPI), kapp-controller, metrics-server 등)를
워크로드 클러스터에 설치합니다. CNI가 배포되어야 Node가 `Ready`로 전환됩니다.

**⑧ 완료**
모든 Machine이 Running, 애드온이 Ready가 되면 Cluster `phase: Provisioned`,
`ControlPlaneReady/InfrastructureReady=True`가 됩니다.

---

## 3. 생성 과정 관찰 (Supervisor Cluster에서)

```
# Supervisor Context로 전환 후 자신의 vSphere Namespace에서 확인
[root@pkyungjin-k8s-master home]# k config use-context 192.168.70.10

# CAPI 리소스 트리 확인
[root@pkyungjin-k8s-master home]# k get cluster,kubeadmcontrolplane,machinedeployment,machine -n pkyungjin-ns01
NAME                               PHASE         AGE
cluster.cluster.x-k8s.io/tkc-01    Provisioned   10m

NAME                                          INITIALIZED   REPLICAS   READY
kubeadmcontrolplane.../tkc-01-xxxxx           true          1          1

NAME                                          READY   REPLICAS
machinedeployment.../tkc-01-node-pool-1-xxx   True    2

NAME                                          PHASE     NODENAME
machine.../tkc-01-xxxxx-abcde                 Running   tkc-01-xxxxx-abcde
machine.../tkc-01-node-pool-1-xxx-fghij       Running   ...

# CAPV / VM Operator 리소스 확인
[root@pkyungjin-k8s-master home]# k get vspherecluster,vspheremachine -n pkyungjin-ns01
[root@pkyungjin-k8s-master home]# k get virtualmachine -n pkyungjin-ns01
NAME                          POWER-STATE   CLASS               IMAGE                            IP
tkc-01-xxxxx-abcde            PoweredOn     best-effort-small   ob-xxxx-photon-3-k8s-v1.27.x    10.244.0.34

# 부트스트랩 cloud-init Secret 확인 (④ 단계 산출물)
[root@pkyungjin-k8s-master home]# k get secret -n pkyungjin-ns01 | grep bootstrap

# 진행 상황 / 실패 원인 추적: Cluster → Machine → VirtualMachine 순으로 conditions 확인
[root@pkyungjin-k8s-master home]# k describe cluster tkc-01 -n pkyungjin-ns01
[root@pkyungjin-k8s-master home]# k describe machine <machine-name> -n pkyungjin-ns01
```

---

## 4. Scale && Upgrade 시 동작

- **Worker Scale-out**: `spec.topology.workers.machineDeployments[].replicas` 수정 →
  MachineSet이 새 Machine 추가 → ⑤~⑥ 과정 반복. Scale-in 시 Machine 삭제 →
  노드 drain → VM 삭제 순으로 진행됩니다.
- **Kubernetes 버전 업그레이드**: `spec.topology.version` 변경 → 새 TKR 이미지 기반의
  VSphereMachineTemplate로 교체 → KCP가 Control Plane을 1대씩 **Rolling Replace**
  (새 VM 생성 → join → 구 VM drain/삭제) → 이후 MachineDeployment가 Worker를
  롤링 교체합니다. 노드는 **In-place 업그레이드가 아닌 VM 재생성(Immutable Infrastructure)**
  방식입니다.

---

## 5. 트러블슈팅 포인트

| 증상 | 확인 포인트 |
|---|---|
| Cluster가 Provisioning에서 멈춤 | `VSphereCluster` conditions — VIP(LB) 확보 실패 여부 (NSX/ALB 상태) |
| Machine이 Provisioning에서 멈춤 | `VirtualMachine` 상태 — VM Class 리소스 부족, Storage Policy 미할당, Content Library에 해당 TKR 이미지 없음 |
| VM은 켜졌는데 Machine이 Running이 안 됨 | VM 콘솔에서 cloud-init 로그 확인, Control Plane Endpoint 통신 여부 |
| Node가 NotReady | CNI(Antrea/Calico) 애드온 배포 여부 — 워크로드 클러스터에서 `k get pods -n kube-system` |
| 업그레이드 중단 | KCP conditions, 신규 TKR 호환성 (`k get tkr`) |

```
# 컨트롤러 로그 직접 확인 (Supervisor 노드 접근 가능 시)
[root@pkyungjin-k8s-master home]# k logs -n vmware-system-capw deploy/capi-controller-manager
[root@pkyungjin-k8s-master home]# k logs -n vmware-system-capw deploy/capw-controller-manager
[root@pkyungjin-k8s-master home]# k logs -n vmware-system-vmop deploy/vmware-system-vmop-controller-manager
```
