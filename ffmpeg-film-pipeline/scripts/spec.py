"""Project definitions for the pipeline.

A film is one dict: key, proj, out, voice, duration, palette, music, shots[].
`newfilm.py` writes one for you from a footage folder; you can also author it by
hand. Lookup order, first hit wins:

    1. $FILM_WORK/spec_local.py   (project-specific, what newfilm.py writes)
    2. ./spec_local.py            (if you run from a project folder)
    3. spec_example.py            (the shipped GEMCO reference)

Every script imports `SPECS` and `SRC` from here, so nothing downstream needs to
know where the project file lives.
"""
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import SRC, WORK  # noqa: E402,F401

HERE = Path(__file__).resolve().parent
CANDIDATES = [WORK / "spec_local.py", Path.cwd() / "spec_local.py", HERE / "spec_example.py"]


def _load():
    for path in CANDIDATES:
        if not path.exists():
            continue
        try:
            ns = runpy.run_path(str(path))
        except Exception as exc:  # a broken project file must not look like "no shots"
            sys.exit(f"[spec] {path} failed to load: {exc.__class__.__name__}: {exc}")
        specs = ns.get("SPECS")
        if not specs:
            sys.exit(f"[spec] {path} defines no SPECS dict")
        if path.name == "spec_example.py":
            print(f"[spec] no spec_local.py found — falling back to the shipped example "
                  f"({path.name}). Run newfilm.py to create a real project.", flush=True)
        else:
            print(f"[spec] using project file {path}", flush=True)
        return specs, path
    sys.exit("[spec] no project file found — run newfilm.py, or set FILM_WORK to a folder "
             "that contains spec_local.py")


SPECS, SOURCE_FILE = _load()
