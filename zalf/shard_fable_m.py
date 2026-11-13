# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть M: G07 G08 G09 G43 — свет и частицы).
Запуск: shard_fable.py <код> <out.mp4>; один кадр: ZAL_FRAME=1.9 shard_fable.py G07 k.png

Все четыре приёма пользователь когда-то отклонил («частицы сами по себе не
интересны»), поэтому здесь у роя всегда есть РАБОТА в кадре:
  G07  рой — указатель: входит сверху, садится под строку, подходит к месту
       каждого нового слова ДО его появления и подсвечивает его тёплым
       (буквы у роя краснеют, под ним тёплое пятно на полу);
  G08  вспышка-разлёт бьёт в слово: оболочка искр, засвет на весь кадр — и в
       самом пике рождается объёмное «OUT.», след искр падает и гаснет 1,5 с,
       камера пролетает сквозь слово;
  G09  поле искр = число: куча пролетает сквозь камеру, угли растекаются по
       полу волной до горизонта, а счётчик на тросах считает ровно их — 10 000;
  G43  вихрь = процесс, который сам ускоряется: поле закручивается всё быстрее,
       стягивается в точку, над ним таймер, который разгоняется вместе с ним.

Частицы считаются в numpy (10 000 углей ≈ 0.3 с на кадр), см. roy().

Числа сняты с плёнки покадрово (polosy/G07m_*, G08m_*, G09m_*, G43m_*):
  G07  (68.467-72.0) рой 5-6 углей, ядро 0.03 h, ореол 0.06 h; входит сверху
       (0.52,0.36) и за 0.5 с опускается в (0.50,0.50), дальше дрожит ±0.02;
       слова: A SWARM 68.467 (плашка на SWARM) · OF 68.700 · AUTONOMOUS 68.767 ·
       AI 69.400 · AGENTS 69.667, проявление за 2-3 кадра; строка 1 центр fy 0.20,
       капитель 0.15 h; AUTONOMOUS fy 0.68 (0.09 h); AI AGENTS fy 0.84 — стоит на
       полу → строки на ~7.3 м. Камера стоит до 70.4, потом наезд ×1.12 за 1.2 с;
       к 71.5 ореол вдвое шире и красит буквы «THEM» в оранжевый.
  G08  (92.6-94.4) надпись исчезает 92.633; искры с 92.867: не кольцо, а
       оболочка, внешний фронт +0.035 h/кадр (≈1 h/с), 300-350 штук, белые с
       кремом (250,234,220), 0.01-0.015 h; ядро растёт монотонно 0.07→0.35 h
       (92.6→93.8), сжатия нет; засвет линейно +0.045/кадр 93.267→93.7, пик
       93.7-93.833 (5 кадров, RGB≈(240,150,66)), спад 5 кадров до 0.38, хвост до
       94.3; THEY 93.5, GOT 93.6, растут и уходят вверх, залиты к 93.8; OUT
       93.867 (O→U→T за 5 кадров), высота 0.27 h → 0.37 h к 94.37 с ускорением;
       угли после вспышки правее OUT (0.64,0.50), дальше букв (параллакс);
       40-60 остаточных искр в нижней половине; 94.8-95.2 пролёт сквозь OUT.
  G09  (142.0-143.9) куча заливает кадр 142.233-142.3, пол до горизонта с
       142.4; горизонт fy 0.37→0.30 (камера наклоняется и летит); у низа 3-5
       углей на клетку 10 %, у горизонта 25-40, всего ≈1000 в кадре; уголь у низа
       0.03 h, у горизонта 0.007 h; пол виден (≈50 %); укладка — цепочки в один
       уголь, шаг 1-1.5 диаметра, зазор между цепочками 2-3 диаметра, линии тока
       огибают проплешины; ядро (255,245,215), тело (255,150,30); стены без
       оранжевой засветки; за ~1 с хаос укладывается в цепочки; THE 143.133,
       AIs 143.2, WORKED 143.567, TOGETHER на плашке; строка (0.35,0.19), 0.09 h.
  G43  (144.3-146.2) табличка (0.645,0.17) 0.27×0.14 → (0.71,0.20) 0.385×0.18,
       два троса, чёрная, цифры белёсые пока крутятся и жёлтые на 88:00:00
       (первый кадр 145.267; прокрутка 0.9 с, часы растут, минуты скачут);
       FOR EIGHTY-EIGHT с 144.3 (плашка на EIGHTY-EIGHT), HOURS 144.733,
       STRAIGHT. 145.167, уход 145.733-145.8; диск: 145.0 rx 0.48 → 145.2 0.415 →
       145.4 0.34 → 145.5 0.245 → 145.6 0.14 → 145.7 точка (сжатие ускоряется),
       центр (0.50,0.48), по часовой, 5-10°/кадр; белая точка в центре с 145.3,
       ореол 0.08×0.06; горизонт fy 0.26 → 0.14 → 0.10 → за кадром (наклон вниз
       и наезд); 146.5 AND THEY, 146.8 CRACKED, 147.0-147.3 кольцо углей наружу.
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import *

FPS = 30
CAP = 0.715                      # капитель Arial Black в долях кегля
INK = (30, 27, 26, 255)
INK_SIDE = (18, 16, 15)
YEL = (242, 206, 74, 255)

# ============================================================== камера с наклоном

class PitchCam(Cam):
    """камера зала плюс наклон вниз (pitch>0 — смотрит в пол). Нужна G09/G43:
    в образце горизонт уходит к верхнему краю, а Cam умеет только поворот."""
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
            dy, dz = dy * c + dz * si, -dy * si + dz * c
        if dz < 0.08: dz = 0.08
        k = F / dz
        return (W / 2 + dx * k, H / 2 - dy * k, dz)
    def horizon(s):
        return H / 2 - F * math.tan(s.pitch)

def proj_np(cam, P):
    """векторная проекция (N,3) → px, py, dz; dz<0.08 → dz=-1 (отбраковать)"""
    d = P - np.array([cam.x, cam.y, cam.z], np.float32)
    dx, dy, dz = d[:, 0], d[:, 1], d[:, 2]
    yaw = getattr(cam, "yaw", 0.0)
    if yaw:
        c, si = math.cos(-yaw), math.sin(-yaw)
        dx, dz = dx * c - dz * si, dx * si + dz * c
    pitch = getattr(cam, "pitch", 0.0)
    if pitch:
        c, si = math.cos(pitch), math.sin(pitch)
        dy, dz = dy * c + dz * si, -dy * si + dz * c
    ok = dz > 0.08
    k = F / np.where(ok, dz, 1.0)
    return W / 2 + dx * k, H / 2 - dy * k, np.where(ok, dz, -1.0)

# ============================================================== зал под наклонную камеру

def room_p(cam, dark=0.0, shafts=True, ropes=True, windows=True):
    """тот же зал, что Z.room, но горизонт берётся из камеры (с наклоном)"""
    hor = cam.horizon() if hasattr(cam, "horizon") else H / 2
    base = (234 - 24 * np.abs(np.linspace(0, 1, H, dtype=np.float32) - 0.5) * 2).astype(np.uint8)
    arr = np.repeat(base[:, None], W, axis=1)
    img = Image.merge("RGBA", (Image.fromarray(arr), Image.fromarray(arr),
                               Image.fromarray(np.minimum(255, arr.astype(np.int16) + 3).astype(np.uint8)),
                               Image.new("L", (W, H), 255)))
    d = ImageDraw.Draw(img, "RGBA")
    if hor > 0:
        d.rectangle([0, 0, W, hor], fill=(230, 232, 235, 255))
    d.rectangle([0, max(0, hor), W, H], fill=(197, 200, 204, 255))
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
                p = [cam.proj((sx * (WALL - 0.2), 0.0, zz + 0.6)), cam.proj((sx * (WALL - 0.2), 0.0, zz + 3.5)),
                     cam.proj((sx * (WALL - 3.4), 0.0, zz + 5.2)), cam.proj((sx * (WALL - 3.4), 0.0, zz + 2.3))]
                dl.polygon([(q[0], q[1]) for q in p], fill=(255, 255, 255, 120))
        lay = lay.filter(ImageFilter.GaussianBlur(9))
        img.alpha_composite(lay)
    if ropes:
        rng = np.random.default_rng(5)
        dr = ImageDraw.Draw(img, "RGBA")
        z0 = math.floor((cam.z + 4) / 3.0) * 3.0
        for i in range(26):
            zz = z0 + (i % 13) * 3.0 + float(rng.uniform(-1.0, 1.0))
            xx = float(rng.uniform(-4.6, 4.6)); yy = float(rng.uniform(0.9, 2.4))
            if zz - cam.z < 1.5: continue
            a = cam.proj((xx, CEIL, zz)); b = cam.proj((xx, yy, zz))
            dr.line([(a[0], a[1]), (b[0], b[1])], fill=(150, 152, 156, 255), width=1)
    if dark > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (8, 7, 6, int(235 * clamp01(dark)))))
    return img

# ============================================================== рой: угли тысячами в numpy

_STAMPS = {}
def _stamp(s):
    """две маски угля s×s: a — ореол (профиль как у Z._sprite), c — ядро"""
    if s not in _STAMPS:
        yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
        r = np.sqrt((xx - (s - 1) / 2) ** 2 + (yy - (s - 1) / 2) ** 2) / (s / 2)
        a = np.clip(1 - r, 0, 1) ** 1.15
        c = np.clip(1 - r * 1.75, 0, 1) ** 1.1
        _STAMPS[s] = (a.ravel(), c.ravel(), np.repeat(np.arange(s), s), np.tile(np.arange(s), s))
    return _STAMPS[s]

_CLASSES = (3, 4, 5, 7, 9, 12, 16, 21, 28, 36, 48, 64)

def _splat(px, py, size, w, wc, Wd, Hd, classes, margin):
    """раскладывает частицы по буферу: A — ореол, C — ядро (bincount, без циклов по частицам)"""
    Wp, Hp = Wd + 2 * margin, Hd + 2 * margin
    A = np.zeros(Wp * Hp, np.float32); C = np.zeros(Wp * Hp, np.float32)
    idx = np.clip(np.searchsorted(np.array(classes, np.float32), size), 0, len(classes) - 1)
    for ci, s in enumerate(classes):
        m = idx == ci
        if not m.any(): continue
        sa, sc, oy, ox = _stamp(s)
        x0 = np.rint(px[m] - s / 2).astype(np.int64) + margin
        y0 = np.rint(py[m] - s / 2).astype(np.int64) + margin
        ok = (x0 >= 0) & (y0 >= 0) & (x0 + s <= Wp) & (y0 + s <= Hp)
        if not ok.any(): continue
        x0, y0 = x0[ok], y0[ok]
        ww = w[m][ok]; wcc = wc[m][ok]
        flat = ((y0[:, None] + oy[None, :]) * Wp + (x0[:, None] + ox[None, :])).ravel()
        A += np.bincount(flat, weights=(ww[:, None] * sa[None, :]).ravel(), minlength=Wp * Hp).astype(np.float32)
        C += np.bincount(flat, weights=(wcc[:, None] * sc[None, :]).ravel(), minlength=Wp * Hp).astype(np.float32)
    A = A.reshape(Hp, Wp)[margin:margin + Hd, margin:margin + Wd]
    C = C.reshape(Hp, Wp)[margin:margin + Hd, margin:margin + Wd]
    return A, C

def _up(z, k):
    return np.asarray(Image.fromarray(np.clip(z * 64, 0, 255).astype(np.uint8))
                      .resize((W, H), Image.BILINEAR), np.float32) / 64

def roy(img, cam, P, sizes, bright=None, t=0.0, glow=0.95, mirror=0.0, floor_glow=0.0,
        pulse=0.18, core=(255.0, 150.0, 30.0), white=0.0, add_k=0.5):
    """тысячи углей одним проходом. P (N,3) — точки, sizes — размер угля в метрах
    (число или (N,)), bright (N,) — яркость 0..1. mirror — вес отражения в полу;
    floor_glow — широкая дымка (подсветка пола и стен); white — доля белого (искры)."""
    P = np.asarray(P, np.float32)
    n = len(P)
    if n == 0: return img
    sizes = np.asarray(sizes, np.float32) if np.ndim(sizes) else np.full(n, float(sizes), np.float32)
    bright = np.ones(n, np.float32) if bright is None else np.asarray(bright, np.float32)
    if pulse > 0:
        bright = bright * (1 - pulse + pulse * np.sin(t * 3.4 + np.arange(n) * 1.7).astype(np.float32))
    if mirror > 0:
        Pm = P.copy(); Pm[:, 1] = -Pm[:, 1] * 0.9
        P = np.concatenate([P, Pm]); sizes = np.concatenate([sizes, sizes * 0.85])
        bright = np.concatenate([bright, bright * mirror])
    px, py, dz = proj_np(cam, P)
    ok = dz > 0.3
    px, py, dz, sizes, bright = px[ok], py[ok], dz[ok], sizes[ok], bright[ok]
    spx = sizes * F / dz                                   # размер на экране, px
    ok = (spx >= 1.5) & (px > -spx) & (px < W + spx) & (py > -spx) & (py < H + spx) & (bright > 0.01)
    px, py, spx, bright = px[ok], py[ok], spx[ok], bright[ok]
    if len(px) == 0: return img
    A = np.zeros((H, W), np.float32); C = np.zeros((H, W), np.float32)
    m = spx <= 64                                          # мелкие и средние — в полном разрешении
    if m.any():
        a, c = _splat(px[m], py[m], spx[m], bright[m] * 0.55, bright[m], W, H, _CLASSES, 64)
        A += a; C += c
    m = (spx > 64) & (spx <= 800)                          # крупные (ближние) — в четверти, потом растянуть
    if m.any():
        a, c = _splat(px[m] / 4, py[m] / 4, spx[m] / 4, bright[m] * 0.55, bright[m], W // 4, H // 4,
                      (16, 21, 28, 36, 48, 64, 96, 128, 160, 200), 200)
        A += _up(a, 4); C += _up(c, 4)
    cov = np.clip(A / 0.55 * 2.6 - 0.45, 0, 1)[..., None]       # сплошное ядро — 83 % диаметра, как в Z.embers
    A3 = A[..., None]; C3 = np.clip(C, 0, 1.5)[..., None]
    add = A3 * np.array([[153.0, 76.5, 15.3]], np.float32) + C3 * np.array([[56.1, 98.2, 131.8]], np.float32)
    if white > 0:
        add = add * (1 - white) + white * (A3 + C3) * 150.0
    # ореол и широкая дымка — в четверти разрешения, один подъём
    im = Image.fromarray(np.clip(add, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    halo = np.asarray(im.filter(ImageFilter.GaussianBlur(11.5)), np.float32) * glow
    if floor_glow > 0:
        halo = halo + np.asarray(im.filter(ImageFilter.GaussianBlur(40)), np.float32) * floor_glow
    halo = np.asarray(Image.fromarray(np.clip(halo, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32)
    arr = np.asarray(img.convert("RGB"), np.float32)
    # сплошной диск: тело core (оранжевое), к центру — бело-жёлтое (255,245,215), как на плёнке
    body = np.array(core, np.float32) * (1 - white) + white * np.array([255, 246, 228], np.float32)
    cen = np.clip(C3 * 1.3, 0, 1)
    corec = body[None, None, :] * (1 - cen) + np.array([255, 245, 215], np.float32) * cen
    arr = arr * (1 - cov) + corec * cov + add * add_k + halo
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

def orange_fill(img, k, color=(240, 150, 66)):
    """засвет: оранжевая заливка силой k (0..1) поверх кадра"""
    if k <= 0.005: return img
    arr = np.asarray(img.convert("RGB"), np.float32)
    c = np.array(color, np.float32)
    arr = arr * (1 - k) + c * k + arr * k * 0.25        # чуть аддитивно, чтобы ядро пробивало в белый
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

def zoom_streaks(img, k, cx=0.5, cy=0.5):
    """радиальный смаз от точки (зум-смаз на пике вспышки)"""
    if k <= 0.01: return img
    base = img.convert("RGB")
    for i, z in enumerate((1.03, 1.07, 1.12)):
        sw, sh = int(W * z), int(H * z)
        big = base.resize((sw, sh), Image.BILINEAR)
        ox = int(cx * W * (z - 1)); oy = int(cy * H * (z - 1))
        big = big.crop((ox, oy, ox + W, oy + H))
        base = Image.blend(base, big, 0.35 * k)
    return base.convert("RGBA")

# ============================================================== слова: быстрый объём

def tiles_crop(lines, fsize, hl=None, color=INK, cond=0.62, fname="ArialBlack.ttf"):
    """плитки слов, обрезанные по контуру: (ширина, высота, [(плитка, cx, cy)]) в px блока"""
    tw, th, tiles = word_tiles(lines, fsize=fsize, fname=fname, hl=hl, color=color)
    out = []
    for tile, cx, cy in tiles:
        tile = tile.resize((max(4, int(tile.size[0] * cond)), tile.size[1]), Image.LANCZOS)
        bb = tile.getbbox()
        if bb is None: continue
        cr = tile.crop((bb[0], 0, bb[2], tile.size[1]))
        out.append((cr, cx * cond - tile.size[0] / 2 + (bb[0] + bb[2]) / 2, cy))
    return tw * cond, th, out

def extrude_fast(canvas, cam, corners, tex, depth, nz, side=INK_SIDE, opacity=1.0):
    """объём за ДВА преобразования: задняя альфа тянется к передней грани сдвигами в numpy
    (вместо 10-50 перспективных копий), потом лицевая грань"""
    front = [cam.proj(c) for c in corners]
    back = [cam.proj((c[0] + nz[0] * depth, c[1], c[2] + nz[2] * depth)) for c in corners]
    if min(p[2] for p in front + back) < 0.3: return
    xs = [p[0] for p in front + back]; ys = [p[1] for p in front + back]
    x0, x1 = int(math.floor(min(xs))), int(math.ceil(max(xs)))
    y0, y1 = int(math.floor(min(ys))), int(math.ceil(max(ys)))
    x0, y0 = max(x0, -W), max(y0, -H); x1, y1 = min(x1, 2 * W), min(y1, 2 * H)
    bw, bh = x1 - x0, y1 - y0
    if bw < 2 or bh < 2 or x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H or bw * bh > 12_000_000: return
    tw, th = tex.size
    src = [(0, 0), (tw, 0), (tw, th), (0, th)]
    dx = sum(f[0] - b[0] for f, b in zip(front, back)) / 4.0
    dy = sum(f[1] - b[1] for f, b in zip(front, back)) / 4.0
    n = int(math.ceil(max(abs(dx), abs(dy))))
    if n >= 1:
        try:
            co = Z._coeffs([(p[0] - x0, p[1] - y0) for p in back], src)
        except Exception:
            return
        A = np.asarray(tex.getchannel("A").transform((bw, bh), Image.PERSPECTIVE, co, Image.BILINEAR), np.float32) / 255
        acc = np.zeros((bh, bw), np.float32)
        shade = np.zeros((bh, bw), np.float32)
        step = max(1, n // 70)
        for k in range(0, n + 1, step):
            ox = int(round(dx * k / n)); oy = int(round(dy * k / n))
            sx0, sx1 = max(0, ox), min(bw, bw + ox); sy0, sy1 = max(0, oy), min(bh, bh + oy)
            if sx1 <= sx0 or sy1 <= sy0: continue
            sub = A[sy0 - oy:sy1 - oy, sx0 - ox:sx1 - ox]
            dst = acc[sy0:sy1, sx0:sx1]
            np.maximum(dst, sub, out=dst)
            sh = shade[sy0:sy1, sx0:sx1]
            sh[sub > 0.5] = 0.78 + 0.22 * k / n
        lay = np.zeros((bh, bw, 4), np.uint8)
        for j in range(3):
            lay[..., j] = np.clip(side[j] * np.where(shade > 0, shade, 0.78), 0, 255).astype(np.uint8)
        lay[..., 3] = np.clip(acc * 255 * opacity, 0, 255).astype(np.uint8)
        canvas.alpha_composite(Image.fromarray(lay, "RGBA"), (max(0, x0), max(0, y0)),
                               (max(0, -x0), max(0, -y0), bw, bh))
    paste_quad(canvas, tex, front, opacity)

def pop(t0, t, dur=0.10, k0=1.10):
    """вход слова: первый кадр крупнее и прозрачнее, за ~3 кадра садится"""
    if t < t0 - 1e-6: return None
    u = seg(t, t0, t0 + dur)
    return k0 + (1.0 - k0) * out_cubic(u), 0.55 + 0.45 * clamp01(u * 2.2)

def text_shadow(canvas, cam, corners, tex, ux, off=(0.9, 0.0, 1.4), blur=12, strength=0.30):
    bl, br = corners[3], corners[2]
    k = corners[0][1] - corners[3][1]
    sh = [(bl[0] + off[0] * k, 0.012, bl[2] + off[2] * k), (br[0] + off[0] * k, 0.012, br[2] + off[2] * k),
          (br[0], 0.012, br[2]), (bl[0], 0.012, bl[2])]
    if min(c[2] for c in sh) - cam.z < 0.35: return
    a = tex.split()[3].point(lambda v: int(v * strength))
    dark = Image.new("RGBA", tex.size, (38, 36, 34, 255)); dark.putalpha(a)
    paste_quad(canvas, dark.filter(ImageFilter.GaussianBlur(blur)), [cam.proj(p) for p in sh])

def warm_tile(tile, k, tint=(255, 120, 30)):
    """подсветить плитку слова тёплым: k 0..1 — сила (лицевая грань у света краснеет)"""
    if k <= 0.01: return tile
    a = np.asarray(tile, np.float32)
    rgb = a[..., :3]
    lum = rgb.mean(-1, keepdims=True) / 255
    kk = k * (0.9 - 0.55 * lum)                     # тёмные буквы краснеют сильнее жёлтой плашки
    lit = rgb * (1 - 0.7 * kk) + np.array(tint, np.float32) * 0.7 * kk
    out = a.copy(); out[..., :3] = np.clip(lit, 0, 255)
    return Image.fromarray(out.astype(np.uint8))

def words(img, cam, t, tiles_, center, cap_m, starts, yaw=0.0, depth=0.10, side=INK_SIDE,
          hang=False, floor=False, shadow=False, warm=None, k0=1.10, fade=None, lift=0.0,
          align="center"):
    """ставит плитки слов в зал. center — центр строки (при floor — низ букв на полу);
    cap_m — высота капители в метрах; starts — t0 каждого слова; warm(point)→0..1 —
    тёплая подсветка по близости роя; fade=(t0,t1) — растворение; lift — подъём (м)."""
    tw, th, tiles = tiles_
    fs = th - 40                                # кегль: th = hline + 2*pad(20)
    scale_m = cap_m / (CAP * fs)
    ux = (math.cos(yaw), 0.0, math.sin(yaw)); nz = (-math.sin(yaw), 0.0, math.cos(yaw))
    op_all = 1.0
    if fade is not None:
        op_all = 1.0 - seg(t, fade[0], fade[1])
        if op_all <= 0.01: return
    for i, (tile, cx, cy) in enumerate(tiles):
        p = pop(starts[i], t, k0=k0)
        if p is None: continue
        s, op = p
        op *= op_all
        w = tile.size[0] * scale_m * s; h = tile.size[1] * scale_m * s
        u = (cx - tw / 2) * scale_m
        if align == "left": u = cx * scale_m
        v = h / 2 if floor else (th / 2 - cy) * scale_m
        cx3 = center[0] + ux[0] * u; cy3 = center[1] + v + lift; cz3 = center[2] + ux[2] * u
        hw, hh = w / 2, h / 2
        c = [(cx3 - ux[0] * hw, cy3 + hh, cz3 - ux[2] * hw), (cx3 + ux[0] * hw, cy3 + hh, cz3 + ux[2] * hw),
             (cx3 + ux[0] * hw, cy3 - hh, cz3 + ux[2] * hw), (cx3 - ux[0] * hw, cy3 - hh, cz3 - ux[2] * hw)]
        if min(q[2] for q in c) - cam.z < 0.35: continue
        tl = tile
        if warm is not None:
            tl = warm_tile(tile, warm((cx3, cy3, cz3)))
        if shadow and lift < 0.02:
            text_shadow(img, cam, c, tile, ux)
        if hang:
            nw = 2 if w > 0.45 else 1
            for j in range(nw):
                f = (j + 0.5) / nw
                top = (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1], c[0][2] + (c[1][2] - c[0][2]) * f)
                wire(img, cam, top, color=(96, 98, 102, 230), width=2)
        extrude_fast(img, cam, c, tl, depth, nz, side=side, opacity=op)

# ============================================================== G07 — рой-указатель

_G07_KEYS = [(0.0, 0.3, 2.9, 7.0), (0.5, 0.0, 1.55, 7.0), (0.75, 0.0, 1.55, 7.0),
             (1.05, -0.9, 1.0, 6.8),      # к AUTONOMOUS (левая половина второй строки, перед буквами)
             (1.25, -0.9, 1.0, 6.8),
             (1.55, -0.8, 0.45, 6.7),     # к AI
             (1.75, -0.8, 0.45, 6.7),
             (2.05, 0.65, 0.45, 6.7),     # к AGENTS
             (2.3, 0.65, 0.45, 6.7),
             (2.9, 0.0, 1.45, 6.8),       # обратно в центр
             (4.5, 0.0, 1.45, 6.8)]

def _g07_swarm(t):
    keys = _G07_KEYS
    for i in range(len(keys) - 1):
        t0, x0, y0, z0 = keys[i]; t1, x1, y1, z1 = keys[i + 1]
        if t <= t1:
            u = seg(t, t0, t1)
            e = (1 - (1 - u) ** 2) if i == 0 else (u * u * (3 - 2 * u))
            return (x0 + (x1 - x0) * e, y0 + (y1 - y0) * e, z0 + (z1 - z0) * e)
    return keys[-1][1:]

def _g07_pts(c, t, n=6, seed=3):
    """6 углей ромбом вокруг центра, перестраиваются и дрожат; на входе вытянуты по диагонали"""
    rng = np.random.default_rng(seed)
    base = rng.uniform(-1, 1, (n, 3)) * np.array([0.32, 0.22, 0.30])
    ph = rng.uniform(0, 6.28, (n, 3)); fr = rng.uniform(0.6, 1.4, (n, 3))
    wob = 0.08 * np.sin(t * 2.4 * fr + ph)
    stretch = 1.0 + 0.6 * (1 - seg(t, 0.0, 0.6))
    P = np.array(c, np.float32)[None, :] + base * np.array([1.0, stretch, 1.0]) + wob
    P[:, 1] = np.maximum(0.06, P[:, 1])
    s = rng.uniform(0.15, 0.22, n)
    return P.astype(np.float32), s.astype(np.float32)

_G07 = {}
def _g07_words():
    if not _G07:
        _G07["top"] = tiles_crop(["A SWARM OF"], 200, hl={1})
        _G07["mid"] = tiles_crop(["AUTONOMOUS"], 200)
        _G07["bot"] = tiles_crop(["AI AGENTS"], 200)
    return _G07

def g07(t):
    """рой углей ведёт взгляд: садится под строку, подходит к месту каждого нового
    слова до его появления и подсвечивает его; камера с 2.4 с наезжает"""
    cz = 1.6 * seg(t, 2.4, 4.5) ** 1.3
    cam = Cam(0.0, 1.55, cz, 0.0)
    img = room(cam)
    wd = _g07_words()
    c = _g07_swarm(t)
    def warm_for(p):
        return 0.9 * clamp01(1.3 - math.dist(p, c) / 1.9)
    # строки на 7.3 м: верх центр 2.75 м, капитель 0.60; AUTONOMOUS 0.83 м, 0.36; AI AGENTS на полу
    words(img, cam, t, wd["top"], (0.0, 2.75, 7.3), 0.60, [0.0, 0.0, 0.233], depth=0.12, hang=True, warm=warm_for)
    words(img, cam, t, wd["mid"], (0.0, 0.83, 7.2), 0.36, [1.10], depth=0.10, warm=warm_for)
    words(img, cam, t, wd["bot"], (0.0, 0.0, 7.1), 0.36, [1.60, 2.10], depth=0.10, floor=True, shadow=True, warm=warm_for)
    P, s = _g07_pts(c, t)
    k = 0.75 + 0.75 * seg(t, 3.0, 4.5)        # к концу ореол вдвое шире и красит буквы, как на 71.5
    br = np.full(len(P), 1.0, np.float32) * (1.15 - 0.15 * seg(t, 0.0, 0.3))   # ярче всего на входе
    img = roy(img, cam, P, s, bright=br, t=t, glow=1.6 * k, floor_glow=1.0 * k, add_k=0.7)
    return img

# ============================================================== G08 — вспышка-разлёт

_G08 = {}
def _g08_words():
    if not _G08:
        _G08["cap"] = tiles_crop(["THAT NOBODY ON EARTH", "KNEW EXISTED."], 200, hl={1})
        _G08["they"] = tiles_crop(["THEY GOT"], 200)
        _G08["out"] = tiles_crop(["OUT."], 200, color=(22, 21, 21, 255))
    return _G08

def _g08_sparks(t, seed=11, n=340):
    """оболочка искр: вылет в 0.32 с, внешний фронт ≈3.3 м/с, после пика — тяжесть и пол"""
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(n, 3)); v /= np.linalg.norm(v, axis=1)[:, None]
    spd = rng.uniform(1.6, 3.4, n)[:, None]
    v = v * spd
    tt = max(0.0, t - 0.32)
    drag = 1.6
    # разгон с сопротивлением: s = v/drag·(1-e^{-drag t}); тяжесть включается после пика (t>1.2)
    disp = v / drag * (1 - np.exp(-drag * tt))
    g = max(0.0, t - 1.15)
    disp[:, 1] -= 2.2 * g * g
    P = np.array([0.0, 1.45, 6.0], np.float32) + disp
    P[:, 1] = np.maximum(0.03, P[:, 1])
    life = np.clip(1.0 - (t - 1.3) / 1.5, 0, 1) if t > 1.3 else 1.0
    br = np.ones(n, np.float32) * life * (0.6 + 0.4 * rng.uniform(0, 1, n))
    br[tt <= 0] = 0.0
    sz = np.full(n, 0.038, np.float32) * (1.0 + 0.5 * seg(t, 1.3, 2.2))
    return P.astype(np.float32), sz, br.astype(np.float32)

def g08(t):
    """искры сжимаются в оболочку, кадр заливает оранжевым, и в пике рождается «OUT.»;
    след искр падает и гаснет 1,5 с; камера разгоняется сквозь слово"""
    # камера: лёгкий наезд, с 2.5 с разгон сквозь OUT., к 4.1 — за ним, темнота
    cz = 0.5 * t + 9.0 * seg(t, 2.5, 4.1) ** 2.6
    cam = Cam(0.25 * seg(t, 1.3, 2.5), 1.55, cz, 0.0)
    dark = seg(t, 3.7, 4.3) * 0.92
    img = room(cam, dark=dark)
    wd = _g08_words()
    # ядро роя в кубе: центр (0,1.45,6), ядро растёт монотонно 0.07→0.35 h
    core_h = 0.07 + 0.28 * seg(t, 0.0, 1.25) ** 1.4
    flash = 0.0
    if t < 1.15: flash = 0.86 * seg(t, 0.72, 1.15)
    elif t < 1.28: flash = 0.86
    elif t < 1.45: flash = 0.86 - 0.48 * seg(t, 1.28, 1.45)
    else: flash = 0.38 * (1 - seg(t, 1.45, 2.3))
    if t < 1.2:
        glass_cube(img, cam, (0.0, 1.3, 6.0), 2.4, t)
        words(img, cam, t, wd["cap"], (-1.9, 0.42, 5.4), 0.20, [-1] * 6, depth=0.03,
              fade=(0.06, 0.09), align="center")
    # THEY GOT: 0.95 / 1.05, растут и уходят вверх к камере, залиты к 1.25
    if 0.95 <= t < 1.26:
        lift = 1.1 * seg(t, 1.0, 1.26) ** 1.5
        words(img, cam, t, wd["they"], (0.1, 2.35, 5.6), 0.22 + 0.34 * seg(t, 1.0, 1.26), [0.95, 1.05],
              depth=0.04, lift=lift)
    # угли после вспышки: правее OUT, дальше букв; до вспышки — ядро
    if t >= 1.3:
        rng = np.random.default_rng(4)
        base = rng.uniform(-1, 1, (5, 3)) * np.array([0.45, 0.35, 0.4])
        wob = 0.07 * np.sin(t * 2.6 * rng.uniform(0.7, 1.3, (5, 3)) + rng.uniform(0, 6.3, (5, 3)))
        P = np.array([0.9, 1.5, 7.0], np.float32) + base + wob
        img = roy(img, cam, P, rng.uniform(0.16, 0.26, 5).astype(np.float32), t=t, glow=1.3, floor_glow=0.6, add_k=0.7)
    # OUT.: рождается в пике 1.32, O→U→T, стоит на 4.3 м, капитель 0.67 м, правый конец дальше
    if t >= 1.32:
        words(img, cam, t, wd["out"], (-0.35, 1.9, 4.6), 0.70, [1.32], yaw=math.radians(14), depth=0.42,
              side=(70, 70, 72), k0=1.0)
    # искры
    Ps, sz, br = _g08_sparks(t)
    if br.max() > 0:
        img = roy(img, cam, Ps, sz, bright=br, t=t, glow=0.5, white=0.85, pulse=0.0, add_k=0.3)
    # ядро до/во время вспышки
    if t < 1.5:
        d = 6.0 - cz
        sz_core = core_h * H / F * d
        rng = np.random.default_rng(2)
        base = rng.uniform(-1, 1, (3, 3)) * np.array([0.35, 0.22, 0.2]) * (sz_core / 0.6)
        P = np.array([0.0, 1.45, 6.0], np.float32) + base
        wh = 0.12 + 0.75 * seg(t, 0.6, 1.2)
        br = np.ones(3, np.float32) * (1.0 - seg(t, 1.3, 1.5))
        img = roy(img, cam, P, np.full(3, sz_core * 0.9, np.float32), bright=br, t=t, glow=1.6 + 1.4 * seg(t, 0.5, 1.2),
                  floor_glow=0.7 + 0.6 * seg(t, 0.3, 1.1), white=wh, pulse=0.08, add_k=0.7)
    if flash > 0:
        img = zoom_streaks(img, seg(t, 1.05, 1.2) * (1 - seg(t, 1.3, 1.45)), 0.5, 0.42)
        img = orange_fill(img, flash)
    # за словом — тёмный зал, рой летит впереди камеры
    if t >= 3.5:
        rng = np.random.default_rng(9)
        base = rng.uniform(-1, 1, (6, 3)) * np.array([0.5, 0.3, 0.5])
        P = np.array([0.0, 1.3, cz + 9.0 - 2.0 * seg(t, 3.5, 4.5)], np.float32) + base
        img = roy(img, cam, P, rng.uniform(0.16, 0.24, 6).astype(np.float32), t=t, glow=1.4, floor_glow=0.8, add_k=0.7)
    v = 2.6 * 9.0 * seg(t, 2.5, 4.1) ** 1.6 / 1.6
    if v > 2.0:
        img = Z_rush(img, clamp01((v - 2.0) / 14.0))
    return img

def Z_rush(img, k):
    """смаз пролёта: пара увеличенных копий поверх"""
    if k <= 0.01: return img
    base = img.convert("RGB")
    for z in (1.012, 1.028):
        sw, sh = int(W * z), int(H * z)
        big = base.resize((sw, sh), Image.BILINEAR).crop(((sw - W) // 2, (sh - H) // 2, (sw - W) // 2 + W, (sh - H) // 2 + H))
        base = Image.blend(base, big, 0.30 * k)
    return base.convert("RGBA")

# ============================================================== поле углей (G09, G43)

_FIELD = {}
def field_pts(n_target=10000, seed=7):
    """10 000 углей цепочками-линиями тока по полу зала: x∈[-6,6], z∈[2,72].
    Цепочка — один уголь шириной, шаг 0.25 м, соседние цепочки через ~0.42 м,
    изгибы — две синусоиды, проплешины — порог шума. Возвращает (P, order, chain_id)."""
    if "P" in _FIELD: return _FIELD["P"], _FIELD["scatter"], _FIELD["rank"]
    rng = np.random.default_rng(seed)
    pts = []
    xs0 = np.arange(-6.3, 6.31, 0.42)
    zs = np.arange(2.0, 72.0, 0.25)
    for i, x0 in enumerate(xs0):
        ph1, ph2 = rng.uniform(0, 6.28, 2)
        x = x0 + 1.1 * np.sin(zs * 0.11 + ph1) + 0.45 * np.sin(zs * 0.33 + ph2) + rng.normal(0, 0.05, len(zs))
        z = zs + rng.uniform(-0.06, 0.06, len(zs))
        pts.append(np.stack([x, np.full(len(zs), 0.06), z], 1))
    P = np.concatenate(pts).astype(np.float32)
    # проплешины: два слоя шума — убираем, где поле выше порога
    nx = np.sin(P[:, 0] * 0.9 + 1.3) * np.sin(P[:, 2] * 0.37 + 0.4) + 0.6 * np.sin(P[:, 0] * 1.7 - P[:, 2] * 0.21)
    keep = nx < 0.55
    P = P[keep]
    P = P[np.abs(P[:, 0]) < 6.0]
    if len(P) > n_target:
        P = P[rng.choice(len(P), n_target, replace=False)]
    elif len(P) < n_target:
        extra = P[rng.choice(len(P), n_target - len(P))] + rng.normal(0, 0.12, (n_target - len(P), 3)).astype(np.float32)
        extra[:, 1] = 0.06
        P = np.concatenate([P, extra])
    scatter = rng.normal(0, 1.0, P.shape).astype(np.float32) * np.array([1.6, 0.9, 1.6], np.float32)
    scatter[:, 1] = np.abs(scatter[:, 1]) + 0.2
    rank = np.argsort(np.argsort(P[:, 2] + rng.normal(0, 1.5, len(P)))).astype(np.float32) / len(P)
    _FIELD["P"], _FIELD["scatter"], _FIELD["rank"] = P, scatter, rank
    return P, scatter, rank

def counter_tex(text, w=680, h=200, final=False, tilt=0.0):
    """чёрная табличка с цифрами в фиксированных ячейках (моноширинный вид);
    пока крутится — белёсые, итог — жёлтые"""
    img = Image.new("RGBA", (w, h), (18, 17, 17, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(72, 70, 68, 255), width=4)
    d.rectangle([5, 5, w - 6, h - 6], outline=(40, 38, 36, 255), width=2)
    f = font("Oswald-Bold.ttf", int(h * 0.62))
    col = (255, 196, 42, 255) if final else (222, 222, 216, 255)
    widths = [h * (0.26 if ch in ":., " else 0.50) for ch in text]
    total = sum(widths)
    x = (w - total) / 2
    for i, ch in enumerate(text):
        b = d.textbbox((0, 0), ch, font=f)
        cx = x + widths[i] / 2; x += widths[i]
        d.text((cx - (b[2] - b[0]) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), ch, font=f, fill=col)
        if not final and ch.isdigit() and (i * 7 + int(ch)) % 5 == 0:
            d.text((cx - (b[2] - b[0]) / 2 - b[0] + 3, (h - (b[3] - b[1])) / 2 - b[1] - 2), ch, font=f,
                   fill=(120, 150, 255, 90))
    return img

def hang_plate(img, cam, tex, center, w_m, t=0.0, sway=0.0, wires=2, depth=0.05):
    """табличка на двух тросах; sway — качание (рад)"""
    h_m = w_m * tex.size[1] / tex.size[0]
    roll = sway * math.sin(t * 1.7)
    c = quad(center, w_m, h_m, 0.0, roll)
    if min(q[2] for q in c) - cam.z < 0.35: return
    for f in (0.12, 0.88):
        top = (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1] + (c[1][1] - c[0][1]) * f, c[0][2])
        wire(img, cam, top, color=(40, 40, 42, 255), width=2)
    extrude_fast(img, cam, c, tex, depth, (0, 0, 1), side=(60, 58, 56))

# ============================================================== G09 — поле = число

_G09 = {}
def _g09_words():
    if not _G09:
        _G09["a"] = tiles_crop(["AI AGENTS"], 200)
        _G09["b"] = tiles_crop(["WORKED TOGETHER"], 200, hl={1})
    return _G09

def _g09_mound(t, cam):
    """куча углей, сквозь которую пролетает камера в первые 0.35 с"""
    rng = np.random.default_rng(21)
    n = 2600
    P = np.stack([rng.normal(0, 1.3, n), np.abs(rng.normal(0, 0.8, n)) + 0.05, rng.uniform(0.0, 6.0, n)], 1).astype(np.float32)
    P[:, 2] += 0.6
    sz = rng.uniform(0.08, 0.16, n).astype(np.float32)
    br = np.ones(n, np.float32) * (1 - seg(t, 0.45, 0.75))
    return P, sz, br

def g09(t):
    """куча пролетает сквозь камеру, угли растекаются по полу волной до горизонта,
    счётчик на тросах считает их — ровно десять тысяч"""
    # камера: быстро вперёд сквозь кучу, потом плавный ход и наклон вниз (горизонт 0.37→0.30)
    cz = 5.5 * (1 - (1 - seg(t, 0.0, 0.5)) ** 2) + 0.9 * max(0.0, t - 0.5)
    pitch = math.radians(4.0 + 3.0 * seg(t, 0.5, 4.5))
    cam = PitchCam(0.0, 2.3, cz, 0.0, pitch)
    img = room_p(cam)
    P, scatter, rank = field_pts()
    # волна зажигания от камеры к горизонту 0.45→2.2 с: уголь загорается по рангу дальности,
    # первые 0.25 с после зажигания — вспышка ×1.6, и он подтягивается из разброса в цепочку
    u = seg(t, 0.45, 2.2)
    lit = rank <= u
    age = (u - rank) * (2.2 - 0.45)                    # секунд с момента зажигания
    settle = np.clip(age / 0.7, 0, 1); settle = settle * settle * (3 - 2 * settle)
    Pt = P + scatter * (1 - settle)[:, None]
    flash = 1.0 + 0.8 * np.clip(1 - age / 0.25, 0, 1)
    br = np.where(lit, flash, 0.0).astype(np.float32)
    # лёгкий дрейф цепочек к камере после укладки — поле «работает»
    Pt[:, 2] -= 0.25 * max(0.0, t - 2.2) * settle
    count = int(round(10000 * u))
    if t < 0.8:
        Pm, sm, bm = _g09_mound(t, cam)
        img = roy(img, cam, Pm, sm, bright=bm, t=t, glow=0.8, floor_glow=0.3)
    img = roy(img, cam, Pt[lit], np.full(int(lit.sum()), 0.12, np.float32), bright=br[lit], t=t,
              glow=0.8, floor_glow=0.15, pulse=0.12, core=(255.0, 200.0, 120.0))
    # счётчик: слева вверху (0.30,0.18), с 0.4 с; итог жёлтым
    if t >= 0.4:
        txt = f"{count:,}".replace(",", " ") if count > 0 else "0"
        final = u >= 1.0
        tex = counter_tex(txt, final=final)
        wd = _g09_words()
        # табличка на 9 м от камеры: ширина 2.6 м, центр 3.3 м
        zc = cam.z + 9.0
        hang_plate(img, cam, tex, (-2.4, 3.35 - 0.6 * seg(t, 0.5, 4.5), zc), 2.6, t=t, sway=0.012)
        words(img, cam, t, wd["a"], (1.75, 3.35 - 0.6 * seg(t, 0.5, 4.5), zc), 0.46, [2.25, 2.25], depth=0.1, hang=True)
        words(img, cam, t, wd["b"], (0.3, 2.45 - 0.6 * seg(t, 0.5, 4.5), zc), 0.46, [2.9, 3.3], depth=0.1, hang=True)
    return img

# ============================================================== G43 — вихрь

_G43 = {}
def _g43_words():
    if not _G43:
        _G43["a"] = tiles_crop(["FOR EIGHTY-EIGHT"], 200, hl={1})
        _G43["b"] = tiles_crop(["HOURS STRAIGHT."], 200)
        _G43["c"] = tiles_crop(["AND THEY"], 200)
        _G43["d"] = tiles_crop(["CRACKED IT."], 200, hl={0})
    return _G43

def _timer_text(u, rng):
    """часы растут 0→88 с ускорением, минуты и секунды скачут; итог 88:00:00"""
    if u >= 1.0: return "88:00:00", True
    hh = int(88 * (u ** 1.6))
    if u > 0.93:
        hh = 87; mm = 52 + int(8 * seg(u, 0.93, 1.0)); ss = int(rng.integers(0, 60))
    else:
        mm = int(rng.integers(0, 60)); ss = int(rng.integers(0, 60))
    return f"{hh:02d}:{mm:02d}:{ss:02d}", False

def g43(t):
    """поле закручивается всё быстрее и стягивается в точку; таймер над ним разгоняется
    вместе с процессом; в конце из точки — кольцо наружу и «CRACKED IT.»"""
    # камера: кран вверх с наклоном (горизонт 0.26 → за кадр) и наезд
    k = seg(t, 0.0, 2.6)
    pitch = math.radians(7.5 + 24.0 * (k * k * (3 - 2 * k)))
    cy = 2.4 + 2.8 * (k * k * (3 - 2 * k))
    cz = 0.35 * t
    cam = PitchCam(0.0, cy, cz, 0.0, pitch)
    img = room_p(cam)
    P, scatter, rank = field_pts()
    # центр вихря на 9.4 м впереди стартовой камеры
    C = np.array([0.0, 9.4], np.float32)
    dx = P[:, 0] - C[0]; dz = P[:, 2] - C[1]
    r0 = np.sqrt(dx * dx + dz * dz); th0 = np.arctan2(dz, dx)
    u = seg(t, 0.3, 2.9)
    R = 1.0 - u ** 2.6                                   # сжатие ускоряется к концу
    Om = 2.4 * u ** 2.2 + 0.25 * t                        # закрутка ускоряется, дифференциальная
    th = th0 - Om / np.sqrt(np.maximum(r0, 0.6) / 4.0)   # по часовой сверху
    r = r0 * R
    Pt = np.stack([C[0] + r * np.cos(th), P[:, 1] + 0.0 * r, C[1] + r * np.sin(th)], 1).astype(np.float32)
    keep = (r > 0.08) & (np.abs(Pt[:, 0]) < 6.2) & (r0 < 16.0)
    br = np.clip(1.4 - r0 / 16.0, 0, 1).astype(np.float32) * (1 - seg(t, 2.8, 2.95))   # дальний край гаснет
    sizes = np.full(len(P), 0.12, np.float32) * (1 - 0.25 * u)
    if br.max() > 0.01:
        img = roy(img, cam, Pt[keep], sizes[keep], bright=br[keep], t=t, glow=0.8, floor_glow=0.15,
                  pulse=0.12, core=(255.0, 200.0, 120.0))
    # белая точка в центре — с 2.0 с, растёт, после сжатия остаётся одна с ореолом
    if t >= 2.0:
        sz = 0.10 + 0.30 * seg(t, 2.0, 2.95)
        wh = 0.5 + 0.4 * seg(t, 2.0, 2.9)
        img = roy(img, cam, np.array([[C[0], 0.12, C[1]]], np.float32), np.array([sz], np.float32), t=t,
                  glow=2.2, floor_glow=1.0, white=wh * 0.7, pulse=0.05, add_k=0.8)
    # кольцо наружу с 3.7 с: 420 углей бегут от точки по полу
    if t >= 3.7:
        rng = np.random.default_rng(5)
        n = 900
        a = rng.uniform(0, 6.283, n); rr = (0.3 + 5.5 * out_cubic(seg(t, 3.7, 4.5))) * rng.uniform(0.78, 1.0, n)
        Pr = np.stack([C[0] + rr * np.cos(a), np.full(n, 0.07), C[1] + rr * np.sin(a)], 1).astype(np.float32)
        img = roy(img, cam, Pr, np.full(n, 0.12, np.float32), t=t, glow=0.8, floor_glow=0.2, pulse=0.12)
    wd = _g43_words()
    # табличка-таймер справа вверху, слова слева; всё висит на 8 м впереди стартовой камеры
    zc = 8.0; yc = 2.6
    rng = np.random.default_rng(int(t * 30) + 3)
    txt, final = _timer_text(u, rng)
    tex = counter_tex(txt, final=final)
    hang_plate(img, cam, tex, (2.1, yc, zc), 2.5, t=t, sway=0.03)
    words(img, cam, t, wd["a"], (-2.5, yc + 0.15, zc), 0.42, [-1, -1], depth=0.08, hang=True, fade=(3.2, 3.4))
    words(img, cam, t, wd["b"], (-2.5, yc - 0.55, zc), 0.42, [1.2, 2.0], depth=0.08, fade=(3.2, 3.4))
    words(img, cam, t, wd["c"], (-2.4, yc + 0.15, zc), 0.42, [3.5, 3.5], depth=0.08, hang=True)
    words(img, cam, t, wd["d"], (-2.4, yc - 0.55, zc), 0.42, [3.8, 4.05], depth=0.08)
    return img

SCENES = {"G07": (g07, 4.5), "G08": (g08, 4.5), "G09": (g09, 4.5), "G43": (g43, 4.5)}

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
