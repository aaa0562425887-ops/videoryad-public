# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть I: G05, G48).
Запуск: shard_fable_i.py <код> <out.mp4>; один кадр: ZAL_FRAME=1.9 shard_fable_i.py G05 k.png

Числа сняты с плёнки покадрово (polosy/G05_vhod, G05_posle, G05_krupno, G48_vhod, G48_posle,
G48_setka):
  G05  кусок 143.5 +4.5. Табло 00:00:00 входит сверху: 144.167 его ещё нет, 144.200 центр на
       11.7 % высоты кадра, 144.233 → 15 %, 144.267 → 16.6 %, 144.300-144.333 → 17 % (самая
       нижняя точка), дальше за ~0.3 с поднимается на 3-4 px при высоте табло 47 px — проскок
       ~8 %. Шаг спуска по кадрам затухает ×0.22 за кадр (экспонента). Наклон верхней кромки:
       144.2 правый край выше на 4 px (≈+1.4°), 144.9 ровно, 145.4 правый ниже на 5 px (≈-1.2°)
       — период качания ≈3 с, амплитуда ±1.5°, не затухает. Табло x 52-78 %, два троса 1-2 px.
       Цифры бегут 144.4-145.267 и встают на 88:00:00, после остановки становятся ЖЁЛТЫМИ.
       Слова слева: WORKED 143.567, TOGETHER(маркер) 143.767, FOR 144.133, EIGHTY-EIGHT(маркер)
       144.300, HOURS 144.767, STRAIGHT. 145.167. Поле углей стягивается в одну точку 144.9→145.6
       (сначала диск с ярким ободом, потом точка); с ~145.7 камера опускается к точке, табло
       уходит вверх из кадра; AND 146.4, THEY 146.533 над точкой.
       Камера: до 144.8 ровно на уровне глаз; 144.8-145.5 ПОДНИМАЕТСЯ (~2.5 м) и наклоняется
       вниз ~9° (горизонт с 50 % уходит к ~20 %, табло при этом остаётся на y 8-26 %); с 145.8
       наклон ещё ~10°, табло уходит из кадра вверх. Сделано классом PCam (наклон) — zal_core
       не трогал. Диск при стягивании сохраняет рисунок рядов → сжатие однородное по осям.
  G48  кусок 261.0 +4.0. До 261.5 внутренняя сцена во весь кадр. Отъезд 261.5→262.1 (600 мс,
       S-образно): правая кромка картины уходит на 4·9·16·24·33·44·57 px за первые семь кадров,
       верхняя кромка трогается раньше нижней (камера одновременно опускается). К 262.1 картина
       x 28-71 %, y 20-60 % (16:9), к 263.0 x 30-69 %, дальше медленно до 31-67 % (камера
       продолжает отъезжать). Тросы картины на 22 % и 76 % её ширины. Плашка FRAME x 36-62 %,
       y 61-68 %, чёрная, FRAME белым, число жёлтым; число = номер кадра ролика (261.8 с →
       7 855), растёт на 1 каждый кадр. ONE 262.167, MORE 262.300, THING. 262.633 над рамой в её
       плоскости, улетают вверх 263.233-263.300. На полу перед картиной встают слова:
       I 263.533, DIDN'T 263.867, MAKE 264.100, THIS 264.433, VIDEO. 264.667 (x 19-76 %, y 76-86 %).
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import *

FPS = 30
CAP = 0.715                       # капитель Arial Black в долях кегля
DARK = (34, 31, 30, 255)
DARK_SIDE = (20, 18, 17)
YEL = (255, 206, 56, 255)

# ----------------------------------------------------------------- общие вещи

def smooth(u):
    u = clamp01(u); return u * u * (3 - 2 * u)

def pop(t0, t, dur=0.10, k0=1.20):
    """вход слова: первый кадр крупнее и прозрачнее, за три кадра садится"""
    if t < t0 - 1e-6: return None
    u = seg(t, t0, t0 + dur)
    return k0 + (1.0 - k0) * out_cubic(u), 0.55 + 0.45 * clamp01(u * 2.2)

def visible(cam, corners, margin=0.3):
    return min(c[2] for c in corners) - cam.z > margin

def vol(img, cam, corners, tex, depth=0.1, steps=4, side=DARK_SIDE, op=1.0):
    """объём копиями в глубину (+z) с прозрачностью"""
    alpha = tex.split()[3]
    for i in range(steps, -1, -1):
        k = i / steps
        cs = [(c[0], c[1], c[2] + depth * k) for c in corners]
        if not visible(cam, cs): continue
        pts = [cam.proj(p) for p in cs]
        if i == 0:
            t = tex
        else:
            v = [int(side[j] * (0.80 + 0.20 * (1 - k))) for j in range(3)]
            t = Image.new("RGBA", tex.size, (v[0], v[1], v[2], 255)); t.putalpha(alpha)
        paste_quad(img, t, pts, op)

def row_tiles(line, fsize=200, hl=None, color=DARK, fname="ArialBlack.ttf", cond=0.80):
    """плитки слов одной строки, обрезанные по ширине; (плитка, смещение центра от левого
    края первого слова в px, высота строки px)"""
    tw, th, tiles = word_tiles([line], fsize=fsize, fname=fname, hl=hl, color=color)
    out = []; x = 0.0
    gap = fsize * 0.50 * cond                      # зазор между словами ~0.55 капители (объём съедает часть)
    for tile, cx, cy in tiles:
        if cond != 1.0:
            tile = tile.resize((max(4, int(tile.size[0] * cond)), tile.size[1]), Image.LANCZOS)
        bb = tile.getbbox()
        if bb is None: continue
        cr = tile.crop((bb[0], 0, bb[2], tile.size[1]))
        out.append((cr, x + cr.size[0] / 2))
        x += cr.size[0] + gap
    return out

def row_cap(tiles, width_m, fsize=200):
    """капитель, при которой строка плиток занимает width_m метров"""
    tile, off = tiles[-1]
    px = off + tile.size[0] / 2
    return width_m / px * (CAP * fsize)

def word_row(img, cam, t, tiles, starts, left, y, z, cap, depth=0.1, side=DARK_SIDE,
             floor=False, shadow=False, dy=0.0, k0=1.20, wires=0):
    """строка слов в плоскости z=const лицом к камере; left — x левого края первого слова,
    y — центр строки (или пол, если floor); cap — высота капители в метрах"""
    sc = cap / (CAP * 200)
    for (tile, off), t0 in zip(tiles, starts):
        p = pop(t0, t, k0=k0)
        if p is None: continue
        s, op = p
        w = tile.size[0] * sc * s; h = tile.size[1] * sc * s
        cx = left + off * sc
        cy = (h / 2 if floor else y) + dy
        c = quad((cx, cy, z), w, h)
        if not visible(cam, c): continue
        if shadow and dy > -0.02:
            bl, br = c[3], c[2]
            sh = [(bl[0] + 0.5 * h, 0.012, bl[2] + 1.1 * h), (br[0] + 0.5 * h, 0.012, br[2] + 1.1 * h),
                  (br[0], 0.012, br[2]), (bl[0], 0.012, bl[2])]
            a = tile.split()[3].point(lambda v: int(v * 0.28))
            dark = Image.new("RGBA", tile.size, (38, 36, 34, 255)); dark.putalpha(a)
            paste_quad(img, dark.filter(ImageFilter.GaussianBlur(12)), [cam.proj(p) for p in sh])
        if wires:
            for j in range(wires):
                f = (j + 0.5) / wires
                top = (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1], c[0][2])
                wire(img, cam, top, color=(96, 98, 102, 230), width=2)
        if s > 1.08:
            for shx in (-0.05, 0.05):
                cc = quad((cx + shx * w, cy, z), w, h)
                paste_quad(img, tile, [cam.proj(q) for q in cc], 0.22)
        vol(img, cam, c, tile, depth=depth, steps=4, side=side, op=op)

class PCam(Cam):
    """камера с наклоном: pitch > 0 — смотрит вниз (горизонт уходит вверх). Всё в zal_core идёт
    через cam.proj, поэтому зал, окна, тросы и угли наклоняются вместе"""
    def __init__(s, x=0.0, y=1.55, z=0.0, yaw=0.0, pitch=0.0):
        Cam.__init__(s, x, y, z, yaw); s.pitch = pitch
    def proj(s, p):
        dx, dy, dz = p[0] - s.x, p[1] - s.y, p[2] - s.z
        if s.yaw:
            c, si = math.cos(-s.yaw), math.sin(-s.yaw)
            dx, dz = dx * c - dz * si, dx * si + dz * c
        if s.pitch:
            c, si = math.cos(s.pitch), math.sin(s.pitch)
            dy, dz = dy * c + dz * si, -dy * si + dz * c
        if dz < 0.08: dz = 0.08
        k = F / dz
        return (W / 2 + dx * k, H / 2 - dy * k, dz)

def far_wall(img, cam):
    """торцевая стена: room() её не рисует, при наклоне камеры в прорехе был бы цвет пола"""
    zz = cam.z + 69.0
    p = [cam.proj((-WALL, CEIL, zz)), cam.proj((WALL, CEIL, zz)), cam.proj((WALL, 0.0, zz)), cam.proj((-WALL, 0.0, zz))]
    ImageDraw.Draw(img, "RGBA").polygon([(q[0], q[1]) for q in p], fill=(229, 231, 234, 255))

def rope(img, cam, top, bottom, color=(96, 98, 102, 235), width=2):
    a = cam.proj(top); b = cam.proj(bottom)
    if a[2] < 0.3 or b[2] < 0.3: return
    ImageDraw.Draw(img, "RGBA").line([(a[0], a[1]), (b[0], b[1])], fill=color, width=width)

# ---------- быстрое поле углей: спрайты кэшируются по размеру ----------
_SPC = {}
def _spr(size):
    if size not in _SPC:
        rgb, al = Z._sprite()
        sp = np.array(Image.fromarray(rgb.astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32)
        sa = np.array(Image.fromarray((al * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR),
                      np.float32)[..., None] / 255.0
        _SPC[size] = (sp, sa)
    return _SPC[size]

def ember_field(img, cam, pts, t, glow=0.9, blur=34):
    """то же, что embers(), но сотни точек за доли секунды: спрайт на каждый размер один"""
    add = np.zeros((H, W, 3), np.float32)
    ca = np.zeros((H, W, 1), np.float32)
    for i, (x, y, z, s) in enumerate(pts):
        pulse = 0.82 + 0.18 * math.sin(t * 3.4 + i * 1.7)
        px, py, dz = cam.proj((x, y, z))
        if dz < 0.3: continue
        size = int(s * F / dz * pulse)
        size = max(6, min(240, (size // 2) * 2))
        if px < -size or px > W + size or py < -size or py > H + size: continue
        sp, sa = _spr(size)
        x0, y0 = int(px - size / 2), int(py - size / 2)
        X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(W, x0 + size), min(H, y0 + size)
        if X1 <= X0 or Y1 <= Y0: continue
        sub = sp[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        suba = sa[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        add[Y0:Y1, X0:X1] += sub * suba * pulse * 0.55
        ca[Y0:Y1, X0:X1] = np.maximum(ca[Y0:Y1, X0:X1], np.clip(suba * 2.6 - 0.45, 0, 1))
    if ca.max() <= 0 and add.max() <= 0: return img
    add = np.minimum(add, 110.0)                    # тысячи наложений не должны выбеливать
    halo = np.asarray(Image.fromarray(np.clip(add, 0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(blur)), np.float32)
    arr = np.asarray(img.convert("RGB"), np.float32)
    core = np.array([255.0, 150.0, 58.0], np.float32)
    halo = halo * np.array([1.0, 0.62, 0.22], np.float32)   # ореол оранжевый, не белёсый
    arr = arr * (1 - ca) + core * ca + add * 0.15 + halo * glow
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

# ----------------------------------------------------------------- G05

def clock_tex(text, color=(245, 245, 245, 255), px=1400, smear=0.0):
    """чёрное табло с цифрами перекидного типа; smear — вертикальный смаз бегущих цифр"""
    h = int(px * 0.29)
    img = Image.new("RGBA", (px, h), (22, 21, 20, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, px - 1, h - 1], outline=(74, 74, 76, 255), width=4)
    f = font("Oswald-Bold.ttf", int(h * 0.84))
    # цифры по ячейкам, чтобы при беге не прыгала ширина
    cells = []; x = px * 0.04
    for ch in text:
        cw = px * (0.036 if ch == ":" else 0.141)
        cells.append((ch, x, cw)); x += cw
    lay = Image.new("RGBA", (px, h), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for ch, x0, cw in cells:
        b = ld.textbbox((0, 0), ch, font=f)
        ld.text((x0 + (cw - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), ch,
                font=f, fill=color)
        if ch != ":":   # шов перекидной карточки
            ld.line([(x0 + cw * 0.08, h / 2), (x0 + cw * 0.92, h / 2)], fill=(22, 21, 20, 255), width=5)
    if smear > 0:
        lay = lay.filter(ImageFilter.GaussianBlur(smear))
    img.alpha_composite(lay)
    return img

def clock_value(t):
    """(строка, цвет, смаз): стоит 00:00:00, с 0.9 бежит, на 1.77 встаёт на 88:00:00 жёлтым"""
    if t < 0.9: return "00:00:00", (245, 245, 245, 255), 0.0
    if t >= 1.77: return "88:00:00", YEL, 0.0
    u = seg(t, 0.9, 1.77)
    k = 1 - (1 - u) ** 2.2                       # разгон быстрый, у 88 тормозит
    secs = int(88 * 3600 * k)
    hh, mm, ss = secs // 3600, (secs // 60) % 60, secs % 60
    rng = np.random.default_rng(int(t * 30))
    if u < 0.92:
        mm, ss = int(rng.integers(0, 60)), int(rng.integers(0, 60))
    sm = 6.0 * (1 - u) + 1.0
    return f"{hh:02d}:{mm:02d}:{ss:02d}", (245, 245, 245, 255), sm

_FIELD = None
def ember_points():
    global _FIELD
    if _FIELD is None:
        rng = np.random.default_rng(11)
        pts = []
        z = EC[1] - 20.0                      # симметрично вокруг точки стягивания: при сжатии к кругу
        while z < EC[1] + 20.0:               # плотность с обеих сторон одна; ряды волнистые, как на плёнке
            x = -6.0 + float(rng.uniform(0, 0.4))
            while x < 6.0:
                xx = x + 0.55 * math.sin(z * 0.45 + x * 0.35) + float(rng.uniform(-0.06, 0.06))
                pts.append((xx, z + float(rng.uniform(-0.08, 0.08)), float(rng.uniform(0.17, 0.30)),
                            float(rng.uniform(0.55, 1.0))))   # последнее — доля радиуса обода, чтобы не лечь в одну линию
                x += 0.42
            z += 0.45 + 0.004 * z
        _FIELD = pts
    return _FIELD

EC = (-0.5, 7.5)       # точка, в которую стягивается поле

def g05_field(t, cz=0.0):
    """угли на полу: до 1.35 поле, 1.35-2.1 стягивание — всё поле равномерно сжимается к точке
    (на плёнке диск сохраняет рисунок рядов, значит сжатие однородное), с низким куполом"""
    u = seg(t, 1.35, 2.1)
    if u >= 1.0:
        return [(EC[0], 0.12, EC[1], 1.1)]
    R = 7.5 * (1 - u) ** 1.3 + 30.0 * (1 - u) ** 12       # 145.0 ~6 м · 145.2 ~3.5 · 145.4 ~1.5 · 145.55 ~0.3
    kx, kz = min(1.0, R / 6.0), min(1.0, R / 20.0)      # поле 12 м в ширину и 40 м в длину —
    hd = 0.12 * R * math.sin(math.pi * u) ** 0.7        # поле не плоское: на плёнке 145.0-145.4 это низкий КУПОЛ
    pts = []
    for i, (x, z, s, j) in enumerate(ember_points()):
        if ((i * 7919) % 1000) / 1000.0 < 0.9 * u ** 1.2: continue   # к точке угли редеют
        dx, dz = (x - EC[0]) * kx, (z - EC[1]) * kz
        rr = math.hypot(dx, dz)
        y = 0.05 + hd * math.sqrt(max(0.0, 1 - (rr / max(R, 1e-3)) ** 2)) if u > 0 else 0.05
        near = clamp01((EC[1] + dz - cz - 2.5) / 2.5)      # купол только впереди камеры, не над головой
        y = 0.05 + (y - 0.05) * near
        pts.append((EC[0] + dx, y, EC[1] + dz, s * (1 + 0.4 * math.sin(math.pi * u)) * (1 - 0.5 * u)))
    if u > 0.6:                                            # яркое ядро, в которое всё сходится
        pts.append((EC[0], 0.10, EC[1], 0.3 + 1.6 * (u - 0.6)))
    return pts

_G05 = {}
def _g05_words():
    if not _G05:
        _G05["and"] = row_tiles("AND THEY", 200, color=DARK, cond=0.72)
    return _G05

def g05(t):
    """табло спускается сверху на двух тросах, проскакивает и качается; поле углей
    стягивается в точку, камера опускается к ней"""
    # камера на плёнке: до 144.8 ровно, 144.8-145.5 поднимается и наклоняется к диску (горизонт
    # с 50 % уходит к ~20 %), с 145.8 наклон сильнее — табло уходит из кадра вверх
    cz = 0.55 * t
    a, b = smooth(seg(t, 1.3, 2.0)), smooth(seg(t, 2.3, 3.0))
    cy = 1.55 + 0.95 * a - 0.3 * b
    cam = PCam(0.0, cy, cz, 0.0, math.radians(9.5) * a + math.radians(10.5) * b)
    img = room(cam)
    far_wall(img, cam)
    # --- слова слева, на тросах (Oswald, как hang_block в библиотеке) ---
    Zt = 7.3
    rows = [[("THE", -1), ("AIs", -1), ("WORKED", 0.07), ("TOGETHER", 0.27)],
            [("FOR", 0.63), ("EIGHTY-EIGHT", 0.80)],
            [("HOURS", 1.27), ("STRAIGHT.", 1.67)]]
    yellow = {"TOGETHER", "EIGHTY-EIGHT"}
    lines, hl, idx = [], set(), 0
    for r in rows:
        ws = [w for w, t0 in r if t >= t0]
        if not ws: continue
        for w in ws:
            if w in yellow: hl.add(idx)
            idx += 1
        lines.append(" ".join(ws))
    if lines:
        hang_block(img, cam, lines, hl, (-2.6, 3.3, Zt), 0.30, fsize=170, wires=True, depth=0.05)
    # --- поле углей ---
    img = ember_field(img, cam, g05_field(t, cz), t, glow=1.1)
    # --- табло ---
    t0 = 0.667
    PW, PH = 1.6, 0.46
    X, Yf, Zp = 0.92, 2.60, 6.7
    if t >= t0:
        drop = (3.53 - Yf) * math.exp(-45.0 * (t - t0))
        over = 0.08 * PH * (seg(t, t0 + 0.05, t0 + 0.13) * (1 - smooth(seg(t, t0 + 0.13, t0 + 0.5))))
        Y = Yf + drop - over
        roll = math.radians(1.5) * math.cos(2 * math.pi * (t - 0.7) / 3.0)
        yaw = math.radians(1.0) * math.sin(2 * math.pi * (t - 0.7) / 3.7)
        s, col, sm = clock_value(t)
        tex = clock_tex(s, col, smear=sm)
        c = quad((X, Y, Zp), PW, PH, yaw=yaw, roll=roll)
        if visible(cam, c):
            for f in (0.12, 0.88):
                top = (X - PW / 2 + PW * f, CEIL, Zp)
                bot = (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1] + (c[1][1] - c[0][1]) * f,
                       c[0][2] + (c[1][2] - c[0][2]) * f)
                rope(img, cam, top, bot, width=2)
            vol(img, cam, c, tex, depth=0.06, steps=3, side=(40, 40, 42), op=1.0)
    # --- AND THEY над точкой ---
    wd = _g05_words()
    word_row(img, cam, t, wd["and"], [2.9, 3.03], EC[0] - 0.85, 0.36, EC[1], 0.36,
             depth=0.05, side=DARK_SIDE)
    return img

# ----------------------------------------------------------------- G48

def box(img, cam, x, z, w, h, d, col, op=1.0):
    """параллелепипед на полу: грани верх, бок к центру, фронт"""
    x0, x1 = x - w / 2, x + w / 2
    z0, z1 = z, z + d
    front = [(x0, h, z0), (x1, h, z0), (x1, 0, z0), (x0, 0, z0)]
    top = [(x0, h, z1), (x1, h, z1), (x1, h, z0), (x0, h, z0)]
    if x > 0: side = [(x0, h, z1), (x0, h, z0), (x0, 0, z0), (x0, 0, z1)]
    else:     side = [(x1, h, z0), (x1, h, z1), (x1, 0, z1), (x1, 0, z0)]
    if not visible(cam, front): return
    r, g, b = col
    def solid(k): return Image.new("RGBA", (32, 32), (int(r * k), int(g * k), int(b * k), 255))
    sh = [(x0 + 0.4, 0.01, z0 + 0.5), (x1 + 0.4, 0.01, z1 + 0.5), (x1, 0.01, z1), (x0, 0.01, z0)]
    paste_quad(img, Image.new("RGBA", (32, 32), (40, 38, 36, int(60 * op))), [cam.proj(q) for q in sh])
    paste_quad(img, solid(1.0), [cam.proj(q) for q in top], op)
    paste_quad(img, solid(0.80), [cam.proj(q) for q in side], op)
    paste_quad(img, solid(0.92), [cam.proj(q) for q in front], op)

def stack(img, cam, x, z, w, h, d, col, n=5):
    """стопка блоков с тонкими швами"""
    for i in range(n):
        hh = h / n
        x0, x1 = x - w / 2, x + w / 2
        y0, y1 = i * hh, (i + 1) * hh - 0.02
        front = [(x0, y1, z), (x1, y1, z), (x1, y0, z), (x0, y0, z)]
        top = [(x0, y1, z + d), (x1, y1, z + d), (x1, y1, z), (x0, y1, z)]
        side = ([(x0, y1, z + d), (x0, y1, z), (x0, y0, z), (x0, y0, z + d)] if x > 0 else
                [(x1, y1, z), (x1, y1, z + d), (x1, y0, z + d), (x1, y0, z)])
        if not visible(cam, front): return
        r, g, b = col
        def solid(k): return Image.new("RGBA", (16, 16), (int(r * k), int(g * k), int(b * k), 255))
        paste_quad(img, solid(1.0), [cam.proj(q) for q in top])
        paste_quad(img, solid(0.80), [cam.proj(q) for q in side])
        paste_quad(img, solid(0.92), [cam.proj(q) for q in front])

def globe_tex(t, px=360):
    """жёлтый глобус с тёмными материками, крутится — пятна едут по долготе"""
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, px - 3, px - 3], fill=(242, 196, 40, 255))
    R = px / 2 - 3
    lay = Image.new("RGBA", (px, px), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    rng = np.random.default_rng(3)
    for i in range(14):
        lon = rng.uniform(0, 2 * math.pi); lat = rng.uniform(-1.0, 1.0)
        rw = rng.uniform(0.10, 0.24); rh = rng.uniform(0.10, 0.22)
        a = lon + t * 0.5
        cz = math.cos(a)
        if cz <= 0.05: continue
        cx = px / 2 + R * math.sin(a) * math.cos(lat)
        cy = px / 2 - R * math.sin(lat) * 0.95
        ww = R * rw * cz; hh = R * rh
        ld.ellipse([cx - ww, cy - hh, cx + ww, cy + hh], fill=(44, 40, 38, 255))
    mask = Image.new("L", (px, px), 0)
    ImageDraw.Draw(mask).ellipse([4, 4, px - 5, px - 5], fill=255)
    lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.split()[3]), np.asarray(mask))))
    img.alpha_composite(lay)
    # тень по правому краю
    sh = Image.new("RGBA", (px, px), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.ellipse([px * 0.25, px * 0.1, px * 1.15, px * 1.05], fill=(60, 40, 10, 70))
    sh.putalpha(Image.fromarray(np.minimum(np.asarray(sh.split()[3]), np.asarray(mask))))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    return img

def wire_cube(img, cam, x, z, size, col=(60, 60, 64, 255), wd=4):
    s = size / 2
    v = [(x - s, 0, z), (x + s, 0, z), (x + s, 0, z + size), (x - s, 0, z + size),
         (x - s, size, z), (x + s, size, z), (x + s, size, z + size), (x - s, size, z + size)]
    p = [cam.proj(q) for q in v]
    d = ImageDraw.Draw(img, "RGBA")
    for e0, e1 in ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)):
        d.line([(p[e0][0], p[e0][1]), (p[e1][0], p[e1][1])], fill=col, width=wd)

_G48 = {}
def _g48_tex():
    if not _G48:
        _G48["here"] = row_tiles("IT'S HERE.", 200, color=(36, 33, 32, 255), cond=0.78)
        _G48["day"] = text_tex(["DAY 243"], fsize=120, fname="ArialBlack.ttf", hl={1},
                               color=(36, 33, 32, 255), pad=14)
        _G48["one"] = row_tiles("ONE MORE THING.", 200, color=DARK, cond=0.74)
        _G48["did"] = row_tiles("I DIDN'T MAKE THIS VIDEO.", 200, color=(40, 37, 36, 255), cond=0.78)
    return _G48

def g48_inner(t):
    """сцена ВНУТРИ картины: тот же зал, большое IT'S HERE. на тросах, предметы на полу,
    уголь-солнце справа; живёт — камера едет, уголь дышит, глобус крутится"""
    cam = Cam(0.0, 1.55, 0.12 * t, 0.0)
    img = room(cam)
    tx = _g48_tex()
    Zi = 9.0 + 0.12 * 0  # мир внутри неподвижен, едет камера
    # IT'S HERE.: x 15-88 %, капитель 8-37 % высоты кадра на d=9 → ширина 6.4 м, капитель 1.43
    word_row(img, cam, t, tx["here"], [-1, -1], -3.1, 2.91, Zi, row_cap(tx["here"], 6.4),
             depth=0.28, side=(22, 20, 19), wires=2)
    # предметы на полу, d≈11.3
    Zo = 11.3
    stack(img, cam, -3.2, Zo, 0.75, 1.55, 0.6, (236, 237, 239), n=6)
    stack(img, cam, -2.0, Zo, 0.45, 1.7, 0.45, (242, 196, 40), n=7)
    box(img, cam, 3.35, Zo + 1.5, 0.45, 2.4, 0.45, (92, 64, 44))
    bank = maket_tex("bank", 400)
    cb = quad((3.0, 0.42, Zo), 1.5, 0.84)
    paste_quad(img, bank, [cam.proj(p) for p in cb])
    wire_cube(img, cam, 1.1, Zo, 1.15)
    gl = globe_tex(t)
    cg = quad((-0.9, 0.56, Zo), 1.1, 1.1)
    # тень глобуса
    sh = Image.new("RGBA", (64, 64), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([8, 8, 56, 56], fill=(40, 38, 36, 80))
    sq = [(-1.5, 0.01, Zo + 0.3), (-0.3, 0.01, Zo + 0.3), (-0.2, 0.01, Zo - 0.4), (-1.6, 0.01, Zo - 0.4)]
    paste_quad(img, sh.filter(ImageFilter.GaussianBlur(5)), [cam.proj(p) for p in sq])
    paste_quad(img, gl, [cam.proj(p) for p in cg])
    # DAY 243 — карточка у нижней кромки, d≈7.4
    day = tx["day"]
    hday = 0.42; wday = hday * day.size[0] / day.size[1]
    cd = quad((0.0, 0.26, 7.4), wday, hday)
    vol(img, cam, cd, day, depth=0.05, steps=2, side=(120, 120, 124))
    # уголь-солнце справа: x 93 %, y 33 % на d=9
    img = embers(img, cam, [(3.7, 2.39, 9.0, 1.35)], t, glow=1.2)
    return img

ZP, WP, HP, YC = 12.0, 3.12, 1.755, 1.99       # картина: где висит, размер, центр по высоте

def g48(t):
    """камера отъезжает — зал оказывается картиной в раме, в этом же зале; под рамой плашка
    со счётчиком кадров, внутри рамы кадр продолжает жить"""
    inner = g48_inner(t)
    if t < 0.5:
        return inner
    # --- внешняя камера: 600 мс отъезда S-образно, потом медленно дальше ---
    # ширина картины на экране: 100 % → 42 % за 600 мс (S-образно), потом → 36 % к концу
    wf = 1.0 - 0.58 * smooth(seg(t, 0.5, 1.1)) - 0.06 * seg(t, 1.1, 4.0) ** 0.9
    d = 3.2 / wf
    cy = YC + (1.55 - YC) * smooth(seg(t, 0.6, 1.15))   # центр картины 50 % → 47 % → 40 %
    cam = Cam(0.0, cy, ZP - d, 0.0)
    img = room(cam)
    # --- картина: рамка на самой картинке, уменьшение заранее (иначе лесенка) ---
    c = quad((0.0, YC, ZP), WP, HP)
    pts = [cam.proj(p) for p in c]
    bw = max(p[0] for p in pts) - min(p[0] for p in pts)
    pic = inner
    bd = ImageDraw.Draw(pic); bd.rectangle([0, 0, W - 1, H - 1], outline=(28, 27, 26, 255), width=7)
    if bw < W * 0.98:
        k = max(bw / W, 0.05)
        pic = pic.resize((max(8, int(W * k)), max(8, int(H * k))), Image.LANCZOS)
    for f in (0.22, 0.76):
        rope(img, cam, (-WP / 2 + WP * f, CEIL, ZP), (-WP / 2 + WP * f, YC + HP / 2, ZP), width=2)
    # плашка FRAME под рамой
    n = int(round((261.0 + t) * 30))
    pt = plate_frame(f"{n:,}")
    pw, ph = 2.03, 0.36
    cpl = quad((0.0, 0.89, ZP), pw, ph)
    for f in (0.2, 0.8):
        rope(img, cam, (-pw / 2 + pw * f, YC - HP / 2, ZP), (-pw / 2 + pw * f, 0.89 + ph / 2, ZP), width=2)
    vol(img, cam, cpl, pt, depth=0.05, steps=2, side=(40, 40, 42))
    vol(img, cam, c, pic, depth=0.05, steps=2, side=(60, 60, 62))
    # --- ONE MORE THING. над рамой, в её плоскости; улетает вверх на 2.2 ---
    tx = _g48_tex()
    fly = 3.0 * seg(t, 2.2, 2.3) ** 2
    if t < 2.3:
        word_row(img, cam, t, tx["one"], [1.17, 1.30, 1.63], -1.5, 3.22, ZP, row_cap(tx["one"], 2.4),
                 depth=0.04, side=DARK_SIDE, dy=fly)
    # --- I DIDN'T MAKE THIS VIDEO. стоит на полу перед картиной ---
    word_row(img, cam, t, tx["did"], [2.53, 2.87, 3.10, 3.43, 3.67], -2.15, 0.0, ZP - 1.1,
             row_cap(tx["did"], 4.3), depth=0.22, side=(22, 20, 19), floor=True, shadow=True)
    return img

def plate_frame(num, px=1300):
    h = int(px * 0.153)
    img = Image.new("RGBA", (px, h), (22, 21, 20, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, px - 1, h - 1], outline=(70, 70, 72, 255), width=4)
    f = font("Oswald-Bold.ttf", int(h * 0.66))
    d.text((px * 0.06, h * 0.12), "FRAME", font=f, fill=(242, 242, 242, 255))
    x = px * 0.50
    for ch in num:
        cw = px * (0.03 if ch == "," else 0.085)
        b = d.textbbox((0, 0), ch, font=f)
        d.text((x + (cw - (b[2] - b[0])) / 2 - b[0], h * 0.12), ch, font=f, fill=YEL)
        if ch != ",":
            d.line([(x + cw * 0.1, h * 0.52), (x + cw * 0.9, h * 0.52)], fill=(22, 21, 20, 255), width=4)
        x += cw
    return img

SCENES = {"G05": (g05, 4.5), "G48": (g48, 4.0)}

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
