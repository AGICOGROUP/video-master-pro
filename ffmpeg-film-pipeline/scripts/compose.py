"""Compose the films with FFmpeg: camera drift, type overlay, progress rail, audio.

Each shot becomes one segment (punch-in drift + overlay fade + rail fill + x264),
then the segments are concatenated and muxed with the mixed voice/music bed.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from paths import OUT, WORK, project_assets  # noqa: E402
sys.path.insert(0, str(WORK))
from spec import SPECS  # noqa: E402

W, H, FPS = 1920, 1080, 30


def run(args):
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"rc={r.returncode}\n{r.stderr[-1800:]}")
    return r.stdout


def seg(spec, i, sh, proj):
    dur = sh["dur"]
    src = proj / "assets" / f"shot{i}.mp4"
    ov = proj / "assets" / "overlay" / f"ov{i}.png"
    out = proj / "assets" / f"seg{i}.mp4"
    frames = max(2, round(dur * FPS))

    if sh.get("drift", "in") == "in":
        zexpr = f"1+0.045*on/{frames - 1}"
    else:
        zexpr = f"1.050-0.046*on/{frames - 1}"

    fade_out = ""
    if i == 0:
        fade_out = ",fade=t=in:st=0:d=0.85"
    if i == len(spec["shots"]) - 1:
        fade_out += f",fade=t=out:st={dur - 1.0:.3f}:d=1.0"

    accent = spec["accent"].replace("#", "0x")
    fc = (
        f"[0:v]zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d=1:s={W}x{H}:fps={FPS},setsar=1[bg];"
        f"[1:v]format=rgba,fade=t=in:st=0.12:d=0.60:alpha=1[ov];"
        f"[bg][ov]overlay=0:0:format=auto[g];"
        f"[g]drawbox=x=0:y=ih-2:w='iw*t/{dur:.3f}':h=2:color={accent}@0.95:t=fill,"
        f"format=yuv420p{fade_out}[v]"
    )
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", src, "-loop", "1", "-i", ov,
         "-filter_complex", fc, "-map", "[v]", "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-r", FPS, "-g", FPS, "-pix_fmt", "yuv420p", "-t", f"{dur:.3f}", out])
    return out


def canvas(spec):
    global W, H, FPS
    W, H = spec.get('w', 1920), spec.get('h', 1080)
    FPS = spec.get('fps', 30)


def build(key):
    spec = SPECS[key]
    canvas(spec)
    OUT.mkdir(parents=True, exist_ok=True)
    proj = WORK / spec["proj"]
    print(f"=== {key}: {spec['proj']} ===")
    segs = []
    for i, sh in enumerate(spec["shots"]):
        p = seg(spec, i, sh, proj)
        segs.append(p)
        print(f"  seg{i} ok  {p.stat().st_size / 1048576:.1f} MB")

    lst = proj / "assets" / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in segs), encoding="utf-8")

    final = OUT / spec["out"]
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", lst,
         "-i", proj / "assets" / "mix.wav",
         "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", "-shortest", final])

    info = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                           "-of", "json", final]))
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), {})
    print(f"  -> {final.name}  {float(info['format']['duration']):.2f}s  "
          f"{int(info['format']['size']) / 1048576:.1f} MB  "
          f"{v['width']}x{v['height']} {v['r_frame_rate']}  a={a.get('codec_name')}")
    return final


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "AB"
    for k in which:
        build(k)
