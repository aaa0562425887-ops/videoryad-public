# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть Q: G34, G35, G36 — белые макеты как мебель зала).
Запуск: shard_fable_q.py <код> <out.mp4>; один кадр: ZAL_FRAME=1.9 shard_fable_q.py G35 k.png

Числа сняты с плёнки покадрово (polosy/G34_*, G35_*, G36_* — обзоры 10 к/с, входы 30 к/с, сетки):
  G34  49.533-49.600 банк входит за 3 кадра, подпись BANKS через 3 кадра (49.700); больница
       50.000, «+» 50.300; ЛЭП 50.400-50.500 (тёмные, не белые); POWER 50.600, GRIDS с жёлтым
       маркером 50.900. Сетка 49.80: банк x 10-35 %, y 42-70 %; подпись y≈76 %, 11 % ширины;
       ряд на ~12-14 м. Камера за 2 с едет вперёд ~0.4 м и чуть вправо.
       На плёнке макеты ПАДАЮТ с потолка (это G12); здесь свой вход — макеты ВСТАЮТ из пола
       как створки, петля по нижней кромке, перелёт ~9°, камера едет вдоль ряда.
  G35  95.233→95.267 коридор входит СКЛЕЙКОЙ за один кадр; стойки чёрные с янтарными
       огоньками рядами, верх зала остаётся белым; точка схода x 0.50 / y 0.50; ближние
       стойки x 0-0.38 и 0.62-1.0, верх y≈0.18, низ y≈0.70-0.85. Угли (5-6 шт.) летят
       впереди камеры x 0.40-0.55, y 0.45-0.55. «THEY» 95.433, «GOT» 95.6, «ONTO» 95.9,
       «THE INTERNET.» 96.2 сразу с маркером; жёлтые замки на стойках с 96.5 (y≈0.5, 4 %
       высоты), с 97.5 ЗЕЛЁНЫЕ открытые замки летят в центре; «THEY STOLE PASSWORDS.» 97.1-97.4.
       Здесь свой вход: стойки выезжают из пола волной от дальнего конца к камере,
       зал темнеет, камера разгоняется в коридор, угли ведут к замку, который открывается.
  G36  85.000→85.033 куб входит СКЛЕЙКОЙ; стоит на полу, тросы к потолку от верхних углов,
       рёбра тёмно-серые ~6 px на 1920, грани с лёгкой молочной дымкой, внутри лист «THE TEST»
       лежит на полу куба, угли 5-7 шт. у верха, пол внутри светится тёплым; сетка 89.80: куб
       x 0.30-0.73, y 0.10-0.95 (куб ~2.8 м на ~6-7 м); белые ТРЕЩИНКИ на стекле в точках
       ударов углей (90.5-91.7); «AND FOUND A HOLE IN THE COMPUTER'S SECURITY» (HOLE маркером)
       89.3-89.9, «THAT NOBODY ON EARTH KNEW EXISTED.» 90.5-91.7. Камера медленно едет вперёд.
       Здесь свой вход: куб спускается с потолка на тросах и ЗАПИРАЕТ лист и угли, угли
       бьются о стенки (трещины), находят щель у ребра и выходят по одному.
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import *

FPS = 30
CAP = 0.715            # высота капители Arial Black в долях кегля
INK = (30, 27, 26, 255)
INK_SIDE = (18, 16, 15)
YEL = (255, 212, 0, 255)

# ----------------------------------------------------------------- общие вещи

def smooth(u):
    u = clamp01(u); return u * u * (3 - 2 * u)

def pop(t0, t, dur=0.10, k0=1.2):
    """вход как на плёнке: первый кадр крупнее и прозрачнее, за 3 кадра садится"""
    if t < t0 - 1e-6: return None
    u = seg(t, t0, t0 + dur)
    return k0 + (1.0 - k0) * out_cubic(u), 0.55 + 0.45 * clamp01(u * 2.2)

def visible(cam, corners, margin=0.35):
    return min(c[2] for c in corners) - cam.z > margin

_TILES = {}
def tiles(lines, fsize=200, hl=None, color=INK, cond=0.78, fname="ArialBlack.ttf"):
    """плитки слов по контуру: (ширина блока, высота, [(плитка, cx, cy)])"""
    key = (tuple(lines), fsize, tuple(sorted(hl)) if hl else None, color, cond, fname)
    if key in _TILES: return _TILES[key]
    tw, th, raw = word_tiles(lines, fsize=fsize, fname=fname, hl=hl, color=color)
    out = []
    for tile, cx, cy in raw:
        tile = tile.resize((max(4, int(tile.size[0] * cond)), tile.size[1]), Image.LANCZOS)
        bb = tile.getbbox()
        if bb is None: continue
        cr = tile.crop((bb[0], 0, bb[2], tile.size[1]))
        out.append((cr, cx * cond - tile.size[0] / 2 + (bb[0] + bb[2]) / 2, cy))
    _TILES[key] = (tw * cond, th, out)
    return _TILES[key]

def paste_q(canvas, tex, pts2d, opacity=1.0, rs=Image.BILINEAR):
    """как zal_core.paste_quad, но с выбором фильтра: BICUBIC стоит 70 мс на кадр 500x500,
    BILINEAR вдвое дешевле, NEAREST — вдесятеро (для одноцветных боковых копий)"""
    xs = [p[0] for p in pts2d]; ys = [p[1] for p in pts2d]
    x0, x1 = int(math.floor(min(xs))), int(math.ceil(max(xs)))
    y0, y1 = int(math.floor(min(ys))), int(math.ceil(max(ys)))
    x0, y0 = max(x0, -W), max(y0, -H)
    x1, y1 = min(x1, 2 * W), min(y1, 2 * H)
    bw, bh = x1 - x0, y1 - y0
    if bw < 2 or bh < 2 or x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H: return
    if bw * bh > 40_000_000: return
    dst = [(p[0] - x0, p[1] - y0) for p in pts2d]
    tw, th = tex.size
    try:
        c = Z._coeffs(dst, [(0, 0), (tw, 0), (tw, th), (0, th)])
    except Exception:
        return
    warped = tex.transform((bw, bh), Image.PERSPECTIVE, c, rs)
    if opacity < 1.0:
        warped.putalpha(warped.split()[3].point(lambda v: int(v * opacity)))
    canvas.alpha_composite(warped, (max(0, x0), max(0, y0)), (max(0, -x0), max(0, -y0), bw, bh))

_SOLID = {}
def _solid(tex, v):
    """одноцветная копия плитки для боковых граней: альфа ужата втрое — transform быстрее"""
    key = (id(tex), v)
    if key not in _SOLID:
        a = tex.split()[3]
        sw, sh = max(4, a.size[0] // 3), max(4, a.size[1] // 3)
        im = Image.new("RGBA", (sw, sh), (v[0], v[1], v[2], 255))
        im.putalpha(a.resize((sw, sh), Image.BILINEAR))
        if len(_SOLID) > 400: _SOLID.clear()
        _SOLID[key] = im
    return _SOLID[key]

def extrude_z(canvas, cam, corners, tex, depth, side=INK_SIDE, steps=6, opacity=1.0):
    """объём копиями в +z, от дальней к ближней (копий не больше 12, цвет ступенями по 4)"""
    p0 = cam.proj(corners[2]); p1 = cam.proj((corners[2][0], corners[2][1], corners[2][2] + depth))
    steps = int(max(steps, min(12, math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 3.0)))
    for i in range(steps, -1, -1):
        k = i / steps
        cs = [(c[0], c[1], c[2] + depth * k) for c in corners]
        if not visible(cam, cs): continue
        if i == 0:
            t = tex
        else:
            kk = round(k * 4) / 4
            t = _solid(tex, tuple(int(side[j] * (0.78 + 0.22 * (1 - kk))) for j in range(3)))
        paste_q(canvas, t, [cam.proj(p) for p in cs], opacity, Image.BILINEAR if i == 0 else Image.NEAREST)

_SHADOW = {}
def soft_shadow(canvas, cam, corners, tex, off=(0.5, 0.9), strength=0.26, blur=16):
    """тень на полу от нижней кромки назад-вправо (размытая копия кэшируется)"""
    bl, br = corners[3], corners[2]
    h = corners[0][1] - corners[3][1]
    sh = [(bl[0] + off[0] * h, 0.012, bl[2] + off[1] * h), (br[0] + off[0] * h, 0.012, br[2] + off[1] * h),
          (br[0], 0.012, br[2]), (bl[0], 0.012, bl[2])]
    if not visible(cam, sh): return
    key = (id(tex), blur)
    if key not in _SHADOW:
        a = tex.split()[3]
        sw, sh_ = max(4, a.size[0] // 2), max(4, a.size[1] // 2)
        dark = Image.new("RGBA", (sw, sh_), (38, 36, 34, 255)); dark.putalpha(a.resize((sw, sh_), Image.BILINEAR))
        if len(_SHADOW) > 200: _SHADOW.clear()
        _SHADOW[key] = dark.filter(ImageFilter.GaussianBlur(blur / 2))
    paste_q(canvas, _SHADOW[key], [cam.proj(p) for p in sh], strength)

def embers_fast(img, cam, pts, t, glow=0.95):
    """угли как в zal_core.embers, но ореол считается на четверти кадра — втрое быстрее"""
    rgb, al = Z._sprite()
    add = np.zeros((H, W, 3), np.float32)
    ca = np.zeros((H, W, 1), np.float32)
    any_ = False
    for i, (x, y, z, s) in enumerate(pts):
        pulse = 0.82 + 0.18 * math.sin(t * 3.4 + i * 1.7)
        px, py, dz = cam.proj((x, y, z))
        if dz < 0.3: continue
        size = min(700, max(10, int(s * F / dz * pulse)))
        if px < -size or px > W + size or py < -size or py > H + size: continue
        sp = np.array(Image.fromarray(rgb.astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32)
        sa = np.array(Image.fromarray((al * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32) / 255.0
        x0, y0 = int(px - size / 2), int(py - size / 2)
        X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(W, x0 + size), min(H, y0 + size)
        if X1 <= X0 or Y1 <= Y0: continue
        sub = sp[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        suba = sa[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][..., None]
        add[Y0:Y1, X0:X1] += sub * suba * pulse * 0.55
        ca[Y0:Y1, X0:X1] = np.maximum(ca[Y0:Y1, X0:X1], np.clip(suba * 2.6 - 0.45, 0, 1))
        any_ = True
    if not any_: return img
    small = Image.fromarray(np.clip(add, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    halo = np.asarray(small.filter(ImageFilter.GaussianBlur(11.5)).resize((W, H), Image.BILINEAR), np.float32)
    arr = np.asarray(img.convert("RGB"), np.float32)
    core = np.array([255.0, 182.0, 92.0], np.float32)
    arr = arr * (1 - ca) + core * ca + add * 0.5 + halo * glow
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

def put_words(img, cam, t, words, center, scale_m, starts, depth=0.14, side=INK_SIDE,
              hang=False, floor=False, shadow=False, opacity=1.0, wires_per=2):
    """плитки слов в пространстве; starts — t0 каждого слова; hang — тросы; floor — низ на полу"""
    tw, th, tl = words
    for i, (tile, cx, cy) in enumerate(tl):
        p = pop(starts[i], t)
        if p is None: continue
        s, op = p
        op *= opacity
        w = tile.size[0] * scale_m * s; h = tile.size[1] * scale_m * s
        u = (cx - tw / 2) * scale_m
        v = h / 2 if floor else (th / 2 - cy) * scale_m
        c = quad((center[0] + u, center[1] + v, center[2]), w, h)
        if not visible(cam, c): continue
        if shadow: soft_shadow(img, cam, c, tile)
        if hang:
            n = wires_per if w > 0.45 else 1
            for j in range(n):
                f = (j + 0.5) / n
                wire(img, cam, (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1], c[0][2]),
                     color=(96, 98, 102, 230), width=2)
        if s > 1.08:
            for sh in (-0.05, 0.05):
                cc = quad((center[0] + u + sh * w, center[1] + v, center[2]), w, h)
                paste_q(img, tile, [cam.proj(q) for q in cc], 0.22)
        extrude_z(img, cam, c, tile, depth, side=side, opacity=op)

def rush_blur(img, k):
    if k <= 0.01: return img
    base = img.convert("RGB")
    for z in (1.02,):
        sw, sh = int(W * z), int(H * z)
        big = base.resize((sw, sh), Image.BILINEAR).crop(((sw - W) // 2, (sh - H) // 2,
                                                            (sw - W) // 2 + W, (sh - H) // 2 + H))
        base = Image.blend(base, big, 0.45 * k)
    return base.convert("RGBA")

def darken(img, k):
    if k <= 0.005: return img
    img.alpha_composite(Image.new("RGBA", (W, H), (8, 7, 6, int(235 * clamp01(k)))))
    return img

# ----------------------------------------------------------------- G34: макеты встают в ряд

_MK = {}
def maket_image(kind):
    """белый макет с мягкой тёмной подложкой (читается на светлом); ЛЭП — тёмная"""
    if kind in _MK: return _MK[kind]
    tex = maket_tex(kind, 480)
    if kind == "power":
        r, g, b, a = tex.split()
        out = Image.merge("RGBA", (r.point(lambda v: v * 0.42), g.point(lambda v: v * 0.42),
                                   b.point(lambda v: v * 0.42), a))
    else:
        out = Image.new("RGBA", tex.size, (0, 0, 0, 0))
        a = tex.split()[3].filter(ImageFilter.GaussianBlur(3))
        sh = Image.new("RGBA", tex.size, (150, 154, 160, 255)); sh.putalpha(a)
        out.alpha_composite(sh, (4, 5)); out.alpha_composite(tex)
    _MK[kind] = out
    return out

def flap_angle(t0, t, dur=0.27):
    """створка встаёт из пола: 0 → 90° за dur с перелётом ~9° и возвратом (out_back)"""
    if t < t0 - 1e-6: return None
    u = seg(t, t0, t0 + dur)
    return math.radians(90.0) * out_back(u, 1.4), u

def maket_flap(img, cam, t, kind, x, z, size, t0):
    """макет — плита с петлёй по нижней кромке на полу; лежит вглубь зала, встаёт к камере"""
    r = flap_angle(t0, t)
    if r is None: return
    phi, u = r
    tex = maket_image(kind)
    w = size
    sn, cs = math.sin(phi), math.cos(phi)
    def corners(ph):
        s_, c_ = math.sin(ph), math.cos(ph)
        return [(x - w / 2, size * s_, z + size * c_), (x + w / 2, size * s_, z + size * c_),
                (x + w / 2, 0.0, z), (x - w / 2, 0.0, z)]
    c = corners(phi)
    if not visible(cam, c): return
    # тень растёт вместе с подъёмом
    if sn > 0.15:
        up = [(x - w / 2, size, z), (x + w / 2, size, z), (x + w / 2, 0, z), (x - w / 2, 0, z)]
        soft_shadow(img, cam, up, tex, off=(0.45, 0.85), strength=0.24 * sn)
    # смаз в середине хода: две призрачные копии по углу
    if 0.15 < u < 0.85:
        for dph in (-0.10, 0.10):
            paste_q(img, tex, [cam.proj(p) for p in corners(phi + dph)], 0.25)
    if u >= 1.0 and kind != "power":
        extrude_z(img, cam, c, tex, 0.30, side=(170, 174, 180), steps=5)
    else:
        paste_q(img, tex, [cam.proj(p) for p in c])

def plus_sign(img, cam, t, x, y, z, t0):
    p = pop(t0, t)
    if p is None: return
    s, op = p
    tex = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(tex)
    d.rectangle([46, 8, 74, 112], fill=(40, 37, 36, 255))
    d.rectangle([8, 46, 112, 74], fill=(40, 37, 36, 255))
    c = quad((x, y, z), 0.55 * s, 0.55 * s)
    extrude_z(img, cam, c, tex, 0.12, side=(22, 20, 19), steps=3, opacity=op)

def label(img, cam, t, text, x, z, starts, hl=None):
    words = tiles([text], 200, hl=hl, color=(34, 31, 30, 255), cond=0.7)
    put_words(img, cam, t, words, (x, 0.0, z), 0.32 / (CAP * 200), starts, depth=0.18,
              side=(20, 18, 17), floor=True, shadow=True)

def g34(t):
    """макеты встают в ряд створками из пола, «+» между ними, камера едет вдоль ряда"""
    cam = Cam(-1.1 + 1.7 * t / 4.5, 1.55, 0.26 * t, 0.0)
    img = room(cam)
    # заголовок на тросах: d≈11, центр 3.25 м, капитель 0.5 м; по словам, как на плёнке
    head = tiles(["THE SYSTEMS THEY", "ALREADY REACH"], 200, hl={4}, color=INK, cond=0.65)
    put_words(img, cam, t, head, (0.6, 3.25, 11.0), 0.50 / (CAP * 200),
              [0.00, 0.10, 0.20, 0.33, 0.47], depth=0.14, hang=True)
    Zm = 12.3
    # ряд: банк → «+» → больница → «+» → ЛЭП; каждый следующий встаёт через ~0.85 с
    maket_flap(img, cam, t, "bank", -3.4, Zm, 3.3, 0.55)
    label(img, cam, t, "BANKS", -3.4, Zm - 0.6, [0.85])
    plus_sign(img, cam, t, -1.7, 1.75, Zm, 1.15)
    maket_flap(img, cam, t, "hospital", 0.0, Zm, 3.1, 1.40)
    label(img, cam, t, "HOSPITALS", 0.0, Zm - 0.6, [1.70])
    plus_sign(img, cam, t, 1.75, 1.75, Zm, 2.00)
    maket_flap(img, cam, t, "power", 3.7, Zm, 3.8, 2.25)
    label(img, cam, t, "POWER GRIDS", 3.55, Zm - 0.6, [2.55, 2.95], hl={1})
    return img

# ----------------------------------------------------------------- G35: коридор стоек

_RACK = {}
def rack_tex():
    """передняя панель стойки 2.3 м: чёрный корпус, 13 юнитов с янтарными огоньками"""
    if "front" in _RACK: return _RACK["front"], _RACK["mirror"]
    w, h = 220, 520
    img = Image.new("RGBA", (w, h), (24, 24, 27, 255))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(3)
    d.rectangle([0, 0, 9, h], fill=(62, 62, 68, 255)); d.rectangle([w - 10, 0, w, h], fill=(62, 62, 68, 255))
    d.rectangle([0, 0, w, 10], fill=(118, 120, 126, 255))        # верхняя кромка — светлая
    y = 18
    while y < h - 30:
        uh = int(rng.integers(26, 44))
        d.rectangle([12, y, w - 13, y + uh - 4], fill=(42, 43, 48, 255))
        d.line([(12, y), (w - 13, y)], fill=(70, 71, 78, 255), width=2)
        kind = rng.integers(0, 3)
        if kind == 0:         # ряд янтарных огоньков
            for i in range(9):
                x = 22 + i * 21
                c = (255, 168, 44, 255) if rng.random() < 0.8 else (110, 230, 90, 255)
                d.ellipse([x, y + uh * 0.35, x + 5, y + uh * 0.35 + 5], fill=c)
        elif kind == 1:       # вентиляция + пара огоньков
            for i in range(6):
                d.line([(30 + i * 28, y + 6), (30 + i * 28, y + uh - 10)], fill=(28, 28, 32, 255), width=4)
            d.ellipse([w - 40, y + uh * 0.35, w - 35, y + uh * 0.35 + 5], fill=(255, 168, 44, 255))
            d.ellipse([w - 28, y + uh * 0.35, w - 23, y + uh * 0.35 + 5], fill=(255, 168, 44, 255))
        else:                 # две линии янтарных мелких
            for i in range(14):
                x = 20 + i * 13
                d.rectangle([x, y + uh * 0.3, x + 3, y + uh * 0.3 + 3], fill=(250, 150, 40, 255))
                if rng.random() < 0.5:
                    d.rectangle([x, y + uh * 0.6, x + 3, y + uh * 0.6 + 3], fill=(255, 190, 70, 255))
        y += uh
    mir = img.filter(ImageFilter.GaussianBlur(3))
    mir.putalpha(Image.new("L", (w, h), 70))
    _RACK["front"], _RACK["mirror"] = img, mir
    return img, mir

def rack(img, cam, t, side, z0, rise_t, locks):
    """стойка на внутренней стороне ряда x=±2.2, 1.0 м вдоль z, 2.3 м высотой;
    выезжает из пола за 0.15 с с перелётом; locks — список (t0, open_t) замков на ней"""
    u = seg(t, rise_t, rise_t + 0.15)
    if u <= 0: return
    hfull = 2.3
    h = hfull * out_back(u, 1.2)
    xx = side * 2.2
    dz = (z0 + 0.5) - cam.z
    if dz < 0.4: return
    tex, mir = rack_tex()
    # видна верхняя часть панели: стойка поднимается из пола лифтом
    frac = clamp01(h / hfull)
    tsub = tex.crop((0, 0, tex.size[0], max(2, int(tex.size[1] * frac))))
    h = hfull * frac
    if side < 0:
        c = [(xx, h, z0 + 1.0), (xx, h, z0), (xx, 0, z0), (xx, 0, z0 + 1.0)]
    else:
        c = [(xx, h, z0), (xx, h, z0 + 1.0), (xx, 0, z0 + 1.0), (xx, 0, z0)]
    fog = clamp01(1.0 - (dz - 16.0) / 36.0)
    if dz < 14 and u >= 1:
        m = mir.crop((0, 0, tex.size[0], tsub.size[1]))
        mc = [(p[0], -p[1] * 0.9, p[2]) for p in (c[3], c[2], c[1], c[0])]
        paste_q(img, m, [cam.proj(p) for p in mc], 0.9 * clamp01(1 - dz / 14))
    paste_q(img, tsub, [cam.proj(p) for p in c], fog)
    for (lt0, open_t) in locks:
        padlock(img, cam, t, side, z0 + 0.5, lt0, open_t)

_LOCK = {}
def lock_tex(state):
    """навесной замок: 'closed' жёлтый, 'open' зелёный с поднятой дужкой"""
    if state in _LOCK: return _LOCK[state]
    w, h = 160, 220
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body = (238, 196, 46, 255) if state == "closed" else (120, 214, 86, 255)
    dark = (120, 92, 20, 255) if state == "closed" else (54, 120, 40, 255)
    if state == "closed":
        d.arc([34, 18, 126, 130], 180, 360, fill=dark, width=16)
        d.line([(42, 74), (42, 112)], fill=dark, width=16); d.line([(118, 74), (118, 112)], fill=dark, width=16)
    else:
        d.arc([48, 4, 140, 116], 180, 360, fill=dark, width=16)
        d.line([(56, 60), (56, 86)], fill=dark, width=16); d.line([(132, 60), (132, 112)], fill=dark, width=16)
    d.rounded_rectangle([18, 104, 142, 212], radius=16, fill=body, outline=dark, width=5)
    d.ellipse([68, 140, 92, 164], fill=dark); d.rectangle([76, 156, 84, 186], fill=dark)
    _LOCK[state] = img
    return img

def padlock(img, cam, t, side, z, t0, open_t):
    p = pop(t0, t, dur=0.12, k0=1.25)
    if p is None: return
    s, op = p
    state = "closed" if (open_t is None or t < open_t) else "open"
    if state == "open":
        p2 = pop(open_t, t, dur=0.12, k0=1.3)
        s = p2[0]
    tex = lock_tex(state)
    hh = 0.50 * s; ww = hh * tex.size[0] / tex.size[1]
    xx = side * (2.2 - 0.05)
    if side < 0:
        c = [(xx, 1.35 + hh / 2, z + ww / 2), (xx, 1.35 + hh / 2, z - ww / 2),
             (xx, 1.35 - hh / 2, z - ww / 2), (xx, 1.35 - hh / 2, z + ww / 2)]
    else:
        c = [(xx, 1.35 + hh / 2, z - ww / 2), (xx, 1.35 + hh / 2, z + ww / 2),
             (xx, 1.35 - hh / 2, z + ww / 2), (xx, 1.35 - hh / 2, z - ww / 2)]
    if not visible(cam, c): return
    paste_q(img, tex, [cam.proj(q) for q in c], op)

def cam_z35(t):
    """разгон в коридор: 1.0 м/с → 3.6 м/с к 2.6 с (плавно), дальше ровно"""
    z, dt = 0.0, 0.01
    n = int(t / dt)
    for i in range(n):
        z += (1.0 + 2.6 * smooth(seg(i * dt, 0.5, 2.6))) * dt
    return z

def g35(t):
    """стойки выезжают из пола волной от дальнего конца, зал темнеет, камера разгоняется;
    текст на тросах в конце коридора, замки на стойках, один открывается — угли входят в него"""
    cz = cam_z35(t)
    cam = Cam(0.12 * math.sin(t * 1.1), 1.55, cz, 0.0)
    dark = 0.58 * smooth(seg(t, 0.15, 1.3))
    img = room(cam, dark=dark)
    # замок, который откроется: правая стойка на z=17
    LOCK_Z = 17.0
    locks = {(-1, 9.0): [(1.85, None)], (1, 11.0): [(1.95, None)], (-1, 13.0): [(2.05, None)],
             (1, LOCK_Z): [(2.15, 2.95)], (-1, 20.0): [(2.25, None)], (1, 24.0): [(2.35, None)],
             (-1, 27.0): [(2.45, None)]}
    # волна подъёма: дальний конец (z=34) в 0.10 с, ближний (z=3) в 1.25 с
    zs = [float(k) for k in range(int(math.floor(cz)) - 1, int(cz) + 46)]
    for z0 in sorted(zs, reverse=True):
        rise_t = 0.10 + 1.15 * clamp01((34.0 - z0) / 31.0)
        for side in (-1, 1):
            rack(img, cam, t, side, z0, rise_t, locks.get((side, z0), []))
    # текст на тросах в конце коридора: z=24, капитель 0.70 м (на плёнке строка ~6 % высоты кадра)
    words1 = tiles(["THEY GOT ONTO"], 200, color=INK, cond=0.62)
    words2 = tiles(["THE INTERNET."], 200, color=INK, cond=0.62)
    words2m = tiles(["THE INTERNET."], 200, hl={1}, color=INK, cond=0.62)
    sc = 0.70 / (CAP * 200)
    put_words(img, cam, t, words1, (0.0, 3.55, 24.0), sc, [0.95, 1.10, 1.25], depth=0.14, hang=True)
    put_words(img, cam, t, words2m if t >= 1.85 else words2, (0.0, 2.70, 24.0), sc, [1.50, 1.62],
              depth=0.14, hang=True)
    # угли ведут камеру: летят впереди, с 2.9 с сворачивают к открытому замку и входят в стойку
    pts = []
    k = smooth(seg(t, 2.9, 3.5))
    lead = (0.15 * math.sin(t * 1.7), 1.45 + 0.12 * math.sin(t * 2.3), cz + 5.5 + 0.4 * math.sin(t * 0.9))
    target = (2.05, 1.35, LOCK_Z)
    cx = lead[0] * (1 - k) + target[0] * k
    cy = lead[1] * (1 - k) + target[1] * k
    czz = lead[2] * (1 - k) + target[2] * k
    inside = seg(t, 3.5, 4.1)                       # ушли в стойку: сжимаются и гаснут
    for i in range(6):
        ph = i * 1.9
        sp = 0.35 * (1 - k) + 0.12 * k
        px = cx + sp * math.sin(t * 2.1 + ph); py = cy + sp * 0.5 * math.cos(t * 1.7 + ph)
        pz = czz + sp * 1.3 * math.sin(t * 1.3 + ph * 0.7)
        px += 0.3 * inside
        s = (0.42 + 0.18 * (i % 3)) * (1 - 0.95 * inside)
        if s < 0.03: continue
        pts.append((px, py, pz, s))
        if k < 0.5: pts.append((px, -py * 0.9, pz, s * 0.7))
    if pts:
        img = embers_fast(img, cam, pts, t, glow=0.9 * (1 - 0.8 * inside))
    v = 1.0 + 2.6 * smooth(seg(t, 0.5, 2.6))
    if v > 2.4:
        img = rush_blur(img, clamp01((v - 2.4) / 6.0))
    return img

# ----------------------------------------------------------------- камера с наклоном (для G36)

class PCam(Cam):
    """Cam с наклоном вниз: на плёнке куб снят сверху, видна верхняя грань.
    pitch > 0 — камера смотрит вниз; чистый поворот, горизонт уходит вверх на F·tg(pitch)"""
    def __init__(s, x=0.0, y=1.55, z=0.0, yaw=0.0, pitch=0.0):
        super().__init__(x, y, z, yaw); s.pitch = pitch
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

def room_pitch(cam, windows=True, dark=0.0, shafts=True, ropes=True):
    """тот же зал, что zal_core.room, но горизонт считается по наклону камеры"""
    g = Image.new("L", (1, H))
    for y in range(H):
        t = y / H
        g.putpixel((0, y), int(234 - 24 * abs(t - 0.5) * 2))
    base = g.resize((W, H))
    img = Image.merge("RGBA", (base, base, base.point(lambda v: min(255, v + 3)),
                               Image.new("L", (W, H), 255)))
    d = ImageDraw.Draw(img, "RGBA")
    hor = max(1.0, H / 2 - F * math.tan(cam.pitch))
    d.rectangle([0, hor, W, H], fill=(197, 200, 204, 255))
    d.rectangle([0, 0, W, hor], fill=(230, 232, 235, 255))
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
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(9)))
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

# ----------------------------------------------------------------- G36: стеклянный куб-клетка

_SHEET = {}
def test_sheet_tex():
    if "s" in _SHEET: return _SHEET["s"]
    w, h = 380, 500
    img = Image.new("RGBA", (w, h), (250, 250, 248, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(205, 205, 202, 255), width=2)
    d.rectangle([22, 22, w - 22, 76], fill=(28, 26, 24, 255))
    d.text((38, 30), "THE TEST", font=font("ArialBlack.ttf", 34), fill=(245, 245, 240, 255))
    f = font("Arimo-Bold.ttf", 17)
    for i in range(10):
        y = 100 + i * 38
        d.text((34, y), f"{i + 1:03d}", font=f, fill=(90, 90, 92, 255))
        d.line([(84, y + 10), (w - 40 - (i % 3) * 50, y + 10)], fill=(200, 200, 198, 255), width=6)
    _SHEET["s"] = img
    return img

def floor_sheet(img, cam, x, z, w, h):
    tex = test_sheet_tex()
    c = [(x - w / 2, 0.012, z + h / 2), (x + w / 2, 0.012, z + h / 2),
         (x + w / 2, 0.012, z - h / 2), (x - w / 2, 0.012, z - h / 2)]
    if visible(cam, c): paste_q(img, tex, [cam.proj(p) for p in c])

def tri(u):
    """треугольная волна -1..1 с резким разворотом (удар о стенку)"""
    return 4 * abs(u - math.floor(u + 0.5)) - 1

EMB = [(1.9, 0.00, 2.7, 0.31, 0.55), (2.6, 0.37, 2.1, 0.62, 0.42), (2.2, 0.71, 3.1, 0.15, 0.60),
       (3.0, 0.22, 2.4, 0.83, 0.48), (2.4, 0.58, 2.9, 0.44, 0.38), (1.7, 0.90, 2.2, 0.08, 0.52)]
CUBE, CUBE_S, CZ0 = (0.45, 0.0, 9.0), 2.9, 9.0
LIM = CUBE_S / 2 - 0.25
HOLE = (0.45 + CUBE_S / 2, 2.2, 9.0 - 0.8)      # щель на правой грани, у переднего верхнего угла

def ember_free(i, t, lim=LIM):
    px_, phx, pz_, phz, s = EMB[i]
    cx, _, cz = CUBE
    x = cx + lim * tri(t / px_ + phx)
    z = cz + lim * tri(t / pz_ + phz)
    y = 1.65 + 0.45 * math.sin(t * 1.9 + i * 1.3)
    return x, y, z, s

def hits_before(t, t_from, lim=LIM):
    """удары о стенки x=± и z=± до момента t: (точка, время)"""
    out = []
    cx, _, cz = CUBE
    for i in range(len(EMB)):
        px_, phx, pz_, phz, s = EMB[i]
        for per, ph, axis in ((px_, phx, 0), (pz_, phz, 2)):
            k = 0
            while True:
                th = (k * 0.5 + 0.5 - ph) * per          # вершины треугольной волны
                k += 1
                if th > t: break
                if th < t_from: continue
                x, y, z, _ = ember_free(i, th, lim)
                if axis == 0: x = cx + (lim if tri(th / per + ph) > 0 else -lim)
                else:         z = cz + (lim if tri(th / per + ph) > 0 else -lim)
                out.append(((x, y, z), th, axis))
                if len(out) > 40: return out
    return out

def crack(lay, cam, p, age, axis, seed, strength=1.0, fade=True):
    """трещинка на грани: лучи в плоскости грани, растёт 0.25 с, за 1.3 с бледнеет"""
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(lay)
    g = smooth(seg(age, 0.0, 0.25)) * strength
    if fade: g *= 1.0 - 0.75 * smooth(seg(age, 0.4, 1.3))
    if g <= 0.02: return
    r = 0.05 + 0.10 * min(1.0, g)
    for i in range(int(rng.integers(4, 7))):
        a = rng.uniform(0, 2 * math.pi); L = r * rng.uniform(0.5, 1.0)
        pts = [p]
        q = p
        for s_ in range(3):
            L2 = L / 3
            a += rng.uniform(-0.6, 0.6)
            if axis == 0: q = (q[0], q[1] + L2 * math.sin(a), q[2] + L2 * math.cos(a))
            else:         q = (q[0] + L2 * math.cos(a), q[1] + L2 * math.sin(a), q[2])
            pts.append(q)
        sp = [cam.proj(x) for x in pts]
        d.line([(x[0], x[1]) for x in sp], fill=(90, 92, 98, int(110 * min(1, g))), width=3)
        d.line([(x[0], x[1]) for x in sp], fill=(255, 255, 255, int(235 * min(1, g))), width=1)

def cube_reflection(lay, cam, center, size, alpha=70):
    cx, cy, cz = center; s = size / 2
    d = ImageDraw.Draw(lay)
    v = [(cx - s, cy - s, cz - s), (cx + s, cy - s, cz - s), (cx + s, cy - s, cz + s), (cx - s, cy - s, cz + s)]
    for q in v:
        a = cam.proj((q[0], -q[1] * 0.9 if q[1] > 0 else q[1], q[2]))
        b = cam.proj((q[0], -(q[1] + size) * 0.9, q[2]))
        d.line([(a[0], a[1]), (b[0], b[1])], fill=(52, 54, 58, alpha), width=5)
    top = [cam.proj((q[0], -(q[1] + size) * 0.9, q[2])) for q in v]
    for i in range(4):
        a, b = top[i], top[(i + 1) % 4]
        d.line([(a[0], a[1]), (b[0], b[1])], fill=(52, 54, 58, alpha // 2), width=4)

def g36(t):
    """куб спускается с потолка на тросах и запирает лист с углями; угли бьются о стекло
    (трещины), находят щель у ребра и выходят по одному; камера медленно едет вперёд-вправо"""
    # камера выше куба и смотрит вниз (на плёнке видна верхняя грань), едет вперёд и влево
    cam = PCam(0.6 - 1.5 * smooth(t / 4.5), 3.3, 0.12 * t, 0.0, pitch=math.radians(8.0))
    img = room_pitch(cam)
    cx, _, cz = CUBE
    # спуск: 0.30 → 0.95 с, out_expo, посадка с лёгким отскоком 4 см
    T0, T1 = 0.30, 0.95
    u = seg(t, T0, T1)
    y_off = (CEIL - CUBE_S) * (1 - out_expo(u))
    if t > T1:
        y_off += 0.04 * math.sin(math.pi * seg(t, T1, T1 + 0.12))
    landed = t >= T1
    floor_sheet(img, cam, cx + 0.15, cz + 0.25, 1.25, 1.55)
    # угли внутри: свободный бег с ударами; с 3.1 с стягиваются к щели, с 3.5 выходят по одному
    inside, outside = [], []
    gather = smooth(seg(t, 3.1, 3.5))
    for i in range(len(EMB)):
        x, y, z, s = ember_free(i, t)
        te = 3.5 + 0.17 * i
        if t >= te:
            dt = t - te
            v = 1.0 + 0.6 * dt
            outside.append((HOLE[0] + v * dt * 1.0 + 0.25 * math.sin(dt * 6 + i),
                            HOLE[1] + v * dt * 0.28 + 0.18 * math.sin(dt * 5 + i * 2),
                            HOLE[2] - v * dt * 0.9, s))
            continue
        hx = HOLE[0] - 0.12; hy = HOLE[1] - 0.05 * i; hz = HOLE[2] + 0.1 * (i % 3)
        x = x * (1 - gather) + hx * gather; y = y * (1 - gather) + hy * gather; z = z * (1 - gather) + hz * gather
        inside.append((x, y, z, s)); inside.append((x, -y * 0.9, z, s * 0.7))
    # текст на тросах ЗА кубом (рисуется до стекла — читается сквозь грани): капитель 0.5 м
    sc = 0.50 / (CAP * 200)
    w1 = tiles(["LOCKED IN"], 200, color=INK, cond=0.66)
    w2 = tiles(["UNTIL THEY FOUND"], 200, color=INK, cond=0.66)
    w3 = tiles(["A HOLE."], 200, hl={1}, color=INK, cond=0.66)
    w3n = tiles(["A HOLE."], 200, color=INK, cond=0.66)
    X = cx - 3.2; ZT = cz + 2.6
    put_words(img, cam, t, w1, (X, 2.55, ZT), sc, [1.25, 1.38], depth=0.12, hang=True)
    put_words(img, cam, t, w2, (X, 1.95, ZT), sc, [2.45, 2.58, 2.72], depth=0.12, hang=True)
    put_words(img, cam, t, w3 if t >= 3.45 else w3n, (X, 1.35, ZT), sc, [3.20, 3.30], depth=0.12, hang=True)
    # сам куб (грани, рёбра, тросы) и его отражение в полу
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if landed:
        cube_reflection(lay, cam, (cx, 0.0, cz), CUBE_S)
    img.alpha_composite(lay)
    glass_cube(img, cam, (cx, CUBE_S / 2 + y_off, cz), CUBE_S, t=t, wires=True)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if landed:
        # посадка: вспышка по нижним рёбрам 4 кадра
        fl = 1 - seg(t, T1, T1 + 0.13)
        if fl > 0:
            s = CUBE_S / 2
            base = [cam.proj(p) for p in ((cx - s, 0.01, cz - s), (cx + s, 0.01, cz - s),
                                          (cx + s, 0.01, cz + s), (cx - s, 0.01, cz + s))]
            d.polygon([(p[0], p[1]) for p in base], outline=(255, 255, 255, int(230 * fl)), width=9)
        # трещины от ударов (только после посадки, пока щель не нашли — дальше старые остаются)
        for (p, th, axis) in hits_before(min(t, 3.3), max(T1 + 0.05, t - 1.4)):
            if abs(p[1] - 1.65) > 0.9: continue
            crack(lay, cam, p, t - th, axis, seed=int(th * 1000) % 9973)
        # щель: с 3.25 с у переднего верхнего угла правой грани
        if t >= 3.25:
            g = smooth(seg(t, 3.25, 3.55))
            crack(lay, cam, HOLE, 0.3, 0, seed=77, strength=1.6 * g, fade=False)
            crack(lay, cam, (HOLE[0], HOLE[1] - 0.08, HOLE[2] + 0.1), 0.3, 0, seed=78, strength=1.3 * g, fade=False)
            # сама щель — тёмный зазор в стекле
            hp = cam.proj(HOLE); r = 0.03 + 0.05 * g
            a = cam.proj((HOLE[0], HOLE[1] + r, HOLE[2] + r * 0.6)); b = cam.proj((HOLE[0], HOLE[1] - r, HOLE[2] - r * 0.6))
            d.line([(a[0], a[1]), (b[0], b[1])], fill=(30, 30, 34, int(200 * g)), width=4)
    img.alpha_composite(lay)
    # угли одним проходом (два прохода — это два полных кадра float): вышедшие рисуются поверх стекла
    if inside or outside:
        img = embers_fast(img, cam, inside + outside, t, glow=0.95)
    return img

SCENES = {"G34": (g34, 4.5), "G35": (g35, 4.5), "G36": (g36, 4.5)}

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
