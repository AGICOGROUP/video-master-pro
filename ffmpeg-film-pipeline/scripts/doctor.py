"""Preflight. Say exactly what is missing and how to fix it.

    python doctor.py                # human report, exit 1 if anything hard fails
    python doctor.py --src D:\\footage
    python doctor.py --json         # machine-readable, for an agent to read

Hard requirements (film cannot be made without them): python, ffmpeg, ffprobe,
libx264 + aac encoders, numpy, Pillow, a CJK font, a latin font.
Soft requirements (only for optional paths): edge-tts (voiceover), node/npx
(HyperFrames), uv (MoneyPrinterTurbo / Pixelle).
"""
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

ROWS = []


def add(name, ok, detail, fix="", hard=True):
    ROWS.append(dict(name=name, ok=bool(ok), detail=detail, fix=fix, hard=hard))


def ver(cmd, args=("--version",)):
    exe = shutil.which(cmd)
    if not exe:
        return None, ""
    try:
        r = subprocess.run([exe, *args], capture_output=True, text=True, timeout=25)
        first = (r.stdout or r.stderr).strip().splitlines()
        return exe, first[0] if first else ""
    except Exception as exc:
        return exe, f"unusable ({exc.__class__.__name__})"


def main():
    add("python", sys.version_info >= (3, 10), sys.version.split()[0],
        "install Python 3.10+ and run the pipeline with it")

    for tool, hard in (("ffmpeg", True), ("ffprobe", True)):
        exe, v = ver(tool, ("-version",))
        add(tool, bool(exe) and "unusable" not in v, v or "not on PATH",
            "winget install Gyan.FFmpeg   |   brew install ffmpeg   |   apt install ffmpeg", hard)

    if shutil.which("ffmpeg"):
        r = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                           capture_output=True, text=True)
        for enc in ("libx264", "aac"):
            add(f"ffmpeg:{enc}", enc in r.stdout, "encoder present" if enc in r.stdout else "missing",
                "use a full ffmpeg build (Gyan/BtbN on Windows, distro build on Linux)")

    for mod, hard, fix in (("numpy", True, "pip install numpy"),
                           ("PIL", True, "pip install pillow"),
                           ("edge_tts", True, "pip install 'edge-tts>=7.3.1'")):
        try:
            m = importlib.import_module(mod)
            v = getattr(m, "__version__", "installed")
            add(mod, True, str(v), fix, hard)
        except Exception:
            add(mod, False, "not installed", fix, hard)

    try:
        import edge_tts  # noqa: F401
        ok = tuple(int(x) for x in getattr(edge_tts, "__version__", "0.0.0").split(".")[:2]) >= (7, 3)
        add("edge-tts>=7.3", ok, getattr(edge_tts, "__version__", "?"),
            "pip install --upgrade 'edge-tts>=7.3.1' (7.2.x returns 403)")
    except Exception:
        pass

    for name, path in paths.font_report().items():
        add(f"font:{name}", path is not None, str(path or "not found"),
            "install a CJK font (Windows: Microsoft YaHei, macOS: PingFang, "
            "Linux: fonts-noto-cjk) or set FILM_FONT_DIR")

    for tool, why in (("node", "HyperFrames / Remotion only"), ("uv", "MoneyPrinterTurbo / Pixelle only")):
        exe, v = ver(tool)
        add(tool, bool(exe), v or f"not on PATH — optional, {why}",
            "winget install OpenJS.NodeJS.LTS / install uv from astral.sh", hard=False)

    src = paths.P.src
    exists = src.exists()
    add("footage:src", exists, str(src) if exists else f"{src} (not found)",
        "pass --src <folder with the camera originals>, or set FILM_SRC")
    if exists:
        media = [p for p in src.rglob("*") if p.suffix.lower() in (".mp4", ".mov", ".m4v", ".avi")]
        add("footage:files", len(media) > 0, f"{len(media)} video files",
            "point --src at the folder that holds the clips")
        if media and shutil.which("ffprobe"):
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(media[0])], capture_output=True, text=True)
            add("footage:probe", r.returncode == 0, f"readable ({r.stdout.strip()[:8]}s)",
                "the file may be corrupt or use an unsupported codec")

    add("work dir", True, str(paths.P.work), "")
    add("out dir", True, str(paths.P.out), "")

    if "--json" in sys.argv:
        print(json.dumps(ROWS, indent=2, default=str))
    else:
        print(f"\n{'':3} {'check':22s} detail")
        print("-" * 78)
        for r in ROWS:
            mark = "OK " if r["ok"] else ("FAIL" if r["hard"] else "skip")
            print(f"{mark:3} {r['name']:22s} {r['detail']}")
            if not r["ok"] and r["fix"]:
                print(f"    {'':22s} -> {r['fix']}")
        bad = [r for r in ROWS if not r["ok"] and r["hard"]]
        print("-" * 78)
        if bad:
            print(f"{len(bad)} blocking problem(s). Fix those before rendering; "
                  f"run `python setup.py` for the python-side ones.")
        else:
            print("ready: the pipeline can render a film on this machine.")
    return 1 if any(not r["ok"] and r["hard"] for r in ROWS) else 0


if __name__ == "__main__":
    sys.exit(main())
