"""CLAUDE showreel - every pixel is code.
Usage:
  python render.py preview 1.5 5 9 11     -> out/preview_XX.XX.png at given seconds
  python render.py video [out/showreel.mp4] [out/music.wav]
                                          -> full render piped to ffmpeg (run music.py first)
"""
import sys, math, shutil, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------- config: edit text here ----------
TITLE = "CLAUDE"
SUBTITLE = "MỌI ĐIỂM ẢNH  ·  MỌI NỐT NHẠC  —  ĐỀU LÀ CODE"
HUD_BRAND = "CLAUDE  ·  SHOWREEL 2026"
HUD_STACK = "NUMPY  ·  PIL  ·  FFMPEG  ·  30 FPS"

W, H, FPS, DUR = 1280, 720, 30, 12.0
NF = int(FPS * DUR)
ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "fonts"
OUT_DIR = ROOT / "out"
rng = np.random.default_rng(7)

def font(name, size):
    path = FONT_DIR / name
    if not path.exists():
        sys.exit(f"Missing font {path} - the repo ships fonts/Inter-*.otf, re-clone or copy them back.")
    return ImageFont.truetype(str(path), size)

F_HUD = font("Inter-Medium.otf", 13)
F_TITLE = font("Inter-ExtraLight.otf", 120)
F_SUB = font("Inter-Medium.otf", 17)

def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)

def fbm(w, h, octaves=6, seed=1):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw, gh = max(2, w >> (7 - o)), max(2, h >> (7 - o))
        g = (r.random((gh, gw)) * 255).astype(np.uint8)
        up = np.asarray(Image.fromarray(g).resize((w, h), Image.BICUBIC), np.float32) / 255
        out += up * amp; tot += amp; amp *= 0.5
    return out / tot

# ---------- precomputed assets ----------
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
NEB = fbm(W * 2, H * 2, seed=3)
CLOUD = fbm(W * 3, 260, seed=11)
_w = fbm(1024, 1024, octaves=5, seed=21)
_w = np.concatenate([_w, _w[:, ::-1]], 1)
WAVE = np.concatenate([_w, _w[::-1]], 0)  # mirrored -> seamless 2048 tile
STARS = np.stack([rng.uniform(-1.6, 1.6, 2600), rng.uniform(-1, 1, 2600), rng.uniform(0.02, 1, 2600)], 1)

# ---------- shot 1: starfield ----------
def shot_stars(u):
    z0 = STARS[:, 2]
    speed = 0.12 + 0.55 * u ** 3
    z = (z0 - speed * u * 1.4) % 1.0 + 0.015
    f = 520
    sx = STARS[:, 0] / z * f * 0.5 + W / 2
    sy = STARS[:, 1] / z * f * 0.5 + H / 2
    b = np.clip(0.5 / z, 0, 6)
    acc = np.zeros((H, W), np.float32)
    # streaks: sample a few points along motion
    for k in range(4):
        zk = z + k * 0.004 * (1 + 8 * u ** 2)
        px = (STARS[:, 0] / zk * f * 0.5 + W / 2).astype(int)
        py = (STARS[:, 1] / zk * f * 0.5 + H / 2).astype(int)
        m = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        np.add.at(acc, (py[m], px[m]), b[m] * (1 - k * 0.22))
    img = Image.fromarray(np.clip(acc * 255, 0, 255).astype(np.uint8))
    core = np.asarray(img.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    bloom = np.asarray(img.filter(ImageFilter.GaussianBlur(5)), np.float32) / 255
    s = 1 + 0.15 * u
    ox, oy = int(W * 0.5 * (1 - 1 / s)), int(H * 0.5 * (1 - 1 / s))
    neb = np.asarray(Image.fromarray((NEB * 255).astype(np.uint8)).crop((ox + W // 2, oy + H // 2, ox + W // 2 + int(W / s), oy + H // 2 + int(H / s))).resize((W, H)), np.float32) / 255
    neb = np.clip(neb - 0.5, 0, 1) * 1.6
    rgb = np.zeros((H, W, 3), np.float32)
    rgb += neb[..., None] * np.array([0.22, 0.10, 0.30]) + (neb ** 2)[..., None] * np.array([0.05, 0.18, 0.22])
    rgb += core[..., None] * np.array([1.0, 0.97, 0.92]) * 1.6
    rgb += bloom[..., None] * np.array([0.6, 0.7, 1.0]) * 1.2
    return rgb

# ---------- shot 2: crystal ----------
PHI = (1 + 5 ** 0.5) / 2
ICO = np.array([[-1, PHI, 0], [1, PHI, 0], [-1, -PHI, 0], [1, -PHI, 0], [0, -1, PHI], [0, 1, PHI],
                [0, -1, -PHI], [0, 1, -PHI], [PHI, 0, -1], [PHI, 0, 1], [-PHI, 0, -1], [-PHI, 0, 1]], np.float32)
ICO /= np.linalg.norm(ICO[0])
EDGES = [(i, j) for i in range(12) for j in range(i + 1, 12) if abs(np.linalg.norm(ICO[i] - ICO[j]) - 1.0515) < 0.05]
BG2 = (np.exp(-((XX - W / 2) ** 2 + (YY - H / 2) ** 2) / (2 * 380 ** 2)))[..., None] * np.array([0.05, 0.07, 0.14], np.float32)

def rot(a, b):
    ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
    ry = np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])
    rx = np.array([[1, 0, 0], [0, cb, -sb], [0, sb, cb]])
    return rx @ ry

def shot_crystal(u, t):
    layer = Image.new("RGB", (W, H)); d = ImageDraw.Draw(layer)
    for scale, a, col, wd in [(250 + 30 * u, t * 0.9, (150, 210, 255), 2), (140, -t * 1.4 + 1, (255, 190, 110), 2)]:
        P = ICO @ rot(a, 0.5 + t * 0.35).T
        zc = P[:, 2] + 3.2
        px = P[:, 0] / zc * 3.2 * scale + W / 2
        py = P[:, 1] / zc * 3.2 * scale + H / 2
        for i, j in EDGES:
            depth = 0.45 + 0.55 * (1 - (P[i, 2] + P[j, 2] + 2) / 4)
            c = tuple(int(v * depth) for v in col)
            d.line([(px[i], py[i]), (px[j], py[j])], fill=c, width=wd)
        for k in range(12):
            r = 3
            d.ellipse([px[k] - r, py[k] - r, px[k] + r, py[k] + r], fill=(255, 245, 230))
    core = np.asarray(layer, np.float32) / 255
    glow = np.asarray(layer.filter(ImageFilter.GaussianBlur(10)), np.float32) / 255
    # rotating light rays
    ang = np.arctan2(YY - H / 2, XX - W / 2)
    rays = (0.5 + 0.5 * np.cos(ang * 9 + t * 0.6)) ** 6 * np.exp(-np.hypot(XX - W / 2, YY - H / 2) / 420)
    rgb = BG2 + rays[..., None] * np.array([0.10, 0.09, 0.07]) + core * 1.1 + glow * 1.6
    return rgb

# ---------- shot 3: ocean sunrise ----------
def shot_ocean(u, t):
    hz = H * (0.66 - 0.07 * ease(u / 0.8))
    sun_x = W * 0.5
    sun_y = hz + 30 - 75 * ease(u / 1.0)
    e = (hz - YY) / H  # elevation, >0 sky
    zen = np.array([0.03, 0.06, 0.18], np.float32)
    hor = np.array([1.00, 0.55, 0.25], np.float32)
    mix = np.exp(-np.clip(e, 0, None) * 5.5)[..., None]
    sky = zen * (1 - mix) + hor * mix
    dsun = np.hypot(XX - sun_x, (YY - sun_y) * 1.15)
    glow = (np.exp(-dsun / 70) * 1.2 + np.exp(-dsun / 260) * 0.35)[..., None] * np.array([1.0, 0.72, 0.42])
    sky = sky + glow
    disc = np.clip((34 - dsun) / 2.0, 0, 1)[..., None] * np.array([1.4, 1.25, 1.0])
    sky = sky + disc
    # clouds: band above horizon, scrolling
    cy0 = int(hz - 250)
    off = int(t * 18) % (W * 2)
    cl = np.zeros((H, W), np.float32)
    y0, y1 = max(cy0, 0), max(int(hz), 0)
    if y1 > y0:
        tex = CLOUD[(y0 - cy0):(y1 - cy0), off:off + W]
        band = np.clip((tex - 0.5) * 3.0, 0, 1)
        vm = np.sin(np.linspace(0, np.pi, y1 - y0))[:, None] ** 1.5
        cl[y0:y1] = band * vm
    rim = np.exp(-dsun / 300)[..., None]
    ccol = np.array([0.18, 0.10, 0.16]) * (1 - rim) + np.array([1.0, 0.55, 0.30]) * rim
    sky = sky * (1 - cl[..., None] * 0.85) + ccol * cl[..., None] * 0.9
    # ocean
    below = YY > hz
    dy = np.clip(YY - hz, 1, None)
    z = 60.0 / dy
    wx = (XX - W / 2) * z / 60
    ix1 = ((wx * 320 + t * 9 + 700)).astype(np.int32) % 2048; iz1 = ((z * 2600 - t * 70)).astype(np.int32) % 2048
    ix2 = ((wx * 760 - t * 14 + 300)).astype(np.int32) % 2048; iz2 = ((z * 5200 - t * 130 + 500)).astype(np.int32) % 2048
    wv = WAVE[iz1, ix1] * 0.6 + WAVE[iz2, ix2] * 0.4
    gl = np.clip((wv - 0.47) * 4.5, 0, 1) ** 2
    gl = np.asarray(Image.fromarray((gl * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    width = 8 + dy * 0.9
    streak = np.exp(-((XX - sun_x) ** 2) / (2 * width ** 2))
    sun_h = np.clip(1 - (sun_y - (hz - 150)) / 180, 0.2, 1.0)
    sea_base = np.array([0.02, 0.04, 0.09]) + hor * np.exp(-dy / 50)[..., None] * 0.55
    sea = sea_base + (streak * gl * 2.2 * sun_h)[..., None] * np.array([1.0, 0.72, 0.45])
    sea = sea + (gl * 0.05)[..., None]
    rgb = np.where(below[..., None], sea, sky)
    haze = np.exp(-np.abs(YY - hz) / 10)[..., None] * np.array([0.35, 0.20, 0.10])
    return rgb + haze

# ---------- text helpers ----------
def tracked(draw, xy, text, fnt, track, fill, anchor_center=True):
    widths = [fnt.getlength(c) for c in text]
    total = sum(widths) + track * (len(text) - 1)
    x, y = xy
    if anchor_center:
        x -= total / 2
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=fnt, fill=fill)
        x += w + track
    return total

def overlay(t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    a = int(200 * ease(t / 0.6))
    tracked(d, (36, 28), HUD_BRAND, F_HUD, 2.5, (255, 255, 255, a), False)
    f = int(round(t * FPS)); tc = f"00:00:{f // FPS:02d}:{f % FPS:02d}"
    tracked(d, (W - 36 - 120, 28), tc, F_HUD, 1.5, (255, 255, 255, a), False)
    shots = [(0, 3.35, "01/03", "STARFIELD  ·  PERSPECTIVE"), (3.35, 6.6, "02/03", "CRYSTAL  ·  3D WIREFRAME"),
             (6.6, 99, "03/03", "SUNRISE  ·  PROCEDURAL OCEAN")]
    for s0, s1, n, name in shots:
        if s0 <= t < s1:
            tracked(d, (36, H - 46), f"{n}   {name}", F_HUD, 2.5, (255, 255, 255, a), False)
    tracked(d, (W - 36 - 330, H - 46), HUD_STACK, F_HUD, 2, (255, 255, 255, int(a * 0.6)), False)
    d.rectangle([36, H - 22, W - 36, H - 21], fill=(255, 255, 255, 50))
    d.rectangle([36, H - 22, 36 + (W - 72) * t / DUR, H - 21], fill=(255, 200, 140, 220))
    # title
    tt = t - 7.6
    if tt > 0:
        k = ease(tt / 1.6)
        title = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(title)
        tracked(td, (W / 2, H * 0.20), TITLE, F_TITLE, 40 + 30 * k, (255, 255, 255, int(255 * k)))
        rl = 300 * ease((tt - 0.5) / 1.2)
        if rl > 1:
            td.rectangle([W / 2 - rl, H * 0.20 + 160, W / 2 + rl, H * 0.20 + 161], fill=(255, 220, 180, 200))
        sk = ease((tt - 1.0) / 1.2)
        if sk > 0:
            tracked(td, (W / 2, H * 0.20 + 178), SUBTITLE, F_SUB, 4,
                    (255, 214, 160, int(235 * sk)))
        glowl = title.filter(ImageFilter.GaussianBlur(14))
        lay = Image.alpha_composite(lay, glowl)
        lay = Image.alpha_composite(lay, title)
    return np.asarray(lay, np.float32) / 255

# ---------- compositing ----------
def frame(t):
    def A(): return shot_stars(min(t / 3.7, 1))
    def B(): return shot_crystal((t - 3.3) / 3.6, t)
    def C(): return shot_ocean((t - 6.5) / 5.5, t)
    if t < 3.3: rgb = A()
    elif t < 3.7: k = ease((t - 3.3) / 0.4); rgb = A() * (1 - k) + B() * k
    elif t < 6.5: rgb = B()
    elif t < 6.9: k = ease((t - 6.5) / 0.4); rgb = B() * (1 - k) + C() * k
    else: rgb = C()
    rgb = 1 - np.exp(-np.clip(rgb, 0, None) * 1.25)  # filmic tonemap
    vig = 1 - 0.35 * (((XX - W / 2) / W) ** 2 + ((YY - H / 2) / H) ** 2)[..., None] * 2
    rgb = rgb * vig
    ov = overlay(t)
    rgb = rgb * (1 - ov[..., 3:]) + ov[..., :3] * ov[..., 3:]
    fade = ease(t / 0.5) * (1 - ease((t - 11.3) / 0.7))
    rgb = rgb * fade
    grain = rng.normal(0, 0.012, (H, W, 1)).astype(np.float32)
    return (np.clip(rgb + grain, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8)

def render_video(out, music):
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg not found on PATH - install it first (apt install ffmpeg / winget install ffmpeg).")
    if not Path(music).exists():
        sys.exit(f"{music} not found - run `python music.py` first.")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    # -g/-keyint_min = FPS -> one keyframe every second (seek-safe, avoids silent render failures)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", str(music), "-c:v", "libx264", "-preset", "medium",
                          "-crf", "21", "-g", str(FPS), "-keyint_min", str(FPS), "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
                         stdin=subprocess.PIPE)
    for i in range(NF):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 30 == 0:
            print(f"frame {i}/{NF}", flush=True)
    p.stdin.close()
    if p.wait() != 0:
        sys.exit(f"ffmpeg failed with exit code {p.returncode}")
    print("DONE", out)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("preview", "video"):
        sys.exit(__doc__)
    OUT_DIR.mkdir(exist_ok=True)
    if sys.argv[1] == "preview":
        for s in sys.argv[2:] or ["2", "5", "10.8"]:
            path = OUT_DIR / f"preview_{float(s):05.2f}.png"
            Image.fromarray(frame(float(s))).save(path)
            print("saved", path)
    else:
        render_video(sys.argv[2] if len(sys.argv) > 2 else OUT_DIR / "showreel.mp4",
                     sys.argv[3] if len(sys.argv) > 3 else OUT_DIR / "music.wav")
