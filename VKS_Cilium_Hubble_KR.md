# VKS Hubble 연동 가이드 — Cilium 관측성

> 대상: VKS 플랫폼·운영 엔지니어
> 정리일: 2026-09-22
> 기준: VKS 3.6 / 3.7, Cilium 애드온 1.19.1 ~ 1.19.4
> 선행 문서: **`VKS_Cilium_CNI_KR.md`** — Cilium CNI가 이미 설치된 클러스터를 전제로 합니다

## 📑 근거 등급 표기

| 표기 | 의미 |
|---|---|
| 🅑 | Broadcom 공식 문서·릴리스 노트에 명시 |
| 🅞 | Cilium 업스트림 일반 지식 — VKS 애드온에서 노출 여부·값이 다를 수 있음 |
| ❓ | 확인이 필요한 미결 항목 |

> 🔴 **이 문서에서 가장 중요한 경계입니다.** VKS의 `AddonConfig`는 **미리 정의된 스키마(`AddonConfigDefinition`)로 검증**됩니다 🅑. 즉 업스트림 Cilium Helm 차트의 모든 값을 그대로 넣을 수 있다고 가정하면 안 됩니다. 공식 문서가 표로 밝힌 값은 4개뿐이고(2절), 그 밖의 값은 **환경에서 실제로 적용되는지 확인한 뒤** 쓰세요.

---

## 1. Hubble이란 — 3층 구조로 이해하기

Hubble은 Cilium의 eBPF 데이터플레인 위에 얹히는 관측 계층입니다. 애플리케이션 코드나 사이드카 없이, 커널에서 본 플로우를 그대로 올려 줍니다. 🅞

```
┌──────────────────────────────────────────────┐
│  Hubble UI            웹 대시보드 · 서비스 맵   │  ← relay 필요
├──────────────────────────────────────────────┤
│  Hubble Relay         클러스터 전체 플로우 집계  │  ← 노드별 서버를 한 엔드포인트로
├──────────────────────────────────────────────┤
│  Hubble Server        노드마다 · TCP 4244      │  ← cilium-agent 안에 내장
├──────────────────────────────────────────────┤
│  eBPF 데이터플레인 (cilium-agent)               │
└──────────────────────────────────────────────┘
```

| 계층 | 범위 | 기본값 (VKS AddonConfig) |
|---|---|---|
| **Hubble Server** | 노드 1대 | `hubble.enabled: true` — **기본으로 켜져 있음** 🅑 |
| **Hubble Relay** | 클러스터 전체 | `hubble.relay.enabled: false` — **꺼져 있음** 🅑 |
| **Hubble UI** | 클러스터 전체 | `hubble.ui.enabled: false` — **꺼져 있음**, Relay 필요 🅑 |

> 💡 **여기서 오해가 자주 납니다.** Cilium을 깔면 `hubble.enabled`가 기본 `true`라 「Hubble이 켜져 있다」고 읽기 쉽습니다. 하지만 그건 **노드 단위 서버**만 돌고 있다는 뜻이고, 클러스터 전체를 한눈에 보는 경험(Relay·UI)은 **명시적으로 켜야** 생깁니다.

---

## 2. 연동 방법 — `AddonConfig` 하나로 켠다 🅑

### 2-1. 설정 가능한 값 (공식 문서 명시)

| 값 경로 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `MTU` | integer | `0` | 파드 인터페이스 MTU (Hubble과 무관하지만 같은 스키마에 있음) |
| `hubble.enabled` | boolean | `true` | Hubble eBPF 관측 계층 활성화 |
| `hubble.relay.enabled` | boolean | `false` | 플로우 집계용 **Hubble Relay 배포** |
| `hubble.ui.enabled` | boolean | `false` | **Hubble UI 웹 대시보드 배포** (Relay 필요) |
| `hubble.ui.service.type` | string | `ClusterIP` | UI 서비스 타입 — `ClusterIP` / `NodePort` / `LoadBalancer` |

### 2-2. Relay + UI 켜기

```yaml
apiVersion: addons.kubernetes.vmware.com/v1alpha1
kind: AddonConfig
metadata:
  name: <cluster-name>-cilium
  namespace: <cluster-namespace>
  annotations:
    # 클러스터 삭제 시 이 AddonConfig도 함께 지우려면 (권장)
    clusteraddon.addons.kubernetes.vmware.com/owned-for-deletion: "true"
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

이 리소스는 **Supervisor의 클러스터 네임스페이스**에 만듭니다. 🅑

### 2-3. 적용 시점 — 두 갈래 🅑

| 시점 | 방법 | 비고 |
|---|---|---|
| **클러스터 생성 전** | `AddonConfig`를 클러스터 네임스페이스에 미리 생성 | 처음부터 Relay·UI가 붙은 상태로 프로비저닝 |
| **클러스터 생성 후** | 기존 `AddonConfig` 수정 (없으면 새로 생성) | Hubble을 나중에 켜는 시나리오 |

> `kubeProxyConfiguration`처럼 immutable한 값과 달리, **Hubble은 사후에 켜고 끌 수 있습니다.** 「일단 Cilium만 올리고 관측은 나중에」가 가능한 구조입니다.

### 2-4. 🔴 방화벽 — 4244/TCP가 없으면 Relay가 아무것도 못 본다

Cilium 설치 시 여는 4개 포트 중 **TCP 4244가 Hubble 서버**입니다. 🅑

| 포트 | 프로토콜 | 용도 | CP | 워커 |
|---|---|---|---|---|
| 4244 | TCP | **Hubble 서버** | ✅ | ✅ |

Relay는 각 노드의 4244로 붙어 플로우를 끌어옵니다. 이 포트를 워커 `machineDeployment` override에 안 넣으면, **Relay 파드는 Running인데 플로우가 안 보이는** 상태가 됩니다. Cilium 설치 단계에서 이미 넣었다면 추가 작업이 없고, Hubble을 나중에 켠다면 **방화벽 변수부터 확인**하세요.

```yaml
# 워커 machineDeployment override — Hubble 서버 포트
- name: node
  value:
    firewall:
      inboundRules:
        - fromPort: 4244
          protocol: tcp
          toPort: 4244
```

⚠️ `node` 변수 변경은 **머신 롤아웃을 유발**합니다. 나중에 방화벽만 고치는 일이 생기지 않도록, **Cilium 설치 단계에서 4개 포트를 한꺼번에** 넣어 두는 편이 낫습니다. 🅑

---

## 3. 접근 방법

### 3-1. Hubble UI 열기

`hubble.ui.service.type`을 무엇으로 뒀느냐에 따라 갈립니다.

**ClusterIP (기본·가장 안전)** — 포트포워딩으로 접근 🅞

```bash
kubectl port-forward -n kube-system svc/hubble-ui 12000:80
# 브라우저에서 http://localhost:12000
```

**NodePort / LoadBalancer** — 클러스터 밖에서 직접 접근 🅑

```yaml
spec:
  values:
    hubble:
      ui:
        service:
          type: LoadBalancer
```

> 🔴 **LoadBalancer를 고르기 전에 두 가지를 보세요.**
> 1. 그 환경에 LB가 있어야 합니다(NSX / Avi). LB가 없으면 Service가 영원히 `Pending`입니다. 참고로 VKS의 Prometheus 애드온이 **LB 없는 환경을 위해 NodePort 노출을 추가**한 것도 같은 맥락입니다 🅑
> 2. **Hubble UI에는 인증이 없습니다** 🅞. LoadBalancer로 열면 네트워크에 닿는 누구나 클러스터 전체의 통신 그래프를 봅니다. 프로덕션에서는 ClusterIP + 포트포워딩이나, 앞단에 인증을 세우는 구성을 쓰세요.
>
> ⚠️ **보조 NIC에는 LoadBalancer 서비스를 못 붙입니다.** Service type LoadBalancer는 **항상 primary 네트워크**에 프로비저닝됩니다 🅑. 「관리망 분리했으니 Hubble UI는 eth1에」 같은 설계는 현재 불가능합니다.

### 3-2. Hubble CLI로 플로우 보기 🅞

```bash
# Relay에 포트포워딩
kubectl port-forward -n kube-system svc/hubble-relay 4245:80

# 실시간 플로우
hubble observe --server localhost:4245 -f

# 드롭된 패킷만
hubble observe --server localhost:4245 --verdict DROPPED

# 특정 네임스페이스
hubble observe --server localhost:4245 --namespace my-app

# 상태 확인
hubble status --server localhost:4245
```

> 🅞 위 명령들은 **업스트림 Cilium/Hubble CLI** 사용법입니다. VKS 애드온 배포에서 서비스 이름·포트가 그대로인지는 실제 클러스터에서 `kubectl get svc -n kube-system` 으로 먼저 확인하세요. 문서에 적힌 이름보다 **자기 클러스터가 내놓는 값이 정본**입니다.

### 3-3. 네트워크 정책 디버깅에 쓰기 🅞

Hubble의 실전 가치는 대시보드 구경이 아니라 **「왜 막혔는가」를 즉시 답하는 것**입니다.

```bash
# 정책 때문에 막힌 트래픽만
hubble observe --verdict DROPPED --type policy-verdict

# 특정 파드로 들어오는 트래픽
hubble observe --to-pod my-namespace/my-pod
```

`CiliumNetworkPolicy`(L7)를 쓰기 시작하면 「되던 게 안 된다」는 문의가 늘어납니다. 그때 **정책 판정(policy-verdict) 플로우**를 보여 주는 것이 Hubble을 켜는 실질적 이유입니다.

---

## 4. 메트릭 — Prometheus 연계 🅑

Cilium **1.19.4**(애드온 저장소 v3.7.0+20260618)에서 다음이 추가됐습니다.

- **Prometheus 메트릭** — cilium-agent / cilium-operator
- **Hubble 플로우 메트릭**

VKS에는 **Prometheus 애드온**이 있고, 3.7에서 **Prometheus Operator가 선택적 서브컴포넌트**로 제공됩니다(기본 비활성, `prometheus-operator: true`로 활성). 활성화하면 CRD 기반으로 `ServiceMonitor` / `PodMonitor` / `PrometheusRule`을 쓸 수 있습니다. 🅑

> ❓ **미결:** Hubble 메트릭을 켜는 값(업스트림의 `hubble.metrics.enabled` 계열)이 VKS `AddonConfig` 스키마에 노출되는지는 공식 문서의 설정 표(2-1)에 **없습니다.** 스키마 검증이 있는 구조라 임의의 Helm 값이 통과한다고 가정하면 안 됩니다.
>
> **확인 방법** — 실환경에서 `AddonConfigDefinition`의 스키마를 직접 읽으세요. 문서에 없는 값을 추측으로 넣지 말고, 스키마가 정본입니다.
> ```bash
> kubectl get addonconfigdefinition -n vmware-system-vks-public
> kubectl get addonconfigdefinition <name> -n vmware-system-vks-public -o yaml
> ```

---

## 5. 검증 절차

```bash
# 1) Hubble 관련 파드
kubectl get pods -n kube-system -l k8s-app=hubble-relay
kubectl get pods -n kube-system -l k8s-app=hubble-ui

# 2) 서비스와 실제 포트 (문서 말고 이 값이 정본)
kubectl get svc -n kube-system | grep hubble

# 3) Relay가 노드들을 실제로 보고 있는지
kubectl port-forward -n kube-system svc/hubble-relay 4245:80 &
hubble status --server localhost:4245
```

`hubble status`가 내놓는 **연결된 노드 수**를 클러스터의 실제 노드 수와 대 보세요. 🅞

> 🔑 **파드가 Running인 것은 「떴다」이지 「보고 있다」가 아닙니다.** 4244 방화벽이 일부 노드풀에만 열려 있으면 Relay는 정상 기동한 채로 **그 노드들의 플로우만 빠뜨립니다.** 이건 에러로 안 나타나고, 「어떤 트래픽이 안 보인다」는 형태로 나중에 발견됩니다. 그래서 노드 수 대조가 검증의 핵심입니다.

---

## 6. 운영 고려사항

| 항목 | 내용 | 등급 |
|---|---|---|
| **리소스 비용** | Relay·UI는 추가 파드입니다. 플로우 버퍼는 메모리를 씁니다 | 🅞 |
| **보존 기간** | Hubble은 기본적으로 **링 버퍼** — 장기 보관 도구가 아닙니다. 과거 사건을 조사하려면 메트릭·로그로 따로 내보내야 합니다 | 🅞 |
| **지원 티어** | Cilium은 **Ecosystem 티어** — 런타임 문제는 Broadcom 지원 범위 밖 | 🅑 |
| **UI 인증 없음** | 노출 방식을 보안 요구에 맞춰 결정 | 🅞 |
| **업그레이드** | 클러스터 업그레이드 전 VKS가 애드온 호환성 사전 점검을 돌립니다. 호환 릴리스가 없으면 **클러스터 업그레이드가 차단**됩니다 | 🅑 |

---

## 7. 체크리스트

- [ ] Cilium CNI가 이미 설치된 클러스터인가 (`VKS_Cilium_CNI_KR.md`)
- [ ] **TCP 4244**가 컨트롤 플레인·**워커 모두**에 열려 있는가
- [ ] `hubble.relay.enabled: true` — UI를 쓰려면 **필수**
- [ ] `hubble.ui.service.type`을 보안 요구에 맞게 골랐는가 (기본 ClusterIP 권장)
- [ ] LoadBalancer를 골랐다면 그 환경에 LB가 있는가
- [ ] `AddonConfig`에 `owned-for-deletion` 어노테이션을 걸었는가
- [ ] `hubble status`의 **연결 노드 수 = 실제 노드 수** 인가
- [ ] 메트릭이 필요하면 `AddonConfigDefinition` 스키마를 **직접 읽어** 확인했는가

---

_출처: Broadcom TechDocs (Create a VKS Cluster Using the Cilium CNI Add-On Package — AddonConfig 설정값·방화벽 포트, Managing Add-ons in VKS Clusters), VKS Standard Packages Release Notes (Cilium 1.19.1 / 1.19.4), VKS 3.7 Release Notes. 🅞 표기 항목은 Cilium 업스트림 일반 지식이며 VKS 애드온 배포에서 다를 수 있습니다._
