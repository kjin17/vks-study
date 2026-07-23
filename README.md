# VKS on VCF 9.1 — 아키텍처 소개 & VCF 9.0 → 9.1 변경점

> vSphere Kubernetes Service(VKS, 구 Tanzu Kubernetes Grid Service)
> 작성: CXS · 2026-07
> 출처: Broadcom TechDocs — VKS 3.5 / 3.6 / 3.7 Release Notes, VCF 9.1 Air-Gapped Deploy Guide

이 문서는 OD(Open Design)로 생성한 Broadcom 템플릿 소개 자료(`index.html`)의 텍스트 companion 이다. GitHub Pages로 배포된다.

---

## 1. VKS란?

- **vSphere Supervisor** 위에서 Kubernetes 클러스터의 프로비저닝과 라이프사이클을 관리하는 서비스 (구 TKG Service).
- 핵심 계층: **ESXi/vSAN → vCenter/Supervisor(관리 K8s 컨트롤 플레인) → vSphere Namespace → VKS 워크로드 클러스터(VKr, vSphere Kubernetes Release)**.
- **Cluster API(CAPI) + CAPV(Cluster API Provider vSphere)** 기반. `builtin-generic` ClusterClass로 클러스터 토폴로지를 정의.

## 2. VKS on VCF 9.1 아키텍처

```
┌──────────────────────────────────────────────┐
│ 애드온: CNI(Antrea/Calico/Cilium), cert-manager,│
│         Prometheus … (VKS Standard Packages)   │
├──────────────────────────────────────────────┤
│ VKS 워크로드 클러스터                           │
│   Control Plane (최대 5노드) + Worker Node Pools │
├──────────────────────────────────────────────┤
│ vSphere Namespace (ns)                         │
├──────────────────────────────────────────────┤
│ vCenter / Supervisor (관리 K8s 컨트롤 플레인)    │
├──────────────────────────────────────────────┤
│ ESXi 호스트 / vSAN                              │
└──────────────────────────────────────────────┘
```

- **관리 도구 변화:** 기존 `kubectl-vsphere` 플러그인 → **VCF CLI(`vcf`) + VCF context** 로 통합.
- **이미지/패키지 공급:** VCF 9.1 내장 **Software Depot(OCI 레지스트리)** — 에어갭 환경에서도 외부 레지스트리 없이 구성 가능.
- **애드온:** cert-manager, Prometheus 등 큐레이션된 **VKS Standard Packages**를 `vcf addon`으로 설치. VKr 1.35부터 CNI(Antrea/Calico/Cilium)도 애드온 프레임워크(**AddonConfig**)로 전환.

## 3. VCF 9.0 대비 9.1 변경점 (요약)

| 항목 | VCF 9.0 (VKS 3.5) | VCF 9.1 (VKS 3.6 / 3.7) |
|---|---|---|
| Kubernetes(VKr) | 1.34 | 1.35(3.6) / 1.36(3.7) |
| CLI | kubectl-vsphere 플러그인 | VCF CLI(`vcf`) + VCF context |
| 이미지 레지스트리 | 외부 OCI 레지스트리 필요(에어갭) | 내장 **Software Depot** OCI 레지스트리 |
| ClusterClass | builtin-generic-v3.5.0 | v3.6.0 / v3.7.0 |
| 노드 OS | Photon / Ubuntu | +RHEL 노드(3.6), FIPS 기본 번들(3.7) |
| 커스텀 이미지 | Image Builder | **ImageBaker**(3.6) |
| CNI 구성 | AntreaConfig / CalicoConfig | **AddonConfig** 프레임워크(VKr 1.35+) |
| 컨트롤 플레인 | 3노드 | **최대 5노드**(3.7) |
| 인증 | 기본 | **네이티브 OIDC**(3.7) |
| 워커 확장 | — | **최대 250 노드**(3.7) |

## 4. 9.1 신규 기능 하이라이트

- **5노드 컨트롤 플레인** — 극한 복원력(2노드 동시 손실 복구는 VKr 1.36.1+/1.35.5+/1.34.8+)
- **인플레이스(In-place) 노드 업데이트** — 롤링 재생성 없이 실행 중 노드에 구성 변경 적용
- **kube-proxy 비활성화 API** — Cilium 등 자체 프록시 CNI 대상(VKr 1.35+)
- **TLS 프로파일 구성** — `security.minimumTLSProtocol` / `security.tlsCipherSuites` (apiserver·etcd·kubelet 일괄)
- **커스텀 RuntimeClass** — ContainerD ulimit 등 DB 워크로드 대응
- **etcd 튜닝** — 최대 요청 크기 조정(대용량 GitOps 트랜잭션 대응)
- **보조 NIC vfio-pci / SR-IOV 바인딩** — Telco 5G Core CNF, DPDK 가속(VMXNET3)
- **CIDR 중복 방지 검증 강화** — Supervisor IP 대역과 Pod/Service CIDR 충돌 차단
- **/usr 읽기 전용 마운트** — Photon, DaemonSet 변조 심층 방어
- **FIPS 기본 번들** — Canonical Pro 구독 불필요(Ubuntu 노드)

## 5. 마이그레이션 / 업그레이드 유의점

- **TKC(TanzuKubernetesCluster) API 지원 완전 제거(3.7)** — VKr 1.32가 마지막. TKC 의존 클러스터는 사전 전환 필요.
- **업그레이드 전 VKr 하한** — VKS 3.6은 VKr 1.32+, VKS 3.7은 VKr 1.33+.
- **ClusterClass 리베이스 필수** — 새 K8s 버전 업그레이드 전 v3.6.0 / v3.7.0 으로 리베이스.
- **에어갭 vs 인터넷 연결 YAML 구분** — 에어갭 vCenter 9.1은 "legacy" 서비스 YAML(공개 레지스트리 참조), 인터넷 연결 vCenter 9.1은 Software Depot 참조 YAML. 잘못 선택 시 이미지 해석 실패.

## 6. 마무리

> VCF 9.1의 VKS는 **내장 Software Depot + VCF CLI 통합 + K8s 1.36 + 엔터프라이즈 복원력/보안(5노드 CP, OIDC, TLS 프로파일, FIPS)** 으로 프로덕션 운영 성숙도를 크게 끌어올린 릴리스다.

---

_출처: Broadcom TechDocs (VKS 3.5/3.6/3.7 Release Notes, VCF 9.1 Air-Gapped Deploy Guide). 본 자료는 공개 문서 기반 학습용 정리._
