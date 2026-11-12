# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть J: G47, G18, G44 — «счётчик добегает»).
Один кадр: ZAL_FRAME=1.1 python3 shard_fable.py G47 k.png

Числа сняты с плёнки покадрово (polosy/G47_vhod, G47_sbor, G47_plashka, G47_stop,
G18_vhod, G44_vhod, G44_plashka, сетки G47/G18/G44_setka):

  G47  база клипа 144.167. Плашка 00:00:00 ПАДАЕТ сверху за 3 кадра (144.200 видна
       высоко и с креном, 144.233 ниже цели, 144.267 села) и держит нули 4 кадра
       (до 144.367). Бег 144.383 → 145.250: 144.400 «00:33:36» · 144.433 «33:23:57»
       · 144.500 «55:57:17» · 144.600 «62:77:70» · 144.700 «70:15:43» ·
       144.767 часы встали «87» · 144.800 «82:33:53» (смаз) · 145.000 «87:29:13» ·
       145.033 десятки минут «5» · 145.100 «87:52:14» · 145.200 «87:59:52» ·
       145.233 «87:59:50» · 145.267 «88:00:00» ЖЁЛТЫМ, резко, без доката.
       Ход — экспонента: остаток до 88:00:00 ≈ exp(-10·u), u — доля бега;
       часы встают на 45 %, десятки минут на 75 %, секунды крутятся до конца.
       Слова: FOR 144.200 · EIGHTY-EIGHT (маркер) 144.300 · HOURS 144.767 ·
       STRAIGHT. 145.167 · растворяются 145.733-145.800 · AND THEY 146.400-146.600.
       Поле углей: до 145.0 — весь пол; 145.0 → 145.72 стягивается в точку
       (радиус 1.0 · 0.9 (145.2) · 0.75 (145.3) · 0.55 (145.4) · 0.4 (145.5) ·
       0.2 (145.6) · 0.08 (145.67) · точка 145.73) — разгон, r ≈ 1 − u^1.8.
       Камера одновременно наклоняется вниз (горизонт 17 % кадра на 144.3, выше
       кадра с 145.0) и идёт вперёд: плашка 0.27 → 0.40 ширины кадра к 146.0.
  G18  в задании кусок 225.0, но «процент на треть кадра + лист» на плёнке стоит
       227.867-229.4+ (на 225.0 — столбики Швеции и чужой эфир). База 227.867.
       Всё появляется ОДНИМ кадром (227.833 ещё эфир, 227.867 уже всё); дальше
       камера наезжает: «70%» 23 % высоты кадра (228.0) → 27 % (229.0).
       Сетка 228.5: «70%» x 36-62 %, y 5-28 %; строки y 30-36 и 37-43 (кегль
       вчетверо меньше); лист x 20-80 %, y 50-79 %, правый край дальше (yaw).
       Маркер на листе по словам: Voters 228.433 · reject 228.567 · data 228.667
       · centers 228.733; строка источника внизу 228.167.
  G44  база 157.0. Столб-шкала x 25 %, основание y 76 % → d≈10.9 м, X≈-2.65;
       плашка «<1%» 19 % × 19 % кадра (2.0 × 1.14 м), центр x 45.5 %, y 65.5 %,
       низ на полу вплотную справа от столба. Вход 157.950 → ~158.42 (≈470 мс):
       157.967 плашка справа-выше на ~0.9 м и крупнее (ближе), крен −8°;
       158.000 ниже и левее цели (перелёт ~20 %), 158.067 почти на месте,
       дрожь крена до 158.2. Слова: BACK 156.2 · THEN, 156.4 · снимаются 157.85 ·
       LESS 157.95 · THAN 158.217 · ONE (маркер) 158.45 · PERCENT (маркер) 158.7 ·
       OF 159.1 · THE 159.2 · WORK 159.4 · OF 159.7 · BUILDING 159.9 · NEW 160.1 ·
       AI 160.4 · SYSTEMS. 160.6. Источник внизу с 158.35.
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import *
from shard_fable_a import pop, tiles_crop, place_words, extrude_dir, line_frame, visible

FPS = 30
DT = 1.0 / FPS
DARK = (30, 27, 26, 255)
DARK_SIDE = (16, 14, 13)
YEL = (246, 200, 48, 255)
CREAM = (238, 232, 216, 255)

_CAP = {}
def cap_ratio(fname):
    """высота капители в долях кегля — мерим шрифтом, а не прикидываем"""
    if fname not in _CAP:
        d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
        b = d.textbbox((0, 0), "H", font=font(fname, 200))
        _CAP[fname] = (b[3] - b[1]) / 200.0
    return _CAP[fname]

# ----------------------------------------------------------------- камера с наклоном

class CamP(Cam):
    """та же камера, но с наклоном вниз (pitch, радианы, >0 — смотрим в пол)"""
    def __init__(s, x=0.0, y=1.55, z=0.0, yaw=0.0, pitch=0.0):
        Cam.__init__(s, x, y, z, yaw)
        s.pitch = pitch
    def proj(s, p):
        dx, dy, dz = p[0] - s.x, p[1] - s.y, p[2] - s.z
        if s.yaw:
            c, si = math.cos(-s.yaw), math.sin(-s.yaw)
            dx, dz = dx * c - dz * si, dx * si + dz * c
        if s.pitch:
            c, si = math.cos(s.pitch), math.sin(s.pitch)
            dy, dz = dy * c + dz * si, dz * c - dy * si
        if dz < 0.08: dz = 0.08
        k = F / dz
        return (W / 2 + dx * k, H / 2 - dy * k, dz)

def room_p(cam, windows=True, shafts=True, ropes=True, shaft_alpha=120):
    """зал под наклонённую камеру: пол — проецируемый четырёхугольник, а не половина кадра"""
    img = Image.new("RGBA", (W, H), (230, 232, 235, 255))
    d = ImageDraw.Draw(img, "RGBA")
    zn = cam.z + 0.12
    fl = [cam.proj((-60, 0.0, zn)), cam.proj((60, 0.0, zn)),
          cam.proj((60, 0.0, cam.z + FAR)), cam.proj((-60, 0.0, cam.z + FAR))]
    d.polygon([(p[0], p[1]) for p in fl], fill=(197, 200, 204, 255))
    for sx in (-1, 1):
        p = [cam.proj((sx * WALL, CEIL, cam.z + 2.0)), cam.proj((sx * WALL, CEIL, cam.z + FAR)),
             cam.proj((sx * WALL, 0.0, cam.z + FAR)), cam.proj((sx * WALL, 0.0, cam.z + 2.0))]
        d.polygon([(q[0], q[1]) for q in p], fill=(222, 225, 229, 255))
    if windows:
        z0 = math.floor((cam.z + 3) / 7.0) * 7.0
        for i in range(10):
            zz = z0 + i * 7.0
            for sx in (-1, 1):
                p = [cam.proj((sx * WALL, 3.75, zz)), cam.proj((sx * WALL, 3.75, zz + 3.1)),
                     cam.proj((sx * WALL, 1.15, zz + 3.1)), cam.proj((sx * WALL, 1.15, zz))]
                d.polygon([(q[0], q[1]) for q in p], fill=(251, 252, 253, 255))
                for k in range(1, 4):
                    yy = 1.15 + 2.6 * k / 4
                    a = cam.proj((sx * WALL, yy, zz)); b = cam.proj((sx * WALL, yy, zz + 3.1))
                    d.line([(a[0], a[1]), (b[0], b[1])], fill=(226, 229, 233, 255), width=2)
    if shafts:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay, "RGBA")
        z0 = math.floor((cam.z + 3) / 7.0) * 7.0
        for i in range(9):
            zz = z0 + i * 7.0
            for sx in (-1, 1):
                p = [cam.proj((sx * (WALL - 0.2), 0.0, zz + 0.6)),
                     cam.proj((sx * (WALL - 0.2), 0.0, zz + 3.5)),
                     cam.proj((sx * (WALL - 3.4), 0.0, zz + 5.2)),
                     cam.proj((sx * (WALL - 3.4), 0.0, zz + 2.3))]
                dl.polygon([(q[0], q[1]) for q in p], fill=(255, 255, 255, int(shaft_alpha)))
        lay = lay.filter(ImageFilter.GaussianBlur(9))
        img.alpha_composite(lay)
    if ropes:
        rng = np.random.default_rng(5)
        dr = ImageDraw.Draw(img, "RGBA")
        z0 = math.floor((cam.z + 4) / 3.0) * 3.0
        for i in range(26):
            zz = z0 + (i % 13) * 3.0 + float(rng.uniform(-1.0, 1.0))
            xx = float(rng.uniform(-4.6, 4.6))
            yy = float(rng.uniform(0.9, 2.4))
            if zz - cam.z < 1.5: continue
            a = cam.proj((xx, CEIL, zz)); b = cam.proj((xx, yy, zz))
            dr.line([(a[0], a[1]), (b[0], b[1])], fill=(150, 152, 156, 255), width=1)
    return img

# ----------------------------------------------------------------- общие вещи

def words_block(lines, cap_m, fname="Oswald-Bold.ttf", cond=1.0, hl=None, color=DARK, fsize=200):
    """плитки строк + метров на пиксель, чтобы капитель была cap_m"""
    tiles = tiles_crop(lines, fsize, hl=hl, color=color, fname=fname, cond=cond)
    return tiles, cap_m / (cap_ratio(fname) * fsize)

def put_plate(img, cam, tex, center, w, h, yaw=0.0, roll=0.0, depth=0.08, side=(40, 40, 42),
              wires=None, opacity=1.0):
    """плоская табличка в пространстве с объёмом вдоль нормали; wires — доли ширины для тросов"""
    c = quad(center, w, h, yaw, roll)
    if not visible(cam, c, 0.25): return
    ux, nz = line_frame(center, yaw)
    if wires:
        for f in wires:
            top = (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1] + (c[1][1] - c[0][1]) * f,
                   c[0][2] + (c[1][2] - c[0][2]) * f)
            wire(img, cam, top, color=(96, 98, 102, 230), width=2)
    extrude_dir(img, cam, c, tex, depth, nz, steps=6, side=side, opacity=opacity)

def blur_fade(img, lay, k):
    """растворение слоя: смаз + прозрачность, k 0..1"""
    if k <= 0: img.alpha_composite(lay); return
    if k >= 1: return
    b = lay.filter(ImageFilter.GaussianBlur(2 + 18 * k))
    a = b.split()[3].point(lambda v: int(v * (1 - k)))
    b.putalpha(a)
    img.alpha_composite(b)

# ----------------------------------------------------------------- угли: быстрый слой

_SPR_CACHE = {}
def _spr(size):
    if size not in _SPR_CACHE:
        rgb, al = Z._sprite()
        s = np.array(Image.fromarray(rgb.astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32)
        a = np.array(Image.fromarray((al * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32) / 255.0
        _SPR_CACHE[size] = (s, a)
    return _SPR_CACHE[size]

def ember_layer(img, cam, pts, t, glow=0.9, core_k=2.6, halo_blur=40):
    """как zal_core.embers, но спрайты кэшируются по размеру — тысячи углей за доли секунды.
    pts — (x, y, z, s[, яркость])"""
    add = np.zeros((H, W, 3), np.float32)
    ca = np.zeros((H, W, 1), np.float32)
    for i, p in enumerate(pts):
        x, y, z, s = p[:4]
        br = p[4] if len(p) > 4 else 1.0
        pulse = (0.82 + 0.18 * math.sin(t * 3.4 + i * 1.7)) * br
        px, py, dz = cam.proj((x, y, z))
        if dz < 0.3: continue
        size = int(s * F / dz * pulse)
        if size < 3: size = 3
        if size > 1400 or px < -size or px > W + size or py < -size or py > H + size: continue
        size = max(4, (size // 2) * 2)
        sp, sa = _spr(size)
        x0, y0 = int(px - size / 2), int(py - size / 2)
        X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(W, x0 + size), min(H, y0 + size)
        if X1 <= X0 or Y1 <= Y0: continue
        sub = sp[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        suba = sa[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][..., None]
        add[Y0:Y1, X0:X1] += sub * suba * pulse * 0.55
        ca[Y0:Y1, X0:X1] = np.maximum(ca[Y0:Y1, X0:X1], np.clip(suba * core_k - 0.45, 0, 1) * min(1.0, br))
    if ca.max() <= 0 and add.max() <= 0:
        return img
    add = np.minimum(add, 150.0)                      # тысячи углей не выжигают кадр в белое
    halo = np.asarray(Image.fromarray(np.clip(add, 0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(halo_blur)), np.float32)
    arr = np.asarray(img.convert("RGB"), np.float32)
    core = np.array([255.0, 168.0, 72.0], np.float32)
    arr = arr * (1 - ca) + core * ca
    arr = arr + add * 0.35 + halo * glow
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

def glow_spot(img, cam, pos, radius_m, strength=1.0, color=(255, 150, 48), core=0.22):
    """большое пятно свечения вокруг точки: оранжевый ореол с квадратичным спадом и белое ядро"""
    px, py, dz = cam.proj(pos)
    if dz < 0.3: return img
    R = int(radius_m * F / dz)
    if R < 4: return img
    x0, y0 = int(px - R), int(py - R)
    X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(W, x0 + 2 * R), min(H, y0 + 2 * R)
    if X1 <= X0 or Y1 <= Y0: return img
    yy, xx = np.mgrid[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    r = np.sqrt((xx - R) ** 2 + (yy - R) ** 2) / R
    fall = np.clip(1 - r, 0, 1) ** 2.2
    wht = np.clip(1 - r / core, 0, 1) ** 1.2
    arr = np.asarray(img.convert("RGB"), np.float32)
    sub = arr[Y0:Y1, X0:X1]
    col = np.array(color, np.float32)
    f = (fall * strength)[..., None]
    sub = sub * (1 - f) + col * f                              # к оранжевому, а не в белое
    sub = sub * (1 - wht[..., None]) + np.array([255, 236, 200], np.float32) * wht[..., None]
    arr[Y0:Y1, X0:X1] = sub
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

# ================================================================= G47: таймер добегает до числа

T88 = 88 * 3600.0                      # 88:00:00 в секундах
G47_BASE = 144.167
G47_T = dict(drop=0.033, hold=0.233, run0=0.217, run1=1.083,     # бег 144.383 → 145.250
             sbor0=0.833, sbor1=1.555, words_out=1.520, and0=2.233, and1=2.433)

def counter_value(t):
    """секунды на табло в момент t: 0 до старта, экспоненциальный ход, точно 88:00:00 на стопе"""
    r0, r1 = G47_T["run0"], G47_T["run1"]
    if t < r0: return 0.0
    if t >= r1: return T88
    u = (t - r0) / (r1 - r0)
    # первые два кадра — разгон (144.400 ещё «00:33:36»), дальше остаток падает как exp(-10u)
    u2 = u * (0.3 + 0.7 * clamp01(u / 0.35))
    k = 10.0
    return T88 * (1 - math.exp(-k * u2)) / (1 - math.exp(-k))

_CNT = {}
def _cnt_glyphs(fsize):
    """цифры 0-9 и двоеточие одним кеглем; все цифры в ячейке одной ширины"""
    if fsize in _CNT: return _CNT[fsize]
    f = font("Oswald-Bold.ttf", fsize)
    d0 = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    bbs = [d0.textbbox((0, 0), c, font=f) for c in "0123456789"]
    cw = int(max(b[2] - b[0] for b in bbs) * 1.18)
    ch = int(max(b[3] - b[1] for b in bbs) * 1.30)
    gl = []
    for c, b in zip("0123456789", bbs):
        im = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(im).text(((cw - (b[2] - b[0])) / 2 - b[0], (ch - (b[3] - b[1])) / 2 - b[1]),
                                c, font=f, fill=255)
        gl.append(np.asarray(im, np.float32) / 255.0)
    _CNT[fsize] = (cw, ch, gl)
    return _CNT[fsize]

# ячейки табло: (делитель в секундах, основание)
CELLS = [(36000, 10), (3600, 10), None, (600, 6), (60, 10), None, (10, 6), (1, 10)]

def cell_value(V, unit, base):
    """одометр: цифра стоит, пока младшие не докрутились; катится вверх на последних 15 %"""
    n = int(V // unit) % base
    r = (V % unit) / unit
    frac = clamp01((r - 0.85) / 0.15)
    return n, frac

def counter_tex(t, px=1240, py=420):
    """табло: чёрное поле в сером ободе, шесть ячеек с катящимися вверх цифрами,
    смаз — усреднение 8 подкадров внутри 1/30 с; после стопа цифры жёлтые"""
    stopped = t >= G47_T["run1"]
    img = Image.new("RGBA", (px, py), (84, 86, 90, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([12, 12, px - 13, py - 13], fill=(12, 12, 14, 255))
    d.rectangle([12, py - 26, px - 13, py - 13], fill=(30, 30, 33, 255))
    fsize = int(py * 0.68)
    cw, ch, gl = _cnt_glyphs(fsize)
    colon_w = int(cw * 0.42)
    total = 6 * cw + 2 * colon_w
    if total > px - 60:                                   # цифры не лезут — ужимаем кегль
        fsize = int(fsize * (px - 60) / total)
        cw, ch, gl = _cnt_glyphs(fsize)
        colon_w = int(cw * 0.42); total = 6 * cw + 2 * colon_w
    x = (px - total) / 2
    y0 = (py - ch) / 2
    samples = [t] if stopped or t < G47_T["run0"] else [t - DT * 0.5 + DT * (i + 0.5) / 8 for i in range(8)]
    vals = [counter_value(s) for s in samples]
    col = YEL if stopped else CREAM
    acc_full = np.zeros((py, px), np.float32)
    for cell in CELLS:
        if cell is None:
            cx = x + colon_w / 2
            r = ch * 0.055
            for cy in (y0 + ch * 0.36, y0 + ch * 0.64):
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
            x += colon_w
            continue
        unit, base = cell
        acc = np.zeros((ch, cw), np.float32)
        for V in vals:
            n, frac = cell_value(V, unit, base)
            off = int(round(frac * ch))
            if off == 0:
                acc += gl[n]
            else:
                # текущая уходит вверх, следующая входит снизу
                acc[:ch - off] += gl[n][off:]
                acc[ch - off:] += gl[(n + 1) % base][:off]
        acc /= len(vals)
        acc_full[int(y0):int(y0) + ch, int(x):int(x) + cw] = np.clip(acc, 0, 1)
        x += cw
    a = Image.fromarray((acc_full * 255).astype(np.uint8))
    lay = Image.new("RGBA", (px, py), col); lay.putalpha(a)
    img.alpha_composite(lay)
    return img

_FIELD = None
def ember_field_pts():
    """поле углей на полу: ряды вдоль изогнутых линий, с тёмными протоками"""
    global _FIELD
    if _FIELD is None:
        rng = np.random.default_rng(47)
        pts = []
        x = -11.0
        while x < 11.0:
            z = -11.0
            while z < 15.0:
                xx = x + 0.9 * math.sin(0.45 * z + 1.1 * math.sin(0.23 * x)) + rng.uniform(-0.05, 0.05)
                zz = z + rng.uniform(-0.05, 0.05)
                chan = math.sin(0.9 * xx + 1.2 * math.sin(0.35 * zz) + 0.3 * zz)
                if abs(chan) > 0.16:                              # тонкие изогнутые протоки
                    pts.append((xx, zz, rng.uniform(0.7, 1.0)))
                z += 0.26
            x += 0.26
        _FIELD = pts
    return _FIELD

def g47(t):
    """плашка падает сверху, цифры срываются вверх и встают на 88:00:00; поле углей — в точку"""
    # камера: наклон 10° → 28° (горизонт уходит за верх кадра с 145.0), ход вперёд 2.3 м
    # камера поднимается с 1.55 до 4.0 м и наклоняется 10° → 37° (сетка 146.0: плашка видна
    # сверху, её верхняя грань открыта; горизонт уходит за верх кадра с 145.0), ход вперёд 2.3 м
    k = seg(t, 0.60, 1.20); k = k * k * (3 - 2 * k)
    pitch = math.radians(10.0 + 27.0 * k)
    cy = 1.55 + 2.45 * k
    cz = 2.3 * out_cubic(seg(t, 0.50, 1.60))
    cam = CamP(0.0, cy, cz, 0.0, pitch)
    img = room_p(cam, shaft_alpha=120 * (1 - 0.8 * k))
    # --- поле углей (центр стягивания — на полу в 6.4 м) ---
    # радиус с плёнки: 145.0 ≈ 3.0 м · 145.3 ≈ 2.1 · 145.5 ≈ 1.1 · 145.6 ≈ 0.55 · 145.72 точка;
    # до 145.0 поле уходит с дальнего плана (11 м → 3 м за 144.6-145.0)
    ZC = 6.4
    u = seg(t, G47_T["sbor0"], G47_T["sbor1"])
    if t < G47_T["sbor0"]:
        R = 11.0 - 8.0 * seg(t, 0.43, G47_T["sbor0"]) ** 2
    else:
        R = 3.0 * (1.0 - u ** 1.5)
    r = R / 11.0
    pts = []
    if R > 0.12:
        for (x, z, b) in ember_field_pts():
            if (x * x + z * z) > 11.0 ** 2: continue
            pts.append((x * r, 0.05, ZC + z * r, 0.20 * (0.55 + 0.45 * r), b))
        img = ember_layer(img, cam, pts, t, glow=0.8, core_k=2.8, halo_blur=30)
    else:
        # одна точка: белое ядро и широкий ореол
        img = glow_spot(img, cam, (0.0, 0.03, ZC), 0.95, strength=0.9, core=0.07, color=(255, 140, 40))
        img = glow_spot(img, cam, (0.0, 0.03, ZC), 0.28, strength=0.9, core=0.30, color=(255, 170, 60))
    # --- слова слева: FOR [EIGHTY-EIGHT] / HOURS STRAIGHT. ---
    words, sc = words_block(["FOR EIGHTY-EIGHT", "HOURS STRAIGHT."], 0.34, cond=0.70, hl={1})
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    place_words(lay, cam, t, words, (-1.15, 1.08, 7.0), math.radians(14.0), sc,
                [0.033, 0.133, 0.600, 1.000], depth=0.10, side=DARK_SIDE)
    blur_fade(img, lay, seg(t, G47_T["words_out"], G47_T["words_out"] + 0.067))
    # --- AND THEY: бледно на 146.4, в полную силу к 146.6 ---
    if t >= G47_T["and0"]:
        w2, sc2 = words_block(["AND THEY"], 0.40, cond=1.0)
        op = 0.25 + 0.75 * seg(t, G47_T["and0"], G47_T["and1"])
        place_words(img, cam, t, w2, (-0.35, 0.75, 6.6), 0.0, sc2, [G47_T["and0"]] * 2,
                    depth=0.08, side=DARK_SIDE, extra_op=op, k0=1.0)
    # --- плашка-табло: падает с потолка за 3 кадра, крен гаснет ---
    if t >= G47_T["drop"] - 1e-6:
        u = seg(t, G47_T["drop"], G47_T["drop"] + 0.10)
        dy = 3.2 * (1 - u * u)
        if u >= 1:
            b = seg(t, G47_T["drop"] + 0.10, G47_T["drop"] + 0.20)
            dy = -0.06 * math.sin(b * math.pi)                     # проскок вниз 6 см
        roll = math.radians(-4.0) * (1 - seg(t, G47_T["drop"], G47_T["drop"] + 0.35)) \
               * math.cos(2 * math.pi * (t - G47_T["drop"]) / 0.25)
        if t >= G47_T["run1"] and t < G47_T["run1"] + 0.07:          # удар стопа: 1 кадр вздрагивает
            roll += math.radians(1.5)
        tex = counter_tex(t)
        center = (1.05, 1.40 + dy, 7.0)
        yaw = math.radians(14.0)
        put_plate(img, cam, tex, center, 1.84, 0.62, yaw, roll, depth=0.09, side=(52, 54, 58),
                  wires=(0.18, 0.82))
        if u < 1:                                                   # смаз падения
            c2 = quad((1.05, 1.40 + dy + 0.35 * (1 - u), 7.0), 1.84, 0.62, yaw, roll)
            paste_quad(img, tex, [cam.proj(p) for p in c2], 0.25)
    return img

# ================================================================= G18: большое число во весь кадр

G18_BASE = 227.867

def sheet_fox(t, w=2000, h=540):
    """лист-подтверждение — рисуем свой: красный ярлык, заголовок с маркером по словам,
    серая подстрока, подпись, ряд кнопок"""
    img = Image.new("RGBA", (w, h), (250, 250, 249, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(212, 212, 210, 255), width=2)
    # ярлык
    tf = font("Arimo-Bold.ttf", 22)
    tag = "FOX NEWS POLL"
    tw = d.textlength(tag, font=tf)
    d.rectangle([(w - tw) / 2 - 14, 30, (w + tw) / 2 + 14, 62], fill=(214, 36, 36, 255))
    d.text(((w - tw) / 2, 34), tag, font=tf, fill=(255, 255, 255, 255))
    # заголовок, две строки, маркер по словам
    hf = font("Arimo-Bold.ttf", 84)
    lines = [("Fox News Poll: Cool your servers! Voters reject data", {6: 0.567, 7: 0.700, 8: 0.800}),
             ("centers", {0: 0.867})]
    y = 86
    for ln, marks in lines:
        ws = ln.split(" ")
        widths = [d.textlength(wd, font=hf) for wd in ws]
        sp = d.textlength(" ", font=hf)
        total = sum(widths) + sp * (len(ws) - 1)
        x = (w - total) / 2
        for i, (wd, ww) in enumerate(zip(ws, widths)):
            if i in marks and t >= marks[i] - 1e-6:
                k = seg(t, marks[i], marks[i] + 0.067)             # маркер проводится за 2 кадра
                d.rectangle([x - 6, y + 8, x - 6 + (ww + 12) * k, y + 80], fill=(252, 224, 48, 255))
            d.text((x, y), wd, font=hf, fill=(22, 22, 24, 255))
            x += ww + sp
        y += 90
    sf = font("Arimo-Bold.ttf", 30)
    s = "More favor the slow approach over rapid AI development"
    d.text(((w - d.textlength(s, font=sf)) / 2, 282), s, font=sf, fill=(132, 132, 134, 255))
    bf = font("Arimo-Bold.ttf", 22)
    s = "By Victoria Balara  ·  Fox News"
    d.text(((w - d.textlength(s, font=bf)) / 2, 330), s, font=bf, fill=(90, 90, 92, 255))
    s = "Published  Jul 27, 2026  8:00am EDT"
    d.text(((w - d.textlength(s, font=bf)) / 2, 366), s, font=bf, fill=(170, 170, 172, 255))
    # кнопки
    x0 = w * 0.30; yb = 440
    d.rounded_rectangle([x0, yb - 20, x0 + 150, yb + 20], radius=20, fill=(32, 92, 196, 255))
    d.text((x0 + 22, yb - 11), "Comments", font=bf, fill=(255, 255, 255, 255))
    cols = [(32, 92, 196), (24, 24, 26), (210, 40, 40), (32, 92, 196), (60, 60, 64), (32, 92, 196)]
    for i, c in enumerate(cols):
        cx = x0 + 200 + i * 56
        d.ellipse([cx - 20, yb - 20, cx + 20, yb + 20], fill=c + (255,))
    d.rounded_rectangle([x0 + 560, yb - 20, x0 + 820, yb + 20], radius=20, fill=(32, 92, 196, 255))
    d.text((x0 + 586, yb - 11), "Add Fox News on Google", font=bf, fill=(255, 255, 255, 255))
    return img

_G18 = {}
def _g18_words():
    if not _G18:
        _G18["num"] = words_block(["70%"], 1.06, cond=0.90)
        _G18["sub"] = words_block(["OF VOTERS OPPOSE DATA CENTERS", "IN THEIR AREA"], 0.27, cond=1.08)
    return _G18

def g18(t):
    """процент на треть кадра, пояснение вчетверо мельче, под ними свой лист; камера наезжает"""
    cz = 1.3 * (1 - (1 - clamp01(t / 4.5)) ** 2)        # наезд с торможением (228.0 → 229.0: +15 %)
    cam = Cam(0.0, 1.55, cz, 0.0)
    img = room(cam)
    wd = _g18_words()
    D = 9.0
    # всё появляется одним кадром; первый кадр — чуть крупнее и прозрачней, как у слов образца
    # всё появляется одним кадром, без пружины (227.867 — сразу в полную силу)
    place_words(img, cam, t, wd["num"][0], (-0.09, 2.92, D), 0.0, wd["num"][1], [-1.0],
                depth=0.26, side=DARK_SIDE, hang=True, wire_per_word=3, k0=1.0)
    place_words(img, cam, t, wd["sub"][0], (0.0, 2.02, D), 0.0, wd["sub"][1], [-1.0] * 8,
                depth=0.10, side=DARK_SIDE, k0=1.0)
    # лист: 5.3 × 1.43 м, центр 0.80 м над полом, правый край дальше
    put_plate(img, cam, sheet_fox(t), (0.05, 0.80, D), 5.3, 1.43, math.radians(5.0), 0.0,
              depth=0.02, side=(180, 180, 182), wires=(0.12, 0.88))
    if t >= 0.30:
        source_line(img, "Fox News poll · Jul 17-20, 2026")
    return img

# ================================================================= G44: выноска у точки шкалы

G44_BASE = 157.0
G44_PL0 = 0.933                     # 157.933 — первый кадр плашки (смаз справа-сверху)
G44_PL_DUR = 0.47

def column_tex(px=160, py=2400):
    """столб-шкала: тёмный, деления по левому краю"""
    img = Image.new("RGBA", (px, py), (74, 68, 62, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, px * 0.12, py], fill=(96, 90, 82, 255))
    step = py / 100.0
    for i in range(100):
        y = int(i * step)
        ln = px * 0.45 if i % 10 == 0 else (px * 0.32 if i % 5 == 0 else px * 0.2)
        d.line([(px * 0.12, y), (px * 0.12 + ln, y)], fill=(196, 190, 180, 255), width=3)
    return img

def plate_lt1_tex(px=1000, py=570):
    """плашка «<1%»: коричневый обод, чёрное поле, три ячейки, жёлтые знаки"""
    img = Image.new("RGBA", (px, py), (98, 84, 66, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([26, 26, px - 27, py - 27], fill=(18, 16, 15, 255))
    cw = (px - 52) / 3.0
    for i in (1, 2):
        d.line([(26 + cw * i, 30), (26 + cw * i, py - 30)], fill=(58, 52, 46, 255), width=4)
    f = font("Oswald-Bold.ttf", int(py * 0.70))
    for i, ch in enumerate("<1%"):
        b = d.textbbox((0, 0), ch, font=f)
        cx = 26 + cw * (i + 0.5)
        d.text((cx - (b[2] - b[0]) / 2 - b[0], (py - (b[3] - b[1])) / 2 - b[1]), ch, font=f,
               fill=(248, 192, 44, 255))
    return img

_G44 = {}
def _g44_words():
    if not _G44:
        _G44["expl"] = words_block(["SHARE OF THE WORK", "OF BUILDING AI THAT", "AI LEADS AT ANTHROPIC"],
                                   0.29, cond=1.0)
        _G44["back"] = words_block(["BACK THEN,"], 0.36, cond=1.05)
        _G44["rows"] = [words_block(["LESS THAN"], 0.36, cond=1.05),
                        words_block(["ONE PERCENT"], 0.36, cond=1.05, hl={0, 1}),
                        words_block(["OF THE WORK OF BUILDING"], 0.36, cond=1.05),
                        words_block(["NEW AI SYSTEMS."], 0.36, cond=1.05)]
        _G44["feb"] = words_block(["FEB"], 0.36, cond=1.0)
        _G44["col"] = column_tex()
        _G44["pl"] = plate_lt1_tex()
    return _G44

def g44(t):
    """жёлтая плашка «<1%» подлетает справа-сверху и встаёт вплотную к низу шкалы"""
    cam = Cam(0.09 * t, 1.55, 0.15 * t, 0.0)
    img = room(cam)
    wd = _g44_words()
    D = 10.9; XC = -2.65
    # столб: 0.27 м шириной, от пола до потолка; основание — тёмная плита 0.8 м
    col = quad((XC, CEIL / 2, D), 0.27, CEIL)
    extrude_dir(img, cam, col, wd["col"], 0.27, (0.0, 0.0, 1.0), steps=4, side=(36, 33, 30))
    base = [(XC - 0.4, 0.03, D + 0.5), (XC + 0.4, 0.03, D + 0.5), (XC + 0.4, 0.03, D - 0.3), (XC - 0.4, 0.03, D - 0.3)]
    paste_quad(img, Image.new("RGBA", (64, 64), (40, 37, 34, 255)), [cam.proj(p) for p in base])
    # FEB — тёмные буквы на полу слева от основания
    place_words(img, cam, t, wd["feb"][0], (XC - 0.95, 0.0, D - 0.2), 0.0, wd["feb"][1], [-1.0],
                depth=0.10, side=DARK_SIDE, floor=True, k0=1.0)
    # пояснение справа от шкалы — отдельным текстом, слева выровнено
    tw, th, tiles = wd["expl"][0]
    place_words(img, cam, t, wd["expl"][0], (0.78 + tw * wd["expl"][1] / 2, 0.66, D), 0.0, wd["expl"][1],
                [-1.0] * len(tiles), depth=0.06, side=DARK_SIDE, k0=1.0)
    # уголь у основания шкалы: широкий ореол и белое ядро
    pulse = 1.0 + 0.05 * math.sin(t * 5.1)
    img = glow_spot(img, cam, (XC, 0.10, D - 0.15), 1.9 * pulse, strength=0.85, core=0.10, color=(255, 140, 40))
    img = glow_spot(img, cam, (XC, 0.14, D - 0.15), 0.75 * pulse, strength=0.9, core=0.32, color=(255, 175, 70))
    # слова сверху: BACK THEN, → LESS THAN / ONE PERCENT / ...
    XL = -1.06                                   # левый край блока слов: x 40 % кадра
    if t < 0.85:
        tw0 = wd["back"][0][0] * wd["back"][1]
        place_words(img, cam, t, wd["back"][0], (XL + tw0 / 2, 2.55, D), 0.0, wd["back"][1], [-1.0, -1.0],
                    depth=0.08, side=DARK_SIDE, k0=1.0)
    else:
        starts = [[0.950, 1.217], [1.450, 1.700], [2.100, 2.200, 2.400, 2.700, 2.900], [3.100, 3.400, 3.600]]
        rows_y = [2.69, 2.33, 1.95, 1.58]                 # сетка 160.8: строки y 28 · 34.5 · 42 · 48 %
        up = 0.20 * seg(t, 3.10, 3.20)                    # с четвёртой строкой блок приподнимается
        for r, (blk, sc_r) in enumerate(wd["rows"]):
            twr = blk[0] * sc_r
            place_words(img, cam, t, blk, (XL + twr / 2, rows_y[r] + up, D), 0.0, sc_r, starts[r],
                        depth=0.08, side=DARK_SIDE)
    # плашка: 2.0 × 1.14 м, низ на полу, справа от столба; вход 470 мс с перелётом 20 %
    if t >= G44_PL0 - 1e-6:
        u = seg(t, G44_PL0, G44_PL0 + 0.15)                   # подлёт 4-5 кадров с перелётом 20 %,
        k = out_back(u, 2.6)                                   # остаток до 470 мс — затухающая дрожь
        off = (0.35 * (1 - k), 1.6 * (1 - k), -2.2 * (1 - k))      # сверху, чуть справа и ближе
        e = t - G44_PL0
        wob = math.exp(-e / 0.10) * math.cos(2 * math.pi * e / 0.22)
        roll = math.radians(-7.0) * wob
        yaw = math.radians(-8.0) * (1 - out_cubic(u)) + math.radians(-2.0) * wob
        center = (-0.40 + off[0], 0.64 + off[1], D + off[2])
        put_plate(img, cam, wd["pl"], center, 2.0, 1.16, yaw, roll, depth=0.12, side=(60, 52, 44))
        if u < 0.4:                                             # смаз на подлёте
            c2 = quad((center[0] + 0.1, center[1] + 0.4, center[2] - 0.4), 2.0, 1.16, yaw, roll)
            paste_quad(img, wd["pl"], [cam.proj(p) for p in c2], 0.3 * (1 - u / 0.4))
    if t >= 1.35:
        source_line(img, "Anthropic Institute · Sep 17, 2026")
    return img

SCENES = {"G47": (g47, 3.0), "G18": (g18, 4.5), "G44": (g44, 5.0)}

if __name__ == "__main__":
    code = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else f"{code}.png"
    t = float(os.environ.get("ZAL_FRAME", "1.0"))
    SCENES[code][0](t).convert("RGB").save(out)
    print("кадр", t, "->", out)
