# VMware VKS Add-ons (구 Standard Packages) 릴리스 노트 — 한글 정리

> **원문:** [VKS Add-ons Release Notes (Broadcom TechDocs)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vks-addons-release-notes.html)
> **포함 릴리스:** v2025.6.17 → v3.7.0+20260618 (총 9개 릴리스)
> **정리일:** 2026-07-15

---

## 1. VKS Add-ons란?

VKS Add-ons는 vSphere Kubernetes Service(VKS) 클러스터의 핵심 기능을 확장하는 **검증된 소프트웨어 컴포넌트 모음**이다. vSphere Supervisor 환경에서 UI, CLI, API로 배포/관리/추적할 수 있다.

- **3.7.0 릴리스부터** 기존 "Core"/"Standard" 패키지 용어를 폐기하고 **통합 VKS Add-ons 프레임워크**로 공식 전환
- 지원 자격은 클러스터의 **VKr 버전 24개월 라이프사이클**에 엄격히 귀속
- 패키지 호환성은 Supervisor의 VKS 버전이 아니라 **클러스터의 Kubernetes(VKr) 버전** 기준

### 지원 티어 4단계

| 티어 | 소유/검증 | Broadcom 지원 범위 |
|---|---|---|
| **Product** | Broadcom 엔지니어링이 큐레이션·패키징·검증, VKS와 심층 통합 | 배포 + 라이프사이클 + **런타임 트러블슈팅까지 완전 지원** |
| **Partner** | ISV(독립 SW 벤더)가 큐레이션·검증 | 배포·라이프사이클 지원, 런타임 문제는 파트너로 에스컬레이션 |
| **Ecosystem** | Broadcom이 큐레이션한 OSS, 기본 인프라 호환성 검증 | 패키징·서명·라이프사이클 문제만. 런타임 버그/보안패치/기능요청은 업스트림 커뮤니티 |
| **Community** | 미검증/사용자 빌드 OSS | **공식 지원 없음** |

---

## 2. VKS Add-ons v3.7.0+20260618 (VKS 3.7 대응)

Standard Packages가 공식적으로 VKS Add-ons 프레임워크로 전환된 첫 릴리스.

- **아티팩트 전달:** 기존 배포 스크립트/에어갭 레지스트리 동기화/CI-CD 파이프라인 호환을 위해 레지스트리 엔드포인트 구조는 이번 사이클에서 변경 없음 — `projects.packages.broadcom.com/vsphere/supervisor/vks-standard-packages/3.7.0-20260618/vks-addons:3.7.0-20260618`
- AddonRepository YAML 구성 파일은 Broadcom Support Portal에서 다운로드
- VKS 3.7.0부터 **다중 AddonRepoInstall 등록 가능**
- **지원 K8s 버전:** v1.33 ~ v1.36

### 신규 애드온 3종 🆕
- **Multus 4.2.4** (Product) — 멀티 NIC
- **NFS Client 4.13.2** (Product) — NFS 기반 PV (CSI Provisioner 6.1.0 / Resizer 2.0.0 / Snapshotter 8.4.0 등 포함)
- **Whereabouts 0.9.3** (Product) — 클러스터 범위 IPAM
- **Headlamp 0.42.0** (Ecosystem) — K8s 대시보드. 애드온 설치 상태 기반 플러그인 자동 설치, artifactHub 외 소스에서 서드파티 플러그인 직접 설치, VKS 로고 적용, 디버그 이미지를 Photon 기반으로 교체, Prometheus 플러그인은 Prometheus 애드온 설치 여부에 따라 동적 배포

### 주요 업데이트
- **공통 변화:** 대부분의 애드온이 K8s v1.34+에서 **PriorityClass 설정 지원** + 취약점 수정(베이스 이미지/Go 의존성 범프)
- **Cilium 1.19.4** (Ecosystem) — 고급 기능 대거 추가: **L7 프록시**(Envoy 기반 L7 정책), **Ingress 컨트롤러**, **Egress Gateway**(SNAT), **Gateway API 컨트롤러**, **eBPF 마스커레이딩**, **XDP 로드밸런서 가속**, 정책 시행 모드 제어, Prometheus 메트릭(agent/operator), Hubble 플로우 메트릭. ⚠️ **L7 Proxy/Ingress/Egress Gateway/Gateway API/eBPF 마스커레이딩은 kube-proxy 비활성화 필수** (`kubernetes.kubeProxyConfiguration.enabled=false`) — 활성 상태로 켜면 검증 오류
- **AKO 2.2.1** — 1.13.4에서 직접 업그레이드 시 PVC 자동 생성/기본 StorageClass 사전 요건 주의
- **Cert Manager 1.20.2** — Gateway API 연계 ListenerSet 지원
- **Cluster Autoscaler 1.36.0** — K8s 1.36 지원
- **Istio 1.30.0** — Pilot 리소스 비활성화 옵션(`istio.pilot.ignoreResources`/`includeResources`, 멀티클러스터에선 불가), `istio-registry-creds` 내부 Secret 제거. 업그레이드 경로 주의: 1.27.8은 1.28.5/1.28.7로 먼저 올린 후 1.30.0으로
- **Prometheus 3.5.3** — NodePort 배포, Web-Config TLS, readiness/livenessProbe 커스터마이징, 커스텀 Alertmanager FQDN. 서브컴포넌트 대폭 범프 (Alertmanager 0.32.0, kube-state-metrics 2.18.0, Thanos 0.41.0 등)
- **Helm Controller 1.5.4** — Helm SDK v4로 업그레이드
- **Velero 1.18.1**, Harbor 2.15.1/2.14.4, Contour 1.33.4 (K8s 1.33~1.36 테스트), Fluent Bit 5.0.5, External DNS 0.21.0, Telegraf 1.38.4, Vault Injector 1.7.4, vSphere PV CSI Webhook 3.8.0, SR-IOV Plugin 3.11.0, Windows GMSA Webhook 0.13.0 등

### ⚠️ 알려진 문제
- **Gatekeeper 애드온이 배포된 클러스터는 업그레이드 전에 validating/mutating 웹훅을 수동으로 스케일다운 또는 임시 비활성화 필수** — 안 하면 클러스터 업그레이드가 차단될 수 있음 (KB 433183 참조)

---

## 3. VKS Standard Package v3.6.0+20260521

- **Gatekeeper 3.22.2 첫 릴리스** 🆕 — OPA Gatekeeper가 VKS 애드온으로 제공. validating/mutating 어드미션 웹훅 + Constraint 정책 지속 감사(audit). VKS 시스템 네임스페이스 보호 내장, 메인 웹훅은 `failurePolicy: Ignore`(Gatekeeper 장애가 워크로드를 막지 않도록). **정책은 프리로드되지 않음** — ConstraintTemplate/Constraint는 직접 적용. VKS cluster management(VCF Automation 9.0.1+)로 정책 관리 중이면 그 방식 유지 권장. 기존 OSS Gatekeeper 설치는 애드온 설치 전 제거 필수
- **Prometheus 3.5.2** — 커스텀 Alertmanager FQDN 지원, 취약점 수정
- 지원 K8s: v1.32 ~ v1.35

---

## 4. VKS Standard Packages v3.6.0+20260416

취약점 수정 중심 릴리스 (VKS 3.6.3의 내장 저장소가 이 버전).

- **Helm Controller 1.4.2 첫 릴리스** 🆕 (source-controller 1.7.0 포함) — Helm 차트 애드온 지원의 기반
- **Cert Manager 1.19.4** — CVE-2026-24051, CVE-2025-68121 수정
- **Istio 1.28.5** — primary-remote 멀티클러스터 모드에서 인증서가 원격 클러스터로 전파되지 않던 동기화 문제 해결
- 그 외 AKO 2.1.4, Contour 1.33.2, External-DNS 0.20.0, Fluent Bit 4.2.3, Harbor 2.14.3/2.13.5, Prometheus 3.5.1, Telegraf 1.37.3, Velero 1.17.2 등 전반적 버전 범프
- 제거된 패키지: Harbor 2.13.5+vmware.1-vks.1 (구버전)

---

## 5. VKS Standard Packages 3.6.0+20260320

- **Cilium 1.19.1 첫 릴리스** 🆕 (VKS의 대안 CNI로 공식 합류) — eBPF 데이터플레인, Hubble UI/Relay 관측성, K8s NetworkPolicy(L3/L4) + CiliumNetworkPolicy(L7). 사용 요건: 클러스터 생성 **전에** Standard Package 저장소 설치 + AddonInstall 리소스 수동 생성 + `bootstrapAddons` 변수를 cilium으로 설정 + 방화벽 규칙 구성 → 이후 클러스터 생성 시 애드온 컨트롤러가 자동 프로비저닝
- **Harbor 2.13.5 / 2.14.3** — audit log 보안 강화, 레지스트리 토큰 검증 개선, CVE 수정
- ⚠️ **알려진 문제:** **Istio 애드온은 Cilium CNI 클러스터와 비호환** — 현재 Cilium 애드온 버전의 제약으로 설치 실패

---

## 6. VKS Standard Packages 3.6.0+20260211 (VKS 3.6.0 대응)

- **Vault Injector 1.6.2 첫 릴리스** 🆕 — agent injector 설치 담당. Secret Store Supervisor와 통신해 VKS 클러스터 파드에 시크릿 주입. 게스트 클러스터 생성 시 자동 설치 지원
- **Prometheus 3.5.0+vmware.3** — **Prometheus Operator가 선택적 서브컴포넌트로 추가** (기본 비활성, `prometheus-operator: true`로 활성): CRD 기반 선언적 관리, ServiceMonitor/PodMonitor/PrometheusRule 지원, 자동 구성 리로드. 선택적 어드미션 웹훅(Cert-manager 필요, HA 지원). Thanos 0.40.0 추가
- **Istio 1.28.2** — Gateway Inference API Extension 스위치(`istio.enableGatewayAPIInference`, 기본 false), 멀티클러스터 구성 지원(multi-primary/primary-remote 사이드카 모드, ambient 모드는 미지원)
- **Harbor 2.14.2** — Ingress로 노출 시 ingress class name 구성, cert-manager CA issuer 설정 지원
- **AKO 2.1.3** — 커스텀 네임스페이스 배포 가능 (기존엔 avi-system 고정)
- **SR-IOV Plugin 3.11.0** — vhost-net 감지/프로비저닝 옵션 추가
- kapp 기반 구성 변경 자동 리로드가 AKO/Contour/Fluent Bit에 적용

---

## 7. VKS Standard Packages 3.5.0+20251218

- **AKO 2.1.2로 메이저 점프** (1.13.4 → 2.1.2) — 컴포넌트별(메인/Gateway API/CRD Operator/VMCI Relay) 세분화된 리소스 제어, 로그 저장용 **PVC 자동 생성**(기본 활성). ⚠️ **1.13.4에서 업그레이드 시 기본 StorageClass 필수** — 없으면 파드가 PVC 바인딩 대기로 Pending에 멈춤. 사전에 `kubectl get storageclass`로 (default) 확인, 없으면 patch로 지정
- **Harbor 2.14.1** — trivy DB 셀프호스팅 구성, 신규 설치 시 `SKIP_LOG_AUDIT_DATABASE=true` 기본값(감사 로그를 DB로 직접 전달 안 함), nginx LB 사용 시 동시 요청 제한 구성
- **Velero 1.17.1** — 특권(privileged) fs-backup 파드 옵션, BackupPVC 어노테이션 지정
- 그 외 Cert Manager 1.19.1, Contour 1.33.0, Fluent Bit 4.1.1, Istio 1.27.4, Prometheus 3.5.0+vmware.2, Telegraf 1.36.4 등

---

## 8. VKS Standard Package v3.5.0+20251022 (VKS 3.5.0 내장, v2025.10.22)

- **AKO(Avi Kubernetes Operator) 1.13.4 첫 릴리스** 🆕 — L4-L7 로드밸런싱. Ingress(IngressClass), Service LoadBalancer, **Gateway API**(GatewayClass/Gateway/HTTPRoute), 멀티테넌시(클러스터/네임스페이스→Avi 테넌트 매핑), IPv6/듀얼스택(Calico·Antrea), Shared VIP, CRD 6종(HostRule, HTTPRule, L4Rule, L7Rule, SSORule, AviInfraSetting). Avi Controller 22.1.3~31.1.1 필요
- **애드온 관리 시스템(Addon Management) 편입 물결** — Cert Manager, Cluster Autoscaler, Contour, External DNS, Fluent Bit, Harbor, Istio 등 주요 패키지가 이 릴리스에서 Addon Management 프레임워크 지원 추가
- **Cluster Autoscaler 1.34.0** — 신규 파라미터: `priorityClassName`, `enforceNodeGroupMinSize`(기본 true), `startupTaint`, `logLevel`. 컨테이너 리소스 구성 가능, v1beta2 Cluster 지원
- **Harbor 2.14.0** — cert-manager 서명 시 additionalDnsName/ipAddresses 설정, HSTS 헤더, jobservice 타임아웃 구성. ⚠️ **Breaking Change:** proxy cache 허용 레지스트리에서 quay/gitlab 제거
- **네임스페이스 limit range / 컨테이너 레벨 CPU·메모리 기본값 구성**이 다수 패키지에 공통 추가
- **대규모 구버전 패키지 제거** — TKG 시절 패키지들(External DNS 0.13/0.14, Contour 1.28~1.30, Harbor 2.9/2.11, Fluent Bit 2.x/3.x, cert-manager 1.14~1.18 구버전, cluster-autoscaler 1.29~1.33 구버전 등) 일괄 정리
- ⚠️ **알려진 문제:** ① X-Small 클러스터에서 기본 리소스 요청 때문에 설치 실패 가능 → 설치 시 requests 값 조정 ② 패키지→애드온 마이그레이션 시 `-f`(values 파일) 미지정하면 **기본 구성이 기존 구성을 덮어씀** (특히 Prometheus StorageClass 주의)

---

## 9. VKS Standard Package v2025.8.19

취약점 수정 중심 유지보수 릴리스.

- Prometheus **2.53.4 → 3.5.0 메이저 업그레이드**, scrape_configs 라벨 누락 수정
- Istio 1.25.3+vmware.2 — 클러스터 업그레이드 멈춤(stuck) 수정, 에어갭/익명 접근 차단 레지스트리 환경 지원
- Contour 1.31.1(GRPCRoute 지원, VKr 1.33+) / 1.32.0, Telegraf 1.34.4(DCGM 메트릭 스크랩, KSM으로 PV/PVC 메트릭 수집) 등

---

## 10. VKS Standard Package v2025.6.17 (문서상 최초 릴리스)

- **Istio 첫 공식 지원 (1.25.3)** — Broadcom이 VKS의 Istio에 대해 **런타임 지원 약속**: 이슈 트리아지·근본원인 분석, 업스트림 PR 대행 제출, 진행상황 추적·공유. 사이드카 모드(기본)/ambient 모드(기본 비활성), mTLS 1.2/1.3, 분산 트레이싱(OpenTelemetry, Zipkin), 지원 번들 수집 도구 제공. 요구사항: VKr 1.29+
- **Velero 첫 Carvel 패키지 릴리스 (1.16.1)**
- **TLS 지원 확산** — External DNS(RFC2136 TLS: 포트 53→853 자동 전환), Fluent Bit(secretName으로 CA 인증서 자동 마운트), Prometheus 2.53.4 TLS 모드
- **PriorityClass 구성 지원**이 Cert Manager, Contour, External DNS, Fluent Bit, Harbor, Prometheus, Telegraf 등 전반에 도입
- **Harbor 2.13.1** — audit log 확장(이미지 pull/push 외 사용자 액션·시스템 이벤트 기록), OIDC PKCE 지원, OIDC 로그아웃 연동. 구 audit log API deprecated
- **Windows GMSA Webhook** — Linux 워커 없는 Windows 전용 클러스터 지원 (웹훅 파드는 컨트롤 플레인에서 실행)
- 구 fluxcd 계열 패키지(helm/kustomize/source-controller) 전부 제거
- ⚠️ **알려진 문제:** VKr 1.29→1.30 업그레이드가 istiod PDB 때문에 멈출 수 있음 (`cannot evict pod ... disruption budget istiod needs 1 healthy pods`). **워크어라운드:** 업그레이드 전 istiod replicas를 2로 올리고(autoscaling 활성 시 minReplicas=2), 업그레이드 후 원복 (KB 345904)

---

## 11. 요점 정리 (TL;DR)

1. **명칭·체계 전환** — "Core/Standard Packages" → **VKS Add-ons** (3.7.0부터). Product/Partner/Ecosystem/Community 4개 지원 티어, VKr 24개월 라이프사이클에 지원 귀속
2. **호환성 기준** — 패키지 호환성은 Supervisor가 아니라 **클러스터의 K8s(VKr) 버전** 기준. v3.7.0 저장소는 K8s 1.33~1.36 커버
3. **애드온 생태계 성장 타임라인** — 2025.6: Istio(런타임 지원)·Velero → 2025.10: AKO·애드온 관리 편입 → 2026.2: Vault Injector·Prometheus Operator → 2026.3: **Cilium**(대안 CNI) → 2026.4: **Helm Controller** → 2026.5: **Gatekeeper** → 2026.6: Multus·Whereabouts·NFS Client·**Headlamp**
4. **운영 주의사항 베스트 3:**
   - Gatekeeper 애드온 사용 시 **클러스터 업그레이드 전 웹훅 비활성화 필수** (KB 433183)
   - AKO 1.13.4 → 2.x 업그레이드 전 **기본 StorageClass 확인** (PVC 자동 생성으로 Pending 위험)
   - 패키지→애드온 마이그레이션 시 **values 파일을 반드시 `-f`로 지정** (기본값 덮어쓰기 방지)
5. **Cilium 고급 기능**(L7/Ingress/Egress GW/Gateway API/eBPF 마스커레이딩)은 **kube-proxy 비활성화가 전제** — VKS 3.7의 kube-proxy 비활성화 API와 세트로 사용. Istio 애드온과 Cilium CNI는 아직 비호환
