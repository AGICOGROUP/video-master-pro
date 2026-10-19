"""Render the typographic layer for every shot as a transparent 1920x1080 PNG.

The same editorial system as the HTML build (chapter numeral, hairline, eyebrow,
CN/EN pair at one size, logo, endcard rows) is reproduced with PIL so the films no
longer depend on a browser to composite text.
"""
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spec import SPECS  # noqa: E402

from paths import LOGO, WORK, font_path  # noqa: E402

W, H = 1920, 1080
OUT_SIZE = (1920, 1080)


def font(name, size):
    return ImageFont.truetype(str(font_path(name)), size)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def text_width(draw, s, f, tracking=0.0):
    if not s:
        return 0
    w = 0
    for ch in s:
        w += draw.textlength(ch, font=f) + tracking
    return w - tracking


def draw_tracked(draw, xy, s, f, fill, tracking=0.0):
    x, y = xy
    for ch in s:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + tracking
    return x


def fade_text_layer(size, draw_fn):
    """Draw on a transparent layer with a soft drop shadow for legibility."""
    shape = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(shape))
    shadow = shape.filter(ImageFilter.GaussianBlur(9))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    black = Image.new("RGBA", size, (0, 0, 0, 0))
    black.putalpha(shadow.getchannel("A").point(lambda a: int(a * 0.55)))
    out.alpha_composite(black)
    out.alpha_composite(shape)
    return out


def scrim(canvas, mode):
    """Paint a tonal scrim behind the type so it reads on bright footage."""
    import numpy as np
    a = np.zeros((H, W), dtype=np.float32)
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    if mode == "hero":
        r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.72)) ** 2)
        a[:] = np.clip(0.30 + r * 0.46, 0, 0.86)
    elif mode == "side":
        a[:] = np.clip(0.965 - np.clip((xx - 620) / 300.0, 0, 1) * 0.965, 0, 0.965)
    else:  # bottom gradient for the editorial blocks
        g = np.clip((yy - H * 0.52) / (H * 0.48), 0, 1) ** 1.25
        a[:] = 0.06 + g * 0.80
        a[: int(H * 0.10), :] = np.maximum(a[: int(H * 0.10), :], 0.45)
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., 0:3] = 4
    rgba[..., 3] = (a * 255).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(rgba, "RGBA"))


def load_logo(spec, width):
    """Logo is optional: a project without one still renders, with a wordmark."""
    path = spec.get("logo") or LOGO
    try:
        img = Image.open(path).convert("RGBA")
    except (FileNotFoundError, OSError):
        return None
    return img.resize((width, max(1, int(width * img.height / img.width))), Image.LANCZOS)


def wordmark(canvas, text, size, xy, fill):
    d = ImageDraw.Draw(canvas)
    d.text(xy, text, font=font("bahnschrift.ttf", size), fill=fill)


def build(spec, sh, idx, out_path):
    global W, H, OUT_SIZE
    tw, th = int(spec.get("w", 1920)), int(spec.get("h", 1080))
    OUT_SIZE = (tw, th)
    # Draw in a 1920-wide logical space so one layout serves 16:9 and 9:16, then
    # scale the finished layer down. Avoids a second hard-coded coordinate set.
    if th > tw:
        W, H = 1920, int(round(1920 * th / tw))
    else:
        W, H = tw, th
    accent = hexrgb(spec["accent"])
    ink = hexrgb(spec["ink"])
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layout = sh["layout"]

    if layout == "endcard":
        d0 = ImageDraw.Draw(canvas)
        d0.rectangle([0, 0, W, H], fill=(3, 5, 6, 232))
        logo = load_logo(spec, 352)
        if logo:
            canvas.alpha_composite(logo, (96, 88))
        else:
            wordmark(canvas, spec.get("brand", "BRAND"), 44, (96, 92), ink)

        f_eb = font("bahnschrift.ttf", 22)
        f_cn = font("msyhbd.ttc", 76)
        f_en = font("segoeui.ttf", 40)
        f_rk = font("msyh.ttc", 27)
        f_rv = font("segoeui.ttf", 27)
        f_cta = font("msyhbd.ttc", 28)
        f_cta_en = font("segoeui.ttf", 28)

        rows = sh.get("rows", [])
        block_h = 34 + 22 + 34 + 86 + 16 + 50 + 40 + len(rows) * 55 + 38 + 44
        y = H - 104 - block_h
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        draw_tracked(d, (96, y), sh["eyebrow"], f_eb, accent + (255,), 8)
        y += 34 + 22
        d.text((96, y), sh["cn"], font=f_cn, fill=(255, 255, 255, 255))
        y += 86 + 16
        d.text((96, y), sh["en"], font=f_en, fill=ink + (255,))
        y += 50 + 40
        for cn, en in rows:
            d.line([(96, y), (96 + 1120, y)], fill=(255, 255, 255, 38), width=1)
            d.text((96, y + 14), cn, font=f_rk, fill=(255, 255, 255, 255))
            tw = text_width(d, en, f_rv)
            d.text((96 + 1120 - tw, y + 14), en, font=f_rv, fill=ink + (255,))
            y += 55
        y += 20
        d.text((96, y), sh["cta_cn"], font=f_cta, fill=(255, 255, 255, 255))
        cw = d.textlength(sh["cta_cn"], font=f_cta)
        d.text((96 + cw + 20, y + 2), sh["cta_en"], font=f_cta_en, fill=accent + (255,))
        canvas.alpha_composite(layer)

    elif layout == "hero":
        scrim(canvas, "hero")
        f_eb = font("bahnschrift.ttf", 23)
        f_cn = font("msyhbd.ttc", 112)
        f_en = font("bahnsans.ttf" if False else "segoeui.ttf", 42)

        probe = ImageDraw.Draw(canvas)
        cn_w = probe.textlength(sh["cn"], font=f_cn)
        en_w = text_width(probe, sh["en"], f_en, 6)
        eb_w = text_width(probe, sh["eyebrow"], f_eb, 9)

        total = 30 + 34 + 1 + 34 + 119 + 26 + 50 + 40 + 2
        y = (H - total) / 2
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        draw_tracked(d, ((W - eb_w) / 2, y), sh["eyebrow"], f_eb, accent + (255,), 9)
        y += 30 + 34
        d.line([((W - 250) / 2, y), ((W + 250) / 2, y)], fill=(255, 255, 255, 90), width=1)
        y += 34
        d.text(((W - cn_w) / 2, y), sh["cn"], font=f_cn, fill=(255, 255, 255, 255))
        y += 119 + 26
        draw_tracked(d, ((W - en_w) / 2, y), sh["en"], f_en, ink + (255,), 6)
        y += 50 + 40
        d.line([((W - 64) / 2, y), ((W + 64) / 2, y)], fill=accent + (255,), width=2)
        canvas.alpha_composite(layer)

    else:  # left / right / side
        right = layout == "right"
        side = layout == "side"
        scrim(canvas, "side" if side else "bottom")
        f_ch = font("bahnschrift.ttf", 30)
        f_eb = font("bahnschrift.ttf", 21)
        f_cn = font("msyhbd.ttc", 42)
        f_en = font("segoeui.ttf", 42)

        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)

        # top-left chapter rail
        d.text((96, 64), sh.get("ch", ""), font=f_ch, fill=accent + (255,))
        cw = d.textlength(sh.get("ch", ""), font=f_ch)
        d.line([(96 + cw + 22, 78), (96 + cw + 56, 78)], fill=(255, 255, 255, 110), width=1)
        draw_tracked(d, (96 + cw + 78, 70), sh["eyebrow"], f_eb, (237, 241, 242, 255), 7)

        logo = load_logo(spec, 292)
        if logo:
            layer.alpha_composite(logo, (W - 96 - 292, 56))
        else:
            wordmark(layer, spec.get("brand", "BRAND"), 34, (W - 96 - 210, 60), ink)

        if side:
            bx, by = 96, int(H * 0.5 - 60)
        else:
            cn_w = d.textlength(sh["cn"], font=f_cn)
            en_w = text_width(d, sh["en"], f_en, 1)
            bx = W - 96 - max(cn_w, en_w) if right else 96
            by = H - 98 - 2 - 26 - 54 - 12 - 54
        d.line([(bx, by), (bx + 92, by)], fill=accent + (255,), width=2)
        y = by + 2 + 26
        if right:
            tw = text_width(d, sh["cn"], f_cn)
            d.text((W - 96 - tw, y), sh["cn"], font=f_cn, fill=(255, 255, 255, 255))
            y += 54 + 12
            tw = text_width(d, sh["en"], f_en, 1)
            draw_tracked(d, (W - 96 - tw, y), sh["en"], f_en, ink + (255,), 1)
        else:
            d.text((bx, y), sh["cn"], font=f_cn, fill=(255, 255, 255, 255))
            y += 54 + 12
            draw_tracked(d, (bx, y), sh["en"], f_en, ink + (255,), 1)
        canvas.alpha_composite(layer)

    if (W, H) != OUT_SIZE:
        canvas = canvas.resize(OUT_SIZE, Image.LANCZOS)
    canvas.save(out_path)
    return out_path


def canvas(spec):
    global W, H
    W, H = spec.get('w', 1920), spec.get('h', 1080)


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else ''.join(SPECS)
    for key in which:
        spec = SPECS[key]
        canvas(spec)
        outdir = WORK / spec["proj"] / "assets" / "overlay"
        outdir.mkdir(parents=True, exist_ok=True)
        for i, sh in enumerate(spec["shots"]):
            p = build(spec, sh, i, outdir / f"ov{i}.png")
            print(key, i, sh["layout"], p.stat().st_size)


if __name__ == "__main__":
    main()
