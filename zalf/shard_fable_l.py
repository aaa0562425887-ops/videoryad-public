# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть L: G03 лучи из окон, G04 отражение в полу).
Запуск: shard_fable_l.py <код> <out.mp4>; один кадр: ZAL_FRAME=1.9 shard_fable_l.py G03 k.png

Оба приёма он отклонял «не понял на статике» — поэтому здесь свет и зеркало показаны
В РАБОТЕ: камера едет, пятна света ползут по полу и стене, солнце чуть сдвигается и
«дышит» облаком, в луче висит пыль; в зеркале пола рождается отражение предмета,
который ВХОДИТ в кадр (слово падает на пол — отражение поднимается ему навстречу).

Числа сняты с плёнки (polosy/G03_vhod, G03_svet, G03_svet_setka, G04_vhod, G04_setka):
  G03  на куске 109.0 свет из окон почти не виден (кадр занят углями) — взято место
       116.4-117.6 и 129.0, где пятна читаются лучше всего. 116.40: пятно от ближнего
       левого окна лежит на полу x 42-60 %, y 76-93 % → центр зала (X≈0) на ~8 м,
       в пятне видна сетка переплёта; окно слева x 5-28 %, y 15-85 %. 129.00: пятна
       x 48-75 %, y 40-50 % — светлые косые четырёхугольники ПОСЕРЕДИНЕ пола, верхний
       край самого дальнего заходит на правую стену (x 80-100 %, y 37-48 %). Солнце
       слева-сверху-сзади: окно 1.15-3.75 м, пятно на 6 м от стены → высота ≈18-21°,
       азимут ≈12° вперёд. Воздух у окон молочный — дымка слабая, не «god rays».
  G04  109.0-111.9: камера НИЗКО (≈0.4 м: низ рамы-коробки на 12 м лежит на y 55 %,
       низ окна 1.15 м на 14 м — на y 40 %). Угли 0.1-0.9 м над полом на 9-10 м,
       ореол ≈0.6 м; их отражение — размытый оранжевый разлив на полу y 60-95 %,
       x 35-70 %, т.е. ШИРЕ самих углей (зеркало под острым углом). Слова на тросах:
       OPENAI 109.3 · SHUT 109.9 · THOSE 110.2 · AIs 110.4 · DOWN. 110.9 (жёлтый).
       111.0-111.5 угли падают на пол и становятся чёрными шариками с отражением.
       В полу отражаются и рама (серые линии, вдвое слабее), и окно (светлое пятно
       под ним на y 50-60 %).
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import *
from shard_fable_a import (pop, tiles_crop, place_words, extrude_dir, word_quad,
                           line_frame, visible, text_shadow, CAP, DARK, DARK_SIDE,
                           YEL, YEL_SIDE)

FPS = 30

def smooth(u):
    u = clamp01(u); return u * u * (3 - 2 * u)

def sstep(x, e0, e1):
    """гладкая ступень для массивов numpy"""
    u = np.clip((x - e0) / np.maximum(1e-6, e1 - e0), 0, 1)
    return u * u * (3 - 2 * u)

# ----------------------------------------------------------------- лучи камеры
def ray_grid(cam, w, h):
    """направления лучей из камеры для сетки w×h (в мировых осях)"""
    sx = (np.arange(w) + 0.5) * (W / w) - W / 2
    sy = H / 2 - (np.arange(h) + 0.5) * (H / h)
    dx = np.broadcast_to(sx[None, :] / F, (h, w)).astype(np.float32)
    dy = np.broadcast_to(sy[:, None] / F, (h, w)).astype(np.float32)
    dz = np.ones((h, w), np.float32)
    if cam.yaw:
        c, s = math.cos(cam.yaw), math.sin(cam.yaw)
        dx, dz = dx * c - dz * s, dx * s + dz * c
    return dx, dy, dz

def surface_hit(cam, dx, dy, dz):
    """ближайшая поверхность зала по лучу: пол (1), стены (2), потолок (3).
    возвращает (px, py, pz, id, t)"""
    big = np.float32(1e9)
    with np.errstate(divide="ignore", invalid="ignore"):
        tf = np.where(dy < -1e-6, -cam.y / dy, big)
        tc = np.where(dy > 1e-6, (CEIL - cam.y) / dy, big)
        tl = np.where(dx < -1e-6, (-WALL - cam.x) / dx, big)
        tr = np.where(dx > 1e-6, (WALL - cam.x) / dx, big)
    tw = np.minimum(tl, tr)
    t = np.minimum(np.minimum(tf, tc), tw)
    sid = np.where(t == tf, 1, np.where(t == tw, 2, 3)).astype(np.int8)
    t = np.minimum(t, FAR)
    return cam.x + dx * t, cam.y + dy * t, cam.z + dz * t, sid, t

# ----------------------------------------------------------------- солнце и окна
def sun(t):
    """направление света ОТ окон левой стены в зал; за клип азимут уходит на 3°,
    облако меняет силу — так пятна ползут даже при стоящей камере"""
    el = math.radians(42.0)
    az = math.radians(12.0 + 0.65 * t)
    L = (math.cos(el) * math.cos(az), -math.sin(el), math.cos(el) * math.sin(az))
    power = 0.78 + 0.22 * math.sin(t * 0.9 + 0.6)
    return L, power

def lit(px, py, pz, L, soft_k=0.012):
    """освещённость точек (массивы) светом из окон левой стены; 0..1 с мягким краем
    и тенью переплёта. Точку сносим назад вдоль луча до плоскости стены x=-WALL."""
    tt = (px + WALL) / L[0]
    wy = py - L[1] * tt
    wz = pz - L[2] * tt
    soft = 0.05 + soft_k * np.clip(tt, 0, 40)
    # по высоте окна
    m = sstep(wy, 1.15 - soft, 1.15 + soft) * (1 - sstep(wy, 3.75 - soft, 3.75 + soft))
    # по длине: окна через 7 м, ширина 3.1
    u = np.mod(wz, 7.0)
    m = m * sstep(u, -soft, soft) * (1 - sstep(u, 3.1 - soft, 3.1 + soft))
    m = m * (tt > 0)
    # переплёт: 3 горизонтальные и 3 вертикальные тонкие тени
    hy = np.mod(wy - 1.15, 0.65); hz = np.mod(u, 0.775)
    bar = 0.035 + soft * 0.4
    sh = np.minimum(1.0, (1 - np.exp(-np.minimum(hy, 0.65 - hy) ** 2 / (bar * bar))) *
                    (1 - np.exp(-np.minimum(hz, 0.775 - hz) ** 2 / (bar * bar))))
    sh = 0.52 + 0.48 * sh
    return m * sh

_NOISE = None
def noise_tex():
    global _NOISE
    if _NOISE is None:
        rng = np.random.default_rng(11)
        n = 128
        a = rng.random((n, n)).astype(np.float32)
        im = Image.fromarray((a * 255).astype(np.uint8))
        im = im.resize((n * 4, n * 4), Image.BICUBIC).filter(ImageFilter.GaussianBlur(10))
        b = np.asarray(im, np.float32) / 255.0
        b = (b - b.min()) / (b.max() - b.min() + 1e-6)
        _NOISE = b
    return _NOISE

def haze_layer(cam, t, L, power, scale=6, samples=22):
    """объёмная дымка в лучах: марш по лучу на уменьшенной сетке"""
    w, h = W // scale, H // scale
    dx, dy, dz = ray_grid(cam, w, h)
    px, py, pz, sid, tmax = surface_hit(cam, dx, dy, dz)
    acc = np.zeros((h, w), np.float32)
    nz = noise_tex(); N = nz.shape[0]
    ts = np.geomspace(0.6, 38.0, samples).astype(np.float32)
    prev = 0.0
    for s in ts:
        step = s - prev; prev = s
        inside = (s < tmax)
        x = cam.x + dx * s; y = cam.y + dy * s; z = cam.z + dz * s
        m = lit(x, y, z, L, soft_k=0.02)
        # дымка гуще у пола и у окна, с медленно плывущими клубами
        dens = (0.55 + 0.45 * np.exp(-y * 0.6))
        ix = ((x * 22 + z * 9 + t * 7.0) % N).astype(np.int32)
        iy = ((y * 30 - z * 13 - t * 4.0) % N).astype(np.int32)
        cl = 0.55 + 0.9 * nz[iy, ix]
        acc += m * dens * cl * step * inside
    acc = acc * power * 0.022
    img = Image.fromarray(np.clip(acc * 255, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    return np.asarray(img.filter(ImageFilter.GaussianBlur(7)), np.float32) / 255.0

def window_light(img, cam, t, shadow_mask=None):
    """пятна света из окон на полу, стенах; плюс дымка. shadow_mask — тень предмета
    на полу (L-массив 0..1), вычитается из света"""
    L, power = sun(t)
    hw, hh = W // 2, H // 2
    dx, dy, dz = ray_grid(cam, hw, hh)
    px, py, pz, sid, tt = surface_hit(cam, dx, dy, dz)
    m = lit(px, py, pz, L)
    gain = np.where(sid == 1, 1.0, np.where(sid == 2, 0.8, 0.0)).astype(np.float32)
    # на стене пятно только на ПРАВОЙ стене (левая — со стороны света)
    gain = np.where((sid == 2) & (px < 0), 0.0, gain)
    # с дальностью свет мягче и бледнее
    gain = gain * (0.55 + 0.45 * np.exp(-tt / 30.0))
    m = m * gain * power
    if shadow_mask is not None:
        m = m * (1 - 0.88 * shadow_mask)
    m = np.asarray(Image.fromarray(np.clip(m * 255, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR),
                   np.float32) / 255.0
    hz = haze_layer(cam, t, L, power)
    arr = np.asarray(img.convert("RGB"), np.float32)
    # пол под лучом — ближе к белому с тёплым оттенком; добавка аддитивная
    warm = np.array([52.0, 48.0, 38.0], np.float32)
    arr = arr + m[..., None] * warm
    arr = arr + hz[..., None] * np.array([150.0, 142.0, 124.0], np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA"), L, power

def lit_tile(tile, corners, t, strength=0.42):
    """текстура предмета, освещённого лучом: по каждому текселю своя точка в зале"""
    L, power = sun(t)
    w, h = tile.size
    TL, TR, BR, BL = corners
    u = (np.arange(w) + 0.5) / w; v = (np.arange(h) + 0.5) / h
    U, V = np.meshgrid(u, v)
    px = TL[0] + U * (TR[0] - TL[0]) + V * (BL[0] - TL[0])
    py = TL[1] + U * (TR[1] - TL[1]) + V * (BL[1] - TL[1])
    pz = TL[2] + U * (TR[2] - TL[2]) + V * (BL[2] - TL[2])
    m = lit(px.astype(np.float32), py.astype(np.float32), pz.astype(np.float32), L) * power
    arr = np.asarray(tile, np.float32)
    k = 1.0 + strength * m[..., None]
    rgb = np.clip(arr[..., :3] * k + m[..., None] * np.array([26, 20, 8], np.float32), 0, 255)
    out = np.concatenate([rgb, arr[..., 3:4]], axis=2)
    return Image.fromarray(out.astype(np.uint8), "RGBA")

def sun_shadow_mask(cam, corners, tile, t):
    """тень предмета от окна на полу: углы сносим вдоль луча до y=0"""
    L, _ = sun(t)
    sh = []
    for c in corners:
        k = max(0.0, c[1]) / (-L[1])
        sh.append((c[0] + L[0] * k, 0.005, c[2] + L[2] * k))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = tile.split()[3]
    solid = Image.new("RGBA", tile.size, (0, 0, 0, 255)); solid.putalpha(a)
    paste_quad(lay, solid, [cam.proj(p) for p in sh])
    lay = lay.filter(ImageFilter.GaussianBlur(5)).resize((W // 2, H // 2), Image.BILINEAR)
    return np.asarray(lay.split()[3], np.float32) / 255.0

def dust(img, cam, t, L, power, n=360):
    """пыль, висящая в лучах: видна только там, где свет"""
    rng = np.random.default_rng(3)
    x = rng.uniform(-6.0, 6.0, n); y = rng.uniform(0.05, 3.6, n); z = rng.uniform(1.0, 34.0, n)
    x = x + 0.12 * np.sin(t * 0.7 + z); y = y + 0.06 * np.sin(t * 0.5 + x * 2.0)
    z = z + 0.08 * np.cos(t * 0.6 + y)
    m = lit(x.astype(np.float32), y.astype(np.float32), z.astype(np.float32), L, soft_k=0.02) * power
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(n):
        if m[i] < 0.15: continue
        sx, sy, dz_ = cam.proj((float(x[i]), float(y[i]), float(z[i])))
        if dz_ < 0.5 or sx < 0 or sx > W or sy < 0 or sy > H: continue
        r = max(1.0, 1.9 / dz_ * 9.0)
        a = int(170 * m[i] * min(1.0, 6.0 / dz_))
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 250, 236, a))

# ----------------------------------------------------------------- G03
_G03 = {}
def _g03_words():
    if not _G03:
        _G03["top"] = line_tiles(tiles_crop(["ASKING THE GOVERNMENT", "FOR A WAY TO"], 200, color=DARK, cond=0.62))
        _G03["bot"] = block_tile(tiles_crop(["SLOW IT DOWN."], 200, color=YEL, vertical=True, cond=0.68))
    return _G03

def line_tiles(words):
    """склеить плитки каждой строки в одну — вдвое-втрое меньше перспективных трансформов"""
    tw, th, tiles = words
    rows = {}
    for tile, cx, cy, base in tiles:
        rows.setdefault(round(cy), []).append((tile, cx, cy))
    out = []
    for cy in sorted(rows):
        row = rows[cy]
        x0 = min(cx - tl.size[0] / 2 for tl, cx, _ in row); x1 = max(cx + tl.size[0] / 2 for tl, cx, _ in row)
        hgt = max(tl.size[1] for tl, _, _ in row)
        im = Image.new("RGBA", (int(x1 - x0) + 2, hgt), (0, 0, 0, 0))
        for tl, cx, _ in row:
            im.alpha_composite(tl, (int(cx - tl.size[0] / 2 - x0), (hgt - tl.size[1]) // 2))
        out.append((im, (x0 + x1) / 2, cy, None))
    return (tw, th, out)

def block_tile(words):
    """склеить плитки строки в ОДНУ (place_words с rise кладёт слова друг на друга)"""
    tw, th, tiles = words
    block = Image.new("RGBA", (int(tw), int(th)), (0, 0, 0, 0))
    for tile, cx, cy, base in tiles:
        block.alpha_composite(tile, (int(cx - tile.size[0] / 2), int(cy - tile.size[1] / 2)))
    bb = block.getbbox()
    block = block.crop((bb[0], 0, bb[2], th))
    return (block.size[0], th, [(block, block.size[0] / 2, th / 2, None)])

def g03(t):
    """лучи из окон: камера едет, пятна ползут по полу и правой стене, в луче пыль и дымка,
    жёлтое слово стоит в пятне и ловит сетку переплёта, тень от него — по лучу"""
    # камера: мягкий проезд вперёд-вправо с поворотом (как на 116-118: кадр плывёт)
    u = smooth(t / 4.5)
    cam = Cam(-0.9 + 1.7 * u, 1.45, 0.4 + 1.4 * u, math.radians(9.0 - 4.0 * u))
    img = room(cam, shafts=False)
    wd = _g03_words()
    # жёлтое слово на полу в пятне света: сетка 116.40 → пятно на ~8 м в середине зала
    bot_scale = 0.46 / (CAP * 200)
    bw, bh, btiles = wd["bot"]
    block = btiles[0][0]
    yaw_b = math.radians(10.0)
    ux, nz = line_frame((0, 0, 0), yaw_b)
    center = (-3.3, 0.0, 11.2)
    w = block.size[0] * bot_scale; h = block.size[1] * bot_scale
    rise0 = 1.25
    shadow = None
    if t >= rise0:
        k = 1.0 - (1.0 - seg(t, rise0, rise0 + 0.2)) ** 1.6
        c = word_quad((center[0], center[1] - (1 - k) * h, center[2]), ux, 0.0, h / 2, w, h)
        shadow = sun_shadow_mask(cam, c, block, t)
    img, L, power = window_light(img, cam, t, shadow)
    # верхние строки на тросах (сетка 117.60: центр ~3.0 м, капитель 0.45 м)
    place_words(img, cam, t, wd["top"], (-2.3, 3.05, 12.8), math.radians(8.0), 0.45 / (CAP * 200),
                [0.10, 0.55], depth=0.14, side=DARK_SIDE, hang=True, wire_per_word=3)
    # нижнее слово: встаёт из пола в луче, освещено по месту каждого текселя
    c = word_quad(center, ux, 0.0, h / 2, w, h)
    lit_block = lit_tile(block, c, t)
    place_words(img, cam, t, (bw, bh, [(lit_block, bw / 2, bh / 2, None)]), center, yaw_b,
                bot_scale, [rise0 - 1.0], depth=0.22, side=YEL_SIDE, floor=True, shadow=True,
                rise=(rise0, 0.2))
    dust(img, cam, t, L, power)
    return img

# ----------------------------------------------------------------- G04
def floor_specks(img, cam, t, n=420, seed=7):
    """белые обрывки на полу (на плёнке пол усыпан ими) — лежат, не отражаются"""
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(img, "RGBA")
    xs = rng.uniform(-5.5, 5.5, n); zs = 3.5 + 28.0 * rng.uniform(0.0, 1.0, n) ** 2
    ang = rng.uniform(0, math.pi, n); sz = rng.uniform(0.04, 0.11, n)
    for i in range(n):
        x, z = xs[i], zs[i] + cam.z * 0.0
        if z - cam.z < 1.0: continue
        a, s = ang[i], sz[i]
        ca, sa = math.cos(a) * s, math.sin(a) * s
        pts = [cam.proj((x - ca, 0.004, z - sa)), cam.proj((x + sa * 0.6, 0.004, z - ca * 0.6)),
               cam.proj((x + ca, 0.004, z + sa)), cam.proj((x - sa * 0.6, 0.004, z + ca * 0.6))]
        if pts[0][2] < 0.6: continue
        v = int(238 + 14 * (i % 2))
        d.polygon([(p[0], p[1]) for p in pts], fill=(v, v, v - 2, 235))

def mirror_lines(img, cam, segs, color, width, strength=0.5):
    """отражение отрезков в полу: y → -y, слабее и чуть размыто"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for a, b in segs:
        pa = cam.proj((a[0], -a[1], a[2])); pb = cam.proj((b[0], -b[1], b[2]))
        d.line([(pa[0], pa[1]), (pb[0], pb[1])], fill=color, width=width)
    lay = lay.filter(ImageFilter.GaussianBlur(2.2))
    a = lay.split()[3].point(lambda v: int(v * strength)); lay.putalpha(a)
    img.alpha_composite(lay)

def box_frame(img, cam, cx, cz, w=2.4, h=2.3, dpt=1.1):
    """тёмная рама-коробка слева (на плёнке 109.0: x 24-44 %, верх y 22 %, низ 55 %)"""
    x0, x1 = cx - w / 2, cx + w / 2
    z0, z1 = cz, cz + dpt
    segs = [((x0, 0, z0), (x0, h, z0)), ((x1, 0, z0), (x1, h, z0)), ((x0, h, z0), (x1, h, z0)),
            ((x0, 0, z1), (x0, h, z1)), ((x1, 0, z1), (x1, h, z1)), ((x0, h, z1), (x1, h, z1)),
            ((x0, h, z0), (x0, h, z1)), ((x1, h, z0), (x1, h, z1))]
    mirror_lines(img, cam, segs, (70, 68, 66, 255), 4, strength=0.42)
    d = ImageDraw.Draw(img, "RGBA")
    for a, b in segs:
        pa = cam.proj(a); pb = cam.proj(b)
        d.line([(pa[0], pa[1]), (pb[0], pb[1])], fill=(58, 55, 52, 255), width=4)

def window_mirror(img, cam):
    """светлое пятно под окнами — отражение окон в глянцевом полу"""
    mask = Image.new("L", (W, H), 0)
    dl = ImageDraw.Draw(mask)
    z0 = math.floor((cam.z + 3) / 7.0) * 7.0
    for i in range(6):
        zz = z0 + i * 7.0
        for sx in (-1, 1):
            p = [cam.proj((sx * WALL, -1.15, zz)), cam.proj((sx * WALL, -1.15, zz + 3.1)),
                 cam.proj((sx * WALL, -3.75, zz + 3.1)), cam.proj((sx * WALL, -3.75, zz))]
            if min(q[2] for q in p) < 0.3: continue
            dl.polygon([(q[0], q[1]) for q in p], fill=80)
    mask = mask.filter(ImageFilter.GaussianBlur(22))
    lay = Image.new("RGBA", (W, H), (255, 255, 255, 0)); lay.putalpha(mask)
    img.alpha_composite(lay)

def mirror_word(img, cam, t, words, center, yaw, scale_m, starts, depth, side, dy_extra=0.0,
                strength=0.48, blur=3.0):
    """отражение объёмного слова в полу: та же геометрия, y → -y, альфа гаснет к дальнему
    краю (верх букв в зеркале — ниже всего на экране), лёгкое размытие"""
    tw, th, tiles = words
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ux, nz = line_frame(center, yaw)
    ymin, ymax = H, 0
    drawn = False
    for i, (tile, cx, cy, base) in enumerate(tiles):
        p = pop(starts[i], t, k0=1.0)
        if p is None: continue
        s, op = p
        w = tile.size[0] * scale_m * s; h = tile.size[1] * scale_m * s
        uu = (cx - tw / 2) * scale_m
        # зеркальная грань: низ слова на высоте -dy_extra (слово висит выше пола на dy_extra)
        c = word_quad((center[0], -dy_extra, center[2]), ux, uu, -h / 2, w, h)
        if not visible(cam, c): continue
        mir = tile.transpose(Image.FLIP_TOP_BOTTOM)   # низ букв — к линии касания
        extrude_dir(lay, cam, c, mir, depth, nz, steps=6,
                    side=tuple(int(v * 0.9) for v in side), opacity=op)
        for q in c:
            sy = cam.proj(q)[1]; ymin = min(ymin, sy); ymax = max(ymax, sy)
        drawn = True
    if not drawn: return
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(lay.split()[3], np.float32) / 255.0
    ys = np.arange(H, dtype=np.float32)[:, None]
    y0, y1 = ymin, max(ymin + 1, ymax)
    ramp = np.clip(1.0 - (ys - y0) / (y1 - y0) * 1.15, 0.0, 1.0)
    a = a * ramp * strength
    lay.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    img.alpha_composite(lay)

def big_halo(img, cam, pts, t, k=1.5, gain=0.5, mirror=False):
    """широкий тёплый ореол вокруг углей (на плёнке ореол ~1.5 м при ядре 0.6):
    считается на четверти разрешения; смешивание К ОРАНЖЕВОМУ, а не аддитивное —
    на светло-сером полу аддитив выгорает в белое"""
    sc = 4
    w, h = W // sc, H // sc
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    acc = np.zeros((h, w), np.float32)
    for i, (x, y, z, s_) in enumerate(pts):
        if mirror: y = -y
        px, py, dz = cam.proj((x, y, z))
        if dz < 0.5: continue
        r = k * s_ * F / dz / sc
        pulse = 0.85 + 0.15 * math.sin(t * 3.4 + i * 1.7)
        d2 = ((xx - px / sc) ** 2 + (yy - py / sc) ** 2) / (r * r)
        acc += np.exp(-d2 * 2.0) * pulse
    if acc.max() <= 0: return img
    acc = 1.0 - np.exp(-acc * 1.6)
    lay = Image.fromarray(np.clip(acc * 255, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    a = np.asarray(lay, np.float32)[..., None] / 255.0 * gain
    arr = np.asarray(img.convert("RGB"), np.float32)
    arr = arr * (1 - a) + a * np.array([255.0, 168.0, 70.0], np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

def ember_reflection(img, cam, pts, t, strength=0.5):
    """отражение углей: зеркальные точки рисуем отдельным проходом, размываем сильнее
    и подмешиваем вдвое слабее — разлив на полу шире самих углей"""
    mpts = [(x, -y, z, s * 1.8) for (x, y, z, s) in pts]
    base = np.asarray(img.convert("RGB"), np.float32)
    ref = embers(img.copy(), cam, mpts, t, glow=1.1)
    ref = np.asarray(big_halo(ref, cam, pts, t, k=2.6, gain=0.75, mirror=True).convert("RGB"), np.float32)
    diff = (ref - base) * strength
    diff = np.asarray(Image.fromarray(np.clip(diff + 128, 0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(16)), np.float32) - 128.0
    out = np.clip(base + diff, 0, 255).astype(np.uint8)
    return Image.fromarray(out).convert("RGBA")

def drop_curve(t, t0, dur, hfrom):
    """падение с ускорением и короткий отскок на посадке → (высота низа, присед)"""
    if t < t0: return hfrom, 0.0
    u = seg(t, t0, t0 + dur)
    y = hfrom * (1 - u * u)
    b = seg(t, t0 + dur, t0 + dur + 0.14)
    bounce = 0.04 * hfrom * math.sin(b * math.pi) * (1 if b > 0 else 0)
    sq = 0.07 * math.sin(seg(t, t0 + dur, t0 + dur + 0.10) * math.pi)
    return y + bounce, sq

_G04 = {}
def _g04_words():
    if not _G04:
        _G04["top"] = tiles_crop(["OPENAI SHUT", "THOSE AIs"], 200, color=DARK, cond=0.62)
        _G04["down"] = tiles_crop(["DOWN."], 200, color=YEL, vertical=True, cond=0.68)
    return _G04

def ember_state(t, i, base):
    """угли: парят до 3.0 с, потом по одному падают и гаснут в чёрные шарики"""
    x, y, z, s = base
    x = x + 0.06 * math.sin(t * 1.1 + i * 2.0) + 0.04 * t
    y = y + 0.06 * math.sin(t * 1.6 + i)
    t0 = 3.0 + i * 0.12
    if t < t0: return x, y, z, s, 0.0
    u = seg(t, t0, t0 + 0.28)
    yy = y * (1 - u * u) + 0.06
    return x, yy, z, s, u

def g04(t):
    """зеркало пола: угли разливаются по полу отражением, рама и окно зеркалятся;
    слово DOWN. срывается с троса и падает на пол — отражение поднимается навстречу"""
    cam = Cam(0.09 * t, 0.42, 0.33 * t, math.radians(1.5 - 0.7 * t))
    img = room(cam, shafts=False)
    # пол: блик от светлой дальней стены у горизонта — глянец
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle([0, H / 2, W, H / 2 + 150], fill=(255, 255, 255, 70))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(40)))
    window_mirror(img, cam)
    floor_specks(img, cam, t)
    box_frame(img, cam, -1.9, 12.0)
    wd = _g04_words()
    # угли: 4 штуки низко над полом на 9-10 м (сетка 109.50)
    base = [(-0.75, 0.40, 9.4, 0.95), (-0.30, 0.62, 9.7, 1.20), (0.15, 0.80, 9.5, 1.05), (0.60, 1.10, 9.9, 1.10)]
    live, dead = [], []
    for i, b in enumerate(base):
        x, y, z, s, u = ember_state(t, i, b)
        if u < 1.0:
            live.append((x, y, z, s * (1 - 0.5 * u)))
        if u > 0.0:
            dead.append((x, y, z, s, u))
    # слова на тросах: OPENAI 0.3 · SHUT 0.9 · THOSE 1.2 · AIs 1.4
    place_words(img, cam, t, wd["top"], (0.9, 2.5, 12.5), math.radians(3.0), 0.36 / (CAP * 200),
                [0.3, 0.9, 1.2, 1.4], depth=0.12, side=DARK_SIDE, hang=True, wire_per_word=2)
    # DOWN.: 1.9 висит в строке (жёлтый), 2.3 срывается, 2.55 стоит на полу
    dsc = 0.36 / (CAP * 200)
    top_y = 1.92
    t_drop = 2.3
    yb, sq = drop_curve(t, t_drop, 0.27, top_y)
    dcenter = (2.75, 0.0, 12.2)
    tw, th, tiles = wd["down"]
    # масштаб после посадки чуть крупнее: слово «садится» на пол и растёт на 15 %
    grow = 1.0 + 0.18 * smooth(seg(t, t_drop, t_drop + 0.27))
    sc = dsc * grow
    # отражение: рождается на подлёте (видно, только когда слово близко к полу)
    if t >= 1.9:
        near = clamp01(1.0 - yb / 1.4)
        if near > 0.02:
            mirror_word(img, cam, t, wd["down"], dcenter, math.radians(3.0), sc, [1.9], 0.30,
                        YEL_SIDE, dy_extra=yb, strength=0.6 * near, blur=2.5 + 6 * (1 - near))
    # само слово
    if t >= 1.9:
        if yb < 0.02:
            # сидит на полу: тень и объём
            place_words(img, cam, t, wd["down"], dcenter, math.radians(3.0), sc, [1.9], depth=0.30,
                        side=YEL_SIDE, floor=True, shadow=True)
        else:
            if t < t_drop:
                wire(img, cam, (dcenter[0] + 0.35, top_y + 0.42, dcenter[2]), color=(96, 98, 102, 230))
                wire(img, cam, (dcenter[0] + 1.05, top_y + 0.42, dcenter[2]), color=(96, 98, 102, 230))
            place_words(img, cam, t, wd["down"], (dcenter[0], yb, dcenter[2]), math.radians(3.0), sc,
                        [1.9], depth=0.30, side=YEL_SIDE, floor=True)
            if t >= t_drop:   # смаз падения
                for k in (0.12, 0.26):
                    place_words(img, cam, t, wd["down"], (dcenter[0], yb + k, dcenter[2]),
                                math.radians(3.0), sc, [1.9], depth=0.05, side=YEL_SIDE, floor=True,
                                extra_op=0.25)
    # упавшие угли: чёрные шарики с отражением
    if dead:
        d = ImageDraw.Draw(img, "RGBA")
        for (x, y, z, s, u) in dead:
            k = clamp01((u - 0.6) / 0.4)
            if k <= 0: continue
            r = 0.06
            for mirror, col, al in ((True, (40, 38, 36), int(120 * k)), (False, (26, 24, 22), int(255 * k))):
                yy = -0.06 if mirror else 0.06
                p = cam.proj((x, yy + 0.03, z))
                rr = r * F / p[2]
                d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=col + (al,))
                if not mirror:
                    d.ellipse([p[0] - rr * 0.5, p[1] - rr * 0.7, p[0] - rr * 0.1, p[1] - rr * 0.3],
                              fill=(120, 116, 110, int(170 * k)))
    if live:
        img = ember_reflection(img, cam, live, t, strength=0.8)
        img = big_halo(img, cam, live, t)
        img = embers(img, cam, live, t, glow=0.95)
    return img

SCENES = {"G03": (g03, 4.5), "G04": (g04, 4.5)}

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
