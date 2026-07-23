# VKS (VMware Kubernetes Service) 아키텍처 및 기능 소개

## 1. VKS 아키텍처 및 개요
VMware Kubernetes Service(VKS, 이전 vSphere with Tanzu 및 vSphere IaaS control plane)는 vSphere 환경에 내장된 쿠버네티스 제어 평면입니다. 기존의 가상 머신(VM)과 최신 컨테이너 기반 클라우드 네이티브 애플리케이션을 단일 통합 플랫폼에서 프로비저닝하고 운영할 수 있도록 아키텍처를 제공합니다. VKS는 별도의 외부 도구나 사일로 현상 없이 vSphere 인프라 위에서 직접 K8s 클러스터를 배포하고 스케일링할 수 있도록 돕습니다 [cite: 1.3.1].

## 2. 기존 가상화 환경 대비 기능 비교
기존 가상화 인프라는 중앙에서 '가상 머신(VM)'이라는 컴퓨팅 리소스를 할당하고 관리하는 데 초점을 맞추었습니다. 반면, **VKS는 기존 가상화 인프라 전체를 쿠버네티스화(K8s-Native)하여 관리합니다** [cite: 1.3.1]. 가상화 관리자(VI Admin)와 개발자(DevOps)는 모두에게 익숙한 쿠버네티스 선언적 API(YAML)를 사용하여 애플리케이션뿐만 아니라 컴퓨트, 네트워크, 스토리지 리소스를 논리적인 단위로 동적 할당 및 관리할 수 있습니다.

## 3. 구성요소 맵핑 (K8s to vSphere Mapping)
VMware 환경과 쿠버네티스의 논리적 구조는 다음과 같이 맵핑됩니다.
* **vCenter ➡️ Supervisor VM**: vCenter 내에서 프로비저닝되며, 쿠버네티스 컨트롤 플레인(Control Plane) 역할을 수행하는 Supervisor 가상 머신입니다.
* **ESX as worker Node ➡️ ESX Host**: 각 ESXi 호스트는 내장된 스피어렛(Spherelet - Kubelet의 vSphere 구현체)을 통해 직접 쿠버네티스 워커 노드처럼 동작합니다.
* **vSphere Namespace ➡️ Resource Pool**: 쿠버네티스의 네임스페이스는 vSphere의 리소스 풀에 직접 매핑됩니다. 이를 통해 CPU, 메모리 등의 컴퓨팅 자원 제한(Quota)과 권한을 하이퍼바이저 레벨에서 물리적으로 제어합니다.
* **datastore ➡️ StorageClass**: vCenter의 데이터스토어(vSAN, VMFS, NFS 등)는 쿠버네티스의 스토리지 클래스(StorageClass)와 연동되어 개발자가 스토리지를 쉽게 호출할 수 있게 합니다.
* **Persistent Volume (PV) ➡️ VMDK**: 쿠버네티스의 영구 볼륨 요청(PVC)은 퍼스트 클래스 디스크(First Class Disk, FCD) 형태의 가상 디스크(VMDK)로 동적 생성되어 컨테이너에 마운트됩니다.
* **CNI ➡️ Networks**: K8s 컨테이너 네트워크 인터페이스(CNI)는 NSX(또는 VDS)를 통해 논리적 스위치, 로드 밸런서, 라우터 등으로 가상화되어 네트워크 패브릭과 매핑됩니다 [cite: 3.1.2].

## 4. Supervisor가 배포할 수 있는 3가지
1. **VM Services**: 개발자가 K8s API(YAML)를 통해 전통적인 가상 머신(VM)을 프로비저닝하고 관리할 수 있게 해주는 서비스입니다 [cite: 1.3.1].
2. **vPod (vSphere Pods)**: 별도의 Linux VM(워커 노드) 없이 ESXi 호스트의 하이퍼바이저 위에서 직접 실행되는 네이티브 K8s Pod입니다. 강력한 보안 격리와 높은 성능을 제공합니다.
3. **VKS Cluster (Tanzu Kubernetes Grid / Guest Cluster)**: 애플리케이션 팀이 직접 사용할 수 있도록 프로비저닝되는 독립적인 업스트림 쿠버네티스 클러스터입니다 [cite: 1.3.1].

## 5. Supervisor Service 에 대한 소개
vSphere 인프라 위에 배포되는 쿠버네티스 컨트롤 플레인 서비스입니다. 개발자 및 DevOps 팀에게 K8s API 엔드포인트를 제공하여 인프라 자원(VM, 컨테이너, 스토리지, 네트워크)을 요청할 수 있도록 지원하며, IT 관리자는 vCenter를 통해 전체 워크로드의 보안, 수명주기, 리소스 정책을 중앙 집중식으로 관리할 수 있습니다 [cite: 1.3.3].

## 6. VKS Service 에 대한 소개
VMware Cloud Foundation 내에서 쿠버네티스 클러스터(게스트 클러스터)의 생성, 스케일링, 업그레이드 등 전체 수명 주기를 자동화하여 관리해 주는 서비스입니다. CNCF 인증을 받은 표준 K8s 클러스터를 온디맨드로 제공하여 퍼블릭 클라우드 환경과 동일한 셀프 서비스 경험을 가능하게 합니다 [cite: 3.2.2].

## 7. vSphere Kubernetes Release (vkr/TKr) 에 대한 소개
VMware(Broadcom)에서 테스트 및 호환성 검증을 완료한 쿠버네티스 바이너리, OS 이미지, 필수 애드온(CoreDNS, CNI, CSI 등)이 포함된 패키지 릴리스입니다. 최신 버전의 K8s 환경을 안정적으로 배포하고 클러스터 간의 파편화를 방지합니다 [cite: 3.2.2].

---

# VCF 9.1 달라진 점 소개 (New Features)

VCF(VMware Cloud Foundation) 9.1은 클라우드 네이티브 워크로드 및 네트워킹 구조를 대폭 혁신하였습니다 [cite: 3.2.4]. 핵심 변경 사항은 다음과 같습니다.

### 1. Enhanced Zone Architecture (향상된 영역 아키텍처)
영역(Zone) 당 여러 클러스터를 배포할 수 있어 애플리케이션 무중단 상태로 하드웨어 교체 및 수명주기 관리가 가능합니다. 특히 AI 전용 GPU 클러스터 등 독립된 워크로드 영역(Custom Zones)을 구성하여 특정 애플리케이션 요구사항(고대역폭, 지연시간 민감도 등)에 맞춰 리소스를 격리하고 유연하게 확장할 수 있습니다 [cite: 3.2.1, 3.2.2].

### 2. Distributed Transit Gateway (DTGW) support for Supervisor
가장 큰 네트워킹 변화 중 하나입니다. 기존 모델에서는 VPC 간 통신이나 물리 네트워크 연동을 위해 전용 NSX Edge 노드 클러스터가 필수적이었으나, VCF 9.1의 DTGW는 ESXi 호스트가 분산 브리징 방식을 통해 물리적 스위치(Switch Fabric)에 직접 연결되도록 지원합니다 [cite: 3.1.2, 3.2.4]. 병목 현상을 일으키던 엣지 노드의 필요성을 없애고 네트워크 성능을 극대화(Line-rate 확보)하였습니다 [cite: 3.1.3].

### 3. Multi Network Support for VKS Cluster
VKS 클러스터 네트워킹이 크게 향상되어 테넌트당 다중 Transit Gateways 및 외부 연결을 지원합니다 [cite: 3.1.5]. 분산 VLAN 연결, 격리된 VPN, 정적 라우팅 및 맞춤형 NAT 설정이 가능해져, 복잡한 외부 라우팅 장비 없이도 멀티 테넌시 및 다중 사이트 통신을 유연하게 구현할 수 있습니다 [cite: 3.1.2].

### 4. VKS Cluster Node Customization
이제 VKS 노드의 운영 체제 수준 최적화가 가능합니다. 워크로드 성격에 맞춰 커널 및 하드웨어 성능을 최적화하는 **TuneD Profile**과, 컨테이너 보안 강화를 위한 **AppArmor Profile** 적용을 지원하여 엔터프라이즈 환경에 맞는 강력한 제어권과 보안을 제공합니다 [cite: 1.1.1, 1.3.1].

### 5. Support CNI Selection and VKS Networking Addon
VKS 클러스터 프로비저닝 시 요구사항에 맞는 특정 CNI(Container Network Interface)를 유연하게 선택할 수 있으며, 추가적인 VKS 네트워킹 애드온 구성을 지원하여 다양한 네트워크 정책 및 환경과의 호환성을 강화했습니다 [cite: 1.3.1].

### 6. VKS Cluster Upgrade Rollout Strategy
K8s 클러스터 프로비저닝(Fast Deploy) 및 업그레이드 속도가 획기적으로 향상되었습니다. VKS 클러스터 프로비저닝 시간은 기존 약 37분에서 **11분(약 70% 단축)**으로 감소하였으며, 업그레이드 시간 또한 약 45분에서 **15분(약 67% 단축)**으로 대폭 줄어드는 새로운 롤아웃 전략이 적용되었습니다 [cite: 3.2.3, 3.2.5].

### 7. Intelligent Node Pool Placement (지능형 노드 풀 배치)
vSphere DRS(Distributed Resource Scheduler) 알고리즘이 쿠버네티스 노드 풀 배치에 직접 적용됩니다. 플랫폼 팀이 복잡한 매니페스트(YAML)를 수동으로 튜닝할 필요 없이, GPU가 필요한 Pod은 GPU 호스트 노드로, NVMe 스토리지가 필요한 워크로드는 NVMe 노드로 자동 분석되어 배치됩니다. 인프라 전체를 분석하여 가장 최적화된 호스트에 노드 풀을 할당합니다 [cite: 3.2.3, 3.2.5].

### 8. VCF Management Services
VCF Automation 및 VCF Operations 서비스와 VKS의 결합이 강화되었습니다 [cite: 3.2.3]. 
* **FinOps 및 K8s 비용 분석**: 네임스페이스 및 VKS 클러스터 단위의 비용 소비 현황(Cost Showback)을 정확히 분석하고 FOCUS 표준에 맞춘 API를 제공합니다 [cite: 3.2.3].
* **규정 준수(Continuous Compliance)**: 런타임 환경의 구성 변경(Drift)을 실시간으로 감지하고 자동으로 교정하는 기능이 추가되었습니다 [cite: 3.1.5].

### 9. Configuration maximum limit (구성 한도 확장)
대규모 엔터프라이즈 및 클라우드 서비스 제공자(CSP)를 위해 아키텍처 스케일이 비약적으로 확장되었습니다.
* **Max ESX Hosts**: 최대 5,000대 지원 [cite: 3.2.4]
* **Max K8s Clusters / Supervisor**: Supervisor당 관리 가능한 VKS 클러스터 개수가 기존 약 100개에서 **500개**로 대폭 상향되었습니다 [cite: 3.2.3, 3.2.4, 3.2.5].

### 10. VCFA BluePrint Catalog
VCF Automation(VCFA, 구 Aria Automation)의 블루프린트 카탈로그를 통한 셀프 서비스가 확장되었습니다 [cite: 1.1.2, 3.2.2]. 인프라 관리자의 개입 없이, 플랫폼 엔지니어가 직접 블루프린트를 통해 VKS 클러스터를 프로비저닝하거나, 재해 복구(DR)를 위한 VM 레벨 복제 등을 카탈로그에서 손쉽게 생성하고 관리할 수 있습니다 [cite: 1.1.2].

---

### 참고 자료 (References)
* [cite: 1.1.1]: VMware Blog - What's New with vSphere in VMware Cloud Foundation 9.1?
* [cite: 1.1.2]: Broadcom TechDocs - Protection and Recovery 9.1 Release Notes
* [cite: 1.3.1]: TD Synnex - VCF 9.1 and VKS: Accelerating Cloud-Native Innovation on a Unified Platform
* [cite: 1.3.3]: Broadcom TechDocs - VMware Cloud Foundation 9.1
* [cite: 3.1.2]: VMware Blog - Simplify Workload Connectivity and Enhance Network Scale and Performance with VCF 9.1
* [cite: 3.1.3]: Puneet Sharma Blog - VCF 9.1 NSX Technical Deep Dive: Implementing Distributed Transit Gateways (DTGW)
* [cite: 3.1.5]: ITQ Blog - VCF 9.1 is here!
* [cite: 3.2.1]: VMware Blog - Deploy Modern Apps Faster, Scale Smarter, and Lower Your TCO with VMware vSphere Kubernetes Service in VCF 9.1
* [cite: 3.2.2]: VMware Docs - The Unified Platform for All Workloads
* [cite: 3.2.3]: VMTECHIE Blog - NSX / VKS
* [cite: 3.2.4]: VirtualVMX - Everything That's New in VMware Cloud Foundation 9.1
* [cite: 3.2.5]: VMTECHIE Blog - VKS Cast of Characters
