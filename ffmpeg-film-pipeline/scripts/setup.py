"""Install what the pipeline needs. Idempotent, and never installs silently.

    python setup.py            # show what would be installed, then do the safe parts
    python setup.py --yes      # no prompt
    python setup.py --check    # same as `python doctor.py`

It installs the python packages itself (pip, no admin needed) and prints the one
system command per OS for ffmpeg — system package managers need the user's own
elevation, so we hand over the exact command instead of guessing.
"""
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = [sys.executable, "-m", "pip", "install", "--upgrade"]
PY_PKGS = ["numpy", "pillow", "edge-tts>=7.3.1"]


def sh(cmd):
    print("  $", " ".join(cmd), flush=True)
    return subprocess.run(cmd, capture_output=True, text=True)


def ffmpeg_hint():
    os_name = platform.system()
    if os_name == "Windows":
        if shutil.which("winget"):
            return "winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements"
        return "download a build from gyan.dev/ffmpeg/builds and add its bin\\ to PATH"
    if os_name == "Darwin":
        return "brew install ffmpeg"
    return "sudo apt install ffmpeg   # or dnf/pacman equivalent"


def font_hint():
    os_name = platform.system()
    if os_name == "Windows":
        return "Windows already ships Microsoft YaHei; if missing, install a CJK font pack"
    if os_name == "Darwin":
        return "PingFang ships with macOS; nothing to do"
    return "sudo apt install fonts-noto-cjk"


def main():
    if "--check" in sys.argv:
        return subprocess.call([sys.executable, str(HERE / "doctor.py"), *sys.argv[2:]]) if False else \
            subprocess.call([sys.executable, str(HERE / "doctor.py")])

    print("== ffmpeg / ffprobe")
    have = shutil.which("ffmpeg") and shutil.which("ffprobe")
    print(f"  {'present' if have else 'MISSING'}")
    if not have:
        print(f"  -> {ffmpeg_hint()}")

    print("== python packages")
    for pkg in PY_PKGS:
        looks = pkg.split(">=")[0]
        mod = {"pillow": "PIL"}.get(looks, looks.replace("-", "_"))
        try:
            __import__(mod)
            print(f"  {looks}: present")
            continue
        except Exception:
            pass
        print(f"  {looks}: installing")
        r = sh(PY + [pkg])
        print("   ", "ok" if r.returncode == 0 else (r.stderr.strip().splitlines() or ["failed"])[-1])

    print("== fonts")
    import paths
    for name, path in paths.font_report().items():
        print(f"  {name}: {path or 'MISSING'}")
    if any(p is None for p in paths.font_report().values()):
        print(f"  -> {font_hint()}")

    print("== optional")
    for tool, why in (("node", "HyperFrames"), ("uv", "MoneyPrinterTurbo / Pixelle")):
        print(f"  {tool}: {'present' if shutil.which(tool) else 'absent'}  ({why})")

    print("\nNow run:  python doctor.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
