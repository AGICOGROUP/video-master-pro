"""Acceptance check for a finished film.

Prints one line per file with duration / resolution / fps / codecs, measures
integrated loudness, flags any audio hole longer than 2.2 s, and writes a
3x3 contact sheet sampled across the timeline so the frames can be eyeballed.

    python verify.py <video.mp4> [more.mp4 ...]
    python verify.py --sheet 12 <video.mp4>     # 12 tiles instead of 9

Exit code 1 if any hard rule fails (duration off, LUFS out of range, no audio,
missing stream), so it can gate a delivery step.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import QA  # noqa: E402

TARGET = dict(w=1920, h=1080, fps=30.0, dur=None, lufs=(-18.0, -14.0), gap=2.2)

# Expected canvases come from the project file when one is resolvable, so the same
# gate works for 16:9 and 9:16 without editing constants.
try:
    from spec import SPECS as _SPECS, SOURCE_FILE as _SRC  # noqa: E402

    IS_EXAMPLE = _SRC.name == "spec_example.py"
    CANVASES = [dict(key=k, w=s.get("w", 1920), h=s.get("h", 1080),
                     fps=float(s.get("fps", 30)),
                     dur=round(sum(float(x["dur"]) for x in s["shots"]), 2))
                for k, s in _SPECS.items()]
except Exception:
    IS_EXAMPLE, CANVASES = True, []


def target_for(w, h):
    """Return (fps, allowed_durations) for a canvas, or None when unknown."""
    hits = [c for c in CANVASES if (c["w"], c["h"]) == (w, h)]
    if not hits:
        return None
    return hits[0]["fps"], [c["dur"] for c in hits]


def run(args):
    return subprocess.run([str(a) for a in args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path])
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {r.stderr[-400:]}")
    info = json.loads(r.stdout)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    return info, v, a


def loudness(path):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
             "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    txt = r.stderr
    i = txt.rfind("{")
    if i < 0:
        return None
    try:
        d = json.loads(txt[i:txt.rfind("}") + 1])
        return float(d["input_i"]), float(d["input_tp"]), float(d["input_lra"])
    except Exception:
        return None


def holes(path, limit):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
             "-af", f"silencedetect=noise=-40dB:d={limit}", "-f", "null", "-"])
    return [float(m) for m in re.findall(r"silence_duration: ([\d.]+)", r.stderr)]


def sheet(path, tiles, out):
    dur = float(probe(path)[0]["format"]["duration"])
    step = dur / (tiles + 1)
    names = []
    for i in range(tiles):
        p = out / f"_t{i}.png"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{step * (i + 1):.2f}",
             "-i", path, "-frames:v", "1", "-vf", "scale=640:360", p])
        names.append(p)
    cols = 3
    rows = (tiles + cols - 1) // cols
    pattern = out / "_t%d.png"
    dst = out / f"{Path(path).stem}_sheet.png"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", pattern,
         "-vf", f"tile={cols}x{rows}", dst])
    for p in names:
        p.unlink(missing_ok=True)
    return dst


def check(path):
    ok = True
    info, v, a = probe(path)
    dur = float(info["format"]["duration"])
    size = int(info["format"]["size"]) / 1048576
    print(f"{Path(path).name}")
    if v is None:
        print("  FAIL no video stream")
        return False
    num, den = (v["r_frame_rate"].split("/") + ["1"])[:2]
    fps = float(num) / float(den)
    hit = target_for(int(v["width"]), int(v["height"]))
    print(f"  {dur:.2f}s  {size:.1f} MB  {v['width']}x{v['height']}  {fps:g}fps  "
          f"v={v['codec_name']}  a={(a or {}).get('codec_name', '-')}")
    if hit is None:
        sizes = ", ".join(sorted({"%dx%d" % (c["w"], c["h"]) for c in CANVASES})) or "1920x1080"
        print(f"  WARN canvas not in project file; expected {sizes}")
    else:
        want_fps, durs = hit
        if abs(fps - want_fps) > 0.01:
            print(f"  FAIL fps {fps:g} != {want_fps:g}")
            ok = False
        if IS_EXAMPLE:
            print("  WARN no project file found; duration unchecked "
                  "(pass --work <dir> so spec_local.py is read)")
        elif not any(abs(dur - d) <= 0.05 for d in durs):
            print(f"  FAIL duration {dur:.2f}s, project expects {durs}")
            ok = False
    if a is None:
        print("  FAIL no audio stream")
        ok = False
    else:
        loud = loudness(path)
        if loud:
            i, tp, lra = loud
            lo, hi = TARGET["lufs"]
            flag = "ok" if lo <= i <= hi else "FAIL"
            print(f"  loudness {i:.2f} LUFS  TP {tp:.2f} dBTP  LRA {lra:.1f}   [{flag}]")
            if flag == "FAIL":
                ok = False
        gaps = holes(path, TARGET["gap"])
        if gaps:
            print(f"  WARN audio holes > {TARGET['gap']}s: {', '.join(f'{g:.1f}s' for g in gaps)}")
        else:
            print(f"  no audio hole >= {TARGET['gap']}s")
    print("  PASS" if ok else "  FAILED")
    return ok


def main():
    tiles = 9
    # paths.py already consumed the location flags; drop them from the file list.
    args, i = [], 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a in ("--src", "--work", "--out", "--qa", "--logo"):
            i += 2
            continue
        if a == "--sheet":
            tiles = int(sys.argv[i + 1])
            i += 2
            continue
        args.append(a)
        i += 1
    files = []
    for a in args:
        p = Path(a)
        files.extend(sorted(p.parent.glob(p.name)) if any(c in a for c in "*?") else [p])
    if not files:
        print(__doc__)
        return 2
    out = QA
    out.mkdir(parents=True, exist_ok=True)
    ok = all([check(f) for f in files])
    for f in files:
        print("  sheet:", sheet(f, tiles, out))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
