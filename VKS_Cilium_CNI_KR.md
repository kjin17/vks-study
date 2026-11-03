# VKS Cilium CNI 교육 자료 — VCF 9.1 / VKS 3.6·3.7

> 대상: VKS 플랫폼·운영 엔지니어
> 정리일: 2026-09-22
> 기준: VKS 3.6 / 3.7, VKr 1.35~1.36, VKS Add-ons v3.6.0+20260320 ~ v3.7.0+20260618

## 📑 이 문서의 근거 등급

교육 자료는 「어디까지가 공식 문서고 어디부터가 일반 지식인지」를 구분해야 현장에서 사고가 안 납니다. 본문에 다음 표기를 답니다.

| 표기 | 의미 |
|---|---|
| 🅑 | Broadcom 공식 문서·릴리스 노트에 명시된 내용 (YAML 스키마, 포트, 제약) |
| 🅞 | Cilium 업스트림 일반 지식 — VKS에서 값이 다를 수 있으니 실환경 확인 필요 |
| ❓ | 출처 간 서술이 엇갈려 **미결**로 남긴 항목 |

---

## 1. 왜 Cilium인가 — VKS의 CNI 선택지

VKS의 전략적 기본 CNI는 여전히 **Antrea**입니다. Calico가 함께 내장(KR-bundled)되고, VKS 3.6부터 **Cilium이 검증된 애드온(Ecosystem 티어)으로 합류**했습니다. 🅑

| CNI | VKS에서의 위치 | 지원 티어 | 도입 |
|---|---|---|---|
| **Antrea** | 전략적 기본 CNI. NSX 어댑터 연계, 하이브리드 캡슐화 모드, 파드 멀티 NIC(SecondaryNetwork) | VKr 내장 | 기존 |
| **Calico** | 내장 대안 CNI. VPC 모드 + Multus 조합의 기준 | VKr 내장 | 기존 |
| **Cilium** | eBPF 데이터플레인 대안 CNI. Hubble 관측성, L7 정책, kube-proxy 대체 | **Ecosystem**(패키징·서명·라이프사이클만 지원) | VKS 3.6 / VKr 1.35 |

⚠️ **티어를 먼저 보세요.** Ecosystem 티어는 **런타임 문제를 Broadcom이 지원하지 않습니다.** 설치·업그레이드·서명까지만 지원 범위입니다. Antrea·Calico(내장)나 Product 티어 애드온과 지원 성격이 다르므로, 프로덕션 도입 전에 이 차이를 의사결정에 반영하세요. 🅑

### Cilium이 가져오는 것

- **eBPF 데이터플레인** — iptables 룰 체인 대신 커널 eBPF 맵으로 서비스·정책을 처리 🅞
- **Hubble 관측성** — 플로우 단위 가시성(UI/Relay). 👉 상세는 `VKS_Cilium_Hubble_KR.md` 🅑
- **네트워크 정책 2계층** — Kubernetes NetworkPolicy(L3/L4) + CiliumNetworkPolicy(L7) 🅑
- **kube-proxy 대체** — VKS 3.7의 kube-proxy 비활성화 API와 세트 🅑

---

## 2. 버전·기능 타임라인 🅑

| 애드온 저장소 릴리스 | Cilium | 주요 내용 |
|---|---|---|
| v3.6.0+20260320 | **1.19.1** 🆕 | VKS 대안 CNI로 공식 합류. eBPF 데이터플레인, Hubble UI/Relay, K8s NetworkPolicy(L3/L4) + CiliumNetworkPolicy(L7) |
| v3.7.0+20260618 | **1.19.4** | L7 프록시(Envoy), Ingress 컨트롤러, Egress Gateway(SNAT), Gateway API 컨트롤러, eBPF 마스커레이딩, XDP 로드밸런서 가속, 정책 시행 모드 제어, Prometheus 메트릭(agent/operator), Hubble 플로우 메트릭 |

> 🔄 **업스트림과의 간격 (2026-11-03 확인, GitHub cilium/cilium releases):** 업스트림 최신 패치는 **1.19.10**(2026-10-23), 안정 최신 계열은 **1.20.4**, 다음 계열 **1.21.0-pre.4**(2026-11-02, BPF 마스커레이딩 기본 활성화 예정)입니다. VKS 3.8에 묶인 Cilium 애드온 버전은 이번에 공식 문서에서 확인하지 못했습니다 ❓ — 3.7의 1.19.4 기준이면 업스트림 패치보다 6단계 뒤입니다(추론).

### 전제 조건 🅑

- VKS **3.6 이상**, VKr **1.35 이상**
- Supervisor에 **VKS 애드온 저장소 v3.6.0+20260320 이상** 설치 (Broadcom Support Portal → My Downloads → vSphere Supervisor Services → VKS Release → Drivers & Tools에서 `AddonRepository` YAML 다운로드)
- Cilium은 **클러스터 생성 전에** 준비가 끝나 있어야 합니다. 생성 후 CNI를 바꿔 끼우는 경로가 아닙니다

---

## 3. 애드온 프레임워크 이해 — 리소스 지도 🅑

VKS 3.5부터 애드온이 선언적 API로 바뀌었습니다. Cilium 설치는 이 리소스들을 순서대로 쌓는 일입니다.

| 리소스 | 위치 | 역할 |
|---|---|---|
| `Addon` | `vmware-system-vks-public` | Supervisor에서 사용 가능한 애드온 목록 |
| `AddonRepository` | `vmware-system-vks-public` | 설치 가능한 PackageRepository 정의 |
| `AddonRepositoryInstall` | `vmware-system-vks-public` | 저장소를 선택된 워크로드 클러스터에 바인딩 |
| `AddonRelease` | `vmware-system-vks-public` | 애드온 버전의 불변 메타데이터 — 버전, 호환 제약, 의존성 |
| `AddonConfigDefinition` | `vmware-system-vks-public` | 애드온 설정의 스키마·템플릿 |
| **`AddonInstall`** | 클러스터 네임스페이스 또는 public | **원하는 애드온 상태를 선언** — 우리가 만드는 것 |
| `ClusterAddon` | 클러스터 네임스페이스 | 클러스터별 애드온 인스턴스 + 상태 보고 |
| **`AddonConfig`** | 클러스터 네임스페이스 | **스키마 검증되는 설정값** — Hubble 등을 켜는 자리 |

> 💡 `vmware-system-vks-public`에는 VCF가 만들어 둔 `AddonInstall`이 있습니다. 네임스페이스 편집 권한이 있으면 개별 네임스페이스에 `AddonInstall`을 만들어 **public 것을 덮어쓰거나**, public에 없는 애드온을 설치할 수 있습니다. 🅑

### ⚠️ VKS 3.7의 저장소 모델 변경

3.7부터 단일 저장소를 계속 갱신하는 방식이 아니라 **버전별 추가(additive) 모델**입니다. 설치·업그레이드 때마다 그 릴리스용 `AddonRepository(Install)`이 새로 생기고 여러 저장소가 공존합니다. 3.5/3.6에서 올라온 환경의 기존 `default-addon-repo-install`은 **deprecated** — 동작은 하지만 더 이상 갱신되지 않으며, 불필요한 리소스는 관리자가 직접 지워야 합니다. 🅑

---

## 4. 설치 4단계 🅑

### Step 1. Supervisor에 `AddonInstall` 생성

```yaml
# addoninstall-cilium.yaml
apiVersion: addons.kubernetes.vmware.com/v1alpha1
kind: AddonInstall
metadata:
  name: <cluster-name>-cilium
  namespace: <cluster-namespace>
spec:
  addonRef:
    name: cilium
  clusters:
    - constraints:
        expression: "cluster.cniRefName() == 'cilium' && version_in_range(cluster.spec.topology.version, '>=1.35.0')"
      selector:
        matchLabels:
          cluster.x-k8s.io/cluster-name: <cluster-name>
      stopMatchingBehavior: Retain
```

```bash
kubectl apply -f addoninstall-cilium.yaml
kubectl get addoninstall <cluster-name>-cilium -n <cluster-namespace>
```

`constraints.expression`은 CEL입니다. 「이 클러스터의 CNI 참조가 cilium이고, K8s 버전이 1.35.0 이상일 때만」이라는 뜻이라, 조건을 벗어난 클러스터에 실수로 붙는 것을 막아 줍니다.

### 🔴 Step 1의 지뢰 — 클러스터를 지워도 `AddonInstall`은 안 지워진다

`Cluster` 리소스를 삭제해도 `AddonInstall`은 **남습니다.** 라이프사이클을 따로 관리하거나, 클러스터에 **ownerReference를 걸어** 같이 지워지게 해야 합니다. 🅑

```bash
# 1) 클러스터 UID 조회
kubectl get cluster <cluster-name> -n <namespace> -o jsonpath='{.metadata.uid}'

# 2) AddonInstall에 ownerReference 패치
kubectl patch addoninstall <addoninstall-name> -n <addoninstall-namespace> --type='merge' -p '
{
  "metadata": {
    "ownerReferences": [
      {
        "apiVersion": "<cluster-api-version>",
        "kind": "Cluster",
        "name": "<cluster-name>",
        "uid": "<retrieved-uid>"
      }
    ]
  }
}'
```

> 이걸 안 걸면 클러스터를 지우고 다시 만들 때 **옛 `AddonInstall`이 살아남아** 새 클러스터에 의도치 않게 매칭될 수 있습니다. 실습 환경에서 클러스터를 반복 생성한다면 반드시 처리하세요.

### Step 2. `AddonConfig`로 기본값 덮어쓰기 (선택)

기본값을 그대로 쓸 거면 건너뛰어도 됩니다. MTU나 Hubble을 손대려면 만듭니다.

| 값 경로 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `MTU` | integer | `0` | 파드 인터페이스 MTU |
| `hubble.enabled` | boolean | `true` | Hubble eBPF 관측 계층 |
| `hubble.relay.enabled` | boolean | `false` | 플로우 집계용 Hubble Relay 배포 |
| `hubble.ui.enabled` | boolean | `false` | Hubble UI 대시보드 (**Relay 필요**) |
| `hubble.ui.service.type` | string | `ClusterIP` | UI 서비스 타입 (ClusterIP / NodePort / LoadBalancer) |

```yaml
apiVersion: addons.kubernetes.vmware.com/v1alpha1
kind: AddonConfig
metadata:
  name: <cluster-name>-cilium
  namespace: <cluster-namespace>
spec:
  values:
    hubble:
      enabled: true
      relay:
        enabled: true
      ui:
        enabled: true
        service:
          type: ClusterIP
```

`AddonConfig`도 클러스터와 함께 삭제되지 않습니다. 같이 지우려면 다음 어노테이션을 답니다. 🅑

```yaml
metadata:
  annotations:
    clusteraddon.addons.kubernetes.vmware.com/owned-for-deletion: "true"
```

> `AddonConfig`는 **클러스터 생성 전에 미리** 만들어도 되고, 생성 후에 수정해도 됩니다. Hubble을 나중에 켜는 시나리오가 여기에 해당합니다.

### Step 3. `bootstrapAddons` 변수로 CNI를 Cilium으로 선택

```yaml
# Cluster 리소스의 spec.topology.variables 에 추가
- name: bootstrapAddons
  value:
    cniRef:
      name: cilium
      namespace: vmware-system-vks-public
```

- 변수 도입: VKS **3.6.0** · K8s **1.35 이상에서만** 지원 🅑
- 적용 범위(Supported Scopes): `cluster`, `controlPlane` 🅑
- `cniRef.namespace`를 생략하면 애드온 매니저의 기본 public 네임스페이스를 씁니다 🅑
- 이 변수는 **초기 부트스트랩 단계**에 쓰입니다. 즉 클러스터를 만들기 전에 YAML에 들어 있어야 합니다 🅑

> 📌 **구형 방식은 폐기됐습니다.** `ClusterBootstrap`의 `cni` 필드와 `AntreaConfig`/`CalicoConfig`는 VKr 1.35+에서 `bootstrapAddons` + `AddonConfig`로 대체되며 자동 마이그레이션됩니다. 예전 블로그·문서를 따라가다 여기서 막히는 경우가 많습니다. 🅑
>
> 🆕 **VKS 3.8 (2026-11-03 확인, VKS 3.8 Release Notes):** VKr **1.37 이상**에서는 `ClusterBootstrap`·`ClusterBootstrapTemplate`·`KappControllerConfig`·`VSphereCSIConfig`·`VSphereCPIConfig` 가 **무시되고, `ClusterBootstrap` 생성 자체가 막힙니다.** 코어 애드온(CNI 포함)의 사용자 설정은 스키마 검증되는 `AddonConfig`(`addons.kubernetes.vmware.com/v1alpha1`)로만 합니다. vCenter UI의 Supervisor → Configure → **Default CNI** 메뉴도 9.x vCenter에서 사라집니다. 🅑

### Step 4. 방화벽 규칙 — 4개 포트

Cilium은 VXLAN 캡슐화, 헬스체크, Hubble 관측을 위해 노드 간 특정 포트가 열려 있어야 합니다. 🅑

| 포트 | 프로토콜 | 용도 | 컨트롤 플레인 | 워커 |
|---|---|---|---|---|
| 2379–2380 | TCP | etcd 클라이언트·피어 통신 | ✅ | — |
| 8472 | UDP | VXLAN 터널 캡슐화 | ✅ | ✅ |
| 4240 | TCP | Cilium 에이전트 헬스체크 | ✅ | ✅ |
| 4244 | TCP | **Hubble 서버** | ✅ | ✅ |

VKS 3.6부터 인바운드 방화벽에 일관된 API(`node.firewall.inboundRules`)가 생겼습니다. 컨트롤 플레인은 `spec.topology.variables`에, 워커는 각 `machineDeployment`의 **variable override**에 넣습니다.

```yaml
# 컨트롤 플레인 — spec.topology.variables
- name: node
  value:
    firewall:
      inboundRules:
        - fromPort: 2379
          protocol: tcp
          toPort: 2380
        - fromPort: 8472
          protocol: udp
          toPort: 8472
        - fromPort: 4240
          protocol: tcp
          toPort: 4240
        - fromPort: 4244
          protocol: tcp
          toPort: 4244
```

```yaml
# 워커 — spec.topology.workers.machineDeployments[].variables.overrides
workers:
  machineDeployments:
    - class: node-pool
      name: node-pool-1
      replicas: 1
      variables:
        overrides:
          - name: node
            value:
              firewall:
                inboundRules:
                  - fromPort: 8472
                    protocol: udp
                    toPort: 8472
                  - fromPort: 4240
                    protocol: tcp
                    toPort: 4240
                  - fromPort: 4244
                    protocol: tcp
                    toPort: 4244
```

`inboundRules` 필드 스펙 🅑

| 필드 | 필수 | 설명 |
|---|---|---|
| `protocol` | ✅ | `tcp`, `udp`, `icmp` 또는 유효한 IANA 프로토콜 번호 |
| `fromPort` | — | 포트 범위 시작(포함) |
| `toPort` | — | 포트 범위 끝(포함) |
| `source` | — | 출발지 CIDR. 미지정 시 모든 출발지 |

> 여기 정의한 규칙은 **클러스터 정상 동작에 필요한 기본 규칙과 병합**됩니다. 기본 규칙을 지우는 게 아니라 얹는 것입니다. 🅑

---

## 5. kube-proxy 없이 돌리기 (kube-proxy-free)

Cilium의 eBPF 서비스 구현으로 kube-proxy를 대체하는 구성입니다. VKS 3.7의 **kube-proxy 비활성화 API**가 이걸 위해 들어왔습니다. 🅑

```yaml
# spec.topology.variables
- name: kubernetes
  value:
    kubeProxyConfiguration:
      enabled: false
```

### 스펙과 제약 🅑

| 항목 | 값 |
|---|---|
| 변수 도입 | `kubeProxyConfiguration` 3.6.0 / `enabled` 필드 **3.7.0** |
| 적용 범위 | **`cluster` 스코프만** (컨트롤 플레인·워커 override 불가) |
| 변경 가능성 | **immutable** — 검증 규칙에 명시 |
| 변경 영향 | 머신 롤아웃 필요 |
| CNI 제약 | **Antrea·KR 내장 Calico에서는 미지원.** 커스텀 CNI에서 쓰려면 **KR 1.35 이상** |
| 클러스터 | 신규 클러스터 대상 |

### 🔴 알려진 문제 — 「비활성화로 보이는데 계속 동작한다」

클러스터 **생성 시** `kubernetes.kubeProxyConfiguration`을 명시하지 않으면, 생성 후에 `enabled` 플래그를 `false`로 바꾸는 것이 허용됩니다. 그런데 실제 kube-proxy는 계속 동작해서 **상태 표시와 실제 동작이 어긋납니다.** 🅑

> **워크어라운드:** kube-proxy 활성/비활성은 **반드시 클러스터 생성 시점에 명시적으로 설정**하고, 생성 후에는 바꾸지 마세요.
>
> 교훈으로 옮기면 — 「상태 칸이 초록인데 동작이 다르다」는 보고가 오면, 그 값이 **생성 시점에 박힌 값인지 사후에 바뀐 값인지**부터 가르세요.

### kube-proxy 비활성화가 전제인 Cilium 고급 기능 🅑

Cilium 1.19.4의 아래 기능들은 **kube-proxy가 켜져 있으면 검증 오류가 납니다.**

- L7 프록시 (Envoy 기반 L7 정책)
- Ingress 컨트롤러
- Egress Gateway (SNAT)
- Gateway API 컨트롤러
- eBPF 마스커레이딩

즉 「Cilium의 좋은 기능을 쓰고 싶다」는 요구는 곧 **「클러스터를 만들 때 kube-proxy를 끄고 시작해야 한다」**는 설계 결정입니다. 나중에 못 바꾸는 값이므로 **클러스터 생성 계획 단계에서 결론을 내세요.**

---

## 6. 검증 절차

### 6-1. 애드온·파드 상태 🅑 + 🅞

```bash
# Supervisor 쪽
kubectl get addoninstall <cluster-name>-cilium -n <cluster-namespace>
kubectl get clusteraddon -n <cluster-namespace>

# 워크로드 클러스터 쪽
kubectl get pods -n kube-system -l k8s-app=cilium
kubectl get daemonset -n kube-system cilium
```

### 6-2. kube-proxy가 정말 없는지 🅞

```bash
kubectl get ds -n kube-system kube-proxy     # 없어야 정상
kubectl -n kube-system exec ds/cilium -- cilium-dbg status | grep -i kubeproxy
```

> 🔑 **설정값이 아니라 동작을 재세요.** `kubeProxyConfiguration.enabled: false`가 YAML에 있다는 건 「그렇게 요청했다」는 뜻이고, DaemonSet이 없고 Cilium이 KubeProxyReplacement를 보고하는 게 「그렇게 됐다」는 뜻입니다. 위 알려진 문제가 정확히 이 둘이 갈라지는 자리입니다.

### 6-3. 노드 간 통신 실동작

방화벽 4개 포트가 실제로 열렸는지는 **파드를 띄워서** 확인합니다. 노드 A의 파드에서 노드 B의 파드로 통신이 되는지, `cilium-health` 상태가 모든 노드에서 ok인지 보세요. 🅞

---

## 7. 알려진 문제 · 비호환 🅑

| 증상 | 원인 | 대응 |
|---|---|---|
| **혼합 OS 클러스터가 Ready 안 됨** | Cilium이 **Windows를 지원하지 않아** Windows 워커가 Not Ready로 남음 | Windows 워커가 필요하면 다른 CNI를 쓰고, Cilium을 써야 하면 **Linux(Photon OS) 워커로만** 구성 |
| **Istio 애드온 설치 실패** | 현재 Cilium 애드온 버전의 제약으로 **Istio 애드온과 Cilium CNI가 비호환** | 서비스 메시가 필수면 CNI 선택을 다시 검토. Cilium 자체의 L7 프록시·Gateway API 컨트롤러가 일부를 대체할 수 있으나 동등물은 아님 |
| kube-proxy 상태 불일치 | 생성 후 플래그 변경 허용 | 생성 시점에 명시 (5절 참조) |
| 업그레이드 중 멈춤 (VKS 3.7 이하) | 이전 VKr에서 남은 Antrea/Calico 고아 `AddonRelease`가 같은 버전으로 겹쳐 잘못된 쪽이 선택됨 | **VKS 3.8.0에서 수정** 🅑 (2026-11-03 확인). CNI를 바꿔 온 클러스터라면 3.8 이전엔 고아 리소스부터 확인 |

> 🔄 **2026-11-03 재확인 (VKS 3.8 Release Notes):** 혼합 OS(Windows 워커) + Cilium 비호환은 3.8 알려진 문제에 **그대로 남아 있습니다.** Istio 비호환은 3.8 VKS 릴리스 노트 본문에서 찾지 못했습니다(애드온 릴리스 노트 쪽 확인 전까지 ❓ 미결로 둡니다).

> ⚠️ **워커 노드 보조 NIC도 Windows 미지원**입니다. Cilium + Multus + Windows를 한 클러스터에 넣으려는 설계는 두 군데서 막힙니다.

---

## 8. 설계 체크리스트 — 클러스터를 만들기 전에 답할 것

클러스터 생성 후에는 못 바꾸거나 롤아웃을 유발하는 항목들입니다.

- [ ] **Ecosystem 티어의 지원 범위**를 이해하고 수용했는가 (런타임 문제 미지원)
- [ ] VKS 3.6+ / VKr 1.35+ 인가
- [ ] 애드온 저장소 **v3.6.0+20260320 이상**이 Supervisor에 설치돼 있는가
- [ ] **kube-proxy를 끌 것인가** — immutable, 생성 시점 결정 🔴
- [ ] 쓰려는 Cilium 고급 기능이 kube-proxy 비활성화를 요구하는가
- [ ] 방화벽 **4개 포트**(2379-2380 / 8472 / 4240 / 4244)를 CP·워커에 각각 넣었는가
- [ ] `AddonInstall`·`AddonConfig`에 **ownerReference / owned-for-deletion**을 걸었는가
- [ ] **Windows 워커가 필요한가** — 필요하면 Cilium 불가
- [ ] **Istio 애드온이 필요한가** — 필요하면 Cilium 불가
- [ ] Hubble을 켤 것인가 → `VKS_Cilium_Hubble_KR.md`

---

## 9. 다음 문서

- **`VKS_Cilium_Hubble_KR.md`** — Hubble Relay/UI 연동, 플로우 관측, 메트릭
- **`VKS_Multus_MultiNIC_KR.md`** — 노드 보조 NIC · Multus/Whereabouts · SR-IOV 멀티 NIC 파드
- `VKS_3.6_Release_Notes_KR.md` / `VKS_3.7_Release_Notes_KR.md` / `VKS_Addons_Release_Notes_KR.md` — 이 문서의 1차 출처

---

_출처: Broadcom TechDocs (Create a VKS Cluster Using the Cilium CNI Add-On Package, Managing Add-ons in VKS Clusters, ClusterClass Variable Reference), VKS 3.6/3.7 Release Notes, VKS Standard Packages Release Notes. 본 자료는 공개 문서 기반 학습용 정리이며, 실제 배포 전에는 해당 릴리스의 공식 문서를 다시 확인하세요._
