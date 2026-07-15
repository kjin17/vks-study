# VMware vSphere Kubernetes Service (VKS) 3.5 릴리스 노트 — 한글 정리

> **원문:** [VMware vSphere Kubernetes Service 3.5 Release Notes (Broadcom TechDocs)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vks-release-notes/vmware-tanzu-kubernetes-grid-service-35-release-notes.html)
> **포함 릴리스:** 3.5.0 (2025-10-27) / 3.5.1 (2026-03-05)
> **정리일:** 2026-07-15

---

## 1. 개요

vSphere Kubernetes Service(VKS, 구 TKG Service)는 vSphere Supervisor 환경에서 Kubernetes 클러스터의 프로비저닝과 라이프사이클 관리를 담당한다. VKS 3.5는 **Kubernetes(VKr) v1.34 지원**, **Cluster API v1beta2 도입**, **애드온 관리 체계 개편(AddonRepository API)**, **builtin-generic-v3.5.0 ClusterClass의 세밀한 구성 변수**가 핵심인 릴리스다.

### 버전 정책 (Versioning and Upgrades)
- 3.5.x 포인트 릴리스는 새 ClusterClass를 도입하지 않고, **3.5.0 베이스 ClusterClass + 누적 버그 수정**만 제공
- 안정성과 중요 버그 수정을 위해 항상 최신 포인트 릴리스로 업그레이드 권장

---

## 2. VKS 3.5 업그레이드 사전 요구사항

- **vCenter / Supervisor Kubernetes 버전** — Supervisor Kubernetes **1.30 이상** 필요 (vCenter 9.0 또는 vCenter 8.0 Update 3g 이상에서 제공)
- **VKr 버전** — VKS 3.5는 **VKr v1.29, v1.30 호환성 제거**. 업그레이드 전에 모든 클러스터가 **VKr 1.31 이상**에서 동작해야 함
- **VKS 버전** — 3.5로 직접 업그레이드하려면 Supervisor에 **VKS 3.2 이상** 설치 필요
- **VKr 1.34 지원 추가** — 이 릴리스에서 VKr 1.34 지원 시작

---

## 3. 지원 중단 안내 (Deprecation)

- **Cluster API v1beta1 폐기 예고** — v1beta1 API 버전이 deprecated 되었으며 향후 VKS 릴리스에서 제거 예정 (업스트림 Cluster API Issue #11920 참조)
- **builtin-generic-v3.4.0 ClusterClass 폐기** — 3.5에서 `builtin-generic-v3.5.0` 도입·권장. Kubernetes v1.34 이상으로 업그레이드하려면 v3.5.0으로 리베이스 필수. v3.4.0은 deprecated, 향후 제거 예정
- **tanzukubernetescluster ClusterClass 제거** (3.5.0 What's New에 포함) — 모든 네임스페이스에서 제거되어 더 이상 지원되지 않음. 해당 ClusterClass로 만든 클러스터는 자동으로 `builtin-generic-v3.1.0`으로 업데이트됨. tanzukubernetescluster 기반 커스텀 ClusterClass 생성도 deprecated — 신규 프로세스로 커스텀 CC 생성 필요

---

## 4. VKS 3.5.1+v1.34 (2026-03-05)

버그 수정 및 보안 패치 릴리스.

### 해결된 문제 (3.5.1)
- **인증서 교체(rotation) 후 클러스터 라이프사이클 작업(생성/스케일/업데이트) 차단** — VKS 3.4.1, 3.4.2, 3.5.0에서 발생. Cluster API가 `runtime-extension-webhook-service` 호출 시 `x509: certificate signed by unknown authority` 오류와 함께 TopologyReconciled 실패. 이번 릴리스에서 수정
- **DSM 호환성 복구** — VKS 3.5.1은 Data Services Manager 9.0.0/9.0.1과 호환됨 (3.5.0은 비호환이었음)
- **커스텀 ClusterClass 사용 시 3.5 업그레이드 후 컨트롤 플레인 자동 롤아웃** — 3.5.1에는 영향 없음 (3.5.0 한정 문제로 정리됨)
- **중복 KR OVA 템플릿이 있는 콘텐츠 라이브러리 추가 시 클러스터 False 상태** — TopologyReconciled 오류 문제 수정

### 알려진 문제 (3.5.1)
- **LCI 9.0.2에서 기본 구성으로 클러스터 생성 시 구버전 VKr로 생성됨** — 최신 VKr 버전이 아닌 이전 버전으로 클러스터가 만들어짐. **워크어라운드:** Custom 구성으로 사용할 VKr 버전을 명시
- **커스텀 인증서 Harbor Supervisor Service 사용 시 1회성 노드 롤아웃** — builtin-generic-v3.2.0~v3.4.0 클러스터, Harbor 2.11.2+vmware.1-tkg.2 미만에서만 발생. **워크어라운드:** KB 문서로 Secret 레이블 패치 또는 Harbor 2.11.2+ 업그레이드 (둘 다 전체 롤아웃 유발)
- **`/var/lib/etcd` 수동 마운트와 `maximumDBSizeGiB` 동시 정의 시 오류** — 3.5.0 업그레이드 후 수동 마운트를 유지한 클러스터는 레거시 구성으로 동작하며 새 자동 etcd 볼륨 프로비저닝/쿼터 관리 혜택을 받지 못함. **워크어라운드:** Cluster 오브젝트에서 `/var/lib/etcd` 경로의 사용자 정의 볼륨 마운트를 제거하고, `spec.topology.controlPlane.variables.overrides[kubernetes].value.etcdConfiguration.maximumDBSizeGiB` 변수로 정의

---

## 5. VKS 3.5.0+v1.34 (2025-10-27)

### 새로운 기능

#### VKS 애드온 관리 개편
Standard Packages 애드온 관리가 대폭 정비됨:
- **AddonRepository / AddonRepositoryInstall API** — 애드온 저장소를 모든 VKS 클러스터에 일괄 설치 가능. 사설 레지스트리로 재배치(relocate)한 경우 포함 설정 간소화. 기본값으로 VKS 패키지에 내장된 저장소 사용 (3.5.0 기준 v2025.10.22). 내장 버전과 다른 버전을 쓰거나 사설 레지스트리를 쓸 때는 다른 AddonRepository를 등록/갱신 가능
- **Supervisor 네임스페이스 단위 관리** — Standard Packages의 설치/업그레이드/구성을 Supervisor 네임스페이스에서 관리. VCF 9.0.1의 VKS Cluster Management 또는 새 VCF CLI `addon` 플러그인으로 사용
- **업그레이드 시 애드온 호환성 사전 점검** — 클러스터 K8s 버전 업그레이드 시 애드온 호환성 pre-check을 수행하고 최신 호환 AddonRelease로 자동 업그레이드. 점검 실패 시 명확한 오류 메시지와 함께 업그레이드 차단
- **설치/업그레이드 사전 점검** — 중복 PackageInstall을 차단하는 마이그레이션 체크 + 의존성 누락 애드온에 대한 비차단(non-blocking) 오류 보고
- **Cluster Autoscaler 설치 간소화** — 클러스터 업그레이드에 따라 자동 업그레이드되도록 개선
- **AddonReconciled 조건** — 클러스터에 설치된 모든 VKS 관리 애드온(Standard Packages 포함)의 reconcile 상태를 Cluster 리소스에 집계. 이 조건이 True가 아니면 K8s 버전 업그레이드 pre-check 실패로 업그레이드 차단
- AddonRelease의 새 버전 및 호환성 메타데이터 발견 용이성 개선

#### Cluster API v1beta2 도입
- 핵심 Cluster API 리소스(Cluster, Machine 등)와 Bootstrap/Control Plane 오브젝트의 **v1beta2 버전** 도입
- 기존 v1beta1로 생성된 클러스터는 업그레이드된 Cluster API 컨트롤러가 **자동으로 v1beta2로 변환**
- 향후 클러스터 LCM 관리에는 v1beta2 API 사용 권장 — **API의 v1 졸업(graduation)을 향한 중요한 단계**
- 모든 리소스의 Status가 개선되어 트러블슈팅 용이

#### PodDisruptionBudget (PDB) 가드레일
- Cluster 오브젝트에 **`SystemChecksSucceeded` 조건 신설** — PDB 관련 사전 업데이트 점검 통과 여부 표시
- `allowedDisruptions <= 0`인 PDB가 하나라도 있으면 조건이 False가 되고 **K8s 버전 업그레이드 차단**
- 주의: 매칭되는 파드가 없는 PDB(잘못된 셀렉터 등 오구성)도 allowedDisruptions가 0이 되어 업그레이드를 차단함

#### Kubernetes 구성 커스터마이징 (builtin-generic-v3.5.0 ClusterClass)
핵심 Kubernetes 컴포넌트와 OS 보안 설정의 세밀한 제어 제공 (모든 변수는 선택사항이며 하위 호환):
- **API 서버** (`kubernetes.apiServerConfiguration`) — 동시 요청 제한(maxRequestsInFlight, maxMutatingRequestsInFlight), 구조화 로깅(text/JSON, verbosity 0~6, flush 주기), 요청 타임아웃, 프로파일링 제어
- **etcd** (`kubernetes.etcdConfiguration`) — `maximumDBSizeGiB`로 DB 크기 제한(2~8 GiB). 시스템이 25% 추가 볼륨을 자동 프로비저닝하고 etcd `--quota-backend-bytes`에 매핑해 쿼터 소진으로 인한 클러스터 장애 방지. **ClusterClass v3.5부터 etcd 스토리지 사이징은 이 변수로만 관리** — `/var/lib/etcd` 직접 마운트는 더 이상 지원되지 않음(원래도 공식 지원 경로가 아니었음). 수동 바인드 마운트/스크립트는 제거 필요
- **kubelet** (`kubernetes.kubeletConfiguration`) — 노드당 maxPods(20~110), 이미지 관리(풀 동작, GC 임계값, 병렬 풀, 자격증명 검증 정책), 구조화 로깅, 컨테이너 로그 로테이션, 레지스트리 QPS 제한, unsafe sysctl 허용목록. 컨트롤 플레인/워커 풀별 오버라이드 가능
- **GRUB 비밀번호 보호** (`osConfiguration.grub.password`) — Linux 노드 부트로더에 PBKDF2 SHA-512 해시 비밀번호 설정 (미지정 시 자동 생성). 무단 부트 파라미터 변경 방지. **CIS/STIG 벤치마크 컴플라이언스** 요건
- **sudo 비밀번호 요구** (`osConfiguration.user.requirePasswordOnSudo`) — sudoers에서 NOPASSWD 제거로 최소 권한 원칙 구현. **STIG 컴플라이언스** 요건

#### VCF CLI 플러그인 변경
- Cluster 플러그인이 v1beta2 Cluster API 사용
- 애드온 관리 + PackageInstall 마이그레이션용 **`addon` 플러그인 신설**
- 클러스터 상태 조건을 v1beta2 조건 체계에 맞춰 조정
- **서포트 번들러 VCF CLI 통합** — cluster 플러그인의 `support-bundle` 서브커맨드로 진단 정보 수집 (별도 도구 다운로드 불필요). 개선점: gzip 압축으로 출력 파일 **70~80% 감소**, `--skip-create-user` 플래그로 임시 사용자 생성 생략, 컨트롤 플레인 노드만 선택적 로그 수집, 네트워크 로그 수집 추가

### 해결된 문제 (3.5.0)
- **KR 1.32 → 1.33 또는 ClusterClass v3.3.0+ 업그레이드가 간헐적으로 실패**하던 문제 수정 (KB#414483 참조)

### 알려진 문제 (3.5.0)
- **Velero 웹훅 장애로 클러스터 생성 실패** — `cbt.mutate.virtualmachine` 웹훅 호출 실패. **워크어라운드:** Velero vSphere Operator 로그로 원인 확인
- **커스텀 인증서 Harbor Supervisor Service 사용 시 1회성 노드 롤아웃** — 위 3.5.1 항목과 동일
- **DSM 9.0.0/9.0.1 비호환** — 3.5.0 업그레이드 시 DSM 동작 불능. **워크어라운드 없음** — DSM 사용자는 3.5.0 업그레이드 금지 (→ 3.5.1에서 호환성 복구)
- **커스텀 ClusterClass 사용 시 업그레이드 후 컨트롤 플레인 자동 롤아웃** — builtin-generic-v3.4.0 기반 커스텀 CC 클러스터. 워크로드는 무관. **워크어라운드 없음** (커스텀 CC 베이스 버전 추론 오류가 원인)
- **중복 KR 버전 템플릿이 있는 콘텐츠 라이브러리 추가 시 클러스터 False 상태** — TopologyReconciled False, 기존 노드 가용성에는 영향 없음. **워크어라운드:** 충돌 OS 템플릿 삭제 또는 `run.tanzu.vmware.com/resolve-os-image` 어노테이션에 콘텐츠 라이브러리 ID 지정 (→ 3.5.1에서 수정)
- **`/var/lib/etcd` 수동 마운트 + `maximumDBSizeGiB` 동시 정의 시 오류** — 위 3.5.1 항목과 동일. **해결책:** etcd 볼륨 구성은 maximumDBSizeGiB 변수 사용

---

## 6. 요점 정리 (TL;DR)

1. **K8s 1.34 지원** — VKr 1.29/1.30 지원 제거, 클러스터 최소 VKr 1.31, Supervisor K8s 1.30+, VKS 3.2+에서 업그레이드 가능
2. **Cluster API v1beta2 시대** — v1beta1 deprecated, 기존 클러스터 자동 변환, v1 졸업을 향한 단계
3. **애드온 관리 대개편** — AddonRepository/AddonRepositoryInstall API, 네임스페이스 단위 관리, 업그레이드 시 호환성 사전 점검·자동 애드온 업그레이드, AddonReconciled 조건
4. **세밀한 클러스터 구성 (v3.5.0 CC)** — API 서버/etcd/kubelet 튜닝, GRUB 비밀번호, sudo 비밀번호 등 CIS/STIG 컴플라이언스 대응. etcd 볼륨은 `maximumDBSizeGiB` 변수로만 관리 (수동 마운트 금지)
5. **업그레이드 가드레일** — PDB `SystemChecksSucceeded` 조건으로 allowedDisruptions ≤ 0인 PDB 존재 시 업그레이드 차단
6. **운영 주의** — 3.5.0은 DSM 9.0.0/9.0.1과 비호환·인증서 교체 후 라이프사이클 차단 버그 있음 → **3.5.1 사용 필수**. tanzukubernetescluster ClusterClass 완전 제거
