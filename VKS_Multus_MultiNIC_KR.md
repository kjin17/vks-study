# VKS 멀티 NIC 파드 교육 자료 — Multus · Whereabouts · SR-IOV

> 대상: VKS 플랫폼·운영 엔지니어, Telco/CNF·고성능 워크로드 담당
> 정리일: 2026-09-22
> 기준: VKS 3.6(노드 보조 NIC) / VKS 3.7(Multus·Whereabouts 애드온, vfio-pci), VKr 1.35~1.36

## 📑 근거 등급 표기

| 표기 | 의미 |
|---|---|
| 🅑 | Broadcom 공식 문서·릴리스 노트·ClusterClass 변수 레퍼런스에 명시 |
| 🅞 | Multus/CNI 업스트림 일반 지식 — VKS에서 다를 수 있음 |
| ❓ | **출처 간 서술이 엇갈려 미결로 남긴 항목** — 실환경 확인 필요 |

---

## 1. 먼저 층을 가르세요 — 노드 NIC ≠ 파드 NIC

멀티 NIC 이야기는 **두 개의 다른 층**이 섞여서 혼란이 큽니다. VKS에서는 이 둘이 명확히 분리돼 있습니다. 🅑

```
┌───────────────────────────────────────────────────────────┐
│  ③ 파드 멀티 NIC                                            │
│     파드마다 net1, net2 … 전용 인터페이스 + 전용 IP            │
│     → Multus + Whereabouts  또는  Antrea SecondaryNetwork   │
├───────────────────────────────────────────────────────────┤
│  ② 노드 보조 NIC (eth1~eth9)                                │
│     노드 VM에 vNIC 추가. 그 노드의 모든 파드가 공유            │
│     → networks 변수 · CAPV/vm-operator가 담당, CNI 무관      │
├───────────────────────────────────────────────────────────┤
│  ① 인프라 네트워크                                           │
│     NSX VPC Subnet  또는  VDS 분산 포트그룹                  │
└───────────────────────────────────────────────────────────┘
```

| 구분 | 노드 보조 NIC (②) | 파드 멀티 NIC (③) |
|---|---|---|
| 단위 | 노드 VM | 개별 파드 |
| 담당 | CAPV / vm-operator (**인프라 계층**) | CNI 메타플러그인 (Multus / Antrea) |
| CNI 의존 | **없음** — Antrea든 Calico든 무관 | 있음 |
| 도입 | VKS 3.6 | Antrea: 3.6 / **Multus: 3.7** |
| 쓰는 곳 | 노드 전체 트래픽 분리 (NFS 스토리지, DB 복제) | 특정 워크로드만 전용 경로 (CNF, 멀티캐스트) |

> 🔴 **가장 흔한 오해:** 노드에 eth1을 붙이면 트래픽이 알아서 나뉜다고 생각하는 것. 아닙니다. **파드는 기본적으로 계속 eth0을 씁니다.** eth1에는 **기본 경로(default route)가 없고**, 목적을 명시적으로 부여하기 전까지 아무것도 흐르지 않습니다. 🅑
>
> 그럼 eth1을 왜 다느냐 — **보안 가치가 위상(topology)에 있기 때문**입니다. Kubernetes API 서버는 eth0의 서브넷에서만 듣습니다. eth0이 제한된 관리망이고 eth1이 다른 서브넷이면, **eth1에만 연결된 것은 컨트롤 플레인에 물리적으로 닿을 수 없습니다.** NetworkPolicy는 잘못 설정하거나 우회할 수 있지만, 물리 계층 방화벽으로 받쳐진 별도 서브넷은 그럴 수 없습니다. 🅑

---

## 2. 지원 백엔드와 제약 🅑

| 백엔드 | 네트워크 제공자 | API 그룹 | 오브젝트 |
|---|---|---|---|
| **NSX VPC** | `NSX_VPC` | `crd.nsx.vmware.com/v1alpha1` | `SubnetSet`, `Subnet` |
| **VDS** | `VSPHERE_NETWORK` | `netoperator.vmware.com/v1alpha1` | `Network` |

⚠️ **NSX-T T1(VPC 없는 레거시 NSX 토폴로지)은 현재 미지원입니다.** 🅑

### 🔴 현재 못 하는 것 — 설계 전에 반드시 읽을 것 🅑

| 제약 | 의미 |
|---|---|
| **보조 네트워크에 LoadBalancer 서비스 불가** | Service type LoadBalancer는 **항상 primary**에 생깁니다. 「Ingress를 특정 보조 서브넷에 노출」은 불가능 |
| **보조 인터페이스에 NetworkPolicy·SecurityPolicy 미적용** | Antrea 네트워크 정책이 보조 NIC에 아직 적용되지 않습니다. **eth1 이상의 트래픽은 K8s 정책 계층에서 필터링되지 않습니다** |
| **primary NIC는 영구** | 생성 후 변경 불가 (변수 검증에 `primary field cannot be updated after creation` 명시). 서브넷을 신중히 계획할 것 |
| **SR-IOV VLAN 태깅은 VDS 전용** | NSX VPC에서는 아직 미지원 |
| **Windows 노드 풀 불가** | Windows 워커는 보조 NIC를 쓸 수 없습니다 |

> ❓ **미결 — 보조 인터페이스를 제거할 수 있는가**
> - VKS 3.6 계열 설명: **추가만 가능(additive only).** eth1을 한 번 붙이면 **제거할 수 없고**, 설정 변경은 되지만 완전 제거는 클러스터 재생성이 필요
> - VKS 3.7 릴리스 노트(Multus 항목): 「보조 인터페이스는 **클러스터 생성 후 안전하게 제거 가능**」
>
> 두 서술이 엇갈립니다. 3.7에서 완화됐을 수도 있고, 3.7 쪽 문장이 **Calico autodetect 워크어라운드 맥락의 다른 인터페이스**를 가리키는 것일 수도 있습니다. **해석으로 메우지 말고**, 도입 전에 쓰려는 정확한 버전에서 실제로 시험해 결론을 내세요. 그때까지는 **보수적으로(제거 불가로) 설계**하는 편이 안전합니다.

---

## 3. 층 ② — 노드 보조 NIC 붙이기

### 3-1. (NSX VPC) 인프라 준비 — Subnet 생성 🅑

```yaml
apiVersion: crd.nsx.vmware.com/v1alpha1
kind: Subnet
metadata:
  name: secondary-node-net
  namespace: vks-ns
spec:
  accessMode: Private          # 보조 노드 IP를 외부망에 노출하지 않음
  subnetDHCPConfig:
    mode: DHCPDeactivated      # 필수: 보조 NIC는 자체적으로 IP를 관리
  advancedConfig:
    staticIPAllocation:
      enabled: false           # 필수: 스케일 시 IP 고갈 방지
```

🔴 **`staticIPAllocation.enabled: false`는 권고가 아니라 필수입니다.** 🅑
보조 노드 vNIC를 받치는 부모 서브넷에서 정적 IP 할당이 켜져 있으면, 노드가 프로비저닝될 때마다 정적 IP를 소비하는데 **롤링 업데이트 중에 그 IP가 반환되지 않습니다.** 자주 스케일하는 클러스터는 서브넷을 고갈시킵니다. **처음부터 false로 두세요.**

> VCF Automation UI로 만든다면 대응 설정은 **Static IP Allocation: No**, **DHCP: None** 입니다. UI가 내는 경고(「이 Subnet에 IP 관리가 정의되지 않아 연결된 워크로드에 IP를 할당하지 않습니다」)는 **의도된 것**입니다 — 노드는 프로비저닝 시점에 NSX와 CAPV에서 IP를 받지, DHCP에서 받지 않습니다. 🅑

### 3-2. (VDS) 인프라 준비 — 포트그룹 3종 설정 🅑

클러스터 생성 **전에** 분산 포트그룹에 다음 세 가지를 **모두** 설정합니다.

1. **Trunk 모드**
2. **Forged Transmits** 허용
3. **MAC Learning Policy** 활성화

🔴 **셋 중 둘만 맞춰도 노드는 정상(healthy)으로 올라옵니다.** 고장은 **나중에 파드 보조 NIC를 만들 때** 통신 불가로 나타나고, **포트그룹 설정을 직접 가리키는 이벤트나 에러가 없습니다.** Antrea의 OVS 브리지가 MAC learning을 요구하기 때문인데, 이 자리가 디버깅 시간을 가장 많이 잡아먹는 지점입니다. 🅑

> 교훈으로 옮기면 — **사전 점검은 진짜 동작으로 해야 합니다.** 노드가 Ready인 것은 포트그룹 설정이 맞다는 증거가 아닙니다. 그 검사는 **파드 보조 NIC 통신**으로만 할 수 있습니다.

### 3-3. `networks` 변수 — 스키마 🅑

도입 VKS **3.6.0** · 적용 범위 `cluster`, `controlPlane`, `workers` · **변경 시 머신 롤아웃 발생**

`networks.interfaces.secondary[]` 필드:

| 필드 | 타입 | 필수 | 도입 | 설명 |
|---|---|---|---|---|
| `name` | string | ✅ | 3.6.0 | 인터페이스 이름. **`eth0`은 사용 불가**(검증 규칙) |
| `network` | object | ✅ | 3.6.0 | 연결할 네트워크 리소스 — `apiVersion` / `kind` / `name` |
| `mtu` | integer | — | 3.6.0 | MTU. 점보 프레임은 9000 |
| `routes` | []object | — | 3.6.0 | 정적 경로 `to`(IPv4 CIDR) / `via`(IPv4). **CloudInit 부트스트랩 프로바이더에서만** |
| `driver` | string | — | **3.7.0** | 바인딩할 커널 드라이버. **현재 `vfio-pci`만 지원** |
| `sriovResourcePool` | object | — | **3.7.0** | SR-IOV 디바이스 플러그인 리소스 풀 — `name`(필수) / `prefix`(필수). **`driver` 지정 시 함께 설정** |

`primary`는 `mtu` / `network` / `routes`만 가지며, **NSX-VPC에서만 커스터마이즈 가능**하고 **`SubnetSet`만 참조**할 수 있습니다(개별 `Subnet` 불가). `secondary`는 `SubnetSet`·`Subnet` 둘 다 됩니다. 🅑

> 💡 **대부분의 배포에서 `primary`는 아예 생략하세요.** VKS가 eth0용 private `SubnetSet`을 자동 생성하며, 그게 내부 관리망의 올바른 기본값입니다. eth0에 **전역 라우팅 가능한 노드 IP**가 필요할 때만 `accessMode: Public`인 `SubnetSet`을 미리 만들어 참조합니다. 🅑

### 3-4. 클러스터 YAML (NSX VPC) 🅑

```yaml
apiVersion: cluster.x-k8s.io/v1beta2
kind: Cluster
metadata:
  name: prod-cluster
  namespace: vks-ns
spec:
  topology:
    class: builtin-generic-v3.6.0
    version: v1.35.0---vmware.2-vkr.4
    controlPlane:
      replicas: 3
    variables:
      - name: storageClass
        value: <your-storage-profile>
      - name: vmClass
        value: best-effort-medium
      - name: networks
        value:
          interfaces:
            # primary 생략 — VKS가 private SubnetSet 자동 생성
            secondary:
              - name: eth1
                mtu: 1500              # NFS·스토리지면 9000(점보 프레임)
                network:
                  apiVersion: crd.nsx.vmware.com/v1alpha1
                  kind: Subnet
                  name: secondary-node-net
    workers:
      machineDeployments:
        - class: node-pool
          name: workers
          replicas: 3
```

### 3-5. 클러스터 YAML (VDS) 🅑

API 그룹과 kind만 다릅니다.

```yaml
- name: networks
  value:
    interfaces:
      secondary:
        - name: eth1
          mtu: 1700
          network:
            apiVersion: netoperator.vmware.com/v1alpha1
            kind: Network
            name: workload-trunk-portgroup   # vSphere의 VDS 포트그룹 이름
```

> VDS에서는 **primary 커스터마이즈 미지원** — eth0은 항상 기본 네임스페이스 Network를 씁니다. 그리고 **클러스터 스펙에 VLAN ID가 없습니다.** 모든 VLAN 구성은 클러스터 생성 전에 **vSphere의 포트그룹에서** 합니다. 🅑

### 3-6. 정적 경로 — eth1에 목적 부여하기 🅑

eth1에 기본 경로가 없으므로, 원격 서브넷(예: NFS 스토리지망)에 닿으려면 정적 경로를 추가합니다.

```yaml
secondary:
  - name: eth1
    mtu: 9000
    network:
      apiVersion: crd.nsx.vmware.com/v1alpha1
      kind: Subnet
      name: secondary-node-net
    routes:
      - to: 192.168.100.0/24      # 스토리지 서브넷
        via: 172.30.0.97          # eth1 쪽 게이트웨이
```

- `to`: IPv4 CIDR — **IPv6 미지원**
- `via`: IPv4 주소 — **IPv6 미지원**
- **CloudInit 부트스트랩 프로바이더에서만** 동작

### 3-7. 검증 🅑

```bash
kubectl get nodes

# VKS 네임스페이스는 기본 restricted PSS라 노드 디버깅이 막힙니다.
# privileged로 도는 kube-system을 대상으로 실행하세요.
kubectl debug node/<node-name> -it --image=nicolaka/netshoot -n kube-system -- bash

# 컨테이너 안에서
ip addr
```

```
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 172.30.0.68/27 ...   ← primary (관리)
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 172.30.0.99/28 ...   ← secondary (워크로드/스토리지)
```

두 인터페이스가 **서로 다른 서브넷**에 있고 **게이트웨이를 공유하지 않는지** 확인합니다. `exit`하면 디버그 파드는 자동 정리됩니다. 🅑

> kubectl 없이도 확인 가능합니다 — vSphere에서 클러스터의 **Node Network** 항목에 eth1과 연결 서브넷이 보이고, 워커 VM의 **IP Addresses**에 primary·secondary IP가 모두 나옵니다. 🅑

### 3-8. 기존 클러스터에 추가할 수 있나 🅑

**가능합니다.** `networks.interfaces.secondary` 목록을 수정하면 VKS가 **롤링 노드 업데이트**로 적용하며 클러스터 전체 다운타임은 없습니다. VCF Automation UI에서 기존 클러스터의 노드 네트워크를 편집해도 됩니다.

단, **primary 변경**과 **인터페이스 제거**는 위 ❓ 항목을 참조하세요.

### 3-9. 환경이 이 기능을 지원하는지 확인 🅑

Supervisor에서 `supports_vks_multi_networks` capability 플래그를 조회합니다. `activated`가 `true`인 조건:

- VKS 3.6 이상이 등록돼 있고
- **VDS**면 `supports_multiple_vds_networks`, **NSX VPC**면 `supports_shared_subnets_with_namespace`(K8s 1.30+ 필요)가 활성

VCF Automation은 UI에 멀티 네트워크 옵션을 띄우기 전에 이 플래그를 읽습니다.

---

## 4. 층 ③ — 파드 멀티 NIC

노드에 eth1이 붙었으면, 이제 **개별 파드**에 전용 인터페이스를 줄 차례입니다. VKS에는 두 갈래가 있습니다.

| 경로 | 도입 | CNI | 지원 티어 | 특징 |
|---|---|---|---|---|
| **Antrea SecondaryNetwork + AntreaIPAM** | VKS 3.6 | Antrea | VKr 내장 | 네이티브 경로. `AntreaIPAM`·`SecondaryNetwork` 피처 게이트 사용, Antrea `IPPool`에서 IP 할당 🅑 |
| **Multus + Whereabouts** | **VKS 3.7** | **Calico(VPC 모드)** | **Product** | 업계 표준 메타플러그인. macvlan/ipvlan/SR-IOV 등 하위 플러그인 자유 🅑 |

### 4-1. Multus·Whereabouts 애드온 🅑

| 애드온 | 버전 | 티어 | 역할 |
|---|---|---|---|
| **Multus** | 4.2.4 | **Product** | 메타플러그인 — 여러 하위 CNI를 호출해 파드에 보조 인터페이스 연결 |
| **Whereabouts** | 0.9.3 | **Product** | **클러스터 범위 IPAM** — 보조 인터페이스들에 IPv4/IPv6를 충돌 없이 동적 할당·추적 |

- 제공 저장소: **VKS Add-ons v3.7.0+20260618**
- **Product 티어** — 배포·라이프사이클·런타임 문제 모두 Broadcom GS 완전 지원. (Cilium의 Ecosystem 티어와 지원 성격이 다릅니다)
- 대상: **VPC 모드 Calico CNI 클러스터에서의 멀티 NIC**

🔴 **VKr 1.36 미만 + Calico 조합의 사전 작업:** 클러스터 생성 **전에** autodetect 인터페이스를 `eth0`으로 설정하는 추가 구성이 필요합니다. 🅑
이유를 풀면 — 노드에 NIC가 여러 개 생기는 순간 Calico의 인터페이스 자동 탐지가 **엉뚱한 NIC를 고를 수 있기 때문**입니다. 「보조 NIC를 붙였더니 Calico가 이상해졌다」는 증상이 여기서 나옵니다.

### 4-2. 애드온 설치 🅑

Multus·Whereabouts도 Cilium과 같은 **애드온 프레임워크**를 씁니다. 리소스 지도는 `VKS_Cilium_CNI_KR.md` 3절과 동일합니다.

```yaml
apiVersion: addons.kubernetes.vmware.com/v1alpha1
kind: AddonInstall
metadata:
  name: <cluster-name>-multus
  namespace: <cluster-namespace>
spec:
  addonRef:
    name: multus
  clusters:
    selector:
      matchLabels:
        cluster.x-k8s.io/cluster-name: <cluster-name>
```

> ⚠️ 위 매니페스트는 **애드온 프레임워크의 일반 형태**입니다. Cilium처럼 `constraints.expression`이나 전용 사전 작업이 필요한지는 애드온마다 다르므로, 설치 전에 Supervisor에서 실제 리소스를 조회해 확인하세요. 🅞
> ```bash
> kubectl get addon -n vmware-system-vks-public
> kubectl get addonrelease -n vmware-system-vks-public | grep -iE 'multus|whereabouts'
> kubectl get addonconfigdefinition -n vmware-system-vks-public
> ```
> CNI 본체인 Cilium은 `bootstrapAddons`로 **부트스트랩 단계에** 선택하지만, Multus는 **주 CNI 위에 얹히는 메타플러그인**이라 그 변수를 쓰지 않습니다.

VCF Automation의 **VKS Cluster Management** UI로도 애드온을 설치·관리할 수 있습니다(VKS 3.5+). 🅑

### 4-3. `NetworkAttachmentDefinition` — 파드가 붙을 네트워크 정의 🅞

Multus는 CNCF Network Plumbing WG 표준을 따릅니다.

```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan-conf
  namespace: my-app
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "macvlan",
    "master": "eth1",
    "mode": "bridge",
    "ipam": {
      "type": "whereabouts",
      "range": "192.168.100.0/24",
      "range_start": "192.168.100.200",
      "range_end": "192.168.100.250",
      "gateway": "192.168.100.1"
    }
  }'
```

- `master: eth1` — **3절에서 노드에 붙인 보조 NIC 이름**입니다. 두 층이 여기서 만납니다
- `ipam.type: whereabouts` — 클러스터 범위 IPAM. `host-local`은 노드별로 독립이라 **노드 간 IP 충돌이 날 수 있습니다.** 여러 노드에 걸치는 보조 네트워크에는 Whereabouts를 쓰세요 🅞
- `NetworkAttachmentDefinition`은 **네임스페이스 범위** 리소스입니다

### 4-4. 파드에 붙이기 🅞

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-nic-pod
  namespace: my-app
  annotations:
    k8s.v1.cni.cncf.io/networks: macvlan-conf
spec:
  containers:
    - name: app
      image: nicolaka/netshoot
      command: ["sleep", "infinity"]
```

`k8s.v1.cni.cncf.io/networks`는 **쉼표로 구분된 `NetworkAttachmentDefinition` 이름 목록**을 받습니다.

결과 인터페이스:

| 인터페이스 | 출처 |
|---|---|
| `lo` | 루프백 |
| `eth0` | **기본 파드 네트워크** — 주 CNI(Calico/Antrea)가 관리 |
| `net1` | 어노테이션으로 붙인 첫 번째 보조 네트워크 |
| `net2`, `net3` … | 추가 보조 네트워크 |

> 🔑 **기본 네트워크는 항상 `eth0`이고, 추가 인터페이스는 `net1`부터 번호가 붙습니다.** 노드의 `eth1`과 파드의 `net1`은 **다른 것**입니다 — 이름이 헷갈리기 쉬우니 문서·코드에 층을 명시하세요.

```bash
# 검증
kubectl exec -n my-app multi-nic-pod -- ip addr
kubectl get pod -n my-app multi-nic-pod -o jsonpath='{.metadata.annotations.k8s\.v1\.cni\.cncf\.io/networks-status}'
```

---

## 5. SR-IOV · DPDK — vfio-pci 바인딩 🅑

VKS 3.7에서 보조 NIC를 **커널 드라이버에서 떼어 vfio-pci에 바인딩**할 수 있게 됐습니다. Telco 5G Core CNF처럼 DPDK 가속이 필요한 워크로드용입니다.

```yaml
- name: networks
  value:
    interfaces:
      secondary:
        - name: eth1
          network:
            apiVersion: netoperator.vmware.com/v1alpha1
            kind: Network
            name: sriov-portgroup
          driver: vfio-pci
          sriovResourcePool:
            prefix: intel.com
            name: sriov_netdevice
```

파드는 **표준 리소스 요청**으로 NIC를 직접 가져갑니다.

```yaml
resources:
  requests:
    intel.com/sriov_netdevice: "1"
  limits:
    intel.com/sriov_netdevice: "1"
```

### 🔴 vIOMMU 경고 — 보안에 직결됩니다 🅑

> 노드 VM에 **vIOMMU가 활성화되어 있지 않으면**, 머신 에이전트가 vfio-pci 바인딩을 진행하기 위해 **VFIO unsafe no-IOMMU 모드를 자동으로 켭니다.** 이 경우 디바이스의 **DMA가 IOMMU로 보호되지 않습니다.**
>
> **프로덕션 배포에서는 노드 VM에 vIOMMU를 활성화하세요.**

이건 「설정이 자동으로 되니 편하다」가 아니라 **격리 보장이 조용히 내려간다**는 뜻입니다. 자동 폴백이 경고 없이 보안 속성을 낮추는 전형적인 자리이므로, 클러스터 인수인계 문서에 **vIOMMU 상태를 명시적으로 적으세요.**

### 그 밖의 제약 🅑

- `sriovResourcePool`은 `driver`를 지정할 때 **함께 설정**해야 합니다
- `name`·`prefix` 둘 다 **필수**
- **SR-IOV VLAN 태깅은 VDS 전용** — NSX VPC 미지원
- 관련 애드온: **SR-IOV Plugin 3.11.0** (vhost-net 감지·프로비저닝 옵션 포함)

---

## 6. 스케일 시 필수 조정 — 워커 250대 🅑

VKS 3.7에서 워커가 150 → **250대**로 늘었습니다. 다만 그냥 늘리면 안 되고 다음을 함께 조정해야 합니다.

| 항목 | 조정값 |
|---|---|
| **컨트롤 플레인 VM 클래스** | Antrea+AVI: 최소 **4 vCPU / 12 GiB** · **Calico+Multus+AVI: 최소 6 vCPU / 12 GiB** |
| **etcd DB 크기** | 최소 **4 GB**로 상향 (기본 2 GB는 고동시성 롤아웃에 부족) |
| **Pod CIDR** | `maxPods` 110(기본)이면 **/15** 마스크, 더 크면 **/14** |
| 🔴 **Multus 메모리 제한** | **1.5 Gi 이상** — 안 올리면 **OOMKilled** |

> `maxSurge > 20`의 고동시성 롤아웃 + 약 11,000 파드 규모에서는 컨트롤 플레인 VM 클래스를 더 올려야 할 수 있습니다.
>
> 📌 **Multus를 쓰면 컨트롤 플레인 요구가 4 vCPU → 6 vCPU로 올라간다**는 점에 주목하세요. 멀티 NIC는 파드 네트워킹만 바꾸는 게 아니라 **클러스터 사이징 결정**입니다.

---

## 7. 트러블슈팅 지도

| 증상 | 먼저 볼 곳 | 등급 |
|---|---|---|
| 노드는 Ready인데 **파드 보조 NIC 통신 불가** (VDS) | 포트그룹 **trunk / Forged Transmits / MAC Learning 3종** — 둘만 맞아도 노드는 정상으로 뜹니다 | 🅑 |
| 스케일 아웃 중 **IP 고갈** | 부모 Subnet의 `staticIPAllocation.enabled` — 반드시 `false` | 🅑 |
| **eth1로 트래픽이 안 나감** | 정상입니다. eth1엔 기본 경로가 없습니다. `routes`를 정의했는지 확인 | 🅑 |
| **Calico가 이상해짐** (보조 NIC 추가 후) | VKr 1.36 미만이면 autodetect 인터페이스를 `eth0`으로 고정하는 사전 구성 | 🅑 |
| **Multus 파드 OOMKilled** | 메모리 제한 1.5 Gi 이상 | 🅑 |
| **파드 간 보조 IP 충돌** | IPAM이 `host-local`이면 노드별 독립 → Whereabouts로 교체 | 🅞 |
| **보조 NIC 트래픽이 정책에 안 걸림** | 정상입니다. 보조 인터페이스에는 NetworkPolicy가 적용되지 않습니다 | 🅑 |
| **Windows 워커에서 안 됨** | 미지원 | 🅑 |

---

## 8. 설계 체크리스트

**인프라 (①)**
- [ ] 백엔드가 **NSX VPC** 또는 **VDS**인가 (NSX-T T1은 미지원)
- [ ] NSX VPC: Subnet에 `DHCPDeactivated` + `staticIPAllocation.enabled: false` 🔴
- [ ] VDS: 포트그룹에 **trunk + Forged Transmits + MAC Learning 3종 모두** 🔴
- [ ] `supports_vks_multi_networks` 플래그가 `activated: true`인가

**노드 보조 NIC (②)**
- [ ] **primary는 생략**해도 되는가 (대부분 생략이 정답)
- [ ] 보조 NIC 이름이 `eth0`이 아닌가
- [ ] 스토리지용이면 MTU 9000을 검토했는가 (경로 전 구간이 점보 프레임을 지원해야 함)
- [ ] 원격 서브넷이 필요하면 `routes`를 정의했는가 (CloudInit 전용, IPv4만)
- [ ] **제거 불가**를 전제로 설계했는가 (❓ 2절 미결 항목)

**파드 멀티 NIC (③)**
- [ ] **Antrea SecondaryNetwork**와 **Multus** 중 무엇을 쓸 것인가
- [ ] Multus면 VKS **3.7 + VPC 모드 Calico**인가
- [ ] VKr 1.36 미만이면 Calico autodetect 사전 구성을 했는가
- [ ] IPAM이 **Whereabouts**인가 (노드 간 충돌 방지)
- [ ] NAD의 `master`가 실제 노드 보조 NIC 이름과 일치하는가

**SR-IOV (선택)**
- [ ] 노드 VM에 **vIOMMU가 활성화**돼 있는가 🔴 (없으면 DMA 보호가 사라집니다)
- [ ] `driver`와 `sriovResourcePool`을 함께 설정했는가
- [ ] VLAN 태깅이 필요하면 **VDS**인가

**스케일**
- [ ] Multus 사용 시 컨트롤 플레인 **6 vCPU / 12 GiB** 이상인가
- [ ] Multus 메모리 제한 **1.5 Gi** 이상인가

---

## 9. 관련 문서

- **`VKS_Cilium_CNI_KR.md`** — 애드온 프레임워크 리소스 지도, `AddonInstall` 라이프사이클
- **`VKS_Cilium_Hubble_KR.md`** — 관측성
- `VKS_3.6_Release_Notes_KR.md` — 멀티 네트워크 도입, Antrea 하이브리드 모드
- `VKS_3.7_Release_Notes_KR.md` — vfio-pci, Multus/Whereabouts, 250노드 스케일
- `VKS_Addons_Release_Notes_KR.md` — Multus 4.2.4 / Whereabouts 0.9.3 / SR-IOV Plugin 3.11.0

---

_출처: Broadcom TechDocs (ClusterClass Variable Reference — networks/secondary/sriovResourcePool 스키마, Configure Multiple Networks for VKS Clusters, Managing Add-ons in VKS Clusters), VCF Blog (VCF 9.1 Brings Multi-Network Support to VKS), VKS 3.6/3.7 Release Notes, VKS Standard Packages Release Notes. 🅞 표기 항목은 Multus/CNI 업스트림 일반 지식입니다. ❓ 표기 항목은 도입 전 실환경 검증이 필요합니다._
