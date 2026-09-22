#!/usr/bin/env python3
"""VKS 고급 네트워킹 덱(Cilium · Hubble · Multus) 생성기.

기존 `docs/VKS_AirGapped_VCF91_Deploy_KR.html` 의 <style> 블록을 그대로 재사용해
같은 Broadcom 템플릿 레이아웃을 유지한다. 스타일을 복제하지 않고 추출하므로,
원본 덱의 스타일이 바뀌면 다시 돌리기만 하면 된다.

    python3 exports/build_netdeck.py
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "VKS_AirGapped_VCF91_Deploy_KR.html"
OUT = ROOT / "docs" / "VKS_Advanced_Networking_KR.html"

TITLE = "VKS 고급 네트워킹 — Cilium · Hubble · Multus"
STORAGE_KEY = "vks-advanced-networking-pos"

# 원본 덱의 .code 는 white-space 지정이 없어 <br>·&nbsp; 로 줄을 만든다.
# 이 덱은 코드 블록을 그대로 붙여 넣는 방식이라 pre-wrap 을 얹는다.
# (원본 스타일은 건드리지 않고 뒤에 덧붙이기만 한다)
STYLE_OVERRIDE = """<style>
  .code { white-space: pre-wrap; overflow-wrap: anywhere; }
  .split .codeblk { gap: 10px; }   /* 코드 2블록 슬라이드가 푸터를 4px 덮어서 */
  .l-thanks .contact { top: 296px; font-size: 14.5px; line-height: 1.72; }
</style>"""

BRAND = '<div class="brand-mark">VMware <span>by Broadcom</span></div>'
COPY = (
    "Broadcom Proprietary and Confidential. Copyright © 2025 Broadcom. All Rights Reserved. "
    "The term “Broadcom” refers to Broadcom Inc. and/or its subsidiaries."
)

def swoosh_left(uid: str) -> str:
    """왼쪽 스우시. gradient id 는 슬라이드마다 달라야 한다 —
    id 가 겹치면 브라우저가 첫 번째(숨겨진 슬라이드 안의) 정의를 잡아
    fill 이 통째로 비어 버린다. 실제로 Thanks 슬라이드에서 한 번 겪었다."""
    return f"""      <svg class="swoosh" style="left:0;top:0" width="560" height="720" viewBox="0 0 560 720" fill="none">
        <defs>
          <linearGradient id="{uid}" x1="0" y1="720" x2="560" y2="0" gradientUnits="userSpaceOnUse">
            <stop stop-color="#61A00A"/><stop offset="1" stop-color="#007A86"/>
          </linearGradient>
        </defs>
        <path d="M0 0 H560 C 380 60 300 180 300 380 C 300 560 220 680 0 720 Z" fill="url(#{uid})"/>
        <path d="M560 14 C 388 76 316 192 316 380 C 316 556 240 672 40 720" stroke="#0193C2" stroke-width="3" fill="none"/>
      </svg>"""


def swoosh_right(uid: str, c1: str, c2: str) -> str:
    return f"""      <svg class="swoosh" style="right:0;top:0;left:auto" width="480" height="720" viewBox="0 0 480 720" fill="none">
        <defs><linearGradient id="{uid}" x1="480" y1="0" x2="0" y2="720" gradientUnits="userSpaceOnUse"><stop stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>
        <path d="M480 0 V720 H120 C 300 640 360 520 360 360 C 360 200 300 80 200 0 Z" fill="url(#{uid})"/>
        <path d="M186 0 C 288 84 346 202 346 360 C 346 522 286 644 100 720" stroke="#0193C2" stroke-width="3" fill="none"/>
      </svg>"""


# --------------------------------------------------------------------------
# 슬라이드 정의: (screen_label, css_class, inner_html)
# 페이지 번호와 footer 는 렌더 단계에서 자동으로 붙는다.
# --------------------------------------------------------------------------
SLIDES: list[tuple[str, str, str]] = []


def slide(label: str, cls: str, body: str) -> None:
    SLIDES.append((label, cls, body))


# 1 · Title -----------------------------------------------------------------
slide(
    "01 Title",
    "l-title",
    swoosh_left("gTitleLeaf")
    + """
      <div class="title-block">
        <div class="eyebrow">VCF 9.1 · VKS 3.6 / 3.7</div>
        <h1>VKS 고급 네트워킹<br>Cilium · Hubble · Multus</h1>
        <div class="rule"></div>
        <div class="subtitle">eBPF 데이터플레인으로 CNI를 바꾸고, 플로우를 관측하고, 파드에 전용 NIC를 붙이는 세 갈래를 한 번에 정리합니다.</div>
      </div>
      <div class="meta">
        <b>대상</b> · VKS 플랫폼·운영 엔지니어, Telco/CNF 담당<br>
        기준 릴리스 : VKS 3.6 / 3.7 · VKr 1.35~1.36
      </div>""",
)

# 2 · Agenda ----------------------------------------------------------------
slide(
    "02 Agenda",
    "l-agenda",
    """      <div class="head"><h2>목차</h2><div class="bar"></div></div>
      <ol>
        <li><span class="num">01</span><span><span class="item-title">전체 지도</span><div class="item-sub">CNI 선택지와 「두 개의 층」</div></span></li>
        <li><span class="num">02</span><span><span class="item-title">Cilium CNI</span><div class="item-sub">애드온 프레임워크 · 설치 4단계</div></span></li>
        <li><span class="num">03</span><span><span class="item-title">kube-proxy 없이 돌리기</span><div class="item-sub">immutable 결정 · 고급 기능의 전제</div></span></li>
        <li><span class="num">04</span><span><span class="item-title">Hubble 연동</span><div class="item-sub">Server / Relay / UI · 플로우 관측</div></span></li>
        <li><span class="num">05</span><span><span class="item-title">노드 보조 NIC</span><div class="item-sub">networks 변수 · NSX VPC / VDS</div></span></li>
        <li><span class="num">06</span><span><span class="item-title">Multus 멀티 NIC 파드</span><div class="item-sub">NAD · Whereabouts · SR-IOV</div></span></li>
      </ol>""",
)

# 3 · Section 01 ------------------------------------------------------------
slide(
    "03 Section-전체지도",
    "l-section",
    swoosh_right("gLeaf2", "#61A00A", "#007A86")
    + """
      <div class="sec-num">SECTION 01</div>
      <h2>전체 지도</h2>
      <div class="sec-sub">세 주제를 각각 배우기 전에, VKS 안에서 서로 어떻게 맞물리는지부터 봅니다.</div>""",
)

# 4 · CNI 선택지 ------------------------------------------------------------
slide(
    "04 CNI 선택지",
    "l-data",
    """      <div class="head"><h2>VKS의 CNI 선택지</h2><div class="sub">Antrea가 전략적 기본이고, Cilium은 VKS 3.6에 합류한 <b>대안</b>입니다</div></div>
      <table style="top:180px">
        <tr><th>CNI</th><th>VKS에서의 위치</th><th>지원 티어</th><th>도입</th></tr>
        <tr><td><b>Antrea</b></td><td>전략적 기본 CNI · NSX 어댑터 · 하이브리드 캡슐화 · 파드 멀티 NIC</td><td>VKr 내장</td><td>기존</td></tr>
        <tr><td><b>Calico</b></td><td>내장 대안 CNI · VPC 모드 + Multus 조합의 기준</td><td>VKr 내장</td><td>기존</td></tr>
        <tr><td><b>Cilium</b></td><td>eBPF 데이터플레인 · Hubble 관측성 · L7 정책 · kube-proxy 대체</td><td><b>Ecosystem</b></td><td>VKS 3.6 / VKr 1.35</td></tr>
      </table>
      <div class="callout warn" style="position:absolute;left:64px;right:64px;top:400px">
        <div class="ico">!</div>
        <div><b>티어를 먼저 보세요.</b> Ecosystem 티어는 패키징·서명·라이프사이클까지만 지원하고 <b>런타임 문제는 Broadcom 지원 범위 밖</b>입니다. 내장 CNI나 Product 티어 애드온과 지원 성격이 다르므로, 프로덕션 도입 결정에 이 차이를 반드시 반영하세요.</div>
      </div>
      <div class="callout tip" style="position:absolute;left:64px;right:64px;top:520px">
        <div class="ico">i</div>
        <div>CNI 관리 방식도 바뀌었습니다. <b>ClusterBootstrap 의 cni 필드 · AntreaConfig · CalicoConfig 는 폐기</b>되고 VKr 1.35+ 에서 <b>bootstrapAddons 변수 + AddonConfig</b> 로 전환됩니다. 예전 문서를 따라가다 여기서 막히는 경우가 많습니다.</div>
      </div>""",
)

# 5 · 두 개의 층 ------------------------------------------------------------
slide(
    "05 두 개의 층",
    "l-two",
    """      <div class="head"><h2>멀티 NIC은 「두 개의 층」이다</h2><div class="sub">이걸 안 가르면 설계도 트러블슈팅도 어긋납니다</div></div>
      <div class="cols">
        <div class="card aqua">
          <div class="card-tag">Layer 2 · 인프라</div>
          <h3>노드 보조 NIC (eth1~eth9)</h3>
          <ul>
            <li>단위 = <b>노드 VM</b>. 그 노드의 모든 파드가 공유</li>
            <li><b>CAPV / vm-operator</b> 가 담당 — CNI 와 무관</li>
            <li><code>networks</code> 변수로 선언 · VKS 3.6</li>
            <li>쓰는 곳 : NFS 스토리지·DB 복제 등 <b>노드 전체 트래픽 분리</b></li>
          </ul>
        </div>
        <div class="card leaf">
          <div class="card-tag">Layer 3 · 파드</div>
          <h3>파드 멀티 NIC (net1, net2 …)</h3>
          <ul>
            <li>단위 = <b>개별 파드</b>. 파드마다 전용 인터페이스·전용 IP</li>
            <li><b>Multus</b>(VKS 3.7) 또는 <b>Antrea SecondaryNetwork</b>(3.6)</li>
            <li><code>NetworkAttachmentDefinition</code> + 파드 어노테이션</li>
            <li>쓰는 곳 : CNF·멀티캐스트 등 <b>특정 워크로드 전용 경로</b></li>
          </ul>
        </div>
      </div>
      <div class="callout warn" style="position:absolute;left:64px;right:64px;bottom:76px">
        <div class="ico">!</div>
        <div><b>eth1 을 붙여도 트래픽은 안 나뉩니다.</b> 파드는 계속 eth0 을 쓰고, eth1 에는 <b>기본 경로가 없습니다</b>. 보안 가치는 <b>위상</b>에 있습니다 — API 서버는 eth0 서브넷에서만 듣기 때문에, eth1 에만 연결된 것은 컨트롤 플레인에 물리적으로 닿지 못합니다.</div>
      </div>""",
)

# 6 · Section 02 ------------------------------------------------------------
slide(
    "06 Section-Cilium",
    "l-section",
    swoosh_right("gAqua2", "#0193C2", "#005B84")
    + """
      <div class="sec-num">SECTION 02</div>
      <h2>Cilium CNI</h2>
      <div class="sec-sub">애드온 프레임워크의 리소스 지도를 먼저 잡고, 설치 4단계를 따라갑니다.</div>""",
)

# 7 · 애드온 리소스 지도 ----------------------------------------------------
slide(
    "07 애드온 리소스 지도",
    "l-data",
    """      <div class="head"><h2>애드온 프레임워크 — 리소스 지도</h2><div class="sub">VKS 3.5부터 애드온이 선언적 API로 전환. Cilium 설치는 이 리소스를 순서대로 쌓는 일입니다</div></div>
      <table style="top:176px">
        <tr><th>리소스</th><th>위치</th><th>역할</th></tr>
        <tr><td><span class="mono">AddonRepository(Install)</span></td><td>vmware-system-vks-public</td><td>패키지 저장소 정의 · 클러스터 바인딩</td></tr>
        <tr><td><span class="mono">AddonRelease</span></td><td>vmware-system-vks-public</td><td>버전의 불변 메타데이터 — 호환 제약·의존성</td></tr>
        <tr><td><span class="mono">AddonConfigDefinition</span></td><td>vmware-system-vks-public</td><td><b>설정 스키마</b> — AddonConfig 를 검증하는 정본</td></tr>
        <tr><td><b><span class="mono">AddonInstall</span></b></td><td>클러스터 ns 또는 public</td><td><b>원하는 애드온 상태 선언</b> — 우리가 만드는 것</td></tr>
        <tr><td><span class="mono">ClusterAddon</span></td><td>클러스터 ns</td><td>클러스터별 인스턴스 + 상태 보고</td></tr>
        <tr><td><b><span class="mono">AddonConfig</span></b></td><td>클러스터 ns</td><td><b>스키마 검증되는 설정값</b> — Hubble 을 켜는 자리</td></tr>
      </table>
      <div class="callout warn" style="position:absolute;left:64px;right:64px;top:520px">
        <div class="ico">!</div>
        <div><b>VKS 3.7 저장소 모델 변경</b> — 단일 저장소 갱신이 아니라 <b>버전별 추가(additive)</b> 방식입니다. 3.5/3.6 에서 올라온 환경의 <span class="mono">default-addon-repo-install</span> 은 deprecated 이며, 불필요한 리소스는 <b>관리자가 직접 삭제</b>해야 합니다.</div>
      </div>""",
)

# 8 · 버전 타임라인 ---------------------------------------------------------
slide(
    "08 버전 타임라인",
    "l-data",
    """      <div class="head"><h2>전제 조건과 버전</h2><div class="sub">Cilium 은 클러스터 생성 <b>전에</b> 준비가 끝나 있어야 합니다 — 사후에 끼워 넣는 경로가 아닙니다</div></div>
      <div class="metrics">
        <div class="metric aqua"><div class="big">3.6+</div><div class="label">VKS 버전</div><div class="desc">VKr 1.35 이상 필요</div></div>
        <div class="metric leaf"><div class="big">1.19.4</div><div class="label">Cilium (v3.7.0+20260618)</div><div class="desc">최초 합류는 1.19.1 (v3.6.0+20260320)</div></div>
        <div class="metric plum"><div class="big">4</div><div class="label">열어야 할 포트</div><div class="desc">2379-2380 / 8472 / 4240 / 4244</div></div>
      </div>
      <table>
        <tr><th>애드온 저장소</th><th>Cilium</th><th>주요 내용</th></tr>
        <tr><td>v3.6.0+20260320</td><td><b>1.19.1</b></td><td>대안 CNI 공식 합류 · eBPF 데이터플레인 · Hubble UI/Relay · NetworkPolicy(L3/L4) + CiliumNetworkPolicy(L7)</td></tr>
        <tr><td>v3.7.0+20260618</td><td><b>1.19.4</b></td><td>L7 프록시(Envoy) · Ingress · Egress Gateway · Gateway API · eBPF 마스커레이딩 · XDP 가속 · Prometheus/Hubble 메트릭</td></tr>
      </table>""",
)

# 9 · 설치 4단계 개요 -------------------------------------------------------
slide(
    "09 설치 4단계",
    "l-steps",
    """      <div class="head"><h2>Cilium 설치 4단계</h2><div class="sub">모두 <b>클러스터 생성 전</b>에 끝나 있어야 합니다</div></div>
      <div class="grid" style="grid-template-columns:repeat(4,1fr);grid-template-rows:1fr">
        <div class="step p-sup"><div class="sn">01</div><div class="host">Supervisor</div><div class="st">AddonInstall 생성</div><div class="sd">CEL 제약으로 대상 클러스터를 한정. <b>ownerReference 필수</b></div></div>
        <div class="step p-adm"><div class="sn">02</div><div class="host">선택</div><div class="st">AddonConfig 작성</div><div class="sd">MTU · Hubble 기본값 덮어쓰기. 사후 수정 가능</div></div>
        <div class="step p-dl"><div class="sn">03</div><div class="host">Cluster YAML</div><div class="st">bootstrapAddons</div><div class="sd">CNI 를 cilium 으로 선택. <b>부트스트랩 단계에만</b> 적용</div></div>
        <div class="step p-dep"><div class="sn">04</div><div class="host">Cluster YAML</div><div class="st">방화벽 규칙</div><div class="sd">CP 와 워커에 <b>각각</b> 넣어야 함</div></div>
      </div>
      <div class="callout warn" style="position:absolute;left:64px;right:64px;top:400px">
        <div class="ico">!</div>
        <div><b>Step 1 의 지뢰 — Cluster 를 지워도 AddonInstall 은 남습니다.</b> 라이프사이클을 따로 관리하거나 클러스터에 ownerReference 를 걸어야 합니다. 안 걸면 클러스터를 지우고 다시 만들 때 <b>옛 AddonInstall 이 살아남아</b> 새 클러스터에 의도치 않게 매칭될 수 있습니다. AddonConfig 는 <span class="mono">clusteraddon.addons.kubernetes.vmware.com/owned-for-deletion: "true"</span> 어노테이션으로 처리합니다.</div>
      </div>""",
)

# 10 · Step 1 코드 ----------------------------------------------------------
slide(
    "10 Step1 AddonInstall",
    "l-content",
    """      <div class="head"><h2>Step 1 · AddonInstall</h2><div class="sub">Supervisor 의 클러스터 네임스페이스에 생성</div></div>
      <div class="split">
        <ul class="lead">
          <li><b>CEL 제약</b>으로 「CNI 참조가 cilium 이고 K8s 1.35 이상」일 때만 매칭</li>
          <li>조건을 벗어난 클러스터에 실수로 붙는 것을 막아 줍니다</li>
          <li><b>ownerReference 를 걸어</b> 클러스터와 함께 지워지게 하세요</li>
        </ul>
        <div class="codeblk">
          <div class="codelabel">addoninstall-cilium.yaml</div>
          <div class="code"><span class="cmd">apiVersion:</span> <span class="str">addons.kubernetes.vmware.com/v1alpha1</span>
<span class="cmd">kind:</span> <span class="str">AddonInstall</span>
<span class="cmd">metadata:</span>
  <span class="arg">name:</span> &lt;cluster-name&gt;-cilium
  <span class="arg">namespace:</span> &lt;cluster-namespace&gt;
<span class="cmd">spec:</span>
  <span class="arg">addonRef:</span>
    <span class="arg">name:</span> <span class="str">cilium</span>
  <span class="arg">clusters:</span>
    - <span class="arg">constraints:</span>
        <span class="arg">expression:</span> <span class="str">"cluster.cniRefName() == 'cilium' &amp;&amp;
          version_in_range(cluster.spec.topology.version, '&gt;=1.35.0')"</span>
      <span class="arg">selector:</span>
        <span class="arg">matchLabels:</span>
          <span class="arg">cluster.x-k8s.io/cluster-name:</span> &lt;cluster-name&gt;
      <span class="arg">stopMatchingBehavior:</span> <span class="str">Retain</span></div>
          <div class="code"><span class="pr">$</span> <span class="cmd">kubectl</span> apply <span class="arg">-f</span> addoninstall-cilium.yaml
<span class="pr">$</span> <span class="cmd">kubectl</span> get addoninstall &lt;cluster-name&gt;-cilium <span class="arg">-n</span> &lt;ns&gt;</div>
        </div>
      </div>""",
)

# 11 · Step 2+3 -------------------------------------------------------------
slide(
    "11 Step2-3 AddonConfig-bootstrapAddons",
    "l-content",
    """      <div class="head"><h2>Step 2·3 · AddonConfig 와 bootstrapAddons</h2><div class="sub">설정값은 <b>AddonConfigDefinition 스키마로 검증</b>됩니다 — 임의의 Helm 값이 통과한다고 가정하지 마세요</div></div>
      <div class="split">
        <div class="codeblk">
          <div class="codelabel">Step 2 · AddonConfig (선택)</div>
          <div class="code"><span class="cmd">apiVersion:</span> <span class="str">addons.kubernetes.vmware.com/v1alpha1</span>
<span class="cmd">kind:</span> <span class="str">AddonConfig</span>
<span class="cmd">metadata:</span>
  <span class="arg">name:</span> &lt;cluster-name&gt;-cilium
  <span class="arg">namespace:</span> &lt;cluster-namespace&gt;
  <span class="arg">annotations:</span>
    <span class="c"># 클러스터와 함께 삭제되게 (권장)</span>
    <span class="arg">clusteraddon.addons.kubernetes.vmware.com/owned-for-deletion:</span> <span class="str">"true"</span>
<span class="cmd">spec:</span>
  <span class="arg">values:</span>
    <span class="arg">hubble:</span>
      <span class="arg">enabled:</span> <span class="str">true</span>
      <span class="arg">relay:</span> { <span class="arg">enabled:</span> <span class="str">true</span> }
      <span class="arg">ui:</span> { <span class="arg">enabled:</span> <span class="str">true</span> }</div>
        </div>
        <div class="codeblk">
          <div class="codelabel">Step 3 · spec.topology.variables</div>
          <div class="code"><span class="cmd">- name:</span> <span class="str">bootstrapAddons</span>
  <span class="arg">value:</span>
    <span class="arg">cniRef:</span>
      <span class="arg">name:</span> <span class="str">cilium</span>
      <span class="arg">namespace:</span> <span class="str">vmware-system-vks-public</span></div>
          <ul class="lead" style="margin-top:6px">
            <li>변수 도입 <b>3.6.0</b> · K8s <b>1.35 이상</b>에서만</li>
            <li>적용 범위 : <span class="mono">cluster</span>, <span class="mono">controlPlane</span></li>
            <li><b>초기 부트스트랩 단계</b>에 쓰이므로 클러스터 생성 전 YAML 에 있어야 합니다</li>
          </ul>
        </div>
      </div>""",
)

# 12 · Step 4 방화벽 --------------------------------------------------------
slide(
    "12 Step4 방화벽",
    "l-data",
    """      <div class="head"><h2>Step 4 · 방화벽 4개 포트</h2><div class="sub"><span class="mono">node.firewall.inboundRules</span> — CP 는 topology.variables, 워커는 machineDeployment override</div></div>
      <table style="top:176px">
        <tr><th>포트</th><th>프로토콜</th><th>용도</th><th>컨트롤 플레인</th><th>워커</th></tr>
        <tr><td><b>2379–2380</b></td><td>TCP</td><td>etcd 클라이언트·피어 통신</td><td>✅</td><td>—</td></tr>
        <tr><td><b>8472</b></td><td>UDP</td><td>VXLAN 터널 캡슐화</td><td>✅</td><td>✅</td></tr>
        <tr><td><b>4240</b></td><td>TCP</td><td>Cilium 에이전트 헬스체크</td><td>✅</td><td>✅</td></tr>
        <tr><td><b>4244</b></td><td>TCP</td><td><b>Hubble 서버</b></td><td>✅</td><td>✅</td></tr>
      </table>
      <div class="callout tip" style="position:absolute;left:64px;right:64px;top:420px">
        <div class="ico">i</div>
        <div>여기 정의한 규칙은 <b>클러스터 정상 동작에 필요한 기본 규칙과 병합</b>됩니다 — 기본 규칙을 지우는 게 아니라 얹는 것입니다. <span class="mono">protocol</span> 만 필수이고 <span class="mono">source</span> 를 비우면 모든 출발지에 적용됩니다.</div>
      </div>
      <div class="callout warn" style="position:absolute;left:64px;right:64px;top:530px">
        <div class="ico">!</div>
        <div><b>4개를 한꺼번에 넣으세요.</b> <span class="mono">node</span> 변수 변경은 <b>머신 롤아웃을 유발</b>합니다. 나중에 Hubble 을 켜면서 4244 만 추가하려면 노드를 한 번 더 굴려야 합니다.</div>
      </div>""",
)

# 13 · Section 03 kube-proxy ------------------------------------------------
slide(
    "13 Section-kubeproxy",
    "l-section",
    swoosh_right("gPlum3", "#6C4B8F", "#005B84")
    + """
      <div class="sec-num">SECTION 03</div>
      <h2>kube-proxy 없이<br>돌리기</h2>
      <div class="sec-sub">클러스터를 만들 때 한 번만 정할 수 있는 값입니다. 고급 기능의 전제이기도 합니다.</div>""",
)

# 14 · kube-proxy-free ------------------------------------------------------
slide(
    "14 kube-proxy-free",
    "l-content",
    """      <div class="head"><h2>kube-proxy 비활성화 API</h2><div class="sub">VKS 3.7 · Cilium 의 eBPF 서비스 구현으로 kube-proxy 를 대체</div></div>
      <div class="split">
        <div class="codeblk">
          <div class="codelabel">spec.topology.variables</div>
          <div class="code"><span class="cmd">- name:</span> <span class="str">kubernetes</span>
  <span class="arg">value:</span>
    <span class="arg">kubeProxyConfiguration:</span>
      <span class="arg">enabled:</span> <span class="str">false</span></div>
          <div class="codelabel" style="margin-top:12px">스펙과 제약</div>
          <div class="code"><span class="c"># 적용 범위   cluster 스코프만</span>
<span class="c"># 변경 가능성 immutable</span>
<span class="c"># 변경 영향   머신 롤아웃</span>
<span class="c"># CNI 제약    Antrea · KR 내장 Calico 미지원</span>
<span class="c">#             커스텀 CNI 는 KR 1.35 이상</span></div>
        </div>
        <ul class="lead">
          <li><b>이 기능들은 kube-proxy 가 켜져 있으면 검증 오류</b>가 납니다 (Cilium 1.19.4)
            <ul>
              <li>L7 프록시 (Envoy 기반 L7 정책)</li>
              <li>Ingress 컨트롤러 · Gateway API 컨트롤러</li>
              <li>Egress Gateway (SNAT)</li>
              <li>eBPF 마스커레이딩</li>
            </ul>
          </li>
          <li>즉 「Cilium 의 좋은 기능을 쓰고 싶다」는 요구는 곧 <b>「클러스터를 만들 때 kube-proxy 를 끄고 시작해야 한다」</b>는 설계 결정입니다</li>
        </ul>
      </div>""",
)

# 15 · Big statement --------------------------------------------------------
slide(
    "15 Big-설정값과동작",
    "l-big",
    """      <div class="eyebrow" style="position:absolute;left:90px;top:150px">KNOWN ISSUE · VKS 3.7</div>
      <div class="statement">설정값이 아니라 <em>동작</em>을 재세요.<br>「비활성화로 표시되는데<br>계속 동작한다」</div>
      <div style="position:absolute;left:90px;right:90px;top:492px;font-size:16px;line-height:1.6;color:#b9bdd0">
        클러스터 <b style="color:#fff">생성 시</b> <span class="mono">kubernetes.kubeProxyConfiguration</span> 을 명시하지 않으면, 생성 후에 <span class="mono">enabled</span> 를 false 로 바꾸는 것이 허용됩니다. 그런데 실제 kube-proxy 는 계속 동작해서 <b style="color:#fff">상태 표시와 실제 동작이 어긋납니다.</b><br>
        <b style="color:#fff">워크어라운드</b> — 활성/비활성은 반드시 <b style="color:#fff">클러스터 생성 시점에 명시</b>하고, 생성 후에는 바꾸지 마세요.
      </div>""",
)

# 16 · Cilium 알려진 문제 ---------------------------------------------------
slide(
    "16 Cilium 알려진 문제",
    "l-data",
    """      <div class="head"><h2>Cilium 알려진 문제 · 비호환</h2><div class="sub">클러스터를 만들기 전에 답해야 하는 항목들</div></div>
      <table style="top:176px">
        <tr><th>증상</th><th>원인</th><th>대응</th></tr>
        <tr><td><b>혼합 OS 클러스터가 Ready 안 됨</b></td><td>Cilium 이 Windows 를 지원하지 않아 Windows 워커가 Not Ready</td><td>Windows 워커가 필요하면 다른 CNI. Cilium 을 쓰려면 <b>Linux(Photon) 워커만</b></td></tr>
        <tr><td><b>Istio 애드온 설치 실패</b></td><td>현 Cilium 애드온 버전의 제약으로 <b>Istio 애드온과 비호환</b></td><td>서비스 메시가 필수면 CNI 선택 재검토</td></tr>
        <tr><td>kube-proxy 상태 불일치</td><td>생성 후 플래그 변경이 허용됨</td><td>생성 시점에 명시</td></tr>
      </table>
      <div class="callout warn" style="position:absolute;left:64px;right:64px;top:430px">
        <div class="ico">!</div>
        <div><b>워커 노드 보조 NIC 도 Windows 미지원</b>입니다. Cilium + Multus + Windows 를 한 클러스터에 넣으려는 설계는 <b>두 군데서 막힙니다</b>. Windows 워크로드가 있는 환경이라면 이 세 가지 조합 자체를 설계 초기에 걸러내세요.</div>
      </div>""",
)

# 17 · Section 04 Hubble ----------------------------------------------------
slide(
    "17 Section-Hubble",
    "l-section",
    swoosh_right("gLeaf4", "#61A00A", "#007A86")
    + """
      <div class="sec-num">SECTION 04</div>
      <h2>Hubble 연동</h2>
      <div class="sec-sub">eBPF 데이터플레인이 본 플로우를 그대로 올려 줍니다. 사이드카도 앱 수정도 없습니다.</div>""",
)

# 18 · Hubble 3층 -----------------------------------------------------------
slide(
    "18 Hubble 3층",
    "l-data",
    """      <div class="head"><h2>Hubble 3층 구조</h2><div class="sub">「Cilium 을 깔면 Hubble 이 켜져 있다」는 절반만 맞습니다</div></div>
      <table style="top:176px">
        <tr><th>계층</th><th>범위</th><th>AddonConfig 값</th><th>기본값</th></tr>
        <tr><td><b>Hubble UI</b> — 웹 대시보드·서비스 맵</td><td>클러스터 전체</td><td><span class="mono">hubble.ui.enabled</span></td><td><b>false</b> (Relay 필요)</td></tr>
        <tr><td><b>Hubble Relay</b> — 플로우 집계</td><td>클러스터 전체</td><td><span class="mono">hubble.relay.enabled</span></td><td><b>false</b></td></tr>
        <tr><td><b>Hubble Server</b> — cilium-agent 내장 · TCP 4244</td><td>노드 1대</td><td><span class="mono">hubble.enabled</span></td><td><b>true</b></td></tr>
        <tr><td>서비스 노출 방식</td><td>UI</td><td><span class="mono">hubble.ui.service.type</span></td><td>ClusterIP</td></tr>
      </table>
      <div class="callout warn" style="position:absolute;left:64px;right:64px;top:440px">
        <div class="ico">!</div>
        <div><span class="mono">hubble.enabled</span> 가 기본 true 라 켜져 있다고 읽기 쉽지만, 그건 <b>노드 단위 서버</b>만 돌고 있다는 뜻입니다. 클러스터 전체를 한눈에 보는 경험(Relay · UI)은 <b>명시적으로 켜야</b> 생깁니다. 그리고 Relay 는 각 노드의 <b>TCP 4244</b> 로 붙습니다 — 워커에 이 포트가 안 열려 있으면 <b>Relay 는 Running 인데 그 노드 플로우만 조용히 빠집니다.</b></div>
      </div>""",
)

# 19 · Hubble 접근 ----------------------------------------------------------
slide(
    "19 Hubble 접근과 검증",
    "l-content",
    """      <div class="head"><h2>접근 · 검증</h2><div class="sub">Hubble 의 실전 가치는 대시보드 구경이 아니라 「왜 막혔는가」를 즉시 답하는 것</div></div>
      <div class="split">
        <div class="codeblk">
          <div class="codelabel">UI · CLI 접근</div>
          <div class="code"><span class="c"># UI (ClusterIP 기본)</span>
<span class="pr">$</span> <span class="cmd">kubectl</span> port-forward <span class="arg">-n</span> kube-system svc/hubble-ui <span class="str">12000:80</span>

<span class="c"># Relay 에 붙어 플로우 보기</span>
<span class="pr">$</span> <span class="cmd">kubectl</span> port-forward <span class="arg">-n</span> kube-system svc/hubble-relay <span class="str">4245:80</span>
<span class="pr">$</span> <span class="cmd">hubble</span> observe <span class="arg">--server</span> localhost:4245 <span class="arg">-f</span>

<span class="c"># 정책 때문에 막힌 트래픽만</span>
<span class="pr">$</span> <span class="cmd">hubble</span> observe <span class="arg">--verdict</span> <span class="str">DROPPED</span> <span class="arg">--type</span> <span class="str">policy-verdict</span></div>
          <div class="codelabel" style="margin-top:12px">검증 — 노드 수를 대조</div>
          <div class="code"><span class="pr">$</span> <span class="cmd">hubble</span> status <span class="arg">--server</span> localhost:4245
<span class="c"># 연결된 노드 수 == 실제 노드 수 인가?</span></div>
        </div>
        <ul class="lead">
          <li><b>파드가 Running 인 것은 「떴다」이지 「보고 있다」가 아닙니다.</b> 4244 가 일부 노드풀에만 열려 있으면 Relay 는 정상 기동한 채로 그 노드들의 플로우를 빠뜨립니다 — 에러로 안 나타납니다</li>
          <li><b>Hubble UI 에는 인증이 없습니다.</b> LoadBalancer 로 열면 네트워크에 닿는 누구나 클러스터 전체 통신 그래프를 봅니다</li>
          <li><b>보조 NIC 에는 LoadBalancer 를 못 붙입니다</b> — Service type LoadBalancer 는 항상 primary 에 생깁니다</li>
          <li>Hubble 은 기본적으로 <b>링 버퍼</b> — 장기 보관 도구가 아닙니다. 과거 사건 조사는 메트릭·로그로 따로 내보내세요</li>
        </ul>
      </div>""",
)

# 20 · Section 05 Multus ----------------------------------------------------
slide(
    "20 Section-노드NIC",
    "l-section",
    swoosh_right("gAqua5", "#0193C2", "#005B84")
    + """
      <div class="sec-num">SECTION 05</div>
      <h2>노드 보조 NIC</h2>
      <div class="sec-sub">파드에 NIC 를 붙이기 전에, 노드에 케이블을 까는 단계입니다. CNI 와 무관합니다.</div>""",
)

# 21 · networks 변수 --------------------------------------------------------
slide(
    "21 networks 변수",
    "l-content",
    """      <div class="head"><h2>networks 변수 · 인프라 준비</h2><div class="sub">NSX VPC 는 Subnet/SubnetSet, VDS 는 Network — API 그룹만 다르고 패턴은 같습니다</div></div>
      <div class="split">
        <div class="codeblk">
          <div class="codelabel">① NSX VPC · Subnet (클러스터 생성 전)</div>
          <div class="code"><span class="cmd">kind:</span> <span class="str">Subnet</span>   <span class="c"># crd.nsx.vmware.com/v1alpha1</span>
<span class="cmd">spec:</span>
  <span class="arg">accessMode:</span> <span class="str">Private</span>
  <span class="arg">subnetDHCPConfig:</span>
    <span class="arg">mode:</span> <span class="str">DHCPDeactivated</span>      <span class="c"># 필수</span>
  <span class="arg">advancedConfig:</span>
    <span class="arg">staticIPAllocation:</span>
      <span class="arg">enabled:</span> <span class="str">false</span>          <span class="c"># 필수 · IP 고갈 방지</span></div>
          <div class="codelabel" style="margin-top:10px">② Cluster · spec.topology.variables</div>
          <div class="code"><span class="cmd">- name:</span> <span class="str">networks</span>
  <span class="arg">value:</span>
    <span class="arg">interfaces:</span>
      <span class="arg">secondary:</span>        <span class="c"># primary 생략이 기본</span>
        - <span class="arg">name:</span> <span class="str">eth1</span>              <span class="c"># eth0 불가 · mtu 9000 = 점보</span>
          <span class="arg">network:</span>
            <span class="arg">apiVersion:</span> <span class="str">crd.nsx.vmware.com/v1alpha1</span>
            <span class="arg">kind:</span> <span class="str">Subnet</span>
            <span class="arg">name:</span> <span class="str">secondary-node-net</span></div>
        </div>
        <ul class="lead">
          <li><b>staticIPAllocation: false 는 권고가 아니라 필수</b>입니다. 켜져 있으면 노드가 프로비저닝될 때마다 정적 IP 를 소비하는데 <b>롤링 업데이트에서 반환되지 않아</b> 서브넷이 고갈됩니다</li>
          <li><b>VDS 는 포트그룹 3종을 모두</b> — trunk 모드 · Forged Transmits · MAC Learning. <b>둘만 맞춰도 노드는 정상으로 뜨고</b>, 고장은 나중에 파드 보조 NIC 통신 불가로 나타납니다. 이걸 가리키는 이벤트나 에러가 없어 디버깅이 가장 긴 지점입니다</li>
          <li><b>primary 는 영구</b>입니다 — 생성 후 변경 불가. <span class="mono">SubnetSet</span> 만 참조 가능하고, 대부분의 배포는 <b>생략이 정답</b>입니다</li>
          <li>eth1 에 목적을 주려면 <span class="mono">routes</span>(<span class="mono">to</span> / <span class="mono">via</span>) 를 추가합니다 — <b>CloudInit 부트스트랩 전용 · IPv4만</b></li>
          <li>기존 클러스터에 <b>추가는 가능</b>합니다 — 롤링 노드 업데이트로 적용</li>
        </ul>
      </div>""",
)

# 22 · Section 06 파드 멀티 NIC ---------------------------------------------
slide(
    "22 Section-Multus",
    "l-section",
    swoosh_right("gPlum6", "#6C4B8F", "#005B84")
    + """
      <div class="sec-num">SECTION 06</div>
      <h2>Multus<br>멀티 NIC 파드</h2>
      <div class="sec-sub">노드에 깐 케이블에 파드를 꽂는 단계입니다. VKS 3.7 · Product 티어.</div>""",
)

# 23 · Multus 애드온과 NAD --------------------------------------------------
slide(
    "23 Multus NAD",
    "l-content",
    """      <div class="head"><h2>Multus · Whereabouts</h2><div class="sub">Multus 4.2.4 + Whereabouts 0.9.3 · <b>Product 티어</b>(런타임까지 Broadcom 완전 지원) · v3.7.0+20260618</div></div>
      <div class="split">
        <div class="codeblk">
          <div class="codelabel">NetworkAttachmentDefinition</div>
          <div class="code"><span class="cmd">apiVersion:</span> <span class="str">k8s.cni.cncf.io/v1</span>
<span class="cmd">kind:</span> <span class="str">NetworkAttachmentDefinition</span>
<span class="cmd">metadata:</span>
  <span class="arg">name:</span> <span class="str">macvlan-conf</span>
<span class="cmd">spec:</span>
  <span class="arg">config:</span> <span class="str">'{</span>
    <span class="str">"type": "macvlan",</span>
    <span class="str">"master": "eth1",</span>        <span class="c">← 노드 보조 NIC</span>
    <span class="str">"mode": "bridge",</span>
    <span class="str">"ipam": {</span>
      <span class="str">"type": "whereabouts",</span>  <span class="c">← 클러스터 범위 IPAM</span>
      <span class="str">"range": "192.168.100.0/24"</span>
    <span class="str">} }'</span></div>
          <div class="codelabel" style="margin-top:10px">파드에 붙이기</div>
          <div class="code"><span class="cmd">metadata:</span>
  <span class="arg">annotations:</span>
    <span class="arg">k8s.v1.cni.cncf.io/networks:</span> <span class="str">macvlan-conf</span>
<span class="c"># 결과: lo · eth0(주 CNI) · net1(보조)</span></div>
        </div>
        <ul class="lead">
          <li><b>master: eth1 에서 두 층이 만납니다.</b> 노드의 <span class="mono">eth1</span> 과 파드의 <span class="mono">net1</span> 은 <b>다른 것</b>입니다 — 문서·코드에 층을 명시하세요</li>
          <li><b>IPAM 은 Whereabouts</b> 를 쓰세요. <span class="mono">host-local</span> 은 노드별로 독립이라 여러 노드에 걸치면 <b>IP 충돌</b>이 납니다</li>
          <li>대상은 <b>VPC 모드 Calico CNI 클러스터</b>. VKr 1.36 미만 + Calico 는 클러스터 생성 전에 <b>autodetect 인터페이스를 eth0 으로 고정</b>하는 사전 구성이 필요합니다 — 노드에 NIC 가 여러 개 생기는 순간 Calico 가 엉뚱한 NIC 를 고를 수 있습니다</li>
          <li>네이티브 대안 : <b>Antrea SecondaryNetwork + AntreaIPAM</b> (VKS 3.6)</li>
        </ul>
      </div>""",
)

# 24 · SR-IOV ---------------------------------------------------------------
slide(
    "24 SR-IOV vfio-pci",
    "l-content",
    """      <div class="head"><h2>SR-IOV · DPDK — vfio-pci 바인딩</h2><div class="sub">VKS 3.7 · Telco 5G Core CNF 등 DPDK 가속 워크로드</div></div>
      <div class="split">
        <div class="codeblk">
          <div class="codelabel">networks.interfaces.secondary</div>
          <div class="code">- <span class="arg">name:</span> <span class="str">eth1</span>
  <span class="arg">network:</span>
    <span class="arg">apiVersion:</span> <span class="str">netoperator.vmware.com/v1alpha1</span>
    <span class="arg">kind:</span> <span class="str">Network</span>
    <span class="arg">name:</span> <span class="str">sriov-portgroup</span>
  <span class="arg">driver:</span> <span class="str">vfio-pci</span>          <span class="c"># 현재 유일한 값</span>
  <span class="arg">sriovResourcePool:</span>
    <span class="arg">prefix:</span> <span class="str">intel.com</span>
    <span class="arg">name:</span> <span class="str">sriov_netdevice</span></div>
          <div class="codelabel" style="margin-top:12px">파드는 표준 리소스 요청으로 가져감</div>
          <div class="code"><span class="cmd">resources:</span>
  <span class="arg">requests:</span>
    <span class="arg">intel.com/sriov_netdevice:</span> <span class="str">"1"</span></div>
        </div>
        <ul class="lead">
          <li><span class="mono">driver</span> 를 지정하면 <span class="mono">sriovResourcePool</span> 을 <b>함께</b> 설정해야 하고, <span class="mono">name</span>·<span class="mono">prefix</span> 둘 다 필수입니다</li>
          <li><b>SR-IOV VLAN 태깅은 VDS 전용</b> — NSX VPC 는 아직 미지원</li>
          <li>관련 애드온 : SR-IOV Plugin 3.11.0</li>
        </ul>
      </div>
      <div class="callout warn" style="position:absolute;left:64px;right:64px;bottom:76px">
        <div class="ico">!</div>
        <div><b>vIOMMU 경고 — 보안에 직결됩니다.</b> 노드 VM 에 vIOMMU 가 활성화돼 있지 않으면 머신 에이전트가 <b>VFIO unsafe no-IOMMU 모드를 자동으로 켭니다</b>. 이 경우 디바이스의 <b>DMA 가 IOMMU 로 보호되지 않습니다</b>. 자동 폴백이 경고 없이 격리 보장을 낮추는 자리이므로, <b>프로덕션에서는 vIOMMU 를 켜고</b> 인수인계 문서에 그 상태를 명시하세요.</div>
      </div>""",
)

# 25 · 제약과 스케일 --------------------------------------------------------
slide(
    "25 제약과 스케일",
    "l-data",
    """      <div class="head"><h2>현재 못 하는 것 · 스케일 조정</h2><div class="sub">설계 전에 반드시 읽을 것</div></div>
      <div class="metrics">
        <div class="metric aqua"><div class="big">250</div><div class="label">워커 노드 상한 (3.7)</div><div class="desc">기존 150 → 250. 단, 아래 조정이 전제</div></div>
        <div class="metric leaf"><div class="big">6 vCPU</div><div class="label">CP VM 클래스 (Calico+Multus+AVI)</div><div class="desc">Antrea+AVI 는 4 vCPU / 12 GiB</div></div>
        <div class="metric plum"><div class="big">1.5 Gi</div><div class="label">Multus 메모리 제한</div><div class="desc">안 올리면 OOMKilled</div></div>
      </div>
      <table>
        <tr><th>제약</th><th>의미</th></tr>
        <tr><td><b>보조 네트워크에 LoadBalancer 불가</b></td><td>Service type LoadBalancer 는 <b>항상 primary</b> 에 생성됩니다</td></tr>
        <tr><td><b>보조 인터페이스에 NetworkPolicy 미적용</b></td><td>eth1 이상의 트래픽은 <b>K8s 정책 계층에서 필터링되지 않습니다</b></td></tr>
        <tr><td><b>NSX-T T1 미지원</b> · <b>Windows 노드 풀 불가</b></td><td>지원 백엔드는 NSX VPC 와 VDS. etcd DB 는 4 GB 이상, Pod CIDR 은 /15~/14</td></tr>
      </table>""",
)

# 26 · 체크리스트 -----------------------------------------------------------
slide(
    "26 체크리스트",
    "l-two",
    """      <div class="head"><h2>클러스터를 만들기 전에 답할 것</h2><div class="sub">생성 후에는 못 바꾸거나 롤아웃을 유발하는 항목들</div></div>
      <div class="cols">
        <div class="card aqua">
          <div class="card-tag">Cilium · Hubble</div>
          <ul>
            <li><b>Ecosystem 티어</b>의 지원 범위를 수용했는가</li>
            <li>VKS 3.6+ / VKr 1.35+ · 애드온 저장소 설치됐는가</li>
            <li><b>kube-proxy 를 끌 것인가</b> — immutable, 생성 시점 결정</li>
            <li>방화벽 <b>4개 포트</b>를 CP·워커에 각각 넣었는가</li>
            <li><b>ownerReference / owned-for-deletion</b> 을 걸었는가</li>
            <li>Windows 워커 · Istio 애드온이 필요한가 (필요 시 Cilium 불가)</li>
            <li><span class="mono">hubble status</span> 의 연결 노드 수 = 실제 노드 수 인가</li>
          </ul>
        </div>
        <div class="card plum">
          <div class="card-tag">멀티 NIC</div>
          <ul>
            <li>NSX VPC : <span class="mono">DHCPDeactivated</span> + <span class="mono">staticIPAllocation: false</span></li>
            <li>VDS : 포트그룹 <b>3종 모두</b> (trunk·Forged·MAC Learning)</li>
            <li><b>primary 는 생략</b>해도 되는가 (대부분 정답)</li>
            <li><b>제거 불가를 전제로</b> 설계했는가 — 3.6/3.7 서술이 엇갈리는 미결 항목</li>
            <li>Multus 면 <b>3.7 + VPC 모드 Calico</b> 인가</li>
            <li>IPAM 이 <b>Whereabouts</b> 인가</li>
            <li>SR-IOV 면 노드 VM 에 <b>vIOMMU</b> 가 켜져 있는가</li>
          </ul>
        </div>
      </div>""",
)

# 27 · Thanks ---------------------------------------------------------------
slide(
    "27 Thanks",
    "l-thanks",
    swoosh_left("gThanksLeaf")
    + """
      <h2>감사합니다</h2>
      <div class="contact" style="left:560px;width:620px">
        <b>텍스트 companion 문서</b><br>
        VKS_Cilium_CNI_KR.md — 설치 4단계 · 애드온 라이프사이클<br>
        VKS_Cilium_Hubble_KR.md — Relay/UI · 메트릭 · 검증<br>
        VKS_Multus_MultiNIC_KR.md — 노드 NIC · NAD · SR-IOV<br><br>
        <b>라이브</b> · <a href="https://kjin17.github.io/vks-study/">kjin17.github.io/vks-study</a><br><br>
        <b>출처</b> · Broadcom TechDocs (Cilium CNI Add-On Package, Managing Add-ons in VKS Clusters,
        ClusterClass Variable Reference, Configure Multiple Networks for VKS Clusters),
        VKS 3.6 / 3.7 Release Notes, VKS Standard Packages Release Notes<br><br>
        공개 문서 기반 학습용 정리입니다. 실제 배포 전에는 해당 릴리스의 공식 문서를 다시 확인하세요.
      </div>""",
)


def render() -> str:
    if not SRC.exists():
        sys.exit(f"원본 덱을 찾을 수 없습니다: {SRC}")
    src = SRC.read_text(encoding="utf-8")
    m = re.search(r"<style>.*?</style>", src, re.S)
    if not m:
        sys.exit("원본 덱에서 <style> 블록을 찾지 못했습니다.")
    style = m.group(0)

    parts = [
        "<!doctype html>",
        '<html lang="ko">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{TITLE}</title>",
        style,
        STYLE_OVERRIDE,
        "</head>",
        "<body>",
        '<div class="stage">',
        '  <div class="deck" id="deck">',
    ]

    total = len(SLIDES)
    for i, (label, cls, body) in enumerate(SLIDES, start=1):
        active = " active" if i == 1 else ""
        parts.append(f"\n    <!-- {i} · {label} -->")
        parts.append(
            f'    <section class="slide {cls}{active}" data-screen-label="{label}">'
        )
        parts.append(body)
        if cls == "l-title":
            parts.append(
                f'      <div class="footer">\n'
                f"        <div>{COPY}</div>\n"
                f"        {BRAND}\n"
                f"      </div>"
            )
        else:
            parts.append(
                f'      <div class="footer">{BRAND}<div class="page-no">{i}</div></div>'
            )
        parts.append("    </section>")

    parts += [
        "",
        "  </div>",
        "</div>",
        "",
        '<nav class="nav">',
        '  <button id="prev" aria-label="Previous">‹</button>',
        '  <div class="dots" id="dots"></div>',
        '  <button id="next" aria-label="Next">›</button>',
        "</nav>",
        "",
        "<script>",
        "(function () {",
        "  var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));",
        "  var dotsBox = document.getElementById('dots');",
        f"  var KEY = '{STORAGE_KEY}';",
        "  var idx = 0;",
        "  var saved = parseInt(localStorage.getItem(KEY), 10);",
        "  if (!isNaN(saved) && saved >= 0 && saved < slides.length) idx = saved;",
        "",
        "  slides.forEach(function (_, i) {",
        "    var d = document.createElement('div');",
        "    d.className = 'dot' + (i === idx ? ' on' : '');",
        "    d.addEventListener('click', function () { go(i); });",
        "    dotsBox.appendChild(d);",
        "  });",
        "  var dots = Array.prototype.slice.call(dotsBox.children);",
        "",
        "  function go(i) {",
        "    idx = (i + slides.length) % slides.length;",
        "    slides.forEach(function (s, k) { s.classList.toggle('active', k === idx); });",
        "    dots.forEach(function (d, k) { d.classList.toggle('on', k === idx); });",
        "    try { localStorage.setItem(KEY, idx); } catch (e) {}",
        "  }",
        "  go(idx);",
        "  document.getElementById('prev').addEventListener('click', function () { go(idx - 1); });",
        "  document.getElementById('next').addEventListener('click', function () { go(idx + 1); });",
        "  document.addEventListener('keydown', function (e) {",
        "    if (e.key === 'ArrowLeft') go(idx - 1);",
        "    if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); go(idx + 1); }",
        "  });",
        "",
        "  function fit() {",
        "    var deck = document.getElementById('deck');",
        "    var de = document.documentElement;",
        "    var w = de.clientWidth || window.innerWidth;",
        "    var h = de.clientHeight || window.innerHeight;",
        "    var s = Math.min(w / 1280, h / 720) * 0.96;",
        "    deck.style.transform = 'scale(' + s + ')';",
        "  }",
        "  window.addEventListener('resize', fit);",
        "  fit();",
        "})();",
        "</script>",
        "</body>",
        "</html>",
        "",
    ]
    print(f"슬라이드 {total}장 생성", file=sys.stderr)
    return "\n".join(parts)


if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8")
    print(f"→ {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")
