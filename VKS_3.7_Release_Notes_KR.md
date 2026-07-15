# VMware vSphere Kubernetes Service (VKS) 3.7 릴리스 노트 — 한글 정리

> **원문:** [VMware vSphere Kubernetes Service 3.7 Release Notes (Broadcom TechDocs)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vks-release-notes/vmware-tanzu-kubernetes-grid-service-37-release-notes.html)
> **릴리스:** vSphere Kubernetes Service 3.7.0+v1.36 (2026-06-18)
> **정리일:** 2026-07-15

---

## 1. 개요

vSphere Kubernetes Service(VKS, 구 TKG Service)는 vSphere Supervisor 환경에서 Kubernetes 클러스터의 프로비저닝과 라이프사이클 관리를 담당하는 컴포넌트 모음이다. VKS 3.7은 **Kubernetes v1.36 지원**, **5노드 컨트롤 플레인**, **네이티브 OIDC 인증**, **워커 노드 최대 250대 확장** 등이 핵심인 릴리스다.

---

## 2. VKS 3.7 업그레이드 사전 요구사항

### ⚠️ 서비스 YAML 선택 주의
vCenter 버전과 네트워크 연결 상태에 따라 올바른 YAML을 선택해야 한다. 잘못 선택하면 **이미지 레지스트리 해석(resolution) 실패**가 발생한다.

| YAML 파일 | 대상 환경 |
|---|---|
| `vsphere-kubernetes-service-legacy-3.7.0+v1.36.yaml` | vCenter **9.0 이하**, 또는 **에어갭(air-gapped)** vCenter 9.1+ 환경. 공개 레지스트리 `projects.packages.broadcom.com` 참조 |
| `vsphere-kubernetes-service-3.7.0+v1.36.yaml` | **인터넷 연결된 vCenter 9.1 이상**. VCF Operations Software Depot 참조 |

### 버전 요구사항
- **VKr (vSphere Kubernetes Release):** VKS 3.7은 **VKr v1.32 호환성을 제거**. 업그레이드 전에 모든 클러스터가 **VKr 1.33 이상**에서 동작해야 함
- **VKS 버전:** 3.7로 업그레이드하려면 Supervisor가 **VKS 3.4.0 이상**을 실행 중이어야 함
- **Supervisor Kubernetes 버전:** 최소 **1.32** 필요 (vCenter 8.0 P07 관련)

---

## 3. 지원 중단 안내 (Deprecation)

- **builtin-generic-v3.7.0 ClusterClass 도입** — VKS 3.7부터 이 ClusterClass 사용을 권장. 기존 클러스터는 Kubernetes v1.36 이상으로 업그레이드하기 전에(또는 업그레이드 과정에서) **v3.7.0으로 리베이스 필수**. 기존 `builtin-generic-v3.6.0`은 deprecated 되었으며 향후 릴리스에서 제거 예정
- **TKC 기반 클러스터 지원 종료** — `TanzuKubernetesCluster`(TKC) API 기반 클러스터 지원이 완전히 제거됨. TKC API를 지원하는 마지막 버전이 VKr v1.32였으므로, TKC API에 의존하는 클러스터는 이 릴리스와 호환되지 않음

---

## 4. 새로운 기능 (What's New)

### 4.1 라이프사이클 및 업그레이드
- **Kubernetes v1.36 지원** — VKr 1.36 호환. Cluster API v1.13, CAPV(Cluster API Provider vSphere) v1.16 사용. VKr 1.32 지원 제거
- **Ubuntu 노드 FIPS 구성 개선** — VKr 1.36 Ubuntu 노드에 FIPS가 기본 번들됨. **Canonical Pro 구독 없이** FIPS 활성화 가능
- **업그레이드 사전 점검 웹훅 허용목록(Allowlist)** — 3.6에서 도입된 잘못 구성된 ValidatingWebhookConfiguration 감지(Gatekeeper, Kyverno, Rancher, k8tz, Dynatrace, Linkerd, OpenTelemetry 대상)에 대해, 클러스터별로 점검 제외할 웹훅 이름 화이트리스트를 어노테이션으로 설정 가능. 전체 점검을 건너뛰는 위험한 `dangerous-skip-...` 어노테이션 없이도 업그레이드 진행 가능. 완전한 하위 호환 (미설정 시 기존 동작 유지)

### 4.2 구성 및 보안
- **5노드 컨트롤 플레인 지원** — 극한의 복원력이 필요한 환경을 위해 컨트롤 플레인 노드 5대 구성 가능. 컨트롤 플레인 2대 동시 손실에서 복구하려면 VKr **1.36.1+ / 1.35.5+ / 1.34.8+** 필요
- **/usr 파티션 읽기 전용 마운트 (Photon OS 전용)** — `osConfiguration.immutability.usrPartitionMode` 변수(builtin-generic-v3.7.0)를 `ReadOnly`로 설정하면 노드 수명 동안 /usr가 읽기 전용으로 마운트됨. DaemonSet 변조에 대한 심층 방어 강화. 기본값은 read-write
- **인플레이스(In-place) 노드 업데이트 확대** — 다양한 노드 구성 변경을 롤링 재생성 없이 실행 중인 노드에 직접 적용. `maxUnavailable`/`maxSurge` 설정을 준수하며, 기본적으로 가용성 유지를 위해 스페어 노드를 잠시 추가. `maxUnavailable`을 1 이상으로 설정하면 완전 인플레이스 방식 선택 가능. Kubernetes 버전이나 VM 클래스 변경 등은 기존 롤링 업데이트 유지. v3.7.0 ClusterClass로 리베이스 시 자동 적용
- **kube-proxy 비활성화 API** — Cilium처럼 자체 프록시 구현을 제공하는 CNI를 위한 kube-proxy 비활성화 프로비저닝 지원 (신규 클러스터, VKr 1.35.0 이상)
- **Kubernetes 컴포넌트 TLS 프로파일 구성** — 새 변수 `security.minimumTLSProtocol`, `security.tlsCipherSuites`로 최소 TLS 버전(1.2/1.3)과 커스텀 암호 스위트를 kube-apiserver, controller-manager, scheduler, etcd, kubelet에 일괄 적용. TLS 1.3에서는 Go 표준에 따라 커스텀 암호 무시
- **Cluster Autoscaler Scale-from-Zero 자동 구성** — Windows 노드 풀 자동 감지(`capacity.cluster-autoscaler...` 어노테이션 불필요), 커스텀 레이블/테인트가 클러스터 변수에서 Autoscaler로 자동 전파되어 어노테이션 중복 관리 불필요
- **커스텀 RuntimeClass 구성** — ContainerD에 커스텀 RuntimeClass 추가 가능. 초기 지원은 Linux ulimit 설정 (memory lock, 파일 오픈 한도 등 DB 워크로드 요구사항 대응)
- **컨트롤 플레인 스케일 튜닝 (etcd 커스터마이징)** — etcd 최대 요청 크기를 클러스터 변수로 조정 가능. 대용량 ConfigMap/Secret으로 인한 GitOps 워크플로 트랜잭션 실패 방지

### 4.3 네트워킹
- **보조 NIC에 vfio-pci 드라이버 바인딩 (VMXNET3, SR-IOV)** — SR-IOV VF 지원으로 Telco 5G Core CNF 같은 고성능 워크로드가 DPDK 가속 VMXNET3 인터페이스를 사용 가능. `networks` 변수의 보조 인터페이스에 두 필드 추가:
  - `driver` — NIC에 바인딩할 드라이버 (현재 `vfio-pci`만 지원)
  - `sriovResourcePool` — 디바이스 플러그인 리소스 풀 등록. 파드가 `requests: <prefix>/<name>: 1` 형태의 표준 리소스 요청으로 NIC 직접 사용
- **CIDR 중복 방지 검증 강화** — Pod/Service CIDR가 Supervisor 관리 IP 대역과 겹치면 클러스터 생성 거부. 신규 생성에만 적용되며 VDS, NSX T1 Gateway, NSX-VPC 등 모든 토폴로지 지원

### 4.4 ID 및 접근 관리 (IAM)
- **네이티브 OIDC 인증** — 기존 Pinniped 기반 인증의 대안으로 워크로드 클러스터에 네이티브 OpenID Connect 인증 지원. Kubernetes 구조화 인증 구성(structured authentication configuration)을 활용해 **CEL 표현식**으로 사용자/그룹/속성 클레임 매핑 가능. Headlamp, Tekton Dashboard 같은 도구의 pass-through JWT 인증이 가능해지고, Pinniped supervisor 엔드포인트에 네트워크 접근이 없는 환경에서도 테넌트 격리 보장
- **워크로드 아이덴티티 페더레이션** — 서비스 어카운트 발급자(issuer) URL 구성 지원. 워크로드가 서비스 어카운트 토큰으로 AWS, GCP, Azure 등 외부 서비스에 직접 인증 가능

### 4.5 애드온 및 애드온 관리
- **버전별 다중 AddonRepositoryInstall** — 단일 저장소를 계속 갱신하던 방식에서 **버전별 추가(additive) 모델**로 전환. 설치/업그레이드 때마다 해당 릴리스용 AddonRepository(Install)가 새로 생성되어 여러 저장소가 공존. 3.5/3.6에서 업그레이드 시 기존 `default-addon-repo-install`은 deprecated (동작은 유지되나 더 이상 갱신 안 됨). 불필요한 리소스는 관리자가 수동 삭제해야 함
- **"Core/Standard 패키지" → "VKS Add-ons"로 리브랜딩** — 4개 지원 티어로 재편:
  - **Product** — Broadcom이 직접 큐레이션·검증. 배포/라이프사이클/런타임 문제 모두 Broadcom GS 완전 지원
  - **Partner** — ISV가 검증. 배포·라이프사이클은 Broadcom, 런타임 문제는 파트너로 에스컬레이션
  - **Ecosystem** — Broadcom 큐레이션 OSS. 패키징·서명·라이프사이클 문제만 지원
  - **Community** — 미검증/사용자 빌드 OSS. 공식 지원 채널 없음
  - 모든 티어의 지원 자격은 클러스터 VKr 버전의 **24개월 라이프사이클**에 귀속
- **신규 애드온 (v3.7.0+20260618)**
  - **Multus/Whereabouts** (Product 티어) — VPC 모드 Calico CNI 클러스터에서 멀티 NIC 지원. v1.36 미만 Kubernetes + Calico는 클러스터 생성 전 autodetect 인터페이스를 eth0으로 설정하는 추가 구성 필요. 보조 인터페이스는 클러스터 생성 후 안전하게 제거 가능
  - **NFS-Client** (Product 티어) — 기존 NFS 공유를 PV로 네이티브 마운트/읽기/쓰기
  - **Headlamp** (Ecosystem 티어) — 통합 UI/셀프서비스 대시보드. Cert-Manager·Prometheus 플러그인 포함
- **Prometheus 애드온 개선** — web-config 기반 TLS 지원, LoadBalancer가 없는 환경을 위한 NodePort 노출 지원
- **Helm 기반 애드온 지원** — 기존 Carvel 기반과 동일한 선언적 애드온 API로 Helm 차트 애드온 배포/관리. 이를 위해 `helm-controller`가 기본 애드온으로 도입 (builtin-generic-v3.7.0 이상에서 자동 설치)
- **Gateway API의 관리형 애드온 전환** — VKS 3.7.0 + VKr 1.36부터 Gateway API를 애드온 관리 프레임워크로 관리 (ClusterBootstrap `additionalPackages`에서 제외). `addon.addons.kubernetes.vmware.com/gateway-api: unmanaged` 레이블로 옵트아웃하면 VKS가 제공하지 않는 버전/구성 사용 가능

### 4.6 CLI 및 도구
- **`vcf clusterclass explain` 신규 명령** — ClusterClass의 사용 가능 변수, 기본값, 문서를 조회. Day-2 구성 작업 시 YAML을 수동으로 뒤질 필요 감소

### 4.7 스케일 및 성능
- **워커 노드 최대 250대로 확장** (기존 150대). 250노드 스케일 운영 시 필수 조정 사항:
  - **컨트롤 플레인 VM 클래스** — Antrea+AVI: 최소 4 vCPU / 12 GiB, Calico+Multus+AVI: 최소 6 vCPU / 12 GiB
  - **etcd DB 크기** — 최소 4 GB로 상향 (기본 2 GB는 고동시성 롤아웃에 부족)
  - **Pod CIDR** — maxPods 110(기본)이면 /15 마스크, 더 크면 /14 마스크
  - **Multus 메모리 제한** — 사용 시 1.5 Gi 이상 (OOMKilled 방지)
  - 참고: maxSurge > 20의 고동시성 롤아웃 + 약 11,000개 파드 규모에서는 컨트롤 플레인 VM 클래스 추가 상향 필요 가능

---

## 5. 해결된 문제 (Fixed Issues)

- **Windows 워커 노드의 AD 도메인 가입 실패** — 클러스터 배포 시 AD 자격증명 Secret에 예기치 않은 개행(`\n`) 문자가 포함되면 Windows 워커 노드가 Active Directory 도메인 가입에 실패하고 gMSA 웹훅 구성이 막히던 문제 해결
- **VKr 업그레이드 중 컨트롤 플레인이 간헐적으로 생성/삭제되는 문제** — VKS 3.4.0 이하에서 생성된 클러스터에서 발생하던 문제가 builtin-generic-v3.7.0 ClusterClass에서 수정됨. v3.4.0 이하 ClusterClass를 쓰는 기존 클러스터는 Kubernetes 버전 업데이트 시 자동으로 새 클래스로 전환됨 (skip-rebase 어노테이션을 붙이면 제외되며, 구버전 ClusterClass 유지 시 불필요한 롤아웃 계속 발생)

---

## 6. 알려진 문제 (Known Issues)

- **VCFA Attach / Regional Harbor 설정이 인플레이스 업데이트를 유발해 Supervisor 불안정 가능** — VCFA Attach 또는 Regional Harbor 레지스트리 구성이 전역 설정 변경을 클러스터에 푸시하는데, builtin-generic-v3.7.0 클러스터에서는 이것이 스페어 노드를 만드는 인플레이스 업데이트를 트리거함. 클러스터/노드풀 규모가 클수록 리소스 생성이 동시다발로 몰려 Supervisor 컨트롤 플레인의 etcd DB 한도를 소진시킬 수 있음. **워크어라운드:** Broadcom Support 문의
- **커스텀 인증서 Harbor Supervisor Service 사용 시 노드 롤아웃** — builtin-generic-v3.2.0~v3.4.0 클러스터가 업그레이드 후 1회성 노드 롤아웃을 겪을 수 있음 (신뢰 인증서 정렬이 결정적(deterministic)으로 바뀐 데 따른 것). Harbor Supervisor 2.11.2+vmware.1-tkg.2 미만에서만 발생. **워크어라운드:** KB 문서로 Secret 레이블 패치 또는 Harbor Supervisor를 2.11.2+vmware.1-tkg.2 이상으로 업그레이드 (두 방법 모두 전체 클러스터 롤아웃 유발)
- **커스텀 ClusterClass 사용 시 VKS 3.5+ 업그레이드 후 컨트롤 플레인 자동 롤아웃** — builtin-generic-v3.4.0 기반 커스텀 CC 클러스터에서 발생. 컨트롤 플레인 노드에만 영향, 워크로드는 무관. **워크어라운드 없음** (커스텀 CC의 베이스 버전 추론 오류가 원인)
- **Cilium CNI + 혼합 OS 클러스터가 Ready 안 됨** — Cilium이 Windows를 지원하지 않아 Windows 워커 노드가 Not Ready로 남음. **워크어라운드:** Windows 워커가 필요하면 다른 CNI 사용, Cilium을 써야 하면 Linux(Photon OS) 워커로만 구성
- **kube-proxy가 비활성화 상태로 표시되지만 계속 동작** — 클러스터 생성 시 `kubernetes.kubeProxyConfiguration`을 명시하지 않으면, 생성 후 `enabled` 플래그를 false로 변경하는 것이 허용되어 상태 표시와 실제 동작이 불일치. **워크어라운드:** kube-proxy 활성/비활성은 반드시 **클러스터 생성 시점**에 명시적으로 설정하고, 생성 후 변경하지 말 것
- **VCFA UI에서 OIDC 구성 클러스터 생성 실패** — UI가 `apiServerConfiguration.extraAuthentication.jwt.issuer` 하위의 `audiences` 필드를 리스트가 아닌 단일 문자열로 잘못 생성함. **워크어라운드:** UI 대신 CLI/API로 배포하고 `audiences`를 YAML 리스트로 작성:
  ```yaml
  issuer:
    audiences:
      - 0oay8xwjv1A2Qrbst697
    url: https://integrator-8865151.okta.com/oauth2/default
  ```

---

## 7. 요점 정리 (TL;DR)

1. **업그레이드 경로 주의** — Supervisor의 VKS 3.4.0+, 모든 클러스터 VKr 1.33+, TKC API 클러스터는 먼저 마이그레이션 필수
2. **YAML 두 종류** — 인터넷 연결 vCenter 9.1+는 일반판, 그 외(9.0 이하/에어갭)는 legacy판
3. **ClusterClass 리베이스** — K8s 1.36으로 가려면 builtin-generic-v3.7.0 필수, v3.6.0은 deprecated
4. **보안 강화 옵션 다수** — TLS 프로파일, /usr 읽기전용(Photon), FIPS(Ubuntu, 구독 불필요), 네이티브 OIDC
5. **스케일 업** — 워커 250대, 5노드 컨트롤 플레인 (단, etcd/CIDR/VM 클래스 조정 필요)
6. **애드온 체계 개편** — "VKS Add-ons" 리브랜딩 + 4개 지원 티어, Helm 애드온 지원, Gateway API 애드온화
