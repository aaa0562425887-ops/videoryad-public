# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть H: G01, G06).
Запуск: shard_fable_h.py <код> <out.mp4>; один кадр: ZAL_FRAME=1.9 shard_fable_h.py G01 k.png

Числа сняты с плёнки покадрово (polosy/G01_vhod, G01_okna_setka, G01_pryamo_setka,
G06_vhod, G06_vozvrat, G06_svet_setka; яркость кадра считалась числом по 1/30 с):
  G01  (пересобран 13.11 по polosy/G01.jpg + G01fin.jpg, числа в шапке блока G01 ниже)
       четыре плана, две склейки: 17.75→18.0 и 21.27→21.33. Табло DAY 243 на тросах,
       пролёт сквозь листы, клевок вниз (горизонт 17 %), листы падают, пустой зал
       (горизонт 47 %, проём 36×96 px → 55 м), чёрные слова висят, жёлтые падают на пол.
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

# ----------------------------------------------------------------- зал с наклоном
def room_p(cam, windows=True, dark=0.0, shafts=True, ropes=True):
    """Тот же зал, что zal_core.room, с ОДНОЙ правкой: линия горизонта берётся из
    проекции, а не прибита к центру кадра. В zal_core камеры без наклона, и пол там
    залит прямоугольником от H/2; у CamP есть pitch, горизонт уезжает — и пол
    оказывался нарисован поверх стен и потолка, а зеркало пола улетало на потолок.
    Отсюда был зеркальный клин вместо зала (замечание Z-0019)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    g = Image.new("L", (1, H))
    for y in range(H):
        t = y / H
        g.putpixel((0, y), int(234 - 24 * abs(t - 0.5) * 2))
    base = g.resize((W, H))
    img = Image.merge("RGBA", (base, base, base.point(lambda v: min(255, v + 3)),
                               Image.new("L", (W, H), 255)))
    d = ImageDraw.Draw(img, "RGBA")
    hor = cam.proj((0.0, cam.y, cam.z + 1e5))[1]          # <- вся правка
    d.rectangle([0, hor, W, H], fill=(211, 214, 218, 255))      # пол — светлее, как в оригинале
    d.rectangle([0, 0, W, hor], fill=(230, 232, 235, 255))      # дальняя стена/воздух
    for sx in (-1, 1):
        p = [cam.proj((sx * WALL, CEIL, cam.z + 2.0)), cam.proj((sx * WALL, CEIL, cam.z + FAR)),
             cam.proj((sx * WALL, 0.0, cam.z + FAR)), cam.proj((sx * WALL, 0.0, cam.z + 2.0))]
        Z._poly(d, p, (222, 225, 229, 255))
    if windows:
        z0 = math.floor((cam.z + 3) / 7.0) * 7.0
        for i in range(10):
            zz = z0 + i * 7.0
            for sx in (-1, 1):
                p = [cam.proj((sx * WALL, 3.75, zz)), cam.proj((sx * WALL, 3.75, zz + 3.1)),
                     cam.proj((sx * WALL, 1.15, zz + 3.1)), cam.proj((sx * WALL, 1.15, zz))]
                Z._poly(d, p, (251, 252, 253, 255))
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
                dl.polygon([(q[0], q[1]) for q in p], fill=(255, 255, 255, 120))
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
    if dark > 0:
        sh = Image.new("RGBA", (W, H), (8, 7, 6, int(235 * clamp01(dark))))
        img.alpha_composite(sh)
    return img


# ================================================================= G01: 17.0-22.0 по плёнке
# Кусок — ЧЕТЫРЕ плана, два из них склейкой (сверено по polosy/G01.jpg и G01fin.jpg):
#   A 17.00-17.75  табло DAY 243 на тросах, камера задрана (горизонт 78 %), повёрнута
#                  влево ~8°, зал узкий: левая стена 2,6 м, правая 7,8 м, проём на 36 м
#                  (ширина проёма 54 px → 1,0 м / 36 м). Цифры докидываются 17.0-17.2.
#   B 18.00-19.75  (склейка) пролёт сквозь облако висящих листов, «I WASN'T» с 18.5,
#                  «EXAGGERATING.» с 19.0; слова растут 0,41 → 0,60 ширины кадра за 1,25 с.
#   C 19.75-21.27  камера клюёт вниз (горизонт 17 % кадра, проём 0,61 ширины → поворот
#                  влево 6°), листы падают и ЛЕЖАТ на полу, «IF» 20.20, «ANYTHING...» 20.27.
#   D 21.33-22.00  (склейка) пустой зал, камера в 6,5 м от левой стены, проём по центру
#                  (36×96 px → 55 м), горизонт ~47 %. Чёрные I / DIDN'T / GO ВИСЯТ на тросах
#                  (центр 2,6 м над полом, 9 м от камеры): 21.333 / 21.467 / 21.667.
#                  Жёлтые FAR (0,9 м, 9,8 м, слева) и ENOUGH. (1,0 м, 11 м, справа) ПАДАЮТ
#                  на пол сверху: FAR 21.62→21.73 (на 21.667 целое, на 0,48 м выше места),
#                  ENOUGH. 21.85→21.94 (в 21.933 уже стоит).
#   Свет — из окон ЛЕВОЙ стены, низко (наклон 1:4) и чуть вперёд: пятна лежат справа,
#   длинными косыми полосами, последнее окно у угла кладёт пятно на дальнюю стену
#   левее проёма (кадр 21.333). Окна 3,3×2,5 м (низ 1,4), шаг 5 м, переплёт 5×5.
FONT_B = "Oswald-Bold.ttf"
OK_W, OK_Y0, OK_Y1, OK_STEP, OK_COLS, OK_ROWS = 3.3, 1.5, 4.0, 4.7, 5, 5
SUN = (4.5, -1.0, 0.8)            # куда идёт луч из окна: вправо, вниз, вперёд
SHADOW = (5.0, -1.0, -0.9)        # тень слов на полу: вправо и чуть к камере (кадр 21.933)            # куда идёт луч из окна: вправо, вниз, вперёд

class Hall:
    def __init__(s, xl, xr, zfar, ceil=5.2, okz0=3.0, okz0_r=5.5, slot_x=0.0, corner_win=True,
                 vid_l=25.0, vid_r=(0.0, 25.0)):
        s.xl, s.xr, s.zfar, s.ceil = xl, xr, zfar, ceil
        s.okz0, s.okz0_r, s.slot_x, s.corner_win = okz0, okz0_r, slot_x, corner_win
        s.vid_l, s.vid_r = vid_l, vid_r          # какие окна РИСУЮТСЯ (дальность от камеры): плёнка показывает 2-3

HALL_A = Hall(-3.8, 5.5, 39.0, okz0=4.2, okz0_r=17.0, slot_x=4.1, corner_win=False, vid_l=25.0, vid_r=(0.0, 25.0))
HALL_D = Hall(-6.4, 18.0, 55.0, okz0=10.7, okz0_r=5.5, slot_x=0.0, corner_win=True, vid_l=25.0, vid_r=(35.0, 999.0))

def _okna(hall, side):
    """список окон стены: (z0, z1) — левая стена может иметь укороченное окно у угла"""
    z0 = hall.okz0 if side < 0 else hall.okz0_r
    out = []
    zz = z0
    while zz < hall.zfar - 0.3:
        z1 = min(zz + OK_W, hall.zfar - 0.1)
        if z1 - zz > 1.0: out.append((zz, z1))
        zz += OK_STEP
    if side < 0 and hall.corner_win:
        zc = hall.zfar - 2.2
        if not out or out[-1][1] < zc - 0.5: out.append((zc, hall.zfar - 0.1))
    return out

def _sun_hit(hall, p):
    """точка на окне левой стены → куда ложится луч: пол (y=0), дальняя стена или правая.
    Возвращает (поверхность, точка)."""
    x, y, z = p
    sx, sy, sz = SUN
    best = None
    for surf, tt in (("floor", y / -sy if sy < 0 else None),
                     ("far", (hall.zfar - z) / sz if sz > 0 else None),
                     ("right", (hall.xr - x) / sx if sx > 0 else None)):
        if tt is None or tt < 0: continue
        if best is None or tt < best[1]: best = (surf, tt)
    surf, tt = best
    return surf, (x + sx * tt, y + sy * tt, z + sz * tt)

def zal2(cam, hall=HALL_D, ropes=8):
    """Зал по кадрам плёнки: стены на hall.xl / hall.xr, дальняя стена hall.zfar, окна
    с переплётом 5×5 в нишах, бетонный пол (тёмный у камеры, светлеет к горизонту),
    потолок с глубокими поперечными балками, косые пятна солнца от окон левой стены,
    жёлтый проём 1,0×2,75 м на дальней стене. Горизонт берётся ИЗ ПРОЕКЦИИ."""
    img = Image.new("RGBA", (W, H), (226, 226, 226, 255))
    d = ImageDraw.Draw(img, "RGBA")
    hor = cam.proj((cam.x, cam.y, cam.z + 1e5))[1]
    xl, xr, zf, ce = hall.xl, hall.xr, hall.zfar, hall.ceil
    zn = cam.z + 0.3

    # --- пол: градиент от тёмного бетона у ног к светлому у горизонта
    y0 = int(max(0, min(H, hor)))
    if y0 < H:
        g = Image.new("RGBA", (1, H - y0))
        for y in range(H - y0):
            k = (y / max(1, H - y0)) ** 0.55
            g.putpixel((0, y), lerp3((186, 182, 176), (128, 123, 117), k) + (255,))
        img.alpha_composite(g.resize((W, H - y0)), (0, y0))
    for i in range(40):                                    # швы плит
        zz = math.floor(cam.z / 3.0) * 3.0 + i * 3.0
        if zz < zn or zz > zf: continue
        a = cam.proj((xl, 0.0, zz)); b = cam.proj((xr, 0.0, zz))
        far = clamp01((zz - cam.z) / 30.0)
        d.line([(a[0], a[1]), (b[0], b[1])], fill=(112, 108, 103, int(110 * (1 - far))), width=1)
    xx = math.floor(xl / 3.0) * 3.0
    while xx < xr:
        if xx > xl + 0.2:
            a = cam.proj((xx, 0.0, zn + 0.3)); b = cam.proj((xx, 0.0, zf))
            d.line([(a[0], a[1]), (b[0], b[1])], fill=(112, 108, 103, 70), width=1)
        xx += 3.0

    # --- потолок: плоскость в тени и глубокие светлые балки поперёк
    Z._poly(d, [cam.proj((xl, ce, zn)), cam.proj((xr, ce, zn)), cam.proj((xr, ce, zf)), cam.proj((xl, ce, zf))],
            (176, 176, 177, 255))
    zz = math.floor(cam.z / 1.5) * 1.5
    balki = []
    while zz < zf:
        if zz > zn: balki.append(zz)
        zz += 1.5
    for zz in reversed(balki):
        far = clamp01((zz - cam.z) / 40.0)
        front = lerp3((222, 222, 223), (210, 210, 211), far) + (255,)
        low = lerp3((246, 246, 246), (232, 232, 232), far) + (255,)
        Z._poly(d, [cam.proj((xl, ce, zz)), cam.proj((xr, ce, zz)),
                    cam.proj((xr, ce - 0.35, zz)), cam.proj((xl, ce - 0.35, zz))], front)
        Z._poly(d, [cam.proj((xl, ce - 0.35, zz)), cam.proj((xr, ce - 0.35, zz)),
                    cam.proj((xr, ce - 0.35, zz + 0.3)), cam.proj((xl, ce - 0.35, zz + 0.3))], low)

    # --- стены и дальняя стена
    for xw, col in ((xl, (229, 229, 228)), (xr, (222, 222, 221))):
        Z._poly(d, [cam.proj((xw, ce, zn)), cam.proj((xw, ce, zf)), cam.proj((xw, 0.0, zf)), cam.proj((xw, 0.0, zn))],
                col + (255,))
    Z._poly(d, [cam.proj((xl, ce, zf)), cam.proj((xr, ce, zf)), cam.proj((xr, 0.0, zf)), cam.proj((xl, 0.0, zf))],
            (212, 211, 209, 255))

    # --- окна с переплётом 5×5 в нишах
    for side, xw in ((-1, xl), (1, xr)):
        for (z0, z1) in _okna(hall, side):
            if z1 < zn + 0.5: continue
            if side < 0 and z0 > cam.z + hall.vid_l: continue
            if side > 0 and not (hall.vid_r[0] <= z0 - cam.z <= hall.vid_r[1]): continue
            zq0, zq1 = max(z0, zn), z1
            n = [cam.proj((xw, OK_Y1 + 0.15, zq0 - 0.15)), cam.proj((xw, OK_Y1 + 0.15, zq1 + 0.15)),
                 cam.proj((xw, OK_Y0 - 0.15, zq1 + 0.15)), cam.proj((xw, OK_Y0 - 0.15, zq0 - 0.15))]
            Z._poly(d, n, (168, 168, 170, 255))
            p = [cam.proj((xw, OK_Y1, zq0)), cam.proj((xw, OK_Y1, zq1)),
                 cam.proj((xw, OK_Y0, zq1)), cam.proj((xw, OK_Y0, zq0))]
            Z._poly(d, p, (253, 253, 251, 255))
            px = abs(p[2][1] - p[1][1]) / (OK_Y1 - OK_Y0)
            wl = max(1, int(px * 0.03))
            d.line([(q[0], q[1]) for q in p] + [(p[0][0], p[0][1])], fill=(84, 84, 86, 255), width=wl)
            for k in range(1, OK_ROWS):
                yy = OK_Y0 + (OK_Y1 - OK_Y0) * k / OK_ROWS
                a = cam.proj((xw, yy, zq0)); b = cam.proj((xw, yy, zq1))
                d.line([(a[0], a[1]), (b[0], b[1])], fill=(84, 84, 86, 255), width=wl)
            for k in range(1, OK_COLS):
                zk = z0 + (z1 - z0) * k / OK_COLS
                if zk < zq0: continue
                a = cam.proj((xw, OK_Y1, zk)); b = cam.proj((xw, OK_Y0, zk))
                d.line([(a[0], a[1]), (b[0], b[1])], fill=(84, 84, 86, 255), width=wl)

    # --- пятна солнца: каждая ячейка переплёта левой стены отбрасывается по лучу SUN
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay, "RGBA")
    for (z0, z1) in _okna(hall, -1):
        if z0 < cam.z + 14.0: continue          # ближние окна пятен в кадр не кладут (плёнка: пол у ног ровный)
        a_fl = int(30 + 120 * clamp01((z0 - cam.z - 20.0) / 20.0))  # дальние пятна ярче (кадр 21.333)
        whole = [_sun_hit(hall, (xl, OK_Y1, z0)), _sun_hit(hall, (xl, OK_Y1, z1)),
                 _sun_hit(hall, (xl, OK_Y0, z1)), _sun_hit(hall, (xl, OK_Y0, z0))]
        if all(h[0] == "floor" for h in whole):     # на полу пятно цельное, без клеток (кадр 21.333)
            pts = [h[1] for h in whole]
            if min(p[2] for p in pts) > zn + 0.2:
                dl.polygon([(q[0], q[1]) for q in (cam.proj(p) for p in pts)], fill=(255, 254, 246, a_fl))
            continue
        for i in range(OK_COLS):
            for j in range(OK_ROWS):
                za, zb = z0 + (z1 - z0) * i / OK_COLS, z0 + (z1 - z0) * (i + 1) / OK_COLS
                ya, yb = OK_Y0 + (OK_Y1 - OK_Y0) * j / OK_ROWS, OK_Y0 + (OK_Y1 - OK_Y0) * (j + 1) / OK_ROWS
                sh = 0.06
                hits = [_sun_hit(hall, (xl, yb - sh, za + sh)), _sun_hit(hall, (xl, yb - sh, zb - sh)),
                        _sun_hit(hall, (xl, ya + sh, zb - sh)), _sun_hit(hall, (xl, ya + sh, za + sh))]
                if len(set(h[0] for h in hits)) != 1: continue
                pts = [h[1] for h in hits]
                if min(p[2] for p in pts) < zn + 0.2: continue
                pr = [cam.proj(p) for p in pts]
                alpha = 150 if hits[0][0] == "floor" else 200
                dl.polygon([(q[0], q[1]) for q in pr], fill=(255, 254, 246, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(lay)

    # --- жёлтый проём на дальней стене
    sx = hall.slot_x
    Z._poly(d, [cam.proj((sx - 0.5, 2.75, zf - 0.05)), cam.proj((sx + 0.5, 2.75, zf - 0.05)),
                cam.proj((sx + 0.5, 0.0, zf - 0.05)), cam.proj((sx - 0.5, 0.0, zf - 0.05))], YEL)

    # --- тросы с потолка
    if ropes:
        rng = np.random.default_rng(3)
        for i in range(ropes):
            zz = float(rng.uniform(4.0, 34.0)) + math.floor(cam.z / 4.0) * 4.0
            xx = float(rng.uniform(xl + 0.5, min(xr - 0.5, xl + 12.0)))
            yy = float(rng.uniform(1.0, 3.4))
            if zz - cam.z < 1.2 or zz > zf - 1: continue
            a = cam.proj((xx, ce, zz)); b = cam.proj((xx, yy, zz))
            far = clamp01((zz - cam.z) / 40.0)
            d.line([(a[0], a[1]), (b[0], b[1])], fill=lerp3((70, 70, 72), (160, 160, 162), far) + (235,), width=1)
    return img

# ------------------------------------------------------------ объёмные слова
_TEXT_TEX = {}
def slovo_tex(slovo, cvet, kegl=320, stretch=1.0):
    """текстура лицевой грани слова (прозрачный фон); ширина/высота в px"""
    key = (slovo, cvet, kegl, stretch)
    if key in _TEXT_TEX: return _TEXT_TEX[key]
    fnt = Z.font(FONT_B, kegl)
    tmp = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    bb = tmp.textbbox((0, 0), slovo, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    im = Image.new("RGBA", (tw + 8, th + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), slovo, font=fnt, fill=cvet + (255,))
    if stretch != 1.0: im = im.resize((int(im.width * stretch), im.height), Image.LANCZOS)
    _TEXT_TEX[key] = im
    return im

def obyom(canvas, cam, corners, tex, depth, side, steps=10, skos=(0.05, -0.30)):
    """объёмное слово: лицевая грань на corners (TL,TR,BR,BL); бока — копии, уходящие
    в глубину +z и вниз-вправо (skos в долях высоты): на плёнке тёмный низ у каждой буквы"""
    cap = abs(corners[0][1] - corners[3][1])
    for i in range(steps, 0, -1):
        k = i / steps
        cs = [(c[0] + skos[0] * cap * k, c[1] + skos[1] * cap * k, c[2] + depth * k) for c in corners]
        solid = Image.new("RGBA", tex.size, side + (255,))
        solid.putalpha(tex.split()[3])
        paste_quad(canvas, solid, [cam.proj(p) for p in cs])
    paste_quad(canvas, tex, [cam.proj(p) for p in corners])

def slovo_visit(canvas, cam, slovo, x, y, z, cap, cvet, side, k=1.0, depth=0.22, tros=True, stretch=1.0):
    """слово ВИСИТ на тросе, центр (x, y, z); k — выскок (out_back)"""
    if k <= 0.001: return
    tex = slovo_tex(slovo, cvet, stretch=stretch)
    w = cap * tex.width / tex.height
    s = out_back(k)
    hw, hh = w * s / 2, cap * s / 2
    c = [(x - hw, y + hh, z), (x + hw, y + hh, z), (x + hw, y - hh, z), (x - hw, y - hh, z)]
    if tros:
        d = ImageDraw.Draw(canvas, "RGBA")
        a = cam.proj((x, cam.y + 20.0, z)); b = cam.proj((x, y + hh, z))
        d.line([(a[0], a[1]), (b[0], b[1])], fill=(64, 64, 66, 235), width=2)
    obyom(canvas, cam, c, tex, depth, side)

def slovo_iz_pola(canvas, cam, slovo, x, z, cap, cvet, side, k, depth=0.30, stretch=1.0):
    """слово ПАДАЕТ на пол и встаёт на него: k 0 — ещё в 1,2 м над полом, 1 — стоит.
    По плёнке FAR на 21.667 уже целое, но верх на 0.51 вместо 0.60 (на 0,48 м выше
    места), на 21.733 стоит; ход — квадрат (как при падении). Тень на полу по SHADOW."""
    if k <= 0.001: return
    tex = slovo_tex(slovo, cvet, stretch=stretch)
    w = cap * tex.width / tex.height
    u = clamp01(k)
    lift = 1.2 * (1.0 - u) ** 2                  # низ слова над полом, пока падает
    c = [(x - w / 2, lift + cap, z), (x + w / 2, lift + cap, z), (x + w / 2, lift, z), (x - w / 2, lift, z)]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # тень на полу по лучу SUN от вышедшей части
    if u > 0.05:
        hgt = cap
        sx, sy, sz = SHADOW
        sh = [(x - w / 2 + sx * hgt, 0.01, z + sz * hgt), (x + w / 2 + sx * hgt, 0.01, z + sz * hgt),
              (x + w / 2, 0.01, z), (x - w / 2, 0.01, z)]
        mask = tex
        a = mask.split()[3].point(lambda v: int(v * 0.72 * u))
        dark = Image.new("RGBA", mask.size, (48, 44, 38, 255)); dark.putalpha(a)
        dark = dark.filter(ImageFilter.GaussianBlur(4))
        paste_quad(canvas, dark, [cam.proj(p) for p in sh])
    obyom(lay, cam, c, tex, depth, side)
    # срез всего, что ниже линии пола на этой дальности
    fl = cam.proj((x - w / 2, -0.12 * cap, z)); fr_ = cam.proj((x + w / 2, -0.12 * cap, z))
    xs0, xs1 = min(fl[0], fr_[0]) - 50, max(fl[0], fr_[0]) + 50
    dl = ImageDraw.Draw(lay)
    dl.polygon([(xs0, fl[1]), (xs1, fr_[1]), (xs1, H + 10), (xs0, H + 10)], fill=(0, 0, 0, 0))
    canvas.alpha_composite(lay)

# ------------------------------------------------------------ листы с постами
LISTY_TXT = [
    ("Same old grift", "Reddit · r/agi · Feb 12, 2026"),
    ("This is called\ncontent marketing.", "Reddit · r/artificialintelligence · Feb 14, 2026"),
    ("This is AI hype.\nStop being so\ncredulous to this\nkind of propaganda.", "Reddit · r/technology · Feb 12, 2026"),
    ("A lot of fear\nmongering.", "Reddit · r/singularity · Feb 13, 2026"),
    ("...it's a joke of an\nessay. Dude is just\ntrying to hype AI", "Reddit · r/ProductManagement · Feb 12, 2026"),
    ("It's an ad for some\nguy's hypeman\nstartup. Ignore.", "Reddit · r/BetterOffline · Feb 13, 2026"),
    ("Completely\ndelusional.", "Reddit · r/Futurology · Feb 12, 2026"),
    ("Who paid for this?", "Reddit · r/agi · Feb 13, 2026"),
    ("Nothing grows\nexponentially\nforever.", "Reddit · r/artificial · Feb 14, 2026"),
    ("Hype, hype, hype.", "Reddit · r/technology · Feb 12, 2026"),
]
BODY_TXT = ("What's the point in using these tools if you're gonna replace us in a few years? "
            "It's weird the author says that but then his conclusion is basically go spend money on stuff I'm invested in. "
            "Good comparison is apt. I remember when the hype started in Jan 2020 when those videos "
            "came out and most of us were like well it's a problem but it's not going to affect me. "
            "They focused on making AI great at writing code first, because building AI requires a lot of code.")

_LIST_TEX = {}
def post_tex(i, w_px=640, h_px=420, bold=42, body=False):
    """лист: жирный заголовок, строка источника, мелкий серый текст"""
    key = (i, w_px, h_px, bold, body)
    if key in _LIST_TEX: return _LIST_TEX[key]
    im = Image.new("RGBA", (w_px, h_px), (250, 250, 248, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w_px - 1, h_px - 1], outline=(222, 222, 220, 255), width=2)
    head, src = LISTY_TXT[i % len(LISTY_TXT)]
    fb = Z.font(FONT_B, bold); fs = Z.font("Arimo-Bold.ttf", max(10, int(bold * 0.32)))
    ft = Z.font("Arimo-Bold.ttf", max(9, int(bold * 0.30)))
    y = int(bold * 0.6)
    for ln in head.split("\n"):
        d.text((int(bold * 0.6), y), ln, font=fb, fill=(24, 24, 26, 255)); y += int(bold * 1.05)
    y += int(bold * 0.2)
    d.text((int(bold * 0.6), y), src, font=fs, fill=(120, 120, 124, 255)); y += int(bold * 0.7)
    if body:
        words = BODY_TXT.split(); ln = ""
        x0 = int(bold * 0.6)
        while y < h_px - bold and words:
            wd = words.pop(0)
            if d.textlength(ln + " " + wd, font=ft) > w_px - 2 * x0 and ln:
                d.text((x0, y), ln, font=ft, fill=(96, 96, 100, 255)); y += int(bold * 0.42); ln = wd
            else:
                ln = (ln + " " + wd).strip()
        if ln and y < h_px - bold: d.text((x0, y), ln, font=ft, fill=(96, 96, 100, 255))
    _LIST_TEX[key] = im
    return im

# (x, z) — где лист ЛЯЖЕТ на пол (мир); y_h — высота центра, пока висит; w, h — ширина, высота/глубина
LISTY = [
    # шесть листов, видимых лежащими в плане C (сняты с кадра 20.667)
    dict(x=-2.2, z=10.7, y_h=2.4, w=6.2, h=4.4, i=2, body=True, big=True),
    dict(x=-2.4, z=4.9, y_h=1.3, w=1.0, h=1.3, i=3),
    dict(x=-2.0, z=6.4, y_h=2.9, w=0.85, h=1.2, i=0),
    dict(x=0.5, z=6.1, y_h=1.9, w=1.0, h=2.3, i=5),
    dict(x=0.1, z=8.5, y_h=3.1, w=0.8, h=1.6, i=4),
    dict(x=-1.0, z=9.1, y_h=1.6, w=0.6, h=1.0, i=1),
    # облако в плане B — ложатся позади и мимо кадра C
    dict(x=-3.9, z=0.2, y_h=3.1, w=1.5, h=1.0, i=0),
    dict(x=-0.2, z=0.6, y_h=3.3, w=1.4, h=0.9, i=1),
    dict(x=1.2, z=1.0, y_h=2.9, w=1.6, h=1.1, i=2, body=True),
    dict(x=-4.3, z=1.3, y_h=1.2, w=1.6, h=1.1, i=4, body=True),
    dict(x=-2.3, z=2.5, y_h=2.4, w=1.9, h=1.3, i=2, body=True),
    dict(x=0.9, z=1.9, y_h=1.1, w=1.4, h=0.9, i=5),
    dict(x=-3.0, z=2.2, y_h=0.9, w=1.3, h=0.9, i=3),
    dict(x=-0.9, z=2.4, y_h=1.4, w=1.2, h=0.8, i=4),
    dict(x=-4.8, z=2.5, y_h=2.5, w=1.2, h=0.8, i=6),
    dict(x=1.6, z=0.5, y_h=1.8, w=1.0, h=0.7, i=7),
    dict(x=-2.4, z=-1.0, y_h=2.6, w=1.6, h=1.1, i=8, body=True),
    dict(x=0.2, z=-1.6, y_h=1.5, w=1.3, h=0.9, i=9),
    dict(x=-3.6, z=-2.4, y_h=2.0, w=1.4, h=0.9, i=1),
    dict(x=1.1, z=-2.9, y_h=3.0, w=1.2, h=0.8, i=3),
]

def listy_g01(img, cam, t, tf):
    """tf — ход падения 0..1 (0 висят, 1 лежат); рисуются от дальних к ближним"""
    order = sorted(range(len(LISTY)), key=lambda i: -LISTY[i]["z"])
    for i in order:
        L = LISTY[i]
        x, z, w, h = L["x"], L["z"], L["w"], L["h"]
        hang = [(x - w / 2, L["y_h"] + h / 2, z), (x + w / 2, L["y_h"] + h / 2, z),
                (x + w / 2, L["y_h"] - h / 2, z), (x - w / 2, L["y_h"] - h / 2, z)]
        lie = [(x - w / 2, 0.02, z + h / 2), (x + w / 2, 0.02, z + h / 2),
               (x + w / 2, 0.02, z - h / 2), (x - w / 2, 0.02, z - h / 2)]
        u = out_cubic(tf)
        c = [tuple(hang[k][j] + (lie[k][j] - hang[k][j]) * u for j in range(3)) for k in range(4)]
        zc = sum(p[2] for p in c) / 4
        if zc - cam.z < 0.6: continue
        pr = [cam.proj(p) for p in c]
        xs = [p[0] for p in pr]; ys = [p[1] for p in pr]
        if max(xs) < -50 or min(xs) > W + 50 or max(ys) < -50 or min(ys) > H + 50: continue
        if max(xs) - min(xs) < 6: continue
        if tf < 0.999:
            d = ImageDraw.Draw(img, "RGBA")
            a = cam.proj((x, cam.y + 20.0, z)); b = cam.proj(((c[0][0] + c[1][0]) / 2, c[0][1], z))
            d.line([(a[0], a[1]), (b[0], b[1])], fill=(70, 70, 72, 220), width=1)
        tex = post_tex(L["i"], w_px=min(2400, int(420 * w)), h_px=min(2400, int(420 * h)),
                       bold=40, body=L.get("body", False))
        paste_quad(img, tex, pr)

# ------------------------------------------------------------ табло DAY 243
def tablo_tex(t):
    """чёрное табло 2,2×2,2 м: DAY, три перекидные цифры, дата; докидывание 215→243 за 0,22 с"""
    S = 900
    im = Image.new("RGBA", (S, S), (16, 16, 17, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S - 1, S - 1], outline=(70, 70, 72, 255), width=6)
    d.text((70, 60), "DAY", font=Z.font(FONT_B, 92), fill=(236, 236, 234, 255))
    u = seg(t, 0.0, 0.22)
    old, new = "215", "243"
    fd = Z.font("ArialBlack.ttf", 330)
    tw = 250; gap = 24; x0 = (S - 3 * tw - 2 * gap) // 2; ty0 = 250; th = 400
    for i in range(3):
        x = x0 + i * (tw + gap)
        d.rectangle([x, ty0, x + tw, ty0 + th], fill=(28, 28, 30, 255))
        tile_new = Image.new("RGBA", (tw, th), (28, 28, 30, 255))
        tile_old = Image.new("RGBA", (tw, th), (28, 28, 30, 255))
        for tile, ch, col in ((tile_new, new[i], (236, 190, 48, 255)), (tile_old, old[i], (240, 240, 238, 255))):
            dd = ImageDraw.Draw(tile)
            bb = dd.textbbox((0, 0), ch, font=fd)
            dd.text(((tw - (bb[2] - bb[0])) // 2 - bb[0], (th - (bb[3] - bb[1])) // 2 - bb[1]), ch, font=fd, fill=col)
        top_new = tile_new.crop((0, 0, tw, th // 2)); bot_new = tile_new.crop((0, th // 2, tw, th))
        top_old = tile_old.crop((0, 0, tw, th // 2)); bot_old = tile_old.crop((0, th // 2, tw, th))
        ui = clamp01(u * 1.0 - i * 0.12 * (1 - u))      # цифры докидываются почти разом
        if ui >= 1.0:
            im.alpha_composite(top_new, (x, ty0)); im.alpha_composite(bot_new, (x, ty0 + th // 2))
        else:
            im.alpha_composite(top_new, (x, ty0)); im.alpha_composite(bot_old, (x, ty0 + th // 2))
            if ui < 0.5:                                   # верхняя створка старой падает
                hh = max(1, int(th // 2 * (1 - 2 * ui)))
                im.alpha_composite(top_old.resize((tw, hh)), (x, ty0 + th // 2 - hh))
            else:                                          # нижняя створка новой раскрывается
                hh = max(1, int(th // 2 * (2 * ui - 1)))
                im.alpha_composite(bot_new.resize((tw, hh)), (x, ty0 + th // 2))
        d.line([(x, ty0 + th // 2), (x + tw, ty0 + th // 2)], fill=(10, 10, 10, 255), width=5)
    fdate = Z.font("ArialBlack.ttf", 74)
    date = "OCT 10 2026" if u > 0.6 else "SEP 1 2026"
    bb = d.textbbox((0, 0), date, font=fdate)
    d.text(((S - (bb[2] - bb[0])) // 2 - bb[0], 718), date, font=fdate, fill=(236, 236, 234, 255))
    return im

def tablo(img, cam, t, center, size=2.2):
    cx, cy, cz = center
    yaw = cam.yaw
    c = Z.quad((cx, cy, cz), size, size, yaw=yaw)
    d = ImageDraw.Draw(img, "RGBA")
    for k in (-0.6, 0.6):
        tx = cx + k * size / 2 * math.cos(yaw); tz = cz + k * size / 2 * math.sin(yaw)
        a = cam.proj((tx, cam.y + 20.0, tz)); b = cam.proj((tx, cy + size / 2, tz))
        d.line([(a[0], a[1]), (b[0], b[1])], fill=(60, 60, 62, 240), width=2)
    tex = tablo_tex(t)
    # тонкий бок табло
    for i in (3, 2, 1):
        cs = [(p[0] - 0.012 * i * math.sin(yaw), p[1], p[2] + 0.012 * i * math.cos(yaw)) for p in c]
        side = Image.new("RGBA", tex.size, (40, 40, 42, 255))
        paste_quad(img, side, [cam.proj(p) for p in cs])
    paste_quad(img, tex, [cam.proj(p) for p in c])

# ------------------------------------------------------------ камера и сборка куска
def g01_cam(t):
    """четыре плана; t 0..5 ↔ 17.0..22.0 плёнки"""
    if t < 1.0:                                   # A: табло, камера почти стоит, задрана
        yaw = math.radians(8.0 + 1.1 * t)
        return HALL_A, CamP(0.0, 1.55, 0.3 * t, yaw, math.radians(7.5))
    if t < 4.333:                                 # B → C: пролёт сквозь листы, клевок вниз
        if t < 3.0: z = -5.0 + 2.2 * (t - 1.0)
        else: z = -0.6 + 0.6 * (t - 3.0)
        pitch = math.radians(8.0) + math.radians(-18.3) * smooth(seg(t, 2.70, 3.20))
        yaw = math.radians(6.0)
        return HALL_D, CamP(-1.0, 1.55, z, yaw, pitch)
    # D: пустой зал, склейка на 21.333
    tt = t - 4.333
    return HALL_D, CamP(0.0, 1.55, 1.5 * tt, 0.0, math.radians(-0.8))

def g01(t):
    """Белый зал как единственная площадка — кусок 17.0-22.0 с плёнки, четыре плана
    (см. шапку блока): табло DAY 243 → пролёт сквозь листы под «I WASN'T EXAGGERATING.»
    → листы падают на пол под «IF ANYTHING...» → пустой зал, чёрные слова висят,
    жёлтые встают из пола."""
    hall, cam = g01_cam(t)
    if t < 1.0:
        img = zal2(cam, hall, ropes=5)
        yaw = cam.yaw
        tablo(img, cam, t, (-5.8 * math.sin(yaw), 2.55, 5.8 * math.cos(yaw)), size=2.3)
        return img
    if t < 4.333:
        img = zal2(cam, hall, ropes=14)
        tf = seg(t, 2.90, 3.13)
        listy_g01(img, cam, t, tf)
        # «I WASN'T» / «EXAGGERATING.» висят впереди, центр по оси камеры плана B
        zl = 4.85; xl_ = -1.0 - (zl + 1.15) * math.sin(math.radians(6.0))
        up = 3.5 * seg(t, 2.95, 3.10) ** 2
        slovo_visit(img, cam, "I WASN'T", xl_, 3.30 + up, zl, 0.70, (22, 22, 24), (58, 58, 60),
                    k=seg(t, 1.30, 1.45), depth=0.25, stretch=1.25)
        slovo_visit(img, cam, "EXAGGERATING.", xl_, 2.25 + up, zl, 0.80, (22, 22, 24), (58, 58, 60),
                    k=seg(t, 1.80, 1.95), depth=0.25)
        # плоская надпись над большим листом: IF 20.20, ANYTHING... 20.27
        if t >= 3.20:
            slova = "IF" if t < 3.267 else "IF ANYTHING..."
            tex = slovo_tex(slova, (22, 22, 24))
            full = slovo_tex("IF ANYTHING...", (22, 22, 24))
            cap = 0.62; wfull = cap * full.width / full.height
            w = cap * tex.width / tex.height
            xc = -1.0 - 11.0 * math.sin(math.radians(6.0)) - 0.37
            x0 = xc - wfull / 2
            c = [(x0, 0.53 + cap / 2, 10.7), (x0 + w, 0.53 + cap / 2, 10.7),
                 (x0 + w, 0.53 - cap / 2, 10.7), (x0, 0.53 - cap / 2, 10.7)]
            paste_quad(img, tex, [cam.proj(p) for p in c])
        return img
    img = zal2(cam, hall, ropes=6)
    tt = t - 4.333
    zb = 9.9                                   # чёрные висят в 9 м от камеры на 21.933
    x_i = -1.95 - 0.30 * (1 - smooth(seg(tt, 0.0, 0.07)))      # «I» качнулось на тросе (21.333→21.400)
    for slovo, xx, k in (("I", x_i, 1.0), ("DIDN'T", -0.40, seg(tt, 0.07, 0.13)), ("GO", 1.70, seg(tt, 0.27, 0.33))):
        slovo_visit(img, cam, slovo, xx, 2.40, zb, 0.66, (22, 22, 24), (58, 58, 60), k=k, depth=0.22)
    slovo_iz_pola(img, cam, "FAR", -2.05, 9.75, 0.88, (236, 190, 48), (166, 126, 22), seg(tt, 0.29, 0.40), depth=0.30, stretch=1.15)
    slovo_iz_pola(img, cam, "ENOUGH.", 1.35, 11.0, 1.0, (236, 190, 48), (166, 126, 22), seg(tt, 0.52, 0.61), depth=0.34, stretch=1.38)
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
