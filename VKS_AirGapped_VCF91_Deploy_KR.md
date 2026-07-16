# VKS 에어갭(Air-Gapped) 배포 가이드 — VCF 9.1.0

> 원문: [vmware/vsphere-supervisor — airgapped/air-gapped-vcf91.md](https://github.com/vmware/vsphere-supervisor/blob/main/airgapped/air-gapped-vcf91.md)
> 정리일: 2026-07-16

인터넷이 차단된(air-gapped) 환경에서 vSphere Kubernetes Service(VKS) 클러스터를 배포하는 절차 정리. 인터넷 연결된 Bastion 호스트에서 바이너리/이미지를 내려받아 격리된 Admin 호스트로 옮기고, Software Depot(내장 OCI 레지스트리)를 통해 Supervisor와 VKS 워크로드를 구성하는 흐름이다.

---

## 용어

| 용어 | 설명 |
|---|---|
| **Bastion 호스트** | 인터넷 연결된 Linux VM — 패키지/이미지 다운로드 담당 |
| **Admin 호스트** | 에어갭 내부의 격리된 Linux VM — 배포 컨트롤 센터 |
| **VCF CLI** | 플러그인 기반 CLI (`vcf`) — 구 kubectl-vsphere 플러그인 대체 |
| **VKS Standard Packages** | cert-manager, Prometheus 등 큐레이션된 애드온 서비스 번들 |
| **Software Depot** | VCF 9.1.0 내장 OCI 레지스트리 — 외부 레지스트리 불필요 |

## 전제 조건 & BOM

- **VCF/VVF 9.1.0 전용** — 이전 릴리스는 외부 OCI 레지스트리 필요 (레거시 가이드 참조)
- Bastion/Admin 호스트: Ubuntu 24.04.4
- 필수 도구: `wget`, `curl`, `docker`, `jq`, `yq`, `openssl`, `imgpkg`, `python3`
- 예시 버전: vCenter 9.1.0 / VKS Service 3.6.3 / Kubernetes(VKr) 1.34.2 / VKS Standard Packages 3.6.0-20260211
- Admin 호스트 권장 사양: 2 vCPU, 4GB RAM, **여유 스토리지 150~200GB**

## 데이터 흐름

```
인터넷 → Bastion 호스트 (다운로드)
       → Admin 호스트 (파일 복사, 에어갭 내부)
       → Software Depot OCI 레지스트리 (업로드)
       → Supervisor / VKS 클러스터 (배포)
```

---

## 1단계. 필요한 플러그인·바이너리·이미지 다운로드 (Bastion)

### 1a. Kubernetes Release OVA
- `https://wp-content.broadcom.com/v2/latest/` 에서 다운로드
- VCF 9.1.0 기본은 **v1.34.2** — 최신 3개 버전 이상 확보 권장

### 1b. VCF CLI 및 플러그인
- Broadcom Support Portal(My Downloads → "VCF consumption CLI")에서 **9.1.0** 버전 다운로드
```bash
tar -xzvf ./VCF-Consumption-CLI-Linux_AMD64-9.1.0.tar.gz
sudo install ./vcf-cli-linux_amd64 /usr/local/bin/vcf
```

### 1c. Supervisor Services 바이너리·YAML
- "legacy"가 포함된 서비스 구성 YAML에서 `spec.template.spec.fetch.imgpkgBundle[].image` 필드로 패키지 이미지 참조 확인
- 마이그레이션 스크립트로 이미지 번들을 tar로 다운로드:
```bash
./oci_image_depot_migrator.py download \
  -s projects.packages.broadcom.com/vsphere/supervisor/argocd-service/1.1.0/argocd-service:v1.1.0_vmware.1
```

### 1d. VKS Standard Packages
```bash
./oci_image_depot_migrator.py download \
  -s projects.packages.broadcom.com/vsphere/supervisor/vks-standard-packages/3.6.0-20260211/vks-standard-packages:3.6.0-20260211
```
→ `vks-standard-packages-3.6.0-20260211.tar` 생성

**요약:** OVA, VCF CLI, 애드온 번들, 서비스 이미지 tar + YAML 전부를 Admin 호스트로 복사한 뒤 다음 단계 진행.

## 2단계. Supervisor 활성화
- 네트워킹·스토리지 정책·프로파일 구성 후 vCenter에서 Supervisor 활성화 (공식 설치 문서 절차)

## 3단계. 콘텐츠 라이브러리 생성 + K8s Release 업로드
- **로컬** Content Library 생성 → 1a에서 받은 OVA 업로드

## 4단계. vSphere Namespace 생성
- VKS 클러스터를 배포할 네임스페이스 생성 (예: `ns01`)

## 5단계. Admin 호스트 구성

### 5a. kubectl 설치
```bash
wget https://<Supervisor-KubeAPI-Endpoint>/wcp/plugin/linux-amd64/vsphere-plugin.zip --no-check-certificate
sudo install kubectl /usr/local/bin/kubectl
```

### 5b. Supervisor 로그인
```bash
# vCenter 루트 CA 신뢰 등록
wget https://<vCenter-IP>/certs/download.zip --no-check-certificate
# VCF 컨텍스트 생성 (구 kubectl-vsphere 대체)
vcf context create supervisor1 --endpoint https://supervisor0.env1.lab.test \
  --username administrator@vsphere.local --type k8s
vcf context use supervisor1:ns01
```

### 5c. Software Depot OCI 업로드 활성화
```bash
./toggle_software_depot_oci_image_upload.sh enable \
  --vsp-host <vsp-host-fqdn> --admin-username <user> --admin-password '<pw>'
```
> ⚠️ **보안 주의:** OCI 업로드는 **인증 게이트가 없음** — 업로드 완료 후 반드시 `disable`로 꺼야 함 (6c 단계).

## 6단계. Software Depot에 패키지 업로드

### 6a. Supervisor Services 업로드
```bash
./oci_image_depot_migrator.py upload \
  -s projects.packages.broadcom.com/vsphere/supervisor/argocd-service/1.1.0/argocd-service:v1.1.0_vmware.1 \
  -t <software-depot-fqdn>
```
(Admin 호스트가 소스 레지스트리에 연결 가능하면 `copy` 액션으로 직접 이관 가능)

### 6b. VKS Standard Packages 업로드
```bash
./oci_image_depot_migrator.py upload \
  -s .../vks-standard-packages:3.6.0-20260211 -t <software-depot-fqdn>
```

### 6c. OCI 업로드 비활성화 (필수)
```bash
./toggle_software_depot_oci_image_upload.sh disable --vsp-host <fqdn> ...
```

## 7단계. Supervisor에 Harbor 구성

- VCF Automation 있는 배포: "Using Harbor" 문서 절차 그대로
- **VCF Automation 없음 / VVF**: 7a·7b 선행 필요

### 7a. 관리 프록시(management proxy) 구성
```bash
./manage-depot-image-proxy.sh add <VC_HOST> <VC_ROOT_SSH_PASSWORD> \
  <VC_ADMIN_USER> <VC_ADMIN_PASSWORD> <SUPERVISOR_ID>
```
→ Supervisor가 Software Depot에서 Harbor 이미지를 당겨올 수 있게 함

### 7b. Harbor 서비스 YAML의 이미지 참조 수정
- 원본 이미지 경로를 프록시 경유로 교체:
  `depot-image-proxy.kube-system.svc.cluster.local/supervisor-service-harbor/ga/2.14.2/harbor:v2.14.2_vmware.2-vks.1`
- 이후 Harbor 서비스 등록·설치

## 8단계. VKS 클러스터 배포

### 8a. VKS 서비스 업데이트 (3.6.1 → **3.6.3** 권장)
- 3.6.3 바이너리·YAML을 미리 다운로드·업로드해둔 상태에서 공식 업그레이드 절차 수행

### 8b. 워크로드 클러스터 배포
```bash
kubectl create -f <vksConfig.yaml> -n ns01
kubectl get cluster -n ns01
kubectl describe cluster workload-vsphere-vks1 -n ns01
```
- v1beta1/v1beta2 Cluster API 지원, `podSecurityStandard` 등 변수 구성 가능

### 8c. VKS Standard Packages 설치
```bash
vcf context use supervisor1:ns01:workload-vsphere-vks1
vcf addon available list
vcf addon install create cert-manager \
  --addon-release-name cert-manager.kubernetes.vmware.com.1.19.1-vmware.1-vks.1 \
  --namespace ns01 --cluster-name workload-vsphere-vks1
kubectl get pods -n cert-manager   # 확인
```
> 💡 설치 실패 시: 네임스페이스에 `pod-security.kubernetes.io/enforce=privileged` 라벨 추가 후 ReplicaSet 삭제 → 재생성 유도

---

## 운영 포인트 요약

1. **9.1.0의 최대 개선:** Software Depot 내장 OCI 레지스트리 덕분에 **외부 레지스트리 없이** 에어갭 구성 가능
2. **보안 필수 절차:** Depot OCI 업로드는 무인증 — 이관 끝나면 즉시 disable
3. **파일 이동 순서 엄수:** 인터넷 → Bastion → Admin → Depot → Supervisor
4. **프록시 경유 이미지 참조:** 관리 프록시 사용 시 YAML의 이미지 경로를 `depot-image-proxy.kube-system.svc.cluster.local` 기준으로 수정해야 함
5. **버전 조합:** VCF CLI 9.1.0 + VKS 3.6.3 + VKr 1.34.2 + Standard Packages 3.6.0-20260211이 검증된 BOM
