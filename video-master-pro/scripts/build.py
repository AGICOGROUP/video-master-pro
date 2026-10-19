"""Cut, grade and lay out the two GEMCO product films.

Shot preparation keeps the source aspect ratio at all times
(force_original_aspect_ratio=increase + centre crop), matches exposure between
shots, and applies one of two house grades. Typography lives in HyperFrames
sub-compositions, one per shot, assembled into index.html.
"""
import html
import json
import os
import subprocess
import sys
from pathlib import Path

from paths import SRC, WORK, project_assets, require_src  # noqa: E402
from spec import SPECS  # noqa: E402

SRC = require_src(SRC)
SRSRC = Path(SRC)
W, H, FPS = 1920, 1080, 30

GRADE_A = ("curves=all='0/0 0.20/0.155 0.50/0.505 0.80/0.855 1/1',"
           "eq=contrast=1.105:saturation=0.84:gamma=0.98,"
           "colorbalance=rs=-0.030:bs=0.055:rm=0.004:bm=0.010:rh=0.040:gh=0.006:bh=-0.028,"
           "vignette=PI/4.6,unsharp=5:5:0.55:5:5:0.0,noise=alls=3:allf=t")

GRADE_B = ("curves=all='0/0 0.20/0.17 0.50/0.53 0.82/0.865 1/1',"
           "eq=contrast=1.065:saturation=1.02:gamma=1.01,"
           "colorbalance=rs=0.020:gs=0.008:bs=-0.026:rm=0.010:bm=-0.004:rh=0.018:gh=0.010:bh=-0.006,"
           "vignette=PI/5.2,unsharp=5:5:0.45:5:5:0.0,noise=alls=3:allf=t")

GRADES = {"A": GRADE_A, "B": GRADE_B}


def canvas(spec):
    global W, H, FPS
    W, H = spec.get('w', 1920), spec.get('h', 1080)
    FPS = spec.get('fps', 30)
    return W, H


def run(args, quiet=True):
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(str(a) for a in args[:9])} ... rc={r.returncode}\n{r.stderr[-2000:]}")
    return r.stdout


def measure_yavg(src, ss, dur):
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", ss, "-t", dur, "-i", src,
               "-vf", "scale=320:-2,signalstats,metadata=print:file=-", "-f", "null", "-"])
    vals = [float(l.split("=")[-1]) for l in out.splitlines() if "signalstats.YAVG" in l]
    return sum(vals) / len(vals) if vals else 105.0


def cut_shots(spec, assets):
    assets.mkdir(parents=True, exist_ok=True)
    grade = GRADES.get(spec["key"], list(GRADES.values())[0])
    info = []
    for i, s in enumerate(spec["shots"]):
        src = SRSRC / s["src"]
        if not src.exists():
            raise FileNotFoundError(src)
        dst = assets / f"shot{i}.mp4"
        yavg = measure_yavg(src, s["start"], s["dur"])
        corr = max(-0.07, min(0.07, (112.0 - yavg) / 255.0 * 0.62))
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={W}:{H},setsar=1,fps={FPS},"
              f"eq=brightness={corr:+.3f},{grade},format=yuv420p")
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-ss", s["start"], "-i", src, "-t", s["dur"], "-an", "-vf", vf,
             "-c:v", "libx264", "-preset", "medium", "-crf", "16",
             "-r", FPS, "-g", FPS, "-keyint_min", FPS, "-pix_fmt", "yuv420p",
             "-movflags", "+faststart", dst])
        p = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height,r_frame_rate",
                            "-show_entries", "format=duration", "-of", "json", dst]))
        st = p["streams"][0]
        info.append(dict(i=i, w=st["width"], h=st["height"], fps=st["r_frame_rate"],
                         dur=round(float(p["format"]["duration"]), 2)))
        print(f"  shot{i} {st['width']}x{st['height']} {float(p['format']['duration']):.2f}s"
              f"  yavg={yavg:5.1f} b={corr:+.3f}  <- {Path(s['src']).name} @{s['start']}")
    return info


# ------------------------------------------------------------------ styling
STYLE = """<style>
@font-face{font-family:'CN';src:url('assets/msyh.ttc')}
@font-face{font-family:'CNB';src:url('assets/msyhbd.ttc')}
@font-face{font-family:'DIN';src:url('assets/bahnschrift.ttf')}
@font-face{font-family:'EN';src:url('assets/segoeui.ttf')}
@font-face{font-family:'ENB';src:url('assets/segoeuib.ttf')}
#root{position:absolute;inset:0;overflow:hidden;background:__BASE__;color:#fff;
  font-family:'EN','CN',sans-serif;-webkit-font-smoothing:antialiased}
#vwrap{position:absolute;inset:0;overflow:hidden}
#vwrap video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
#shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(4,6,7,.55) 0%,rgba(4,6,7,.06) 30%,rgba(4,6,7,.02) 55%,rgba(4,6,7,.30) 78%,rgba(4,6,7,.80) 100%)}
#edge{position:absolute;inset:0;box-shadow:inset 0 0 220px rgba(0,0,0,.55)}
#topbar{position:absolute;left:96px;top:64px;display:flex;align-items:center;gap:22px}
#chap{font-family:'DIN';font-size:30px;font-weight:600;letter-spacing:.10em;color:__ACCENT__;line-height:1}
#chapsep{width:34px;height:1px;background:rgba(255,255,255,.42)}
#eyebrow{font-family:'DIN';font-size:21px;letter-spacing:.34em;color:#EDF1F2;text-transform:uppercase;line-height:1}
#brand{position:absolute;right:96px;top:56px;width:292px;height:94px;
  filter:drop-shadow(0 2px 10px rgba(0,0,0,.55))}
#block{position:absolute;left:96px;bottom:98px;max-width:1240px}
#block.rt{left:auto;right:96px;text-align:right;max-width:1120px}
#block.rt #rule{margin-left:auto}
#shade.rt{background:linear-gradient(270deg,rgba(4,6,7,.76) 0%,rgba(4,6,7,.32) 42%,rgba(4,6,7,.04) 72%,rgba(4,6,7,.20) 100%)}
#dim{position:absolute;inset:0;background:#04070a;pointer-events:none}
#rule{width:92px;height:2px;background:__ACCENT__;margin-bottom:26px}
#cn{font-family:'CNB';font-size:42px;font-weight:700;line-height:1.28;color:#fff;letter-spacing:.012em}
#en{font-family:'EN';font-size:42px;line-height:1.28;color:__INK__;margin-top:12px;letter-spacing:.006em}
#rail{position:absolute;left:0;right:0;bottom:0;height:2px;background:rgba(255,255,255,.14)}
#railfill{width:100%;height:100%;background:__ACCENT__}
#meta{position:absolute;left:96px;bottom:40px;font-family:'DIN';font-size:15px;letter-spacing:.32em;color:rgba(255,255,255,.52);text-transform:uppercase}

/* hero */
#hero{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
  background:radial-gradient(ellipse at 50% 46%,rgba(3,5,6,.55) 0%,rgba(3,5,6,.78) 62%,rgba(3,5,6,.9) 100%)}
#h-eyebrow{font-family:'DIN';font-size:23px;letter-spacing:.40em;color:__ACCENT__;text-transform:uppercase}
#h-line{width:250px;height:1px;background:rgba(255,255,255,.34);margin:34px 0}
#h-cn{font-family:'CNB';font-size:112px;font-weight:700;line-height:1.06;letter-spacing:.06em;color:#fff}
#h-en{font-family:'EN';font-size:42px;letter-spacing:.14em;color:__INK__;margin-top:26px;text-transform:uppercase}
#h-rule{width:64px;height:2px;background:__ACCENT__;margin-top:40px}

/* side panel */
#panel{position:absolute;left:0;top:0;bottom:0;width:820px;
  background:linear-gradient(90deg,rgba(4,7,8,.96) 0%,rgba(4,7,8,.94) 62%,rgba(4,7,8,.55) 86%,rgba(4,7,8,0) 100%)}
#sblock{position:absolute;left:96px;top:50%;transform:translateY(-42%);max-width:610px}
#sblock #rule{margin-bottom:24px}
#sblock #en{margin-top:14px}

/* endcard */
#card{position:absolute;inset:0;background:linear-gradient(180deg,rgba(3,5,6,.80) 0%,rgba(3,5,6,.90) 46%,rgba(3,5,6,.96) 100%)}
#ec-logo{position:absolute;left:96px;top:88px;width:352px;height:113px;
  filter:drop-shadow(0 3px 14px rgba(0,0,0,.6))}
#ec-wrap{position:absolute;left:96px;bottom:104px;right:96px;max-width:1460px}
#ec-eyebrow{font-family:'DIN';font-size:22px;letter-spacing:.36em;color:__ACCENT__;text-transform:uppercase}
#ec-cn{font-family:'CNB';font-size:76px;font-weight:700;line-height:1.14;color:#fff;margin-top:34px;letter-spacing:.03em}
#ec-en{font-family:'EN';font-size:40px;line-height:1.24;color:__INK__;margin-top:16px;letter-spacing:.10em;text-transform:uppercase}
#ec-rows{margin-top:40px;max-width:1120px}
.row{display:flex;align-items:baseline;gap:20px;padding:12px 0;border-top:1px solid rgba(255,255,255,.14)}
.rk{font-family:'CN';font-size:27px;color:#fff;width:214px;flex:none;letter-spacing:.02em}
.ls{flex:1;border-bottom:1px dotted rgba(255,255,255,.16);transform:translateY(-6px)}
.rv{font-family:'EN';font-size:27px;color:__INK__;letter-spacing:.02em}
#ec-cta{margin-top:38px;font-family:'CNB';font-size:28px;font-weight:700;color:#fff}
#ec-cta span{font-family:'EN';font-weight:400;font-size:28px;color:__ACCENT__;margin-left:20px;letter-spacing:.02em}
</style>"""

BODY_HERO = """
<div id="vwrap" data-layout-allow-overflow><video id="v1" class="clip" src="assets/shot__IDX__.mp4"
  data-start="0" data-duration="__DUR__" data-track-index="0" muted playsinline
  style="object-position:__ALIGN__"></video></div>
<div id="hero">
  <div id="h-eyebrow">__EYEBROW__</div>
  <div id="h-line"></div>
  <div id="h-cn">__CN__</div>
  <div id="h-en">__EN__</div>
  <div id="h-rule"></div>
</div>
<div id="meta">__CH__ / 09 &nbsp;&nbsp; 60 SEC</div>
<div id="rail"><div id="railfill"></div></div>"""

BODY_LEFT = """
<div id="vwrap" data-layout-allow-overflow><video id="v1" class="clip" src="assets/shot__IDX__.mp4"
  data-start="0" data-duration="__DUR__" data-track-index="0" muted playsinline
  style="object-position:__ALIGN__"></video></div>
<div id="shade"></div><div id="dim" style="opacity:__DIM__"></div><div id="edge"></div>
<div id="topbar"><div id="chap">__CH__</div><div id="chapsep"></div><div id="eyebrow">__EYEBROW__</div></div>
<img id="brand" src="assets/logo_white.png" alt="GEMCO" />
<div id="block">
  <div id="rule"></div>
  <div id="cn">__CN__</div>
  <div id="en">__EN__</div>
</div>
<div id="rail"><div id="railfill"></div></div>"""

BODY_RIGHT = """
<div id="vwrap" data-layout-allow-overflow><video id="v1" class="clip" src="assets/shot__IDX__.mp4"
  data-start="0" data-duration="__DUR__" data-track-index="0" muted playsinline
  style="object-position:__ALIGN__"></video></div>
<div id="shade" class="rt"></div><div id="dim" style="opacity:__DIM__"></div><div id="edge"></div>
<div id="topbar"><div id="chap">__CH__</div><div id="chapsep"></div><div id="eyebrow">__EYEBROW__</div></div>
<img id="brand" src="assets/logo_white.png" alt="GEMCO" />
<div id="block" class="rt">
  <div id="rule"></div>
  <div id="cn">__CN__</div>
  <div id="en">__EN__</div>
</div>
<div id="rail"><div id="railfill"></div></div>"""

BODY_SIDE = """
<div id="vwrap" data-layout-allow-overflow><video id="v1" class="clip" src="assets/shot__IDX__.mp4"
  data-start="0" data-duration="__DUR__" data-track-index="0" muted playsinline
  style="object-position:__ALIGN__"></video></div>
<div id="panel"></div><div id="dim" style="opacity:__DIM__"></div><div id="edge"></div>
<div id="topbar"><div id="chap">__CH__</div><div id="chapsep"></div><div id="eyebrow">__EYEBROW__</div></div>
<div id="sblock">
  <div id="rule"></div>
  <div id="cn">__CN__</div>
  <div id="en">__EN__</div>
</div>
<div id="rail"><div id="railfill"></div></div>"""

BODY_END = """
<div id="vwrap" data-layout-allow-overflow><video id="v1" class="clip" src="assets/shot__IDX__.mp4"
  data-start="0" data-duration="__DUR__" data-track-index="0" muted playsinline
  style="object-position:__ALIGN__;opacity:.34"></video></div>
<div id="card"></div>
<img id="ec-logo" src="assets/logo_white.png" alt="GEMCO" />
<div id="ec-wrap">
  <div id="ec-eyebrow">__EYEBROW__</div>
  <div id="ec-cn">__CN__</div>
  <div id="ec-en">__EN__</div>
  <div id="ec-rows">__ROWS__</div>
  <div id="ec-cta">__CTA_CN__<span>__CTA_EN__</span></div>
</div>
<div id="rail"><div id="railfill"></div></div>"""

BODIES = dict(hero=BODY_HERO, left=BODY_LEFT, right=BODY_RIGHT, side=BODY_SIDE, endcard=BODY_END)

MOTION = """
const tl = gsap.timeline({paused:true});
const DUR = __DUR__;
const ease = 'power3.out';
tl.fromTo('#vwrap', {scale: __S0__, transformOrigin:'__ORIGIN__'},
                   {scale: __S1__, duration:DUR, ease:'none'}, 0);
tl.fromTo('#railfill', {scaleX:0, transformOrigin:'left center'},
                        {scaleX:1, duration:DUR, ease:'none'}, 0);
tl.fromTo('#topbar', {opacity:0, y:-10}, {opacity:1, y:0, duration:.7, ease:ease}, .10);
tl.fromTo('#brand', {opacity:0}, {opacity:1, duration:.9, ease:'power2.out'}, .22);
tl.fromTo('#chap', {opacity:0, x:-14}, {opacity:1, x:0, duration:.7, ease:ease}, .12);
tl.fromTo('#eyebrow', {opacity:0, x:-10}, {opacity:1, x:0, duration:1.0, ease:'power2.out'}, .16);
tl.fromTo('#rule', {scaleX:0, transformOrigin:'left center'},
                   {scaleX:1, duration:.6, ease:'power3.out'}, .10);
tl.fromTo('#cn', {y:34, opacity:0}, {y:0, opacity:1, duration:.8, ease:ease}, .18);
tl.fromTo('#en', {y:24, opacity:0}, {y:0, opacity:1, duration:.75, ease:ease}, .34);
tl.fromTo('#hero', {opacity:0}, {opacity:1, duration:.9, ease:'power2.out'}, 0);
tl.fromTo('#h-eyebrow', {opacity:0, y:-8}, {opacity:1, y:0, duration:1.0, ease:'power2.out'}, .15);
tl.fromTo('#h-line', {scaleX:0, opacity:0}, {scaleX:1, opacity:1, duration:.8, ease:'power3.out'}, .30);
tl.fromTo('#h-cn', {y:44, opacity:0, filter:'blur(10px)'},
                   {y:0, opacity:1, filter:'blur(0px)', duration:1.0, ease:ease}, .34);
tl.fromTo('#h-en', {y:26, opacity:0}, {y:0, opacity:1, duration:.85, ease:ease}, .58);
tl.fromTo('#h-rule', {scaleX:0}, {scaleX:1, duration:.7, ease:'power3.out'}, .80);
tl.fromTo('#meta', {opacity:0}, {opacity:1, duration:.8, ease:ease}, .9);
tl.fromTo('#panel', {opacity:0}, {opacity:1, duration:.8, ease:'power2.out'}, .05);
tl.fromTo('#sblock', {opacity:0, x:-26}, {opacity:1, x:0, duration:.85, ease:ease}, .12);
tl.fromTo('#card', {opacity:0}, {opacity:1, duration:.9, ease:'power2.out'}, 0);
tl.fromTo('#ec-logo', {opacity:0, y:-12}, {opacity:1, y:0, duration:.9, ease:ease}, .12);
tl.fromTo('#ec-eyebrow', {opacity:0, x:-10}, {opacity:1, x:0, duration:1.0, ease:'power2.out'}, .30);
tl.fromTo('#ec-cn', {y:30, opacity:0}, {y:0, opacity:1, duration:.8, ease:ease}, .42);
tl.fromTo('#ec-en', {y:22, opacity:0}, {y:0, opacity:1, duration:.75, ease:ease}, .60);
tl.fromTo('#ec-rows .row', {y:16, opacity:0}, {y:0, opacity:1, duration:.55, ease:ease, stagger:.13}, .86);
tl.fromTo('#ec-cta', {y:12, opacity:0}, {y:0, opacity:1, duration:.6, ease:ease}, 1.62);
window.__timelines["__CID__"] = tl;
"""


def fill(template, spec, sh, idx):
    rows = ""
    if sh.get("rows"):
        rows = "".join(
            f'<div class="row"><span class="rk">{html.escape(c)}</span>'
            f'<span class="ls"></span><span class="rv">{html.escape(e)}</span></div>'
            for c, e in sh["rows"])
    out = template
    repl = {
        "__IDX__": f"{idx}", "__DUR__": f"{sh['dur']:.2f}", "__ALIGN__": sh.get("align", "50% 50%"),
        "__CH__": sh.get("ch", ""), "__EYEBROW__": html.escape(sh.get("eyebrow", "")),
        "__CN__": html.escape(sh.get("cn", "")), "__EN__": html.escape(sh.get("en", "")),
        "__ROWS__": rows, "__CTA_CN__": html.escape(sh.get("cta_cn", "")),
        "__CTA_EN__": html.escape(sh.get("cta_en", "")),
        "__DIM__": f'{sh.get("dim", 0.0):.2f}',
    }
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def scene_html(spec, sh, idx):
    style = (STYLE.replace("__BASE__", spec["base"])
                  .replace("__ACCENT__", spec["accent"])
                  .replace("__INK__", spec["ink"]))
    body = fill(BODIES[sh["layout"]], spec, sh, idx)
    # scale drift: "in" pushes slowly toward the frame, "out" settles back
    s0, s1 = ("1.005", "1.052") if sh.get("drift", "in") == "in" else ("1.058", "1.004")
    origin = " ".join(x.replace("%", "%") for x in sh.get("align", "50% 50%").split())
    motion = (MOTION.replace("__DUR__", f"{sh['dur']:.2f}")
                    .replace("__S0__", s0).replace("__S1__", s1)
                    .replace("__ORIGIN__", origin)
                    .replace("__CID__", f"shot{idx}"))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8" /></head>
<body><template>
{style}
<div id="root" data-composition-id="shot{idx}" data-width="1920" data-height="1080">
{body}
</div>
<script>
{motion}
</script>
</template></body></html>
"""


def write_index(spec, proj):
    shots = spec["shots"]
    total = sum(s["dur"] for s in shots)
    assert abs(total - spec["duration"]) < 1e-6, f"{spec['key']} total {total}"
    hosts, cursor = [], 0.0
    for i, s in enumerate(shots):
        hosts.append(f'    <div id="host{i}" data-composition-id="shot{i}" '
                     f'data-composition-src="compositions/shot{i}.html" data-start="{cursor:.2f}" '
                     f'data-duration="{s["dur"]:.2f}" data-track-index="1" '
                     f'data-width="1920" data-height="1080"></div>')
        cursor += s["dur"]
    html_out = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1920, height=1080" />
  <title>{spec['title']}</title>
  <script src="assets/gsap.min.js"></script>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    html,body{{width:1920px;height:1080px;overflow:hidden;background:{spec['base']}}}
    #root{{position:relative;width:100%;height:100%;overflow:hidden}}
    #root>div{{position:absolute;inset:0}}
    #open,#close{{position:absolute;inset:0;background:#000;pointer-events:none}}
    #open{{opacity:1}}
    #close{{opacity:0}}
  </style>
</head>
<body>
  <div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="{total:.2f}">
{chr(10).join(hosts)}
    <audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{total:.2f}" data-track-index="9" data-volume="1"></audio>
    <div id="open"></div>
    <div id="close"></div>
  </div>
  <script>
    const tl = gsap.timeline({{paused:true}});
    tl.fromTo('#open',{{opacity:1}},{{opacity:0,duration:0.85,ease:'power2.inOut'}},0);
    tl.fromTo('#close',{{opacity:0}},{{opacity:1,duration:1.0,ease:'power2.inOut'}},{total - 1.05:.2f});
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""
    (proj / "index.html").write_text(html_out, encoding="utf-8")
    return total


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "AB"
    for key in which:
        spec = SPECS[key]
        canvas(spec)
        proj = WORK / spec["proj"]
        assets = proj / "assets"
        print(f"=== {key}: {spec['proj']} ===")
        cut_shots(spec, assets)
        (proj / 'compositions').mkdir(parents=True, exist_ok=True)
        for i, s in enumerate(spec["shots"]):
            (proj / "compositions" / f"shot{i}.html").write_text(scene_html(spec, s, i), encoding="utf-8")
        total = write_index(spec, proj)
        print(f"  total={total:.2f}s -> {proj}")


if __name__ == "__main__":
    main()
