# VMware vSphere Kubernetes Service (VKS) 3.6 릴리스 노트 — 한글 정리

> **원문:** [VMware vSphere Kubernetes Service 3.6 Release Notes (Broadcom TechDocs)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vks-release-notes/vmware-tanzu-kubernetes-grid-service-36-release-notes.html)
> **포함 릴리스:** 3.6.0 (2026-02-11) / 3.6.1 (2026-04-13) / 3.6.2 (2026-04-13) / 3.6.3 (2026-06-16)
> **정리일:** 2026-07-15

---

## 1. 개요

vSphere Kubernetes Service(VKS, 구 TKG Service)는 vSphere Supervisor 환경에서 Kubernetes 클러스터의 프로비저닝과 라이프사이클 관리를 담당한다. VKS 3.6은 **Kubernetes v1.35 지원**, **RHEL 노드 지원**, **ImageBaker 도입**, **CNI의 애드온 프레임워크 전환**이 핵심인 메이저 릴리스이며, 이후 3.6.1~3.6.3 포인트 릴리스가 버그 수정과 VCF 9.1 연계 기능을 추가했다.

### 버전 정책 (Versioning and Upgrades)
- 포인트 릴리스(3.6.x)는 메이저 릴리스(3.6.0)와 **동일한 베이스 ClusterClass**를 유지하고, 누적 버그 수정만 포함 (새 ClusterClass 도입 없음)
- 메이저 릴리스의 요구사항·업그레이드 전제조건·deprecation은 모든 포인트 릴리스에 동일하게 적용
- 안정성과 중요 버그 수정을 위해 **항상 최신 포인트 릴리스**로 설치/업그레이드 권장

---

## 2. VKS 3.6 업그레이드 사전 요구사항

- **vCenter / Supervisor Kubernetes 버전** — Supervisor Kubernetes **1.30 이상** 필요 (vCenter 9.0 또는 vCenter 8.0 Update 3g 이상에서 제공)
- **VKr 버전** — VKS 3.6은 **VKr v1.31 호환성 제거**. 업그레이드 전에 모든 클러스터가 **VKr 1.32 이상**에서 동작해야 함
- **VKS 버전** — 3.6으로 직접 업그레이드하려면 Supervisor에 **VKS 3.3 이상** 설치 필요

---

## 3. 지원 중단 안내 (Deprecation)

- **Image Builder → ImageBaker** — Image Builder는 Kubernetes 1.34 및 2026년 2월 이전 패치 버전까지만 지원. 그 이후 릴리스되는 모든 마이너/패치 버전의 커스텀 노드 OS 이미지는 **ImageBaker** 필수
- **ClusterBootstrap의 CNI 지정 방식 폐기** — VKr 1.35부터 CNI 선택은 `bootstrapAddons` ClusterClass 변수 사용. ClusterBootstrap 리소스의 `cni` 필드는 공식 deprecated
- **AntreaConfig / CalicoConfig 폐기** — VKr v1.35부터 **AddonConfig** 리소스로 Antrea/Calico를 구성. 단, VKr 1.35 미만 클러스터 생성 시에는 여전히 AntreaConfig/CalicoConfig 사용
- **builtin-generic-v3.5.0 ClusterClass 폐기** — 3.6에서 `builtin-generic-v3.6.0` 도입·권장. Kubernetes v1.35 이상으로 업그레이드하려면 v3.6.0으로 리베이스 필수. v3.5.0은 deprecated, 향후 제거 예정

---

## 4. VKS 3.6.3+v1.35 (2026-06-16)

업그레이드 신뢰성, 에어갭 지원 수정, 웹훅 가드레일 강화, 애드온 프레임워크 정확성, 보안 패치 중심 릴리스.

### 새로운 기능
- **업그레이드 사전 점검 웹훅 허용목록(Allowlist)** — 3.6.0에서 도입된 잘못 구성된 ValidatingWebhookConfiguration 감지(Gatekeeper, Kyverno, Rancher, k8tz, Dynatrace, Linkerd, OpenTelemetry 대상)에 대해, 클러스터 어노테이션으로 점검 제외 웹훅 목록 설정 가능. 목록에 있는 웹훅만 감지되면 `SystemChecksSucceeded`가 True가 되어 업그레이드 진행. 완전한 하위 호환
- **addons.kubernetes.vmware.com API 공식 문서화** — AddonConfig, AddonInstall, AddonRelease 등 애드온 API 그룹 전체가 developer.broadcom.com에 공개
- **내장 애드온 저장소 갱신** — 기본 AddonRepository가 Standard 패키지 3.6.0+20260416으로 업데이트. 자동 갱신을 건너뛰려면 `addons.kubernetes.vmware.com/skip-vks-managed-addon-repository-update` 어노테이션 사용
- **machineadm 서비스 로그를 서포트 번들에 포함** — 모든 게스트 클러스터 Linux 노드에서 노드 부트스트랩을 담당하는 machineadm systemd 서비스 로그가 kubelet/containerd 로그와 함께 수집됨 (head/tail 각 10M 제한). 노드 레벨 문제의 근본 원인 분석 개선

### 해결된 문제 (3.6.3)
- Ubuntu 노드에 추가 볼륨(`/var/lib/containerd`, `/var/lib/kubelet`) 구성 시 파티션 포맷 실패로 워커 노드가 NotReady로 멈추던 문제
- Antrea AddonConfig 검증 오류가 ClusterAddon 상태에 반영되지 않던 문제
- VKS 콘텐츠 라이브러리에 사용자 커스텀 이미지 등 비-VKS 이미지가 있으면 업그레이드 사전 점검(UCS)이 오류를 내던 문제 (이제 VKS 관리 이미지만 검증)
- 워커 노드 풀 없는 **컨트롤 플레인 전용 클러스터**가 Available 상태가 되지 못하던 문제 (`spec.topology.workers` 부재로 Antrea 애드온 템플릿 렌더링 실패)
- Windows 노드가 인플레이스 업데이트 대상으로 잘못 분류되어 CA 인증서 추가 주입 시 롤아웃이 일어나지 않던 문제 (이제 Windows 노드는 구성 변경 시 롤아웃 필요로 올바르게 식별)
- 동일 `spec.version`의 AddonRelease가 여러 개일 때 선택이 비결정적이어서 업그레이드가 멈추던 문제
- maxPods > 110 검증이 ClusterClass 버전을 확인하지 않고 무조건 적용되어, 더 높은 maxPods를 정상 지원하는 구버전 ClusterClass 클러스터가 잘못 거부되던 문제
- **에어갭 업그레이드 kapp 교착(deadlock)** — pull/push 번들 재배치 워크플로 사용 시 최초 재배치 실패 후 kapp이 FAILED 상태 PackageInstall에서 무한 대기하던 문제
- TKC 클러스터(1.32.x)의 호환 업그레이드 목록에 TKC API를 지원하지 않는 VKr 1.33.1이 잘못 표시되던 문제

### 알려진 문제 (3.6.3)
- **VKS 3.4.0 이하에서 만든 클러스터의 VKr 업그레이드 시 컨트롤 플레인이 간헐적으로 생성/삭제** — 첫 컨트롤 플레인 머신이 두 번 롤아웃됨. 수동 개입 불필요, 업그레이드는 정상 완료
- **Velero 웹훅 장애로 클러스터 생성 실패** — `cbt.mutate.virtualmachine` 웹훅 호출 실패 오류. **워크어라운드:** Velero vSphere Operator 로그로 원인 확인
- **커스텀 인증서 Harbor Supervisor Service 사용 시 1회성 노드 롤아웃** — builtin-generic-v3.2.0~v3.4.0 클러스터, Harbor 2.11.2+vmware.1-tkg.2 미만에서만 발생. **워크어라운드:** [KB 405355](https://knowledge.broadcom.com/external/article/405355)로 Secret 레이블 패치 또는 Harbor 2.11.2+ 업그레이드 (둘 다 전체 롤아웃 유발)
- **DSM 비호환** — VKS 3.5.0/3.6.0은 Data Services Manager 9.0.0/9.0.1과 호환되지 않음 (업그레이드 시 DSM 동작 불능). **워크어라운드 없음** — DSM 9.0.0/9.0.1 사용자는 업그레이드 금지
- **커스텀 ClusterClass 사용 시 VKS 3.5+ 업그레이드 후 컨트롤 플레인 자동 롤아웃** — 워크로드는 무관, **워크어라운드 없음**

---

## 5. VKS 3.6.2+v1.35 (2026-04-13)

인플레이스 전파 흐름, 보안 프로파일 권한, 애드온 저장소 업데이트 개선 + 업스트림 안정성용 CAPI 업데이트 + 보안 패치.

### 해결된 문제 (3.6.2)
- `vmware-system-vks-public` 외 애드온 저장소 업데이트 시 invalid specification 오류
- **AD 도메인 조인 사용 시 Windows 노드가 클러스터 가입 실패**하던 문제
- 1.34→1.35 클러스터 업그레이드 후 antrea interworking 기능 사용 불가 문제
- 클러스터 trust 구성 변경 후 컨트롤 플레인 노드가 NotReady로 멈추던 문제

### 알려진 문제 (3.6.2) — 주요 항목
- **Windows 워커 노드에 추가 CA 인증서 주입 실패** — trust/proxy 변수 변경 시 Linux 노드는 인플레이스로 적용되지만 Windows 노드는 적용도 롤아웃도 안 됨. **워크어라운드:** Windows 노드 풀을 수동 롤아웃 (스케일 다운/업 또는 머신 오브젝트 삭제 후 재생성)
- 그 외 3.6.3의 알려진 문제와 동일 항목 다수 (컨트롤 플레인 이중 롤아웃, Velero 웹훅, Harbor 커스텀 인증서, DSM 비호환)

---

## 6. VKS 3.6.1+v1.35 (2026-04-13)

CAPI 버전 상향(업스트림 개선 + kube-apiserver 이슈 완화 포함 보안 수정). **VCF 9.1과 결합 시 대형 신기능 다수.**

### VCF 9.1 + VKS 3.6.1 신기능
- **멀티 네트워크 지원** — 워커 노드에 전용 보조 네트워크 인터페이스, 파드에 Antrea CNI 관리 추가 인터페이스 프로비저닝. 관리 트래픽과 고부하 데이터 트래픽(NFS 스토리지, DB 복제 등) 분리 가능. SR-IOV로 유선급(near-wire-speed) 성능 지원, VPC VLAN Extension 서브넷 통한 외부 멀티캐스트 연결
- **Antrea 하이브리드 캡슐화 모드** — 같은 서브넷 내 노드 간 Pod-to-Pod/Pod-to-Service 트래픽의 캡슐화를 끄는 Hybrid 모드. TCP 트랜잭션·지연 지표에서 **최대 40% 성능 향상** 관측. AntreaProxy, Egress, AntreaNetworkPolicy, NodePortLocal, Multicast 등 주요 기능과 완전 호환
- **Supervisor당 클러스터 수 2.5배 확대** — Supervisor당 최대 **500 VKS 클러스터 / 총 4,000 노드** 지원. 수평 확장을 위해 Supervisor를 여러 개 운영할 필요 감소 (구체 수치는 configmax.broadcom.com 참조)
- **VM Fast Deploy로 배포/업그레이드 시간 단축** — VM 프로비저닝 방식 개선. 실험실 환경 기준 워커 100대 클러스터 생성 4분(70% 개선), 업그레이드 약 30분(85% 개선)
- **EncryptionClass 지원** — VCF Automation 연계 멀티테넌시. 테넌트별 고유 암호화 키 할당으로 데이터 암호화 격리, 사업부별 독립적 키 관리/수명주기 제어
- **노드 풀 자동 배치** — `failureDomain` 파라미터가 선택사항으로 변경. 시스템이 노드 풀을 존(zone) 간 자동 분산 (노드 풀 내 VM은 단일 존에 유지, 물리 호스트 분산은 best-effort)
- **애드온 관리 API로 CNI 관리** — 커스텀 CNI를 VKS 애드온 프레임워크로 사용 가능. Antrea는 전략적 기본 CNI 유지, **Cilium이 검증된 Standard Package로 제공** (eBPF 기반 네트워킹/관측성, 고급 로드밸런싱, 투명 암호화)
- **신뢰 CA 인증서의 계층적 구성** — Supervisor / Supervisor 네임스페이스 / 개별 클러스터 레벨에서 CA 인증서 구성. 네임스페이스 범위 CA 추가/갱신은 기존 클러스터의 롤링 업데이트를 유발하지 않음
- **Fleet Depot Service 변경 시 플릿 전체 롤아웃 방지** — VCF 9.1 업그레이드 중 Software Depot Service 활성화가 기존 클러스터의 파괴적 롤아웃을 유발하지 않음
- **Harbor 엔드포인트 패키지 관리 간소화** — 각 노드 hosts 파일에 Harbor 엔드포인트를 추가해 `depot.kube-system.svc`가 Harbor LB IP로 안정적으로 해석되도록 함 (복잡한 DNS 구성 불필요)

### 해결된 문제 (3.6.1)
- **maxPods > 110 구성 클러스터의 무한 컨트롤 플레인 롤아웃** (3.6.0 발생 문제) 수정

### 알려진 문제 (3.6.1) — VCF 9.1 관련 주요 항목
- **(VCF 9.1) 컨테이너 레지스트리 구성 적용 시 Windows 노드 시작 실패** — VKr 1.35.0 미만 Windows 노드가 containerd 기본 런타임 이름이 비어 부트스트랩 중 멈춤. **워크어라운드:** VKS 3.6.2로 업그레이드. 기존 클러스터는 약 60분 후 머신 헬스체크가 자동 롤아웃하거나, `cluster.x-k8s.io/remediate-machine` 어노테이션으로 즉시 조치
- **(VCF 9.1) 단일 존 → 멀티 존 전환 시 클러스터 False 상태** — Immediate 바인딩 StorageClass로 배포된 클러스터의 네임스페이스에 존이 추가되면 발생. **워크어라운드:** 노드 풀 StorageClass를 WaitForFirstConsumer(late-binding)로 변경
- **(VCF 9.1) VKS 3.6 + VCF 9.1 업그레이드 후 클러스터 False 상태** — failureDomain 미정의 클러스터는 WFFC StorageClass 필요. **워크어라운드:** 업그레이드 전(권장) 또는 후에 각 노드 풀에 failureDomain 명시, 또는 `-latebinding` StorageClass로 전환 (둘 다 노드 풀 롤링 업데이트 유발)
- **(VCF 9.1) 리저널 Harbor 배포 환경에서 VCF/Supervisor 9.1 업그레이드 시 전체 클러스터 자동 롤링 업데이트** — 새 인증서·DNS 항목 채택을 위한 노드 교체. **워크어라운드:** VCF 9.1 업그레이드 전에 ① VKS 3.6.1+ 업그레이드 ② 레거시(v1alpha3) 클러스터 폐기 ③ 모든 클러스터를 ClusterClass 3.6.0+로 업그레이드
- **(VCF 9.1) ClusterClass 3.1.0 클러스터는 리저널 Harbor에서 패키지 사용 불가** — **워크어라운드:** ClusterClass 3.2.0+로 업그레이드, 또는 AddonRepositoryInstall을 공개 URL/사설 레지스트리로 변경
- 그 외: Windows CA 주입 실패, AD 도메인 조인 실패, antrea interworking(KB 432638), trust 구성 후 NotReady(고아 프로세스 kill -9로 정리) 등 3.6.2에서 수정된 문제들이 이 시점에는 알려진 문제로 존재

---

## 7. VKS 3.6.0+v1.35 (2026-02-11)

### 새로운 기능

#### 라이프사이클 및 업그레이드
- **Kubernetes 1.35 지원** — VKr 1.35는 24개월 지원. 클러스터를 v1.35로 올리려면 VKS 3.6 필요
- **Standard 패키지** — 내장 기본 AddonRepository가 v3.6.0+20260211로 자동 전환 (skip 어노테이션으로 자동 갱신 회피 가능)
- **RHEL 기반 노드 지원** — RHEL 커스텀 노드 OS 이미지 지원. 새 **ImageBaker** 도구(Image Builder 대체)로 RHEL 이미지 빌드
  - 참고: Photon OS/Ubuntu 내장 이미지는 VCF 구독에 포함되어 완전 지원. **RHEL/Windows는 BYO 라이선스** 필요하며 OS 관련 문제는 해당 OS 벤더 담당 (VKS 지원 범위는 ImageBaker 이미지 생성 기능까지)
- **ImageBaker + VCF CLI 통합** — Photon OS/Ubuntu/Windows/RHEL 커스텀 노드 이미지 빌드. vCenter와 독립적으로 동작하는 스탠드얼론 도구라 인프라 요구사항 대폭 감소. Kubernetes v1.35 이상 지원 (v1.34 이하는 기존 Image Builder 유지)
- **정책 도구 오구성으로 인한 라이프사이클 실패 방지 가드레일** — 기존 PDB(Pod Disruption Budget) 점검에 더해 Admission Webhook 오구성 사전 점검 추가. `SystemChecksSucceeded`에 오구성 웹훅과 dry-run 실패의 상세 정보 포함

#### 구성 및 보안
- **builtin-generic-v3.6.0 ClusterClass** — 새 ClusterClass 변수 다수 추가
- **커스텀 Linux 노드 성능 프로파일 (TuneD)** — Supervisor 클러스터의 커스텀 리소스로 TuneD 프로파일 지원. CPU, 메모리 관리, 네트워킹, 블록 디바이스, I/O 스케줄링 등 커널 파라미터 튜닝. 범용 워크로드용 사전 구성 프로파일 포함
- **AppArmor 프로파일 지원** — Photon OS/Ubuntu 노드풀 전반에 선언적 MAC(Mandatory Access Control) 관리. 노드 재시작/라이프사이클 업데이트에도 보안 정책이 자동 동기화·유지
- **클러스터 생성 시 CNI 선택** — VKr 1.35부터 `bootstrapAddons` ClusterClass 변수로 CNI 선택 (ClusterBootstrap 방식은 미지원). 명시하지 않으면 Antrea 기본. CNI 애드온 상태는 VCF Automation 9.0.1+에서 확인 가능
- **애드온 프레임워크 기반 CNI 구성 간소화** — Antrea/Calico 구성을 AddonConfig 커스텀 리소스로 관리 (1.35+). 클러스터 생성 전 사전 구성 또는 배포 후 수정 가능. 기존 클러스터를 VKr 1.35로 업그레이드하면 AntreaConfig/CalicoConfig가 새 프레임워크로 자동 마이그레이션
- **OS 공통 인바운드 방화벽 규칙 인터페이스** — 클러스터 생성 시 소스 IP/CIDR/프로토콜/포트 정책을 단일 API로 정의, 모든 지원 OS에 적용. iptables(Linux)/netsh(Windows)를 따로 관리할 필요 제거. 표준 Kubernetes 노드 포트 범위 밖의 추가 포트/프로토콜도 구성 가능. 혼합 노드풀 클러스터에 특히 유용
- **Late-Binding StorageClass를 클러스터 기본으로 지정** — WaitForFirstConsumer(WFFC) StorageClass를 기본으로 지정 가능. 파드가 노드에 스케줄된 후 볼륨을 생성해 멀티 AZ 환경의 크로스존 마운트 실패 방지. 기본 StorageClass 설정에 `-latebinding` 접미사 사용

#### 기타
- **서포트 번들 도구 개선** — vCenter SSO 관리자 권한 없이 클러스터 사용자가 독립적으로 서포트 번들 생성 가능

### 해결된 문제 (3.6.0) — 주요 항목
- Linux 첫 부팅 시 구성 컴포넌트 다운로드 재시도로 노드 부트스트랩 견고성 향상
- GRUB 비밀번호의 사용자명 설정 가능 (컴플라이언스 대응)
- 클러스터 삭제 시 고아 리소스 감소 (리소스 소유권 관리 개선)
- Linux 추가 볼륨 포맷 간헐 실패 해결
- `vcf addon install migrate` 실행 시 리소스 자동 정리 + 기존 구성 데이터 값 자동 적용
- 애드온 업그레이드 `--force` 옵션 도입 (Ready=True가 아니어도 진행, core 애드온 제외)
- `vcf package available get` JSON 출력에 버전 정보 포함
- 런타임 익스텐션 파드 인증서 교체 후 클러스터 생성 실패 수정
- Supervisor SSO 사용자가 `cluster.x-k8s.io/remediate-machine` 레이블로 머신 조치를 안전하게 트리거 가능
- **etcd 관련 검증 웹훅 도입** — `maximumDBSizeGiB` 변수(3.5.0 도입)와 수동 `/var/lib/etcd` 볼륨 마운트는 상호 배타적. 둘을 함께 정의하면 검증 오류로 차단, 수동 마운트 단독 사용 시 경고

### 알려진 문제 (3.6.0) — 주요 항목
- **maxPods > 110 구성 시 무한 컨트롤 플레인 롤아웃** (→ 3.6.1에서 수정)
- Windows AD 도메인 조인 실패 (→ 3.6.2에서 수정. 임시: 도메인 조인 없이 배포 후 SSH로 수동 조인)
- 1.34→1.35 업그레이드 후 antrea interworking 사용 불가 (→ 3.6.2에서 수정. KB 432638)
- trust 구성 변경 후 컨트롤 플레인 NotReady (→ 3.6.2에서 수정. 임시: 고아 프로세스 `kill -9` 후 containerd 자동 재시작 확인)
- 컨트롤 플레인 이중 롤아웃 / Velero 웹훅 / Harbor 커스텀 인증서 / DSM 9.0.0·9.0.1 비호환 / 커스텀 CC 컨트롤 플레인 자동 롤아웃 — 3.6.3까지 동일하게 지속되는 항목들
- **중복 KR 버전 템플릿이 있는 콘텐츠 라이브러리 추가 시 클러스터 False 상태** — TopologyReconciled 조건이 False가 되나 기존 노드 가용성에는 영향 없음 (향후 reconcile/업데이트만 영향). **워크어라운드:** 충돌 OS 템플릿 삭제 또는 `run.tanzu.vmware.com/resolve-os-image` 어노테이션에 콘텐츠 라이브러리 ID 지정

---

## 8. 요점 정리 (TL;DR)

1. **K8s 1.35 시대 개막** — VKr 1.31 지원 제거, 클러스터 최소 VKr 1.32, Supervisor K8s 1.30+, VKS 3.3+에서 업그레이드
2. **이미지 도구 세대교체** — Image Builder → **ImageBaker** (vCenter 독립, Photon/Ubuntu/Windows/RHEL 지원), **RHEL 노드 지원** 시작 (BYO 라이선스)
3. **CNI 관리 방식 전환** — ClusterBootstrap `cni` 필드/AntreaConfig/CalicoConfig 폐기 → `bootstrapAddons` 변수 + AddonConfig 리소스 (VKr 1.35+), Cilium이 검증 패키지로 합류
4. **VCF 9.1 결합 시 스케일 대폭 확대 (3.6.1)** — Supervisor당 500 클러스터/4,000 노드, VM Fast Deploy(생성 70%/업그레이드 85% 단축), 멀티 네트워크+SR-IOV, Antrea 하이브리드 모드(최대 40% 성능 향상)
5. **보안 강화** — AppArmor 선언적 관리, TuneD 프로파일, OS 공통 방화벽 API, EncryptionClass 테넌트별 키, 계층적 CA 인증서
6. **운영 주의사항** — DSM 9.0.0/9.0.1과 비호환(업그레이드 금지), maxPods>110 무한 롤아웃은 3.6.1+에서 해결, Windows 관련 이슈는 3.6.2/3.6.3에서 순차 해결 → **최신 포인트 릴리스(3.6.3) 사용 권장**
