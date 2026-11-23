#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Фильм «Верица» — блок 0 «ХУК», сцены 01-08 (первая минута, 73,5 с).

Правила: план ≤5 с (карта и отрисовка — исключение), движение с первого кадра,
без субтитров, текст в полях 96/54, подписи честные (место · дата · источник),
стиль темнее Киссинджера, доска расследования — сквозной образ.
Паузы по тексту — вставки в начало сцены (timing.py). Времена фраз — секунды
озвучки golos.mp3 по тишинам (silencedetect), переводятся в секунды сцены rel().
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import fx
import karta as K
from core import W, H, SS

SCENES = {}
SAFE_X, SAFE_Y = 96, 54


def scene(sid):
    def deco(fn):
        SCENES[sid] = fn
        return fn
    return deco


def rel(sid, v):
    """секунда озвучки → секунда сцены (с учётом вставки в начале)"""
    s = C.scene_info(sid)
    return v - s["voice_start"] + s["insert"]


def shots(t, lst, dur):
    for i, (t0, fn) in enumerate(lst):
        t1 = lst[i + 1][0] if i + 1 < len(lst) else dur
        if t < t1 or i == len(lst) - 1:
            return fn, max(0.0, t - t0), max(0.2, t1 - t0)
    return lst[-1][1], 0.0, 1.0


def flash(img, tt, d=0.1, a=0.6):
    if tt >= d:
        return img
    return Image.blend(img.convert("RGB"), Image.new("RGB", img.size, C.WHITE), a * (1 - tt / d))


def fit_px(text, kind, px, maxw, track=0.0):
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    while px > 20 and C.text_w(d, text, C.font(kind, px * SS), track) / SS > maxw:
        px -= 4
    return px


def word(text, k, y, px=160, kind="head", color=C.WHITE, track=0.06, x=W / 2, anchor="ms", rise=40, maxw=W - 2 * SAFE_X):
    if k <= 0:
        return None
    px = fit_px(text, kind, px, maxw, track)
    kk = C.out_cubic(k)
    return C.text_layer([text], kind, px, color, x, y + (1 - kk) * rise, anchor, track, a=C.clamp(k * 2))


def red_line(k, x0, x1, y, w=5, a=255):
    if k <= 0:
        return None
    im = C.layer()
    ImageDraw.Draw(im).rectangle([x0 * SS, y * SS, (x0 + (x1 - x0) * C.out_cubic(k)) * SS, (y + w) * SS], fill=C.RED + (a,))
    return C.done(im)


def zoom_at(img, z, cx, cy):
    """наезд z на точку (cx, cy) кадра"""
    if z <= 1.0:
        return img
    w, h = img.size
    cw, ch = w / z, h / z
    x0 = min(max(0, cx - cw / 2), w - cw)
    y0 = min(max(0, cy - ch / 2), h - ch)
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.LANCZOS)


def grade(fr, k=1.0):
    """тёмный строй видео: цвет приглушён, тени провалены, холодный оттенок в тенях"""
    a = np.asarray(fr.convert("RGB"), np.float32) / 255.0
    lum = a.mean(axis=2, keepdims=True)
    a = a * (1 - 0.38 * k) + lum * 0.38 * k
    a = np.clip((a - 0.06 * k) * (1 + 0.18 * k), 0, 1)
    a = a ** (1 + 0.22 * k)
    a[:, :, 2] += 0.025 * k * (1 - lum[:, :, 0])[:, :, None][:, :, 0]
    a[:, :, 0] *= 1 - 0.03 * k
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), "RGB")


_v = {}


def vid(key, name, start=0.0, **kw):
    if key not in _v:
        _v[key] = C.Vid(name, start, **kw)
    return _v[key]


def verica(key, name, tt, zoom=2.0, cx=0.47, cy=0.28, push=0.08, hand=3.0, k_grade=1.0):
    """врезка Верицы: зум на лицо (срезает бегущую строку и значок канала), наезд, лёгкая рука"""
    fr = vid(key, name, 0.0, zoom=zoom, cx=cx, cy=cy).at(tt)
    hx, hy = fx.handheld(tt, hand, hash(key) % 7)
    z = 1.0 + push * tt
    img = zoom_at(fr, z, W / 2 + hx, H / 2 + hy)
    return grade(img, k_grade)


CAP_V = ("Верица Обренович", "Белград · интервью 21.04.2019", "METANOJA TV")
CAP_B = ("balkanprophecies.blogspot.com", "запись 25.05.2016", "копия веб-архива 08.07.2018")


# ═════════════════════════ страница блога ═════════════════════════
_pg = {}
# рамки строк на полной странице (пиксели blog_full.png, промерено 23.11)
LINE_PUTIN = (677, 6753, 932, 6765)
LINE_DAUGHTERS = (626, 7031, 987, 7043)


def page():
    if "p" not in _pg:
        _pg["p"] = Image.open(C.apath("blog_full.png")).convert("RGB")
    return _pg["p"]


def page_view(yc, scale, xc=860.0, hide=()):
    """окно страницы: центр (xc, yc) в пикселях страницы, масштаб scale; hide — рамки, закрашенные белым"""
    p = page()
    pw, ph = p.size
    cw, ch = W / scale, H / scale
    x0 = min(max(0, xc - cw / 2), pw - cw)
    y0 = min(max(0, yc - ch / 2), ph - ch)
    crop = p.crop((int(x0), int(y0), int(x0 + cw) + 1, int(y0 + ch) + 1))
    if hide:
        d = ImageDraw.Draw(crop)
        for (a, b, c, e) in hide:
            d.rectangle([a - x0 - 6, b - y0 - 5, c - x0 + 6, e - y0 + 5], fill=(255, 255, 255))
    return crop.resize((W, H), Image.LANCZOS), (x0, y0, scale)


def to_frame(box, geo):
    x0, y0, s = geo
    return ((box[0] - x0) * s, (box[1] - y0) * s, (box[2] - x0) * s, (box[3] - y0) * s)


def page_dark(img, t, k=1.0):
    """страница в темноте: холодная, зерно, виньетка — читается только под фонарём"""
    a = np.asarray(img, np.float32)
    a *= 0.92
    a[:, :, 0] *= 0.93
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    return C.grain(img, t, 0.03)


def addr_bar(t, k_type, k_enter=0.0):
    """чёрный экран, строка адреса веб-архива, адрес печатается, курсор мигает"""
    img = Image.new("RGB", (W, H), (4, 4, 5))
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    bw, bh = 1500, 84
    bx, by = (W - bw) / 2, H * 0.45 - bh / 2
    d.rounded_rectangle([bx * SS, by * SS, (bx + bw) * SS, (by + bh) * SS], radius=10 * SS,
                        fill=(20, 20, 24, 255), outline=(70, 70, 76, 255), width=2 * SS)
    url = "web.archive.org/web/20180708195913/http://balkanprophecies.blogspot.com/"
    n = int(len(url) * C.clamp(k_type))
    f = C.font("head_l", 34 * SS)
    C.tracked(d, (bx + 28) * SS, (by + 54) * SS, url[:n], f, (215, 215, 210, 255), 0.02)
    tw = C.text_w(d, url[:n], f, 0.02) / SS
    f2 = C.font("head_l", 24 * SS)
    C.tracked(d, bx * SS, (by - 22) * SS, "ВЕБ-АРХИВ · КОПИЯ СТРАНИЦЫ ОТ 8 ИЮЛЯ 2018", f2, C.GREY + (255,), 0.3)
    out = C.over(img, C.done(lay))
    cur = fx.cursor(bx + 30 + tw, by + 60, 40, t if (k_type <= 0 or k_type >= 1) else 0.0, 3, 1.0, (215, 215, 210))
    out = C.over(out, cur).convert("RGB")
    if k_enter > 0:
        out = Image.blend(out, Image.new("RGB", (W, H), (230, 228, 224)), C.clamp(k_enter))
    return C.grain(out, t, 0.04)


# ═════════════════════════ 01 · курсор, блог, дата ═════════════════════════
@scene("01")
def s01(t, dur):
    c_blog = rel("01", 3.09)     # «В маленьком блоге…»
    c_line = rel("01", 6.83)     # «Одна строка.»
    T_SCROLL = 2.6

    def a_cursor(tt, d):
        return addr_bar(tt, C.seg(tt, 0.55, 1.95), C.seg(tt, d - 0.12, d))

    def b_scroll(tt, d):
        k = C.smoother(tt / d)
        yc = C.lerp(700, 5900, k)
        sc = C.lerp(1.35, 1.6, k)
        # скорость для размытия движения
        k2 = C.smoother(min(1.0, (tt + 1 / 60.0) / d))
        vy = (C.lerp(700, 5900, k2) - yc) * 60.0 * sc

        def crop(y):
            return page_view(y, sc)[0]
        img = fx.scroll_blur(crop, yc, vy, n=5)
        img = fx.fonar(img, W / 2 + 60 * math.sin(tt * 2), H * 0.5, 560, 380, 0.10, 0.06, t)
        return flash(page_dark(img, t), tt, 0.12, 0.9)

    def c_post(tt, d):
        sc = 1.6 + 0.07 * tt
        img, geo = page_view(5900 + 24 * tt, sc, 860)
        fy = H * 0.5 - 140 + 120 * C.smoother(C.seg(tt, 0.2, 1.4))
        img = fx.fonar(img, W * 0.42, fy, 640, 330, 0.10, 0.04, t)
        img = page_dark(img, t)
        return C.over(img, K.date_tag("25 МАЯ 2016", C.seg(tt, 0.25, 0.8), sub="запись в блоге"),
                      C.caption(*CAP_B, k=C.seg(tt, 0.5, 1.1)))

    def d_line(tt, d):
        sc = 2.4 + 0.05 * tt
        img, geo = page_view(6759, sc, 805, hide=(LINE_PUTIN,))
        box = to_frame(LINE_PUTIN, geo)
        img = fx.fonar(img, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, 560, 300, 0.10, 0.05, t)
        img = page_dark(img, t)
        # тонкая красная рамка вокруг пустого места — «одна строка»
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        k = C.out_cubic(C.seg(tt, 0.05, 0.6))
        x0, y0, x1, y1 = box[0] - 26, box[1] - 18, box[2] + 26, box[3] + 18
        per = 2 * ((x1 - x0) + (y1 - y0))
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        left = per * k
        poly = [pts[0]]
        for i in range(4):
            seg_len = abs(pts[i + 1][0] - pts[i][0]) + abs(pts[i + 1][1] - pts[i][1])
            if left <= 0:
                break
            f = min(1.0, left / seg_len)
            poly.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f))
            left -= seg_len
        if len(poly) > 1:
            dd.line([(x * SS, y * SS) for x, y in poly], fill=C.RED + (255,), width=3 * SS)
        return C.over(img, C.done(lay), C.caption(*CAP_B, k=1.0)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_cursor), (T_SCROLL, b_scroll), (5.0, c_post), (c_line, d_line)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 02 · строка проявляется ═════════════════════════
@scene("02")
def s02(t, dur):
    c_say = rel("02", 8.38)
    sc = 2.4 + 0.045 * t
    base, geo = page_view(6759, sc, 805, hide=(LINE_PUTIN,))
    true, _ = page_view(6759, sc, 805)
    box = to_frame(LINE_PUTIN, geo)
    img = fx.proyavka(base, true, (box[0] - 30, box[1] - 22, box[2] + 30, box[3] + 22), C.seg(t, 0.0, 1.35), seed=5)
    img = fx.fonar(img, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 40, 600, 320, 0.10, 0.05, t)
    img = page_dark(img, t)
    k_tr = C.seg(t, c_say, c_say + 2.1)
    lays = [red_line(C.seg(t, 1.25, 1.8), box[0] - 8, box[2] + 8, box[3] + 12, 4),
            C.caption(*CAP_B, k=1.0)]
    if k_tr > 0:
        lays.append(C.text_layer(["ПЕРЕВОД"], "head_l", 24, C.GREY, SAFE_X, H - 270, "ls", 0.3, a=C.clamp(k_tr * 3)))
        lays.append(fx.typed("«Путин будет пожизненным президентом России»", k_tr, "head_r", 48, C.WHITE, SAFE_X, H - 214, 0.02, True, t))
    return C.finish(C.over(img, *lays), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 03 · четыре года, перепись, обнуление ═════════════════════════
_bg = {}


def dark_bg(seed=7):
    if seed not in _bg:
        p = C.paper(W, H, seed=seed, tone=(30, 28, 30), dark=0.0).filter(ImageFilter.GaussianBlur(1.2))
        _bg[seed] = C.vignette(p, 0.5)
    return _bg[seed]


@scene("03")
def s03(t, dur):
    c_4 = rel("03", 11.17)      # «Через четыре года»
    c_k = rel("03", 12.25)      # «Конституцию»
    c_p = rel("03", 12.95)      # «перепишут»
    c_0 = rel("03", 13.75)      # «И его сроки обнулят»

    def a_years(tt, d):
        img = C.kb(dark_bg(7), tt / d, 0.05, 0.5, 0.5)
        k = C.seg(tt, c_4 + 0.15, c_4 + 1.0)
        num = fx.flip_number(["2016", "2017", "2018", "2019", "2020"], k, W / 2, H * 0.5, 300)
        lays = [num, C.text_layer(["ЧЕРЕЗ ЧЕТЫРЕ ГОДА"], "head_l", 40, C.GREY, W / 2, H * 0.5 - 250, "ms", 0.36,
                                  a=C.seg(tt, c_4, c_4 + 0.4))]
        if k >= 1:
            lays.append(C.text_layer(["2020"], "head", 300, C.RED, W / 2, H * 0.5 + 300 * 0.36, "ms", 0.02,
                                     a=C.seg(tt, c_4 + 1.0, c_4 + 1.35)))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    def b_konst(tt, d):
        img = C.kb(dark_bg(8), tt / d, 0.06, 0.5, 0.5)
        tk = c_p - c_k
        g = C.seg(tt, tk, tk + 0.18) * (1 - C.seg(tt, tk + 0.18, tt and tk + 0.5))
        px = fit_px("КОНСТИТУЦИЯ", "head", 190, W - 2 * SAFE_X, 0.08)
        lay = word("КОНСТИТУЦИЯ", C.seg(tt, 0.0, 0.45), H * 0.5 + px * 0.36, px, "head", C.WHITE, 0.08)
        img = C.over(img, lay).convert("RGB")
        if g > 0:
            img = fx.glitch(img, g, seed=3 + int(tt * 30), slices=18, shift=160, rgb=22)
        after = C.seg(tt, tk + 0.3, tk + 0.6)
        if after > 0:
            # переписана: красная копия ложится поверх со сдвигом
            red = C.text_layer(["КОНСТИТУЦИЯ"], "head", px, C.RED, W / 2 + 9, H * 0.5 + px * 0.36 + 7, "ms", 0.08, a=after)
            img = C.over(img, red, C.text_layer(["ПЕРЕПИСАНА · 2020"], "head_l", 40, C.GREY, W / 2, H * 0.5 + px * 0.36 + 110,
                                                "ms", 0.36, a=after)).convert("RGB")
        return C.grain(img, t, 0.04)

    def c_zero(tt, d):
        img = C.kb(dark_bg(9), tt / d, 0.06, 0.5, 0.5)
        k = C.seg(tt, 0.1, 1.1)
        return C.grain(C.over(img, C.big_number("0", "ПРЕЗИДЕНТСКИЕ СРОКИ", "обнулены · две тысячи двадцатый", k,
                                                px=340, count_from=2)).convert("RGB"), t, 0.04)

    fn, tt, d = shots(t, [(0.0, a_years), (c_k, b_konst), (c_0, c_zero)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0)


# ═════════════════════════ 04 · строкой ниже ═════════════════════════
@scene("04")
def s04(t, dur):
    c_s = rel("04", 15.60)     # «Строкой ниже вторая фраза.»
    c_d = rel("04", 17.65)     # «Дочери Путина…»
    T_B = c_d - 0.55

    def a_pan(tt, d):
        k = C.smoother(C.seg(tt, c_s, c_s + 1.2))
        yc = C.lerp(6759, 7037, k)
        sc = 2.4 + 0.03 * tt
        img, geo = page_view(yc, sc, 805, hide=(LINE_DAUGHTERS,))
        bp = to_frame(LINE_PUTIN, geo)
        bd = to_frame(LINE_DAUGHTERS, geo)
        fy = C.lerp((bp[1] + bp[3]) / 2, (bd[1] + bd[3]) / 2, k)
        img = fx.fonar(img, W / 2, fy, 600, 300, 0.10, 0.05, t)
        img = page_dark(img, t)
        return C.over(img, red_line(1.0, bp[0] - 8, bp[2] + 8, bp[3] + 12, 4), C.caption(*CAP_B, k=1.0)).convert("RGB")

    def b_reveal(tt, d):
        sc = 2.8 + 0.05 * tt
        base, geo = page_view(7037, sc, 805, hide=(LINE_DAUGHTERS,))
        true, _ = page_view(7037, sc, 805)
        box = to_frame(LINE_DAUGHTERS, geo)
        k = C.seg(tt, 0.35, 1.5)
        img = fx.vydelenie(base, true, box, k)
        img = fx.fonar(img, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 30, 640, 330, 0.10, 0.05, t)
        img = page_dark(img, t)
        k_tr = C.seg(tt, 0.75, 2.9)
        lays = [C.caption(*CAP_B, k=1.0)]
        if k_tr > 0:
            lays.append(C.text_layer(["ПЕРЕВОД"], "head_l", 24, C.GREY, SAFE_X, H - 270, "ls", 0.3, a=C.clamp(k_tr * 3)))
            lays.append(fx.typed("«Дочери Путина станут успешными политиками»", k_tr, "head_r", 48, C.WHITE, SAFE_X, H - 214, 0.02, True, t))
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    fn, tt, d = shots(t, [(0.0, a_pan), (T_B, b_reveal)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 05 · имён не называл ═════════════════════════
@scene("05")
def s05(t, dur):
    c_god = rel("05", 20.85)
    c_ni = rel("05", 22.94)
    img = C.kb(dark_bg(10), t / dur, 0.05, 0.5, 0.5)
    lays = []
    dim = 1 - 0.6 * C.seg(t, c_ni, c_ni + 0.3)
    for i, y in enumerate((H * 0.42, H * 0.58)):
        k = C.seg(t, 0.25 + i * 0.35, 0.6 + i * 0.35)
        if k <= 0:
            continue
        x0 = W / 2 - 420
        lays.append(C.text_layer(["ИМЯ"], "head_l", 36, C.GREY, x0, y, "ls", 0.3, a=k * dim))
        lay = C.layer()
        ImageDraw.Draw(lay).rectangle([(x0 + 110) * SS, (y + 2) * SS, (x0 + 110 + 730 * C.out_cubic(k)) * SS, (y + 4) * SS],
                                      fill=C.GREY3 + (int(255 * dim),))
        lays.append(C.done(lay))
        if k >= 1:
            lays.append(fx.cursor(x0 + 122, y - 2, 40, t + i * 0.5, 3, 1.0, C.WHITE))
    lays.append(K.date_tag("2016", C.seg(t, c_god, c_god + 0.5), sub="отец · публично"))
    k0 = C.seg(t, c_ni, c_ni + 0.7)
    if k0 > 0:
        lays.append(C.big_number("0 РАЗ", "НАЗВАЛ ИМЕНА ДОЧЕРЕЙ", None, k0, px=300, count_from=0))
    return C.finish(C.grain(C.over(img, *lays).convert("RGB"), t, 0.04), t, dur, fi=0.0, fo=0.25, grain_k=0.0)


# ═════════════════════════ 06 · Верица ═════════════════════════
K.CITIES.update({"Белград": (20.46, 44.82), "Сараево": (18.41, 43.86), "София": (23.32, 42.70),
                 "Загреб": (15.98, 45.81), "Скопье": (21.43, 41.99)})
BALKAN = K.Okno(lon=(12.2, 29.8), lat=(39.2, 48.2))


@scene("06")
def s06(t, dur):
    c_eti = rel("06", 23.82)
    c_serb = rel("06", 25.1)
    c_pish = rel("06", 26.24)
    c_gsh = rel("06", 27.55)
    c_oper = rel("06", 29.18)
    c_slovo = rel("06", 30.75)
    c_leto = rel("06", 32.74)
    c_prich = rel("06", 35.34)

    def a_silent(tt, d):
        img = verica("v05", "v05_krupno_1500.mp4", tt, push=0.05, hand=2.5)
        return C.over(img, C.caption(*CAP_V, k=C.seg(tt, 0.5, 1.2))).convert("RGB")

    def b_eti(tt, d):
        img = verica("v03", "v03_krupno_0100.mp4", tt, zoom=2.2, push=0.12, hand=3.5)
        return C.over(img, C.caption(*CAP_V, k=1.0)).convert("RGB")

    def b_map(tt, d):
        base = K.base(BALKAN, hot="Serbia")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.9, 0, 255).astype(np.uint8), "RGB")
        x, y = BALKAN.xy(20.46, 44.82)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        for j in range(3):
            ph = (tt * 0.9 + j * 0.33) % 1.0
            r = (12 + 150 * ph) * SS
            a = int(200 * (1 - ph))
            dd.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], outline=C.RED + (a,), width=3 * SS)
        img = C.over(base, C.done(lay), K.city_layer(["Белград"], C.seg(tt, 0.1, 0.5), okno=BALKAN, px=34),
                     K.date_tag("СЕРБИЯ", C.seg(tt, 0.05, 0.5), sub="карта условная"))
        img = C.kb(img.convert("RGB"), tt / d, 0.10, 0.45, 0.45)
        return C.grain(img, t, 0.03)

    def c_shtab(tt, d):
        img = verica("v04", "v04_krupno_0240.mp4", tt, zoom=2.1, push=0.07, hand=3.0)
        k = C.seg(tt, c_gsh - c_pish, c_gsh - c_pish + 0.5)
        img = C.fade(img, 1 - 0.35 * k)
        return C.over(img, word("ГЕНЕРАЛЬНЫЙ ШТАБ", k, H * 0.80, 120),
                      red_line(C.seg(tt, c_gsh - c_pish + 0.3, c_gsh - c_pish + 0.9), W / 2 - 300, W / 2 + 300, H * 0.80 + 24, 5),
                      C.text_layer(["ПО ПУБЛИКАЦИЯМ · ДОКУМЕНТОВ НЕТ"], "head_l", 26, C.GREY, W / 2, H * 0.80 + 70, "ms", 0.3,
                                   a=C.seg(tt, c_gsh - c_pish + 0.5, c_gsh - c_pish + 1.0)),
                      C.caption(*CAP_V, k=1.0)).convert("RGB")

    def d_rec(tt, d):
        ts = c_slovo - c_oper
        step = int(C.seg(tt, ts, ts + 0.01)) + int(C.seg(tt, ts + 0.8, ts + 0.81)) + int(C.seg(tt, ts + 1.6, ts + 1.61))
        z = 2.0 + 0.28 * step + 0.03 * tt
        fr = vid("v06", "v06_krupno_2400.mp4", 0.0, zoom=2.0, cx=0.47, cy=0.28).at(tt)
        hx, hy = fx.handheld(tt, 9.0, 2.0)
        img = zoom_at(fr, z / 2.0, W / 2 + hx, H / 2 + hy - 20 * (step))
        img = grade(img, 0.6)
        img = fx.vidoiskatel(img, tt, tc0=14 * 60 + 7, zoom_step=step)
        img = flash(img, tt, 0.06, 0.4)
        return C.over(img, C.caption("запись оператора", "по публикациям", "кадр: METANOJA TV, 2019", C.seg(tt, 0.4, 1.0), y=H - 130)).convert("RGB")

    def e_death(tt, d):
        T_FREEZE = 0.6
        key = "v07"
        if tt < T_FREEZE:
            img = verica(key, "v07_krupno_2940.mp4", tt, push=0.06, hand=2.0)
            return C.over(img, C.caption(*CAP_V, k=1.0)).convert("RGB")
        if "frozen" not in _v:
            fr = verica(key, "v07_krupno_2940.mp4", T_FREEZE, push=0.06, hand=2.0)
            _v["frozen"] = fr.convert("L").convert("RGB")
        img = _v["frozen"]
        k_bw = C.seg(tt, T_FREEZE, T_FREEZE + 0.25)
        img = Image.blend(verica(key, "v07_krupno_2940.mp4", T_FREEZE, push=0.06, hand=2.0), img, k_bw) if k_bw < 1 else img
        img = C.vignette(img, 0.6)
        k_r = C.seg(tt, 1.35, 2.55)
        img = fx.raspad(img, k_r, seed=9, amp=300)
        return C.over(img, K.date_tag("ЛЕТО 2019", C.seg(tt, 0.95, 1.4) * (1 - C.seg(tt, 2.2, 2.55)), sub="её не стало"),
                      flash_layer(C.seg(tt, T_FREEZE, T_FREEZE + 0.08) * (1 - C.seg(tt, T_FREEZE + 0.08, T_FREEZE + 0.2)))).convert("RGB")

    def f_cause(tt, d):
        img = Image.new("RGB", (W, H), (6, 6, 7))
        img = C.grain(img, t, 0.05)
        k = C.seg(tt, 0.1, 0.5)
        x0 = W / 2 - 440
        y = H * 0.5
        lays = [C.text_layer(["ПРИЧИНА СМЕРТИ"], "head_l", 36, C.GREY, x0, y, "ls", 0.3, a=k)]
        lay = C.layer()
        ImageDraw.Draw(lay).rectangle([(x0 + 330) * SS, (y + 2) * SS, (x0 + 330 + 560 * C.out_cubic(k)) * SS, (y + 4) * SS],
                                      fill=C.GREY3 + (255,))
        lays.append(C.done(lay))
        if k >= 1:
            lays.append(fx.cursor(x0 + 342, y - 2, 40, tt, 3, 1.0, C.WHITE))
        return C.over(img, *lays).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_silent), (c_eti, b_eti), (c_serb, b_map), (c_pish, c_shtab), (c_oper, d_rec),
                          (c_leto, e_death), (c_prich, f_cause)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.4, grain_k=0.035, vig=0.25)


def flash_layer(k):
    if k <= 0:
        return None
    im = Image.new("RGBA", (W, H), C.WHITE + (int(255 * C.clamp(k)),))
    return im


# ═════════════════════════ доска расследования ═════════════════════════
CARDS = [("01", "ЧЕЛОВЕК", "пожизненный президент"), ("02", "СЕМЬЯ", "дочери"), ("03", "СТРАНА", "две тысячи двадцать седьмой")]
CARD_POS = [(W * 0.24, H * 0.46, -2.5), (W * 0.50, H * 0.54, 1.5), (W * 0.76, H * 0.44, -1.0)]
CARD_W, CARD_H = 440, 290
_board = {}


def board_bg():
    if "bg" not in _board:
        p = C.paper(W, H, seed=41, tone=(62, 52, 44), dark=0.05)
        n = C.noise(W, H, 44, 2.0).filter(ImageFilter.GaussianBlur(0.8))
        a = np.asarray(p, np.float32) + (np.asarray(n, np.float32) / 255 - 0.5)[:, :, None] * 26
        _board["bg"] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    return _board["bg"]


def card_tex(i, k_text=1.0):
    """карточка на бумаге: номер красным, заголовок, подпись; текст открывается шторкой"""
    key = ("card", i, round(k_text, 2))
    if key in _board:
        return _board[key]
    num, title, sub = CARDS[i]
    s = 2
    w, h = CARD_W * s, CARD_H * s
    im = C.paper(w, h, seed=50 + i, tone=C.PAPER2, dark=0.02).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(120, 110, 95, 255), width=2)
    C.tracked(d, 28 * s, 54 * s, num, C.font("head", 40 * s), C.RED + (255,), 0.1)
    d.line([(28 * s, 66 * s), (90 * s, 66 * s)], fill=C.RED + (255,), width=3)
    if k_text > 0:
        lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        px = fit_px(title, "head", 76, CARD_W - 56, 0.06) * s
        C.tracked(dd, 28 * s, 165 * s, title, C.font("head", px), C.INK + (255,), 0.06)
        C.tracked(dd, 28 * s, 215 * s, sub, C.font("serif_i", 27 * s), (90, 80, 70, 255), 0.0)
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rectangle([0, 0, int(w * C.out_cubic(k_text)), h], fill=255)
        lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.split()[3]), np.asarray(m)).astype(np.uint8)))
        im = Image.alpha_composite(im, lay)
    out = im.resize((CARD_W, CARD_H), Image.LANCZOS)
    _board[key] = out
    return out


def pin_at(d, x, y):
    s = SS
    d.ellipse([(x - 11) * s, (y - 11) * s, (x + 11) * s, (y + 11) * s], fill=C.RED2 + (255,))
    d.ellipse([(x - 8) * s, (y - 9) * s, (x + 6) * s, (y + 5) * s], fill=C.RED + (255,))
    d.ellipse([(x - 5) * s, (y - 7) * s, (x - 1) * s, (y - 3) * s], fill=(250, 200, 190, 255))


def thread(d, pts, k, sag=46):
    """красная нить от булавки к булавке с провисом; k — сколько нарисовано"""
    if k <= 0:
        return
    path = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        for j in range(25):
            u = j / 24
            x = x0 + (x1 - x0) * u
            y = y0 + (y1 - y0) * u + sag * 4 * u * (1 - u)
            path.append((x, y))
    n = max(2, int(len(path) * C.out_cubic(k)))
    d.line([(x * SS, y * SS) for x, y in path[:n]], fill=C.RED + (255,), width=3 * SS)


def board(t, lamp_t, drop=(0, 0, 0), text=(0, 0, 0), k_thread=0.0, dark=0.10, amp=440.0):
    """доска под качающейся лампой; drop — ход падения карточек, text — ход открытия текста"""
    lx, ly = fx.lampa_pos(lamp_t, W / 2, amp, 3.6)
    img = board_bg().copy().convert("RGBA")
    pins = []
    for i, (cx, cy, ang) in enumerate(CARD_POS):
        k = drop[i]
        if k <= 0:
            continue
        kk = C.out_cubic(k)
        sc = 1.3 - 0.3 * kk
        yy = cy - 90 * (1 - kk)
        tex = card_tex(i, text[i]).rotate(ang, Image.BICUBIC, expand=True)
        if sc != 1.0:
            tex = tex.resize((int(tex.size[0] * sc), int(tex.size[1] * sc)), Image.LANCZOS)
        sh, sx, sy = fx.shadow_of(tex.size, lx, ly, cx, yy, blur=16 + int(30 * (1 - kk)), a=int(170 * kk))
        img.alpha_composite(sh, (sx, sy))
        tex = C.alpha(tex, C.clamp(k * 2))
        img.alpha_composite(tex, (int(cx - tex.size[0] / 2), int(yy - tex.size[1] / 2)))
        if k >= 1:
            pins.append((cx, cy - CARD_H / 2 + 26))
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    if len(pins) >= 2:
        thread(d, pins, k_thread)
    for x, y in pins:
        pin_at(d, x, y)
    img = C.over(img, C.done(lay)).convert("RGB")
    return fx.lampa(img, lx, ly, 1150, dark)


@scene("07")
def s07(t, dur):
    c_tri = rel("07", 37.07)
    c_chel = rel("07", 39.40)
    c_sem = rel("07", 40.63)
    c_str = rel("07", 41.93)
    c_prov = rel("07", 43.28)
    c_sb = rel("07", 44.86)
    c_net = rel("07", 45.83)
    c_posch = rel("07", 46.62)
    c_otv = rel("07", 50.99)
    c_byla = rel("07", 54.18)
    drops = (c_tri + 0.2, c_tri + 0.5, c_tri + 0.8)

    def a_board(tt, d):
        dr = tuple(C.seg(tt, drops[i], drops[i] + 0.45) for i in range(3))
        img = board(t, t, dr, (0, 0, 0), C.seg(tt, drops[2] + 0.4, drops[2] + 1.3))
        img = C.kb(img, tt / d, 0.04, 0.5, 0.5)
        lay = C.text_layer(["ТРИ ПРЕДСКАЗАНИЯ"], "head_l", 44, C.WHITE, W / 2, H - 120, "ms", 0.36,
                           a=C.seg(tt, c_tri + 0.1, c_tri + 0.5))
        return C.over(img, lay).convert("RGB")

    def push_card(i, tt, d):
        text = [1, 1, 1]
        for j in range(3):
            text[j] = 1.0 if j < i else (C.seg(tt, 0.1, 0.6) if j == i else 0.0)
        img = board(t, t, (1, 1, 1), tuple(text), 1.0)
        cx, cy, _ = CARD_POS[i]
        z = 1.45 + 0.25 * C.smoother(tt / d)
        img = zoom_at(img, z, cx, cy + 10)
        return flash(img, tt, 0.05, 0.35)

    def c_dates(tt, d):
        img = board(t, t, (1, 1, 1), (1, 1, 1), 1.0)
        img = C.kb(img, 1 - C.smoother(tt / d), 0.12, 0.5, 0.5)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        years = list(range(2016, 2028))
        x0, x1, y = 220, W - 220, H - 170
        k = C.seg(tt, 0.15, 1.35)
        dd.line([(x0 * SS, y * SS), ((x0 + (x1 - x0) * C.out_cubic(k)) * SS, y * SS)], fill=C.WHITE + (200,), width=2 * SS)
        f = C.font("head_r", 30 * SS)
        for i, yr in enumerate(years):
            u = i / (len(years) - 1)
            if u > C.out_cubic(k):
                break
            x = x0 + (x1 - x0) * u
            col = C.RED if yr in (2016, 2020, 2027) else C.WHITE
            dd.line([(x * SS, (y - 14) * SS), (x * SS, (y + 2) * SS)], fill=col + (255,), width=3 * SS)
            C.tracked(dd, x * SS, (y + 44) * SS, str(yr), f, col + (255,), 0.04, "ms")
        img = C.over(C.fade(img, 0.55), C.done(lay),
                     C.text_layer(["ПРОВЕРИМ ПО ДАТАМ"], "head_l", 44, C.WHITE, W / 2, 150, "ms", 0.36, a=C.seg(tt, 0.0, 0.4)))
        return img.convert("RGB")

    def c_sbylos(tt, d):
        img = C.fade(board(t, t, (1, 1, 1), (1, 1, 1), 1.0), 0.35)
        img = C.kb(img, tt / d, 0.05, 0.5, 0.5)
        tn = c_net - c_sb
        px = 118
        return C.over(img, word("СБЫЛОСЬ", C.seg(tt, 0.0, 0.4), H * 0.5 + px * 0.36, px, "head", C.WHITE, 0.08, W * 0.27),
                      word("НЕ СБЫЛОСЬ", C.seg(tt, tn, tn + 0.4), H * 0.5 + px * 0.36, px, "head", C.GREY, 0.08, W * 0.73),
                      slash(C.seg(tt, tn - 0.1, tn + 0.3))).convert("RGB")

    def d_2027(tt, d):
        img = C.fade(board(t, t, (1, 1, 1), (1, 1, 1), 1.0), 0.3).filter(ImageFilter.GaussianBlur(4))
        img = C.kb(img, tt / d, 0.05, 0.5, 0.5)
        k = C.seg(tt, 0.3, 3.3)
        return C.over(img, C.big_number("2027", "ПО ЕЁ СЛОВАМ ВЫПАДАЕТ НА", "год", k, px=360, count_from=2016)).convert("RGB")

    def e_prorok(tt, d):
        img = verica("v08", "v08_krupno_3420.mp4", tt, push=0.07, hand=2.5)
        tb = c_byla - c_otv
        k = C.seg(tt, tb, tb + 0.4)
        img = C.fade(img, 1 - 0.4 * k)
        return C.over(img, word("ПРОРОК?", k, H * 0.5 + 80, 230, "head", C.WHITE, 0.08),
                      red_line(C.seg(tt, tb + 0.3, tb + 0.8), W / 2 - 260, W / 2 + 260, H * 0.5 + 104, 6),
                      C.caption(*CAP_V, k=C.seg(tt, 0.3, 0.9))).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_board), (c_chel, lambda a, b: push_card(0, a, b)), (c_sem, lambda a, b: push_card(1, a, b)),
                          (c_str, lambda a, b: push_card(2, a, b)), (c_prov, c_dates), (c_sb, c_sbylos),
                          (c_posch, d_2027), (c_otv, e_prorok)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.035, vig=0.2)


def slash(k):
    if k <= 0:
        return None
    im = C.layer()
    kk = C.out_cubic(k)
    x0, y0 = W / 2 + 60, H * 0.5 - 110
    x1, y1 = W / 2 - 60, H * 0.5 + 110
    ImageDraw.Draw(im).line([(x0 * SS, y0 * SS), ((x0 + (x1 - x0) * kk) * SS, (y0 + (y1 - y0) * kk) * SS)],
                            fill=C.RED + (255,), width=7 * SS)
    return C.done(im)


# ═════════════════════════ 08 · пауза и титр ═════════════════════════
@scene("08")
def s08(t, dur):
    T_T = 2.0
    if t < T_T:
        k = C.smoother(t / T_T)
        img = board(t, t + 19.63, (1, 1, 1), (1, 1, 1), 1.0, dark=0.10 * (1 - k), amp=440 + 900 * k)
        img = C.fade(img, 1 - 0.85 * k)
        return C.finish(img, t, dur, fi=0.0, fo=0.0, grain_k=0.035, vig=0.3)
    tt = t - T_T
    img = C.fade(board(t, 2.0 + 19.63, (1, 1, 1), (1, 1, 1), 1.0), 0.22).filter(ImageFilter.GaussianBlur(5))
    img = C.kb(img, tt / (dur - T_T), 0.05, 0.5, 0.5)
    k1 = C.seg(tt, 0.0, 0.55)
    px1 = fit_px("БУДУЩЕЕ ПУТИНА И РОССИИ", "head", 124, W - 2 * SAFE_X, 0.08)
    lays = []
    if k1 > 0:
        sc = 1.5 - 0.5 * C.out_expo(k1)
        lays.append(C.text_layer(["2027"], "head", int(300 * sc), C.RED, W / 2, H * 0.58 + 300 * sc * 0.36, "ms", 0.02, a=C.clamp(k1 * 2)))
    lays.append(word("БУДУЩЕЕ ПУТИНА И РОССИИ", C.seg(tt, 0.45, 1.0), H * 0.58 - 190, px1, "head", C.WHITE, 0.08, rise=30))
    lays.append(red_line(C.seg(tt, 0.9, 1.5), W / 2 - 330, W / 2 + 330, H * 0.58 + 140, 5))
    lays.append(word("взрывные предсказания Верицы Обренович", C.seg(tt, 1.1, 1.7), H * 0.58 + 215, 52, "serif_i", C.GREY, 0.0, rise=16))
    img = C.over(img, *lays).convert("RGB")
    img = flash(img, tt, 0.1, 0.5)
    return C.finish(img, t, dur, fi=0.0, fo=0.7, grain_k=0.04, vig=0.35)
import scenes2  # noqa: E402,F401  — сцены второго куска (09-26) регистрируются в SCENES

import scenes3  # noqa: E402,F401  — сцены третьего куска (27-39)
import scenes4  # noqa: E402,F401  — сцены четвёртого куска (40-56)
import scenes5  # noqa: E402,F401  — сцены пятого куска (57-81)
import scenes6  # noqa: E402,F401  — сцены шестого куска (82-118)
