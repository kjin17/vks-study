# VKS (VMware Kubernetes Service) 아키텍처 및 기능 소개

> **문서 성격:** 앞부분(고객 소개)은 VKS를 처음 접하는 고객에게 가치·활용 사례를 설명하는 개요이고, 이어지는 번호 섹션은 기술 상세입니다. 모든 사실은 Broadcom 공식 TechDocs(VMware Cloud Foundation 9.1 / VKS 3.5~3.7 릴리스 노트, 본 저장소 정리본)를 근거로 합니다.

---

# VKS 고객 소개 (Customer Overview)

## 한 줄 요약
**VKS는 이미 운영 중인 vSphere 인프라를 그대로 쿠버네티스 플랫폼으로 전환**하여, 전통적인 VM과 최신 컨테이너 애플리케이션을 **하나의 검증된 플랫폼**에서 운영하게 합니다. 별도의 쿠버네티스 스택을 새로 구축·운영할 필요가 없습니다.

## 왜 VKS인가 — 고객의 고민과 해결

| 기존 고민 (Pain Point) | VKS의 해결 |
|---|---|
| 컨테이너용 K8s를 별도로 구축·운영 (사일로, 이중 투자) | vSphere 위에서 K8s를 **네이티브로 제공** — 기존 인프라 재사용 |
| 개발팀의 셀프서비스 요구 vs 인프라팀의 통제 필요 | 개발자는 **표준 K8s API(YAML)**, 관리자는 **vCenter 거버넌스**로 양립 |
| K8s 버전·애드온 파편화와 보안 패치 부담 | **검증된 VKr 릴리스 번들** + 24개월 지원 라이프사이클 |
| 규제·에어갭 환경의 컨테이너 도입 난이도 | VCF 9.1 **내장 Software Depot** 기반 에어갭 배포 지원 |
| 클라우드 대비 비용·거버넌스 가시성 부족 | **FinOps 비용 분석 + 지속 컴플라이언스**(VCF 9.1) |

## 핵심 이점 (Benefits)
- **익숙한 운영** — vCenter·DRS·vSAN·NSX를 그대로 활용, 신규 학습 곡선 최소화
- **개발자 셀프서비스** — 네임스페이스만 할당하면 개발팀이 온디맨드로 클러스터·VM·스토리지를 요청
- **엔터프라이즈 보안·거버넌스** — 하이퍼바이저 레벨 격리(vPod), AppArmor·TuneD, CIS/STIG 대응, 네이티브 OIDC, 계층적 CA 인증서
- **검증된 안정성** — CNCF 인증 K8s + Broadcom 검증 애드온(Product/Partner 티어는 런타임까지 지원)
- **경제성** — 기존 하드웨어·라이선스 재사용, 클러스터/네임스페이스 단위 비용 showback

## 이런 고객에게 (활용 사례)
- **애플리케이션 현대화** — 레거시 VM과 신규 컨테이너를 단일 플랫폼에서 점진적으로 전환
- **AI/ML 플랫폼** — Custom Zone + 지능형 노드 풀 배치로 GPU 워크로드 격리·최적 배치
- **Telco / 5G** — SR-IOV·DPDK(vfio-pci) 보조 NIC로 CNF 고성능 네트워킹
- **멀티테넌시 / CSP** — 테넌트별 EncryptionClass 키, 다중 네트워크, Supervisor당 500 클러스터 스케일
- **규제 산업 / 에어갭** — 인터넷 차단 환경에서도 안전한 컨테이너 배포

## 숫자로 보는 가치 (VCF 9.1 기준)
- 클러스터 **프로비저닝 약 70% 단축**(약 37→11분), **업그레이드 약 67% 단축**(약 45→15분)
- Supervisor당 **500 클러스터 / 4,000 노드**, 클러스터당 워커 **최대 250대**
- Antrea 하이브리드 캡슐화 모드로 **최대 40% 네트워크 성능 향상**
- **DTGW**로 전용 NSX Edge 노드 클러스터 없이 **Line-rate 성능** 확보

## 도입 여정 (3단계)
1. **활성화** — VCF 9.1에서 vSphere Supervisor 활성화 (vCenter·NSX·스토리지 연동)
2. **네임스페이스 할당** — 팀·프로젝트별 vSphere Namespace 생성 → 리소스 쿼터·권한 부여
3. **셀프서비스 배포** — 개발팀이 VKS 클러스터·VM·vPod을 K8s API로 온디맨드 프로비저닝

## 경쟁 대안 대비 차별점 (Why VMware by Broadcom)
- **하이퍼바이저 네이티브** — vPod은 별도 워커 VM 없이 ESXi 위에서 직접 실행, VM급 격리 + 컨테이너 민첩성
- **인프라 지능형 연계** — vSphere DRS가 K8s 노드 풀 배치까지 자동 최적화 (수동 YAML 튜닝 불필요)
- **단일 플랫폼 통합** — 컴퓨트·네트워크·스토리지·보안·백업(Velero)·레지스트리(Harbor)를 VCF 안에서 일괄 제공
- **검증·지원 체계** — VKr 24개월 라이프사이클 + 4개 애드온 지원 티어(Product~Community)

---

## 1. VKS 아키텍처 및 개요
VMware Kubernetes Service(VKS, 이전 vSphere with Tanzu 및 vSphere IaaS control plane)는 vSphere 환경에 내장된 쿠버네티스 제어 평면입니다. 기존의 가상 머신(VM)과 최신 컨테이너 기반 클라우드 네이티브 애플리케이션을 단일 통합 플랫폼에서 프로비저닝하고 운영할 수 있도록 아키텍처를 제공합니다. VKS는 별도의 외부 도구나 사일로 현상 없이 vSphere 인프라 위에서 직접 K8s 클러스터를 배포하고 스케일링할 수 있도록 돕습니다.

## 2. 기존 가상화 환경 대비 기능 비교
기존 가상화 인프라는 중앙에서 '가상 머신(VM)'이라는 컴퓨팅 리소스를 할당하고 관리하는 데 초점을 맞추었습니다. 반면, **VKS는 기존 가상화 인프라 전체를 쿠버네티스화(K8s-Native)하여 관리합니다**. 가상화 관리자(VI Admin)와 개발자(DevOps)는 모두에게 익숙한 쿠버네티스 선언적 API(YAML)를 사용하여 애플리케이션뿐만 아니라 컴퓨트, 네트워크, 스토리지 리소스를 논리적인 단위로 동적 할당 및 관리할 수 있습니다.

## 3. 구성요소 맵핑 (K8s to vSphere Mapping)
VMware 환경과 쿠버네티스의 논리적 구조는 다음과 같이 맵핑됩니다.
* **vCenter ➡️ Supervisor VM**: vCenter 내에서 프로비저닝되며, 쿠버네티스 컨트롤 플레인(Control Plane) 역할을 수행하는 Supervisor 가상 머신입니다.
* **ESX as worker Node ➡️ ESX Host**: 각 ESXi 호스트는 내장된 스피어렛(Spherelet - Kubelet의 vSphere 구현체)을 통해 직접 쿠버네티스 워커 노드처럼 동작합니다.
* **vSphere Namespace ➡️ Resource Pool**: 쿠버네티스의 네임스페이스는 vSphere의 리소스 풀에 직접 매핑됩니다. 이를 통해 CPU, 메모리 등의 컴퓨팅 자원 제한(Quota)과 권한을 하이퍼바이저 레벨에서 물리적으로 제어합니다.
* **datastore ➡️ StorageClass**: vCenter의 데이터스토어(vSAN, VMFS, NFS 등)는 쿠버네티스의 스토리지 클래스(StorageClass)와 연동되어 개발자가 스토리지를 쉽게 호출할 수 있게 합니다.
* **Persistent Volume (PV) ➡️ VMDK**: 쿠버네티스의 영구 볼륨 요청(PVC)은 퍼스트 클래스 디스크(First Class Disk, FCD) 형태의 가상 디스크(VMDK)로 동적 생성되어 컨테이너에 마운트됩니다.
* **CNI ➡️ Networks**: K8s 컨테이너 네트워크 인터페이스(CNI)는 NSX(또는 VDS)를 통해 논리적 스위치, 로드 밸런서, 라우터 등으로 가상화되어 네트워크 패브릭과 매핑됩니다.

## 4. Supervisor가 배포할 수 있는 3가지
1. **VM Services**: 개발자가 K8s API(YAML)를 통해 전통적인 가상 머신(VM)을 프로비저닝하고 관리할 수 있게 해주는 서비스입니다.
   - 기존 VM을 K8S API로 관리
   - VM Operator CRD 사용 (VirtualMachine)
   - VM 생명주기 자동화
2. **vPod (vSphere Pods)**: 별도의 Linux VM(워커 노드) 없이 ESXi 호스트의 하이퍼바이저 위에서 직접 실행되는 네이티브 K8s Pod입니다. 강력한 보안 격리와 높은 성능을 제공합니다.
   - ESXi 위에서 직접 실행되는 Pod
   - VM 격리 수준 보안
   - 별도의 Worker Node VM 불필요
   - 빠른 프로비저닝
3. **VKS Cluster (Tanzu Kubernetes Grid / Guest Cluster)**: 애플리케이션 팀이 직접 사용할 수 있도록 프로비저닝되는 독립적인 업스트림 쿠버네티스 클러스터입니다.
   - 완전한 K8S 클러스터 프로비저닝
   - CP + Worker Node 모두 VM
   - 표준 K8S API 완전 호환
   - 멀티 테넌트 독립 클러스터
   - Helm, kubectl 모두 사용

## 5. Supervisor Service 에 대한 소개
vSphere 인프라 위에 배포되는 쿠버네티스 컨트롤 플레인 서비스입니다. 개발자 및 DevOps 팀에게 K8s API 엔드포인트를 제공하여 인프라 자원(VM, 컨테이너, 스토리지, 네트워크)을 요청할 수 있도록 지원하며, IT 관리자는 vCenter를 통해 전체 워크로드의 보안, 수명주기, 리소스 정책을 중앙 집중식으로 관리할 수 있습니다.

## 6. VKS Service 에 대한 소개
VMware Cloud Foundation 내에서 쿠버네티스 클러스터(게스트 클러스터)의 생성, 스케일링, 업그레이드 등 전체 수명 주기를 자동화하여 관리해 주는 서비스입니다. CNCF 인증을 받은 표준 K8s 클러스터를 온디맨드로 제공하여 퍼블릭 클라우드 환경과 동일한 셀프 서비스 경험을 가능하게 합니다.

## 7. vSphere Kubernetes Release (vkr/TKr) 에 대한 소개
VMware(Broadcom)에서 테스트 및 호환성 검증을 완료한 쿠버네티스 바이너리, OS 이미지, 필수 애드온(CoreDNS, CNI, CSI 등)이 포함된 패키지 릴리스입니다. 최신 버전의 K8s 환경을 안정적으로 배포하고 클러스터 간의 파편화를 방지합니다.

---

# VCF 9.1 달라진 점 소개 (New Features)

VCF(VMware Cloud Foundation) 9.1은 클라우드 네이티브 워크로드 및 네트워킹 구조를 대폭 혁신하였습니다. 핵심 변경 사항은 다음과 같습니다.

### 1. Enhanced Zone Architecture (향상된 영역 아키텍처)
영역(Zone) 당 여러 클러스터를 배포할 수 있어 애플리케이션 무중단 상태로 하드웨어 교체 및 수명주기 관리가 가능합니다. 특히 AI 전용 GPU 클러스터 등 독립된 워크로드 영역(Custom Zones)을 구성하여 특정 애플리케이션 요구사항(고대역폭, 지연시간 민감도 등)에 맞춰 리소스를 격리하고 유연하게 확장할 수 있습니다.

### 2. Distributed Transit Gateway (DTGW) support for Supervisor
가장 큰 네트워킹 변화 중 하나입니다. 기존 모델에서는 VPC 간 통신이나 물리 네트워크 연동을 위해 전용 NSX Edge 노드 클러스터가 필수적이었으나, VCF 9.1의 DTGW는 ESXi 호스트가 분산 브리징 방식을 통해 물리적 스위치(Switch Fabric)에 직접 연결되도록 지원합니다. 병목 현상을 일으키던 엣지 노드의 필요성을 없애고 네트워크 성능을 극대화(Line-rate 확보)하였습니다.

### 3. Multi Network Support for VKS Cluster
VKS 클러스터 네트워킹이 크게 향상되어 테넌트당 다중 Transit Gateways 및 외부 연결을 지원합니다. 분산 VLAN 연결, 격리된 VPN, 정적 라우팅 및 맞춤형 NAT 설정이 가능해져, 복잡한 외부 라우팅 장비 없이도 멀티 테넌시 및 다중 사이트 통신을 유연하게 구현할 수 있습니다.

### 4. VKS Cluster Node Customization
이제 VKS 노드의 운영 체제 수준 최적화가 가능합니다. 워크로드 성격에 맞춰 커널 및 하드웨어 성능을 최적화하는 **TuneD Profile**과, 컨테이너 보안 강화를 위한 **AppArmor Profile** 적용을 지원하여 엔터프라이즈 환경에 맞는 강력한 제어권과 보안을 제공합니다.

### 5. Support CNI Selection and VKS Networking Addon
VKS 클러스터 프로비저닝 시 요구사항에 맞는 특정 CNI(Container Network Interface)를 유연하게 선택할 수 있으며, 추가적인 VKS 네트워킹 애드온 구성을 지원하여 다양한 네트워크 정책 및 환경과의 호환성을 강화했습니다.

### 6. VKS Cluster Upgrade Rollout Strategy
K8s 클러스터 프로비저닝(Fast Deploy) 및 업그레이드 속도가 획기적으로 향상되었습니다. VKS 클러스터 프로비저닝 시간은 기존 약 37분에서 **11분(약 70% 단축)**으로 감소하였으며, 업그레이드 시간 또한 약 45분에서 **15분(약 67% 단축)**으로 대폭 줄어드는 새로운 롤아웃 전략이 적용되었습니다.

### 7. Intelligent Node Pool Placement (지능형 노드 풀 배치)
vSphere DRS(Distributed Resource Scheduler) 알고리즘이 쿠버네티스 노드 풀 배치에 직접 적용됩니다. 플랫폼 팀이 복잡한 매니페스트(YAML)를 수동으로 튜닝할 필요 없이, GPU가 필요한 Pod은 GPU 호스트 노드로, NVMe 스토리지가 필요한 워크로드는 NVMe 노드로 자동 분석되어 배치됩니다. 인프라 전체를 분석하여 가장 최적화된 호스트에 노드 풀을 할당합니다.

### 8. VCF Management Services
VCF Automation 및 VCF Operations 서비스와 VKS의 결합이 강화되었습니다. 
* **FinOps 및 K8s 비용 분석**: 네임스페이스 및 VKS 클러스터 단위의 비용 소비 현황(Cost Showback)을 정확히 분석하고 FOCUS 표준에 맞춘 API를 제공합니다.
* **규정 준수(Continuous Compliance)**: 런타임 환경의 구성 변경(Drift)을 실시간으로 감지하고 자동으로 교정하는 기능이 추가되었습니다.

### 9. Configuration maximum limit (구성 한도 확장)
대규모 엔터프라이즈 및 클라우드 서비스 제공자(CSP)를 위해 아키텍처 스케일이 비약적으로 확장되었습니다.
* **Max ESX Hosts**: 최대 5,000대 지원
* **Max K8s Clusters / Supervisor**: Supervisor당 관리 가능한 VKS 클러스터 개수가 기존 약 100개에서 **500개**로 대폭 상향되었습니다.

### 10. VCFA BluePrint Catalog
VCF Automation(VCFA, 구 Aria Automation)의 블루프린트 카탈로그를 통한 셀프 서비스가 확장되었습니다. 인프라 관리자의 개입 없이, 플랫폼 엔지니어가 직접 블루프린트를 통해 VKS 클러스터를 프로비저닝하거나, 재해 복구(DR)를 위한 VM 레벨 복제 등을 카탈로그에서 손쉽게 생성하고 관리할 수 있습니다.

---

# VKS 릴리스별 달라진 점 (버전별 New Features)

> **근거 문서:** 본 저장소의 `VKS_3.5_Release_Notes_KR.md` · `VKS_3.6_Release_Notes_KR.md` · `VKS_3.7_Release_Notes_KR.md` · `VKS_Addons_Release_Notes_KR.md` (모두 Broadcom TechDocs 공식 릴리스 노트 한글 정리본, 기준일 2026-07-15)

## 버전·호환성 한눈에 보기

| VKS | Kubernetes(VKr) | 릴리스일 | 핵심 키워드 |
|---|---|---|---|
| **3.5** | v1.34 | 2025-10-27 | Cluster API v1beta2, AddonRepository API, CIS/STIG 구성 변수 |
| **3.6** | v1.35 | 2026-02-11 | RHEL 노드, ImageBaker, CNI 애드온화, (VCF 9.1 결합) 스케일·성능 |
| **3.7** | v1.36 | 2026-06-18 | 5노드 컨트롤 플레인, 네이티브 OIDC, 워커 250대, VKS Add-ons 리브랜딩 |

> 각 메이저 버전은 이전 VKr 호환성을 순차 제거합니다(3.5→VKr 1.31 최소, 3.6→1.32 최소, 3.7→1.33 최소). 업그레이드 전 모든 클러스터의 VKr을 먼저 상향하고, ClusterClass도 해당 버전(`builtin-generic-v3.x.0`)으로 리베이스해야 합니다. 안정성을 위해 **항상 최신 포인트 릴리스** 사용을 권장합니다.

---

## VKS 3.5 (K8s 1.34 · 2025-10-27)

### 라이프사이클 & API
- **Cluster API v1beta2 도입** — 기존 v1beta1로 만든 클러스터는 자동 변환. API v1 졸업(graduation)을 향한 단계이며 Status 개선으로 트러블슈팅 용이
- **애드온 관리 개편** — `AddonRepository` / `AddonRepositoryInstall` API 신설, Supervisor 네임스페이스 단위 관리, 업그레이드 시 애드온 호환성 사전 점검 후 최신 호환 버전으로 자동 업그레이드, `AddonReconciled` 조건 집계

### 구성 & 보안 (builtin-generic-v3.5.0 ClusterClass)
- **세밀한 컴포넌트 튜닝** — API 서버(동시요청·구조화 로깅·타임아웃), etcd(`maximumDBSizeGiB` 2~8 GiB, 25% 자동 볼륨 프로비저닝), kubelet(maxPods 20~110, 이미지 GC 등)
- **컴플라이언스(CIS/STIG)** — GRUB 부트로더 비밀번호(PBKDF2 SHA-512), sudo 비밀번호 요구(NOPASSWD 제거)
- **PDB 가드레일** — `SystemChecksSucceeded` 조건 신설. `allowedDisruptions ≤ 0`인 PDB가 있으면 K8s 버전 업그레이드 차단
- **VCF CLI** — Cluster 플러그인 v1beta2 전환, `addon` 플러그인 신설, `support-bundle` 서브커맨드 통합(gzip 70~80% 감소)

> ⚠️ **운영 주의:** 3.5.0은 DSM 9.0.0/9.0.1 비호환 + 인증서 교체 후 라이프사이클 차단 버그가 있어 **3.5.1 사용 필수**. `tanzukubernetescluster` ClusterClass는 완전 제거됨.

---

## VKS 3.6 (K8s 1.35 · 2026-02-11)

### 코어 (3.6.0)
- **Kubernetes 1.35 지원** (VKr 1.35, 24개월 지원) · VKr 1.31 호환 제거
- **RHEL 기반 노드 지원** — 커스텀 노드 OS로 RHEL 추가 (Photon/Ubuntu는 구독 포함, RHEL·Windows는 BYO 라이선스)
- **ImageBaker 도입** — 기존 Image Builder 대체. vCenter와 독립된 스탠드얼론 도구로 인프라 요구 대폭 감소, Photon/Ubuntu/Windows/RHEL 이미지 빌드, VCF CLI 통합 (K8s 1.35+)
- **CNI 관리 애드온화** — `bootstrapAddons` ClusterClass 변수 + `AddonConfig` 리소스로 전환. 기존 `ClusterBootstrap.cni` 필드·`AntreaConfig`/`CalicoConfig`는 폐기(1.35+에서 자동 마이그레이션)
- **보안·구성** — TuneD 성능 프로파일(커널 튜닝), AppArmor 선언적 MAC, OS 공통 인바운드 방화벽 API(iptables/netsh 통합), Late-Binding(WFFC) StorageClass 기본화로 크로스존 마운트 실패 방지

### VCF 9.1 결합 시 대형 신기능 (3.6.1)
- **스케일 2.5배** — Supervisor당 최대 **500 VKS 클러스터 / 총 4,000 노드**
- **VM Fast Deploy** — 워커 100대 클러스터 생성 **약 4분(70%↓)**, 업그레이드 **약 30분(85%↓)**
- **멀티 네트워크 + SR-IOV** — 워커/파드에 보조 인터페이스, 관리·데이터 트래픽 분리, 유선급(near-wire-speed) 성능
- **Antrea 하이브리드 캡슐화 모드** — 동일 서브넷 노드 간 캡슐화 해제로 TCP 지연 지표 **최대 40% 향상**
- **EncryptionClass** — 테넌트별 고유 암호화 키(멀티테넌시), **계층적 CA 인증서**(Supervisor/네임스페이스/클러스터 레벨), **Cilium**이 검증 Standard 패키지로 합류

> ⚠️ **운영 주의:** DSM 9.0.0/9.0.1 비호환, `maxPods>110` 무한 롤아웃(3.6.1 수정), Windows 관련 이슈는 3.6.2/3.6.3에서 순차 해결 → **3.6.3 사용 권장**.

---

## VKS 3.7 (K8s 1.36 · 2026-06-18)

### 코어 & 보안
- **Kubernetes 1.36 지원** (Cluster API v1.13, CAPV v1.16) · VKr 1.32 호환 제거
- **5노드 컨트롤 플레인** — 컨트롤 플레인 2대 동시 손실에서 복구 (VKr 1.36.1+ / 1.35.5+ / 1.34.8+ 필요)
- **네이티브 OIDC 인증** — Pinniped 대안. 구조화 인증 구성 + **CEL 표현식**으로 사용자/그룹 클레임 매핑, pass-through JWT(Headlamp 등) 지원 · **워크로드 아이덴티티 페더레이션**(AWS/GCP/Azure 직접 인증)
- **보안 옵션 확대** — TLS 프로파일(최소버전·암호 스위트 일괄), /usr 읽기전용 마운트(Photon), **FIPS 기본 번들**(Ubuntu, Canonical Pro 구독 불필요)
- **인플레이스 노드 업데이트 확대** — 다양한 구성 변경을 롤링 재생성 없이 적용 · **kube-proxy 비활성화 API**(Cilium 대응) · 커스텀 RuntimeClass(DB용 ulimit) · etcd 요청 크기 튜닝
- ⚠️ **TKC(`TanzuKubernetesCluster`) API 지원 완전 제거** — TKC 의존 클러스터는 사전 마이그레이션 필수

### 네트워킹 & 스케일
- **보조 NIC vfio-pci 바인딩(SR-IOV VF)** — DPDK 가속으로 Telco 5G Core CNF 등 고성능 워크로드 대응 (`driver`/`sriovResourcePool` 필드)
- **CIDR 중복 방지 검증 강화** — Pod/Service CIDR가 Supervisor IP 대역과 겹치면 생성 거부
- **워커 노드 250대로 확장** (기존 150대) — 단, etcd DB 4GB↑, Pod CIDR 마스크, 컨트롤 플레인 VM 클래스 상향 등 조정 필요

### 애드온
- **"VKS Add-ons" 공식 리브랜딩** — 기존 Core/Standard 용어 폐기, 4개 지원 티어로 재편
- **Helm 애드온 지원**(`helm-controller` 기본 도입), **Gateway API 애드온화**, **버전별 다중 AddonRepositoryInstall**
- **신규 애드온** — Multus/Whereabouts(멀티 NIC), NFS-Client(NFS PV), Headlamp(대시보드)
- **CLI** — `vcf clusterclass explain`으로 ClusterClass 변수·기본값 조회

---

## VKS Add-ons 생태계 (구 Standard Packages)

VKS 클러스터 기능을 확장하는 **검증된 소프트웨어 컴포넌트 모음**. 3.7.0부터 "Core/Standard 패키지" 용어를 폐기하고 통합 **VKS Add-ons** 프레임워크로 전환했습니다. 패키지 호환성은 Supervisor가 아니라 **클러스터의 K8s(VKr) 버전** 기준이며, 지원 자격은 **VKr 24개월 라이프사이클**에 귀속됩니다.

### 지원 티어 4단계

| 티어 | 소유/검증 | Broadcom 지원 범위 |
|---|---|---|
| **Product** | Broadcom 엔지니어링 큐레이션·검증 | 배포 + 라이프사이클 + **런타임 트러블슈팅까지 완전 지원** |
| **Partner** | ISV(독립 SW 벤더) 검증 | 배포·라이프사이클 지원, 런타임은 파트너 에스컬레이션 |
| **Ecosystem** | Broadcom 큐레이션 OSS | 패키징·서명·라이프사이클만, 런타임은 업스트림 |
| **Community** | 미검증/사용자 빌드 OSS | 공식 지원 없음 |

### 생태계 성장 타임라인
- **2025.6** — Istio(런타임 지원 약속)·Velero 첫 Carvel 패키지
- **2025.10** — AKO(Avi Operator, L4-L7 LB·Gateway API) 합류, 주요 패키지 애드온 관리 편입
- **2026.2** — Vault Injector, Prometheus Operator(선택)
- **2026.3** — **Cilium**(eBPF 기반 대안 CNI) 합류
- **2026.4** — **Helm Controller**(Helm 차트 애드온 기반)
- **2026.5** — **Gatekeeper**(OPA 정책)
- **2026.6** — Multus·Whereabouts·NFS-Client·**Headlamp**

> ⚠️ **Cilium 고급 기능**(L7 프록시/Ingress/Egress Gateway/Gateway API/eBPF 마스커레이딩)은 **kube-proxy 비활성화**가 전제입니다 — VKS 3.7의 kube-proxy 비활성화 API와 세트로 사용하세요. (현재 Istio 애드온과 Cilium CNI는 비호환)

---

## 업그레이드 · 운영 체크리스트 (공통)

1. **업그레이드 경로** — Supervisor의 VKS 버전과 모든 클러스터의 VKr을 먼저 상향 (3.7는 Supervisor VKS 3.4+, 클러스터 VKr 1.33+). TKC API 클러스터는 3.7 전에 마이그레이션 필수
2. **ClusterClass 리베이스** — `builtin-generic-v3.5.0 → v3.6.0 → v3.7.0` 순차 리베이스. 구버전은 deprecated 후 제거 예정
3. **에어갭/YAML 선택** — 3.7은 인터넷 연결 vCenter 9.1+는 일반판, 9.0 이하·에어갭은 `-legacy` YAML (잘못 고르면 이미지 레지스트리 해석 실패)
4. **애드온 주의** — Gatekeeper 사용 시 업그레이드 전 웹훅 비활성화(KB 433183) · AKO 1.13.4→2.x 전 기본 StorageClass 확인 · 패키지→애드온 마이그레이션 시 values 파일 `-f` 지정
5. **최신 포인트 릴리스 사용** — 3.5.1 / 3.6.3 등 누적 버그 수정본 권장
