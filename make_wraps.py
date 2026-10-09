#!/usr/bin/env python3
"""Generate Tesla custom wraps (PNG 1024x1024) masked to the Model Y template panels.

Usage: python3 make_wraps.py [template.png]
Output: wraps/*.png  (copy the folder to USB drive root as `Wraps`)
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).parent
TEMPLATE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "templates" / "modely_template.png"
OUT = ROOT / "wraps"
S = 1024
rng = np.random.default_rng(42)


def panel_mask():
    """True inside car panels: everything not reachable from the border without crossing outline."""
    t = np.asarray(Image.open(TEMPLATE).convert("RGBA").resize((S, S)))
    opaque_dark = (t[..., 3] > 0) & (t[..., :3].mean(-1) < 200)
    line = Image.fromarray((opaque_dark * 255).astype("uint8")).filter(ImageFilter.MaxFilter(9))
    barrier = np.asarray(line) > 0
    # flood fill outside from corners
    from collections import deque
    outside = np.zeros_like(barrier)
    q = deque([(0, 0), (0, S - 1), (S - 1, 0), (S - 1, S - 1)])
    for p in q:
        outside[p] = True
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < S and 0 <= nx < S and not outside[ny, nx] and not barrier[ny, nx]:
                outside[ny, nx] = True
                q.append((ny, nx))
    # panels = not outside; outlines themselves get painted too (slight bleed avoids gaps)
    return ~outside


def grid():
    y, x = np.mgrid[0:S, 0:S]
    return x.astype(float), y.astype(float)


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def lerp(c1, c2, t):
    t = np.clip(t, 0, 1)[..., None]
    return hexrgb(c1) * (1 - t) + hexrgb(c2) * t


def noise(scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((S // scale + 2, S // scale + 2))
    im = Image.fromarray((small * 255).astype("uint8")).resize((S, S), Image.BICUBIC)
    return np.asarray(im, float) / 255


# ---------- skins ----------
def carbon():
    x, y = grid()
    cell = 12
    a = ((x // cell + y // cell) % 2).astype(float)
    wave = np.sin(x / cell * np.pi) * np.sin(y / cell * np.pi)
    base = 22 + 18 * a + 10 * wave
    img = np.stack([base, base, base * 1.05], -1)
    return img


def midnight():
    x, y = grid()
    img = lerp("#05060f", "#1b2a6b", y / S * 0.8 + noise(128, 1) * 0.3)
    stars = rng.random((S, S)) > 0.9985
    stars = np.asarray(Image.fromarray((stars * 255).astype("uint8")).filter(ImageFilter.MaxFilter(3))) > 0
    img[stars] = 255
    return img


def racing():
    x, y = grid()
    img = np.zeros((S, S, 3)) + hexrgb("#d10a10")
    for off, w, col in ((0, 70, "#f5f5f5"), (-105, 26, "#111111"), (105, 26, "#111111")):
        m = np.abs(x - S / 2 - off) < w / 2
        img[m] = hexrgb(col)
    return img


def synthwave():
    x, y = grid()
    img = lerp("#2b0a5e", "#ff2e97", (y / S) ** 1.2)
    lines = (y % 64 < 4) | (x % 64 < 4)
    img[lines] = hexrgb("#22e6ff")
    return img


def camo():
    n = noise(64, 3) * 0.5 + noise(32, 4) * 0.3 + noise(128, 5) * 0.2
    cols = ["#3b4a2a", "#6b7a45", "#2a2f1c", "#8a7a52"]
    img = np.zeros((S, S, 3))
    q = np.digitize(n, np.quantile(n, [0.25, 0.5, 0.75]))
    for i, c in enumerate(cols):
        img[q == i] = hexrgb(c)
    return img


def sunset():
    x, y = grid()
    t = y / S
    img = lerp("#ff512f", "#f09819", t * 2)
    img2 = lerp("#f09819", "#8e2de2", (t - 0.5) * 2)
    return np.where((t > 0.5)[..., None], img2, img)


def matte_white_stripe():
    x, y = grid()
    img = np.zeros((S, S, 3)) + hexrgb("#e8e8ea")
    img += (noise(2, 9)[..., None] - 0.5) * 6
    m = np.abs(x - S / 2) < 14
    img[m] = hexrgb("#0a84ff")
    return img


def neon_dots():
    x, y = grid()
    s = 36
    v = np.sin(x / s * 2) + np.sin((x * 0.5 + y * 0.866) / s * 2) + np.sin((x * 0.5 - y * 0.866) / s * 2)
    img = lerp("#0b0b0b", "#00e5a8", (v - 1.0) * 2)
    return img


SKINS = {
    "Carbon_Fiber": carbon,
    "Midnight_Stars": midnight,
    "Racing_Red": racing,
    "Synthwave": synthwave,
    "Forest_Camo": camo,
    "Sunset_Fade": sunset,
    "Matte_White_Blue": matte_white_stripe,
    "Neon_Dots": neon_dots,
}

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    mask = panel_mask()
    for name, fn in SKINS.items():
        rgb = np.clip(fn(), 0, 255).astype("uint8")
        rgba = np.dstack([rgb, np.where(mask, 255, 0).astype("uint8")])
        im = Image.fromarray(rgba, "RGBA")
        path = OUT / f"{name}.png"
        im.save(path, optimize=True)
        print(path.name, f"{path.stat().st_size / 1024:.0f} KB")
