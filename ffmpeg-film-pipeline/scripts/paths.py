"""One place that decides where anything lives.

Resolution order, for every path the pipeline touches:

    command-line flag  ->  environment variable  ->  neutral default

No absolute machine-specific path is baked into this skill, so the same files
run on the author's box and on a teammate's box without edits. Defaults are
relative to the current directory: ./source, ./work, ./out.
"""
import argparse
import os
import sys
from pathlib import Path
from types import SimpleNamespace

ENV = {
    "src": "FILM_SRC",
    "work": "FILM_WORK",
    "out": "FILM_OUT",
    "qa": "FILM_QA",
    "logo": "FILM_LOGO",
}

FLAGS = {
    "src": "--src",
    "work": "--work",
    "out": "--out",
    "qa": "--qa",
    "logo": "--logo",
}


def _parse():
    p = argparse.ArgumentParser(add_help=False)
    for flag in FLAGS.values():
        p.add_argument(flag, dest=flag.lstrip("-"), default=None)
    ns, _ = p.parse_known_args()
    return vars(ns)


def _pick(name, default):
    cli = _parse()
    v = cli.get(name) or os.environ.get(ENV[name])
    return Path(v).expanduser().resolve() if v else Path(default).expanduser().resolve()


def resolve():
    work = _pick("work", Path.cwd() / "work")
    out = _pick("out", Path.cwd() / "out")
    qa = _pick("qa", work / "_qa")
    src = _pick("src", Path.cwd() / "source")
    logo = _pick("logo", work / "logo_white.png")
    return SimpleNamespace(src=src, work=work, out=out, qa=qa, logo=logo)


P = resolve()
SRC = P.src
WORK = P.work
OUT = P.out
QA = P.qa
LOGO = P.logo


def require_src(src=None):
    """Fail loudly and usefully rather than halfway through a cut."""
    src = Path(src or SRC)
    if not src.exists():
        sys.exit(
            f"[paths] raw footage folder not found: {src}\n"
            f"        pass --src <folder> or set {ENV['src']}.\n"
            f"        expected: a folder that holds the camera originals (mp4/mov)."
        )
    return src


def project_assets(spec):
    """Where build.py puts cut shots and where compose.py reads them."""
    return WORK / spec["proj"] / "assets"


# --------------------------------------------------------------------- fonts
# One catalog, resolved by glob so Windows / macOS / Linux all work. Callers
# keep asking for the historical file names; we hand back whatever exists.
FONT_DIRS = [
    Path(os.environ.get("FILM_FONT_DIR", "")) if os.environ.get("FILM_FONT_DIR") else None,
    Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
    Path("/System/Library/Fonts"),
    Path("/System/Library/Fonts/Supplemental"),
    Path("/Library/Fonts"),
    Path.home() / "Library/Fonts",
    Path("/usr/share/fonts"),
    Path("/usr/local/share/fonts"),
    Path.home() / ".fonts",
]

ALIASES = {
    "msyh.ttc": ["msyh.ttc", "NotoSansCJK*.ttc", "NotoSansSC*.otf", "PingFang*.ttc",
                 "Hiragino*GB*.tt*", "wqy-zenhei*.tt*"],
    "msyhbd.ttc": ["msyhbd.ttc", "msyh.ttc", "NotoSansCJK*Bold*.tt*", "NotoSansSC*Bold*.otf",
                   "PingFang*.ttc", "wqy-zenhei*.tt*"],
    "segoeui.ttf": ["segoeui.ttf", "DejaVuSans.ttf", "Arial.ttf", "LiberationSans-Regular.ttf",
                    "Helvetica*.tt*"],
    "segoeuib.ttf": ["segoeuib.ttf", "DejaVuSans-Bold.ttf", "Arial*Bold*.tt*",
                     "LiberationSans-Bold.ttf", "Helvetica*.tt*"],
    "bahnschrift.ttf": ["bahnschrift.ttf", "DINAlternate*.tt*", "DejaVuSans-Bold.ttf",
                        "LiberationSans-Bold.ttf", "Arial*Bold*.tt*"],
}

_font_cache = {}


def font_path(name):
    """Return a real font file for a requested name, searching the whole OS."""
    if name in _font_cache:
        return _font_cache[name]
    patterns = ALIASES.get(name, [name])
    for pattern in patterns:
        for d in FONT_DIRS:
            if not d or not d.exists():
                continue
            hits = sorted(d.rglob(pattern))
            if hits:
                _font_cache[name] = hits[0]
                return hits[0]
    raise FileNotFoundError(
        f"[paths] no usable font for {name!r}. Install a CJK + latin font, or set "
        f"FILM_FONT_DIR to a folder that has one."
    )


def font_report():
    """{(requested) name: resolved path or None} — used by doctor.py."""
    out = {}
    for name in ALIASES:
        try:
            out[name] = font_path(name)
        except FileNotFoundError:
            out[name] = None
    return out
