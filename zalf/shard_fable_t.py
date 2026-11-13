# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть T: G41 финальный логотип объёмом, G42 дверь света).
Один кадр: ZAL_FRAME=1.9 python3 shard_fable.py G41 /tmp/k.png

Числа сняты с плёнки покадрово (polosy/G41_vhod, G41_kadr, G41_dalshe, G41_ugol, сетки G41/G41b;
polosy/G42_vhod, G42_kadr, G42_dalshe, G42_konec, сетка G42):

  G41  277.233-277.367 предыдущая сцена уезжает ВВЕРХ с вертикальным смазом за 4 кадра, зал пустой;
       277.433 «MATT SHUMER» первым входит сверху, 277.467-277.700 весь блок (логотип + подпись)
       ОПУСКАЕТСЯ сверху за 8 кадров (~270 мс): низ букв по кадру 0.11 → 0.125 → 0.18 → 0.26 →
       0.33 → 0.38 → 0.40 → 0.41 → 0.42 (разгон-торможение, без перелёта);
       покой: буквы x 0.11-0.955, y 0.26-0.42 (капитель 16% кадра), «MATT SHUMER» x 0.41-0.60,
       y 0.47-0.50; висит на тросах, не стоит на полу;
       277.767 уголёк входит справа-сверху (0.93, 0.02) с хвостом-кометой, 278.000 садится в
       ТОЧКУ между BIG и AI (0.78, 0.38) — 7 кадров, 233 мс; 278.033-278.133 вспышка-ореол
       вдвое больше, к 278.3 ровный ореол ~12% ширины кадра; буквы BIG и AI рядом подсвечены тёплым;
       281.5 → 283.0 свет гаснет за ~1.5 с: стены и пол в тёмно-серый, окна остаются тусклыми,
       под углём на полу широкое тёплое пятно-отражение (y 0.75-1.0), подпись тонет в темноте;
       камера всё время едет: медленный наезд, буквы 0.845 → 0.81 ширины кадра к 281.
       В клипе 4.5 с плёнка 277.2-283.5 сжата: вход 0-0.13, спуск 0.20-0.50, уголь 0.567-0.80,
       вспышка до 1.1, затемнение 2.3-3.6, конец в темноте с углём.

  G42  249.633 кадр: светлая стена с косыми пятнами окон, слева висячий лист «FROM THE ESSAY · FEB 9, 2026 /
       It just hasn't / knocked on your door / yet. It's about to.» x 0.15-0.47, y 0.10-0.45;
       справа жёлтая ДВЕРЬ x 0.57-0.68, y 0.28-0.73 (высота 0.45 кадра), линия пола 0.73;
       камера наезжает: дверь 0.45 → 0.56 (253.2) → 0.64 (254.4) → 0.76 (256.9) → 0.82 (258.0);
       252.567-252.633 маркер по «knocked on your door» — три слова за три кадра;
       252.8-253.2 зал гаснет за ~0.35 с, дверь остаётся цветной, под ней на полу — светлая полоса
       (свет из-под двери) и мягкое свечение;
       253.400-253.500 лист улетает ВВЕРХ за 3 кадра со смазом; камера за 0.9 с центрует дверь
       (0.645 → 0.50);
       253.4 «THAT» · 253.467 «IT» · 253.6 «WAS» · 253.8 «ABOUT» · 254.3 «TO.» — слова на двери;
       255.4-255.5 текст улетает вверх за 2 кадра; (256.0-257.0 «IT'S NOT KNOCKING ANYMORE.» — в клип не вошло);
       258.2 дверь получает филёнку и косяк; 258.3-258.8 РАСКРЫВАЕТСЯ за 15 кадров (0.5 с), петли
       СЛЕВА, створка уходит от нас: угол 25° (258.4) · 45° (258.5) · 58° (258.6) · 73° (258.7) · 90°;
       проём — чистый белый свет, 258.6 щель, 258.7 полкадра, 258.8 кадр почти весь белый с оранжевым
       углём внизу проёма и стеной, залитой оранжевым; 258.9 — уже следующая светлая сцена.
       Засвет гасит зал за 6 кадров (258.6-258.8) и в один кадр превращается в белый зал.
       В клипе 4.5 с: лист+дверь 0-1.9 (маркер 1.0, темнеет 1.5-1.8), лист улетает 1.9, слова
       2.0-2.6, улетают 3.0, косяк 3.05, раскрытие 3.2-3.7, рывок 3.5-3.9, бело 3.9, белый зал 4.2.
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import *

FPS = 30
INK = (28, 26, 25, 255)
INK_SIDE = (54, 50, 48)

# ----------------------------------------------------------------- общие вещи

def smooth(u):
    u = clamp01(u); return u * u * (3 - 2 * u)

def smear(img, dx, dy, n=7):
    """смаз движения: среднее сдвинутых копий (края тянутся, без заворота)"""
    if abs(dx) < 1 and abs(dy) < 1: return img
    arr = np.asarray(img.convert("RGB"), np.float32)
    p = int(max(abs(dx), abs(dy))) + 1
    pad = np.pad(arr, ((p, p), (p, p), (0, 0)), mode="edge")
    acc = np.zeros_like(arr)
    for i in range(n):
        f = i / (n - 1) - 0.5
        sx, sy = int(round(dx * f)), int(round(dy * f))
        acc += pad[p + sy:p + sy + H, p + sx:p + sx + W]
    return Image.fromarray((acc / n).astype(np.uint8)).convert("RGBA")

def rush_blur(img, k):
    """смаз пролёта: пара увеличенных копий поверх, k — сила 0..1"""
    if k <= 0.01: return img
    base = img.convert("RGB")
    for z in (1.012, 1.03):
        sw, sh = int(W * z), int(H * z)
        big = base.resize((sw, sh), Image.BILINEAR).crop(((sw - W) // 2, (sh - H) // 2,
                                                            (sw - W) // 2 + W, (sh - H) // 2 + H))
        base = Image.blend(base, big, 0.32 * k)
    return base.convert("RGBA")

def add_glow(img, cx, cy, rx, ry, color, strength, blur=40):
    """аддитивное тёплое/белое пятно: эллипс в 1/4 размера, размыт, растянут на кадр"""
    if strength <= 0.003: return img
    sw, sh = W // 4, H // 4
    m = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(m).ellipse([cx / 4 - rx / 4, cy / 4 - ry / 4, cx / 4 + rx / 4, cy / 4 + ry / 4], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur / 4)).resize((W, H), Image.BILINEAR)
    mask = np.asarray(m, np.float32)[..., None] / 255.0 * strength
    arr = np.asarray(img.convert("RGB"), np.float32)
    arr = arr + mask * np.array(color, np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

def to_white(img, w, color=(255, 250, 240)):
    if w <= 0.002: return img
    arr = np.asarray(img.convert("RGB"), np.float32)
    arr = arr * (1 - w) + np.array(color, np.float32) * w
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

def mul_tex(tex, k):
    """затемнить текстуру множителем k (альфа не трогаем)"""
    r, g, b, a = tex.split()
    return Image.merge("RGBA", (r.point(lambda v: int(v * k)), g.point(lambda v: int(v * k)),
                                b.point(lambda v: int(v * k)), a))

def cond_tex(tex, cond):
    return tex.resize((max(4, int(tex.size[0] * cond)), tex.size[1]), Image.LANCZOS)

def face_quad(cx, cy, cz, w, h, yaw=0.0, roll=0.0):
    return quad((cx, cy, cz), w, h, yaw, roll)

def visible(cam, corners, margin=0.3):
    return min(c[2] for c in corners) - cam.z > margin

def cast_shadow(canvas, cam, corners, tex, light=(0.55, -1.0, 0.35), strength=0.24, blur=16):
    """настоящая тень на полу: углы объекта сносятся по направлению света на плоскость пола,
    тень получается скошенной копией контура (свет из окон слева-сверху-спереди)"""
    pts = []
    for (x, y, z) in corners:
        k = y / -light[1]
        pts.append((x + light[0] * k, 0.012, z + light[2] * k))
    if not visible(cam, pts): return
    a = tex.split()[3].point(lambda v: int(v * strength))
    dark = Image.new("RGBA", tex.size, (36, 34, 32, 255)); dark.putalpha(a)
    dark = dark.filter(ImageFilter.GaussianBlur(blur))
    paste_quad(canvas, dark, [cam.proj(p) for p in pts])

def hang_wires(canvas, cam, corners, fracs, color=(104, 106, 110, 230)):
    tl, tr = corners[0], corners[1]
    for f in fracs:
        p = (tl[0] + (tr[0] - tl[0]) * f, tl[1], tl[2] + (tr[2] - tl[2]) * f)
        if p[2] - cam.z < 0.4: continue
        wire(canvas, cam, p, color=color, width=2)

def loose_wires(canvas, cam, zmin, zmax, n=16, seed=11, color=(150, 152, 156, 255)):
    """десятки тонких тросов, висящих ни на чём — без них кадр пустой"""
    if zmax - zmin < 0.5: return
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(canvas, "RGBA")
    for i in range(n):
        xx = float(rng.uniform(-4.2, 4.2)); zz = float(rng.uniform(zmin, zmax)); yy = float(rng.uniform(0.9, 2.9))
        if zz - cam.z < 1.2: continue
        a = cam.proj((xx, CEIL, zz)); b = cam.proj((xx, yy, zz))
        d.line([(a[0], a[1]), (b[0], b[1])], fill=color, width=1)

# ================================================================= G41

_G41 = {}
def _g41_tex():
    """логотип: тяжёлый узкий гротеск образца = Arial Black, сжатый до 0.60; подпись — тот же, 0.80.
    запоминаем, где в текстуре стоит точка между BIG и AI — туда сядет уголь"""
    if _G41: return _G41
    fs, cond, pad = 260, 0.60, 6
    tex = text_tex(["SOMETHINGBIG.AI"], fsize=fs, cond=1.0, color=INK, pad=pad)
    f = font("ArialBlack.ttf", fs)
    d0 = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    s = d0.textbbox((0, 0), "SOMETHINGBIG.AI", font=f)
    a = d0.textbbox((0, 0), "SOMETHINGBIG", font=f)
    b = d0.textbbox((0, 0), "SOMETHINGBIG.", font=f)
    bb = tex.getbbox()
    dot_x = (pad - s[0] + (a[2] + b[2]) / 2 - bb[0]) * cond
    dot_y = (pad - s[1] + s[3] - bb[1]) - fs * 0.075
    tex = cond_tex(tex.crop(bb), cond)
    sub = text_tex(["MATT SHUMER"], fsize=64, cond=1.0, color=INK, pad=4)
    sub = cond_tex(sub.crop(sub.getbbox()), 0.80)
    _G41.update(logo=tex, dot=(dot_x, dot_y), sub=sub)
    return _G41

def g41(t):
    """финальный логотип: блок опускается сверху на тросах, уголь прилетает в точку,
    свет гаснет — остаётся уголь и его отражение в полу"""
    # вход: предыдущая сцена ушла вверх — камера садится сверху за 4 кадра с вертикальным смазом
    u_in = seg(t, 0.0, 0.13)
    cam = Cam(-0.04 * t, 1.55 + 1.9 * (1 - u_in) ** 2, 0.08 * t, 0.0)
    # свет гаснет: плёнка 281.5-283.0, у нас 2.3-3.6
    dk = 0.75 * smooth(seg(t, 2.3, 3.6))
    img = room(cam, dark=dk)
    T = _g41_tex()
    logo, (dot_x, dot_y), sub = T["logo"], T["dot"], T["sub"]
    # покой: буквы на 9 м, капитель 0.79 м, центр букв 2.34 м, центр по x +0.26 м
    D = 9.0
    cap = 0.79; sm = cap / logo.size[1]; lw = logo.size[0] * sm
    # спуск: 8 кадров, разгон-торможение, сверху на полкадра (2.47 м на этой дальности)
    u_dr = smooth(seg(t, 0.20, 0.50))
    dy = (1 - u_dr) * 2.47
    if t < 0.20 - 1e-6: dy = 2.47 + 0.8
    yc = 2.34 + dy
    c = face_quad(0.26, yc, D, lw, cap)
    sw_ = 1.70; ssm = sw_ / sub.size[0]; sh_ = sub.size[1] * ssm
    cs = face_quad(0.26, 1.62 + dy, D, sw_, sh_)
    # тень и отражение — под блоком; отражение в полу (на этой дальности в кадр входит только краем)
    cast_shadow(img, cam, c, logo, strength=0.24 * (1 - 0.6 * dk))
    cast_shadow(img, cam, cs, sub, strength=0.18 * (1 - 0.6 * dk), blur=8)
    reflection(img, cam, c, logo, strength=0.12)
    # тросы — к верху букв
    hang_wires(img, cam, c, (0.06, 0.24, 0.41, 0.58, 0.73, 0.90),
               color=(104, 106, 110, int(230 * (1 - 0.5 * dk))))
    # объём: копии в глубину от дальней к ближней
    extrude(img, cam, c, logo, depth=0.26, steps=7, shade=INK_SIDE)
    extrude(img, cam, cs, sub, depth=0.05, steps=2, shade=INK_SIDE)
    # --- уголь: вылетает справа-сверху за 2 кадра после посадки блока, 7 кадров полёта
    dot_w = (c[0][0] + dot_x * sm, c[0][1] - dot_y * sm, D - 0.12)
    t_e0, t_e1 = 0.567, 0.80
    pts = []
    if t >= t_e0:
        u = seg(t, t_e0, t_e1)
        u = 0.5 * u + 0.5 * out_cubic(u)
        start = (3.15, 3.55, 7.4)
        px_ = start[0] + (dot_w[0] - start[0]) * u
        py_ = start[1] + (dot_w[1] - start[1]) * u
        pz_ = start[2] + (dot_w[2] - start[2]) * u
        burst = 1.0 + 1.3 * math.sin(math.pi * seg(t, t_e1, t_e1 + 0.30)) if t >= t_e1 else 1.0
        s0 = 0.50 * burst
        pts.append((px_, py_, pz_, s0))
        if u < 1.0:                      # хвост кометы
            for k in range(1, 6):
                uu = max(0.0, u - k * 0.045)
                pts.append((start[0] + (dot_w[0] - start[0]) * uu, start[1] + (dot_w[1] - start[1]) * uu,
                            start[2] + (dot_w[2] - start[2]) * uu, s0 * (0.55 - k * 0.08)))
        img = embers(img, cam, pts, t, glow=0.9 + 0.5 * dk)
        # тёплое пятно-отражение угля в полу: в светлом зале едва, в тёмном — главное пятно света
        foot = cam.proj((dot_w[0], 0.0, dot_w[2]))
        warm = (0.10 + 0.62 * dk / 0.75) * (burst if t >= t_e1 else 0.6)
        img = add_glow(img, foot[0], foot[1] + H * 0.12, W * 0.16, H * 0.30, (255, 150, 48), warm, blur=60)
    if u_in < 1.0:
        img = smear(img, 0, 90 * (1 - u_in) + 8)
    return img

# ================================================================= G42

_G42 = {}
def _wall_tex():
    """стена: светлая штукатурка, косые пятна света из окон слева-сверху, тени переплётов"""
    if "wall" in _G42: return _G42["wall"]
    w, h = 2480, 1000                                  # 200 px/м: 12.4 × 5 м
    rng = np.random.default_rng(42)
    base = np.full((h, w), 221.0, np.float32)
    nz = rng.normal(0, 3.2, (h // 4, w // 4)).astype(np.float32)
    base += np.kron(nz, np.ones((4, 4), np.float32))
    base[::14, :] -= 4.0                               # ряды кладки, еле видны
    lay = Image.new("L", (w, h), 0); d = ImageDraw.Draw(lay)
    for x0 in (-500, 700, 1900):
        d.polygon([(x0, 0), (x0 + 620, 0), (x0 + 620 + 850, h), (x0 + 850, h)], fill=255)
    lay = lay.filter(ImageFilter.GaussianBlur(28))
    band = np.asarray(lay, np.float32) / 255.0
    ml = Image.new("L", (w, h), 0); dm = ImageDraw.Draw(ml)
    for x0 in range(-900, w, 130):
        dm.line([(x0, 0), (x0 + 850, h)], fill=255, width=7)
    for y0 in range(-600, h + 600, 230):
        dm.line([(0, y0), (w, y0 + 420)], fill=255, width=6)
    ml = ml.filter(ImageFilter.GaussianBlur(3))
    mul = np.asarray(ml, np.float32) / 255.0
    arr = base + 24 * band - 14 * (1 - band) - 22 * mul * band
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.merge("RGBA", (Image.fromarray(arr), Image.fromarray(arr),
                               Image.fromarray(np.clip(arr.astype(np.int16) - 4, 0, 255).astype(np.uint8)),
                               Image.new("L", (w, h), 255)))
    _G42["wall"] = img
    return img

def _sheet_tex(hl_n):
    """висячий лист с цитатой; hl_n — сколько слов «knocked on your door» уже под маркером"""
    key = ("sheet", hl_n)
    if key in _G42: return _G42[key]
    w, h = 1800, 1100
    img = Image.new("RGBA", (w, h), (247, 245, 240, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(214, 212, 206, 255), width=3)
    fh = font("Oswald-Bold.ttf", 44)
    x = 90
    for ch in "FROM THE ESSAY · FEB 9, 2026":
        d.text((x, 92), ch, font=fh, fill=(70, 68, 64, 255)); x += d.textlength(ch, font=fh) + 7
    fb = font("Arimo-Bold.ttf", 128)
    lines = ["It just hasn't", "knocked on your door", "yet. It's about to."]
    y = 215
    for i, ln in enumerate(lines):
        if i == 1 and hl_n > 0:
            ws = ln.split(" "); x = 90
            for j, wd in enumerate(ws):
                tw = d.textlength(wd, font=fb)
                if j < hl_n:
                    d.rectangle([x - 8, y + 22, x + tw + 8, y + 140], fill=(255, 212, 0, 255))
                x += tw + d.textlength(" ", font=fb)
        d.text((90, y), ln, font=fb, fill=(32, 30, 28, 255))
        y += 165
    _G42[key] = img
    return img

def _door_tex(k_dark, panel):
    """створка 0.9 × 2.0 м, 500 px/м. k_dark — насколько погас зал (дверь темнеет в охру, низ светится),
    panel — филёнка и косяк (0..1)"""
    key = ("door", round(k_dark, 2), round(panel, 2))
    if key in _G42: return _G42[key]
    w, h = 450, 1000
    arr = np.zeros((h, w, 3), np.float32)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    col = np.array([239, 198, 58], np.float32) * (1 - 0.30 * k_dark) + np.array([12, 4, 0], np.float32) * k_dark
    arr[:] = col
    arr *= (1.0 - 0.08 * yy)                                   # чуть темнее книзу
    leak = np.clip((yy - 0.92) / 0.08, 0, 1) ** 1.6 * k_dark   # свет из-под двери
    arr += leak * np.array([70, 70, 110], np.float32)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, h - 8, w, h], fill=(40, 32, 12, 255))       # порог
    if panel > 0:
        lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        a = int(255 * panel)
        dl.rectangle([32, 40, w - 32, h - 60], outline=(96, 72, 14, a), width=4)
        dl.rectangle([48, 56, w - 48, h - 76], outline=(255, 232, 150, int(a * 0.5)), width=2)
        dl.rectangle([0, 0, w - 1, h - 1], outline=(70, 52, 10, a), width=6)
        img.alpha_composite(lay)
    _G42[key] = img
    return img

def _door_words():
    if "words" in _G42: return _G42["words"]
    tw, th, tiles = word_tiles(["THAT IT", "WAS", "ABOUT", "TO."], fsize=150, color=INK, line_gap=6, pad=10)
    out = []
    for tile, cx, cy in tiles:
        bb = tile.getbbox()
        if bb is None: continue
        cr = cond_tex(tile.crop(bb), 0.66)
        out.append((cr, (cx - tile.size[0] / 2 + (bb[0] + bb[2]) / 2) * 0.66, cy))
    _G42["words"] = (tw * 0.66, th, out)
    return _G42["words"]

def g42(t):
    """дверь света: жёлтый проём на стене, зал гаснет, слова на двери, створка раскрывается —
    белый свет из проёма гасит зал, камера входит в него и выходит в белый зал"""
    ZW = 8.0                                              # стена
    DX, DW, DH = 1.13, 0.9, 2.0                           # дверь: центр по x, ширина, высота
    # --- камера
    d = 8.0 - 1.4 * smooth(seg(t, 0.0, 1.9))              # наезд 8 → 6.6
    d -= 2.0 * seg(t, 1.9, 3.2)                           # → 4.6 к началу раскрытия
    d -= 1.0 * seg(t, 3.2, 3.7)                           # → 3.6 пока створка идёт
    ur = seg(t, 3.55, 3.92)                               # рывок в проём
    d -= 3.4 * ur * ur
    cy = 1.05 + 0.20 * smooth(seg(t, 0.0, 1.9)) - 0.05 * seg(t, 2.0, 2.9)
    cx = DX * smooth(seg(t, 2.0, 2.9))                    # центруем дверь за 0.9 с после ухода листа
    # белый зал после засвета
    w_out = seg(t, 3.74, 3.92) ** 1.4
    if t >= 3.92:
        cam2 = Cam(0.0, 1.55, 0.7 * (t - 3.92), 0.0)
        img = room(cam2)
        back = 1.0 - smooth(seg(t, 3.92, 4.25))
        img = add_glow(img, W * 0.5, H * 0.72, W * 0.22, H * 0.24, (255, 140, 40), 0.55 * back, blur=80)
        return to_white(img, back)
    cam = Cam(cx, cy, ZW - d, 0.0)
    kd = smooth(seg(t, 1.5, 1.8))                         # зал гаснет за 0.3 с
    img = room(cam, windows=False, shafts=(kd < 0.5), ropes=False, dark=0.78 * kd)
    # --- стена
    wall = _wall_tex()
    if kd > 0: wall = mul_tex(wall, 1 - 0.74 * kd)
    wq = [(-WALL, CEIL, ZW), (WALL, CEIL, ZW), (WALL, 0.0, ZW), (-WALL, 0.0, ZW)]
    paste_quad(img, wall, [cam.proj(p) for p in wq])
    loose_wires(img, cam, cam.z + 2.0, ZW - 0.3, n=18,
                color=(150 - int(90 * kd), 152 - int(90 * kd), 156 - int(90 * kd), 255))
    # --- дверь: проём света и створка
    a_open = math.radians(90.0) * (1 - (1 - seg(t, 3.2, 3.7)) ** 1.3)
    xl = DX - DW / 2
    z0 = ZW - 0.02
    # косяк появляется вместе с филёнкой
    panel = seg(t, 3.05, 3.15)
    if panel > 0:
        jamb = Image.new("RGBA", (64, 128), (54, 46, 30, int(255 * panel)))
        jq = [(xl - 0.06, DH + 0.06, ZW - 0.01), (xl + DW + 0.06, DH + 0.06, ZW - 0.01),
              (xl + DW + 0.06, 0.0, ZW - 0.01), (xl - 0.06, 0.0, ZW - 0.01)]
        paste_quad(img, jamb, [cam.proj(p) for p in jq])
    # проём — чистый свет; виден только когда створка пошла
    if a_open > 0:
        light = Image.new("RGBA", (64, 128), (255, 250, 232, 255))
        oq = [(xl, DH, ZW), (xl + DW, DH, ZW), (xl + DW, 0.0, ZW), (xl, 0.0, ZW)]
        paste_quad(img, light, [cam.proj(p) for p in oq])
    # створка: петли слева, уходит от нас
    door = _door_tex(kd, panel)
    if a_open > 0: door = mul_tex(door, 1 - 0.55 * math.sin(a_open))
    xf, zf = xl + DW * math.cos(a_open), z0 + DW * math.sin(a_open)
    dq = [(xl, DH, z0), (xf, DH, zf), (xf, 0.0, zf), (xl, 0.0, z0)]
    if a_open < math.radians(89.0):
        paste_quad(img, door, [cam.proj(p) for p in dq])
    # свет из-под двери на полу, пока зал тёмный и створка закрыта
    if kd > 0.02 and a_open < 0.3:
        ga = (np.linspace(230, 0, 128, dtype=np.float32) * kd).astype(np.uint8)
        g = Image.merge("RGBA", (Image.new("L", (64, 128), 255), Image.new("L", (64, 128), 246),
                                 Image.new("L", (64, 128), 205), Image.fromarray(np.tile(ga[:, None], (1, 64)))))
        fq = [(xl - 0.12, 0.005, z0), (xl + DW + 0.12, 0.005, z0), (xl + DW + 0.3, 0.005, z0 - 1.1), (xl - 0.3, 0.005, z0 - 1.1)]
        paste_quad(img, g, [cam.proj(p) for p in fq])
        foot = cam.proj((DX, 0.0, z0))
        img = add_glow(img, foot[0], foot[1], W * 0.09, H * 0.08, (255, 225, 150), 0.55 * kd, blur=36)
    # --- слова на двери: 2.0 THAT · 2.07 IT · 2.2 WAS · 2.37 ABOUT · 2.6 TO.; улетают вверх в 3.0
    tw, th, tiles = _door_words()
    starts = [2.0, 2.07, 2.2, 2.37, 2.6]
    u_up = seg(t, 3.0, 3.07)
    if t >= 2.0 and u_up < 1.0:
        smw = (DW - 0.12) / tw
        up = 3.0 * u_up * u_up
        for i, (tile, cxw, cyw) in enumerate(tiles):
            if t < starts[i] - 1e-6: continue
            p = seg(t, starts[i], starts[i] + 0.10)
            s = 1.15 + (1.0 - 1.15) * out_cubic(p)
            op = 0.6 + 0.4 * clamp01(p * 2.0)
            wq_ = tile.size[0] * smw * s; hq_ = tile.size[1] * smw * s
            wx = DX + (cxw - tw / 2) * smw
            wy = DH - 0.10 - cyw * smw + up
            for gh, gop in ((0.0, op), (-0.45, 0.35 * u_up), (-0.8, 0.2 * u_up)):
                if gop <= 0.01: continue
                q = face_quad(wx, wy + gh * up, ZW - 0.05, wq_, hq_)
                paste_quad(img, tile, [cam.proj(pp) for pp in q], gop)
    # --- лист с цитатой: висит ближе стены, улетает вверх в 1.9 за 3 кадра
    u_fly = seg(t, 1.9, 2.0)
    if u_fly < 1.0:
        hl_n = sum(1 for k in (1.0, 1.033, 1.067) if t >= k - 1e-6)
        sheet = _sheet_tex(hl_n)
        if kd > 0: sheet = mul_tex(sheet, 1 - 0.6 * kd)
        zs = ZW - 2.2
        fly = 4.0 * u_fly * u_fly
        sq = face_quad(-1.07, 1.78 + fly, zs, 1.8, 1.1, yaw=math.radians(12), roll=math.radians(-2))
        # тень листа на стене
        sh = [(p[0] + 0.28, p[1] - 0.22, ZW - 0.015) for p in sq]
        a = Image.new("RGBA", (64, 40), (30, 28, 26, int(70 * (1 - 0.5 * kd) * (1 - u_fly))))
        paste_quad(img, a.filter(ImageFilter.GaussianBlur(3)), [cam.proj(p) for p in sh])
        if u_fly == 0: hang_wires(img, cam, sq, (0.08, 0.92))
        op = 1.0 - 0.7 * u_fly
        for gh, gop in ((0.0, op), (-0.5, 0.3 * u_fly), (-0.9, 0.18 * u_fly)):
            if gop <= 0.01: continue
            q = [(p[0], p[1] + gh * fly, p[2]) for p in sq]
            paste_quad(img, sheet, [cam.proj(p) for p in q], gop)
    # --- засвет из проёма: белое + тёплое, уголь внизу проёма
    if a_open > 0:
        so = math.sin(a_open)
        pc = cam.proj((DX, DH * 0.5, ZW)); pb = cam.proj((DX, 0.1, ZW))
        rad = DW * F / max(0.3, ZW - cam.z)
        img = add_glow(img, pc[0], pc[1], rad * 1.6, rad * 3.2, (255, 244, 215), 0.75 * so * (1 + 1.5 * ur), blur=70)
        img = add_glow(img, pb[0], pb[1], rad * 2.2, rad * 1.4, (255, 150, 45), 0.70 * so * (1 + 1.0 * ur), blur=90)
        if a_open > math.radians(45):
            es = 0.42 * seg(a_open, math.radians(45), math.radians(75))
            img = embers(img, cam, [(DX - 0.12, 0.26, ZW + 0.25, es)], t, glow=1.2)
    if ur > 0:
        img = rush_blur(img, clamp01(ur * 1.6))
    return to_white(img, w_out)

SCENES = {"G41": (g41, 4.5), "G42": (g42, 4.5)}

if __name__ == "__main__":
    code = sys.argv[1]; out = sys.argv[2]
    SCENES[code][0](float(os.environ.get("ZAL_FRAME", "1.0"))).convert("RGB").save(out)
    print("кадр", out)
