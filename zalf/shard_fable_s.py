# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть S: G37, G46).
Один кадр: ZAL_FRAME=1.9 python3 shard_fable.py G37 /tmp/k.png

Числа сняты с плёнки покадрово (polosy/G37_polosa_*, G37_setka, G46_polosa_*, G46_setka):

  G37  кусок взят 112.0-116.5 (в таблице 111.0 — там ещё догорают угли прошлой сцены,
       сама стена входит на 111.967). Стена — не плоскость, а РЕШЁТКА тёмных шариков
       на тросах с потолка: ряды по ширине, по высоте и в глубину.
       111.967-112.167 камера ВНУТРИ решётки и вылетает из неё назад-вверх (шары 8-10 %
       кадра, смаз); 112.200 слева входит перекидной счётчик на двух ножках (первый
       кадр — одна перевёрнутая плашка), цифры мечутся: 459·493·507·539·523·532·573·
       637·613·647·682·702·732·742·749·738·778·733·870·846·843·832·893·933·922·949·943·
       934·994·983·999·1038·1070·1029·1053 … садится на 1,134 к 114.2 и ЖЕЛТЕЕТ.
       Слова на тросах над решёткой: MORE 112.367 · THAN 112.6 · A 112.7 · THOUSAND
       (жёлтая наклейка) 112.9 · PEOPLE 113.267 · WHO 113.6 · BUILD 113.8 · AI 114.0.
       Сетка 114.30: решётка x 10-90 %, y 36-92 % (≈32 столбца × 20 рядов, в глубину
       десятки рядов); счётчик x 16-44 %, y 65-88 %, ножки до 97 % → d≈6 м, короб
       1.64×0.72 м, низ короба 0.31 м над полом, X≈-1.2; строки текста на 20 % и 30 %
       высоты, капитель ≈0.30 м на d≈7 → Y 2.7 и 2.3 м — висят ровно над решёткой
       (верх решётки 2.1 м).

  G46  кусок взят 235.25-239.75 (в таблице 235.0 — первые 0.3 с ещё амфитеатр).
       Здание СОБИРАЕТСЯ: колоннада стоит на полу с первого кадра (235.3), а части
       ОПУСКАЮТСЯ на тросах с потолка и садятся друг на друга, без отскока:
       антаблемент виден 235.35, идёт ровно, садится на колонны 235.85 (0.5 с);
       фронтон виден 235.75, садится 236.03 (0.28 с); барабан купола 236.22→236.52
       (0.3 с); сам купол-шар 237.03→237.33 (0.3 с). Тросы над частями остаются.
       Сетка 236.00: здание x 2-95 %, линия основания 77 % → d≈10.5 м, ширина ≈9.5 м;
       верх колонн 47 % → 1.7 м, конёк фронтона 30 % → 2.7 м; 237.40: купол x 38-55 %,
       y 8-33 % (d≈7.8 → шар ⌀≈1.2 м, верх 4.0 м). Камера за 2.5 с подъезжает
       с 10.5 до 7.8 м и дальше ползёт. Свет из левых окон: тень ложится на пол
       ВПРАВО-ВПЕРЁД от каждой части, под зданием мягкое отражение.
       Слова: FOR 235.63 · ALL 235.77 · OF 235.93 · HISTORY, 236.07 · GOVERNMENTS
       236.63 · HAVE 236.97 · BEEN 237.23 (слева, 4 строки, x 6-30 %, y 15-40 %);
       THE 237.23 · MOST 237.30 · POWERFUL(маркер) 237.60 · ORGANIZATIONS 238.0 ·
       ON 238.6 · EARTH. 238.8 (справа, x 70-96 %). Угли у купола с 239.2.
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import *

CAP = 0.715                   # капитель Arial Black в долях кегля
YEL = (255, 212, 0, 255)
INK = (30, 27, 26, 255)

# ----------------------------------------------------------------- общие вещи

def pop(t0, t, dur=0.10, k0=1.22):
    """вход слова как на плёнке: первый кадр крупнее и прозрачнее, за ~3 кадра садится"""
    if t < t0 - 1e-6: return None
    u = seg(t, t0, t0 + dur)
    return k0 + (1.0 - k0) * out_cubic(u), 0.55 + 0.45 * clamp01(u * 2.2)

def visible(cam, corners, margin=0.35):
    return min(c[2] for c in corners) - cam.z > margin

def smooth(u):
    u = clamp01(u); return u * u * (3 - 2 * u)

def rush_blur(img, k):
    """смаз пролёта: пара увеличенных копий поверх, k — сила 0..1"""
    if k <= 0.01: return img
    base = img.convert("RGB")
    for z in (1.012, 1.028):
        sw, sh = int(W * z), int(H * z)
        big = base.resize((sw, sh), Image.BILINEAR).crop(((sw - W) // 2, (sh - H) // 2,
                                                            (sw - W) // 2 + W, (sh - H) // 2 + H))
        base = Image.blend(base, big, 0.30 * k)
    return base.convert("RGBA")

def _tiles(lines, fsize, hl=None, color=INK, cond=0.62, left=False):
    """плитки слов, сжатые по ширине и обрезанные по контуру:
    (ширина блока, высота блока, [(плитка, cx, cy)]); left — строки по левому краю"""
    tw, th, tiles = word_tiles(lines, fsize=fsize, hl=hl, color=color)
    out = []
    for tile, cx, cy in tiles:
        tile = tile.resize((max(4, int(tile.size[0] * cond)), tile.size[1]), Image.LANCZOS)
        bb = tile.getbbox()
        if bb is None: continue
        out.append((tile.crop((bb[0], 0, bb[2], tile.size[1])), cx * cond, cy))
    if left:
        rows = {}
        for tile, cx, cy in out:
            rows[cy] = min(rows.get(cy, 1e9), cx - tile.size[0] / 2)
        out = [(tile, cx - rows[cy] + 10, cy) for tile, cx, cy in out]
    return tw * cond, th, out

def hang_words(img, cam, t, words, starts, origin, cap, fsize=200, align="c",
               depth=0.10, side=(18, 16, 15), wires=True):
    """слова на тросах: origin — (X, Y верхней строки по центру, Z); cap — капитель в метрах;
    align 'c' — блок центрирован по X, 'l' — левый край блока в origin[0]"""
    tw, th, tiles = words
    sc = cap / (CAP * fsize)
    for i, (tile, cx, cy) in enumerate(tiles):
        p = pop(starts[i], t)
        if p is None: continue
        s, op = p
        w, h = tile.size[0] * sc * s, tile.size[1] * sc * s
        u = (cx - (tw / 2 if align == "c" else 0)) * sc
        v = -(cy - tiles[0][2]) * sc
        ux = (math.cos(cam.yaw), 0.0, math.sin(cam.yaw))        # ось строки = ось экрана
        c = quad((origin[0] + u * ux[0], origin[1] + v, origin[2] + u * ux[2]), w, h, yaw=cam.yaw)
        if not visible(cam, c): continue
        if wires:
            n = 2 if w > 0.5 else 1
            for j in range(n):
                f = (j + 0.5) / n
                wire(img, cam, (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1], c[0][2]),
                     color=(96, 98, 102, 230), width=2)
        if s > 1.08:
            for sh in (-0.05, 0.05):
                cc = quad((origin[0] + (u + sh * w) * ux[0], origin[1] + v, origin[2] + (u + sh * w) * ux[2]), w, h, yaw=cam.yaw)
                paste_quad(img, tile, [cam.proj(q) for q in cc], 0.22)
        if op < 1.0:
            a = tile.split()[3].point(lambda v_: int(v_ * op)); tile = tile.copy(); tile.putalpha(a)
        extrude(img, cam, c, tile, depth=depth, steps=2, shade=side)

def at_screen(cam, fx, fy, d):
    """точка мира, которая ляжет в кадр на долю (fx, fy) на дальности d (с учётом поворота камеры)"""
    dx_ = (fx - 0.5) * W / F * d; dy = (0.5 - fy) * H / F * d
    c, si = math.cos(cam.yaw), math.sin(cam.yaw)
    return (cam.x + dx_ * c - d * si, cam.y + dy, cam.z + dx_ * si + d * c)

# ----------------------------------------------------------------- G37: решётка шариков

NX, NY, NZ = 32, 18, 3
SX, SY, SZ = 0.165, 0.115, 0.32
LAT_X0, LAT_Y0, LAT_Z0 = -2.6, 0.22, 9.0        # левый-нижний-передний шар
BALL_R = 0.033

_LAT = {}
def _lattice():
    if not _LAT:
        ix, iy, iz = np.meshgrid(np.arange(NX), np.arange(NY), np.arange(NZ), indexing="ij")
        # передний слой ровный, задние чуть разболтаны (±12 % шага) — иначе ряды
        # в глубину выстраиваются в радиальную «звезду», которой на плёнке нет
        rng = np.random.default_rng(37)
        jit = (iz.ravel() > 0).astype(np.float64)
        X = LAT_X0 + ix.ravel() * SX + jit * rng.uniform(-0.12, 0.12, ix.size) * SX
        Y = LAT_Y0 + iy.ravel() * SY + jit * rng.uniform(-0.12, 0.12, ix.size) * SY
        Zc = LAT_Z0 + iz.ravel() * SZ + jit * rng.uniform(-0.1, 0.1, ix.size) * SZ
        _LAT["xyz"] = (X.astype(np.float64), Y.astype(np.float64), Zc.astype(np.float64))
        cx, cz = np.meshgrid(np.arange(NX), np.arange(NZ), indexing="ij")
        _LAT["cols"] = (LAT_X0 + cx.ravel() * SX, LAT_Z0 + cz.ravel() * SZ)
    return _LAT

def lattice(img, cam, blur=0.0):
    """тысячи шариков на тросах: проекция numpy, рисование — эллипсы ImageDraw далеко→близко"""
    L = _lattice()
    X, Y, Zc = L["xyz"]
    d = ImageDraw.Draw(img, "RGBA")
    # тросы: один на столбец (x,z), от потолка до нижнего шара
    cxs, czs = L["cols"]
    dz = czs - cam.z
    ok = dz > 0.5
    k = F / np.where(ok, dz, 1.0)
    px = W / 2 + (cxs - cam.x) * k
    ya = H / 2 - (CEIL - cam.y) * k
    yb = H / 2 - (LAT_Y0 - cam.y) * k
    front = czs < LAT_Z0 + SZ * 0.5
    for i in np.nonzero(ok & (px > -5) & (px < W + 5))[0]:
        d.line([(px[i], ya[i]), (px[i], yb[i])], fill=(150, 152, 156, 130 if front[i] else 45), width=1)
    # шары
    dz = Zc - cam.z
    ok = dz > 0.8
    k = F / np.where(ok, dz, 1.0)
    px = W / 2 + (X - cam.x) * k
    py = H / 2 - (Y - cam.y) * k
    r = BALL_R * k
    ok &= (px > -r - 2) & (px < W + r + 2) & (py > -r - 2) & (py < H + r + 2)
    idx = np.nonzero(ok)[0]
    idx = idx[np.argsort(-dz[idx])]
    sm = 1.0 + 3.0 * blur                        # смаз: шар вытягивается по ходу камеры
    # слои в глубину светлеют (воздух): передний почти чёрный, задний серый
    layer = np.rint((Zc - LAT_Z0) / SZ).astype(int)
    for i in idx:
        x, y, rr = px[i], py[i], r[i]
        g = (56, 124, 168)[min(2, layer[i])]
        body = (g, g - 2, g - 4, 255)
        if rr < 1.2:
            d.point((x, y), fill=body); continue
        ry = rr * sm
        d.ellipse([x - rr, y - ry, x + rr, y + ry], fill=body)
        if rr >= 3.5:
            d.ellipse([x - rr * 0.62, y - ry * 0.72, x + rr * 0.18, y - ry * 0.02], fill=(g + 70, g + 68, g + 66, 255))
        if rr >= 9:
            d.ellipse([x - rr * 0.42, y - ry * 0.55, x - rr * 0.12, y - ry * 0.28], fill=(g + 130, g + 128, g + 126, 255))
    return len(idx)

def lattice_shadow(img, cam):
    """мягкое пятно под решёткой на полу"""
    x0, x1 = LAT_X0 - 0.3, LAT_X0 + (NX - 1) * SX + 0.3
    z0, z1 = LAT_Z0 - 0.2, LAT_Z0 + (NZ - 1) * SZ + 0.2
    sh = [(x0, 0.01, z1), (x1, 0.01, z1), (x1, 0.01, z0), (x0, 0.01, z0)]
    if not visible(cam, sh): return
    tex = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    ImageDraw.Draw(tex).rectangle([24, 24, 231, 231], fill=(40, 42, 46, 90))
    tex = tex.filter(ImageFilter.GaussianBlur(18))
    paste_quad(img, tex, [cam.proj(p) for p in sh])

# перекидной счётчик
_CNT = {}
def counter_tex(text, settled, flips, px=820):
    """чёрный короб, ячейки по ширине знака (запятая узкая), белые цифры, по посадке жёлтые;
    flips — номера ячеек, пойманных на полуобороте"""
    h = int(px * 0.44)
    key = (text, settled, tuple(sorted(flips)))
    if key in _CNT: return _CNT[key]
    img = Image.new("RGBA", (px, h), (18, 17, 17, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, px - 1, h - 1], outline=(70, 68, 66, 255), width=6)
    f = font("Oswald-Bold.ttf", int(h * 0.74))
    col = YEL if settled else (236, 236, 236, 255)
    dig_w = px * 0.17; com_w = px * 0.07; gap = 6
    widths = [com_w if ch == "," else dig_w for ch in text]
    total = sum(widths) + gap * (len(text) - 1)
    x = (px - total) / 2
    for i, ch in enumerate(text):
        cw = widths[i]
        d.rectangle([x, h * 0.12, x + cw, h * 0.88], fill=(30, 29, 29, 255))
        b = d.textbbox((0, 0), ch, font=f)
        tx = x + (cw - (b[2] - b[0])) / 2 - b[0]; ty = (h - (b[3] - b[1])) / 2 - b[1]
        if ch == ",": ty = h * 0.70 - b[3]
        if i in flips and not settled:
            lay = Image.new("RGBA", (px, h), (0, 0, 0, 0))
            ImageDraw.Draw(lay).text((tx, ty), ch, font=f, fill=col)
            lay = lay.crop((int(x), 0, int(x + cw), int(h / 2)))
            img.alpha_composite(lay, (int(x), 0))
            d.rectangle([x + 6, h * 0.50, x + cw - 6, h * 0.64], fill=(50, 49, 49, 255))
        else:
            d.text((tx, ty), ch, font=f, fill=col)
        d.line([(x, h / 2), (x + cw, h / 2)], fill=(12, 12, 12, 255), width=3)
        x += cw + gap
    _CNT[key] = img
    return img

def counter_value(t, t_on=0.2, t_set=2.2, final=1134):
    """цифры мечутся вокруг растущего значения, садятся на final"""
    if t < t_on: return None, False, set()
    u = seg(t, t_on, t_set)
    if u >= 1.0: return f"{final:,}", True, set()
    fr = int(t * 30)
    rng = np.random.default_rng(fr * 7919 + 13)
    base = final * (1 - (1 - u) ** 1.6)
    v = int(base + rng.uniform(-110, 110) * (1 - u * 0.5))
    v = max(100, v)
    n = len(f"{v:,}")
    flips = set(int(x) for x in rng.choice(n, size=int(rng.integers(0, 3)), replace=False))
    return f"{v:,}", False, flips

def counter(img, cam, t, x, z, t_on=0.2):
    p = pop(t_on, t, dur=0.13, k0=1.18)
    if p is None: return
    s, op = p
    txt, settled, flips = counter_value(t, t_on)
    tex = counter_tex(txt or "", settled, flips)
    wm, hm = 1.64 * s, 0.72 * s
    leg_h = 0.31
    c = quad((x, leg_h + hm / 2, z), wm, hm)
    if not visible(cam, c): return
    # ножки
    d = ImageDraw.Draw(img, "RGBA")
    for sx in (-0.36, 0.36):
        a = cam.proj((x + sx * wm, 0.0, z)); b = cam.proj((x + sx * wm, leg_h + 0.05, z))
        d.line([(a[0], a[1]), (b[0], b[1])], fill=(28, 27, 27, int(255 * op)), width=max(3, int(0.05 * F / a[2])))
    # тень на пол и отражение
    floor_shadow(img, cam, [(x - wm / 2, leg_h, z), (x + wm / 2, leg_h, z), (x + wm / 2, 0, z), (x - wm / 2, 0, z)], tex)
    reflection(img, cam, c, tex, strength=0.14)
    if op < 1.0:
        a = tex.split()[3].point(lambda v: int(v * op)); tex = tex.copy(); tex.putalpha(a)
    extrude(img, cam, c, tex, depth=0.22, steps=3, shade=(40, 39, 38))

_G37 = {}
def _g37_words():
    if not _G37:
        _G37["w"] = _tiles(["MORE THAN A THOUSAND", "PEOPLE WHO BUILD AI"], 200, hl={3})
    return _G37

def g37_cam(t):
    """0-0.3 вылет из решётки назад-вверх (у Cam нет наклона, поэтому «сверху» на плёнке
    заменён ходом вправо от счётчика, 112.3: счётчик x 0-25 %); 0.3-2.0 к центру; дальше ползёт"""
    a = (0.45, 1.2, 7.4)
    b = (0.6, 1.55, 3.6)
    c = (-0.05, 1.58, 2.3)
    if t < 0.3:
        u = out_cubic(t / 0.3)
        p = [a[i] + (b[i] - a[i]) * u for i in range(3)]
    else:
        u = smooth(seg(t, 0.3, 2.0))
        p = [b[i] + (c[i] - b[i]) * u for i in range(3)]
        e = max(0.0, t - 2.0)
        p[0] += 0.05 * e; p[2] -= 0.08 * e
    return Cam(p[0], p[1], p[2], 0.0)

def g37(t):
    """стена-перфорация: решётка тысяч шариков на тросах, камера вылетает из неё,
    перед ней перекидной счётчик мечется и садится на 1,134, над ней слова на тросах"""
    cam = g37_cam(t)
    img = room(cam)
    lattice_shadow(img, cam)
    # скорость камеры → смаз шаров и кадра
    v = 0.0
    if t < 0.3:
        c0, c1 = cam, g37_cam(t + 1 / 30)
        v = math.hypot(c1.x - c0.x, c1.y - c0.y, c1.z - c0.z) * 30
    blur = clamp01(v / 40.0)
    lattice(img, cam, blur=blur)
    wd = _g37_words()
    hang_words(img, cam, t, wd["w"],
               [0.367, 0.6, 0.7, 0.9, 1.267, 1.6, 1.8, 2.0],
               (-0.3, 2.72, LAT_Z0 + 0.3), 0.30, depth=0.12)
    counter(img, cam, t, -1.2, LAT_Z0 - 0.7, t_on=0.2)
    if blur > 0.05:
        img = rush_blur(img, blur)
    return img

# ----------------------------------------------------------------- G46: макет здания

CLAY_F = (222, 216, 208, 255)      # передняя грань
CLAY_S = (172, 164, 156, 255)      # боковая
CLAY_T = (238, 234, 228, 255)      # верхняя
CLAY_D = (156, 148, 140, 255)      # грань в тени (стена за колоннами)
LIGHT = (1.15, 0.0, -0.55)         # куда уезжает тень по полу на 1 м высоты (свет слева-сзади, тень к камере)

def _draw(img, op):
    """рисовать прямо (грани непрозрачные) или на слое (мина 1: RGBA-заливка не смешивается)"""
    if op >= 0.999: return img, ImageDraw.Draw(img, "RGBA"), None
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return img, ImageDraw.Draw(lay, "RGBA"), lay

def shadow_hull(img, cam, x0, x1, z0, z1, h, alpha=95, blur=7):
    """тень параллелепипеда на полу: подошва + верхняя грань, снесённая по свету, одним контуром"""
    lx, lz = LIGHT[0] * h, LIGHT[2] * h
    pts = [(x0, z0), (x1, z0), (x1, z1), (x0, z1), (x0 + lx, z0 + lz), (x1 + lx, z0 + lz),
           (x1 + lx, z1 + lz), (x0 + lx, z1 + lz)]
    if min(z for _, z in pts) - cam.z < 0.4: return
    p2 = [cam.proj((x, 0.01, z)) for x, z in pts]
    # выпуклая оболочка на экране
    P = sorted((q[0], q[1]) for q in p2)
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for q in P:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0: lower.pop()
        lower.append(q)
    for q in reversed(P):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0: upper.pop()
        upper.append(q)
    hull = lower[:-1] + upper[:-1]
    xs = [q[0] for q in hull]; ys = [q[1] for q in hull]
    bx0, by0 = int(max(0, min(xs) - 40)), int(max(0, min(ys) - 40))
    bx1, by1 = int(min(W, max(xs) + 40)), int(min(H, max(ys) + 40))
    if bx1 - bx0 < 2 or by1 - by0 < 2: return
    lay = Image.new("RGBA", (bx1 - bx0, by1 - by0), (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(q[0] - bx0, q[1] - by0) for q in hull], fill=(60, 58, 56, alpha))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)), (bx0, by0))

def box(img, cam, x0, x1, y0, y1, z0, z1, cf=CLAY_F, cs=CLAY_S, ct=CLAY_T, shadow=True, op=1.0):
    """параллелепипед: тень на пол, боковая, верхняя, передняя грани (порядок художника)"""
    if z0 - cam.z < 0.4: return
    if shadow and y0 < 0.05:
        shadow_hull(img, cam, x0, x1, z0, z1, y1 - y0, alpha=int(95 * op))
    img, d, lay = _draw(img, op)
    def put(corners, col):
        if not visible(cam, corners): return
        p = [cam.proj(q) for q in corners]
        d.polygon([(q[0], q[1]) for q in p], fill=col[:3] + (int(255 * op),))
    if cam.x < x0:
        put([(x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (x0, y0, z1)], cs)
    elif cam.x > x1:
        put([(x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (x1, y0, z0)], cs)
    if cam.y > y1:
        put([(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], ct)
    elif cam.y < y0:
        put([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], cs)
    put([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], cf)
    if lay is not None: img.alpha_composite(lay)

def pediment(img, cam, xc, y0, apex, z0, z1, half, op=1.0):
    """треугольный фронтон: два ската, полка карниза и передний треугольник"""
    if z0 - cam.z < 0.4: return
    img, d, lay = _draw(img, op)
    def tri(pts, col):
        p = [cam.proj(q) for q in pts]
        d.polygon([(q[0], q[1]) for q in p], fill=col[:3] + (int(255 * op),))
    L = (xc - half, y0, z0); R = (xc + half, y0, z0); A = (xc, apex, z0)
    Lb = (xc - half, y0, z1); Rb = (xc + half, y0, z1); Ab = (xc, apex, z1)
    tri([L, A, Ab, Lb], (214, 209, 202))           # левый скат
    tri([R, A, Ab, Rb], (234, 230, 224))           # правый скат
    if cam.y < y0: tri([L, R, Rb, Lb], CLAY_S)
    tri([L, A, R], CLAY_F)
    if lay is not None: img.alpha_composite(lay)

def sphere(img, cam, cx, cy, cz, r, op=1.0):
    """шар-купол: затенённый диск, свет слева-сверху-спереди, край с сглаживанием"""
    p = cam.proj((cx, cy, cz))
    if p[2] < 0.4: return
    R = r * F / p[2]
    n = int(max(6, min(1400, R * 2)))
    yy, xx = np.mgrid[0:n, 0:n]
    u = (xx - n / 2 + 0.5) / (n / 2); v = (yy - n / 2 + 0.5) / (n / 2)
    rr = np.sqrt(u * u + v * v)
    zz = np.sqrt(np.clip(1 - rr * rr, 0, 1))
    lgt = np.array([-0.55, 0.62, -0.55]); lgt /= np.linalg.norm(lgt)
    nd = u * lgt[0] + (-v) * lgt[1] + zz * lgt[2]
    sh = 0.80 + 0.20 * np.clip(nd, 0, 1) - 0.10 * np.clip(-nd, 0, 1)
    rgba = np.zeros((n, n, 4), np.uint8)
    base = np.array([240, 236, 230], np.float32)
    rgba[..., :3] = np.clip(base[None, None, :] * sh[..., None], 0, 255).astype(np.uint8)
    a = np.clip((1.0 - rr) * n * 0.5, 0, 1)
    rgba[..., 3] = (a * 255 * op).astype(np.uint8)
    sp = Image.fromarray(rgba, "RGBA")
    img.alpha_composite(sp, (int(p[0] - n / 2), int(p[1] - n / 2)))

def lower(t, t0, t1, h_from=4.6):
    """опускание на тросах: ровный ход с замедлением у посадки; возвращает dy (0 — село) или None"""
    if t < t0 - 1e-6: return None
    u = seg(t, t0, t1)
    return h_from * (1 - (1 - (1 - u) ** 2.2))

def rise(t, t0, t1):
    """рост из пола: доля высоты 0..1 с перелётом 3 % на посадке"""
    u = seg(t, t0, t1)
    k = 1.0 - (1.0 - u) ** 1.6
    return k + 0.03 * math.sin(math.pi * seg(t, t1, t1 + 0.1))

def piece_wires(img, cam, pts, y_top):
    for (x, z) in pts:
        wire(img, cam, (x, y_top, z), color=(118, 120, 124, 210), width=2)

# геометрия здания (метры, центр фасада X=BX, передняя кромка Z=BZ)
BX, BZ = 0.3, 10.5
COL_H, COL_W, COL_N, COL_STEP = 1.30, 0.30, 8, 0.56
ENT_H, PED_H = 0.30, 0.55
WING_H = 1.25

def building(img, cam, t, k_rise, dy_ent, dy_ped, dy_drum, dy_dome):
    """колоннада растёт из пола, остальное опускается с потолка.
    dy_* — на сколько часть ещё выше своего места (None — её ещё нет)"""
    base_y = 0.0
    # стилобат (платформа) и крылья — встают вместе с колоннами
    plat_h = 0.28 * k_rise
    box(img, cam, BX - 4.8, BX + 4.8, 0.0, plat_h, BZ - 0.25, BZ + 3.2, shadow=k_rise > 0.6)
    y0 = plat_h
    hw = WING_H * k_rise
    box(img, cam, BX - 4.6, BX - 2.5, y0, y0 + hw, BZ + 0.3, BZ + 2.8, shadow=k_rise > 0.6)
    box(img, cam, BX + 2.5, BX + 4.5, y0, y0 + hw, BZ + 0.3, BZ + 2.8, shadow=k_rise > 0.6)
    # стена целлы за колоннами (в тени)
    hc = COL_H * k_rise
    box(img, cam, BX - 2.25, BX + 2.25, y0, y0 + hc, BZ + 0.9, BZ + 3.0,
        cf=CLAY_D, cs=CLAY_D, ct=CLAY_T, shadow=False)
    # колонны
    for i in range(COL_N):
        xc = BX + (i - (COL_N - 1) / 2) * COL_STEP
        box(img, cam, xc - COL_W / 2, xc + COL_W / 2, y0, y0 + hc, BZ, BZ + COL_W, shadow=k_rise > 0.6)
    top_col = y0 + COL_H
    # антаблемент
    if dy_ent is not None:
        ya = top_col + dy_ent
        box(img, cam, BX - 2.4, BX + 2.4, ya, ya + ENT_H, BZ - 0.08, BZ + 3.05, shadow=False)
        piece_wires(img, cam, [(BX - 2.0, BZ + 0.6), (BX, BZ + 0.6), (BX + 2.0, BZ + 0.6)], ya + ENT_H)
        if dy_ent > 0.02:
            _drop_shadow(img, cam, BX - 2.4, BX + 2.4, BZ - 0.08, BZ + 3.05, dy_ent + top_col)
    # фронтон
    if dy_ped is not None:
        yp = top_col + ENT_H + dy_ped
        pediment(img, cam, BX, yp, yp + PED_H, BZ - 0.08, BZ + 3.05, 2.4)
        piece_wires(img, cam, [(BX - 1.2, BZ + 1.2), (BX + 1.2, BZ + 1.2)], yp + PED_H * 0.5)
    # барабан купола
    drum_y = top_col + ENT_H + 0.25
    if dy_drum is not None:
        yd = drum_y + dy_drum
        box(img, cam, BX - 1.0, BX + 1.0, yd, yd + 0.55, BZ + 0.75, BZ + 2.4, cf=CLAY_D, shadow=False)
        for i in range(6):
            xc = BX - 0.85 + i * 0.34
            box(img, cam, xc - 0.07, xc + 0.07, yd, yd + 0.55, BZ + 0.62, BZ + 0.76, shadow=False)
        box(img, cam, BX - 1.1, BX + 1.1, yd + 0.55, yd + 0.65, BZ + 0.55, BZ + 2.5, shadow=False)
        piece_wires(img, cam, [(BX - 0.6, BZ + 1.5), (BX + 0.6, BZ + 1.5)], yd + 0.65)
    # купол
    if dy_dome is not None:
        yc = drum_y + 0.65 + 0.44 + dy_dome
        sphere(img, cam, BX, yc, BZ + 1.55, 0.58)
        piece_wires(img, cam, [(BX, BZ + 1.55)], yc + 0.56)

def _drop_shadow(img, cam, x0, x1, z0, z1, y):
    """тень висящей части на полу: уехала по свету и размыта сильнее, чем у стоящей"""
    shadow_hull(img, cam, x0 + LIGHT[0] * y, x1 + LIGHT[0] * y, z0 + LIGHT[2] * y, z1 + LIGHT[2] * y,
                0.3, alpha=55, blur=16)

def building_reflection(img, cam, k_rise):
    """глянец пола: зеркальная копия фасада под линией пола, слабая и размытая"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cam2 = Cam(cam.x, -cam.y, cam.z, 0.0)          # камера под полом = зеркало
    hc = COL_H * k_rise
    y0 = 0.28 * k_rise
    box(lay, cam2, BX - 4.8, BX + 4.8, 0.0, y0, BZ - 0.25, BZ + 3.2, shadow=False)
    box(lay, cam2, BX - 4.6, BX - 2.5, y0, y0 + WING_H * k_rise, BZ + 0.3, BZ + 2.8, shadow=False)
    box(lay, cam2, BX + 2.5, BX + 4.5, y0, y0 + WING_H * k_rise, BZ + 0.3, BZ + 2.8, shadow=False)
    for i in range(COL_N):
        xc = BX + (i - (COL_N - 1) / 2) * COL_STEP
        box(lay, cam2, xc - COL_W / 2, xc + COL_W / 2, y0, y0 + hc, BZ, BZ + COL_W, shadow=False)
    lay = lay.transpose(Image.FLIP_TOP_BOTTOM)
    bb = lay.getbbox()
    if bb is None: return
    bb = (max(0, bb[0] - 12), max(0, bb[1] - 12), min(W, bb[2] + 12), min(H, bb[3] + 12))
    lay.paste(lay.crop(bb).filter(ImageFilter.GaussianBlur(5)), bb)
    # ослабить к низу
    a = np.asarray(lay.split()[3], np.float32)
    yy = np.arange(H, dtype=np.float32)[:, None]
    hor = H / 2
    fade = np.clip(1.0 - (yy - hor) / (H * 0.45), 0.0, 1.0) ** 1.5
    a = (a * fade * 0.30).astype(np.uint8)
    lay.putalpha(Image.fromarray(a, "L"))
    img.alpha_composite(lay)

_G46 = {}
def _g46_words():
    if not _G46:
        _G46["l"] = _tiles(["FOR ALL OF", "HISTORY,", "GOVERNMENTS", "HAVE BEEN"], 200, cond=0.66, left=True)
        _G46["r"] = _tiles(["THE MOST", "POWERFUL", "ORGANIZATIONS", "ON EARTH."], 200, hl={2}, cond=0.66, left=True)
    return _G46

def g46_cam(t):
    u = smooth(seg(t, 0.0, 2.5))
    cz = 2.7 * u + 0.12 * max(0.0, t - 2.5)
    cx = -1.7 + 0.4 * u            # камера левее здания: видны левые грани, как на плёнке
    yaw = -math.atan2(BX + 0.3 - cx, BZ + 1.5 - cz)   # и довёрнута на здание, чтобы оно было в центре
    return Cam(cx, 1.55, cz, yaw)

def g46(t):
    """белый макет здания-символа: колоннада растёт из пола, антаблемент, фронтон, барабан
    и купол опускаются на тросах и садятся друг на друга; тень по свету из окон, глянец пола"""
    cam = g46_cam(t)
    img = room(cam)
    k_rise = rise(t, 0.0, 0.17)
    dy_ent = lower(t, 0.10, 0.60)
    dy_ped = lower(t, 0.50, 0.78, h_from=4.2)
    dy_drum = lower(t, 0.97, 1.27, h_from=3.9)
    dy_dome = lower(t, 1.78, 2.08, h_from=3.2)
    building_reflection(img, cam, k_rise)
    # всё ниже линии пола на дальности здания — обрезать (рост из пола)
    if k_rise < 0.999:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        building(lay, cam, t, k_rise, dy_ent, dy_ped, dy_drum, dy_dome)
        yf = H / 2 + cam.y * F / max(0.3, BZ - cam.z)
        ImageDraw.Draw(lay).rectangle([0, int(yf), W, H], fill=(0, 0, 0, 0))
        img.alpha_composite(lay)
    else:
        building(img, cam, t, k_rise, dy_ent, dy_ped, dy_drum, dy_dome)
    wd = _g46_words()
    # блоки текста висят на дальности здания: слева x 6-30 %, справа 70-96 % кадра (237.4)
    if "pl" not in wd:               # точки подвеса считаются по камере момента 237.35 (t=2.1), дальше висят
        cam21 = g46_cam(2.1)
        wd["pl"] = at_screen(cam21, 0.06, 0.17, 7.8)
        wd["pr"] = at_screen(cam21, 0.70, 0.17, 7.8)
    hang_words(img, cam, t, wd["l"], [0.38, 0.52, 0.68, 0.82, 1.38, 1.72, 1.98],
               wd["pl"], 0.22, align="l", depth=0.10)
    hang_words(img, cam, t, wd["r"], [1.98, 2.05, 2.35, 2.75, 3.35, 3.55],
               wd["pr"], 0.22, align="l", depth=0.10)
    # угли у купола под конец куска (на плёнке с 239.2)
    if t > 3.9:
        pts = cluster(BX + 0.9, 3.4, BZ + 1.6, 0.55 * seg(t, 3.9, 4.3), n=4, seed=3, mirror=False)
        img = embers(img, cam, pts, t, glow=0.7)
    return img

SCENES = {"G37": (g37, 4.5), "G46": (g46, 4.5)}
