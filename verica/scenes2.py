#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Фильм «Верица» — второй кусок: блок 1 «КТО ОНА» и начало блока 2 «ДЕЛО ПЕРВОЕ»
до Дрездена, сцены 09-26 (163 с). Сцены 01-08 (первая минута) заморожены его
словом 23.11 — здесь только новый код, scenes.py не трогается.

Новые эффекты этого куска (fx2 внизу файла): папка-досье, которая открывается
пустой · эхо строк (фраза повторяется из статьи в статью) · шёпот (слухи
расплываются копиями) · россыпь точек по карте · стопка заголовков · перемотка
лет назад с роллом кадра.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import fx
import karta as K
import scenes as S
from core import W, H, SS
from scenes import (scene, rel, shots, flash, word, red_line, zoom_at, grade, vid, verica,
                    CAP_V, CAP_B, page_view, to_frame, page_dark, dark_bg, LINE_PUTIN,
                    card_tex, pin_at, thread, board_bg, CARD_POS, CARD_W, CARD_H, BALKAN, fit_px)

SAFE_X, SAFE_Y = 96, 54
K.CITIES.update({"Дрезден": (13.74, 51.05), "Москва": (37.62, 55.75), "Берлин": (13.40, 52.52)})
EUROPE = K.Okno(lon=(-2.0, 42.0), lat=(41.5, 61.0))
CAP_SD = ("sd.rs", "27.06.2016", "скриншот страницы 23.11.2026")
CAP_CH = ("заставка канала", "METANOJA TV", "интервью опубликовано 21.04.2019")

_doc = {}


def doc_view(name, yc, scale, xc=960.0):
    """окно любого скриншота-документа (как page_view для блога)"""
    if name not in _doc:
        _doc[name] = Image.open(C.apath(name)).convert("RGB")
    p = _doc[name]
    pw, ph = p.size
    cw, ch = W / scale, H / scale
    x0 = min(max(0, xc - cw / 2), pw - cw)
    y0 = min(max(0, yc - ch / 2), ph - ch)
    crop = p.crop((int(x0), int(y0), int(x0 + cw) + 1, int(y0 + ch) + 1))
    return crop.resize((W, H), Image.LANCZOS), (x0, y0, scale)


def label(text, k, y, px=40, color=C.GREY, x=W / 2, anchor="ms", track=0.36):
    if k <= 0:
        return None
    return C.text_layer([text], "head_l", px, color, x, y, anchor, track, a=k)


def quote_line(text, k, y, px=44, x=SAFE_X):
    """серая строка курсивом, въезжает слева"""
    if k <= 0:
        return None
    kk = C.out_cubic(k)
    return C.text_layer([text], "serif_i", px, C.GREY, x - 60 * (1 - kk), y, "ls", 0.0, a=k)


# ═════════════════════════ доска: новые карточки ═════════════════════════
EXTRA = {
    "lich": ((W * 0.26, H * 0.80, 1.5), "?", "ЛИЧНОСТЬ", ["год рождения — ?", "семья — ?", "родство — ?"]),
    "zachem": ((W * 0.74, H * 0.80, -2.0), "?", "ЗАЧЕМ ОПЕРАТОР?", ["записывать каждое слово", "вернёмся к этому"]),
    "mitr": ((W * 0.50, H * 0.82, 1.0), "", "МИТРОВИЧ", ["«психолог»", "все записи — на его канале"]),
}
_b2 = {}


def card_extra(key, k_text=1.0):
    ck = ("x", key, round(k_text, 2))
    if ck in _b2:
        return _b2[ck]
    (_, _, _), num, title, lines = EXTRA[key]
    s = 2
    w, h = CARD_W * s, CARD_H * s
    im = C.paper(w, h, seed=60 + len(key), tone=C.PAPER2, dark=0.02).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(120, 110, 95, 255), width=2)
    if num:
        C.tracked(d, 28 * s, 54 * s, num, C.font("head", 40 * s), C.RED + (255,), 0.1)
    d.line([(28 * s, 66 * s), (90 * s, 66 * s)], fill=C.RED + (255,), width=3)
    if k_text > 0:
        lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        px = fit_px(title, "head", 60, CARD_W - 56, 0.06) * s
        C.tracked(dd, 28 * s, 135 * s, title, C.font("head", px), C.INK + (255,), 0.06)
        for i, ln in enumerate(lines):
            C.tracked(dd, 28 * s, (180 + i * 34) * s, ln, C.font("serif_i", 25 * s), (90, 80, 70, 255), 0.0)
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rectangle([0, 0, int(w * C.out_cubic(k_text)), h], fill=255)
        lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.split()[3]), np.asarray(m)).astype(np.uint8)))
        im = Image.alpha_composite(im, lay)
    out = im.resize((CARD_W, CARD_H), Image.LANCZOS)
    _b2[ck] = out
    return out


def board2(t, lamp_t, extra=(), k_thread2=0.0, dark=0.10, amp=440.0, tail=0.0):
    """доска с тремя карточками хука (пришпилены) и новыми карточками extra=[(key, k_drop, k_text)];
    k_thread2 — нить от карточки 01 к ЛИЧНОСТЬ и дальше; tail — нить уходит вправо за край"""
    lx, ly = fx.lampa_pos(lamp_t, W / 2, amp, 3.6)
    img = board_bg().copy().convert("RGBA")
    pins = []
    items = [(CARD_POS[i], card_tex(i, 1.0), 1.0, None) for i in range(3)]
    for key, kd, kt in extra:
        if kd > 0:
            items.append((EXTRA[key][0], card_extra(key, kt), kd, key))
    for (cx, cy, ang), tex0, k, key in items:
        kk = C.out_cubic(k)
        sc = 1.3 - 0.3 * kk
        yy = cy - 90 * (1 - kk)
        tex = tex0.rotate(ang, Image.BICUBIC, expand=True)
        if sc != 1.0:
            tex = tex.resize((int(tex.size[0] * sc), int(tex.size[1] * sc)), Image.LANCZOS)
        sh, sx, sy = fx.shadow_of(tex.size, lx, ly, cx, yy, blur=16 + int(30 * (1 - kk)), a=int(170 * kk))
        img.alpha_composite(sh, (sx, sy))
        tex = C.alpha(tex, C.clamp(k * 2))
        img.alpha_composite(tex, (int(cx - tex.size[0] / 2), int(yy - tex.size[1] / 2)))
        if k >= 1:
            pins.append((key, (cx, cy - CARD_H / 2 + 26)))
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    base_pins = [p for k, p in pins if k is None]
    if len(base_pins) >= 2:
        thread(d, base_pins, 1.0)
    ex = {k: p for k, p in pins if k}
    if k_thread2 > 0 and "lich" in ex:
        thread(d, [base_pins[0], ex["lich"]], k_thread2, sag=30)
    if "zachem" in ex and tail > 0:
        thread(d, [base_pins[0], ex["zachem"]], min(1.0, tail * 2), sag=60)
        x, y = ex["zachem"]
        thread(d, [(x, y), (W + 80, y - 160)], C.seg(tail, 0.5, 1.0), sag=20)
    if "mitr" in ex:
        thread(d, [ex["mitr"], base_pins[1]], 1.0, sag=20)
    for _, (x, y) in pins:
        pin_at(d, x, y)
    img = C.over(img, C.done(lay)).convert("RGB")
    return fx.lampa(img, lx, ly, 1150, dark)


# ═════════════════════════ 09 · заставка канала, имя ═════════════════════════
@scene("09")
def s09(t, dur):
    c_name = rel("09", 55.71)
    c_nostr = rel("09", 58.9)
    c_vanga = rel("09", 61.3)

    def a_intro(tt, d):
        fr = vid("v01a", "v01_intro_0000-0014.mp4", 5.0, zoom=1.0).at(tt)
        img = grade(fr, 0.5)
        img = flash(img, tt - 4.0, 0.06, 0.3) if tt >= 4.0 else img
        return C.over(img, C.caption(*CAP_CH, k=C.seg(tt, 0.4, 1.0), y=150)).convert("RGB")

    def b_name(tt, d):
        img = verica("v16", "v16_krupno_4400.mp4", tt, push=0.06, hand=2.5)
        img = C.fade(img, 1 - 0.35 * C.seg(tt, 0.1, 0.5))
        return C.over(img, word("ВЕРИЦА ОБРЕНОВИЧ", C.seg(tt, 0.15, 0.6), H * 0.5 + 60, 150),
                      red_line(C.seg(tt, 0.5, 1.0), W / 2 - 360, W / 2 + 360, H * 0.5 + 84, 5),
                      C.caption(*CAP_V, k=C.seg(tt, 0.6, 1.2))).convert("RGB")

    def c_nick(tt, d):
        img = verica("v13", "v13_krupno_2015.mp4", tt, zoom=2.2, push=0.07, hand=3.0)
        img = C.fade(img, 0.6)
        tv = c_vanga - c_nostr
        return C.over(img, label("В СЕРБИИ", C.seg(tt, 0.0, 0.4), H * 0.36 - 70, 30),
                      word("«СЕРБСКИЙ НОСТРАДАМУС»", C.seg(tt, 0.05, 0.5), H * 0.36 + 30, 96, "serif_b", C.WHITE, 0.0),
                      label("В РОССИИ", C.seg(tt, tv, tv + 0.4), H * 0.64 - 70, 30),
                      word("«СЕРБСКАЯ ВАНГА»", C.seg(tt, tv + 0.05, tv + 0.5), H * 0.64 + 30, 96, "serif_b", C.WHITE, 0.0),
                      C.caption(*CAP_V, k=1.0)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_intro), (c_name, b_name), (c_nostr, c_nick)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.3, fo=0.0, grain_k=0.035, vig=0.25)


# ═════════════════════════ 10 · династия, родство ═════════════════════════
@scene("10")
def s10(t, dur):
    c_fam = rel("10", 62.88)
    c_rod = rel("10", 67.82)
    c_neiz = rel("10", 68.60)
    c_nich = rel("10", 69.47)

    def a_dyn(tt, d):
        img = C.kb(dark_bg(12), tt / d, 0.06, 0.5, 0.5)
        return C.grain(C.over(img, label("ФАМИЛИЯ КАК У КОРОЛЕВСКОЙ ДИНАСТИИ", C.seg(tt, 0.1, 0.5), H * 0.5 - 170, 34),
                              word("ОБРЕНОВИЧИ", C.seg(tt, 0.2, 0.7), H * 0.5 + 70, 200),
                              red_line(C.seg(tt, 0.6, 1.2), W / 2 - 300, W / 2 + 300, H * 0.5 + 96, 5),
                              label("ПРАВИЛИ СЕРБИЕЙ · ДЕВЯТНАДЦАТЫЙ ВЕК", C.seg(tt, 1.9, 2.4), H * 0.5 + 160, 34)).convert("RGB"), t, 0.04)

    def b_rod(tt, d):
        img = C.kb(dark_bg(13), tt / d, 0.08, 0.5, 0.5)
        tn = c_neiz - c_rod
        k = C.seg(tt, 0.0, 0.35)
        sc = 1.6 - 0.6 * C.out_expo(k)
        lays = [C.text_layer(["?"], "head", int(420 * sc), C.RED, W / 2, H * 0.5 + 150, "ms", 0.0, a=C.clamp(k * 2)),
                label("РОДСТВО", C.seg(tt, 0.1, 0.4), H * 0.5 - 200, 40, C.WHITE),
                label("НЕИЗВЕСТНО", C.seg(tt, tn, tn + 0.4), H * 0.5 + 240, 44)]
        return C.grain(flash(C.over(img, *lays).convert("RGB"), tt, 0.08, 0.5), t, 0.04)

    def c_nothing(tt, d):
        img = verica("v11", "v11_krupno_0320.mp4", tt, push=0.06, hand=2.5)
        img = C.fade(img, 0.55)
        return C.over(img, word("ПОЧТИ НИЧЕГО НЕ ИЗВЕСТНО", C.seg(tt, 0.2, 0.7), H * 0.5 + 40, 110, "head_l", C.WHITE, 0.2),
                      C.caption(*CAP_V, k=1.0)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_dyn), (c_rod, b_rod), (c_nich, c_nothing)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 11 · пусто, пусто ═════════════════════════
@scene("11")
def s11(t, dur):
    c_god = rel("11", 71.69)
    c_sem = rel("11", 73.11)
    img = C.kb(dark_bg(14), t / dur, 0.05, 0.5, 0.5)
    lays = []
    for i, (lab, c0, y) in enumerate((("ГОД РОЖДЕНИЯ", c_god, H * 0.42), ("СЕМЬЯ", c_sem, H * 0.58))):
        k = C.seg(t, c0, c0 + 0.35)
        if k <= 0:
            continue
        x0 = W / 2 - 520
        lays.append(C.text_layer([lab], "head_l", 36, C.GREY, x0, y, "ls", 0.3, a=k))
        lay = C.layer()
        ImageDraw.Draw(lay).rectangle([(x0 + 330) * SS, (y + 2) * SS, (x0 + 330 + 700 * C.out_cubic(k)) * SS, (y + 4) * SS],
                                      fill=C.GREY3 + (255,))
        lays.append(C.done(lay))
        kt = C.seg(t, c0 + 0.5, c0 + 0.95)
        lays.append(fx.typed("пусто", kt, "serif_i", 40, C.GREY2, x0 + 345, y - 6, 0.0, True, t) if kt > 0 else
                    fx.cursor(x0 + 345, y - 2, 40, t, 3, 1.0, C.WHITE))
    return C.finish(C.grain(C.over(img, *lays).convert("RGB"), t, 0.04), t, dur, fi=0.0, fo=0.0, grain_k=0.0)


# ═════════════════════════ 12 · карточка ЛИЧНОСТЬ, издания пишут ═════════════════════════
YUG = ("Serbia", "Republic of Serbia", "Croatia", "Bosnia and Herzegovina", "Montenegro", "Slovenia", "North Macedonia", "Macedonia", "Kosovo")


def yug_layer(k):
    key = ("yug", round(k, 2))
    if key in _b2:
        return _b2[key]
    lay = None
    for ft in K.feats():
        if K.name_of(ft) in YUG:
            for ring in K.rings(ft):
                if len(ring) < 20:
                    continue
                z = K.zone_layer(tuple(tuple(pt[:2]) for pt in ring), k, okno=BALKAN, hatch=True, fill_a=55, outline=True)
                lay = z if lay is None else Image.alpha_composite(lay, z)
    _b2[key] = lay
    return lay


@scene("12")
def s12(t, dur):
    c_zato = rel("12", 74.19)
    c_izd = rel("12", 75.74)
    c_yug = rel("12", 78.3)

    def a_card(tt, d):
        img = board2(t, t + 30, extra=[("lich", C.seg(tt, 0.1, 0.55), C.seg(tt, 0.5, 1.0))], k_thread2=C.seg(tt, 0.9, 1.5))
        cx, cy, _ = EXTRA["lich"][0]
        z = 1.0 + 0.7 * C.smoother(C.seg(tt, 0.4, 2.4))
        img = zoom_at(img, z, cx, cy - 40)
        return C.over(img, label("ЗАТО ИЗВЕСТНО ДРУГОЕ", C.seg(tt, c_zato - 0.0, c_zato + 0.4), H - 110, 40, C.WHITE)).convert("RGB")

    def b_izd(tt, d):
        img = verica("v12", "v12_krupno_0645.mp4", tt, zoom=2.1, push=0.07, hand=3.0)
        img = C.fade(img, 0.6)
        return C.over(img, word("ИЗДАНИЯ ПИШУТ", C.seg(tt, 0.1, 0.5), H * 0.5 + 50, 140),
                      label("БАЛКАНСКИЕ И РОССИЙСКИЕ · ДОКУМЕНТОВ НЕТ", C.seg(tt, 0.5, 0.9), H * 0.5 + 120, 30),
                      C.caption(*CAP_V, k=1.0)).convert("RGB")

    def c_yug_map(tt, d):
        base = K.base(BALKAN, hot="Republic of Serbia")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.7, 0, 255).astype(np.uint8), "RGB")
        img = C.over(base, yug_layer(C.seg(tt, 0.0, 1.2)),
                     K.city_layer(["Белград"], C.seg(tt, 0.6, 1.0), okno=BALKAN, px=32),
                     K.date_tag("ЮГОСЛАВИЯ", C.seg(tt, 0.1, 0.5), sub="границы условные"),
                     word("ЮГОСЛАВСКИЕ ВОЕННЫЕ", C.seg(tt, 1.0, 1.5), H - 150, 96, "head", C.WHITE, 0.08))
        img = C.kb(img.convert("RGB"), tt / d, 0.08, 0.55, 0.5)
        return C.grain(img, t, 0.03)

    fn, tt, d = shots(t, [(0.0, a_card), (c_izd, b_izd), (c_yug, c_yug_map)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.035, vig=0.2)


# ═════════════════════════ 13 · Группа 69, папка пустая ═════════════════════════
@scene("13")
def s13(t, dur):
    c_gr = rel("13", 84.40)
    c_dok = rel("13", 87.43)

    def a_folder(tt, d):
        img = board2(t, t + 36, extra=[("lich", 1, 1)], k_thread2=1.0)
        img = C.fade(img, 0.5).filter(ImageFilter.GaussianBlur(2))
        k = C.seg(tt, 0.1, 0.8)
        return C.over(img, folder(k_in=k, k_open=0.0, t=tt),
                      label("НАЗЫВАЮТ ДАЖЕ ПОДРАЗДЕЛЕНИЕ", C.seg(tt, 0.3, 0.8), 150, 40, C.WHITE)).convert("RGB")

    def b_69(tt, d):
        img = C.kb(dark_bg(15), tt / d, 0.06, 0.5, 0.5)
        k = C.seg(tt, 0.05, 1.3)
        return C.grain(C.over(img, C.big_number("69", "ГРУППА", "при Генеральном штабе · по публикациям", k, px=380, count_from=0)).convert("RGB"), t, 0.04)

    def c_empty(tt, d):
        img = board2(t, t + 36, extra=[("lich", 1, 1)], k_thread2=1.0)
        img = C.fade(img, 0.5).filter(ImageFilter.GaussianBlur(2))
        return C.over(img, folder(k_in=1.0, k_open=C.seg(tt, 0.0, 0.7), t=tt),
                      label("ДОКУМЕНТОВ НЕТ", C.seg(tt, 0.5, 0.9), H - 120, 44, C.WHITE)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_folder), (c_gr, b_69), (c_dok, c_empty)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.035, vig=0.25)


# ═════════════════════════ 14 · из статьи в статью, оператор, зачем ═════════════════════════
@scene("14")
def s14(t, dur):
    c_det = rel("14", 88.63)
    c_stat = rel("14", 89.65)
    c_oper = rel("14", 91.7)
    c_slovo = rel("14", 94.28)
    c_zachem = rel("14", 96.32)

    def a_echo(tt, d):
        img = C.kb(dark_bg(16), tt / d, 0.05, 0.5, 0.5)
        te = c_stat - c_det
        return C.grain(C.over(img, label("ЕСТЬ ДЕТАЛЬ", C.seg(tt, 0.0, 0.4), H * 0.5 - 250, 40, C.WHITE),
                              echo_lines("ПОВТОРЯЕТСЯ ИЗ СТАТЬИ В СТАТЬЮ", C.seg(tt, te, te + 1.6), H * 0.5 - 120)).convert("RGB"), t, 0.04)

    def b_rec(tt, d):
        ts = c_slovo - c_oper
        step = int(C.seg(tt, ts, ts + 0.01)) + int(C.seg(tt, ts + 0.7, ts + 0.71))
        z = 2.0 + 0.25 * step + 0.03 * tt
        fr = vid("v14", "v14_krupno_2640.mp4", 0.0, zoom=2.0, cx=0.47, cy=0.28).at(tt)
        hx, hy = fx.handheld(tt, 8.0, 5.0)
        img = zoom_at(fr, z / 2.0, W / 2 + hx, H / 2 + hy - 20 * step)
        img = grade(img, 0.6)
        img = fx.vidoiskatel(img, tt + 3.0, tc0=21 * 60 + 40, zoom_step=step)
        img = flash(img, tt, 0.06, 0.4)
        return C.over(img, C.caption("телеоператор от властей", "по публикациям · документов нет", "кадр: METANOJA TV, 2019", C.seg(tt, 0.4, 1.0), y=H - 130),
                      label("ЧТОБЫ НИ ОДНО СЛОВО НЕ ПРОПАЛО", C.seg(tt, ts, ts + 0.4), 170, 34, C.WHITE)).convert("RGB")

    def c_zachem_fn(tt, d):
        img = Image.new("RGB", (W, H), (6, 6, 7))
        k = C.seg(tt, 0.05, 0.45)
        sc = 1.4 - 0.4 * C.out_expo(k)
        lays = [C.text_layer(["ЗАЧЕМ?"], "head", int(260 * sc), C.WHITE, W / 2, H * 0.5 + 80, "ms", 0.06, a=C.clamp(k * 2)),
                label("ГОСУДАРСТВУ ЗАПИСЫВАТЬ СЛОВА ЯСНОВИДЯЩЕЙ", C.seg(tt, 0.6, 1.1), H * 0.5 + 170, 34)]
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.05)

    fn, tt, d = shots(t, [(0.0, a_echo), (c_oper, b_rec), (c_zachem, c_zachem_fn)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 15 · запомните этот вопрос ═════════════════════════
@scene("15")
def s15(t, dur):
    c_zap = rel("15", 99.20)
    c_vern = rel("15", 100.67)
    img = board2(t, t + 40, extra=[("lich", 1, 1), ("zachem", C.seg(t, 0.15, 0.6), C.seg(t, 0.55, 1.0))], k_thread2=1.0,
                 tail=C.seg(t, c_vern - 0.2, c_vern + 1.0))
    cx, cy, _ = EXTRA["zachem"][0]
    z = 1.0 + 0.6 * C.smoother(C.seg(t, c_zap, c_zap + 1.3)) - 0.3 * C.smoother(C.seg(t, c_vern, c_vern + 1.0))
    img = zoom_at(img, max(1.0, z), cx, cy - 60)
    return C.finish(C.over(img, label("ЗАПОМНИТЕ ЭТОТ ВОПРОС", C.seg(t, c_zap, c_zap + 0.4), 150, 40, C.WHITE)).convert("RGB"),
                    t, dur, fi=0.0, fo=0.0, grain_k=0.035, vig=0.2)


# ═════════════════════════ 16 · Верица без слов, Митрович, канал ═════════════════════════
@scene("16")
def s16(t, dur):
    c_ryad = rel("16", 102.14)
    c_mitr = rel("16", 104.15)
    c_kanal = rel("16", 107.05)

    def a_silent(tt, d):
        img = verica("v09", "v09_krupno_3910.mp4", tt, push=0.05, hand=2.5)
        return C.over(img, C.caption(*CAP_V, k=C.seg(tt, 0.5, 1.2))).convert("RGB")

    def b_mitr(tt, d):
        tm = c_mitr - c_ryad
        img = board2(t, t + 44, extra=[("lich", 1, 1), ("zachem", 1, 1), ("mitr", C.seg(tt, tm, tm + 0.45), C.seg(tt, tm + 0.4, tm + 0.9))],
                     k_thread2=1.0, tail=1.0)
        cx, cy, _ = EXTRA["mitr"][0]
        z = 1.0 + 0.5 * C.smoother(C.seg(tt, tm, tm + 1.5))
        img = zoom_at(img, z, cx, cy - 60)
        return C.over(img, label("РЯДОМ С НЕЙ ВСЕГДА ОДИН ЧЕЛОВЕК", C.seg(tt, 0.0, 0.4), 150, 40, C.WHITE)).convert("RGB")

    def c_channel(tt, d):
        fr = vid("v01b", "v01_intro_0000-0014.mp4", 5.3, zoom=1.0).at(tt)
        img = grade(fr, 0.5)
        return C.over(img, C.caption(*CAP_CH, k=C.seg(tt, 0.2, 0.7), y=150),
                      label("ВСЕ ИЗВЕСТНЫЕ ЗАПИСИ — НА ЕГО КАНАЛЕ", C.seg(tt, 0.3, 0.8), H - 120, 34, C.WHITE)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_silent), (c_ryad, b_mitr), (c_kanal, c_channel)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.035, vig=0.25)


# ═════════════════════════ 17 · после смерти? газета ═════════════════════════
SD = "sd_rs_live.png"


@scene("17")
def s17(t, dur):
    c_ross = rel("17", 110.06)
    c_netak = rel("17", 114.36)
    c_gaz = rel("17", 115.49)
    c_kadr = rel("17", 119.99)
    c_zhiv = rel("17", 121.76)

    def a_posle(tt, d):
        img = C.kb(dark_bg(17), tt / d, 0.05, 0.5, 0.5)
        return C.grain(C.over(img, label("В РОССИИ ПИШУТ", C.seg(tt, 0.1, 0.5), H * 0.5 - 200, 40),
                              word("ТОЛЬКО ПОСЛЕ ЕЁ СМЕРТИ?", C.seg(tt, 1.6, 2.1), H * 0.5 + 60, 130, "head_l", C.WHITE, 0.1)).convert("RGB"), t, 0.04)

    def b_netak(tt, d):
        img = C.kb(dark_bg(17), (tt + 4.4) / 5.6, 0.05, 0.5, 0.5)
        return C.grain(C.over(img, label("В РОССИИ ПИШУТ", 1.0, H * 0.5 - 200, 40),
                              word("ТОЛЬКО ПОСЛЕ ЕЁ СМЕРТИ?", 1.0, H * 0.5 + 60, 130, "head_l", C.GREY2, 0.1),
                              red_line(C.seg(tt, 0.0, 0.4), W / 2 - 560, W / 2 + 560, H * 0.5 + 14, 10),
                              word("ЭТО НЕ ТАК", C.seg(tt, 0.1, 0.5), H * 0.5 + 220, 100, "head", C.RED, 0.1)).convert("RGB"), t, 0.04)

    def c_paper(tt, d):
        k = C.smoother(C.seg(tt, 0.0, 1.6))
        yc = C.lerp(300, 600, k)
        sc = C.lerp(1.4, 2.0, k)
        img, geo = doc_view(SD, yc, sc, 782)
        img = fx.fonar(img, W * 0.45, H * 0.45, 640, 360, 0.10, 0.05, t)
        img = page_dark(img, t)
        return C.over(img, K.date_tag("27 ИЮНЯ 2016", C.seg(tt, 2.3, 2.8), sub="сербская газета"),
                      C.caption(*CAP_SD, k=C.seg(tt, 0.4, 1.0))).convert("RGB")

    def d_frame(tt, d):
        sc = 1.9 + 0.1 * tt
        img, geo = doc_view(SD, 930, sc, 782)
        img = fx.fonar(img, W * 0.5, H * 0.5, 600, 400, 0.12, 0.04, t)
        img = page_dark(img, t)
        return flash(C.over(img, label("С КАДРОМ ТОГО ЖЕ КАНАЛА", C.seg(tt, 0.1, 0.5), 150, 36, C.WHITE),
                            C.caption(*CAP_SD, k=1.0)).convert("RGB"), tt, 0.06, 0.35)

    def e_alive(tt, d):
        img = verica("v13b", "v13_krupno_2015.mp4", tt + 1.5, push=0.08, hand=2.5)
        img = C.fade(img, 0.6)
        return C.over(img, word("ЕЁ СЛУШАЛИ ПРИ ЖИЗНИ", C.seg(tt, 0.1, 0.5), H * 0.5 + 50, 130),
                      C.caption(*CAP_V, k=1.0)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_posle), (c_netak, b_netak), (c_gaz, c_paper), (c_kadr, d_frame), (c_zhiv, e_alive)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 18 · дата крупно, 28 дней ═════════════════════════
@scene("18")
def s18(t, dur):
    c_24 = rel("18", 123.53)
    c_22 = rel("18", 128.02)

    def a_date(tt, d):
        sc = 3.4 + 0.15 * tt
        img, geo = doc_view(SD, 640, sc, 700)
        img = fx.fonar(img, W * 0.38, H * 0.48, 520, 260, 0.10, 0.04, t)
        img = page_dark(img, t)
        return C.over(img, K.date_tag("27.06.2016", C.seg(tt, 0.1, 0.5), px=96, sub="дата публикации"),
                      C.caption(*CAP_SD, k=1.0)).convert("RGB")

    def b_line(tt, d):
        img = C.kb(dark_bg(18), tt / d, 0.05, 0.5, 0.5)
        t22 = c_22 - c_24
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        y = H * 0.55
        x0, x1 = 300, W - 300
        k1 = C.seg(tt, 0.0, 0.5)
        k2 = C.seg(tt, t22, t22 + 0.8)
        dd.line([(x0 * SS, y * SS), ((x0 + (x1 - x0) * C.out_cubic(k2)) * SS, y * SS)], fill=C.RED + (255,), width=4 * SS)
        if k1 > 0:
            dd.ellipse([(x0 - 10) * SS, (y - 10) * SS, (x0 + 10) * SS, (y + 10) * SS], fill=C.WHITE + (int(255 * k1),))
        if k2 >= 1:
            dd.ellipse([(x1 - 10) * SS, (y - 10) * SS, (x1 + 10) * SS, (y + 10) * SS], fill=C.RED + (255,))
        lays = [C.done(lay),
                K.date_tag("24 ИЮНЯ 2019", k1, x=x0 + 240, y=y - 60, px=56, sub="последнее видео"),
                K.date_tag("22 ИЮЛЯ 2019", C.seg(tt, t22 + 0.5, t22 + 0.9), x=x1 + 40, y=y + 120, px=56, sub="её не стало")]
        kn = C.seg(tt, t22 + 0.9, t22 + 1.8)
        if kn > 0:
            lays.append(C.big_number("28 ДНЕЙ", None, None, kn, cx=W / 2, cy=H * 0.3, px=170, count_from=0, rings=False))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    fn, tt, d = shots(t, [(0.0, a_date), (c_24, b_line)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 19 · слухи ═════════════════════════
@scene("19")
def s19(t, dur):
    c_sl = rel("19", 130.58)
    c_int = rel("19", 132.31)
    c_mog = rel("19", 135.36)
    c_pod = rel("19", 137.78)
    c_opr = rel("19", 138.91)

    def a_sluhi(tt, d):
        img = C.kb(dark_bg(19), tt / d, 0.05, 0.5, 0.5)
        return C.grain(C.over(img, label("ДАЛЬШЕ НАЧИНАЮТСЯ", C.seg(tt, c_sl, c_sl + 0.4), H * 0.5 - 210, 40),
                              whisper("СЛУХИ", C.seg(tt, c_sl + 0.1, c_sl + 1.4), tt)).convert("RGB"), t, 0.05)

    def b_int(tt, d):
        img = verica("v15", "v15_krupno_3330.mp4", tt, push=0.06, hand=3.5)
        img = C.fade(img, 0.45)
        return C.over(img, quote_line("«…после слишком откровенного интервью»", C.seg(tt, 0.1, 0.6), H * 0.5 + 20, 52),
                      label("СЛУХ · ПОДТВЕРЖДЕНИЙ НЕТ", C.seg(tt, 0.5, 0.9), H * 0.5 + 90, 28, C.GREY, SAFE_X, "ls"),
                      C.caption(*CAP_V, k=1.0)).convert("RGB")

    def c_mog_fn(tt, d):
        img = C.kb(dark_bg(20), tt / d, 0.06, 0.5, 0.5)
        return C.grain(C.over(img, quote_line("«…никто не знает, где её могила»", C.seg(tt, 0.1, 0.6), H * 0.5 + 20, 52),
                              label("СЛУХ · ПОДТВЕРЖДЕНИЙ НЕТ", C.seg(tt, 0.5, 0.9), H * 0.5 + 90, 28, C.GREY, SAFE_X, "ls")).convert("RGB"), t, 0.05)

    def d_fields(tt, d):
        img = C.kb(dark_bg(21), tt / d, 0.05, 0.5, 0.5)
        to = c_opr - c_pod
        lays = []
        for lab, c0, y in (("ПОДТВЕРЖДЕНИЯ", 0.0, H * 0.42), ("ОПРОВЕРЖЕНИЯ", to, H * 0.58)):
            k = C.seg(tt, c0, c0 + 0.35)
            if k <= 0:
                continue
            x0 = W / 2 - 520
            lays.append(C.text_layer([lab], "head_l", 36, C.GREY, x0, y, "ls", 0.3, a=k))
            lay = C.layer()
            ImageDraw.Draw(lay).rectangle([(x0 + 360) * SS, (y + 2) * SS, (x0 + 360 + 640 * C.out_cubic(k)) * SS, (y + 4) * SS], fill=C.GREY3 + (255,))
            lays.append(C.done(lay))
            if k >= 1:
                lays.append(C.text_layer(["—"], "head_l", 44, C.GREY2, x0 + 380, y - 4, "ls", 0.0, a=C.seg(tt, c0 + 0.5, c0 + 0.8)))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    fn, tt, d = shots(t, [(0.0, a_sluhi), (c_int, b_int), (c_mog, c_mog_fn), (c_pod, d_fields)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 20 · сотни ясновидящих, будем проверять ═════════════════════════
@scene("20")
def s20(t, dur):
    c_sot = rel("20", 140.37)
    c_slovo = rel("20", 142.25)
    c_prov = rel("20", 144.10)

    def a_dots(tt, d):
        base = K.base(BALKAN, hot="")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.6, 0, 255).astype(np.uint8), "RGB")
        img = C.over(base, dots_layer(C.seg(tt, 0.2, 3.2), tt),
                     K.date_tag("БАЛКАНЫ", C.seg(tt, 0.1, 0.5), sub="карта условная"),
                     label("ЯСНОВИДЯЩИХ — СОТНИ", C.seg(tt, c_sot + 0.1, c_sot + 0.5), H - 130, 44, C.WHITE))
        img = C.kb(img.convert("RGB"), tt / d, 0.08, 0.5, 0.5)
        return C.grain(img, t, 0.03)

    def b_slovo(tt, d):
        img = C.fade(board2(t, t + 50, extra=[("lich", 1, 1), ("zachem", 1, 1), ("mitr", 1, 1)], k_thread2=1.0, tail=1.0), 0.5)
        img = C.kb(img, tt / d, 0.05, 0.5, 0.5)
        return C.over(img, word("НА СЛОВО ВЕРИТЬ НЕ БУДЕМ", C.seg(tt, 0.1, 0.5), H * 0.5 + 40, 110, "head_l", C.GREY, 0.15)).convert("RGB")

    def c_prov_fn(tt, d):
        img = C.fade(board2(t, t + 50, extra=[("lich", 1, 1), ("zachem", 1, 1), ("mitr", 1, 1)], k_thread2=1.0, tail=1.0), 0.45)
        img = C.kb(img, (tt + 1.9) / 3.3, 0.05, 0.5, 0.5)
        return flash(C.over(img, word("БУДЕМ ПРОВЕРЯТЬ", C.seg(tt, 0.0, 0.4), H * 0.5 + 60, 170),
                            red_line(C.seg(tt, 0.3, 0.8), W / 2 - 400, W / 2 + 400, H * 0.5 + 86, 6)).convert("RGB"), tt, 0.06, 0.4)

    fn, tt, d = shots(t, [(0.0, a_dots), (c_slovo, b_slovo), (c_prov, c_prov_fn)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.035, vig=0.2)


# ═════════════════════════ 21 · ДЕЛО ПЕРВОЕ ═════════════════════════
@scene("21")
def s21(t, dur):
    c_date = rel("21", 145.76)
    c_belg = rel("21", 148.24)
    c_int = rel("21", 149.14)
    c_zap = rel("21", 150.93)
    c_blog = rel("21", 152.7)
    c_kop = rel("21", 154.7)

    def a_title(tt, d):
        img = board2(t, 10.0, extra=[("lich", 1, 1), ("zachem", 1, 1), ("mitr", 1, 1)], k_thread2=1.0, tail=1.0, amp=0.0)
        cx, cy, _ = CARD_POS[0]
        img = C.fade(zoom_at(img, 2.3 + 0.1 * tt, cx, cy), 0.35).filter(ImageFilter.GaussianBlur(3))
        k = C.seg(tt, 0.0, 0.5)
        sc = 1.3 - 0.3 * C.out_expo(k)
        px = fit_px("ДЕЛО ПЕРВОЕ", "head", 170, W - 2 * SAFE_X, 0.1)
        lays = [C.text_layer(["ДЕЛО ПЕРВОЕ"], "head", int(px * sc), C.WHITE, W / 2, H * 0.5 + 40, "ms", 0.1, a=C.clamp(k * 2)),
                red_line(C.seg(tt, 0.4, 0.9), W / 2 - 200, W / 2 + 200, H * 0.5 + 66, 5),
                word("пожизненный", C.seg(tt, 0.6, 1.0), H * 0.5 + 150, 60, "serif_i", C.GREY, 0.0, rise=16),
                K.date_tag("2 ФЕВРАЛЯ 2016", C.seg(tt, c_date, c_date + 0.5), sub="Белград · большое интервью")]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.1, 0.5)

    def b_belg(tt, d):
        base = K.base(BALKAN, hot="Republic of Serbia")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.9, 0, 255).astype(np.uint8), "RGB")
        x, y = BALKAN.xy(20.46, 44.82)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        for j in range(3):
            ph = (tt * 0.9 + j * 0.33) % 1.0
            r = (12 + 150 * ph) * SS
            dd.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], outline=C.RED + (int(200 * (1 - ph)),), width=3 * SS)
        img = C.over(base, C.done(lay), K.city_layer(["Белград"], C.seg(tt, 0.05, 0.4), okno=BALKAN, px=36),
                     K.date_tag("2 ФЕВРАЛЯ 2016", 1.0, sub="карта условная"))
        return C.grain(zoom_at(img.convert("RGB"), 1.3 + 0.2 * tt, x, y), t, 0.03)

    def c_int_fn(tt, d):
        img = verica("v12b", "v12_krupno_0645.mp4", tt + 1.0, zoom=2.1, push=0.08, hand=3.0)
        return C.over(img, label("БОЛЬШОЕ ИНТЕРВЬЮ · ЗАПИСИ НЕ НАШЛИ", C.seg(tt, 0.2, 0.6), 150, 34, C.WHITE),
                      C.caption(*CAP_V, k=1.0)).convert("RGB")

    def d_novideo(tt, d):
        sc = 2.0 + 0.05 * tt
        img, geo = page_view(6090, sc, 805)
        img = fx.fonar(img, W * 0.5, H * 0.5, 520, 360, 0.10, 0.05, t)
        img = page_dark(img, t)
        return flash(C.over(img, label("САМОЙ ЗАПИСИ НЕТ · ОСТАЛСЯ ПЕРЕСКАЗ", C.seg(tt, 0.2, 0.6), 150, 34, C.WHITE),
                            C.caption(*CAP_B, k=1.0)).convert("RGB"), tt, 0.06, 0.3)

    def e_blog(tt, d):
        k = C.smoother(C.seg(tt, 0.0, 1.2))
        img, geo = page_view(C.lerp(6090, 5920, k), 1.8, 805)
        img = fx.fonar(img, W * 0.45, H * 0.45, 640, 360, 0.10, 0.05, t)
        img = page_dark(img, t)
        return C.over(img, label("ТОТ САМЫЙ БЛОГ", C.seg(tt, 0.2, 0.6), 150, 34, C.WHITE),
                      C.caption(*CAP_B, k=1.0)).convert("RGB")

    def f_wayback(tt, d):
        sc = 2.4 + 0.06 * tt
        img, geo = page_view(140, sc, 420)
        img = fx.fonar(img, W * 0.3, H * 0.3 - 60 * C.smoother(C.seg(tt, 0.3, 1.2)), 560, 300, 0.10, 0.05, t)
        img = page_dark(img, t)
        return flash(C.over(img, K.date_tag("8 ИЮЛЯ 2018", C.seg(tt, 0.8, 1.3), sub="копия веб-архива"),
                            label("КОПИЯ СТРАНИЦЫ СОХРАНЕНА В ВЕБ-АРХИВЕ", C.seg(tt, 0.2, 0.6), H - 130, 34, C.WHITE),
                            C.caption(*CAP_B, k=1.0)).convert("RGB"), tt, 0.06, 0.3)

    fn, tt, d = shots(t, [(0.0, a_title), (c_belg, b_belg), (c_int, c_int_fn), (c_zap, d_novideo), (c_blog, e_blog), (c_kop, f_wayback)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.3, grain_k=0.0, vig=0.3)


# ═════════════════════════ 22 · за два года до новости ═════════════════════════
@scene("22")
def s22(t, dur):
    sc = 2.4 + 0.04 * t
    img, geo = page_view(6759, sc, 805)
    box = to_frame(LINE_PUTIN, geo)
    img = fx.fonar(img, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 40, 600, 320, 0.10, 0.05, t)
    img = page_dark(img, t)
    y = box[3] + 150
    lay = C.layer()
    dd = ImageDraw.Draw(lay)
    pts = [(W * 0.22, "25.05.2016", "запись", 0.3), (W * 0.5, "08.07.2018", "копия в веб-архиве", 1.3), (W * 0.78, "2020", "стало новостью", 2.4)]
    for i, (x, dt, sub, t0) in enumerate(pts):
        k = C.seg(t, t0, t0 + 0.4)
        if k <= 0:
            continue
        col = C.RED if i == 2 else C.WHITE
        dd.ellipse([(x - 9) * SS, (y - 9) * SS, (x + 9) * SS, (y + 9) * SS], fill=col + (int(255 * k),))
        if i > 0:
            xp = pts[i - 1][0]
            dd.line([(xp * SS, y * SS), ((xp + (x - xp) * C.out_cubic(k)) * SS, y * SS)], fill=C.RED + (255,), width=3 * SS)
    lays = [red_line(1.0, box[0] - 8, box[2] + 8, box[3] + 12, 4), C.done(lay)]
    for i, (x, dt, sub, t0) in enumerate(pts):
        k = C.seg(t, t0 + 0.1, t0 + 0.5)
        lays.append(C.text_layer([dt], "head", 44, C.WHITE, x, y + 60, "ms", 0.04, a=k))
        lays.append(C.text_layer([sub.upper()], "head_l", 24, C.GREY, x, y + 92, "ms", 0.3, a=k))
    lays.append(C.caption(*CAP_B, k=1.0))
    return C.finish(C.over(img, *lays).convert("RGB"), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 23 · 2020: Дума, обнуление, 2036, 83 ═════════════════════════
@scene("23")
def s23(t, dur):
    c_dal = rel("23", 162.67)
    c_10 = rel("23", 164.28)
    c_duma = rel("23", 166.44)
    c_obn = rel("23", 167.81)
    c_1iul = rel("23", 170.17)
    c_2036 = rel("23", 172.61)
    c_83 = rel("23", 176.48)

    def a_dal(tt, d):
        img = C.kb(dark_bg(22), tt / d, 0.05, 0.5, 0.5)
        return C.grain(C.over(img, label("ЧТО ПРОИСХОДИТ ДАЛЬШЕ", C.seg(tt, 0.1, 0.5), H * 0.5 + 15, 48, C.WHITE)).convert("RGB"), t, 0.04)

    def b_10(tt, d):
        img = C.kb(dark_bg(23), tt / d, 0.06, 0.5, 0.5)
        return C.grain(C.over(img, fx.flip_number(["2016", "2017", "2018", "2019", "2020"], C.seg(tt, 0.0, 0.7), W / 2, H * 0.45, 260),
                              label("10 МАРТА", C.seg(tt, 0.7, 1.1), H * 0.45 + 220, 70, C.WHITE)).convert("RGB"), t, 0.04)

    def c_duma_fn(tt, d):
        img = C.kb(dark_bg(24), tt / d, 0.06, 0.5, 0.5)
        return C.grain(C.over(img, word("ГОСУДАРСТВЕННАЯ ДУМА", C.seg(tt, 0.05, 0.45), H * 0.5 + 50, 150),
                              red_line(C.seg(tt, 0.4, 0.9), W / 2 - 300, W / 2 + 300, H * 0.5 + 74, 5)).convert("RGB"), t, 0.04)

    def d_obn(tt, d):
        img = C.kb(dark_bg(25), tt / d, 0.06, 0.5, 0.5)
        px = fit_px("ОБНУЛИТЬ", "head", 220, W - 2 * SAFE_X, 0.08)
        img = C.over(img, word("ОБНУЛИТЬ", C.seg(tt, 0.0, 0.4), H * 0.5 + px * 0.36, px, "head", C.WHITE, 0.08),
                     label("ПРЕЗИДЕНТСКИЕ СРОКИ", C.seg(tt, 0.5, 0.9), H * 0.5 + 150, 40)).convert("RGB")
        g = C.seg(tt, 0.35, 0.5) * (1 - C.seg(tt, 0.5, 0.85))
        if g > 0:
            img = fx.glitch(img, g, seed=11 + int(tt * 30), slices=16, shift=140, rgb=20)
        return C.grain(img, t, 0.04)

    def e_vote(tt, d):
        img = C.kb(dark_bg(26), tt / d, 0.05, 0.5, 0.5)
        k = C.seg(tt, 0.6, 2.0)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        x0, x1, y = 300, W - 300, H * 0.56
        dd.rectangle([x0 * SS, (y - 22) * SS, x1 * SS, (y + 22) * SS], fill=C.GREY3 + (255,))
        dd.rectangle([x0 * SS, (y - 22) * SS, (x0 + (x1 - x0) * 0.7792 * C.out_cubic(k)) * SS, (y + 22) * SS], fill=C.RED + (255,))
        val = 77.92 * C.out_cubic(k)
        lays = [C.done(lay), label("1 ИЮЛЯ 2020 · ИТОГИ ГОЛОСОВАНИЯ", C.seg(tt, 0.1, 0.5), H * 0.56 - 160, 40, C.WHITE),
                C.text_layer(["ЗА  %s %%" % ("%.1f" % val).replace(".", ",")], "head", 90, C.RED, x0, y - 50, "ls", 0.04, a=C.clamp(k * 3)),
                C.text_layer(["ПРОТИВ  21,3 %"], "head_l", 44, C.GREY, x1, y - 50, "rs", 0.1, a=C.seg(tt, 1.9, 2.3)),
                label("ПО ДАННЫМ ЦИК РОССИИ", C.seg(tt, 0.8, 1.2), y + 90, 26)]
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    def f_2036(tt, d):
        img = C.kb(dark_bg(27), tt / d, 0.06, 0.5, 0.5)
        years = [str(y) for y in range(2020, 2037)]
        return C.grain(C.over(img, label("МОЖЕТ ОСТАВАТЬСЯ В КРЕМЛЕ ДО", C.seg(tt, 0.1, 0.5), H * 0.5 - 220, 36),
                              fx.flip_number(years, C.seg(tt, 0.3, 2.6), W / 2, H * 0.5, 300),
                              C.text_layer(["2036"], "head", 300, C.RED, W / 2, H * 0.5 + 108, "ms", 0.02, a=C.seg(tt, 2.6, 2.9))).convert("RGB"), t, 0.04)

    def g_83(tt, d):
        img = C.kb(dark_bg(28), tt / d, 0.06, 0.5, 0.5)
        return C.grain(C.over(img, C.big_number("83 ГОДА", "ЕМУ БУДЕТ", None, C.seg(tt, 0.05, 1.0), px=320, count_from=67)).convert("RGB"), t, 0.04)

    fn, tt, d = shots(t, [(0.0, a_dal), (c_10, b_10), (c_duma, c_duma_fn), (c_obn, d_obn), (c_1iul, e_vote), (c_2036, f_2036), (c_83, g_83)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 24 · заголовки ═════════════════════════
@scene("24")
def s24(t, dur):
    c_pr = rel("24", 178.25)
    c_q = rel("24", 181.2)
    img = C.kb(dark_bg(29), t / dur, 0.05, 0.5, 0.5)
    img = C.over(img, headlines(C.seg(t, c_pr, c_pr + 2.0), t)).convert("RGB")
    k = C.seg(t, c_q, c_q + 0.4)
    lays = [label("ЗАПАДНАЯ ПРЕССА · ТЕ ЖЕ ДВА СЛОВА", C.seg(t, c_pr, c_pr + 0.4), 150, 34, C.WHITE)]
    if k > 0:
        img = C.fade(img, 1 - 0.5 * k)
        px = fit_px("«ПРЕЗИДЕНТ ПОЖИЗНЕННО»", "head", 150, W - 2 * SAFE_X, 0.06)
        sc = 1.3 - 0.3 * C.out_expo(k)
        lays.append(C.text_layer(["«ПРЕЗИДЕНТ ПОЖИЗНЕННО»"], "head", int(px * sc), C.WHITE, W / 2, H * 0.5 + 50, "ms", 0.06, a=C.clamp(k * 2)))
        lays.append(red_line(C.seg(t, c_q + 0.3, c_q + 0.8), W / 2 - 400, W / 2 + 400, H * 0.5 + 76, 6))
    img = C.over(img, *lays).convert("RGB")
    img = flash(img, t - c_q, 0.08, 0.5) if t >= c_q else img
    return C.finish(C.grain(img, t, 0.04), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 25 · честная оговорка, 16 лет ═════════════════════════
@scene("25")
def s25(t, dur):
    c_ch = rel("25", 183.01)
    c_16 = rel("25", 184.6)
    c_ug = rel("25", 187.79)

    def a_ch(tt, d):
        img = C.kb(dark_bg(30), tt / d, 0.05, 0.5, 0.5)
        return C.grain(C.over(img, label("ЧЕСТНАЯ ОГОВОРКА", C.seg(tt, c_ch, c_ch + 0.4), H * 0.5 + 15, 54, C.WHITE)).convert("RGB"), t, 0.04)

    def b_16(tt, d):
        img = C.kb(dark_bg(31), tt / d, 0.06, 0.5, 0.5)
        return C.grain(C.over(img, C.big_number("16 ЛЕТ", "К ДВЕ ТЫСЯЧИ ШЕСТНАДЦАТОМУ У ВЛАСТИ", None, C.seg(tt, 0.05, 1.3), px=320, count_from=0)).convert("RGB"), t, 0.04)

    def c_ug_fn(tt, d):
        img = C.kb(dark_bg(32), tt / d, 0.06, 0.5, 0.5)
        return C.grain(C.over(img, word("УГАДАТЬ БЫЛО НЕТРУДНО", C.seg(tt, 0.05, 0.45), H * 0.5 + 40, 120, "head_l", C.WHITE, 0.15)).convert("RGB"), t, 0.04)

    fn, tt, d = shots(t, [(0.0, a_ch), (c_16, b_16), (c_ug, c_ug_fn)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 26 · тридцать лет назад, Дрезден ═════════════════════════
@scene("26")
def s26(t, dur):
    c_komu = rel("26", 190.42)
    c_30 = rel("26", 192.28)
    c_gorod = rel("26", 194.73)
    c_rush = rel("26", 196.6)

    def a_komu(tt, d):
        img = verica("v16b", "v16_krupno_4400.mp4", tt + 0.5, push=0.08, hand=2.5)
        img = C.fade(img, 0.65)
        return C.over(img, label("КОМУ ОНА ЭТО ПРЕДСКАЗАЛА", C.seg(tt, c_komu, c_komu + 0.4), H - 130, 40, C.WHITE),
                      C.caption(*CAP_V, k=1.0)).convert("RGB")

    def b_rewind(tt, d):
        years = [str(y) for y in range(2016, 1984, -1)]
        return rewind(years, C.seg(tt, 0.0, 2.2), tt, t)

    def c_map(tt, d):
        base = K.base(EUROPE, hot="Germany")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.6, 0, 255).astype(np.uint8), "RGB")
        x, y = EUROPE.xy(13.74, 51.05)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        for j in range(3):
            ph = (tt * 0.8 + j * 0.33) % 1.0
            r = (10 + 120 * ph) * SS
            dd.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], outline=C.RED + (int(200 * (1 - ph)),), width=3 * SS)
        tr = c_rush - c_gorod
        img = C.over(base, C.done(lay), K.city_layer(["Дрезден", "Берлин", "Москва"], C.seg(tt, 0.3, 0.8), okno=EUROPE, px=30, side={"Москва": "l"}),
                     K.date_tag("1985", C.seg(tt, 0.1, 0.5), sub="тридцать лет назад · карта условная"),
                     word("ГДЕ ОН УВИДЕЛ, КАК РУШИТСЯ ВЛАСТЬ", C.seg(tt, tr, tr + 0.5), H - 140, 70, "head_l", C.WHITE, 0.15))
        return C.grain(zoom_at(img.convert("RGB"), 1.0 + 0.35 * C.smoother(tt / d), x, y), t, 0.03)

    fn, tt, d = shots(t, [(0.0, a_komu), (c_30, b_rewind), (c_gorod, c_map)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.035, vig=0.25)


# ═════════════════════════ fx2 — новые эффекты второго куска ═════════════════════════
def folder(k_in, k_open, t):
    """папка-досье: въезжает снизу, потом обложка открывается влево — внутри пустой лист"""
    fw, fh = 760, 540
    cx, cy = W / 2, H * 0.55 + 120 * (1 - C.out_cubic(k_in))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if k_in <= 0:
        return lay
    x0, y0 = int(cx - fw / 2), int(cy - fh / 2)
    # нижняя часть папки + лист
    back = C.paper(fw, fh, seed=70, tone=(150, 132, 104), dark=0.05).convert("RGBA")
    sheet = C.paper(fw - 60, fh - 50, seed=71, tone=(222, 214, 196), dark=0.0).convert("RGBA")
    back.alpha_composite(sheet, (30, 25))
    d = ImageDraw.Draw(back)
    if k_open > 0.5:
        a = int(255 * C.seg(k_open, 0.6, 0.95))
        f = C.font("head_l", 56)
        d.text((fw / 2, fh / 2), "ПУСТО", font=f, fill=(120, 110, 100, a), anchor="mm")
    sh, sx, sy = fx.shadow_of((fw, fh), W / 2, -200, cx, cy, blur=24, a=160)
    lay.alpha_composite(sh, (sx, sy))
    lay.alpha_composite(C.alpha(back, C.clamp(k_in * 2)), (x0, y0))
    # обложка с язычком: открывается вокруг левого края
    cover = C.paper(fw, fh, seed=72, tone=(126, 108, 84), dark=0.0).convert("RGBA")
    dc = ImageDraw.Draw(cover)
    dc.rectangle([0, 0, fw - 1, fh - 1], outline=(70, 58, 44, 255), width=3)
    dc.rectangle([fw - 260, 28, fw - 40, 92], fill=(204, 34, 30, 255))
    dc.text((fw - 150, 60), "ГРУППА 69", font=C.font("head", 40), fill=(240, 238, 234, 255), anchor="mm")
    dc.text((fw / 2, fh * 0.62), "ДЕЛО", font=C.font("head_l", 48), fill=(60, 50, 40, 255), anchor="mm")
    dc.text((fw / 2, fh * 0.62 + 60), "ПРИ ГЕНЕРАЛЬНОМ ШТАБЕ", font=C.font("head_l", 26), fill=(80, 70, 60, 255), anchor="mm")
    ang = math.pi * C.smoother(k_open)
    cs = math.cos(ang)
    if cs > 0.02:
        wdt = max(2, int(fw * cs))
        cv = cover.resize((wdt, fh), Image.LANCZOS)
        cv = C.alpha(cv, C.clamp(k_in * 2))
        lay.alpha_composite(cv, (x0, y0))
    elif cs < -0.02:
        wdt = max(2, int(fw * -cs))
        backside = C.paper(wdt, fh, seed=73, tone=(160, 142, 116), dark=0.1).convert("RGBA")
        lay.alpha_composite(backside, (x0 - wdt, y0))
    return lay


def echo_lines(text, k, y0, n=6):
    """фраза повторяется вниз эхом: каждая следующая строка тусклее и мельче"""
    if k <= 0:
        return None
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    for i in range(n):
        ki = C.seg(k, i / n, (i + 1) / n)
        if ki <= 0:
            break
        px = 72 - i * 8
        a = int(255 * (1 - i * 0.14) * C.clamp(ki * 2))
        f = C.font("head_l" if i else "head", px * SS)
        C.tracked(d, W / 2 * SS, (y0 + i * 78 + (1 - C.out_cubic(ki)) * 30) * SS, text, f, C.WHITE + (a,), 0.12, "ms")
    return C.done(lay)


def whisper(text, k, t):
    """шёпот: слово и его размытые копии расплываются в стороны"""
    if k <= 0:
        return None
    base = C.text_layer([text], "head", 220, C.WHITE, W / 2, H * 0.5 + 80, "ms", 0.1, a=C.clamp(k * 2))
    out = base
    for i in range(1, 5):
        dx = (i * 28 + 10 * math.sin(t * 1.3 + i)) * C.out_cubic(k)
        dy = (i * 6) * C.out_cubic(k)
        for sgn in (-1, 1):
            g = base.filter(ImageFilter.GaussianBlur(3 * i))
            g = C.alpha(g, 0.35 / i)
            sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sh.paste(g, (int(sgn * dx), int(dy)), g)
            out = Image.alpha_composite(out, sh)
    return out


_dots = {}


def dots_layer(k, t, n=420):
    """россыпь точек по суше Балкан: появляются по одной, свежие пульсируют"""
    if "pts" not in _dots:
        base = K.base(BALKAN, hot="")
        a = np.asarray(base.convert("L"))
        rng = np.random.default_rng(5)
        pts = []
        while len(pts) < n:
            x, y = int(rng.uniform(SAFE_X, W - SAFE_X)), int(rng.uniform(SAFE_Y + 40, H - 160))
            if a[y, x] > 22:
                pts.append((x, y))
        _dots["pts"] = pts
    pts = _dots["pts"]
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    m = int(len(pts) * C.clamp(k))
    for i in range(m):
        x, y = pts[i]
        age = (k * len(pts) - i) / len(pts) * 3.0
        r = (3.5 + 4 * max(0, 1 - age)) * SS
        d.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], fill=C.RED + (255,))
        if age < 0.5:
            rr = (8 + 40 * age * 2) * SS
            d.ellipse([x * SS - rr, y * SS - rr, x * SS + rr, y * SS + rr], outline=C.RED + (int(160 * (1 - age * 2)),), width=2 * SS)
    return C.done(lay)


def headlines(k, t, n=7):
    """стопка газетных полос: тёмные панели со строками-брусками влетают с разных сторон"""
    if k <= 0:
        return None
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    rng = random.Random(3)
    for i in range(n):
        ki = C.seg(k, i / n, (i + 1) / n + 0.15)
        if ki <= 0:
            break
        kk = C.out_cubic(ki)
        pw, ph = rng.randint(520, 820), rng.randint(200, 300)
        cx, cy = rng.randint(300, W - 300), rng.randint(220, H - 220)
        side = rng.choice((-1, 1))
        x = cx + side * (1 - kk) * 900
        a = int(230 * kk)
        x0, y0 = (x - pw / 2) * SS, (cy - ph / 2) * SS
        d.rectangle([x0, y0, x0 + pw * SS, y0 + ph * SS], fill=(26, 26, 30, a), outline=(70, 70, 76, a), width=2 * SS)
        d.rectangle([x0 + 24 * SS, y0 + 24 * SS, x0 + (pw - 24) * SS, y0 + 70 * SS], fill=(190, 188, 184, a))
        for j in range(5):
            yy = y0 + (96 + j * 24) * SS
            wl = rng.uniform(0.5, 0.92)
            d.rectangle([x0 + 24 * SS, yy, x0 + (24 + (pw - 48) * wl) * SS, yy + 9 * SS], fill=(96, 96, 100, a))
    return C.done(lay)


def rewind(values, k, tt, t):
    """перемотка назад: годы бегут вниз, кадр катится вертикально и мерцает"""
    img = C.kb(dark_bg(33), tt / 3.0, 0.08, 0.5, 0.5)
    num = fx.flip_number(values, k, W / 2, H * 0.5, 300)
    img = C.over(img, num, label("НА ТРИДЦАТЬ ЛЕТ НАЗАД", C.seg(tt, 0.0, 0.4), H * 0.5 - 230, 40)).convert("RGB")
    a = np.asarray(img, np.uint8)
    roll = int((H * 0.9 * (1 - C.smoother(k)) * tt * 1.7) % H) if k < 1 else 0
    if roll:
        a = np.roll(a, roll, axis=0)
        a[max(0, roll - 3):roll + 3] = 230
    fl = 1.0 + 0.25 * math.sin(tt * 41.0) * (1 - k)
    a = np.clip(a.astype(np.float32) * fl, 0, 255).astype(np.uint8)
    out = Image.fromarray(a, "RGB")
    if k < 1:
        out = fx.glitch(out, 0.25 * (1 - k), seed=int(tt * 30), slices=10, shift=60, rgb=8)
    return C.grain(out, t, 0.06)
