#!/usr/bin/env python3
"""덱 슬라이드의 내용이 1280x720 프레임을 넘치는지 실제 브라우저로 잰다.

`.slide` 는 overflow:hidden 이라 넘친 내용이 **조용히 잘립니다.** 육안으로는
멀쩡해 보이므로 자를 따로 대야 합니다. 각 슬라이드를 차례로 active 로 만든 뒤
모든 자손 요소의 bounding rect 를 슬라이드 기준으로 재서 최대값을 보고합니다.

    python3 exports/check_deck_overflow.py docs/VKS_Advanced_Networking_KR.html

넘친 슬라이드가 하나라도 있으면 exit 1.
"""
from __future__ import annotations

import html
import pathlib
import re
import subprocess
import sys
import tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1280, 720

PROBE = """
<script>
(function(){
  document.getElementById('deck').style.transform='none';
  var out=[];
  document.querySelectorAll('.slide').forEach(function(s,i){
    var was=s.classList.contains('active');
    s.classList.add('active');
    var sr=s.getBoundingClientRect();
    var mb=0,mr=0,wb='',wr='';
    s.querySelectorAll('*').forEach(function(el){
      if(el.tagName==='SVG'||el.closest('svg'))return;
      if(el.closest('.footer'))return;
      var r=el.getBoundingClientRect();
      if(r.width===0&&r.height===0)return;
      var b=r.bottom-sr.top,x=r.right-sr.left;
      var tag=el.tagName+'.'+(typeof el.className==='string'?el.className:'');
      if(b>mb){mb=b;wb=tag;}
      if(x>mr){mr=x;wr=tag;}
    });
    out.push([i+1,s.getAttribute('data-screen-label'),Math.round(mb),wb,Math.round(mr),wr].join('\\t'));
    if(!was)s.classList.remove('active');
  });
  var pre=document.createElement('pre');
  pre.id='__overflow_report__';
  pre.textContent=out.join('\\n');
  document.body.appendChild(pre);
})();
</script>
</body>"""


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(f"사용법: {sys.argv[0]} <deck.html>")
    deck = pathlib.Path(sys.argv[1]).resolve()
    if not deck.exists():
        sys.exit(f"파일 없음: {deck}")
    if not pathlib.Path(CHROME).exists():
        sys.exit(f"Chrome 을 찾을 수 없습니다: {CHROME}")

    src = deck.read_text(encoding="utf-8")
    if "</body>" not in src:
        sys.exit("</body> 가 없습니다 — 덱 파일이 맞습니까?")

    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(src.replace("</body>", PROBE, 1))
        probe_path = fh.name

    dom = subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            f"--window-size={W},{H}",
            "--virtual-time-budget=5000",
            "--dump-dom",
            f"file://{probe_path}",
        ],
        capture_output=True,
        text=True,
    ).stdout

    m = re.search(r'<pre id="__overflow_report__">(.*?)</pre>', dom, re.S)
    if not m:
        sys.exit("측정 결과를 못 읽었습니다. 자가 안 닿았습니다 — 0 으로 읽지 마세요.")

    # 두 단계로 판정한다.
    #   ❌ CLIP  — 720px 를 넘어 overflow:hidden 에 실제로 잘림
    #   ⚠️ FOOTER— 잘리진 않지만 푸터 띠(하단 76px)를 덮어 글자가 겹쳐 보임
    # 720 하나만 보면 겹침을 통과시킨다. 실제로 그렇게 한 번 놓쳤다.
    CLIP, SAFE = H, H - 76
    clipped = warned = 0
    print(f"{'#':>3}  {'슬라이드':<34} {'하단':>6} {'우측':>6}  판정")
    print("-" * 100)
    for line in html.unescape(m.group(1)).strip().split("\n"):
        idx, label, mb, wb, mr, wr = line.split("\t")
        mb, mr = int(mb), int(mr)
        note = ""
        if mb > CLIP or mr > W:
            clipped += 1
            if mb > CLIP:
                note += f"❌ 잘림 하단 +{mb - CLIP}px ({wb}) "
            if mr > W:
                note += f"❌ 잘림 우측 +{mr - W}px ({wr}) "
        elif mb > SAFE:
            warned += 1
            note = f"⚠️  푸터 침범 +{mb - SAFE}px ({wb})"
        else:
            note = "✅"
        print(f"{idx:>3}  {label:<34} {mb:>6} {mr:>6}  {note}")

    pathlib.Path(probe_path).unlink(missing_ok=True)
    total = len(html.unescape(m.group(1)).strip().splitlines())
    print("-" * 100)
    if clipped or warned:
        print(f"잘림 {clipped}장 · 푸터 침범 {warned}장 — 내용을 줄이거나 배치를 조정하세요.")
        return 1
    print(f"전체 {total}장 통과 (내용이 {W}x{SAFE} 안전 영역 안).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
