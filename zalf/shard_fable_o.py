# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть O: G27 G28 G29 G30 — данные, ставшие предметами зала).
Запуск: shard_fable.py G27 out.mp4 · один кадр: ZAL_FRAME=1.9 shard_fable.py G27 k.png

Числа сняты с плёнки покадрово (polosy/G27_vhod, G27_sery, G28_vhod, G28_podpisi,
G29_vhod, G29_ai, G30_rost и сетки G27..G30_setka), перевод доли кадра в метры:
X = (fx−0.5)·0.975·d, Y = cam + (0.5−fy)·0.549·d.

  G27  кусок взят 35.25-39.75 (в таблице 37.0 — рост уже идёт). Жёлтый брусок —
       стопка плит ~0.26 м: первая плита 35.283, дальше по плите каждые ~0.2 с, плита
       прилетает СВЕРХУ (1 кадр висит над стопкой тонкой пластиной, за 2 кадра садится);
       одиннадцать плит к 37.5. Табло «2026 · JAN-AUG» висит справа и едет вверх вместе
       с верхом, цифры крутятся 0 → 116 175. Слова: JOB 36.167 · CUTS 36.333 · BLAMED
       36.833 · ON 37.0 · AI 37.167 (маркер) · ARE 37.667 · ALREADY 37.833 · DOUBLE 38.333;
       наклейка «2×» 38.467; табло «ALL OF 2025» ПАДАЕТ с потолка 38.800-38.833 (1 кадр смаза),
       серый столб встаёт из пола 38.867-39.0 (4 кадра) на половину жёлтого (54 836 / 116 175);
       ALL 38.7 · OF 38.9 · LAST 38.967 · YEAR. 39.333. Камера едет вперёд ~0.6 м/с:
       жёлтый 0.44 высоты кадра на 37.5 → 0.52 на 39.5.
  G28  кусок взят 219.0-223.5 (в таблице 221.0 — рост уже кончается). Ряд колонн из
       белых плит стоит, жёлтая растёт 219.0 → 221.8 теми же плитами сверху; счётчик
       «$135B → $725B» быстро в начале и ~150 B/с дальше (≈ u^0.35). Подпись страны
       всплывает, когда жёлтая ПРОХОДИТ её значение: DENMARK 219.733 · NORWAY 220.3 ·
       ISRAEL 220.83 · SWEDEN 221.17. Камера низкая, горизонт ниже центра (вертикали
       остаются вертикальными — шифт, не наклон); с 221.5 отъезд назад и вправо, ряд
       уходит влево. MORE 222.667 · THAN 222.75 · SWEDEN'S 222.833 (жёлтые буквы) ·
       ENTIRE 223.2 · ECONOMY 223.5 · LAST 223.8 · YEAR. 224.1.
  G29  кусок взят 201.55-206.05. Шкала — тёмный столб слева (x≈0.32), 0% у пола (y 0.72),
       100% y 0.30; уголь сидит на верхушке столба. Квадраты спускаются с потолка на
       тросах 201.583-202.35, от дальних у столба к ближним справа, каждый ~0.3 с со
       смазом; средняя 37% — толстая чёрная линия вдоль ряда. 203.75-204.3 уголь СРЫВАЕТСЯ
       с верхушки и летит вдоль линии 100%, в его следе через кадр-два встают жёлтые
       квадратики (все 12 к 204.3). AND 201.583 · SOME 201.717 · GOT 201.983 · ALMOST
       202.117 · NOTHING 202.383 · RIGHT. 202.833 · THE 203.333 · AI 203.667 · GOT 203.833 ·
       EVERY 204.017 · SINGLE 204.35 · ONE 204.883 · RIGHT. 205.167 · «AI 100%» 205.167.
  G30  кусок 161.0-165.5 (как в таблице). Столб с делениями x≈0.27 от пола (y 0.80) до
       потолка; у основания уголь «FEB» и табло «<1%» (центр y 0.69). BY 161.45 · AUGUST?
       161.55, подпись AUG встаёт сразу на ВЕРХНЕЙ отметке (y 0.28), и только потом
       161.45-162.3 (26 кадров) по столбу едет второй уголь, табло едет с ним (центр
       0.69 → 0.33), цифры 3·5·7·10·12·13·15·16·18·19·20·21·21·22·23·23·24·24·24·25…26 —
       кубический выход; столб под углём НАЛИВАЕТСЯ оранжевым от основания; строки
       «OF THE WORK…» перескакивают под табло в 161.7, когда табло проходит сквозь них.
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import *

FPS = 30
CAP = 0.715                       # высота капители Arial Black в долях кегля
COND = 0.80                       # сжатие по ширине — шрифт образца у́же Arial Black
INK = (34, 31, 30, 255)
INK_SIDE = (18, 16, 15)
YEL = (242, 206, 74, 255)
YEL_SIDE = (186, 150, 40)
SRC_GRAY = (96, 98, 102, 255)


def smooth(u):
    u = clamp01(u); return u * u * (3 - 2 * u)


# ----------------------------------------------------------------- камера со сдвигом горизонта
class SCam(Cam):
    """шифт-объектив: горизонт ниже центра кадра, зал виден «снизу вверх», а вертикали
    остаются вертикальными — так на плёнке в G28/G29 (наклона камеры там нет)"""
    def __init__(s, x=0.0, y=1.55, z=0.0, yaw=0.0, shift=0.0):
        super().__init__(x, y, z, yaw); s.shift = shift
    def proj(s, p):
        x, y, dz = Cam.proj(s, p)
        return (x, y + s.shift, dz)

def horizon(cam):
    return H / 2 + getattr(cam, "shift", 0.0)

def hall(cam, **kw):
    """зал из zal_core плюс заплатка: room() держит горизонт на H/2, при сдвиге клин
    между стенами над истинным горизонтом остаётся залит полом — красим его воздухом"""
    img = room(cam, **kw)
    sh = getattr(cam, "shift", 0.0)
    if sh > 0:
        d = ImageDraw.Draw(img)
        yh = H / 2 + sh
        k = WALL / max(0.3, CEIL - cam.y)
        far = WALL * F / FAR
        d.rectangle([W / 2 - far, H / 2, W / 2 + far, yh], fill=(230, 232, 235, 255))
        d.polygon([(W / 2 - k * sh, H / 2), (W / 2 + k * sh, H / 2), (W / 2, yh)], fill=(230, 232, 235, 255))
    return img

def floor_line(cam, dz):
    return horizon(cam) + cam.y * F / max(0.3, dz)


# ----------------------------------------------------------------- коробки (бруски, плиты, столбы)
def box(d, cam, x0, x1, y0, y1, z0, z1, top, front, side, seams=(), seam_col=None):
    """непрозрачная коробка: грани — многоугольники; видимые грани выбираются по камере.
    seams — высоты горизонтальных швов (рисуются на фронте и боку)"""
    P = lambda x, y, z: cam.proj((x, y, z))[:2]
    if y1 - y0 < 0.004: return
    # верх (камера выше) или низ (камера ниже)
    if cam.y > y1:
        d.polygon([P(x0, y1, z1), P(x1, y1, z1), P(x1, y1, z0), P(x0, y1, z0)], fill=top)
    elif cam.y < y0:
        v = tuple(int(c * 0.80) for c in side[:3]) + (255,)
        d.polygon([P(x0, y0, z1), P(x1, y0, z1), P(x1, y0, z0), P(x0, y0, z0)], fill=v)
    # бок
    if cam.x < x0:
        d.polygon([P(x0, y1, z1), P(x0, y1, z0), P(x0, y0, z0), P(x0, y0, z1)], fill=side)
        sx = x0
    elif cam.x > x1:
        d.polygon([P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1), P(x1, y0, z0)], fill=side)
        sx = x1
    else:
        sx = None
    # фронт
    d.polygon([P(x0, y1, z0), P(x1, y1, z0), P(x1, y0, z0), P(x0, y0, z0)], fill=front)
    if seams and seam_col:
        for ys in seams:
            if ys <= y0 + 0.01 or ys >= y1 - 0.01: continue
            a, b = P(x0, ys, z0), P(x1, ys, z0)
            d.line([a, b], fill=seam_col, width=2)
            if sx is not None:
                c = P(sx, ys, z1)
                d.line([P(sx, ys, z0), c], fill=seam_col, width=2)

def shadow_layer(img, cam, bases, blur=14, alpha=0.32, dirv=(0.55, 0.85)):
    """тени на полу одним слоем: bases — [(x0,x1,z0,z1,высота)]; свет спереди-слева"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    P = lambda x, z: cam.proj((x, 0.012, z))[:2]
    for (x0, x1, z0, z1, h) in bases:
        if h <= 0.02: continue
        L = min(h, 2.5) * 0.45
        ox, oz = dirv[0] * L, dirv[1] * L
        if z0 - cam.z < 0.6: continue
        d.polygon([P(x0, z0), P(x1, z0), P(x1 + ox, z0 + oz), P(x1 + ox, z1 + oz),
                   P(x0 + ox, z1 + oz), P(x0, z1)], fill=(40, 38, 36, int(255 * alpha)))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(lay)

def stack(d, cam, t, x, z, w, dp, sl, n, land, cols, seed=0, arrive=0.10, hover=0.55):
    """стопка плит, растущая из пола: плита i садится в land[i]; до этого она 3 кадра
    летит сверху (на плёнке над стопкой на кадр видна тонкая пластина). cols —
    (верх, фронт, бок, шов). Возвращает (высота стопки, [(y0,y1) летящей плиты] )"""
    top, front, side, seam = cols
    rng = np.random.default_rng(seed)
    jit = rng.uniform(-0.025, 0.025, (n, 2))
    h = 0.0
    flying = None
    for i in range(n):
        L = land[i]
        if t < L - arrive - 1e-6: break
        jx, jz = jit[i]
        x0, x1 = x - w / 2 + jx, x + w / 2 + jx
        z0, z1 = z - dp / 2 + jz, z + dp / 2 + jz
        if t >= L:
            u = seg(t, L, L + 0.07)                   # посадка: 2 кадра присед 4 %
            sq = 0.04 * math.sin(math.pi * u) if u < 1 else 0.0
            y0, y1 = i * sl, (i + 1) * sl - sq * sl
            box(d, cam, x0, x1, y0, y1, z0, z1, top, front, side)
            if i > 0:                                 # шов между плитами
                P = lambda x, y, z: cam.proj((x, y, z))[:2]
                d.line([P(x0, y0, z0), P(x1, y0, z0)], fill=seam, width=2)
                sx = x0 if cam.x < x0 else (x1 if cam.x > x1 else None)
                if sx is not None:
                    d.line([P(sx, y0, z0), P(sx, y0, z1)], fill=seam, width=2)
            h = y1
        else:
            u = seg(t, L - arrive, L)
            off = hover * (1 - u) ** 2
            y0 = i * sl + off
            box(d, cam, x0, x1, y0, y0 + sl, z0, z1, top, front, side)
            flying = (y0, y0 + sl, x0, x1, z0, z1, off)
    return h, flying


# ----------------------------------------------------------------- слова
def pop(t0, t, dur=0.10, k0=1.22):
    """вход слова как на плёнке: первый кадр крупнее и прозрачнее, за ~3 кадра садится"""
    if t < t0 - 1e-6: return None
    u = seg(t, t0, t0 + dur)
    s = k0 + (1.0 - k0) * out_cubic(u)
    op = 0.55 + 0.45 * clamp01(u * 2.2)
    return s, op

def tiles(lines, fsize=200, color=INK, hl=None, cond=COND, fname="ArialBlack.ttf"):
    """плитки слов, обрезанные по ширине: (ширина блока, высота, кегль, [(плитка, cx, cy)])"""
    tw, th, tl = word_tiles(lines, fsize=fsize, fname=fname, hl=hl, color=color)
    out = []
    for tile, cx, cy in tl:
        if cond != 1.0:
            tile = tile.resize((max(4, int(tile.size[0] * cond)), tile.size[1]), Image.LANCZOS)
            cx = cx * cond
        bb = tile.getbbox()
        if bb is None: continue
        cr = tile.crop((bb[0], 0, bb[2], tile.size[1]))
        out.append((cr, cx - tile.size[0] / 2 + (bb[0] + bb[2]) / 2, cy))
    return tw * cond, th, fsize, out

def visible(cam, corners, margin=0.35):
    return min(c[2] for c in corners) - cam.z > margin

def extrude_c(canvas, cam, corners, tex, depth, side, steps=4, opacity=1.0, floor_clip=False):
    """объём копиями в глубину (+z) с цветным боком; floor_clip — резать по линии пола"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)) if floor_clip else canvas
    alpha = tex.split()[3]
    for i in range(steps, -1, -1):
        k = i / steps
        cs = [(c[0], c[1], c[2] + depth * k) for c in corners]
        if not visible(cam, cs): continue
        pts = [cam.proj(p) for p in cs]
        if i == 0:
            tx = tex
        else:
            v = [int(side[j] * (0.80 + 0.20 * (1 - k))) for j in range(3)]
            tx = Image.new("RGBA", tex.size, (v[0], v[1], v[2], 255)); tx.putalpha(alpha)
        paste_quad(lay, tx, pts, opacity)
    if floor_clip:
        zc = sum(c[2] for c in corners) / 4.0
        yf = int(max(0, min(H, floor_line(cam, zc - cam.z))))
        if yf < H:
            ImageDraw.Draw(lay).rectangle([0, yf, W, H], fill=(0, 0, 0, 0))
        canvas.alpha_composite(lay)

def text_shadow(canvas, cam, corners, tex, off=(0.9, 1.4), blur=12, strength=0.28):
    bl, br = corners[3], corners[2]
    k = corners[0][1] - corners[3][1]
    sh = [(bl[0] + off[0] * k, 0.012, bl[2] + off[1] * k), (br[0] + off[0] * k, 0.012, br[2] + off[1] * k),
          (br[0], 0.012, br[2]), (bl[0], 0.012, bl[2])]
    if not visible(cam, sh): return
    a = tex.split()[3].point(lambda v: int(v * strength))
    dark = Image.new("RGBA", tex.size, (38, 36, 34, 255)); dark.putalpha(a)
    paste_quad(canvas, dark.filter(ImageFilter.GaussianBlur(blur)), [cam.proj(p) for p in sh])

def put_words(img, cam, t, block, center, cap_m, starts, depth=0.12, side=INK_SIDE,
              hang=False, floor=False, shadow=False, align="left", k0=1.22, rise=None):
    """block — из tiles(); center — (x, y, z): x — левый край (align=left) или центр,
    y — центр строки (floor=True: пол под нижней кромкой); starts — t0 каждого слова.
    rise — (t0, dur): весь блок выезжает из пола за dur, с перелётом 3 %."""
    tw, th, fsize, tl = block
    sc = cap_m / (CAP * fsize)
    cx0, cy0, cz = center
    for i, (tile, cx, cy) in enumerate(tl):
        p = pop(starts[i] if i < len(starts) else starts[-1], t, k0=k0)
        if p is None: continue
        s, op = p
        w, h = tile.size[0] * sc * s, tile.size[1] * sc * s
        x = cx0 + (cx if align == "left" else cx - tw / 2) * sc
        if floor:
            y = h / 2 + 0.01 + (th / 2 - cy) * sc
        else:
            y = cy0 + (th / 2 - cy) * sc
        dy = 0.0
        if rise is not None:
            r0, rd = rise
            u = seg(t, r0, r0 + rd)
            kk = 1.0 - (1.0 - u) ** 1.6
            kk += 0.03 * math.sin(math.pi * seg(t, r0 + rd, r0 + rd + 0.1))
            dy = -(1.0 - kk) * th * sc * 1.05
        c = quad((x, y + dy, cz), w, h)
        if not visible(cam, c): continue
        if shadow and dy > -0.02:
            text_shadow(img, cam, c, tile)
        if hang:
            n = 2 if w > 0.5 else 1
            for j in range(n):
                f = (j + 0.5) / n
                wire(img, cam, (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1], cz), color=(96, 98, 102, 230), width=2)
        if s > 1.08:                                 # первый кадр входа — смаз по горизонтали
            for shx in (-0.05, 0.05):
                cc = quad((x + shx * w, y + dy, cz), w, h)
                paste_quad(img, tile, [cam.proj(q) for q in cc], 0.22)
        extrude_c(img, cam, c, tile, depth, side, steps=4, opacity=op, floor_clip=rise is not None)


# ----------------------------------------------------------------- табло и наклейка
def board_tex(value, sub=None, px=640, ratio=0.47, vcol=(255, 204, 60, 255),
              scol=(236, 236, 234, 255), frame=(214, 214, 212, 255)):
    """чёрное табло в светлой тонкой рамке: сверху мелкая подпись, крупно — значение"""
    h = int(px * ratio)
    img = Image.new("RGBA", (px, h), frame)
    d = ImageDraw.Draw(img)
    d.rectangle([9, 9, px - 10, h - 10], fill=(22, 20, 19, 255))
    if sub:
        fs = font("Arimo-Bold.ttf", int(h * 0.19))
        b = d.textbbox((0, 0), sub, font=fs)
        d.text(((px - (b[2] - b[0])) / 2 - b[0], h * 0.13 - b[1]), sub, font=fs, fill=scol)
        fv = font("Oswald-Bold.ttf", int(h * 0.50)); yv = h * 0.60
    else:
        fv = font("Oswald-Bold.ttf", int(h * 0.66)); yv = h * 0.50
    b = d.textbbox((0, 0), value, font=fv)
    d.text(((px - (b[2] - b[0])) / 2 - b[0], yv - (b[3] - b[1]) / 2 - b[1]), value, font=fv, fill=vcol)
    return img

def hang_tex(img, cam, tex, center, w, h, depth=0.08, side=(70, 66, 62), wires=2, opacity=1.0, scale=1.0):
    c = quad((center[0], center[1], center[2]), w * scale, h * scale)
    if not visible(cam, c): return
    for j in range(wires):
        f = (j + 0.5) / wires
        wire(img, cam, (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1], c[0][2]), color=(104, 106, 110, 235), width=2)
    extrude_c(img, cam, c, tex, depth, side, steps=3, opacity=opacity)

def roll(v, final, t_done, t, seed=0):
    """бегущие цифры: пока растёт — младшие разряды крутятся, в t_done ровно final"""
    if t >= t_done: return final
    rng = np.random.default_rng(int(t * 1000) + seed)
    return int(v) - int(v) % 1000 + int(rng.integers(0, 1000)) if v > 1000 else int(v)


# ================================================================= G27
_G27 = {}
def _g27_blocks():
    if not _G27:
        _G27["title"] = tiles(["JOB CUTS BLAMED ON AI"], 200, hl={4})
        _G27["l1"] = tiles(["ARE ALREADY DOUBLE"], 200)
        _G27["l2"] = tiles(["ALL OF LAST YEAR."], 200)
        _G27["st"] = sticker_tex("2×", 230)
    return _G27

def g27(t):
    """столбики-бруски из пола: жёлтый растёт плитами сверху, табло едет с верхом, серый
    встаёт целиком за 4 кадра, наклейка «2×» между ними"""
    cam = Cam(0.05 * t, 1.55, 0.6 * t, 0.0)
    img = hall(cam)
    b = _g27_blocks()
    ZB = 12.5
    SL, N = 0.255, 11
    land = [0.03 + i * 0.2 for i in range(N)]
    hfull = SL * N
    # тени (оба столба) одним слоем — до коробок
    hy = min(hfull, max(0.0, (t - 0.03) / 2.0 * hfull))
    hg = 0.47 * hfull * out_expo(seg(t, 3.62, 3.75))
    shadow_layer(img, cam, [(0.8 - 0.72, 0.8 + 0.72, ZB - 0.57, ZB + 0.57, hy),
                            (-1.1 - 0.62, -1.1 + 0.62, ZB - 0.5, ZB + 0.5, hg)])
    d = ImageDraw.Draw(img)
    # серый столб — встаёт целиком, швы едут с ним (38.867-39.0)
    if hg > 0.01:
        ov = 1.0 + 0.03 * math.sin(math.pi * seg(t, 3.75, 3.85))
        hgg = hg * ov
        box(d, cam, -1.1 - 0.62, -1.1 + 0.62, 0.0, hgg, ZB - 0.5, ZB + 0.5,
            (204, 202, 198, 255), (176, 174, 170, 255), (150, 148, 144, 255),
            seams=[hgg - k * 0.26 for k in range(1, 7)], seam_col=(132, 130, 126, 255))
    # жёлтая стопка
    hy_real, fly = stack(d, cam, t, 0.8, ZB, 1.45, 1.15, SL, N, land,
                         ((250, 216, 98, 255), (236, 196, 52, 255), (198, 158, 40, 255), (184, 146, 32, 255)), seed=3)
    if fly is not None and fly[6] > 0.05:              # смаз летящей плиты
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        y0, y1, x0, x1, z0, z1, off = fly
        for k in (0.5, 1.0):
            P = lambda x, y, z: cam.proj((x, y, z))[:2]
            yy = y0 + off * 0.6 * k
            dl.polygon([P(x0, yy + SL, z0), P(x1, yy + SL, z0), P(x1, yy, z0), P(x0, yy, z0)], fill=(236, 196, 52, 70))
        img.alpha_composite(lay)
    # табло 2026 · JAN-AUG: едет вверх с ростом, цифры крутятся
    hv = min(hfull, max(0.0, (t - 0.03) / 2.05 * hfull))
    val = roll(116175 * hv / hfull, 116175, 2.25, t)
    tex = board_tex(f"{val:,}", "2026 · JAN-AUG")
    yc = max(0.75, hv - 0.85 + 0.38)
    hang_tex(img, cam, tex, (2.55, yc, ZB), 1.65, 1.65 * 0.47)
    # табло ALL OF 2025 — падает с потолка 38.800-38.833 (t 3.55-3.60)
    if t >= 3.55:
        u = seg(t, 3.55, 3.62)
        drop = (CEIL - 2.4) * (1 - u) ** 2
        tex2 = board_tex("54,836", "ALL OF 2025", vcol=(240, 240, 238, 255))
        if u < 1:
            for k in (0.4, 0.8):
                c = quad((-1.4, 2.38 + drop + k * 0.5, ZB), 2.2, 2.2 * 0.47)
                paste_quad(img, tex2, [cam.proj(q) for q in c], 0.25)
        hang_tex(img, cam, tex2, (-1.4, 2.38 + drop, ZB), 2.2, 2.2 * 0.47)
    # наклейка 2× (38.467 → t 3.22)
    p = pop(3.22, t, k0=1.25)
    if p is not None:
        s, op = p
        st = b["st"]
        hang_tex(img, cam, st, (3.5, 0.74, ZB), 1.5, 1.5 * st.size[1] / st.size[0], depth=0.05,
                 side=YEL_SIDE, opacity=op, scale=s)
    # надписи
    put_words(img, cam, t, b["title"], (-3.9, 3.54, ZB), 0.54, [0.92, 1.08, 1.58, 1.75, 1.92],
              depth=0.16, hang=True)
    put_words(img, cam, t, b["l1"], (-3.3, 0.0, 10.6), 0.17, [2.42, 2.58, 3.08], depth=0.10,
              floor=True, shadow=True)
    put_words(img, cam, t, b["l2"], (0.5, 0.0, 10.6), 0.17, [3.45, 3.65, 3.72, 4.08], depth=0.10,
              floor=True, shadow=True)
    source_line(img, "Job cuts report · 2026")
    return img


# ================================================================= G28
# ряд плотный: шаг ~0.8 м по x и 0.6 м в глубину (сетка 219.3: центры колонн 0.07 · 0.20 ·
# 0.33 · 0.44 · 0.55 · 0.70 ширины кадра, ширина каждой ~0.08-0.11 → ~0.6 м на 6-9 м)
G28_ROW = [("FINLAND", 300, -3.0, 9.4), ("DENMARK", 462, -2.2, 8.8), ("NORWAY", 531, -1.4, 8.2),
           ("ISRAEL", 611, -0.6, 7.6), ("SWEDEN", 669, 0.2, 7.0)]
G28_YEL = (1.2, 6.2)
G28_M = 2.9 / 725.0            # метров на миллиард: $725B → 2.9 м (сетка 223.8: 0.55 кадра на ~9 м)
_G28 = {}
def _g28_blocks():
    if not _G28:
        for name, v, x, z in G28_ROW:
            _G28[name] = tiles([f"{name} ${v}B"], 200)
        _G28["t1"] = tiles(["MORE THAN"], 200)
        _G28["t2"] = tiles(["SWEDEN'S"], 200, color=YEL)
        _G28["t3"] = tiles(["ENTIRE ECONOMY LAST YEAR."], 200)
        _G28["head"] = tiles(["FOUR COMPANIES", "WILL SPEND"], 200)
    return _G28

def g28_value(t):
    u = seg(t, 0.0, 2.8)
    return 725.0 * (u ** 0.35)

def g28(t):
    """колонны-страны: ряд белых стопок стоит, жёлтая растёт плитами, подписи стран
    всплывают, когда жёлтая проходит их высоту; камера низкая и смотрит вверх (шифт),
    потом отъезд назад-вправо с выравниванием горизонта"""
    k = smooth(seg(t, 0.8, 3.4))
    cam = SCam(0.12 * t, 1.3 + 0.25 * k, -3.8 * k, 0.0, shift=110 * (1 - k))
    img = hall(cam)
    b = _g28_blocks()
    SL = 0.25
    W_, D_ = 0.60, 0.46
    val = g28_value(t)
    hy = val * G28_M
    bases = []
    for name, v, x, z in G28_ROW:
        bases.append((x - W_ / 2, x + W_ / 2, z - D_ / 2, z + D_ / 2, v * G28_M))
    bases.append((G28_YEL[0] - W_ / 2, G28_YEL[0] + W_ / 2, G28_YEL[1] - D_ / 2, G28_YEL[1] + D_ / 2, hy))
    shadow_layer(img, cam, bases, alpha=0.28)
    d = ImageDraw.Draw(img)
    white = ((240, 238, 234, 255), (216, 212, 206, 255), (188, 184, 178, 255), (170, 166, 160, 255))
    rng = np.random.default_rng(11)
    for name, v, x, z in G28_ROW:               # дальние первыми
        h = v * G28_M
        n = int(h / SL) + 1
        land = [-1.0] * n
        stack(d, cam, 10.0, x, z, W_, D_, SL, n, land, white, seed=int(rng.integers(0, 999)))
        # верхняя плита — до точной высоты: перекрываем её коробкой
        box(d, cam, x - W_ / 2 - 0.03, x + W_ / 2 + 0.03, (n - 1) * SL - 0.01, h, z - D_ / 2 - 0.03, z + D_ / 2 + 0.03,
            white[0], white[1], white[2])
    # жёлтая: плиты садятся по мере роста значения
    N = int(2.9 / SL) + 1
    land = []
    for i in range(N):
        need = (i + 1) * SL / G28_M                   # значение, при котором плита i ложится
        land.append(2.8 * min(1.0, need / 725.0) ** (1 / 0.35))
    yl = ((250, 216, 98, 255), (236, 196, 52, 255), (198, 158, 40, 255), (184, 146, 32, 255))
    hreal, fly = stack(d, cam, t, G28_YEL[0], G28_YEL[1], W_, D_, SL, N, land, yl, seed=5, hover=0.5)
    if fly is not None and fly[6] > 0.05:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        y0, y1, x0, x1, z0, z1, off = fly
        P = lambda x, y, z: cam.proj((x, y, z))[:2]
        for kk in (0.5, 1.0):
            yy = y0 + off * 0.6 * kk
            dl.polygon([P(x0, yy + SL, z0), P(x1, yy + SL, z0), P(x1, yy, z0), P(x0, yy, z0)], fill=(236, 196, 52, 70))
        img.alpha_composite(lay)
    # счётчик $…B — жёлтые объёмные цифры справа от верха, на тросе
    vv = int(round(val / 5.0) * 5) if t < 2.8 else 725
    cnt = tiles([f"${vv}B"], 200, color=YEL)
    top = max(hy, 0.3)
    put_words(img, cam, t, cnt, (G28_YEL[0] + 0.55, top - 0.05, G28_YEL[1] - 0.2), 0.27, [-1.0], depth=0.10,
              side=YEL_SIDE, hang=True, k0=1.0)
    # подписи стран: всплывают, когда жёлтая прошла их значение; лесенкой слева от колонн
    for i, (name, v, x, z) in enumerate(G28_ROW):
        if name == "FINLAND": continue
        t0 = 2.8 * (v / 725.0) ** (1 / 0.35)
        blk = b[name]
        wmm = blk[0] * 0.20 / (CAP * 200)
        put_words(img, cam, t, blk, (x - 0.15 - wmm, 0.45 + 0.42 * (i - 1), z - D_ / 2 - 0.6), 0.20, [t0, t0], depth=0.08)
    # заголовок в начале (на плёнке 219.0 он уже уходит) и в конце
    if t < 0.45:
        put_words(img, cam, t, b["head"], (-2.6, 3.9, 10.5), 0.22, [-1, -1, -1, -1], depth=0.08, hang=True)
    zt = 5.4
    put_words(img, cam, t, b["t1"], (0.9, 3.75, zt), 0.24, [3.67, 3.75], depth=0.10, hang=True)
    put_words(img, cam, t, b["t2"], (0.9 + b["t1"][0] * 0.24 / (CAP * 200) + 0.12, 3.75, zt), 0.24, [3.83],
              depth=0.10, side=YEL_SIDE, hang=True)
    put_words(img, cam, t, b["t3"], (0.9, 3.38, zt), 0.24, [4.2, 4.35, 4.45, 4.5], depth=0.10)
    source_line(img, "IMF · Apr 2026 · company filings")
    return img


# ================================================================= G29
G29_POST = (-2.27, 13.3)
G29_END = (1.9, 5.2)
G29_TOP = 3.07
G29_VALS = [45, 30, 88, 12, 52, 5, 95, 27, 60, 9, 41, 3]
_G29 = {}
def _g29_blocks():
    if not _G29:
        _G29["p100"] = tiles(["100%"], 200); _G29["p90"] = tiles(["90%"], 200)
        _G29["avg"] = tiles(["AVERAGE 37%"], 200); _G29["p0"] = tiles(["0%"], 200)
        _G29["acc"] = tiles(["12 ACCOUNTANTS"], 200)
        _G29["a1"] = tiles(["AND SOME GOT", "ALMOST NOTHING RIGHT."], 200, hl={4})
        _G29["a2"] = tiles(["THE AI GOT", "EVERY SINGLE", "ONE RIGHT."], 200, hl={3, 4})
        _G29["ai"] = tiles(["AI 100%"], 200, hl={0, 1})
    return _G29

def g29_row(s):
    return (G29_POST[0] + (G29_END[0] - G29_POST[0]) * s, G29_POST[1] + (G29_END[1] - G29_POST[1]) * s)

def row_line(d, cam, y, s0, s1, col, width):
    """линия вдоль ряда на высоте y от параметра s0 до s1, обрезанная перед камерой"""
    pts = []
    for s in np.linspace(s0, s1, 24):
        x, z = g29_row(s)
        if z - cam.z < 1.2: break
        pts.append(cam.proj((x, y, z))[:2])
    if len(pts) > 1:
        d.line(pts, fill=col, width=width, joint="curve")

def g29(t):
    """разброс точек на нитях: квадраты спускаются с потолка к своим высотам, средняя —
    чёрная линия вдоль ряда, потом уголь срывается с верхушки шкалы и ведёт линию 100 %,
    в его следе встают жёлтые квадратики"""
    cam = SCam(0.1 * t, 1.2, 0.25 * t, 0.0, shift=60)
    img = hall(cam)
    b = _g29_blocks()
    px, pz = G29_POST
    SQW, SQH = 0.55, 0.68
    # положения квадратов
    sq = []
    for i, v in enumerate(G29_VALS):
        s = (i + 0.6) / 12.5
        x, z = g29_row(s)
        bottom = max(0.05, v / 100.0 * G29_TOP)
        t0 = 0.03 + i * 0.055
        u = seg(t, t0, t0 + 0.30)
        if t < t0 - 1e-6:
            continue
        off = (CEIL - bottom - SQH) * (1 - u) ** 2
        sq.append((i, s, x, z, bottom + off, u, v))
    # тени на полу — от севших квадратов
    shadow_layer(img, cam, [(x - SQW / 2, x + SQW / 2, z - 0.05, z + 0.05, 0.6) for (i, s, x, z, y0, u, v) in sq if u >= 1],
                 alpha=0.30, blur=8, dirv=(0.5, 0.7))
    d = ImageDraw.Draw(img)
    P = lambda x, y, z: cam.proj((x, y, z))[:2]
    # столб шкалы
    box(d, cam, px - 0.07, px + 0.07, 0.0, G29_TOP, pz - 0.07, pz + 0.07, (72, 68, 66, 255), (52, 48, 46, 255), (36, 33, 32, 255))
    # средняя: толстая чёрная линия вдоль ряда, 100 % — тонкая
    row_line(d, cam, 0.37 * G29_TOP, 0.0, 1.9, (28, 26, 25, 255), 7)
    row_line(d, cam, G29_TOP, 0.0, 1.9, (60, 58, 56, 255), 3)
    # квадраты: дальние первыми; тросы к потолку; летящие — со смазом
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    for (i, s, x, z, y0, u, v) in sq:
        y1 = y0 + SQH
        d.line([P(x, CEIL, z), P(x, y1, z)], fill=(104, 106, 110, 255), width=2)
        if u < 1:
            for kk in (0.35, 0.7):
                yy = y0 + (1 - u) * 0.9 * kk
                dl.polygon([P(x - SQW / 2, yy + SQH, z), P(x + SQW / 2, yy + SQH, z), P(x + SQW / 2, yy, z), P(x - SQW / 2, yy, z)],
                           fill=(40, 38, 36, 60))
        box(d, cam, x - SQW / 2, x + SQW / 2, y0, y1, z - 0.04, z + 0.04, (58, 55, 53, 255), (38, 36, 35, 255), (26, 24, 23, 255))
    img.alpha_composite(lay)
    # уголь: сидит на верхушке, 2.2-2.75 летит вдоль 100 %, за ним — жёлтая линия и квадратики
    uf = seg(t, 2.2, 2.75)
    ue = uf ** 1.15 * 1.3                      # к 2.75 уходит за ряд
    if uf > 0:
        ys = G29_TOP + 0.02
        pts = []
        for s in np.linspace(0, min(ue, 1.9), 30):
            x, z = g29_row(s)
            if z - cam.z < 1.2: break
            pts.append(P(x, ys, z))
        if len(pts) > 1:
            d.line(pts, fill=(242, 206, 74, 255), width=4, joint="curve")
        for i in range(12):
            s = (i + 0.6) / 12.5
            if ue < s: continue
            x, z = g29_row(s)
            p = pop(0.0, 1.0 if ue - s > 0.06 else 0.03, k0=1.3)
            sc = p[0]
            d.line([P(x, ys, z), P(x, ys - 0.22, z)], fill=(180, 150, 40, 255), width=2)
            box(d, cam, x - 0.15 * sc, x + 0.15 * sc, ys - 0.22 - 0.3 * sc, ys - 0.22, z - 0.03, z + 0.03,
                (250, 216, 98, 255), (236, 196, 52, 255), (198, 158, 40, 255))
    # подписи шкалы
    for key, y in (("p100", G29_TOP), ("p90", 0.9 * G29_TOP), ("avg", 0.37 * G29_TOP), ("p0", 0.08)):
        blk = b[key]
        wmm = blk[0] * 0.20 / (CAP * 200)
        put_words(img, cam, t, blk, (px - 0.25 - wmm, y, pz - 0.1), 0.20, [-1] * 4, depth=0.06, k0=1.0)
    put_words(img, cam, t, b["acc"], (0.9, 0.0, 7.25), 0.15, [-1, -1], depth=0.06, floor=True, shadow=True, k0=1.0)
    # угли
    if uf <= 0:
        pts = [(px, G29_TOP + 0.10, pz - 0.15, 0.75)]
    else:
        pts = []
        for j, back in enumerate((0.0, 0.05, 0.10, 0.15)):
            s = ue - back
            if s < 0: continue
            x, z = g29_row(s)
            if z - cam.z < 1.0: continue
            pts.append((x, G29_TOP + 0.10, z - 0.15, 0.75 * (1 - j * 0.22)))
    if pts and t < 2.95:
        img = embers(img, cam, pts, t, glow=0.9)
    # верхний текст
    if t < 1.78:
        put_words(img, cam, t, b["a1"], (-4.1, 3.3, 9.6), 0.25, [0.03, 0.17, 0.43, 0.58, 0.83, 1.3], depth=0.10, hang=True)
    else:
        put_words(img, cam, t, b["a2"], (-4.1, 3.3, 9.6), 0.25, [1.78, 2.12, 2.28, 2.47, 2.8, 3.33, 3.62], depth=0.10, hang=True)
        put_words(img, cam, t, b["ai"], (-1.3, 3.85, 9.6), 0.28, [3.62, 3.62], depth=0.10, hang=True)
    source_line(img, "Survey · Oct 2026 · spread shown schematically")
    return img


# ================================================================= G30
_G30 = {}
def _g30_blocks():
    if not _G30:
        _G30["a"] = tiles(["LESS THAN", "ONE PERCENT"], 200, hl={2, 3})
        _G30["b"] = tiles(["BY AUGUST?"], 200)
        _G30["c"] = tiles(["OF THE WORK OF BUILDING", "NEW AI SYSTEMS."], 200)
        _G30["r"] = tiles(["SHARE OF THE WORK", "OF BUILDING AI", "THAT AI LEADS"], 200)
        _G30["feb"] = tiles(["FEB"], 200); _G30["aug"] = tiles(["AUG"], 200)
    return _G30

def glow_add(img, polys, blur=42, k=0.95, color=(255, 150, 40)):
    """аддитивное свечение: яркие многоугольники размываются и складываются с кадром"""
    lay = Image.new("L", (W, H), 0)
    dl = ImageDraw.Draw(lay)
    for p in polys:
        dl.polygon(p, fill=255)
    g = np.asarray(lay.filter(ImageFilter.GaussianBlur(blur)), np.float32)[..., None] / 255.0
    arr = np.asarray(img.convert("RGB"), np.float32)
    arr = arr + g * np.array(color, np.float32) * k
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

def g30(t):
    """шкала роста с подсветкой: подпись AUG встаёт на верхней отметке, потом уголь едет
    по столбу вверх, столб под ним наливается оранжевым, табло едет рядом и считает"""
    cam = Cam(0.03 * t, 1.55, 0.3 * t, 0.0)
    img = hall(cam)
    b = _g30_blocks()
    PX, PZ, PW = -2.1, 9.4, 0.22
    u = out_cubic(seg(t, 1.15, 2.0))
    y_e = 0.12 + (2.43 - 0.12) * u
    shadow_layer(img, cam, [(PX - PW / 2, PX + PW / 2, PZ - PW / 2, PZ + PW / 2, CEIL)], alpha=0.25)
    d = ImageDraw.Draw(img)
    P = lambda x, y, z: cam.proj((x, y, z))[:2]
    # основание и столб
    box(d, cam, PX - 0.45, PX + 0.45, 0.0, 0.035, PZ - 0.45, PZ + 0.45, (62, 58, 55, 255), (46, 42, 40, 255), (34, 31, 30, 255))
    box(d, cam, PX - PW / 2, PX + PW / 2, 0.035, CEIL, PZ - PW / 2, PZ + PW / 2, (70, 66, 63, 255), (50, 46, 44, 255), (34, 31, 30, 255))
    # деления линейки на фронте: каждые 0.1 м, длинные через 0.5
    for i in range(1, 50):
        y = i * 0.1
        L = 0.11 if i % 5 == 0 else 0.055
        d.line([P(PX - PW / 2, y, PZ - PW / 2 - 0.001), P(PX - PW / 2 + L, y, PZ - PW / 2 - 0.001)], fill=(150, 146, 142, 255), width=2)
    # налитая часть столба: от основания до угля
    if y_e > 0.14:
        lit = [P(PX - PW / 2, y_e, PZ - PW / 2 - 0.002), P(PX + PW / 2, y_e, PZ - PW / 2 - 0.002),
               P(PX + PW / 2, 0.04, PZ - PW / 2 - 0.002), P(PX - PW / 2, 0.04, PZ - PW / 2 - 0.002)]
        d.polygon(lit, fill=(255, 196, 92, 255))
        core = [P(PX - PW * 0.2, y_e, PZ - PW / 2 - 0.003), P(PX + PW * 0.2, y_e, PZ - PW / 2 - 0.003),
                P(PX + PW * 0.2, 0.04, PZ - PW / 2 - 0.003), P(PX - PW * 0.2, 0.04, PZ - PW / 2 - 0.003)]
        d.polygon(core, fill=(255, 236, 170, 255))
        pulse = 0.85 + 0.15 * math.sin(t * 5.0)
        img = glow_add(img, [lit], blur=40, k=0.75 * pulse)
    # табло: едет вверх рядом с углём, цифры считают
    v = 1 + 25 * u
    txt = "<1%" if t < 1.15 else f"{int(round(v))}%"
    tex = board_tex(txt, None, px=640, ratio=0.72)
    yc = 0.65 + (2.43 - 0.65) * u
    hang_tex(img, cam, tex, (-0.4, yc, PZ), 1.56, 1.56 * 0.72, wires=2)
    # подписи FEB и AUG (AUG встаёт на верхней отметке сразу, в 1.05)
    put_words(img, cam, t, b["feb"], (PX - 0.95, 0.14, PZ - 0.2), 0.16, [-1], depth=0.06, k0=1.0)
    put_words(img, cam, t, b["aug"], (PX - 0.95, 2.43, PZ - 0.2), 0.16, [1.05], depth=0.06)
    # угли: у основания всегда, второй едет по столбу
    pts = [(PX + 0.05, 0.16, PZ - 0.2, 0.8)]
    if t >= 1.15:
        pts.append((PX + 0.05, y_e + 0.04, PZ - 0.2, 0.9))
    img = embers(img, cam, pts, t, glow=0.9)
    # тексты
    if t < 1.0:
        put_words(img, cam, t, b["a"], (-1.0, 3.35, PZ), 0.22, [-1] * 4, depth=0.10, hang=True)
    else:
        put_words(img, cam, t, b["b"], (-1.0, 3.5, PZ), 0.22, [1.0, 1.1], depth=0.10, hang=True)
    if t < 1.7:
        put_words(img, cam, t, b["c"], (-1.0, 2.75, PZ), 0.20, [-1] * 7, depth=0.08)
    else:
        put_words(img, cam, t, b["c"], (-1.0, 1.55, PZ), 0.20, [1.7] * 7, depth=0.08, k0=1.1)
    put_words(img, cam, t, b["r"], (1.2, 0.6, PZ), 0.13, [-1] * 9, depth=0.05, k0=1.0)
    source_line(img, "Research note · Sep 17, 2026")
    return img


SCENES = {"G27": (g27, 4.5), "G28": (g28, 4.5), "G29": (g29, 4.5), "G30": (g30, 4.5)}

if __name__ == "__main__":
    code = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else f"{code}.png"
    t = float(os.environ.get("ZAL_FRAME", "1.0"))
    SCENES[code][0](t).convert("RGB").save(out)
    print("кадр", t, "->", out)
