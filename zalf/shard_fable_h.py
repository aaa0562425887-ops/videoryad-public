# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть H: G01, G06).
Запуск: shard_fable_h.py <код> <out.mp4>; один кадр: ZAL_FRAME=1.9 shard_fable_h.py G01 k.png

Числа сняты с плёнки покадрово (polosy/G01_vhod, G01_okna_setka, G01_pryamo_setka,
G06_vhod, G06_vozvrat, G06_svet_setka; яркость кадра считалась числом по 1/30 с):
  G01  17.0-17.6: камера почти стоит (жёлтый проём не растёт), весь кадр уходит вправо
       на ~1,3 % за 0,6 с → поворот влево ≈1,1°/с; горизонт на 78 % высоты → камера
       задрана вверх ≈7°. 21.4-21.6: ближнее окно 17 % → 15,5 % → 19,3 м → 18,4 м,
       ≈4 м/с на открытом прогоне, горизонт 57 % (≈2° вверх). Пол — мягкое зеркало окон,
       жёлтый проём на дальней стене в точке схода, потолок балками, десятки тросов.
  G06  вход в черноту: 252.80 (ярк. 170) → 253.33 (95) → 253.83 (56): крутая часть 400 мс,
       хвост ещё 500 мс, тьма = 33 % от света, зал остаётся серым, не чёрным.
       Возврат: 258.00-258.70 свечение растёт медленно (+5 ярк. за 700 мс), 258.73 прорыв,
       258.73-259.00 добор до полного за 300 мс → возврат ≈1,0 с против 0,6 с входа.
       Жёлтый проём 1,0×2,75 м на 10,2 м (251.0) → 6,4 м (255.0), камера доезжает
       ≈0,6 м/с и сдвигается вправо на 1,2 м; слова на проёме 253.40/.47/.60/.73/254.13.
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import *

FPS = 30
YEL = (236, 190, 48, 255)

def smooth(u):
    u = clamp01(u); return u * u * (3 - 2 * u)

# ----------------------------------------------------------------- камера с наклоном
class CamP(Cam):
    """та же камера, плюс наклон pitch (радианы, >0 — смотрит вверх, горизонт опускается)"""
    def __init__(s, x=0.0, y=1.55, z=0.0, yaw=0.0, pitch=0.0):
        Cam.__init__(s, x, y, z, yaw); s.pitch = pitch
    def proj(s, p):
        dx, dy, dz = p[0] - s.x, p[1] - s.y, p[2] - s.z
        if s.yaw:
            c, si = math.cos(-s.yaw), math.sin(-s.yaw)
            dx, dz = dx * c - dz * si, dx * si + dz * c
        if s.pitch:
            c, si = math.cos(s.pitch), math.sin(s.pitch)
            dy, dz = dy * c - dz * si, dy * si + dz * c
        if dz < 0.08: dz = 0.08
        k = F / dz
        return (W / 2 + dx * k, H / 2 - dy * k, dz)

# ----------------------------------------------------------------- детали зала
def lerp3(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))

_WALLTEX = {}
def wall_tex(bands):
    key = bands
    if key in _WALLTEX: return _WALLTEX[key]
    w, h = 1240, 500
    img = Image.new("RGBA", (w, h), (225, 227, 230, 255))
    if bands:   # свет из окон ложится на правую половину стены мягкими косыми полосами
        lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.polygon([(w * 0.45, 0), (w, 0), (w, h), (w * 0.70, h)], fill=(246, 247, 248, 255))
        for i in range(5):
            x0 = w * 0.50 + i * 150
            d.polygon([(x0, 0), (x0 + 26, 0), (x0 + 26 - 150, h), (x0 - 150, h)], fill=(212, 213, 215, 255))
        lay = lay.filter(ImageFilter.GaussianBlur(22))
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
        rng = np.random.default_rng(11)
        for i in range(6):
            x = float(rng.uniform(w * 0.3, w))
            d.line([(x, 0), (x - 50, h)], fill=(216, 217, 219, 255), width=1)
    _WALLTEX[key] = img
    return img

def far_wall(img, cam, z, dark=0.0, bands=False, slot=True):
    """дальняя стена зала во всю ширину; slot — жёлтая полоса-проём в точке схода"""
    tex = wall_tex(bands)
    if dark > 0:
        k = clamp01(dark)
        arr = np.asarray(tex, np.float32)
        arr[..., :3] = arr[..., :3] * (1 - 0.80 * k) + np.array([10, 9, 8], np.float32) * (0.80 * k)
        tex = Image.fromarray(arr.astype(np.uint8))
    c = [(-WALL, CEIL, z), (WALL, CEIL, z), (WALL, 0.0, z), (-WALL, 0.0, z)]
    paste_quad(img, tex, [cam.proj(p) for p in c])
    if slot:
        st = Image.new("RGBA", (40, 120), lerp3(YEL, (120, 92, 20), clamp01(dark)) + (255,))
        c = [(-0.42, 2.4, z - 0.01), (0.42, 2.4, z - 0.01), (0.42, 0.0, z - 0.01), (-0.42, 0.0, z - 0.01)]
        paste_quad(img, st, [cam.proj(p) for p in c])
        reflection(img, cam, c, st, strength=0.45)

def beams(img, cam, z0, z1, step=2.6):
    """потолочные балки: светлые полосы на плоскости потолка поперёк зала"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    z = math.floor(z0 / step) * step
    while z < z1:
        if z - cam.z > 1.2:
            p = [cam.proj((-WALL, CEIL, z)), cam.proj((WALL, CEIL, z)),
                 cam.proj((WALL, CEIL, z + 0.5)), cam.proj((-WALL, CEIL, z + 0.5))]
            d.polygon([(q[0], q[1]) for q in p], fill=(243, 244, 246, 255))
            a, b = cam.proj((-WALL, CEIL, z + 0.5)), cam.proj((WALL, CEIL, z + 0.5))
            d.line([(a[0], a[1]), (b[0], b[1])], fill=(224, 226, 230, 255), width=1)
        z += step
    img.alpha_composite(lay)

def floor_mirror(img, cam, zmax, strength=0.28):
    """пол как мягкое зеркало: окна отражаются вниз размытыми светлыми пятнами"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    z0 = math.floor((cam.z + 3) / 7.0) * 7.0
    for i in range(10):
        zz = z0 + i * 7.0
        if zz > zmax - 3.1: break
        for sx in (-1, 1):
            p = [cam.proj((sx * WALL, -1.15, zz)), cam.proj((sx * WALL, -1.15, zz + 3.1)),
                 cam.proj((sx * WALL, -2.7, zz + 3.1)), cam.proj((sx * WALL, -2.7, zz))]
            d.polygon([(q[0], q[1]) for q in p], fill=(255, 255, 255, int(255 * strength)))
    lay = lay.filter(ImageFilter.GaussianBlur(26))
    img.alpha_composite(lay)

def extra_ropes(img, cam, n=40, seed=3, zspan=60.0, zmax=None):
    """десятки тонких тросов на разной высоте — без них кадр пустой"""
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(img, "RGBA")
    base = math.floor(cam.z / 3.0) * 3.0
    for i in range(n):
        zz = base + float(rng.uniform(1.5, zspan))
        if zmax is not None and zz > zmax - 0.5: continue
        xx = float(rng.uniform(-5.4, 5.4)); yy = float(rng.uniform(0.6, 3.2))
        if zz - cam.z < 1.2: continue
        a = cam.proj((xx, CEIL, zz)); b = cam.proj((xx, yy, zz))
        far = clamp01((zz - cam.z) / 40.0)
        col = lerp3((132, 134, 138), (190, 192, 196), far)
        d.line([(a[0], a[1]), (b[0], b[1])], fill=col + (235,), width=1 if far > 0.3 else 2)

# ----------------------------------------------------------------- G01
def g01_cam(t):
    """камера ни мгновения не стоит: разгон 0,4 → 3,6 м/с, поворот от окон к оси зала,
    задранный на 7° взгляд выравнивается, лёгкое покачивание"""
    def v(tt): return 0.4 + 3.2 * smooth(seg(tt, 0.6, 3.2))
    n = max(1, int(t * 60)); dt = t / n if n else 0
    z = sum(v(i * dt) for i in range(n)) * dt
    yaw = math.radians(12.0) * (1 - smooth(seg(t, 0.0, 3.0))) + math.radians(0.5) * math.sin(1.3 * t)
    pitch = math.radians(7.0) * (1 - smooth(seg(t, 0.4, 3.2))) + math.radians(0.25) * math.sin(0.9 * t + 1)
    x = -0.35 + 0.55 * smooth(seg(t, 0.0, 4.0)) + 0.06 * math.sin(1.1 * t)
    y = 1.55 + 0.03 * math.sin(1.7 * t)
    return CamP(x, y, z, yaw, pitch), v(t)

def g01(t):
    """белый зал как единственная площадка: глянцевый пол, окна, свет полосами, тросы"""
    cam, v = g01_cam(t)
    ZW = 60.0
    img = room(cam)
    floor_mirror(img, cam, ZW)
    far_wall(img, cam, ZW, slot=True)
    beams(img, cam, cam.z + 1.0, min(ZW, cam.z + 34.0))
    extra_ropes(img, cam, n=26, seed=3, zmax=ZW)
    return img

# ----------------------------------------------------------------- G06
PANEL_W, PANEL_H, PANEL_Z = 1.0, 2.75, 10.1
WALL_Z = 10.2
WORDS = [("THAT", 1.80), ("IT", 1.87), ("WAS", 2.00), ("ABOUT", 2.13), ("TO.", 2.53)]
WORDS_OUT = 3.90

def panel_tex(t, lit, dark_k):
    """жёлтая полоса-проём: при свете плоская, во тьме светится снизу вверх; слова по одному"""
    w, h = 400, int(400 * PANEL_H / PANEL_W)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / h
        if lit:
            col = (238, 192, 52)
        else:
            col = lerp3((150, 108, 26), (236, 184, 44), k ** 1.3)
        d.line([(0, y), (w, y)], fill=col + (255,))
    d.rectangle([0, 0, w - 1, h - 1], outline=(96, 72, 18, 255), width=3)
    if not lit and t < WORDS_OUT:
        f = font("ArialBlack.ttf", 84)
        rows = [["THAT", "IT"], ["WAS"], ["ABOUT"], ["TO."]]
        y = int(h * 0.07)
        for row in rows:
            widths = [d.textlength(wd, font=f) for wd in row]
            x = (w - sum(widths) - 18 * (len(row) - 1)) / 2
            for wd, ww in zip(row, widths):
                t0 = dict(WORDS)[wd]
                if t >= t0:
                    u = seg(t, t0, t0 + 0.10)
                    s = 1.22 - 0.22 * out_cubic(u)
                    tf = font("ArialBlack.ttf", int(84 * s))
                    tw = d.textlength(wd, font=tf)
                    d.text((x + ww / 2 - tw / 2, y - 84 * (s - 1) / 2), wd, font=tf, fill=(26, 20, 12, 255))
                x += ww + 18
            y += 110
    return img

def quote_tex():
    w, h = 980, 470
    img = Image.new("RGBA", (w, h), (250, 250, 249, 255))
    d = ImageDraw.Draw(img)
    d.text((40, 30), "FROM THE ESSAY · FEB 9, 2026", font=font("Oswald-Bold.ttf", 24), fill=(90, 90, 92, 255))
    return img

def quote_lines(img, t):
    img = img.copy()
    d = ImageDraw.Draw(img)
    f = font("Oswald-Bold.ttf", 104)
    lines = ["It just hasn't", "knocked on your door", "yet. It's about to."]
    y = 84
    for i, ln in enumerate(lines):
        if i == 1 and t >= 1.0:          # жёлтый маркер на «knocked on your door», как на плёнке 252.6
            tw = d.textlength(ln, font=f)
            d.rectangle([34, y + 18, 48 + tw, y + 118], fill=(246, 206, 60, 255))
        d.text((40, y), ln, font=f, fill=(28, 28, 30, 255))
        y += 118
    return img

_QT = {}
def g06_quote(img, cam, t):
    """лист с цитатой слева от проёма: висит на двух тросах, на 1,75 с срывается вверх"""
    if t > 2.1: return
    if "base" not in _QT: _QT["base"] = quote_tex()
    tex = quote_lines(_QT["base"], t)
    w, h = 3.6, 3.6 * tex.size[1] / tex.size[0]
    dy = 0.0
    if t > 1.75:
        u = seg(t, 1.75, 1.95); dy = 4.5 * u * u
    c = quad((-3.2, 1.95 + dy, WALL_Z - 0.55), w, h)
    if dy < 0.1:
        sh = Image.new("RGBA", tex.size, (60, 60, 64, 255)); sh.putalpha(tex.split()[3].point(lambda v: int(v * 0.30)))
        cs = quad((-3.2 + 0.22, 1.95 - 0.18, WALL_Z - 0.02), w, h)
        paste_quad(img, sh.filter(ImageFilter.GaussianBlur(8)), [cam.proj(p) for p in cs])
    for fx in (0.15, 0.85):
        top = (c[0][0] + (c[1][0] - c[0][0]) * fx, c[0][1], c[0][2])
        wire(img, cam, top, color=(110, 112, 116, 220), width=2)
    paste_quad(img, tex, [cam.proj(p) for p in c])
    if dy < 0.1: reflection(img, cam, c, tex, strength=0.07)

def g06_panel(img, cam, t, lit, dark_k, opacity=1.0):
    tex = panel_tex(t, lit, dark_k)
    c = quad((0.0, PANEL_H / 2, PANEL_Z), PANEL_W, PANEL_H)
    for fx in (0.12, 0.38, 0.62, 0.88):
        top = (c[0][0] + (c[1][0] - c[0][0]) * fx, c[0][1], c[0][2])
        wire(img, cam, top, color=(96, 98, 102, 220) if lit else (70, 64, 54, 220), width=2)
    if opacity < 1.0:
        a = tex.split()[3].point(lambda v: int(v * opacity)); tex = tex.copy(); tex.putalpha(a)
    extrude(img, cam, c, tex, depth=0.10, steps=3, shade=(120, 96, 30) if lit else (70, 52, 14))
    reflection(img, cam, c, tex, strength=0.07 if lit else 0.34)
    return c

def warm_glow(img, cam, strength, radius=0.55, color=(255, 150, 60)):
    """тёплое свечение возврата: аддитивное пятно от проёма, растёт медленно"""
    if strength <= 0.005: return img
    px, py, _ = cam.proj((0.0, PANEL_H * 0.12, PANEL_Z))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - px) / (W * radius)) ** 2 + ((yy - py) / (W * radius * 0.8)) ** 2)
    m = np.clip(1 - r, 0, 1) ** 1.8 * strength
    arr = np.asarray(img.convert("RGB"), np.float32)
    arr = arr + m[..., None] * np.array(color, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

def g06_dark(t):
    """доля тьмы 0..1: вход 1,2-2,2 с (крутые 0,5 с + хвост), возврат 4,0-5,05 с
    (0,7 с медленного подъёма, затем прорыв за 0,35 с)"""
    d_in = 0.62 * smooth(seg(t, 1.2, 1.7)) + 0.38 * smooth(seg(t, 1.55, 2.2))
    slow = 0.08 * smooth(seg(t, 4.0, 4.7))
    fast = out_cubic(seg(t, 4.7, 5.05))       # прорыв: 81 % за первые 150 мс, добор до 5,05
    return clamp01(d_in - slow) * (1 - fast)

def g06(t):
    """гашение зала: свет уходит, остаётся жёлтый проём и угли; свет возвращается медленнее"""
    # плёнка: 10,2 м (251.0) → 8,8 м (253.6) → 6,4 м (255.0), потом стоит; вправо на 1,2 м
    z = 1.4 * smooth(seg(t, 0.0, 2.6)) + 2.4 * smooth(seg(t, 2.5, 4.0))
    u = smooth(seg(t, 0.0, 4.0))
    cam = Cam(-1.2 + 1.2 * u, 1.70 + 0.02 * math.sin(1.5 * t), z, 0.0)
    dk = g06_dark(t)
    img = room(cam)
    far_wall(img, cam, WALL_Z, dark=0.0, bands=True, slot=False)
    extra_ropes(img, cam, n=18, seed=5, zspan=9.0, zmax=WALL_Z)
    g06_quote(img, cam, t)
    g06_panel(img, cam, t, lit=True, dark_k=0.0)
    if dk > 0.001:
        D = 0.82 * dk                       # тьма = 33 % света: зал остаётся серым
        img.alpha_composite(Image.new("RGBA", (W, H), (8, 7, 6, int(235 * D))))
        # проём светится сам: поверх тьмы его светящаяся версия
        gk = smooth(seg(dk, 0.45, 1.0))              # проём светится сам лишь когда тьма глубокая
        c = g06_panel(img, cam, t, lit=False, dark_k=dk, opacity=gk)
        # полоска подсветки у ног и пятно на полу
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        st = Image.new("RGBA", (80, 12), (255, 246, 225, 255))
        q = [(-PANEL_W / 2 - 0.05, 0.05, PANEL_Z - 0.14), (PANEL_W / 2 + 0.05, 0.03, PANEL_Z - 0.14),
             (PANEL_W / 2 + 0.05, 0.0, PANEL_Z - 0.14), (-PANEL_W / 2 - 0.05, 0.0, PANEL_Z - 0.14)]
        paste_quad(lay, st, [cam.proj(p) for p in q], gk)
        pool = Image.new("RGBA", (200, 120), (0, 0, 0, 0))
        ImageDraw.Draw(pool).ellipse([10, 10, 190, 110], fill=(255, 232, 180, int(215 * gk)))
        pool = pool.filter(ImageFilter.GaussianBlur(14))
        q = [(-1.6, 0.0, PANEL_Z + 0.2), (1.6, 0.0, PANEL_Z + 0.2), (1.6, 0.0, PANEL_Z - 2.2), (-1.6, 0.0, PANEL_Z - 2.2)]
        paste_quad(lay, pool, [cam.proj(p) for p in q])
        img.alpha_composite(lay)
        # угли у подножия — единственный свет кроме проёма
        pts = cluster(-0.7, 0.08, PANEL_Z - 0.5, 0.20, n=2, seed=2) + cluster(0.75, 0.07, PANEL_Z - 0.4, 0.18, n=2, seed=4) \
            + cluster(-1.7, 0.06, PANEL_Z - 1.8, 0.15, n=2, seed=6) + cluster(1.8, 0.06, PANEL_Z - 1.3, 0.14, n=1, seed=7)
        if gk > 0.02: img = embers(img, cam, pts, t, glow=0.85 * gk)
    # возврат: тёплое свечение растёт медленно (4,0-4,7), прорыв 4,7-5,05, свечение гаснет вместе с ним
    sw = smooth(seg(t, 4.0, 4.7)) * 0.75 * (1 - smooth(seg(t, 4.7, 5.1)))
    if sw > 0:
        img = warm_glow(img, cam, sw, radius=0.35 + 0.6 * smooth(seg(t, 4.6, 5.2)))
    return img

SCENES = {"G01": (g01, 5.0), "G06": (g06, 6.0)}

def render(code, out):
    fn, dur = SCENES[code]
    n = int(dur * FPS)
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        exe = "ffmpeg"
    p = subprocess.Popen([exe, "-y", "-nostdin", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{Z.W}x{Z.H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(fn(i / FPS).convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    print("готово:", out, n, "кадров")

if __name__ == "__main__":
    code = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else f"{code}.mp4"
    if os.environ.get("ZAL_FRAME"):
        t = float(os.environ["ZAL_FRAME"])
        SCENES[code][0](t).convert("RGB").save(out)
        print("кадр", t, "->", out)
    else:
        render(code, out)
