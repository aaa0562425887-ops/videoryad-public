# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть P: G31 амфитеатр кресел, G32 шар из точек,
G33 галерея рам). Запуск через общий shard_fable.py; один кадр:
ZAL_FRAME=1.9 python3 shard_fable.py G31 /tmp/k.png

Числа сняты с плёнки покадрово (polosy/G31_*, G32_*, G33_*):
  G31  база 229.55. Камера смотрит круто вниз, пол на весь кадр, два серых клина
       кресел уже стоят (229.6); REPUBLICANS ложится на пол 229.767 (2 кадра
       прозрачности); красный идёт по клину РАДИАЛЬНЫМИ линиями от прохода наружу
       229.9→230.4 (15 кадров); DEMOCRATS 230.4; синий 230.567→231.0;
       AGREE 231.133 · ON 231.367 · ALMOST 231.467 · NOTHING. 231.9 — лежат на полу
       в проходе; 232.4-232.47 текст улетает смазом, 232.5→232.75 камера за 8 кадров
       отъезжает назад и выравнивается, клинья видны сзади снизу; DATA CENTER 232.6;
       THEY 232.733 · AGREE 232.933 · ON 233.067 · THIS. 233.2 на тросах;
       лист 60% встаёт слева 233.3-233.4, 76% справа 233.4-233.5.
  G32  база 59.0. Шар R≈1.15 м, центр x≈-1.0, y≈1.2 (сетка 59.30: x 8-55 %,
       y 27-100 %), над ним оранжевый «солнце»-уголёк; точки жёлтые ~20 px при
       d≈5.3, шаг ~22 px, континенты, медленное вращение. FOR 59.267 · EVERY 59.4 ·
       SINGLE(жёлтый) 59.667 · USER 60.4 · ON 60.467 · EARTH 60.667.
       Осыпание 60.4→61.1: верх теряет точки первым, они сползают по шару, падают с
       низа и ложатся кучей на пол; уголёк гаснет 60.4-60.5; камера подъезжает,
       шар уходит влево (61.4: x 0-50 %), с 61.5 камера отъезжает.
       Вход на плёнке — склейка из-под панели эфира; здесь по заданию точки
       СТЯГИВАЮТСЯ в шар (0-0.8 с), шар вырастает за 0.3 с.
  G33  база 137.2. Камера летит над «TEN THOUSAND», в верхней половине облако
       углей; ряд из семи рам виден точкой 137.233 (d≈45), 137.4 d≈20, 137.6 d≈11,
       137.9 d≈9.5 — торможение out_expo; рамы 1.0×1.6 м, шаг 1.62, высота
       центра 1.75; A MILLION-DOLLAR уже под рамами; $1,000,000 137.5 ·
       NAVIER-STOKES 137.567 · PRIZE 137.967 · PROBLEM 138.3; угли стекаются
       к средней раме и обводят её оранжевой рамкой 138.1→138.5, облако оседает
       в «море» у пола к 140.5; ABOUT 138.567 · HOW 138.867 · WATER 139.25 ·
       FLOWS, 139.5; THAT HAD STUMPED 140.3 · MATHEMATICIANS 140.8 · FOR 141.2 ·
       GENERATIONS. 141.5; 140.5→141.5 камера идёт вперёд-вправо, рамы проезжают
       мимо (141.5: средняя рама x 30-48 %, d≈5.4, камера смещена на +0.6).
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import (W, H, F, CEIL, WALL, FAR, Cam, quad, paste_quad, room, text_tex,
                      sticker_tex, extrude, wire, out_expo, out_back, out_cubic, seg,
                      clamp01, font, embers, put_above_floor, floor_shadow)

FPS = 30

# ============================================================== общие вещи

def smooth(u):
    u = clamp01(u); return u * u * (3 - 2 * u)

class PCam(Cam):
    """камера с наклоном: pitch > 0 — смотрит вниз"""
    def __init__(s, x=0.0, y=1.55, z=0.0, yaw=0.0, pitch=0.0):
        Cam.__init__(s, x, y, z, yaw); s.pitch = pitch
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
    def proj_np(s, P):
        dx, dy, dz = P[:, 0] - s.x, P[:, 1] - s.y, P[:, 2] - s.z
        if s.yaw:
            c, si = math.cos(-s.yaw), math.sin(-s.yaw)
            dx, dz = dx * c - dz * si, dx * si + dz * c
        if getattr(s, "pitch", 0.0):
            c, si = math.cos(s.pitch), math.sin(s.pitch)
            dy, dz = dy * c + dz * si, dz * c - dy * si
        dz = np.maximum(dz, 0.08)
        k = F / dz
        return W / 2 + dx * k, H / 2 - dy * k, dz

def proj_np(cam, P):
    if isinstance(cam, PCam): return cam.proj_np(P)
    return PCam(cam.x, cam.y, cam.z, cam.yaw).proj_np(P)

def room_p(cam, windows=True, shafts=True, ropes=True):
    """тот же зал, что Z.room, но пол считается от настоящего горизонта —
    нужен для наклонённой камеры; полосы света размываются в половинном размере"""
    img = Image.new("RGBA", (W, H), (230, 232, 235, 255))
    d = ImageDraw.Draw(img)
    y_h = H / 2 - F * math.tan(getattr(cam, "pitch", 0.0))
    d.rectangle([0, max(-1, y_h), W, H], fill=(197, 200, 204, 255))
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
        lay = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        z0 = math.floor((cam.z + 3) / 7.0) * 7.0
        for i in range(9):
            zz = z0 + i * 7.0
            for sx in (-1, 1):
                p = [cam.proj((sx * (WALL - 0.2), 0.0, zz + 0.6)),
                     cam.proj((sx * (WALL - 0.2), 0.0, zz + 3.5)),
                     cam.proj((sx * (WALL - 3.4), 0.0, zz + 5.2)),
                     cam.proj((sx * (WALL - 3.4), 0.0, zz + 2.3))]
                dl.polygon([(q[0] / 2, q[1] / 2) for q in p], fill=(255, 255, 255, 70))
        lay = lay.filter(ImageFilter.GaussianBlur(12)).resize((W, H), Image.BILINEAR)
        img.alpha_composite(lay)
    if ropes:
        rng = np.random.default_rng(5)
        dr = ImageDraw.Draw(img)
        z0 = math.floor((cam.z + 4) / 3.0) * 3.0
        for i in range(26):
            zz = z0 + (i % 13) * 3.0 + float(rng.uniform(-1.0, 1.0))
            xx = float(rng.uniform(-4.6, 4.6))
            yy = float(rng.uniform(0.9, 2.4))
            if zz - cam.z < 1.5: continue
            a = cam.proj((xx, CEIL, zz)); b = cam.proj((xx, yy, zz))
            dr.line([(a[0], a[1]), (b[0], b[1])], fill=(150, 152, 156, 255), width=1)
    return img

def rush_blur(img, k):
    if k <= 0.01: return img
    base = img.convert("RGB")
    for z in (1.012, 1.03):
        sw, sh = int(W * z), int(H * z)
        big = base.resize((sw, sh), Image.BILINEAR).crop(((sw - W) // 2, (sh - H) // 2,
                                                            (sw - W) // 2 + W, (sh - H) // 2 + H))
        base = Image.blend(base, big, 0.32 * k)
    return base.convert("RGBA")

def shear(tex, k=0.18):
    w, h = tex.size
    return tex.transform((int(w + k * h), h), Image.AFFINE, (1, k, -k * h, 0, 1, 0), Image.BICUBIC)

_CAP = {}
def cap_px(fname, fsize=200):
    key = (fname, fsize)
    if key not in _CAP:
        d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
        b = d.textbbox((0, 0), "H", font=font(fname, fsize))
        _CAP[key] = b[3] - b[1]
    return _CAP[key]

def lines_at(t, spec):
    """spec — строки из слов (слово, t0, жёлтый?). Возвращает (строки, индексы жёлтых)"""
    lines, hl, idx = [], set(), 0
    for ln in spec:
        ws = []
        for w, t0, y in ln:
            if t >= t0 - 1e-6:
                ws.append(w)
                if y: hl.add(idx)
                idx += 1
        if ws: lines.append(" ".join(ws))
    return lines, hl

_TEX = {}
def block_tex(lines, hl, fname, color, cond):
    key = (tuple(lines), tuple(sorted(hl)), fname, color, cond)
    if key not in _TEX:
        _TEX[key] = text_tex(list(lines), fsize=200, fname=fname, hl=hl, color=color, cond=cond)
    return _TEX[key]

def hang_words(img, cam, lines, hl, left, top, z, cap_m, fname="Oswald-Bold.ttf",
               color=(28, 26, 26, 255), wires=True, depth=0.08, side=(16, 15, 15),
               cond=1.0, opacity=1.0, lift=0.0, exit_u=0.0):
    """блок слов в воздухе: левый верхний угол в (left, top, z); exit_u — улёт вверх со смазом"""
    if not lines: return
    tex = block_tex(lines, hl, fname, color, cond)
    sc = cap_m / (cap_px(fname) * cond if False else cap_px(fname))
    w = tex.size[0] * sc; h = tex.size[1] * sc
    top = top + lift
    c = quad((left + w / 2, top - h / 2, z), w, h)
    if exit_u > 0:
        for k in (0.5, 1.0):
            cc = quad((left + w / 2, top - h / 2 + 1.4 * exit_u * k, z), w, h)
            paste_quad(img, tex, [cam.proj(p) for p in cc], (1 - exit_u) * 0.35)
        return
    if wires:
        for f in (0.12, 0.88):
            wire(img, cam, (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1], z), color=(96, 98, 102, 230))
    if opacity < 1.0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        extrude(lay, cam, c, tex, depth=depth, steps=4, shade=side)
        a = lay.split()[3].point(lambda v: int(v * opacity)); lay.putalpha(a)
        img.alpha_composite(lay)
    else:
        extrude(img, cam, c, tex, depth=depth, steps=4, shade=side)

def floor_text(img, cam, tex, cx, cz, width_m, lift=0.12, side=(60, 20, 18), opacity=1.0, steps=4):
    """надпись лежит на полу плашмя, выдавлена вверх на lift"""
    hm = width_m * tex.size[1] / tex.size[0]
    alpha = tex.split()[3]
    for i in range(0, steps + 1):
        y = 0.012 + lift * i / steps
        c = [(cx - width_m / 2, y, cz + hm / 2), (cx + width_m / 2, y, cz + hm / 2),
             (cx + width_m / 2, y, cz - hm / 2), (cx - width_m / 2, y, cz - hm / 2)]
        if i < steps:
            v = [int(side[j] * (0.75 + 0.25 * i / steps)) for j in range(3)]
            tt = Image.new("RGBA", tex.size, (v[0], v[1], v[2], 255)); tt.putalpha(alpha)
        else:
            tt = tex
        paste_quad(img, tt, [cam.proj(p) for p in c], opacity)

# ---------------------------------------------------------- угли полем (numpy)
_SPRS = {}
def _spr(size):
    if size not in _SPRS:
        rgb, al = Z._sprite()
        sp = np.asarray(Image.fromarray(rgb.astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32)
        sa = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32) / 255.0
        _SPRS[size] = (sp, sa)
    return _SPRS[size]

def ember_field(arr, cam, P, S, t, phase, glow=0.9, maxsize=240):
    """arr — float32 (H,W,3), меняется на месте и возвращается. P (N,3) м, S (N) м"""
    n = len(P)
    if n == 0: return arr
    sx, sy, dz = proj_np(cam, P)
    pulse = 0.82 + 0.18 * np.sin(t * 3.4 + phase)
    size = S * F / dz * pulse
    keep = (dz > 0.3) & (size >= 3) & (sx > -size) & (sx < W + size) & (sy > -size) & (sy < H + size)
    if not keep.any(): return arr
    sx, sy, dz, size, pulse = sx[keep], sy[keep], dz[keep], size[keep], pulse[keep]
    size = np.clip(size, 3, maxsize)
    q = np.where(size < 40, np.round(size / 2) * 2, np.round(size / 8) * 8).astype(int)
    order = np.argsort(-dz)
    add = np.zeros((H, W, 3), np.float32)
    ca = np.zeros((H, W), np.float32)
    for i in order:
        s = int(q[i]); sp, sa = _spr(s)
        x0, y0 = int(sx[i] - s / 2), int(sy[i] - s / 2)
        X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(W, x0 + s), min(H, y0 + s)
        if X1 <= X0 or Y1 <= Y0: continue
        sub = sp[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        suba = sa[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        pu = float(pulse[i])
        add[Y0:Y1, X0:X1] += sub * suba[..., None] * (pu * 0.55)
        np.maximum(ca[Y0:Y1, X0:X1], np.clip(suba * 2.6 - 0.45, 0, 1), out=ca[Y0:Y1, X0:X1])
    small = Image.fromarray(np.clip(add, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    halo = np.asarray(small.filter(ImageFilter.GaussianBlur(11)).resize((W, H), Image.BILINEAR), np.float32)
    core = np.array([255.0, 182.0, 92.0], np.float32)
    ca3 = ca[..., None]
    arr *= (1 - ca3); arr += core * ca3
    arr += add * 0.5 + halo * glow
    return arr

def to_arr(img): return np.asarray(img.convert("RGB"), np.float32).copy()
def to_img(arr): return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

# ============================================================== G31 · амфитеатр

ZA = 40.0                       # точка схода рядов (сцена)
G31_GRAY = (168, 168, 172); G31_RED = (226, 62, 56); G31_BLUE = (58, 98, 224)
TH0, TH1 = math.radians(13.0), math.radians(56.0)

_CH = []
def _g31_chairs():
    if not _CH:
        for k in range(6):
            r = 1.6 + 0.5 * k
            n = max(2, int(round(r * (TH1 - TH0) / 0.38)))
            for side in (-1, 1):
                for i in range(n):
                    th = TH0 + (TH1 - TH0) * (i + 0.5) / n
                    x = side * r * math.sin(th); z = ZA - r * math.cos(th)
                    yaw = math.atan2(0.0 - x, ZA - z)          # лицом к точке схода
                    _CH.append((x, z, yaw, side, th, k))
    return _CH

_LIGHT = np.array([-0.35, 0.90, -0.30]); _LIGHT /= np.linalg.norm(_LIGHT)
def box_faces(cam, cx, cz, yaw, w, d, h, y0=0.0):
    """грани коробки, видимые камере: [(полигон, затенение)]"""
    fx, fz = math.sin(yaw), math.cos(yaw)
    rx, rz = math.cos(yaw), -math.sin(yaw)
    def P(sx, sz, y): return (cx + rx * sx + fx * sz, y, cz + rz * sx + fz * sz)
    hw, hd = w / 2, d / 2
    faces = [((0, 1, 0), [P(-hw, -hd, y0 + h), P(hw, -hd, y0 + h), P(hw, hd, y0 + h), P(-hw, hd, y0 + h)]),
             ((fx, 0, fz), [P(-hw, hd, y0 + h), P(hw, hd, y0 + h), P(hw, hd, y0), P(-hw, hd, y0)]),
             ((-fx, 0, -fz), [P(hw, -hd, y0 + h), P(-hw, -hd, y0 + h), P(-hw, -hd, y0), P(hw, -hd, y0)]),
             ((rx, 0, rz), [P(hw, hd, y0 + h), P(hw, -hd, y0 + h), P(hw, -hd, y0), P(hw, hd, y0)]),
             ((-rx, 0, -rz), [P(-hw, -hd, y0 + h), P(-hw, hd, y0 + h), P(-hw, hd, y0), P(-hw, -hd, y0)])]
    out = []
    for n, pts in faces:
        c = [sum(p[i] for p in pts) / 4 for i in range(3)]
        v = (cam.x - c[0], cam.y - c[1], cam.z - c[2])
        if n[0] * v[0] + n[1] * v[1] + n[2] * v[2] <= 0: continue
        sh = 0.60 + 0.40 * max(0.0, n[0] * _LIGHT[0] + n[1] * _LIGHT[1] + n[2] * _LIGHT[2])
        out.append(([cam.proj(p)[:2] for p in pts], sh))
    return out

def chair(d, cam, x, z, yaw, col, s=1.0):
    fx, fz = math.sin(yaw), math.cos(yaw)
    for (ox, oz, w, dd, h) in ((0.0, 0.0, 0.32, 0.30, 0.22), (-fx * 0.12, -fz * 0.12, 0.32, 0.07, 0.50)):
        for poly, sh in box_faces(cam, x + ox, z + oz, yaw, w * s, dd * s, h * s):
            c = tuple(int(col[i] * sh) for i in range(3)) + (255,)
            d.polygon(poly, fill=c)

def g31_cam(t):
    # сверху: камера под самым потолком (выше нельзя — зал без крыши), наклон 45°,
    # в кадре пол от 2.85 до 8.65 м вперёд; медленно ползёт вперёд и к проходу
    a = (-0.55 + 0.3 * t / 2.85, CEIL, ZA - 7.3 + 0.35 * t / 2.85, math.radians(45.0))
    if t <= 2.85: return PCam(a[0], a[1], a[2], 0.0, a[3])
    u = out_cubic(seg(t, 2.85, 3.2))
    b = (0.25, 1.3, ZA - 8.5 + 0.25 * seg(t, 3.2, 4.5), 0.0)
    return PCam(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u,
                0.0, a[3] * (1 - u))

_G31T = {}
def _g31_tex():
    if not _G31T:
        _G31T["rep"] = shear(text_tex(["REPUBLICANS"], 200, "Oswald-Bold.ttf", color=(226, 58, 52, 255)), 0.2)
        _G31T["dem"] = shear(text_tex(["DEMOCRATS"], 200, "Oswald-Bold.ttf", color=(64, 110, 230, 255)), 0.2)
        for k, s in (("agree", "AGREE ON"), ("almost", "ALMOST"), ("nothing", "NOTHING.")):
            _G31T[k] = text_tex([s], 200, "ArialBlack.ttf", color=(30, 28, 28, 255), cond=0.8)
        pl = Image.new("RGBA", (640, 170), (42, 42, 46, 255))
        dd = ImageDraw.Draw(pl); dd.rectangle([0, 0, 639, 169], outline=(90, 90, 96, 255), width=6)
        f = font("Oswald-Bold.ttf", 100); b = dd.textbbox((0, 0), "DATA CENTER", font=f)
        dd.text(((640 - (b[2] - b[0])) / 2 - b[0], (170 - (b[3] - b[1])) / 2 - b[1]), "DATA CENTER",
                font=f, fill=(240, 240, 242, 255))
        _G31T["plate"] = pl
        for k, val, col, who in (("s60", "60%", (220, 50, 46, 255), "OF REPUBLICANS"),
                                 ("s76", "76%", (58, 98, 224, 255), "OF DEMOCRATS")):
            sh = Image.new("RGBA", (780, 580), (250, 250, 248, 255))
            dd = ImageDraw.Draw(sh); dd.rectangle([0, 0, 779, 579], outline=(205, 205, 203, 255), width=4)
            dd.text((50, 40), val, font=font("ArialBlack.ttf", 190), fill=col)
            dd.text((50, 300), who, font=font("Oswald-Bold.ttf", 92), fill=(34, 32, 32, 255))
            dd.text((50, 410), "OPPOSE", font=font("Oswald-Bold.ttf", 92), fill=(34, 32, 32, 255))
            _G31T[k] = sh
    return _G31T

def g31(t):
    cam = g31_cam(t)
    img = room_p(cam)
    tx = _g31_tex()
    chairs = _g31_chairs()
    # цвет: красный идёт по левому клину от прохода наружу 0.35→0.85, синий 1.02→1.45
    sw_r = TH0 + (TH1 - TH0) * seg(t, 0.35, 0.85)
    sw_b = TH0 + (TH1 - TH0) * seg(t, 1.02, 1.45)
    lit = 0.28 * seg(t, 3.65, 3.9)                         # «а тут они согласны» — обе стороны одинаково
    # тени на пол одним слоем, кресла после, от дальних к ближним
    shl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(shl)
    items = []
    for (x, z, yaw, side, th, k) in chairs:
        t_row = (0.0 if side < 0 else 0.12) + 0.035 * k
        s = out_back(seg(t, t_row, t_row + 0.12))
        if s <= 0.02: continue
        sw = sw_r if side < 0 else sw_b
        if side < 0: tcol = 0.35 + 0.5 * (th - TH0) / (TH1 - TH0)
        else:        tcol = 1.02 + 0.43 * (th - TH0) / (TH1 - TH0)
        if th < sw - 1e-6:
            base = G31_RED if side < 0 else G31_BLUE
            fl = 1.3 if (t - tcol) < 0.07 else 1.0
            col = tuple(min(255, int((base[i] * (1 - lit) + 255 * lit) * fl)) for i in range(3))
        else:
            col = G31_GRAY
        dist = (x - cam.x) ** 2 + (z - cam.z) ** 2
        items.append((dist, x, z, yaw, col, s))
        fx, fz = math.sin(yaw), math.cos(yaw)
        sh = [(x - 0.17 * s + 0.12, 0.01, z - 0.2 * s + 0.16), (x + 0.17 * s + 0.12, 0.01, z - 0.2 * s + 0.16),
              (x + 0.17 * s + 0.2, 0.01, z + 0.17 * s + 0.25), (x - 0.17 * s + 0.2, 0.01, z + 0.17 * s + 0.25)]
        ds.polygon([cam.proj(p)[:2] for p in sh], fill=(30, 30, 34, 60))
    img.alpha_composite(shl)
    d = ImageDraw.Draw(img)
    # надписи на полу — под креслами по порядку рисования они не мешают: лежат дальше
    if t < 2.97:
        ex = seg(t, 2.85, 2.97)
        op = (1.0 - ex)
        for key, cx, cz, wm, lift, side, t0 in (("rep", -1.5, ZA + 0.45, 2.3, 0.07, (150, 30, 28), 0.22),
                                                 ("dem", 1.5, ZA + 0.45, 2.0, 0.07, (34, 60, 150), 0.85),
                                                 ("agree", 0.0, ZA - 2.0, 1.3, 0.09, (12, 11, 11), 1.58),
                                                 ("almost", 0.0, ZA - 2.65, 1.15, 0.09, (12, 11, 11), 1.92),
                                                 ("nothing", 0.0, ZA - 3.4, 1.65, 0.10, (12, 11, 11), 2.35)):
            if t < t0: continue
            fade = 0.4 + 0.6 * clamp01((t - t0) / 0.07)
            if key == "agree" and t >= 1.82 and t < 1.92: pass
            tex = tx[key]
            if key == "agree" and t < 1.82:
                tex = block_tex(("AGREE",), set(), "ArialBlack.ttf", (30, 28, 28, 255), 0.8)
                wm = 0.75
            if ex > 0:   # улёт: смаз к камере
                for kk in (0.4, 0.8):
                    floor_text(img, cam, tex, cx, cz - 1.6 * ex * kk, wm, lift, side, 0.3 * op, steps=1)
            else:
                floor_text(img, cam, tex, cx, cz, wm, lift, side, fade * op)
    for dist, x, z, yaw, col, s in sorted(items, key=lambda q: -q[0]):
        chair(d, cam, x, z, yaw, col, s)
    if t >= 2.85:
        # DATA CENTER на тросах
        p = out_back(seg(t, 3.05, 3.15))
        if p > 0.02:
            c = quad((0.9, 2.3, ZA + 0.5), 1.7 * p, 0.45 * p)
            wire(img, cam, (0.9 - 0.6, 2.3 + 0.22, ZA + 0.5)); wire(img, cam, (0.9 + 0.6, 2.3 + 0.22, ZA + 0.5))
            extrude(img, cam, c, tx["plate"], depth=0.08, steps=3, shade=(24, 24, 26))
        lines, hl = lines_at(t, [[("THEY", 3.18, 0), ("AGREE", 3.38, 0)], [("ON", 3.52, 0), ("THIS.", 3.65, 0)]])
        hang_words(img, cam, lines, hl, -3.3, 3.75, ZA - 5.0, 0.85, "ArialBlack.ttf", (30, 28, 28, 255),
                   wires=True, depth=0.14, cond=0.8)
        # листы встают из пола и повисают
        for key, x, t0, yaw in (("s60", -2.6, 3.75, 0.2), ("s76", 2.4, 3.85, -0.2)):
            u = out_back(seg(t, t0, t0 + 0.17))
            if u <= 0: continue
            cy = -0.7 + (1.64 + 0.7) * u
            c = quad((x, cy, ZA - 11.5), 1.3, 0.95, yaw)
            for f in (0.15, 0.85):
                top = (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1], c[0][2] + (c[1][2] - c[0][2]) * f)
                wire(img, cam, top)
            put_above_floor(img, cam, c, tx[key], depth=0.03, steps=2, shade=(120, 120, 122))
    v = 0.0
    if 2.85 < t < 3.25:
        v = 1.0 - out_cubic(seg(t, 2.85, 3.2)) ** 0.5
        img = rush_blur(img, clamp01(v * 1.4))
    return img

# ============================================================== G32 · шар из точек

_LAND = [
 [(-168,66),(-160,70),(-140,70),(-125,72),(-110,73),(-95,72),(-80,70),(-65,62),(-60,50),(-66,44),
  (-70,42),(-75,36),(-80,32),(-81,26),(-84,30),(-90,29),(-97,27),(-97,20),(-90,18),(-87,15),(-84,10),
  (-79,8),(-85,12),(-95,16),(-105,20),(-110,24),(-115,30),(-118,34),(-124,40),(-124,48),(-130,54),
  (-140,60),(-150,61),(-165,60),(-168,66)],
 [(-79,8),(-75,10),(-62,10),(-52,4),(-50,0),(-35,-5),(-38,-13),(-40,-22),(-48,-26),(-53,-34),(-58,-38),
  (-65,-42),(-66,-47),(-68,-53),(-72,-53),(-75,-45),(-73,-35),(-71,-28),(-70,-18),(-76,-12),(-81,-5),
  (-80,0),(-78,5)],
 [(-73,78),(-60,82),(-30,83),(-20,80),(-20,70),(-42,60),(-50,62),(-55,68),(-62,72)],
 [(-9,43),(-9,37),(0,37),(12,44),(16,39),(20,40),(24,37),(28,41),(36,37),(35,33),(34,28),(38,24),(43,13),
  (52,17),(57,24),(60,26),(66,24),(72,20),(77,8),(80,13),(86,21),(90,22),(94,19),(98,10),(104,2),(108,12),
  (110,20),(115,23),(121,30),(122,38),(126,36),(128,40),(135,44),(141,52),(150,60),(156,52),(160,55),
  (163,60),(170,62),(180,66),(180,71),(160,72),(140,73),(120,73),(100,77),(80,73),(68,69),(55,69),(45,68),
  (35,68),(30,70),(20,70),(14,65),(10,60),(5,59),(8,57),(12,55),(8,54),(4,52),(0,51),(-5,48),(-2,46)],
 [(-17,15),(-17,21),(-10,30),(-5,36),(10,37),(20,32),(32,31),(35,24),(38,18),(43,12),(51,12),(50,5),
  (42,-2),(40,-10),(35,-20),(33,-26),(28,-33),(20,-35),(17,-29),(12,-18),(13,-10),(9,-2),(9,4),(3,6),
  (-5,5),(-8,5),(-14,8)],
 [(114,-22),(114,-34),(118,-35),(130,-32),(137,-35),(140,-38),(147,-39),(150,-37),(153,-30),(153,-25),
  (146,-18),(142,-11),(137,-12),(131,-12),(126,-14),(122,-18)],
 [(-6,50),(-3,54),(-5,58),(-2,58),(1,52),(-2,50)],
 [(130,32),(136,35),(140,36),(142,42),(140,45),(138,40),(134,34)],
 [(44,-12),(49,-13),(50,-18),(48,-25),(44,-25),(43,-18)],
 [(95,5),(104,-5),(106,-6),(100,0)], [(109,-1),(117,0),(119,2),(116,6),(110,4),(108,1)],
 [(-180,-70),(180,-70),(180,-90),(-180,-90)],
]

def _inpoly(px, py, poly):
    inside = np.zeros(len(px), bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        cond = (y1 > py) != (y2 > py)
        xint = x1 + (py - y1) * (x2 - x1) / ((y2 - y1) if y2 != y1 else 1e-9)
        inside ^= cond & (px < xint)
    return inside

_GL = {}
def _g32_dots():
    """точки по равномерной сетке на сфере, только суша: (lat, lon) в радианах"""
    if "lat" not in _GL:
        lats, lons = [], []
        step = 2.75
        for la in np.arange(-84, 84.1, step):
            n = max(8, int(round(360 * math.cos(math.radians(la)) / step)))
            for i in range(n):
                lo = -180 + 360 * (i + 0.5 * (int(la / step) % 2)) / n
                lats.append(la); lons.append(lo)
        lats = np.array(lats); lons = np.array(lons)
        land = np.zeros(len(lats), bool)
        for poly in _LAND:
            land |= _inpoly(lons, lats, poly)
        rng = np.random.default_rng(32)
        n = int(land.sum())
        _GL["lat"] = np.radians(lats[land]); _GL["lon"] = np.radians(lons[land])
        _GL["n"] = n
        # вход: разлёт по залу, из которого точки стягиваются
        dirs = rng.normal(size=(n, 3)); dirs /= np.linalg.norm(dirs, axis=1)[:, None]
        _GL["start"] = dirs * (1.6 + 3.2 * rng.random(n))[:, None]
        _GL["start"][:, 1] = np.abs(_GL["start"][:, 1]) * 0.6 + 0.2
        _GL["ta"] = 0.05 + 0.55 * rng.random(n)
        # осыпание: время отпускания по широте сверху вниз + случай
        _GL["tr"] = 1.40 + 0.45 * (1 - (np.sin(_GL["lat"]) + 1) / 2) + 0.08 * rng.random(n)
        _GL["pile_r"] = 0.25 + 1.45 * np.sqrt(rng.random(n))
        _GL["pile_a"] = rng.random(n) * 2 * math.pi
    return _GL

_DOT = {}
def _dot_sprite(size):
    if size not in _DOT:
        n = 48
        yy, xx = np.mgrid[0:n, 0:n]
        nx = (xx - n / 2 + 0.5) / (n / 2); ny = -(yy - n / 2 + 0.5) / (n / 2)
        r2 = nx * nx + ny * ny
        a = np.clip((1 - np.sqrt(r2)) * (n / 2) * 0.9, 0, 1)
        nz = np.sqrt(np.clip(1 - r2, 0, 1))
        lam = np.clip(nx * -0.45 + ny * 0.6 + nz * 0.66, 0, 1)
        spec = np.clip(nx * -0.3 + ny * 0.5 + nz * 0.81, 0, 1) ** 24
        rgb = np.zeros((n, n, 3), np.float32)
        rgb[..., 0] = 150 + 100 * lam + 60 * spec
        rgb[..., 1] = 100 + 95 * lam + 60 * spec
        rgb[..., 2] = 18 + 30 * lam + 90 * spec
        im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize((size, size), Image.BILINEAR)
        am = Image.fromarray((a * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR)
        _DOT[size] = (np.asarray(im, np.float32), np.asarray(am, np.float32)[..., None] / 255.0)
    return _DOT[size]

def splat_dots(arr, sx, sy, dz, size, order):
    for i in order:
        s = int(size[i]); sp, sa = _dot_sprite(s)
        x0, y0 = int(sx[i] - s / 2), int(sy[i] - s / 2)
        X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(W, x0 + s), min(H, y0 + s)
        if X1 <= X0 or Y1 <= Y0: continue
        sub = sp[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]; a = sa[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        reg = arr[Y0:Y1, X0:X1]
        reg *= (1 - a); reg += sub * a

def sphere_body(arr, cam, center, R, alpha=1.0, floor_fade=False):
    """чёрный глянцевый шар: затенение по нормали в numpy"""
    px, py, dz = cam.proj(center)
    if dz < 0.3: return
    Rp = R * F / dz
    x0, x1 = int(max(0, px - Rp - 2)), int(min(W, px + Rp + 3))
    y0, y1 = int(max(0, py - Rp - 2)), int(min(H, py + Rp + 3))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    nx = (xx - px) / Rp; ny = -(yy - py) / Rp
    r2 = nx * nx + ny * ny
    r = np.sqrt(r2)
    edge = np.clip((1 - r) * Rp * 0.8, 0, 1)
    nz = np.sqrt(np.clip(1 - r2, 0, 1))
    L1 = np.array([-0.55, 0.62, 0.56]); L1 /= np.linalg.norm(L1)
    lam = np.clip(nx * L1[0] + ny * L1[1] + nz * L1[2], 0, 1)
    H1 = np.array([-0.35, 0.55, 0.76]); H1 /= np.linalg.norm(H1)
    spec = np.clip(nx * H1[0] + ny * H1[1] + nz * H1[2], 0, 1)
    H2 = np.array([0.72, 0.30, 0.63]); H2 /= np.linalg.norm(H2)
    spec2 = np.clip(nx * H2[0] + ny * H2[1] + nz * H2[2], 0, 1)
    rim = (1 - nz) ** 3
    v = 12 + 26 * lam + 150 * spec ** 70 + 70 * spec ** 12 + 55 * spec2 ** 40 + 48 * rim + 22 * np.clip(-ny, 0, 1)
    col = np.stack([v, v, v + 3], -1)
    a = edge * alpha
    if floor_fade:
        a = a * np.clip((yy - (py - Rp)) / (2 * Rp) * 1.3, 0, 1)[...] * 1.0
        a = a * np.clip(1.0 - (yy - (py - Rp)) / (1.6 * Rp), 0, 1)
    a3 = a[..., None]
    reg = arr[y0:y1, x0:x1]
    reg *= (1 - a3); reg += col * a3

def g32_dot_positions(t, center, R, cam):
    """позиции всех точек в метрах и флаг «на поверхности»"""
    g = _g32_dots()
    n = g["n"]; lat = g["lat"]; lon = g["lon"]
    omega = math.radians(5.0)
    tr = g["tr"]
    phi = lon + math.radians(28.0) + omega * np.minimum(t, tr)
    th0 = math.pi / 2 - lat                          # полярный угол от верха
    tau = np.maximum(0.0, t - tr)
    # скольжение по меридиану вниз: θ = θ0 + 5τ + 14τ²; сход с шара на θe
    the = math.pi - 0.32
    tau1 = (-5 + np.sqrt(25 + 56 * np.maximum(0.0, the - th0))) / 28
    th = np.where(tau < tau1, th0 + 5 * tau + 14 * tau * tau, the)
    on_sphere = tau < tau1
    cx, cy, cz = center
    sx = np.sin(th) * np.cos(phi); sy = np.cos(th); sz = np.sin(th) * np.sin(phi)
    Rr = R * 1.02
    P = np.stack([cx + Rr * sx, cy + Rr * sy, cz + Rr * sz], 1)
    # свободное падение после схода
    tau2 = np.maximum(0.0, tau - tau1)
    v1 = Rr * (5 + 28 * tau1)
    vx = v1 * np.cos(the) * np.cos(phi); vy = -v1 * np.sin(the); vz = v1 * np.cos(the) * np.sin(phi)
    fall = np.stack([P[:, 0] + vx * tau2, P[:, 1] + vy * tau2 - 4.9 * tau2 * tau2, P[:, 2] + vz * tau2], 1)
    landed = fall[:, 1] <= 0.03
    pile = np.stack([cx + g["pile_r"] * np.cos(g["pile_a"]) * 1.0, np.full(n, 0.03),
                     cz + g["pile_r"] * np.sin(g["pile_a"]) * 0.75 - 0.1], 1)
    P = np.where(on_sphere[:, None], P, np.where(landed[:, None], pile, fall))
    # вход: стягивание из разлёта
    ua = np.array([out_expo(v) for v in np.clip((t - g["ta"]) / 0.38, 0, 1)]) if t < 1.2 else np.ones(n)
    start = np.array(center) + g["start"]
    P = start + (P - start) * ua[:, None]
    normal = np.stack([sx, sy, sz], 1)
    return P, on_sphere & (ua > 0.999), normal

def g32(t):
    sm1 = smooth(seg(t, 0, 2.4)); sm2 = smooth(seg(t, 2.4, 4.5))
    cam = Cam(0.55 * sm1 - 0.25 * sm2, 1.55, 1.3 * sm1 - 1.0 * sm2, 0.0)
    img = room(cam)
    R = 1.15 * out_back(seg(t, 0.0, 0.30))
    center = (-1.0, 1.2, 5.4)
    arr = to_arr(img)
    # тень-контакт и отражение шара в полу
    if R > 0.05:
        sh = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([8, 8, 88, 88], fill=(30, 30, 34, 150))
        sh = sh.filter(ImageFilter.GaussianBlur(9))
        q = [(center[0] - R * 1.1, 0.01, center[2] + R * 1.1), (center[0] + R * 1.1, 0.01, center[2] + R * 1.1),
             (center[0] + R * 1.1, 0.01, center[2] - R * 1.1), (center[0] - R * 1.1, 0.01, center[2] - R * 1.1)]
        img = to_img(arr); paste_quad(img, sh, [cam.proj(p) for p in q]); arr = to_arr(img)
        sphere_body(arr, cam, (center[0], -center[1], center[2]), R, alpha=0.22, floor_fade=True)
    P, on_s, normal = g32_dot_positions(t, center, max(R, 0.02), cam)
    # точки за шаром: на поверхности — по нормали к камере; в полёте — за плоскостью центра внутри круга
    sx, sy, dz = proj_np(cam, P)
    pcx, pcy, pdz = cam.proj(center); Rp = R * F / pdz
    vcam = np.array([cam.x - center[0], cam.y - center[1], cam.z - center[2]]); vcam /= np.linalg.norm(vcam)
    ndv = normal @ vcam
    inside = (sx - pcx) ** 2 + (sy - pcy) ** 2 < Rp * Rp
    hidden = np.where(on_s, ndv < 0.06, (dz > pdz) & inside)
    size = np.clip(0.062 * F / dz, 4, 60)
    keep = (~hidden) & (dz > 0.4) & (sx > -40) & (sx < W + 40) & (sy > -40) & (sy < H + 40)
    far = keep & (dz > pdz)
    near = keep & ~far
    # дальние точки → шар → ближние точки
    idx = np.nonzero(far)[0]; idx = idx[np.argsort(-dz[idx])]
    splat_dots(arr, sx, sy, dz, size, idx)
    if R > 0.02: sphere_body(arr, cam, center, R)
    idx = np.nonzero(near)[0]; idx = idx[np.argsort(-dz[idx])]
    splat_dots(arr, sx, sy, dz, size, idx)
    img = to_img(arr)
    # трос и узел сверху
    if R > 0.3:
        wire(img, cam, (center[0], center[1] + R, center[2]), color=(70, 70, 74, 230), width=2)
        kx, ky, kdz = cam.proj((center[0], center[1] + R + 0.05, center[2]))
        kr = 0.06 * F / kdz
        ImageDraw.Draw(img).ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill=(24, 24, 26, 255))
    # «солнце» над шаром: гаснет 1.40-1.55
    es = 0.55 * (1 - seg(t, 1.40, 1.55)) * clamp01(t / 0.25)
    if es > 0.03:
        img = embers(img, cam, [(center[0], center[1] + R + 0.5, center[2], es)], t, glow=1.3)
    # надпись на тросах
    if t < 2.5:
        spec = [[("FOR", 0.27, 0), ("EVERY", 0.40, 0), ("SINGLE", 0.67, 1)],
                [("USER", 1.40, 0), ("ON", 1.47, 0), ("EARTH", 1.67, 0)]]
        lines, hl = lines_at(t, spec)
        ex = seg(t, 2.42, 2.5)
        hang_words(img, cam, lines, hl, -0.3, 3.65, 10.5, 0.36, wires=True, depth=0.07, exit_u=ex)
    else:
        spec = [[("THIS", 2.55, 0), ("WAS", 2.65, 0), ("THE", 2.75, 0), ("FIRST", 2.85, 1)],
                [("TIME", 3.05, 0), ("SOMETHING", 3.3, 0)], [("LIKE", 3.55, 0), ("THIS", 3.7, 0), ("HAPPENED.", 3.9, 0)]]
        lines, hl = lines_at(t, spec)
        hang_words(img, cam, lines, hl, -0.3, 3.65, 10.5, 0.36, wires=True, depth=0.07)
    return img

# ============================================================== G33 · галерея рам

ZF = 22.0
FW, FH, FY, FSTEP = 1.0, 1.6, 1.75, 1.62

def _frame_tex(i):
    key = ("frame", i)
    if key in _TEX: return _TEX[key]
    w, h = 300, 480
    im = Image.new("RGBA", (w, h), (248, 247, 244, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(70, 70, 74, 255), width=5)
    d.rectangle([w // 2 - 22, 0, w // 2 + 22, 26], fill=(28, 28, 30, 255))        # зажим
    ink = (44, 44, 48, 255); cx, cy = w / 2, h / 2 + 20
    if i == 0:
        d.ellipse([cx - 95, cy - 95, cx + 95, cy + 95], outline=ink, width=6)
        d.ellipse([cx - 45, cy - 30, cx + 45, cy + 30], outline=ink, width=6)
    elif i == 1:
        d.ellipse([cx - 110, cy - 60, cx + 110, cy + 60], outline=ink, width=6)
        d.ellipse([cx - 40, cy - 18, cx + 40, cy + 18], outline=ink, width=6)
    elif i == 2:
        d.line([cx, cy - 130, cx, cy + 130], fill=ink, width=5)
        for k in range(-3, 4): d.line([cx - 12, cy + k * 40, cx + 12, cy + k * 40], fill=ink, width=4)
        pts = [(cx - 110 + k * 2.2, cy + 70 * math.sin(k / 100 * 2 * math.pi * 1.5)) for k in range(101)]
        d.line(pts, fill=ink, width=6)
    elif i == 3:
        for k in range(-3, 4):
            d.line([cx + k * 40, cy - 125, cx + k * 40, cy + 125], fill=ink, width=4)
            d.line([cx - 125, cy + k * 40, cx + 125, cy + k * 40], fill=ink, width=4)
        d.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], outline=ink, width=6)
    elif i == 4:
        for k in range(-3, 4):
            yk = cy + k * 42
            amp = 10 if abs(k) > 1 else 22
            pts = [(cx - 115 + j * 2.3, yk + amp * math.sin(j / 100 * 2 * math.pi * 1.2 + k)) for j in range(101)]
            d.line(pts, fill=ink, width=5)
        d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], outline=ink, width=6)
    elif i == 5:
        for k in (-1, 1):
            pts = [(cx - 110 + j * 2.2, cy + k * 45 + 28 * math.sin(j / 100 * 2 * math.pi)) for j in range(101)]
            d.line(pts, fill=ink, width=6)
    else:
        d.ellipse([cx - 100, cy - 100, cx + 100, cy + 100], outline=ink, width=6)
        d.ellipse([cx - 100, cy - 30, cx + 100, cy + 30], outline=ink, width=5)
        d.ellipse([cx + 20, cy - 70, cx + 60, cy - 40], outline=ink, width=5)
    _TEX[key] = im
    return im

_G33 = {}
def _g33_particles():
    if "cloud" not in _G33:
        rng = np.random.default_rng(33)
        n1 = 2600
        cl = np.stack([rng.uniform(-7, 7, n1), rng.uniform(2.4, 6.0, n1), rng.uniform(ZF - 62, ZF + 12, n1)], 1)
        _G33["cloud"] = cl
        _G33["cs"] = rng.uniform(0.05, 0.16, n1) ** 1.0
        _G33["cph"] = rng.uniform(0, 6.28, n1)
        _G33["td"] = 1.0 + 1.4 * rng.random(n1)
        _G33["yfloor"] = 0.12 + 0.5 * rng.random(n1)
        n2 = 520
        st = np.stack([rng.uniform(-6, 6, n2), rng.uniform(2.4, 5.0, n2), rng.uniform(ZF - 12, ZF + 4, n2)], 1)
        p = rng.random(n2); off = 0.06 + 0.26 * rng.random(n2)
        bw, bh = FW + 0.22, FH + 0.22
        per = 2 * (bw + bh); s = p * per
        tx = np.zeros(n2); ty = np.zeros(n2)
        m = s < bw;                 tx[m] = -bw / 2 + s[m];               ty[m] = bh / 2 + off[m]
        m = (s >= bw) & (s < bw + bh); tx[m] = bw / 2 + off[m];           ty[m] = bh / 2 - (s[m] - bw)
        m = (s >= bw + bh) & (s < 2 * bw + bh); tx[m] = bw / 2 - (s[m] - bw - bh); ty[m] = -bh / 2 - off[m]
        m = s >= 2 * bw + bh;        tx[m] = -bw / 2 - off[m];            ty[m] = -bh / 2 + (s[m] - 2 * bw - bh)
        tg = np.stack([tx, FY + ty, ZF + 0.12 + 0.15 * rng.random(n2)], 1)
        _G33["hst"] = st; _G33["htg"] = tg
        _G33["hs"] = rng.uniform(0.05, 0.10, n2); _G33["hph"] = rng.uniform(0, 6.28, n2)
        _G33["th"] = 0.9 + 0.45 * rng.random(n2)
    return _G33

def g33_cam(t):
    u = seg(t, 0, 1.1)
    d = 9.5 + 50 * 2 ** (-12 * u)
    d -= 1.5 * smooth(seg(t, 1.2, 3.2))
    k = seg(t, 3.2, 4.5) ** 2
    d -= 2.6 * k
    x = 0.6 * k
    return Cam(x, 1.55, ZF - d, 0.0), d

def g33(t):
    cam, d = g33_cam(t)
    img = room(cam)
    g = _g33_particles()
    # «TEN THOUSAND» на полу под камерой в первые кадры
    if t < 0.2:
        tex = block_tex(("TEN THOUSAND",), set(), "ArialBlack.ttf", (30, 28, 28, 255), 0.8)
        floor_text(img, cam, tex, 0.0, ZF - 56.5, 9.0, 0.5, (14, 13, 13), 1.0, steps=2)
    # частицы: облако оседает к полу, часть стекается к средней раме
    u = np.array([smooth(v) for v in np.clip((t - g["td"]) / 0.9, 0, 1)])
    cl = g["cloud"].copy()
    cl[:, 1] = cl[:, 1] + (g["yfloor"] - cl[:, 1]) * u
    cl[:, 1] += 0.05 * np.sin(1.7 * t + g["cph"])
    uh = np.array([out_cubic(v) for v in np.clip((t - g["th"]) / 0.35, 0, 1)])
    hl = g["hst"] + (g["htg"] - g["hst"]) * uh[:, None]
    hl[:, 0] += 0.035 * np.sin(6.0 * t + g["hph"]) * uh
    hl[:, 1] += 0.035 * np.cos(5.0 * t + g["hph"]) * uh
    P = np.concatenate([cl, hl]); S = np.concatenate([g["cs"], g["hs"]]); PH = np.concatenate([g["cph"], g["hph"]])
    far = P[:, 2] > ZF - 0.02
    arr = to_arr(img)
    arr = ember_field(arr, cam, P[far], S[far], t, PH[far], glow=0.95)
    img = to_img(arr)
    # рамы на тросах, с тенью на полу
    for i in range(7):
        x = (i - 3) * FSTEP
        c = quad((x, FY, ZF), FW, FH)
        if ZF - cam.z < 0.4: continue
        tex = _frame_tex(i)
        if d < 30:
            floor_shadow(img, cam, c, tex)
        for f in (0.5,):
            wire(img, cam, (x, FY + FH / 2, ZF), color=(80, 82, 86, 230), width=2)
        extrude(img, cam, c, tex, depth=0.04, steps=2, shade=(150, 150, 152))
    arr = to_arr(img)
    arr = ember_field(arr, cam, P[~far], S[~far], t, PH[~far], glow=0.95)
    img = to_img(arr)
    # надписи
    top = [[("$1,000,000", 0.30, 1)], [("NAVIER-STOKES", 0.37, 0)]]
    lines, hl_ = lines_at(t, top)
    hang_words(img, cam, lines, hl_, -1.85, 4.1, ZF - 0.6, 0.36, wires=True, depth=0.07)
    if t < 1.37:
        bot = [[("A", -1, 0), ("MILLION-DOLLAR", -1, 1)], [("PRIZE", 0.77, 0), ("PROBLEM", 1.10, 0)]]
        ex = seg(t, 1.28, 1.37)
    elif t < 3.1:
        bot = [[("ABOUT", 1.37, 0), ("HOW", 1.67, 0), ("WATER", 2.05, 0)], [("FLOWS,", 2.30, 0)]]
        ex = seg(t, 2.98, 3.08)
    else:
        bot = [[("THAT", 3.1, 0), ("HAD", 3.1, 0), ("STUMPED", 3.1, 0)], [("MATHEMATICIANS", 3.6, 0)],
               [("FOR", 4.0, 0), ("GENERATIONS.", 4.3, 0)]]
        ex = 0.0
    lines, hl_ = lines_at(t, bot)
    hang_words(img, cam, lines, hl_, -4.1, 0.95, ZF - 0.6, 0.30, wires=False, depth=0.07, exit_u=ex)
    # смаз пролёта по скорости
    if t < 0.9:
        v = 50 * 12 * math.log(2) / 1.1 * 2 ** (-12 * seg(t, 0, 1.1))
        img = rush_blur(img, clamp01(v / 70.0))
    return img

SCENES = {"G31": (g31, 4.5), "G32": (g32, 4.5), "G33": (g33, 4.5)}
