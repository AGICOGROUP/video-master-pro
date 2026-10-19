"""Audio for the two GEMCO promo videos.

Voiceover : edge-tts multilingual neural voices (the newer, more expressive
            generation -- a straight upgrade over GuyNeural/ChristopherNeural).
Music     : an original, procedurally-synthesised corporate/product-promo bed
            (major key, mid tempo, warm pad + soft arpeggio + light percussion).
Mix       : the bed's integrated loudness is MEASURED and then placed a fixed
            number of LU below the narration, plus sidechain ducking, so the
            voiceover is always clearly on top of the music.

The bed is synthesised from scratch with numpy -- no third-party samples, so
the commercial-rights position stays clean.
"""
import asyncio
import math
import os
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

from paths import WORK, project_assets  # noqa: E402
SR = 48000
sys.path.insert(0, str(WORK))
from spec import SPECS  # noqa: E402

# How far below the narration the music bed sits (integrated LUFS).
# 12 LU keeps the bed audible on phone speakers while the voice stays dominant.
BED_BELOW_LU = 12.0
# Gentle extra ducking applied while the voice is present.
DUCK_THRESHOLD = 0.050
DUCK_RATIO = 3.0


def run(args):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"rc={r.returncode}\n{r.stderr[-1500:]}")
    return r.stdout


def dur_of(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(out.strip())


def measure_lufs(path):
    """Integrated loudness (LUFS) of an audio file, via the ffmpeg loudnorm summary."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
                        "-af", "loudnorm=print_format=summary", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in (r.stderr or "").splitlines():
        if "Input Integrated" in line:
            return float(line.split(":")[-1].replace("LUFS", "").strip())
    raise RuntimeError("could not measure loudness of %s" % path)


# ------------------------------------------------------------------ TTS
async def _synth(text, voice, rate, out):
    import edge_tts
    c = edge_tts.Communicate(text, voice, rate=rate)
    await asyncio.wait_for(c.save(str(out)), timeout=75)


def synth_vo(spec, proj):
    assets = proj / "assets"
    (assets / "vo").mkdir(parents=True, exist_ok=True)
    cursor, placed = 0.0, []
    for i, s in enumerate(spec["shots"]):
        slot_start, slot_end = cursor, cursor + s["dur"]
        budget = s["dur"] - 0.75
        out = assets / "vo" / f"vo{i}.mp3"
        chosen = None
        # Start just under natural pace (a calmer read sounds less like an
        # announcer), then only speed up as far as the shot budget requires.
        for rate in ("-3%", "+1%", "+6%", "+11%", "+16%", "+22%"):
            for attempt in range(3):
                try:
                    asyncio.run(_synth(s["vo"], spec["voice"], rate, out))
                    d = dur_of(out)
                    chosen = (rate, d)
                    break
                except Exception as e:  # network jitter
                    if attempt == 2:
                        raise RuntimeError(f"vo{i} failed: {e}")
            if chosen and chosen[1] <= budget:
                break
        if not chosen:
            raise RuntimeError(f"vo{i} could not be produced")
        rate, d = chosen
        if d > budget:
            raise RuntimeError(f"vo{i} too long: {d:.2f}s > {budget:.2f}s even at {rate}")
        delay = slot_start + 0.32
        s["_vo_file"] = str(out)
        s["_vo_dur"] = d
        s["_vo_delay"] = delay
        placed.append((i, round(d, 2), rate, round(slot_start, 2), round(slot_end, 2)))
        print(f"  vo{i}: {d:5.2f}s (budget {budget:.2f}s, rate {rate}) @ {delay:.2f}s  | {s['vo'][:52]}")
        cursor = slot_end
    return placed


# ------------------------------------------------------------------ music
def _tone(f, t, amps=(1.0, 0.34, 0.15, 0.06), detune=0.0):
    x = np.zeros_like(t)
    for k, a in enumerate(amps, start=1):
        x += a * np.sin(2 * np.pi * f * k * (1.0 + detune * k) * t)
    return x


def _env(n, a, r):
    e = np.ones(n)
    na, nr = min(int(a * SR), n), min(int(r * SR), n)
    if na:
        e[:na] = np.linspace(0, 1, na) ** 1.5
    if nr:
        e[n - nr:] = np.linspace(1, 0, nr) ** 1.8
    return e


def music_promo(dur, root, bpm, seed, bright=1.0, perc=1.0):
    """Corporate / product-promo bed.

    Major key, mid tempo, I-V-vi-IV cycle: warm sustained pad, a soft bell
    arpeggio on the eighths, a gentle root-note bass, and light percussion
    (soft kick on 1 and 3, shaker off-beats, soft clap on 2 and 4 in the back
    half). Kept out of the low-mid band the narration occupies, so it reads as
    uplifting rather than dark.
    """
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))

    def semi(note, k):
        return note * (2.0 ** (k / 12.0))

    # I - V - vi - IV
    prog = [(0, "maj"), (7, "maj"), (9, "min"), (5, "maj")]
    slots = 8
    seg = dur / slots

    # ---- sustained pad (mid register, an octave above the bass) --------
    for i in range(slots):
        semi_off, quality = prog[i % 4]
        a = semi(root, semi_off) * 2.0
        third = semi(root, semi_off + (4 if quality == "maj" else 3)) * 2.0
        fifth = semi(root, semi_off + 7) * 2.0
        m = (t >= i * seg) & (t < min(dur, (i + 1) * seg + 0.9))
        if not m.any():
            continue
        tt = t[m] - i * seg
        env = _env(m.sum(), 0.55, 0.9)
        lvl = 0.050 * env
        L = (_tone(a, tt, detune=-0.0012) * 0.9 + _tone(third, tt, detune=0.0016) * 0.62
             + _tone(fifth, tt, detune=0.0009) * 0.5)
        R = (_tone(a, tt, detune=0.0013) * 0.9 + _tone(third, tt, detune=-0.0015) * 0.62
             + _tone(fifth, tt, detune=-0.0008) * 0.5)
        out[m, 0] += L * lvl
        out[m, 1] += R * lvl

    # ---- bell arpeggio on the eighths ----------------------------------
    beat = 60.0 / bpm
    eighth = beat / 2.0
    k = 0
    while k * eighth < dur:
        b0 = k * eighth
        slot = min(slots - 1, int(b0 / seg))
        semi_off, quality = prog[slot % 4]
        third = semi_off + (4 if quality == "maj" else 3)
        tones = [semi_off, third, semi_off + 7, third + 12]
        f = semi(root, tones[(k // 2) % 4]) * 4.0          # up two octaves
        m = (t >= b0) & (t < b0 + 1.7)
        tt = t[m] - b0
        env = (1 - np.exp(-tt * 120.0)) * np.exp(-tt * 4.2)
        note = _tone(f, tt, amps=(1.0, 0.20, 0.07)) * 0.040 * bright * env
        pan = 0.32 if (k % 2 == 0) else 0.68
        out[m, 0] += note * math.sqrt(1 - pan)
        out[m, 1] += note * math.sqrt(pan)
        k += 1

    # ---- bass: root of the chord, on each beat -------------------------
    k = 0
    while k * beat < dur:
        b0 = k * beat
        slot = min(slots - 1, int(b0 / seg))
        semi_off = prog[slot % 4][0]
        f = semi(root, semi_off)                            # low but above the rumble
        m = (t >= b0) & (t < b0 + 0.55)
        tt = t[m] - b0
        env = (1 - np.exp(-tt * 90.0)) * np.exp(-tt * 3.4)
        note = np.sin(2 * np.pi * f * tt) * 0.050 * env
        out[m, 0] += note
        out[m, 1] += note
        k += 1

    # ---- percussion ----------------------------------------------------
    if perc > 0:
        kb = int(0.16 * SR)
        tt = np.arange(kb) / SR
        kick = np.sin(2 * np.pi * (58.0 + 68.0 * np.exp(-tt * 26.0)) * tt) * np.exp(-tt * 14.0)
        clap_n = int(0.20 * SR)
        ct = np.arange(clap_n) / SR
        clap = rng.normal(0, 1, clap_n) * np.exp(-ct * 34.0)
        clap = np.diff(clap, prepend=0.0)                 # crude HP -> "clap" not "thud"
        sk = int(0.05 * SR)
        st = np.arange(sk) / SR
        shake = np.diff(rng.normal(0, 1, sk), prepend=0.0) * np.exp(-st * 70.0)
        b = 0
        while b * beat < dur:
            i0 = int(b * beat * SR)
            if b % 2 == 0:
                seg_ = min(kb, n - i0)
                if seg_ > 0:
                    out[i0:i0 + seg_, 0] += kick[:seg_] * 0.17 * perc
                    out[i0:i0 + seg_, 1] += kick[:seg_] * 0.17 * perc
            else:
                if b >= 4:                                # back half only
                    seg_ = min(clap_n, n - i0)
                    if seg_ > 0:
                        out[i0:i0 + seg_, 0] += clap[:seg_] * 0.055 * perc
                        out[i0:i0 + seg_, 1] += clap[:seg_] * 0.055 * perc
            b += 1
        b = 0
        while b * eighth < dur:
            i0 = int(b * eighth * SR)
            if b % 2 == 1:
                seg_ = min(sk, n - i0)
                if seg_ > 0:
                    out[i0:i0 + seg_, 0] += shake[:seg_] * 0.030 * perc
                    out[i0:i0 + seg_, 1] += shake[:seg_] * 0.034 * perc
            b += 1

    # ---- soft swell into the last chord change -------------------------
    st0 = dur * 0.60
    m = (t >= st0) & (t < dur)
    if m.any():
        tt = (t[m] - st0) / max(1e-6, dur - st0)
        swell = rng.normal(0, 1, m.sum()) * (tt ** 2.2) * 0.020
        swell = np.diff(swell, prepend=0.0)
        out[m, 0] += swell
        out[m, 1] += swell

    peak = float(np.max(np.abs(out)))
    if peak > 0:
        out = out / peak * 0.62
    return out


def write_music(spec, assets):
    m = spec["music"]
    x = music_promo(spec["duration"], root=m["root"], bpm=m["bpm"], seed=m["seed"],
                    bright=m.get("bright", 1.0), perc=m.get("perc", 1.0))
    fade_in = int(1.2 * SR)
    fade_out = int(2.6 * SR)
    x[:fade_in] *= (np.linspace(0, 1, fade_in) ** 1.4)[:, None]
    x[-fade_out:] *= (np.linspace(1, 0, fade_out) ** 1.6)[:, None]
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    path = assets / "music.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"  music: {path.name}  {dur_of(path):.2f}s  {measure_lufs(path):.1f} LUFS")
    return path


# ------------------------------------------------------------------ mix
def _build_voice(spec, assets):
    """Sum the placed voiceover clips into one voice-only track."""
    shots = spec["shots"]
    inputs, filters, labels = [], [], []
    for i, s in enumerate(shots):
        inputs += ["-i", s["_vo_file"]]
        d = int(round(s["_vo_delay"] * 1000))
        filters.append(f"[{i}:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,"
                       f"volume=1.0,adelay={d}|{d}[v{i}]")
        labels.append(f"[v{i}]")
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,"
                   f"apad,atrim=duration={spec['duration']},"
                   f"loudnorm=I=-16:TP=-1.5:LRA=9,alimiter=limit=0.97[vo]")
    out = assets / "voice.wav"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
         "-filter_complex", ";".join(filters), "-map", "[vo]", "-ar", str(SR),
         "-ac", "2", "-c:a", "pcm_s16le", str(out)])
    return out


def mix(spec, assets):
    voice = _build_voice(spec, assets)
    vo_lufs = measure_lufs(voice)
    bed_lufs = measure_lufs(assets / "music.wav")
    gain_db = (vo_lufs - BED_BELOW_LU) - bed_lufs
    gain_db = min(gain_db, 0.0)          # never boost the bed above its master level
    gain = 10.0 ** (gain_db / 20.0)
    total = spec["duration"]
    print(f"  voice {vo_lufs:.1f} LUFS | bed {bed_lufs:.1f} LUFS | "
          f"bed gain {gain_db:+.1f} dB -> {vo_lufs - BED_BELOW_LU:.1f} LUFS")

    filters = [
        f"[1:a]aresample={SR},aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"atrim=duration={total},volume={gain:.6f},afade=t=in:d=1.2,"
        f"afade=t=out:st={total - 2.6:.3f}:d=2.6[bed]",
        "[0:a]asplit=2[voice][control]",
        f"[bed][control]sidechaincompress=threshold={DUCK_THRESHOLD}:ratio={DUCK_RATIO}"
        f":attack=25:release=650[duck]",
        "[voice][duck]amix=inputs=2:normalize=0,"
        "loudnorm=I=-16:TP=-1.5:LRA=9,alimiter=limit=0.97[out]",
    ]
    out = assets / "mix.wav"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(voice), "-i", str(assets / "music.wav"),
         "-filter_complex", ";".join(filters), "-map", "[out]", "-ar", str(SR),
         "-ac", "2", "-c:a", "pcm_s16le", str(out)])
    print(f"  mix: {out.name}  {dur_of(out):.2f}s  {measure_lufs(out):.1f} LUFS")
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    mixonly = "--mixonly" in sys.argv
    which = args[0] if args else "AB"
    for key in which:
        spec = SPECS[key]
        proj = WORK / spec["proj"]
        assets = proj / "assets"
        print(f"=== {key} audio ===")
        if mixonly:
            cursor = 0.0
            for i, s in enumerate(spec["shots"]):
                s["_vo_file"] = str(assets / "vo" / f"vo{i}.mp3")
                s["_vo_dur"] = dur_of(s["_vo_file"])
                s["_vo_delay"] = cursor + 0.32
                cursor += s["dur"]
        else:
            synth_vo(spec, proj)
            write_music(spec, assets)
        mix(spec, assets)


if __name__ == "__main__":
    main()
