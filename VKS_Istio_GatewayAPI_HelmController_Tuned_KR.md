# Istio && Gateway API && Helm Controller (Tuned Configuration)

Istio Service Mesh를 Helm 기반으로 설치하고, Kubernetes Gateway API로 트래픽을 노출하며,
Flux Helm Controller를 통해 선언적으로 관리하는 방법을 정리합니다.
마지막 장에는 운영 환경을 위한 튜닝(Tuned) 구성 방법을 포함합니다.

관련 매니페스트는 `manifests/istio/` 디렉토리를 참조하세요.

---

## 1. 사전 준비 (Prerequisites)

```
# Kubernetes 1.27+ 클러스터 및 kubectl / helm 필요
[root@pkyungjin-k8s-master home]# kubectl version --short
[root@pkyungjin-k8s-master home]# helm version

# Helm 미설치 시
[root@pkyungjin-k8s-master home]# curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### 1-1. Gateway API CRD 설치

Gateway API는 Ingress의 후속 표준 API로, CRD를 먼저 설치해야 합니다.

```
# Gateway API v1.2.1 Standard Channel CRD 설치
[root@pkyungjin-k8s-master home]# kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.1/standard-install.yaml

# 설치 확인
[root@pkyungjin-k8s-master home]# kubectl get crd | grep gateway
gatewayclasses.gateway.networking.k8s.io
gateways.gateway.networking.k8s.io
grpcroutes.gateway.networking.k8s.io
httproutes.gateway.networking.k8s.io
referencegrants.gateway.networking.k8s.io
```

> **참고**: TLSRoute, TCPRoute 등 실험적 기능이 필요하면 `experimental-install.yaml`을 사용합니다.

---

## 2. Istio 설치 (Helm 기반)

Istio는 `base`(CRD), `istiod`(Control Plane), `gateway`(Data Plane Ingress) 3개의 차트로 구성됩니다.

### 2-1. Helm Repository 등록

```
[root@pkyungjin-k8s-master home]# helm repo add istio https://istio-release.storage.googleapis.com/charts
[root@pkyungjin-k8s-master home]# helm repo update

# 사용 가능한 버전 확인
[root@pkyungjin-k8s-master home]# helm search repo istio
```

### 2-2. istio-base 설치 (CRD)

```
[root@pkyungjin-k8s-master home]# kubectl create namespace istio-system

[root@pkyungjin-k8s-master home]# helm install istio-base istio/base \
  -n istio-system \
  --version 1.24.2 \
  --set defaultRevision=default
```

### 2-3. istiod 설치 (Control Plane) — 튜닝 values 적용

```
# manifests/istio/istiod-values.yaml 은 4장의 튜닝 항목이 반영된 values 파일입니다
[root@pkyungjin-k8s-master home]# helm install istiod istio/istiod \
  -n istio-system \
  --version 1.24.2 \
  -f manifests/istio/istiod-values.yaml \
  --wait

# 설치 확인
[root@pkyungjin-k8s-master home]# kubectl get pods -n istio-system
NAME                      READY   STATUS    RESTARTS   AGE
istiod-6d9f7c5b8d-x2k4p   1/1     Running   0          1m
```

### 2-4. Ingress Gateway 설치

Gateway API를 사용하는 경우 별도의 gateway 차트 설치 없이 `Gateway` 리소스 생성 시
Istio가 자동으로 Deployment/Service를 배포합니다(Automated Deployment).
전통적인 Istio Gateway(VirtualService) 방식을 쓸 경우에만 아래를 설치합니다.

```
# (선택) 전통적인 istio-ingressgateway 방식
[root@pkyungjin-k8s-master home]# kubectl create namespace istio-ingress

[root@pkyungjin-k8s-master home]# helm install istio-ingress istio/gateway \
  -n istio-ingress \
  --version 1.24.2 \
  -f manifests/istio/gateway-values.yaml \
  --wait
```

### 2-5. Sidecar Injection 활성화

```
# 워크로드 네임스페이스에 라벨 부여
[root@pkyungjin-k8s-master home]# kubectl create namespace demo
[root@pkyungjin-k8s-master home]# kubectl label namespace demo istio-injection=enabled

# 확인
[root@pkyungjin-k8s-master home]# kubectl get namespace -L istio-injection
NAME           STATUS   AGE   ISTIO-INJECTION
demo           Active   1m    enabled
istio-system   Active   5m
```

---

## 3. Gateway API로 서비스 노출

### 3-1. 테스트 애플리케이션 배포

```
[root@pkyungjin-k8s-master home]# kubectl apply -n demo -f https://raw.githubusercontent.com/istio/istio/release-1.24/samples/httpbin/httpbin.yaml
```

### 3-2. Gateway && HTTPRoute 생성

`manifests/istio/gateway.yaml` — Gateway 리소스 (LoadBalancer 자동 생성):

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: demo-gateway
  namespace: demo
spec:
  gatewayClassName: istio
  listeners:
  - name: http
    port: 80
    protocol: HTTP
    allowedRoutes:
      namespaces:
        from: Same
```

`manifests/istio/httproute.yaml` — HTTPRoute 리소스:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: httpbin-route
  namespace: demo
spec:
  parentRefs:
  - name: demo-gateway
  hostnames:
  - "httpbin.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: httpbin
      port: 8000
```

```
[root@pkyungjin-k8s-master home]# kubectl apply -f manifests/istio/gateway.yaml
[root@pkyungjin-k8s-master home]# kubectl apply -f manifests/istio/httproute.yaml

# Gateway 상태 및 External IP 확인
[root@pkyungjin-k8s-master home]# kubectl get gateway -n demo
NAME           CLASS   ADDRESS          PROGRAMMED   AGE
demo-gateway   istio   192.168.70.100   True         1m

# 라우팅 테스트
[root@pkyungjin-k8s-master home]# curl -s -H "Host: httpbin.example.com" http://192.168.70.100/get
```

### 3-3. 트래픽 분할 (Canary) 예시

Gateway API는 `backendRefs`의 `weight` 필드로 가중치 기반 트래픽 분할을 지원합니다.

```yaml
    backendRefs:
    - name: httpbin-v1
      port: 8000
      weight: 90
    - name: httpbin-v2
      port: 8000
      weight: 10
```

---

## 4. 운영 환경 Tuned 구성 (Production Tuning)

`manifests/istio/istiod-values.yaml`, `manifests/istio/gateway-values.yaml`에 반영된 튜닝 포인트입니다.

### 4-1. Control Plane (istiod) 튜닝

| 항목 | 기본값 | 튜닝값 | 목적 |
|---|---|---|---|
| replicaCount | 1 | 2 | Control Plane 고가용성 |
| HPA | 1~5 | 2~5 (CPU 80%) | 부하 시 자동 확장 |
| resources.requests | 500m/2Gi | 500m/2Gi + limits 명시 | 노드 리소스 보호 |
| PDB | 활성 | 활성 (minAvailable 1) | 노드 드레인 시 가용성 보장 |

### 4-2. Sidecar Proxy 튜닝

```yaml
# istiod-values.yaml 발췌
global:
  proxy:
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: "2"
        memory: 1Gi
```

- **concurrency: 2** — Envoy Worker Thread 수 제한 (기본값은 CPU 코어 수만큼 생성되어 과도한 메모리 사용)
- **holdApplicationUntilProxyStarts: true** — 사이드카가 준비되기 전 앱 컨테이너 시작으로 인한 초기 요청 실패 방지

### 4-3. 트레이싱 샘플링 비율 조정

```yaml
meshConfig:
  defaultConfig:
    tracing:
      sampling: 1.0   # 운영: 1% (기본 100%는 오버헤드 큼)
```

### 4-4. Sidecar 리소스 스코프 제한

기본적으로 모든 사이드카는 메시 전체의 서비스 정보를 수신하여 메모리를 낭비합니다.
네임스페이스 단위 `Sidecar` 리소스로 xDS 푸시 범위를 제한합니다 (`manifests/istio/sidecar-scope.yaml`).

```yaml
apiVersion: networking.istio.io/v1
kind: Sidecar
metadata:
  name: default
  namespace: demo
spec:
  egress:
  - hosts:
    - "./*"              # 같은 네임스페이스
    - "istio-system/*"   # Control Plane
```

> 대규모 클러스터에서 사이드카 메모리 사용량과 istiod xDS 푸시 부하를 크게 줄이는 핵심 튜닝입니다.

### 4-5. Gateway (Data Plane) 튜닝

```yaml
# gateway-values.yaml 발췌
autoscaling:
  enabled: true
  minReplicas: 2        # 단일 장애점 제거
  maxReplicas: 5
  targetCPUUtilizationPercentage: 80
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: "2"
    memory: 1Gi
podDisruptionBudget:
  minAvailable: 1
```

### 4-6. mTLS 강제 (보안 튜닝)

```
# 메시 전체 STRICT mTLS 적용 (manifests/istio/peer-authentication.yaml)
[root@pkyungjin-k8s-master home]# kubectl apply -f manifests/istio/peer-authentication.yaml
```

---

## 5. Helm Controller를 통한 선언적 관리 (GitOps)

Flux의 `source-controller` + `helm-controller`를 사용하면 위의 Helm 설치 과정을
`HelmRepository` / `HelmRelease` CR로 선언적으로 관리할 수 있습니다.
(수동 `helm install/upgrade` 없이 컨트롤러가 상태를 지속적으로 조정 — drift 자동 복구)

### 5-1. Helm Controller 설치

```
# Flux CLI 설치
[root@pkyungjin-k8s-master home]# curl -s https://fluxcd.io/install.sh | bash

# source-controller + helm-controller만 설치 (전체 GitOps 스택 불필요 시)
[root@pkyungjin-k8s-master home]# flux install --components=source-controller,helm-controller

# 확인
[root@pkyungjin-k8s-master home]# kubectl get pods -n flux-system
NAME                                 READY   STATUS    RESTARTS   AGE
helm-controller-5f7c8d9b6d-abcde     1/1     Running   0          1m
source-controller-7d6b8f9c5d-fghij   1/1     Running   0          1m
```

### 5-2. HelmRepository && HelmRelease 생성

`manifests/istio/helmrepository-istio.yaml` — 차트 소스 정의:

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: istio
  namespace: flux-system
spec:
  interval: 1h
  url: https://istio-release.storage.googleapis.com/charts
```

`manifests/istio/helmrelease-istiod.yaml` — 릴리스 정의 (버전 고정 + 자동 복구):

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: istiod
  namespace: istio-system
spec:
  interval: 10m
  dependsOn:
  - name: istio-base
  chart:
    spec:
      chart: istiod
      version: "1.24.2"        # 버전 고정 (의도치 않은 업그레이드 방지)
      sourceRef:
        kind: HelmRepository
        name: istio
        namespace: flux-system
  install:
    remediation:
      retries: 3
  upgrade:
    remediation:
      retries: 3
      remediateLastFailure: true
  values:
    pilot:
      replicaCount: 2
```

```
[root@pkyungjin-k8s-master home]# kubectl apply -f manifests/istio/helmrepository-istio.yaml
[root@pkyungjin-k8s-master home]# kubectl apply -f manifests/istio/helmrelease-base.yaml
[root@pkyungjin-k8s-master home]# kubectl apply -f manifests/istio/helmrelease-istiod.yaml

# 릴리스 상태 확인
[root@pkyungjin-k8s-master home]# kubectl get helmrelease -n istio-system
NAME         AGE   READY   STATUS
istio-base   2m    True    Helm install succeeded
istiod       1m    True    Helm install succeeded
```

> **참고 (Tanzu)**: TKG 환경에서는 kapp-controller(Carvel) 기반 Package가 기본 패키지 관리
> 방식이며, Flux Helm Controller는 TKG 2.x부터 `fluxcd-helm-controller` 표준 패키지로도
> 설치할 수 있습니다: `tanzu package install fluxcd-helm-controller -p fluxcd-helm-controller.tanzu.vmware.com`

### 5-3. 업그레이드 && 롤백

```
# 업그레이드: HelmRelease의 version 필드 수정 후 apply (컨트롤러가 자동 수행)
# 강제 reconcile
[root@pkyungjin-k8s-master home]# flux reconcile helmrelease istiod -n istio-system

# 릴리스 히스토리 확인 (helm CLI와 호환)
[root@pkyungjin-k8s-master home]# helm history istiod -n istio-system
```

---

## 6. 검증 && 트러블슈팅

```
# istioctl 설치
[root@pkyungjin-k8s-master home]# curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.24.2 sh -
[root@pkyungjin-k8s-master home]# install istio-1.24.2/bin/istioctl /usr/bin/istioctl

# 메시 전체 구성 검증
[root@pkyungjin-k8s-master home]# istioctl analyze -A

# 프록시 동기화 상태 확인
[root@pkyungjin-k8s-master home]# istioctl proxy-status

# 특정 Pod의 mTLS / 라우팅 설정 확인
[root@pkyungjin-k8s-master home]# istioctl x describe pod <pod-name> -n demo
```

| 증상 | 확인 포인트 |
|---|---|
| Gateway PROGRAMMED=False | GatewayClass `istio` 존재 여부, istiod 로그 |
| HTTPRoute 미동작 | `kubectl get httproute -o yaml`의 status.conditions (Accepted/ResolvedRefs) |
| 503 응답 | 사이드카 주입 여부, PeerAuthentication STRICT 시 미주입 워크로드 통신 차단 |
| 사이드카 OOMKilled | Sidecar 리소스로 스코프 제한(4-4), proxy memory limit 상향 |
