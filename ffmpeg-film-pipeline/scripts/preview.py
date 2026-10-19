"""Contact sheet of every planned cut, labelled with the line it must carry.

    python preview.py            # all projects in the loaded spec
    python preview.py A          # just one
    python preview.py --at 0.5   # sample 50 % into the slot instead of the middle

Run this before build.py. If the picture does not show what the line claims
(feed going in, the die, the bracing inside the container), change `start` in
the spec — do not ship a film where the narration describes something else.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import QA, SRC, font_path  # noqa: E402
from spec import SPECS  # noqa: E402

COLS, TW = 3, 560


def at_frac():
    if "--at" in sys.argv:
        return float(sys.argv[sys.argv.index("--at") + 1])
    return 0.5


def grab(src_file, t, dst, tw, th):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", f"{t:.2f}", "-i", str(SRC / src_file), "-frames:v", "1",
                    "-vf", f"scale={tw}:{th}:force_original_aspect_ratio=increase:flags=lanczos,"
                           f"crop={tw}:{th}", str(dst)], check=True)


def sheet(key, spec):
    shots = spec["shots"]
    w, h = spec.get("w", 1920), spec.get("h", 1080)
    th = int(TW * h / w)
    rows = (len(shots) + COLS - 1) // COLS
    lab = 76
    img = Image.new("RGB", (COLS * TW, rows * (th + lab)), (14, 16, 18))
    draw = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(str(font_path("msyh.ttc")), 19)
    f2 = ImageFont.truetype(str(font_path("segoeui.ttf")), 16)
    tmp = Path(tempfile.mkdtemp())
    frac = at_frac()
    for i, s in enumerate(shots):
        p = tmp / f"{i:02d}.jpg"
        grab(s["src"], s["start"] + s["dur"] * frac, p, TW, th)
        im = Image.open(p).convert("RGB").resize((TW, th))
        x, y = (i % COLS) * TW, (i // COLS) * (th + lab)
        img.paste(im, (x, y))
        draw.text((x + 8, y + th + 5), f"{i + 1:02d}  {s.get('en', '')[:56]}", font=f1, fill=(240, 240, 240))
        draw.text((x + 8, y + th + 30), f"     {s['start']}s  {Path(s['src']).name[:34]}",
                  font=f2, fill=(150, 200, 205))
        draw.text((x + 8, y + th + 50), f"     {s.get('cn', '')[:34]}", font=f2, fill=(150, 155, 160))
    QA.mkdir(parents=True, exist_ok=True)
    dst = QA / f"preview_{spec['proj']}_{key}.png"
    img.save(dst)
    print(dst)
    return dst


if __name__ == "__main__":
    # Skip the location flags paths.py already consumed, so only projection keys remain.
    keys, i = [], 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a in ("--src", "--work", "--out", "--qa", "--logo", "--at"):
            i += 2
            continue
        if not a.startswith("--"):
            keys.append(a)
        i += 1
    keys = keys or list(SPECS)
    unknown = [k for k in keys if k not in SPECS]
    if unknown:
        sys.exit(f"[preview] no such projection key: {', '.join(unknown)} "
                 f"(have {', '.join(SPECS)})")
    for k in keys:
        sheet(k, SPECS[k])
