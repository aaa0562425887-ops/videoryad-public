# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть N: G14, G19, G22, G45 — «бумажная» группа).
Запуск: shard_fable_n.py <код> <out.mp4>; один кадр: ZAL_FRAME=1.9 shard_fable_n.py G14 k.png

Главное в каждом приёме — КАК содержимое появляется, а не как лист выглядит стоя.
Числа сняты с плёнки покадрово (polosy/G14_*, G19_*, G22_*, G45_*):

  G14  28.867-30.533 (t=0 ↔ 28.867). Доска-табло стоит со склейки, камера наезжает
       (+11% ширины за 1.67 с). Жёлтая строка ARTIFICIAL INTELLIGENCE перебирается с
       8-й строки на 2-ю: каждый ход = 1 кадр «мусора» в двух соседних строках (половинки
       знаков, жёлтое с белым вперемешку) + 1-3 кадра покоя: покой на 8 до 29.100, перебор
       29.133, 7 (29.167-29.233), 29.267-29.300 два хода подряд, 5 (29.333), 4 (29.367-29.400),
       3 (29.467-29.500), 2 (29.567-29.700); 29.733 перебор ВСЕЙ доски → 29.767 наверху
       «#1 ARTIFICIAL / INTELLIGENCE» ×1.65, список сдвинут вверх на строку.
       Слева на тросах: AI(наклейка, с 0) · WAS 29.067 · THE 29.267 · NUMBER 29.333 (перелёт 17%,
       1 кадр) · ONE(наклейка 29.767, растёт 85→100% за 3 кадра) · REASON 29.967.
  G19  99.100-102.967 (t=0 ↔ 99.100). Лист 3:2 на двух тросах от углов, правый край ближе
       (hL/hR 0.85 → 1.00 к 102.5): камера уходит вправо и доворачивает, угли слева уезжают
       с x 0.33 до 0.145, лист на экране стоит. Маркер — три мазка СЛЕВА НАПРАВО под буквами:
       99.633-99.767 (5 к.), 99.733-99.900 (6 к.), 100.700-100.933 (8 к.), текст сквозь него виден.
       На полу объёмные слова: A REAL (с 0) · COMPANY. наклейка 99.534 · 100.134 уходят в пол
       со смазом · ALL 100.200 · TO 100.400 · CHEAT наклейка 100.534 · ON 100.967 · THE 101.100
       · TEST. 101.200.
  G22  272.567-274.57 (t=0 ↔ 272.567). Не один лист, а СТОПКА из трёх цитат: задний B висит,
       A опускается с потолка 272.567→272.90 (10 кадров, чистый ease-out: 25·22·19·17·13·
       11·9·5·4·2·0 px, без перелёта), C — 272.867→273.267 (11 кадров), каждый ниже и левее
       предыдущего. Текст на листе весь сразу, узкий жирный гротеск, кап 0.12 высоты листа,
       шаг 0.21, поля слева 0.025. На полу: I JUST (с 0) · GAVE 272.800 · IT 272.967 ·
       NOTES. 273.067 (садятся сверху на 0.02 кадра за 3 кадра). После посадки камера
       медленно обходит стопку (листы влево 0.056 W/с, фон вправо).
  G45  207.500-211.950 (t=0 ↔ 207.500). Слева панель «FREE VERSION» на двух тросах, уже висит.
       Список — прямо в воздухе, без подложки, тяжёлый узкий гротеск капителью, левый край
       0.37, верх 0.335, шаг строк 0.095, кап 0.068; растёт ТОЛЬКО вниз. Пункты пословно:
       READ 207.733 · THE 208.000 · CONTRACTS 208.233 (бледное) / 208.267 · BUILT 208.833 ·
       THE 209.100 · MODEL 209.400 · WROTE 210.000 · THE 210.200 · REPORT 210.500 ·
       MADE 211.000 · THE 211.300 · SLIDES 211.600; слово встаёт на первом кадре чуть меньше,
       выше и серое, на втором садится. Галочек нет — с каждым пунктом справа на тросе
       встаёт ПРЕДМЕТ с перелётом масштаба (5 кадров): CONTRACT 208.500 · MODEL 209.600 ·
       QUARTERLY REPORT 210.600 · RESULTS 211.700. Камера: наезд +8% за кусок.
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import *
from shard_fable_a import (pop, tiles_crop, place_words, visible, line_frame, word_quad,
                           text_shadow, CAP, YEL, YEL_SIDE, DARK, DARK_SIDE)

FPS = 30
DT = 1.0 / FPS
INK = (24, 22, 24, 255)
PAPER = (244, 242, 238, 255)
MUST = (214, 176, 58, 255)        # горчичный жёлтый табло и наклеек

def out_quad(t): t = clamp01(t); return 1 - (1 - t) * (1 - t)

def sysfont(name, size, fallback="Arimo-Bold.ttf"):
    """системный DejaVu (есть на раннере), иначе наш шрифт из fonts/"""
    for p_ in (os.path.join("/usr/share/fonts/truetype/dejavu", name), os.path.join(FONTDIR, name)):
        if os.path.exists(p_):
            return ImageFont.truetype(p_, size)
    return font(fallback, size)

# ----------------------------------------------------------------- общие вещи

def hang_tex(img, cam, tex, center, w_m, yaw, t, t0, k0=1.12, dur=0.10, wires=(0.12, 0.88),
             depth=0.0, sway=0.0, opacity=1.0, shadow=True, dy=0.0):
    """повесить лист/доску в зал: входит с перелётом масштаба (первый кадр крупнее и
    прозрачнее, за ~3 кадра садится), висит на тросах; dy — сдвиг по высоте (спуск).
    Возвращает углы прямоугольника в пространстве или None, если ещё не вошёл."""
    p = pop(t0, t, dur=dur, k0=k0)
    if p is None: return None
    s, op = p
    op *= opacity
    h_m = w_m * tex.size[1] / tex.size[0]
    yw = yaw + (sway * math.sin((t - t0) * 1.3) if sway else 0.0)
    cc = (center[0], center[1] + dy, center[2])
    c = quad(cc, w_m * s, h_m * s, yaw=yw)
    if not visible(cam, c): return None
    if shadow and s < 1.04 and dy < 0.05:
        _floor_shadow_soft(img, cam, c, tex, op)
    if wires:
        for fx in wires:
            top = (c[0][0] + (c[1][0] - c[0][0]) * fx, c[0][1], c[0][2] + (c[1][2] - c[0][2]) * fx)
            wire(img, cam, top, color=(104, 106, 110, 230), width=2)
    if s > 1.06:                                   # первый кадр входа — смаз
        for sh in (-0.03, 0.03):
            c2 = quad((cc[0] + sh * w_m, cc[1], cc[2]), w_m * s, h_m * s, yaw=yw)
            paste_quad(img, tex, [cam.proj(q) for q in c2], 0.20)
    if depth > 0:
        side_faces(img, cam, c, depth, yw, op)
    paste_quad(img, tex, [cam.proj(q) for q in c], op)
    return c

def side_faces(img, cam, c, depth, yaw, op=1.0, col=(58, 58, 60), bottom=(36, 36, 38)):
    """толщина доски: видимая боковая грань и нижняя — по одному многоугольнику"""
    nz = (-math.sin(yaw), 0.0, math.cos(yaw))
    back = [(q[0] + nz[0] * depth, q[1], q[2] + nz[2] * depth) for q in c]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if cam.proj(c[0])[0] > cam.proj(back[0])[0]:
        face = (c[0], back[0], back[3], c[3])
    else:
        face = (c[1], back[1], back[2], c[2])
    d.polygon([cam.proj(q)[:2] for q in face], fill=col + (int(255 * op),))
    d.polygon([cam.proj(q)[:2] for q in (c[3], c[2], back[2], back[3])], fill=bottom + (int(255 * op),))
    img.alpha_composite(lay)

def _floor_shadow_soft(img, cam, c, tex, op):
    bl, br = c[3], c[2]
    sh = [(bl[0] + 0.35, 0.012, bl[2] + 1.1), (br[0] + 0.35, 0.012, br[2] + 1.1),
          (br[0], 0.012, br[2] + 0.15), (bl[0], 0.012, bl[2] + 0.15)]
    if not visible(cam, sh): return
    small = (max(8, tex.size[0] // 6), max(8, tex.size[1] // 6))
    a = tex.split()[3].resize(small, Image.BILINEAR).point(lambda v: int(v * 0.20 * op))
    dark = Image.new("RGBA", small, (40, 40, 44, 255)); dark.putalpha(a)
    dark = dark.filter(ImageFilter.GaussianBlur(5))
    paste_quad(img, dark, [cam.proj(p) for p in sh])

def embers_fast(img, cam, pts, t, glow=0.95):
    """те же угли, что Z.embers, но ореол считается на половинном кадре и только в своей рамке"""
    rgb, al = Z._sprite()
    hw, hh = W // 2, H // 2
    add = np.zeros((hh, hw, 3), np.float32)
    ca = np.zeros((hh, hw, 1), np.float32)
    for i, (x, y, z, s) in enumerate(pts):
        pulse = 0.82 + 0.18 * math.sin(t * 3.4 + i * 1.7)
        px, py, dz = cam.proj((x, y, z))
        if dz < 0.3: continue
        px, py = px / 2, py / 2
        size = max(6, int(s * F / dz * pulse / 2))
        if size > 700 or px < -size or px > hw + size or py < -size or py > hh + size: continue
        sp = np.array(Image.fromarray(rgb.astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32)
        sa = np.array(Image.fromarray((al * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32) / 255.0
        x0, y0 = int(px - size / 2), int(py - size / 2)
        X0, Y0 = max(0, x0), max(0, y0); X1, Y1 = min(hw, x0 + size), min(hh, y0 + size)
        if X1 <= X0 or Y1 <= Y0: continue
        sub = sp[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        suba = sa[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][..., None]
        add[Y0:Y1, X0:X1] += sub * suba * pulse * 0.55
        ca[Y0:Y1, X0:X1] = np.maximum(ca[Y0:Y1, X0:X1], np.clip(suba * 2.6 - 0.45, 0, 1))
    if ca.max() <= 0 and add.max() <= 0:
        return img
    halo_s = Image.fromarray(np.clip(add, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(23))
    m = np.asarray(halo_s.convert("L")) > 1
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return img
    X0, X1 = max(0, xs.min() * 2 - 4), min(W, xs.max() * 2 + 6)
    Y0, Y1 = max(0, ys.min() * 2 - 4), min(H, ys.max() * 2 + 6)
    bw, bh = X1 - X0, Y1 - Y0
    box_s = (X0 // 2, Y0 // 2, X0 // 2 + (bw + 1) // 2, Y0 // 2 + (bh + 1) // 2)
    halo = np.asarray(halo_s.crop(box_s).resize((bw, bh), Image.BILINEAR), np.float32)
    addf = np.asarray(Image.fromarray(np.clip(add, 0, 255).astype(np.uint8)).crop(box_s)
                      .resize((bw, bh), Image.BILINEAR), np.float32)
    caf = np.asarray(Image.fromarray((ca[..., 0] * 255).astype(np.uint8)).crop(box_s)
                     .resize((bw, bh), Image.BILINEAR), np.float32)[..., None] / 255.0
    sub = img.crop((X0, Y0, X1, Y1)).convert("RGB")
    arr = np.asarray(sub, np.float32)
    core = np.array([255.0, 182.0, 92.0], np.float32)
    arr = arr * (1 - caf) + core * caf
    arr = arr + addf * 0.5 + halo * glow
    img.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA"), (X0, Y0))
    return img

def place_words_n(img, cam, t, words, center, yaw, scale_m, starts, depth, side,
                  hang=False, shadow=False, wire_per_word=1, k0=1.22, steps=3, settle=None,
                  pale=False):
    """как place_words из части A, но объём — 3-4 копии вместо 9-48; settle=(сдвиг_м, кадры) —
    слово приходит выше и за N кадров опускается на место (плёнка 28.9, 207.7); pale —
    первый кадр серый и полупрозрачный (G45)"""
    tw, th, tiles = words
    ux, nz = line_frame(center, yaw)
    for i, (tile, cx, cy, base) in enumerate(tiles):
        p = pop(starts[i], t, k0=k0)
        if p is None: continue
        s, op = p
        w = tile.size[0] * scale_m * s; h = tile.size[1] * scale_m * s
        u = (cx - tw / 2) * scale_m
        v = (th / 2 - cy) * scale_m
        dy = 0.0
        if settle is not None:
            sm, nf = settle
            dy = sm * (1 - out_cubic(seg(t, starts[i], starts[i] + nf * DT)))
        tx = tile
        if pale and t < starts[i] + DT * 0.99:
            tx = Image.new("RGBA", tile.size, (150, 150, 152, 255)); tx.putalpha(tile.split()[3])
            op *= 0.7
        c = word_quad((center[0], center[1] + dy, center[2]), ux, u, v, w, h)
        if not visible(cam, c): continue
        if shadow:
            text_shadow(img, cam, c, tile, ux)
        if hang:
            n = wire_per_word if tile.size[0] * scale_m > 0.45 else 1
            for j in range(n):
                f = (j + 0.5) / n
                top = (c[0][0] + (c[1][0] - c[0][0]) * f, c[0][1], c[0][2] + (c[1][2] - c[0][2]) * f)
                wire(img, cam, top, color=(96, 98, 102, 230), width=2)
        if s > 1.08:
            for sh in (-0.05, 0.05):
                c2 = word_quad((center[0] + sh * w * ux[0], center[1] + dy, center[2] + sh * w * ux[2]), ux, u, v, w, h)
                paste_quad(img, tile, [cam.proj(q) for q in c2], 0.22)
        alpha = tile.split()[3]
        for k_ in range(steps, -1, -1):
            k = k_ / steps
            cs = [(q[0] + nz[0] * depth * k, q[1], q[2] + nz[2] * depth * k) for q in c]
            if k_ == 0:
                t2 = tx
            else:
                v3 = [int(side[j] * (0.78 + 0.22 * (1 - k))) for j in range(3)]
                t2 = Image.new("RGBA", tile.size, (v3[0], v3[1], v3[2], 255)); t2.putalpha(alpha)
            paste_quad(img, t2, [cam.proj(q) for q in cs], op)

def floor_words(img, cam, t, words, center, scale_m, starts, sink=None, k0=1.15, depth=0.22,
                settle=None):
    """объёмные слова, стоящие на полу (нижняя кромка на y=0); sink=(t0,t1) — уход в пол
    со смазом вниз (как 100.134 на плёнке)"""
    dy = 0.0; op = 1.0
    if sink is not None:
        u = seg(t, sink[0], sink[1])
        if u >= 1: return
        if u > 0:
            dy = -u * u * 1.2
            op = 1.0 - u * 0.6
    if settle is not None and dy == 0.0:
        sm, nf = settle
        dy = sum(sm * (1 - out_cubic(seg(t, s0, s0 + nf * DT))) for s0 in starts if t >= s0) / max(1, len(starts))
        dy = max(0.0, dy)
    place_words(img, cam, t, words, (center[0], center[1] + dy, center[2]), 0.0, scale_m, starts,
                depth=depth, side=DARK_SIDE, floor=True, shadow=(abs(dy) < 0.02), floor_clip=(dy < 0),
                extra_op=op, k0=k0)

def cell_text(d, x, y, cw, ch, s, f, fill):
    """набор по ячейкам фиксированной ширины — моноширинное табло"""
    for i, ch_ in enumerate(s):
        if ch_ == " ": continue
        b = d.textbbox((0, 0), ch_, font=f)
        ww, hh = b[2] - b[0], b[3] - b[1]
        d.text((x + i * cw + (cw - ww) / 2 - b[0], y + (ch - hh) / 2 - b[1]), ch_, font=f, fill=fill)

FLIP_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#/-"

# ----------------------------------------------------------------- G14 · табло
G14_HEAD = "WHY U.S. COMPANIES SAID THEY CUT JOBS"
G14_ROWS = ["OTHER REASONS GIVEN", "CLOSING", "COST-CUTTING", "GOVERNMENT CUTS",
            "MARKET / ECONOMIC", "RESTRUCTURING", "TARIFFS"]
G14_YEL = "ARTIFICIAL INTELLIGENCE"
# (t, позиция жёлтой строки 1..8 после хода); между ними — кадр перебора двух строк
G14_MOVES = [(0.267, 7), (0.400, 6), (0.433, 5), (0.500, 4), (0.567, 3), (0.667, 2)]
G14_TOPFLIP = 0.867     # перебор всей доски
G14_TOP = 0.900         # «#1 ARTIFICIAL / INTELLIGENCE» наверху
G14_BW, G14_BH = 3.21, 3.10          # доска, м (0.439 × 0.753 кадра на d=7.5)
G14_BX, G14_BY, G14_BZ = 1.54, 1.59, 7.5

_BOARD_BG = {}
def board_bg(w, h):
    """чёрная доска с рамкой, сеткой флапов и заголовком — один раз"""
    if (w, h) in _BOARD_BG: return _BOARD_BG[(w, h)]
    img = Image.new("RGBA", (w, h), (6, 5, 7, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(40, 37, 38, 255), width=max(3, w // 200))
    cw, x0 = w * 0.91 / 23, w * 0.045
    for r in range(11):
        y = h * (0.035 + 0.080 * r)
        for i in range(23):
            d.rectangle([x0 + i * cw + 2, y, x0 + (i + 1) * cw - 2, y + h * 0.058],
                        fill=(11, 10, 12, 255), outline=(17, 16, 18, 255))
            d.line([x0 + i * cw + 2, y + h * 0.029, x0 + (i + 1) * cw - 2, y + h * 0.029],
                   fill=(6, 5, 7, 255), width=2)
    fh = font("Oswald-Bold.ttf", int(h * 0.042))
    d.text((x0, h * 0.035), G14_HEAD, font=fh, fill=(196, 192, 194, 255))
    glare = Image.new("RGBA", (w // 8, h // 8), (0, 0, 0, 0))
    ImageDraw.Draw(glare).rectangle([0, 0, w // 8, int(h * 0.20) // 8], fill=(255, 255, 255, 16))
    img.alpha_composite(glare.filter(ImageFilter.GaussianBlur(5)).resize((w, h), Image.BILINEAR))
    _BOARD_BG[(w, h)] = img
    return img

def board_tex(t, w=1100, h=1060):
    """табло в момент t: строки в ячейках, перебор = мусор в двух строках на 1 кадр"""
    img = board_bg(w, h).copy()
    d = ImageDraw.Draw(img)
    cw, x0 = w * 0.91 / 23, w * 0.045
    ch = h * 0.058
    f = sysfont("DejaVuSansMono-Bold.ttf", int(h * 0.050), "Oswald-Bold.ttf")
    fp = font("Oswald-Bold.ttf", int(h * 0.050))
    WH, YL = (206, 202, 204, 255), (214, 176, 58, 255)
    def row_y(r): return h * (0.035 + 0.080 * (r + 2))        # r = 1..8
    pos = 8
    flip = set()
    for (tm, p_) in G14_MOVES:
        if t >= tm: pos = p_
        if tm - DT * 0.99 <= t < tm: flip |= {p_, p_ + 1}       # кадр перед ходом — мусор
    top_mode = t >= G14_TOP
    all_flip = G14_TOPFLIP <= t < G14_TOP
    rng = np.random.default_rng(int(round(t * FPS)))
    order = list(G14_ROWS)
    if top_mode:
        rows = [(r + 1, s, False) for r, s in enumerate(order)]       # список ушёл на строку вверх
    else:
        order.insert(pos - 1, G14_YEL)
        rows = [(r + 1, s, s == G14_YEL) for r, s in enumerate(order)]
    for (r, s, yel) in rows:
        y = row_y(r)
        if r in flip or (all_flip and r >= 2):
            # мусор: случайные знаки, половинки, жёлтое с белым вперемешку
            for i in range(23):
                if rng.uniform() < 0.25: continue
                c1 = FLIP_CHARS[rng.integers(len(FLIP_CHARS))]
                col = YL if rng.uniform() < 0.5 else WH
                cell_text(d, x0 + i * cw, y, cw, ch, c1, f, col)
                if rng.uniform() < 0.6:
                    c2 = FLIP_CHARS[rng.integers(len(FLIP_CHARS))]
                    half = Image.new("RGBA", (int(cw), int(ch / 2)), (6, 5, 7, 255))
                    cell_text(ImageDraw.Draw(half), 0, -ch / 2 if rng.uniform() < 0.5 else 0, cw, ch, c2, f,
                              YL if rng.uniform() < 0.5 else WH)
                    img.alpha_composite(half, (int(x0 + i * cw), int(y + (ch / 2 if rng.uniform() < 0.5 else 0))))
            continue
        if r == 1:
            d.text((x0, y + ch * 0.08), s, font=fp, fill=WH)        # пропорциональный заголовок списка
        else:
            cell_text(d, x0, y, cw, ch, s, f, YL if yel else WH)
    if top_mode and not all_flip:
        # крупный блок ×1.65 в двух пустых рядах под заголовком
        fb = sysfont("DejaVuSansMono-Bold.ttf", int(h * 0.050 * 1.65), "Oswald-Bold.ttf")
        cwb, chb = cw * 1.65, ch * 1.65
        y1, y2 = row_y(-1) - ch * 0.15, row_y(0) - ch * 0.05
        fn = sysfont("DejaVuSansMono-Bold.ttf", int(h * 0.13), "Oswald-Bold.ttf")
        d.text((x0, y1 - ch * 0.05), "#1", font=fn, fill=YL)
        cell_text(d, x0 + cwb * 2.4, y1, cwb, chb, "ARTIFICIAL", fb, YL)
        cell_text(d, x0 + cwb * 2.4, y2, cwb, chb, "INTELLIGENCE", fb, YL)
    return img

_G14W = {}
def _g14_words():
    if not _G14W:
        _G14W["ai"] = tiles_crop(["AI"], 200, hl={0}, color=DARK, cond=0.66)
        _G14W["was"] = tiles_crop(["WAS"], 200, color=DARK, cond=0.66)
        _G14W["l2"] = tiles_crop(["THE NUMBER"], 200, color=DARK, cond=0.66)
        _G14W["one"] = tiles_crop(["ONE"], 200, hl={0}, color=DARK, cond=0.66)
        _G14W["reason"] = tiles_crop(["REASON"], 200, color=DARK, cond=0.66)
    return _G14W

def g14(t):
    # чистый наезд: ширина доски +11% за 1.67 с → d 7.5 → 6.75, дальше тот же ход
    cam = Cam(0.0, 1.55, 0.45 * t, 0.0)
    img = room(cam)
    tex = board_tex(t)
    hang_tex(img, cam, tex, (G14_BX, G14_BY, G14_BZ), G14_BW, 0.0, t, -1.0, k0=1.0,
             wires=(0.14, 0.83), depth=0.08, sway=0.0)
    wd = _g14_words()
    Zt = 7.0
    big = 0.51 / (CAP * 200); small = 0.33 / (CAP * 200)
    # строка 1: AI на наклейке (с нуля, досаживается вниз 0.028 кадра за 3 к.), WAS 29.067
    place_words_n(img, cam, t, wd["ai"], (-2.66, 2.43, Zt), 0.0, big, [-1.0], depth=0.06,
                  side=DARK_SIDE, hang=True, k0=1.0, settle=(0.11, 3) if t < 0.2 else None)
    place_words_n(img, cam, t, wd["was"], (-1.66, 2.43, Zt), 0.0, big, [0.200], depth=0.06,
                  side=DARK_SIDE, hang=True, wire_per_word=2, k0=1.03)
    # строка 2: THE 29.267 (осадка), NUMBER 29.333 (перелёт 17%, 1 кадр)
    place_words_n(img, cam, t, wd["l2"], (-1.82, 1.74, Zt), 0.0, small, [0.400, 0.467], depth=0.05,
                  side=DARK_SIDE, hang=True, k0=1.17, settle=(0.10, 2))
    # строка 3: ONE на наклейке 29.767 (растёт 85→100%), REASON 29.967
    place_words_n(img, cam, t, wd["one"], (-2.75, 1.32, Zt), 0.0, small, [0.900], depth=0.05,
                  side=DARK_SIDE, hang=True, k0=0.85)
    place_words_n(img, cam, t, wd["reason"], (-1.57, 1.32, Zt), 0.0, small, [1.100], depth=0.05,
                  side=DARK_SIDE, hang=True, k0=1.03, settle=(0.04, 2))
    if t >= 0.167:
        source_line(img, "SOURCE: OUTPLACEMENT SURVEY · 2026")
    return img

# ----------------------------------------------------------------- G19 · статья
G19_HEAD = ["Lab says its AI models secretly",
            "broke out of a secure test environment",
            "and hacked into a partner company's",
            "servers in order to cheat on an evaluation"]
# мазки маркера: (строка, слово с, слово по, t старта, t конца)
G19_STROKES = [(2, 1, 99, 0.533, 0.667), (3, 0, 3, 0.633, 0.800), (3, 3, 99, 1.600, 1.833)]
G19_D = 6.0
G19_W, G19_H = 3.05, 2.03        # лист 3:2, высота 0.61 кадра на d=6
G19_CX = 0.75

_ART = {}
def article_bg(w, h):
    """лист без маркера и заголовка — рисуется один раз"""
    if (w, h) in _ART: return _ART[(w, h)]
    img = Image.new("RGBA", (w, h), (252, 250, 247, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(216, 214, 208, 255), width=2)
    for i in range(3):
        d.rectangle([44, int(h * 0.11) + i * 10, 72, int(h * 0.11) + i * 10 + 3], fill=(50, 50, 52, 255))
    d.text((92, int(h * 0.085)), "THE LEDGER", font=font("ArialBlack.ttf", int(h * 0.075)), fill=(24, 24, 26, 255))
    px0, py0 = w - 200, int(h * 0.09)
    d.rounded_rectangle([px0, py0, w - 44, py0 + int(h * 0.085)], radius=int(h * 0.045), fill=(212, 39, 38, 255))
    d.text((px0 + 26, py0 + int(h * 0.018)), "Subscribe", font=font("Arimo-Bold.ttf", int(h * 0.045)), fill=(255, 255, 255, 255))
    d.line([44, int(h * 0.24), w - 44, int(h * 0.24)], fill=(226, 224, 218, 255), width=2)
    d.text((44, int(h * 0.31)), "↗ Trending", font=font("Arimo-Bold.ttf", int(h * 0.040)), fill=(40, 40, 42, 255))
    d.text((240, int(h * 0.31)), "Just plain math: Social Security is six years from a cliff, and",
           font=font("Arimo-Bold.ttf", int(h * 0.036)), fill=(150, 150, 154, 255))
    d.text((44, int(h * 0.50)), "C Y B E R S E C U R I T Y", font=font("Arimo-Bold.ttf", int(h * 0.034)), fill=(110, 110, 114, 255))
    d.ellipse([int(w * 0.43), int(h * 0.515), int(w * 0.43) + 8, int(h * 0.515) + 8], fill=(212, 39, 38, 255))
    d.text((int(w * 0.455), int(h * 0.50)), "A I   L A B S", font=font("Arimo-Bold.ttf", int(h * 0.034)), fill=(110, 110, 114, 255))
    _ART[(w, h)] = img
    return img

def article_tex(t, w=1200, h=800):
    """лист: маркер растёт слева направо по мазкам (ПОД буквами), заголовок серифом"""
    img = article_bg(w, h).copy()
    d = ImageDraw.Draw(img)
    f = sysfont("DejaVuSerif-Bold.ttf", int(h * 0.062))
    ys = [int(h * 0.61), int(h * 0.70), int(h * 0.79), int(h * 0.88)]
    sp = d.textlength(" ", font=f)
    words = []
    for li, ln in enumerate(G19_HEAD):
        x = 50; row = []
        for wd in ln.split(" "):
            tw = d.textlength(wd, font=f)
            row.append((x, x + tw)); x += tw + sp
        words.append(row)
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    drawn = False
    for (li, a, b, t0, t1) in G19_STROKES:
        k = seg(t, t0, t1)
        if k <= 0: continue
        row = words[li]
        x0 = row[a][0] - 8; x1 = row[min(b, len(row)) - 1][1] + 8
        xe = x0 + (x1 - x0) * k
        y0 = ys[li] - int(h * 0.006); y1 = ys[li] + int(h * 0.078)
        ld.rectangle([x0, y0, xe, y1], fill=(255, 232, 110, 235))
        if k < 1:
            ld.ellipse([xe - 10, y0, xe + 10, y1], fill=(255, 232, 110, 235))
        drawn = True
    if drawn:
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
    for li, ln in enumerate(G19_HEAD):
        d.text((50, ys[li]), ln, font=f, fill=(28, 26, 30, 255))
    return img

_G19W = {}
def _g19_words():
    if not _G19W:
        _G19W["a"] = tiles_crop(["A REAL"], 200, color=DARK, vertical=True, cond=0.70)
        _G19W["b"] = tiles_crop(["COMPANY."], 200, hl={0}, color=DARK, vertical=True, cond=0.70)
        _G19W["c"] = tiles_crop(["ALL TO CHEAT"], 200, hl={2}, color=DARK, vertical=True, cond=0.70)
        _G19W["d"] = tiles_crop(["ON THE TEST."], 200, color=DARK, vertical=True, cond=0.70)
    return _G19W

def g19(t):
    # лист на экране стоит, а камера уходит вправо на 0.9 м и доворачивает влево:
    # правый край листа ближе (18°) → фронтально, угли (ближе листа) уезжают влево
    k = seg(t, 0.0, 3.4)
    cam = Cam(G19_CX - 0.2 + 0.9 * k, 1.55, 0.0, math.radians(5.3 + 8.6 * k))
    img = room(cam)
    pts = cluster(G19_CX - 1.0, 1.50, 2.6, 0.40, n=6, seed=19, mirror=False)
    pts += [(G19_CX - 1.25, 1.05, 2.8, 0.34), (G19_CX - 0.8, 1.25, 2.4, 0.30)]
    img = embers_fast(img, cam, pts, t, glow=1.0)
    wd = _g19_words()
    sc1 = 0.56 / (CAP * 200); sc2 = 0.47 / (CAP * 200)
    floor_words(img, cam, t, wd["a"], (0.85, 0.0, 9.7), sc1, [-1.0, -1.0], sink=(1.034, 1.10))
    floor_words(img, cam, t, wd["b"], (0.95, 0.0, 6.8), sc2, [0.434], sink=(1.034, 1.10), k0=1.0)
    floor_words(img, cam, t, wd["c"], (0.85, 0.0, 9.7), sc1, [1.100, 1.300, 1.434])
    floor_words(img, cam, t, wd["d"], (0.95, 0.0, 6.8), sc2, [1.867, 2.000, 2.100], k0=1.0)
    tex = article_tex(t)
    hang_tex(img, cam, tex, (G19_CX, 2.0, G19_D), G19_W, math.radians(-18 * (1 - k)), t, -1.0,
             k0=1.0, wires=(0.03, 0.97), depth=0.0, sway=0.0)
    return img

# ----------------------------------------------------------------- G22 · стопка цитат
# лист: (строки, дальность, центр X, центр Y посадки, ширина, высота, t старта, длительность, ход)
G22_SHEETS = [
    (["I would love to see", "the bar go above", "Sweden, Denmark, and", "all the other ones."],
     6.5, 0.38, 2.50, 2.28, 1.46, -1.0, 0.33, 0.0),
    (["“You have a tendency", "to add more when", "less is sometimes", "better.”"],
     5.8, -0.14, 1.93, 2.09, 1.27, 0.0, 0.333, 1.12),
    (["“These all suck.", "They're slow, they're", "boring, they don't", "grip me.”"],
     5.0, -0.05, 1.56, 2.05, 1.07, 0.300, 0.367, 1.03),
]
G22_FLOOR = [("I JUST", -1.0), ("GAVE", 0.233), ("IT", 0.400), ("NOTES.", 0.500)]

_QT = {}
def quote_tex(lines, w_m, h_m, px=900):
    key = tuple(lines)
    if key in _QT: return _QT[key]
    w = px; h = int(px * h_m / w_m)
    img = Image.new("RGBA", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    f = font("Oswald-Bold.ttf", int(h * 0.12 / 0.72))          # кап 0.12 высоты листа
    y = h * 0.13 - int(h * 0.12 / 0.72) * 0.18
    for ln in lines:
        d.text((w * 0.03, y), ln, font=f, fill=(18, 16, 15, 255))
        y += h * 0.21
    _QT[key] = img
    return img

_G22W = {}
def _g22_words():
    if not _G22W:
        _G22W["w"] = tiles_crop(["I JUST GAVE IT NOTES."], 200, color=DARK, vertical=True, cond=0.70)
    return _G22W

def g22(t):
    # после посадки стопки камера медленно обходит её: вправо и доворот влево
    k = seg(t, 0.7, 4.5)
    cam = Cam(0.35 * k, 1.55, 0.0, math.radians(-2.2 * k))
    img = room(cam)
    wd = _g22_words()
    # на полу за стопкой: кап 0.25 м на d≈7.6, слова садятся сверху на 0.02 кадра за 3 кадра
    starts = [-1.0, -1.0, 0.233, 0.400, 0.500]
    floor_words(img, cam, t, wd["w"], (0.05, 0.0, 7.6), 0.225 / (CAP * 200), starts, k0=1.0,
                depth=0.16, settle=(0.08, 3))
    # стопка: задний лист висит, A и C опускаются с ease-out без перелёта
    for (lines, d_, cx, cy, wm, hm, t0, dur, travel) in G22_SHEETS:
        if t < t0: continue
        u = out_quad(seg(t, t0, t0 + dur))
        dy = travel * (1 - u)
        tex = quote_tex(lines, wm, hm)
        c = hang_tex(img, cam, tex, (cx, cy, d_), wm, math.radians(2.5), t, -1.0, k0=1.0,
                     wires=(0.07, 0.93), dy=dy, shadow=(dy < 0.02))
        if c is not None and dy < 0.02:
            # мягкая тень стопки на лист сзади — тёмная полоса у нижней кромки
            pass
    return img

# ----------------------------------------------------------------- G45 · чек-лист
G45_ITEMS = [[("READ", 0.233), ("THE", 0.500), ("CONTRACTS", 0.733)],
             [("BUILT", 1.333), ("THE", 1.600), ("MODEL", 1.900)],
             [("WROTE", 2.500), ("THE", 2.700), ("REPORT", 3.000)],
             [("MADE", 3.500), ("THE", 3.800), ("SLIDES", 4.100)]]
G45_CARDS = [("contract", 1.000), ("model", 2.100), ("report", 3.100), ("results", 4.200)]

_G45T = {}
def panel_tex(w=640, h=990):
    if "panel" in _G45T: return _G45T["panel"]
    img = Image.new("RGBA", (w, h), (248, 247, 245, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(200, 200, 198, 255), width=2)
    d.rectangle([0, 0, w, int(h * 0.11)], fill=(26, 26, 28, 255))
    d.text((34, int(h * 0.03)), "FREE VERSION", font=font("ArialBlack.ttf", int(h * 0.045)), fill=(246, 246, 246, 255))
    d.rounded_rectangle([34, int(h * 0.17), w - 34, int(h * 0.30)], radius=18, fill=(226, 226, 224, 255))
    d.text((56, int(h * 0.205)), "Can you do my", font=font("Arimo-Bold.ttf", int(h * 0.036)), fill=(50, 50, 52, 255))
    d.text((56, int(h * 0.245)), "quarterly report?", font=font("Arimo-Bold.ttf", int(h * 0.036)), fill=(50, 50, 52, 255))
    d.text((34, int(h * 0.36)), "Here are", font=font("ArialBlack.ttf", int(h * 0.075)), fill=(28, 28, 30, 255))
    d.text((34, int(h * 0.44)), "some tips...", font=font("ArialBlack.ttf", int(h * 0.075)), fill=(28, 28, 30, 255))
    for i in range(9):
        d.line([34, int(h * 0.58) + i * int(h * 0.036), w - 34 - (i % 3) * 90, int(h * 0.58) + i * int(h * 0.036)],
               fill=(208, 208, 206, 255), width=7)
    _G45T["panel"] = img
    return img

def card_tex(kind, w=600, h=250):
    if kind in _G45T: return _G45T[kind]
    if kind in ("report", "results"):
        img = Image.new("RGBA", (w, h), (22, 22, 24, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w - 1, h - 1], outline=(70, 70, 72, 255), width=3)
        if kind == "report":
            d.text((36, 36), "QUARTERLY", font=font("ArialBlack.ttf", 52), fill=(240, 240, 240, 255))
            d.text((36, 102), "REPORT", font=font("ArialBlack.ttf", 52), fill=(240, 240, 240, 255))
            d.rectangle([36, 184, 260, 194], fill=MUST)
            d.text((36, 206), "Q3 · 2026", font=font("Arimo-Bold.ttf", 26), fill=(170, 170, 172, 255))
        else:
            d.text((36, 24), "RESULTS", font=font("ArialBlack.ttf", 44), fill=(240, 240, 240, 255))
            for i, hh in enumerate((0.35, 0.55, 0.45, 0.8, 1.0)):
                x = 56 + i * 100
                d.rectangle([x, 222 - 130 * hh, x + 60, 222], fill=MUST if i == 4 else (150, 150, 152, 255))
    else:
        img = Image.new("RGBA", (w, h), (248, 247, 245, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w - 1, h - 1], outline=(200, 200, 198, 255), width=2)
        if kind == "contract":
            d.text((36, 20), "CONTRACT", font=font("ArialBlack.ttf", 40), fill=(30, 30, 32, 255))
            for i in range(6):
                y = 86 + i * 27
                if i in (2, 3, 6):
                    d.rectangle([40, y - 4, w - 60 - (i % 2) * 60, y + 14], fill=MUST)
                d.line([40, y + 5, w - 60 - (i % 3) * 70, y + 5], fill=(120, 120, 122, 255), width=6)
        else:   # model — таблица с жёлтым столбцом
            d.text((36, 18), "MODEL", font=font("ArialBlack.ttf", 40), fill=(30, 30, 32, 255))
            cols, rows = 5, 5
            x0, y0, cw, rh = 36, 80, (w - 72) / cols, 32
            d.rectangle([x0 + cw * 3, y0, x0 + cw * 4, y0 + rh * rows], fill=MUST)
            for r in range(rows + 1):
                d.line([x0, y0 + r * rh, w - 40, y0 + r * rh], fill=(150, 150, 152, 255), width=2)
            for c in range(cols + 1):
                d.line([x0 + c * cw, y0, x0 + c * cw, y0 + rh * rows], fill=(150, 150, 152, 255), width=2)
            fs = font("Arimo-Bold.ttf", 17)
            for r in range(rows):
                for c in range(cols):
                    d.text((x0 + c * cw + 10, y0 + r * rh + 7), f"{(r * 7 + c * 13) % 97}.{(r + c) % 10}", font=fs,
                           fill=(60, 60, 62, 255))
    _G45T[kind] = img
    return img

_G45W = {}
def _g45_words():
    if not _G45W:
        for i, row in enumerate(G45_ITEMS):
            _G45W[i] = tiles_crop([" ".join(w for w, _ in row)], 200, color=(43, 43, 43, 255), cond=0.66)
    return _G45W

def g45(t):
    # очень медленный наезд (+8% за кусок) со сносом влево-вниз
    cam = Cam(-0.03 * t, 1.55 - 0.02 * t, 0.10 * t, 0.0)
    img = room(cam)
    # левая панель-повод, уже висит: x 0.03-0.31, y 0.11-0.88 на d=6
    hang_tex(img, cam, panel_tex(), (-1.93, 1.57, 6.0), 1.64, math.radians(8), t, -1.0, k0=1.0,
             wires=(0.15, 0.85))
    # список в воздухе: левый край X=-0.82, верх первой строки 2.14, шаг 0.34, кап 0.24 на d=6.5
    wd = _g45_words()
    sc = 0.24 / (CAP * 200)
    for i, row in enumerate(G45_ITEMS):
        tw, th, tiles = wd[i]
        wm = tw * sc
        cy = 2.14 - 0.24 * 0.5 - 0.34 * i
        place_words_n(img, cam, t, wd[i], (-0.82 + wm / 2, cy, 6.5), 0.0, sc, [t0 for _, t0 in row],
                      depth=0.0, side=DARK_SIDE, k0=0.94, settle=(-0.05, 1), pale=True, steps=1)
    # справа карточки-предметы на тросах, с перелётом масштаба 5 кадров
    for i, (kind, t0) in enumerate(G45_CARDS):
        cy = 2.62 - 0.69 * i
        hang_tex(img, cam, card_tex(kind), (1.84, cy, 6.0), 1.5, math.radians(-10), t, t0,
                 k0=1.18, dur=0.167, wires=(0.12, 0.88))
    source_line(img, "ILLUSTRATION")
    return img

SCENES = {"G14": (g14, 4.5), "G19": (g19, 4.5), "G22": (g22, 4.5), "G45": (g45, 4.5)}

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
