"""First-run gate: install the Python side, then prove the machine can render.

    python firstrun.py              # install missing packages, then run the full check
    python firstrun.py --check      # check only, install nothing

Exit 0 means the pipeline is ready. Exit 1 prints the exact command to fix each
blocking item. Safe to run repeatedly.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKGS = ["numpy", "pillow", "edge-tts>=7.3.1"]
MODS = {"numpy": "numpy", "pillow": "PIL", "edge-tts": "edge_tts"}


def missing():
    out = []
    for pkg in PKGS:
        name = pkg.split(">=")[0]
        try:
            __import__(MODS[name])
        except Exception:
            out.append(pkg)
    return out


def main():
    check_only = "--check" in sys.argv

    print("== step 1/2  python packages")
    gaps = missing()
    if not gaps:
        print("  all present: " + ", ".join(PKGS))
    elif check_only:
        print("  MISSING: " + ", ".join(gaps) + "  (run without --check to install)")
    else:
        for pkg in gaps:
            print(f"  installing {pkg} ...", flush=True)
            r = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", pkg],
                               capture_output=True, text=True)
            print("   ", "ok" if r.returncode == 0 else
                  (r.stderr.strip().splitlines() or ["failed"])[-1])
        gaps = missing()
        if gaps:
            print("  still missing: " + ", ".join(gaps))

    print("\n== step 2/2  environment check")
    rc = subprocess.call([sys.executable, str(HERE / "doctor.py"), *sys.argv[1:]])
    print("\n" + "-" * 78)
    if rc == 0:
        print("READY. Next: python newfilm.py --src <footage> --work <dir> --out <dir> "
              "--proj film01 --shots 8 --duration 40 --aspect 16:9")
    else:
        print("NOT READY. Fix the FAIL lines above, then run this script again.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
