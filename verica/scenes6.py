#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Фильм «Верица» — шестой кусок: блоки 5 «СЧЁТ», 6 «НОСИТЕЛИ ИНФОРМАЦИИ», 7 «ФИНАЛ», сцены 82-118 (≈152 с, до конца).

Штампы — ТОЛЬКО здесь, в блоке 5 (его решение). Людей в кадре нет, кроме Верицы из врезок: Ванга — карта
Болгарии и карточка-досье с подписью «по публикациям · документов в кадре нет». Финал — снова страница
блога из начала, взгляд Верицы в камеру (v10) в полной тишине, титры источников.

Новые эффекты своей разработки (fx6, низ файла):
  shtamp           — штамп: прилетает с высоты, бьёт, краска с пропусками, пыль от удара
  lestnica_promahov — промахи строками: год красным, пункт серым, строки встают одна под другой
  sortirovka       — два столбца С ДАТОЙ / БЕЗ ДАТЫ: пункты разлетаются по колонкам, слева — перечёркнуты
  kompas           — стрелка компаса качается и замирает на направлении
  tsiferblat       — циферблат: стрелки крутятся и останавливаются на «дне и часе»
  chertezh         — чертёж: сетка, пунктирный маршрут по точкам, подписи
  perepis          — перепись слова: «ПРОРОКИ» рвётся глитчем и зачёркивается, ниже печатается новое
  tribuna          — трибуна с перечёркнутым микрофоном и обходная пунктирная дорожка
  eho_radar        — эхо-радар: кольцо уходит, отклик возвращается точкой
  schyot_palochek  — счёт палочками под двумя словами
  titry            — титры источников: список едет вверх
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import fx
import karta as K
from core import W, H, SS
from scenes import (scene, rel, shots, flash, word, red_line, zoom_at, vid, verica,
                    CAP_V, CAP_B, page_view, to_frame, page_dark, dark_bg, CARD_POS, CARD_W, CARD_H, fit_px,
                    LINE_PUTIN, LINE_DAUGHTERS, BALKAN)
from scenes2 import label, EXTRA
from scenes3 import lamp_bg, rukopis
from scenes4 import board4, board_blur_bg
from scenes5 import roscherk, strana_layer, rukopis_layer

SAFE_X, SAFE_Y = 96, 54

CAP_PUBL = ("по публикациям", "документов в кадре нет", None)
CAP_KARTA = ("карта условная", None, None)
CAP_SHEMA = ("схема условная", None, None)
CAP_VANGA = ("Ванга · Болгария", "по публикациям · документов в кадре нет", None)
CAP_PROM = ("интервью 2016 года", "по публикациям", None)

EXTRA["promahi"] = ((W * 0.09, H * 0.60, -2.0), "", "ПРОМАХИ", ["Курдистан · Германия · Испания", "Босния · Турция · база в Сербии"])
EXTRA["vanga"] = ((W * 0.91, H * 0.60, 1.5), "", "ВАНГА", ["Болгария · с 1967 на службе", "рядом — спецслужбы"])
EXTRA["kto"] = ((W * 0.50, H * 0.50, -3.0), "?", "КТО И ЗАЧЕМ?", ["сказал ей это", "десять лет назад"])

ALL6 = [("kat", 1, 1), ("mar", 1, 1), ("sech", 1, 1), ("dolzh", 1, 1), ("ross", 1, 1), ("posle", 1, 1)]
BULG = K.Okno(lon=(17.0, 33.0), lat=(38.5, 46.5))
K.CITIES.update({"София": (23.32, 42.70), "Белград": (20.46, 44.80)})

PROMAHI = [("2017", "независимый Курдистан"), ("2018", "раскол Германии"), ("2019", "распад Испании"),
           ("2020", "распад Боснии"), ("—", "война России с Турцией"), ("2019", "российская база в Сербии")]


def board6(t, lamp_t, extra=(), threads=(), amp=0.0, dark=0.10):
    return board4(t, lamp_t, list(ALL6) + list(extra), threads=threads, amp=amp, dark=dark)


def card_center(key):
    if isinstance(key, int):
        cx, cy, _ = CARD_POS[key]
    else:
        cx, cy, _ = EXTRA[key][0]
    return cx, cy


def board_card(t, tt, key, z0=2.0, z1=1.8, extra=(), threads=()):
    """доска, наезд на карточку key"""
    img = board6(t, 30.0 + tt, extra, threads, amp=300.0)
    cx, cy = card_center(key)
    z = z0 - (z0 - z1) * C.smoother(C.seg(tt, 0.0, 1.5))
    return zoom_at(img, z, cx, cy), z


def on_zoom(x, y, z, cx, cy):
    """координаты точки доски → координаты кадра после zoom_at(img, z, cx, cy)"""
    cw, ch = W / z, H / z
    x0 = min(max(0, cx - cw / 2), W - cw)
    y0 = min(max(0, cy - ch / 2), H - ch)
    return (x - x0) * z, (y - y0) * z


# ═════════════════════════ 82 · титр СЧЁТ · теперь честно ═════════════════════════
@scene("82")
def s82(t, dur):
    c_chto = rel("82", 488.96)

    def a_title(tt, d):
        img = board_blur_bg(t, extra=ALL6)
        k = C.seg(tt, 0.0, 0.5)
        sc = 1.3 - 0.3 * C.out_expo(k)
        px = fit_px("СЧЁТ", "head", 190, W - 2 * SAFE_X, 0.14)
        lays = [C.text_layer(["СЧЁТ"], "head", int(px * sc), C.WHITE, W / 2, H * 0.5 + 40, "ms", 0.14, a=C.clamp(k * 2)),
                red_line(C.seg(tt, 0.4, 0.9), W / 2 - 160, W / 2 + 160, H * 0.5 + 66, 5),
                word("теперь честно", C.seg(tt, 0.6, 1.0), H * 0.5 + 150, 60, "serif_i", C.GREY, 0.0, rise=16)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.1, 0.5)

    def b_board(tt, d):
        img = board6(t, 30.0 + tt, amp=360.0)
        img = zoom_at(img, 1.25 - 0.1 * C.smoother(C.seg(tt, 0, d)), W * 0.5, H * 0.5)
        return flash(C.over(img, word("ЧТО СБЫЛОСЬ", C.seg(tt, 0.05, 0.45), 150, 96, "head", C.WHITE, 0.12, rise=28)).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_title), (c_chto, b_board)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 83 · армия вошла · попадание ═════════════════════════
@scene("83")
def s83(t, dur):
    c_skaz = rel("83", 492.31)
    c_pop = rel("83", 494.53)

    def a(tt, d):
        img, z = board_card(t, tt, "ross", 2.3, 2.1)
        cx, cy = card_center("ross")
        sx, sy = on_zoom(cx, cy - 60, z, cx, cy)
        ks = C.seg(tt, c_skaz, c_skaz + 0.5)
        lays = [label("РОССИЙСКАЯ АРМИЯ ВОШЛА В УКРАИНУ", C.seg(tt, 0.05, 0.45), 130, 40, C.WHITE),
                label("СКАЗАНО · 2015   НАПЕЧАТАНО · 27.06.2016   СОБЫТИЕ · 24.02.2022", ks, 190, 30, C.WHITE),
                shtamp("СБЫЛОСЬ", C.seg(tt, c_pop + 0.15, c_pop + 0.5), sx, sy, -8.0, C.WHITE, tt)]
        return C.over(img, *lays).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 84 · пожизненный · проверит время ═════════════════════════
@scene("84")
def s84(t, dur):
    c_zakon = rel("84", 497.04)
    c_prov = rel("84", 498.77)

    def a(tt, d):
        img, z = board_card(t, tt, 0, 2.3, 2.1)
        cx, cy = card_center(0)
        sx, sy = on_zoom(cx, cy + 40, z, cx, cy)
        lays = [label("ПОЖИЗНЕННЫЙ ПРЕЗИДЕНТ", C.seg(tt, 0.05, 0.45), 130, 40, C.WHITE),
                label("ЗАКОН ЭТО УЖЕ ПОЗВОЛЯЕТ · ПОПРАВКИ 2020", C.seg(tt, c_zakon, c_zakon + 0.4), H - 150, 30, C.GREY),
                shtamp("ПРОВЕРИТ ВРЕМЯ", C.seg(tt, c_prov + 0.1, c_prov + 0.45), sx, sy, 6.0, C.GREY, tt)]
        return C.over(img, *lays).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 85 · дочери · не сбылось · не опровергнуто ═════════════════════════
@scene("85")
def s85(t, dur):
    c_ne = rel("85", 501.10)
    c_no = rel("85", 501.99)

    def a(tt, d):
        img, z = board_card(t, tt, 1, 2.3, 2.1)
        cx, cy = card_center(1)
        sx, sy = on_zoom(cx, cy + 30, z, cx, cy)
        lays = [label("ДОЧЕРИ-ПОЛИТИКИ", C.seg(tt, 0.05, 0.45), 130, 40, C.WHITE),
                shtamp("НЕ СБЫЛОСЬ", C.seg(tt, c_ne + 0.1, c_ne + 0.45), sx - 40, sy - 30, -10.0, C.RED, tt),
                shtamp("НЕ ОПРОВЕРГНУТО", C.seg(tt, c_no + 0.2, c_no + 0.55), sx + 60, sy + 90, 7.0, C.GREY, tt)]
        return C.over(img, *lays).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 86 · теперь промахи ═════════════════════════
@scene("86")
def s86(t, dur):
    c_prom = rel("86", 503.34)
    c_int = rel("86", 504.78)

    def a(tt, d):
        img = C.kb(dark_bg(81), tt / 4.0, 0.05, 0.5, 0.5)
        kp = C.seg(tt, c_prom, c_prom + 0.45)
        return C.grain(C.over(img, label("ТЕПЕРЬ", C.seg(tt, 0.2, 0.6), H * 0.5 - 170, 40, C.GREY),
                              word("ПРОМАХИ", kp, H * 0.5 + 60, 170, "head", C.RED, 0.12, rise=36),
                              roscherk(C.seg(tt, c_prom + 0.3, c_prom + 0.8), 9),
                              label("В ИНТЕРВЬЮ ШЕСТНАДЦАТОГО ГОДА ОНА НАЗЫВАЛА ГОДЫ", C.seg(tt, c_int, c_int + 0.45), H - 150, 36, C.WHITE),
                              C.caption(*CAP_PROM, k=C.seg(tt, c_int, c_int + 0.5))).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 87 · список промахов с годами ═════════════════════════
@scene("87")
def s87(t, dur):
    cues = [rel("87", v) for v in (507.57, 509.5, 511.8, 513.79, 515.6)]

    def a(tt, d):
        img = C.kb(dark_bg(82), tt / 10.0, 0.04, 0.5, 0.5)
        ks = [C.seg(tt, c, c + 0.5) for c in cues] + [0.0]
        return C.grain(C.over(img, lestnica_promahov(ks, tt), label("ОНА НАЗЫВАЛА ГОДЫ", C.seg(tt, 0.05, 0.4), 130, 40, C.GREY),
                              C.caption(*CAP_PROM, k=1.0)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 88 · база в Сербии ═════════════════════════
@scene("88")
def s88(t, dur):
    c_baza = rel("88", 519.0)

    def a(tt, d):
        base = K.base(BALKAN, hot="Republic of Serbia")
        base = zoom_at(base, 1.08 + 0.05 * tt / d, W * 0.5, H * 0.5)
        x, y = BALKAN.xy(20.46, 44.80)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        kb = C.seg(tt, c_baza, c_baza + 0.6)
        if kb > 0:
            a = int(255 * C.smoother(kb))
            for j in range(3):
                ph = (tt * 0.8 + j * 0.33) % 1.0
                r = (10 + 90 * ph) * SS
                dd.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], outline=C.RED + (int(a * (1 - ph)),), width=3 * SS)
            C.tracked(dd, x * SS, (y - 30) * SS, "?", C.font("head", 120 * SS), C.RED + (a,), 0.0, "ms")
        return C.over(base, C.done(lay), K.city_layer(["Белград"], C.seg(tt, 0.2, 0.6), BALKAN, 28, {"Белград": "r"}),
                      label("ЗАПИСЬ 2019 ГОДА", C.seg(tt, 0.05, 0.4), 130, 40, C.GREY, x=SAFE_X, anchor="ls"),
                      word("РОССИЙСКАЯ ВОЕННАЯ БАЗА В СЕРБИИ", kb, H - 150, 64, "head", C.WHITE, 0.12, x=SAFE_X, anchor="ls", rise=24),
                      C.caption(*CAP_KARTA, k=1.0)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 89 · штампы бьют · не сбылось ничего ═════════════════════════
@scene("89")
def s89(t, dur):
    c_ne = rel("89", 520.91)

    def a(tt, d):
        img = C.kb(dark_bg(82), (tt + 9.6) / 10.0, 0.04, 0.5, 0.5)
        lays = [lestnica_promahov([1.0] * 6, tt + 9.6, stamps=[C.seg(tt, 0.05 + i * 0.16, 0.3 + i * 0.16) for i in range(6)])]
        kn = C.seg(tt, c_ne + 0.5, c_ne + 0.9)
        lays.append(word("НИЧЕГО", kn, H - 120, 120, "head", C.RED, 0.14, x=W - SAFE_X, anchor="rs", rise=30))
        lays.append(C.caption(*CAP_PROM, k=1.0))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 90 · вот что бросается в глаза ═════════════════════════
@scene("90")
def s90(t, dur):
    c_vot = rel("90", 522.31)

    def a(tt, d):
        img = board6(t, 40.0 + tt * 1.6, [("promahi", C.seg(tt, 0.2, 0.8), C.seg(tt, 0.5, 1.2))], threads=[("promahi", 0, C.seg(tt, 0.9, 1.5))], amp=520.0, dark=0.07)
        z = 1.15 + 0.15 * C.smoother(C.seg(tt, 0, d))
        img = zoom_at(img, z, W * 0.35, H * 0.5)
        return C.over(img, word("ВОТ ЧТО БРОСАЕТСЯ В ГЛАЗА", C.seg(tt, c_vot, c_vot + 0.45), H - 130, 72, "head", C.WHITE, 0.12, rise=24)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 91 · с точной датой — мимо · 92 · где даты нет ═════════════════════════
LEFT = [("2017", "Курдистан"), ("2018", "раскол Германии"), ("2019", "распад Испании"), ("2020", "распад Боснии"), ("2019", "база в Сербии")]
RIGHT = [("армия войдёт в Украину", "сбылось"), ("пожизненный президент", "закон позволяет"), ("дочери-политики", "ждёт")]


@scene("91")
def s91(t, dur):
    c_mimo = rel("91", 526.2)

    def a(tt, d):
        img = C.kb(dark_bg(83), tt / 6.0, 0.04, 0.5, 0.5)
        lay = sortirovka(C.seg(tt, 0.1, 1.6), 0.0, C.seg(tt, c_mimo - 0.3, c_mimo + 0.6), 0.0, tt)
        return C.grain(C.over(img, lay, label("ВСЕ ЕЁ ПРЕДСКАЗАНИЯ С ТОЧНОЙ ДАТОЙ", C.seg(tt, 0.05, 0.45), 110, 36, C.WHITE),
                              word("МИМО", C.seg(tt, c_mimo, c_mimo + 0.4), H - 110, 110, "head", C.RED, 0.14, x=W * 0.27, rise=28)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


@scene("92")
def s92(t, dur):
    c_net = rel("92", 528.23)

    def a(tt, d):
        img = C.kb(dark_bg(83), (tt + 2.94) / 6.0, 0.04, 0.5, 0.5)
        lay = sortirovka(1.0, C.seg(tt, 0.1, 1.3), 1.0, C.seg(tt, c_net, c_net + 0.6), tt + 2.94)
        return C.grain(C.over(img, lay, label("ПОПАДАЕТ ОНА ТАМ", C.seg(tt, 0.05, 0.45), 110, 36, C.WHITE),
                              word("ГДЕ ДАТЫ НЕТ", C.seg(tt, c_net, c_net + 0.4), H - 110, 96, "head", C.WHITE, 0.14, x=W * 0.73, rise=28)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 93 · направление · намерение ═════════════════════════
@scene("93")
def s93(t, dur):
    c_nam = rel("93", 531.48)

    def a(tt, d):
        img = C.kb(dark_bg(84), tt / 4.0, 0.05, 0.5, 0.5)
        lay = kompas(C.seg(tt, 0.1, 2.0), tt)
        return C.grain(C.over(img, lay, label("ТАМ, ГДЕ РЕЧЬ О", C.seg(tt, 0.05, 0.4), 130, 36, C.GREY),
                              word("НАПРАВЛЕНИИ", C.seg(tt, 0.5, 0.95), H - 190, 96, "head", C.WHITE, 0.14, rise=28),
                              word("О НАМЕРЕНИИ", C.seg(tt, c_nam, c_nam + 0.4), H - 100, 60, "head_l", C.RED, 0.16, rise=20)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 94 · пророк видит день и час ═════════════════════════
@scene("94")
def s94(t, dur):
    c_pror = rel("94", 532.68)

    def a(tt, d):
        img = C.kb(dark_bg(85), tt / 4.0, 0.05, 0.5, 0.5)
        lay = tsiferblat(C.seg(tt, 0.1, 2.4), tt)
        return C.grain(C.over(img, lay, label("ПРОРОК ВИДИТ", C.seg(tt, c_pror, c_pror + 0.4), 130, 40, C.GREY),
                              word("ДЕНЬ И ЧАС", C.seg(tt, c_pror + 0.6, c_pror + 1.0), H - 120, 96, "head", C.WHITE, 0.14, rise=28)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 95 · знаком с планами ═════════════════════════
@scene("95")
def s95(t, dur):
    c_tot = rel("95", 535.6)

    def a(tt, d):
        img = chertezh(C.seg(tt, 0.0, 2.4), tt)
        return C.over(img, label("НАПРАВЛЕНИЕ ЗНАЕТ ТОТ", C.seg(tt, 0.05, 0.4), 130, 40, C.GREY),
                      word("КТО ЗНАКОМ С ПЛАНАМИ", C.seg(tt, c_tot, c_tot + 0.45), H - 150, 80, "head", C.WHITE, 0.12, rise=26),
                      C.caption(*CAP_SHEMA, k=1.0)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.6, grain_k=0.03, vig=0.3)


# ═════════════════════════ 96 · пауза 2 с · Верица без слов 3 с ═════════════════════════
@scene("96")
def s96(t, dur):
    def a_dark(tt, d):
        img = board6(t, 50.0 + tt, amp=200.0, dark=0.05)
        img = C.fade(zoom_at(img, 1.6, W * 0.5, H * 0.5), 0.5)
        return C.grain(img, t, 0.04)

    def b_verica(tt, d):
        img = verica("v04c", "v04_krupno_0240.mp4", tt, push=0.10, hand=2.5)
        return flash(C.over(img, C.caption(*CAP_V, k=C.seg(tt, 0.2, 0.7))).convert("RGB"), tt, 0.06, 0.3)

    fn, tt, d = shots(t, [(0.0, a_dark), (2.0, b_verica)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.5, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 97 · вернёмся к вопросу · зачем оператор ═════════════════════════
@scene("97")
def s97(t, dur):
    c_zach = rel("97", 539.27)

    def a(tt, d):
        img, z = board_card(t, tt, "zachem", 1.6, 2.2)
        kz = C.seg(tt, c_zach, c_zach + 0.45)
        return flash(C.over(img, label("ВЕРНЁМСЯ К ВОПРОСУ ИЗ НАЧАЛА", C.seg(tt, 0.05, 0.45), 130, 40, C.WHITE),
                            word("ЗАЧЕМ ГОСУДАРСТВУ ОПЕРАТОР РЯДОМ С ЯСНОВИДЯЩЕЙ?", kz, H - 150, 64, "head", C.WHITE, 0.1, rise=24)).convert("RGB"), tt, 0.08, 0.4)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 98 · Болгария · Ванга ═════════════════════════
@scene("98")
def s98(t, dur):
    c_vanga = rel("98", 543.64)

    def a(tt, d):
        base = K.base(BULG, hot="")
        lay = strana_layer(("Bulgaria",), BULG, C.seg(tt, 0.1, 0.8), C.RED, 110)
        img = zoom_at(C.over(base, lay).convert("RGB"), 1.05 + 0.08 * tt / d, W * 0.5, H * 0.5)
        return C.over(img, label("БОЛГАРИЯ", C.seg(tt, 0.05, 0.4), 150, 64, C.WHITE, x=SAFE_X, anchor="ls", track=0.2),
                      word("ВАНГА", C.seg(tt, c_vanga, c_vanga + 0.4), H - 150, 150, "head", C.WHITE, 0.14, x=SAFE_X, anchor="ls", rise=36),
                      C.caption(*CAP_KARTA, k=1.0)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 99-102 · досье Ванги ═════════════════════════
VANGA = ["с 1967 года — на государственной службе", "с зарплатой", "её изучает институт при Академии наук", "к ней едут первые лица"]


def vanga_sheet(tt, t, k_in, ks, zoom=1.0, note=0.0):
    img = lamp_bg(49).convert("RGBA")
    w, h = 1240, 720
    sheet = C.paper(w, h, seed=141, tone=(200, 190, 170), dark=0.0).convert("RGBA")
    d = ImageDraw.Draw(sheet)
    d.rectangle([0, 0, w - 1, h - 1], outline=(110, 100, 86, 255), width=3)
    d.line([(60, 150), (w - 60, 150)], fill=(110, 100, 86, 255), width=2)
    d.text((60, 118), "ВАНГА", font=C.font("head", 64), fill=C.INK + (255,), anchor="ls")
    d.text((w - 60, 118), "Болгария · по публикациям", font=C.font("serif_i", 36), fill=(110, 100, 86, 255), anchor="rs")
    y = 240
    for ln, k in zip(VANGA, ks):
        n = int(len(ln) * C.clamp(k))
        if n > 0:
            d.text((60, y), ln[:n], font=C.font("serif", 44), fill=C.INK + (255,), anchor="ls")
        y += 100
    if note > 0:
        sheet = Image.alpha_composite(sheet, rukopis("полвека", note, 760, 640, 56, (w, h), angle=-5.0, heavy=True))
    kk = C.out_cubic(k_in)
    x0, y0 = int(W / 2 - w / 2), int(H * 0.52 - h / 2 + (1 - kk) * 400)
    sh, sx, sy = fx.shadow_of((w, h), W / 2, -300, x0 + w / 2, y0 + h / 2, blur=24, a=180)
    img.alpha_composite(sh, (sx, sy))
    img.alpha_composite(C.alpha(sheet, C.clamp(k_in * 2)), (x0, y0))
    out = img.convert("RGB")
    if zoom > 1.0:
        out = zoom_at(out, zoom, W / 2, H * 0.52)
    out = fx.fonar(out, W * 0.5, H * 0.5, 940, 580, 0.10, 0.045, t)
    return C.grain(out, t, 0.03)


@scene("99")
def s99(t, dur):
    def a(tt, d):
        img = vanga_sheet(tt, t, C.seg(tt, 0.1, 0.9), [C.seg(tt, 0.6, 2.6), 0, 0, 0])
        return C.over(img, C.caption(*CAP_VANGA, k=1.0)).convert("RGB")
    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


@scene("100")
def s100(t, dur):
    def a(tt, d):
        img = vanga_sheet(tt, t, 1.0, [1, C.seg(tt, 0.1, 0.7), 0, 0], 1.0 + 0.05 * C.smoother(tt / d))
        return C.over(img, label("С ЗАРПЛАТОЙ", C.seg(tt, 0.3, 0.7), H - 130, 54, C.WHITE, track=0.3), C.caption(*CAP_VANGA, k=1.0)).convert("RGB")
    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


@scene("101")
def s101(t, dur):
    def a(tt, d):
        img = vanga_sheet(tt, t, 1.0, [1, 1, C.seg(tt, 0.1, 1.9), 0], 1.05)
        return C.over(img, C.caption(*CAP_VANGA, k=1.0)).convert("RGB")
    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


@scene("102")
def s102(t, dur):
    def a(tt, d):
        img = vanga_sheet(tt, t, 1.0, [1, 1, 1, C.seg(tt, 0.1, 1.3)], 1.05 + 0.03 * tt / d)
        return C.over(img, C.caption(*CAP_VANGA, k=1.0)).convert("RGB")
    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 103 · полвека · рядом всегда были спецслужбы ═════════════════════════
@scene("103")
def s103(t, dur):
    c_to = rel("103", 557.51)
    c_ryadom = rel("103", 558.3)

    def a_polveka(tt, d):
        img = vanga_sheet(tt, t, 1.0, [1, 1, 1, 1], 1.08, note=C.seg(tt, 0.2, 1.2))
        return C.over(img, label("УЖЕ ПОЛВЕКА О НЕЙ ГОВОРЯТ ТО ЖЕ", C.seg(tt, 0.3, 0.7), H - 130, 40, C.WHITE), C.caption(*CAP_VANGA, k=1.0)).convert("RGB")

    def b_dve(tt, d):
        img = board6(t, 60.0 + tt, [("vanga", C.seg(tt, 0.0, 0.6), C.seg(tt, 0.3, 1.0))], threads=[("vanga", "zachem", C.seg(tt, c_ryadom - c_to, c_ryadom - c_to + 0.8))], amp=300.0)
        img = zoom_at(img, 1.3 - 0.1 * C.smoother(tt / d), W * 0.72, H * 0.68)
        return flash(C.over(img, label("ЧТО О ВЕРИЦЕ", C.seg(tt, 0.05, 0.4), 130, 40, C.WHITE),
                            word("РЯДОМ ВСЕГДА БЫЛИ СПЕЦСЛУЖБЫ", C.seg(tt, c_ryadom - c_to, c_ryadom - c_to + 0.45), H - 130, 72, "head", C.WHITE, 0.12, rise=24)).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_polveka), (c_to, b_dve)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 104 · их всех подозревают · 105 · а если не зря? ═════════════════════════
@scene("104")
def s104(t, dur):
    c_ih = rel("104", 560.19)

    def a(tt, d):
        img = board6(t, 70.0 + tt * 1.4, [("vanga", 1, 1)], amp=480.0, dark=0.06)
        img = zoom_at(img, 1.05 + 0.05 * tt / d, W * 0.5, H * 0.5)
        return C.over(img, word("ИХ ВСЕХ ПОДОЗРЕВАЮТ", C.seg(tt, c_ih, c_ih + 0.45), H * 0.5 + 40, 110, "head", C.WHITE, 0.12, rise=30)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.35)


@scene("105")
def s105(t, dur):
    c_esli = rel("105", 561.65)

    def a(tt, d):
        img = C.kb(dark_bg(86), tt / 4.0, 0.05, 0.5, 0.5)
        fl = 0.75 + 0.25 * (0.5 + 0.5 * math.sin(tt * 23.0) * math.sin(tt * 7.1))
        img = C.fade(img, fl)
        return C.grain(C.over(img, label("А ЕСЛИ ПОДОЗРЕВАЮТ", C.seg(tt, c_esli, c_esli + 0.4), H * 0.5 - 120, 48, C.GREY),
                              word("НЕ ЗРЯ?", C.seg(tt, c_esli + 0.6, c_esli + 1.0), H * 0.5 + 110, 170, "head", C.RED, 0.12, rise=36)).convert("RGB"), t, 0.05)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 106 · не пророки · носители информации ═════════════════════════
@scene("106")
def s106(t, dur):
    c_nos = rel("106", 564.65)

    def a(tt, d):
        img = C.kb(dark_bg(87), tt / 3.0, 0.05, 0.5, 0.5)
        img = perepis(img, C.seg(tt, 0.2, 1.2), C.seg(tt, c_nos, c_nos + 1.2), tt, t)
        return C.grain(img, t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 107 · с трибуны нельзя · через них можно ═════════════════════════
@scene("107")
def s107(t, dur):
    c_nelz = rel("107", 568.0)

    def a(tt, d):
        img = C.kb(dark_bg(88), tt / 4.0, 0.04, 0.5, 0.5)
        lay = tribuna(C.seg(tt, 0.1, 0.8), C.seg(tt, c_nelz - 0.3, c_nelz + 0.3), C.seg(tt, 0.6, 2.4), tt)
        return C.grain(C.over(img, lay, label("ЧЕРЕЗ НИХ МОЖНО СКАЗАТЬ ТО,", C.seg(tt, 0.05, 0.45), 130, 40, C.WHITE),
                              word("ЧТО НЕЛЬЗЯ СКАЗАТЬ С ТРИБУНЫ", C.seg(tt, c_nelz, c_nelz + 0.45), H - 130, 64, "head", C.WHITE, 0.12, rise=24),
                              C.caption(*CAP_SHEMA, k=1.0)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 108 · проверить, как отзовётся · подготовить ═════════════════════════
@scene("108")
def s108(t, dur):
    c_podg = rel("108", 571.37)

    def a(tt, d):
        img = C.kb(dark_bg(89), tt / 3.0, 0.04, 0.5, 0.5)
        lay = eho_radar(C.seg(tt, 0.1, 1.7), tt)
        return C.grain(C.over(img, lay, label("ПРОВЕРИТЬ, КАК ОТЗОВЁТСЯ", C.seg(tt, 0.05, 0.45), 130, 44, C.WHITE),
                              word("ПОДГОТОВИТЬ", C.seg(tt, c_podg, c_podg + 0.4), H - 130, 96, "head", C.RED, 0.14, rise=28)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 109 · это версия · доказательств нет ═════════════════════════
@scene("109")
def s109(t, dur):
    c_dok = rel("109", 573.22)

    def a(tt, d):
        img = lamp_bg(50).convert("RGBA")
        w, h = 1100, 520
        sheet = C.paper(w, h, seed=151, tone=(200, 190, 170), dark=0.0).convert("RGBA")
        dd = ImageDraw.Draw(sheet)
        dd.rectangle([0, 0, w - 1, h - 1], outline=(110, 100, 86, 255), width=3)
        dd.text((60, 118), "ВЕРСИЯ", font=C.font("head", 72), fill=C.INK + (255,), anchor="ls")
        dd.line([(60, 150), (w - 60, 150)], fill=(110, 100, 86, 255), width=2)
        kd = C.seg(tt, c_dok + 0.1, c_dok + 1.0)
        ln = "доказательств — нет"
        n = int(len(ln) * kd)
        if n > 0:
            dd.text((60, 290), ln[:n], font=C.font("serif", 56), fill=C.INK + (255,), anchor="ls")
        kk = C.out_cubic(C.seg(tt, 0.1, 0.8))
        x0, y0 = int(W / 2 - w / 2), int(H * 0.5 - h / 2 + (1 - kk) * 400)
        sh, sx, sy = fx.shadow_of((w, h), W / 2, -300, x0 + w / 2, y0 + h / 2, blur=24, a=180)
        img.alpha_composite(sh, (sx, sy))
        img.alpha_composite(C.alpha(sheet, C.clamp(kk * 2)), (x0, y0))
        out = fx.fonar(img.convert("RGB"), W * 0.5, H * 0.5, 900, 540, 0.10, 0.045, t)
        return C.grain(C.over(out, label("ЭТО ВЕРСИЯ", C.seg(tt, 0.3, 0.7), H - 110, 40, C.GREY)).convert("RGB"), t, 0.03)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 110 · но она объясняет всё ═════════════════════════
@scene("110")
def s110(t, dur):
    c_arm = rel("110", 576.22)
    c_dat = rel("110", 578.09)
    c_op = rel("110", 579.31)

    def a(tt, d):
        th = [("ross", "kto", C.seg(tt, c_arm, c_arm + 0.7)), ("promahi", "kto", C.seg(tt, c_dat, c_dat + 0.7)), ("zachem", "kto", C.seg(tt, c_op, c_op + 0.7))]
        img = board6(t, 80.0 + tt, [("promahi", 1, 1), ("vanga", 1, 1), ("kto", C.seg(tt, 0.1, 0.6), 0.0)], threads=th, amp=320.0)
        img = zoom_at(img, 1.12 - 0.08 * C.smoother(tt / d), W * 0.5, H * 0.55)
        return C.over(img, label("НО ОНА ОБЪЯСНЯЕТ ВСЁ", C.seg(tt, 0.05, 0.45), H - 240, 40, C.WHITE, x=SAFE_X, anchor="ls"),
                      label("ТОЧНОЕ СЛОВО ПРО АРМИЮ", C.seg(tt, c_arm, c_arm + 0.4), H - 190, 34, C.WHITE, x=SAFE_X, anchor="ls"),
                      label("ОШИБКИ В ДАТАХ", C.seg(tt, c_dat, c_dat + 0.4), H - 145, 34, C.WHITE, x=SAFE_X, anchor="ls"),
                      label("ОПЕРАТОРА", C.seg(tt, c_op, c_op + 0.4), H - 100, 34, C.WHITE, x=SAFE_X, anchor="ls")).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.6, grain_k=0.03, vig=0.3)


# ═════════════════════════ 111 · снова страница блога · две строки ═════════════════════════
@scene("111")
def s111(t, dur):
    c_dve = rel("111", 584.00)

    def a(tt, d):
        sc = 2.1 + 0.03 * tt
        img, geo = page_view(6895, sc, 805)
        b1, b2 = to_frame(LINE_PUTIN, geo), to_frame(LINE_DAUGHTERS, geo)
        k = C.smoother(C.seg(tt, 0.0, 2.0))
        img = fx.fonar(img, W * 0.5, C.lerp(b1[1] - 200, (b1[1] + b2[3]) / 2, k), 640, C.lerp(260, 420, k), 0.08, 0.05, t)
        img = page_dark(img, t)
        kd = C.seg(tt, c_dve, c_dve + 0.5)
        return C.over(img, red_line(kd, b1[0] - 8, b1[2] + 8, b1[3] + 10, 4), red_line(C.seg(tt, c_dve + 0.3, c_dve + 0.8), b2[0] - 8, b2[2] + 8, b2[3] + 10, 4),
                      K.date_tag("25.05.2016", C.seg(tt, 2.0, 2.5), sub="маленький блог"),
                      word("ДВЕ СТРОКИ", kd, H - 150, 80, "head", C.WHITE, 0.12, rise=24),
                      C.caption(*CAP_B, k=C.seg(tt, 1.2, 1.8))).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.6, fo=0.0, grain_k=0.0, vig=0.3)


@scene("112")
def s112(t, dur):
    def a(tt, d):
        sc = 2.5 + 0.04 * tt
        img, geo = page_view(6759, sc, 805)
        b1 = to_frame(LINE_PUTIN, geo)
        img = fx.fonar(img, (b1[0] + b1[2]) / 2, (b1[1] + b1[3]) / 2 + 30, 640, 300, 0.10, 0.05, t)
        img = page_dark(img, t)
        return flash(C.over(img, red_line(1.0, b1[0] - 8, b1[2] + 8, b1[3] + 10, 5),
                            label("ПЕРВАЯ", C.seg(tt, 0.05, 0.4), 130, 46, C.WHITE),
                            word("СБЫВАЕТСЯ У НАС НА ГЛАЗАХ", C.seg(tt, 0.5, 0.95), H - 150, 72, "head", C.WHITE, 0.12, rise=24),
                            C.caption(*CAP_B, k=1.0)).convert("RGB"), tt, 0.06, 0.3)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


@scene("113")
def s113(t, dur):
    c_zhd = rel("113", 589.46)

    def a(tt, d):
        sc = 2.5 + 0.04 * tt
        img, geo = page_view(7037, sc, 805)
        b2 = to_frame(LINE_DAUGHTERS, geo)
        img = fx.fonar(img, (b2[0] + b2[2]) / 2, (b2[1] + b2[3]) / 2 + 30, 640, 300, 0.10, 0.05, t)
        img = page_dark(img, t)
        kz = C.seg(tt, c_zhd, c_zhd + 0.4)
        return flash(C.over(img, red_line(1.0, b2[0] - 8, b2[2] + 8, b2[3] + 10, 5),
                            label("ВТОРАЯ · ПРО ДОЧЕРЕЙ", C.seg(tt, 0.05, 0.4), 130, 46, C.WHITE),
                            word("ЖДЁТ", kz, H - 150, 110, "head", C.WHITE, 0.14, rise=30),
                            fx.cursor(W / 2 + 190, H - 150, 90, tt, 6, 1.0, C.RED) if kz >= 1 else None,
                            C.caption(*CAP_B, k=1.0)).convert("RGB"), tt, 0.06, 0.3)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 114 · не пророком, а голосом · 115 · кто и зачем ═════════════════════════
@scene("114")
def s114(t, dur):
    c_ne = rel("114", 591.6)
    c_gol = rel("114", 592.90)

    def a(tt, d):
        img = verica("v03c", "v03_krupno_0100.mp4", tt, push=0.10, hand=2.5, k_grade=1.0)
        img = C.fade(img, 0.75)
        return C.over(img, label("И ЕСЛИ ВЕРИЦА ОБРЕНОВИЧ БЫЛА", C.seg(tt, 1.5, 1.9), 130, 40, C.GREY),
                      word("НЕ ПРОРОКОМ", C.seg(tt, c_ne, c_ne + 0.45), H * 0.5 + 40, 110, "head", C.WHITE, 0.14, rise=30),
                      word("А ГОЛОСОМ", C.seg(tt, c_gol, c_gol + 0.45), H * 0.5 + 180, 110, "head", C.RED, 0.14, rise=30),
                      C.caption(*CAP_V, k=1.0)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.5, fo=0.0, grain_k=0.03, vig=0.3)


@scene("115")
def s115(t, dur):
    c_sbud = rel("115", 595.43)
    c_kto = rel("115", 597.60)
    c_10 = rel("115", 599.3)

    def a_vopros(tt, d):
        img = C.kb(dark_bg(90), tt / 4.0, 0.05, 0.5, 0.5)
        return C.grain(C.over(img, label("ГЛАВНЫЙ ВОПРОС НЕ В ТОМ,", C.seg(tt, 0.1, 0.5), H * 0.5 - 100, 48, C.GREY),
                              word("СБУДЕТСЯ ЛИ ЭТО", C.seg(tt, c_sbud, c_sbud + 0.45), H * 0.5 + 80, 130, "head_l", C.WHITE, 0.12, rise=30),
                              roscherk(C.seg(tt, c_sbud + 0.8, c_sbud + 1.3), 13)).convert("RGB"), t, 0.04)

    def b_kto(tt, d):
        img = board6(t, 90.0 + tt * 1.5, [("promahi", 1, 1), ("vanga", 1, 1), ("kto", 1, C.seg(tt, 0.1, 0.9))], threads=[("ross", "kto", 1.0), ("promahi", "kto", 1.0), ("zachem", "kto", 1.0)], amp=420.0)
        img = zoom_at(img, 1.5 + 0.3 * C.smoother(tt / d), W * 0.5, H * 0.5)
        return flash(C.over(img, word("КТО И ЗАЧЕМ", C.seg(tt, 0.05, 0.5), 160, 120, "head", C.WHITE, 0.14, rise=30),
                            word("СКАЗАЛ ЕЙ ЭТО ДЕСЯТЬ ЛЕТ НАЗАД", C.seg(tt, c_10 - c_kto, c_10 - c_kto + 0.45), H - 130, 60, "head", C.WHITE, 0.12, rise=20)).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_vopros), (c_kto, b_kto)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.8, grain_k=0.0, vig=0.3)


# ═════════════════════════ 116 · взгляд в камеру · полная тишина ═════════════════════════
@scene("116")
def s116(t, dur):
    img = verica("v10c", "v10_v_kameru_4350.mp4", t, push=0.05, hand=1.5, k_grade=0.9)
    return C.finish(C.over(img, C.caption(*CAP_V, k=C.seg(t, 0.4, 1.0))).convert("RGB"), t, dur, fi=0.6, fo=0.8, grain_k=0.03, vig=0.35)


# ═════════════════════════ 117 · пророк или источник · я посчитаю ═════════════════════════
@scene("117")
def s117(t, dur):
    c_pror = rel("117", 603.14)
    c_ist = rel("117", 603.89)
    c_posch = rel("117", 604.95)

    def a(tt, d):
        img = C.kb(dark_bg(91), tt / 5.0, 0.04, 0.5, 0.5)
        lay = schyot_palochek(C.seg(tt, c_pror, c_pror + 0.4), C.seg(tt, c_ist, c_ist + 0.4), C.seg(tt, c_posch, c_posch + 1.4), tt)
        return C.grain(C.over(img, lay, label("НАПИШИТЕ В КОММЕНТАРИЯХ ОДНО СЛОВО", C.seg(tt, 0.05, 0.5), 150, 40, C.WHITE),
                              label("Я ПОСЧИТАЮ", C.seg(tt, c_posch, c_posch + 0.4), H - 110, 40, C.GREY)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.4, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 118 · титры источников ═════════════════════════
TITRY = [
    ("ИСТОЧНИКИ", ""),
    ("Интервью Верицы Обренович", "METANOJA TV · YouTube · опубликовано 21.04.2019"),
    ("Блог balkanprophecies.blogspot.com", "запись 25.05.2016 · копия веб-архива 08.07.2018"),
    ("Газета sd.rs", "статья от 27.06.2016 · скриншот страницы 23.11.2026"),
    ("Фильм «Путин»", "А. Кондрашов · 2018 · цитирование фрагмента"),
    ("Удостоверение МГБ ГДР", "Wikimedia Commons · общественное достояние"),
    ("Ангеликаштрассе, 4 · Дрезден", "фото Jörg Blobelt · CC BY-SA 4.0 · Brücke-Osteuropa · CC0"),
    ("Дрезден, декабрь 1989", "Bundesarchiv, Bild 183 · фото Ulrich Haessler, Matthias Hiekel · CC BY-SA 3.0 de"),
    ("Указ Президента РФ № 680", "kremlin.ru · Указ № 192 · pravo.gov.ru"),
    ("Итоги голосования 01.07.2020", "ЦИК России"),
    ("Карты", "Natural Earth · условные"),
    ("Музыка", "Jeremy Blake — Missing Persons, Final Girl · Godmode — To Pass Time · Incoming Transition"),
    ("Письмо 1987 года, план особняка, схемы", "реконструкция по публикациям · подлинников в кадре нет"),
    ("Голос", "ПЛАНЕТА · ОЛЬКА NEWS"),
]


@scene("118")
def s118(t, dur):
    img = board6(t, 100.0 + t * 0.6, [("promahi", 1, 1), ("vanga", 1, 1), ("kto", 1, 1)], amp=200.0, dark=0.05)
    img = C.fade(zoom_at(img, 1.3, W * 0.5, H * 0.5), 0.16).filter(ImageFilter.GaussianBlur(3))
    lay = titry(C.seg(t, 2.0, dur - 0.5), t)
    return C.finish(C.over(img, lay).convert("RGB"), t, dur, fi=0.8, fo=1.5, grain_k=0.03, vig=0.35)


# ═════════════════════════ fx6 — новые эффекты шестого куска ═════════════════════════
_shtamp = {}


def shtamp(text, k, cx, cy, angle=-8.0, color=C.RED, tt=0.0):
    """штамп: прилетает с высоты (масштаб 1,8→1), бьёт, краска с пропусками, в момент удара — пыль"""
    if k <= 0:
        return None
    key = (text, tuple(color))
    if key not in _shtamp:
        s = 2
        f = C.font("head", 84 * s)
        d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        tw = C.text_w(d0, text, f, 0.12)
        w, h = int(tw / 1 + 100 * s), 150 * s
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([4 * s, 4 * s, w - 4 * s, h - 4 * s], radius=14 * s, outline=color + (255,), width=6 * s)
        C.tracked(d, w / 2, h / 2 + 30 * s, text, f, color + (255,), 0.12, "ms")
        n = np.asarray(C.noise(w, h, 71, 1.3), np.float32) / 255.0
        n2 = np.asarray(C.noise(w, h, 72, 6.0), np.float32) / 255.0
        al = np.asarray(im.getchannel("A"), np.float32) * np.clip(0.35 + 0.9 * n * (0.6 + 0.6 * n2), 0, 1)
        im.putalpha(Image.fromarray(np.clip(al, 0, 255).astype(np.uint8), "L"))
        _shtamp[key] = im.resize((w // s, h // s), Image.LANCZOS)
    im = _shtamp[key]
    kk = C.out_expo(k)
    sc = 1.8 - 0.8 * kk
    rot = im.rotate(angle, Image.BICUBIC, expand=True)
    if sc != 1.0:
        rot = rot.resize((max(2, int(rot.size[0] * sc)), max(2, int(rot.size[1] * sc))), Image.LANCZOS)
    rot = C.alpha(rot, C.clamp(k * 3) * (0.55 + 0.45 * kk))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(rot, (int(cx - rot.size[0] / 2), int(cy - rot.size[1] / 2)))
    if 0.85 < k < 1.0:
        dust = C.layer()
        dd = ImageDraw.Draw(dust)
        ph = (k - 0.85) / 0.15
        r = (40 + 220 * ph) * SS
        dd.ellipse([cx * SS - r, cy * SS - r * 0.45, cx * SS + r, cy * SS + r * 0.45], outline=(230, 225, 215, int(160 * (1 - ph))), width=int(6 * SS * (1 - ph) + 1))
        out = Image.alpha_composite(out, C.done(dust))
    return out


def lestnica_promahov(ks, tt, stamps=None):
    """промахи строками: год красным слева, пункт серым; stamps — доли удара штампа НЕ СБЫЛОСЬ по строкам"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    f_y = C.font("head", 64 * s)
    f_p = C.font("serif_i", 44 * s)
    rows = []
    for i, ((yr, txt), k) in enumerate(zip(PROMAHI, ks)):
        if k <= 0:
            continue
        a = int(255 * C.smoother(k))
        y = H * 0.27 + i * 112 + (1 - C.out_cubic(k)) * 30
        C.tracked(d, (SAFE_X + 220) * s, y * s, yr, f_y, C.RED + (a,), 0.04, "rs")
        C.tracked(d, (SAFE_X + 270) * s, (y - 4) * s, txt, f_p, C.WHITE + (int(a * 0.85),), 0.0, "ls")
        d.line([((SAFE_X + 40) * s, (y + 24) * s), ((W - SAFE_X - 40) * s, (y + 24) * s)], fill=(60, 60, 66, a), width=1 * s)
        rows.append((i, y))
    out = C.done(lay)
    if stamps:
        for i, y in rows:
            k = stamps[i] if i < len(stamps) else 0.0
            st = shtamp("НЕ СБЫЛОСЬ", k, W * 0.72 + (i % 2) * 60, y - 10, -6.0 + (i % 3) * 5, C.RED, tt)
            if st is not None:
                out = Image.alpha_composite(out, st)
    return out


def sortirovka(k_left, k_right, k_strike, k_dots, tt):
    """два столбца: С ДАТОЙ (слева, строки влетают и перечёркиваются) и БЕЗ ДАТЫ (справа, точки)"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    k_div = C.clamp(max(k_left, k_right) * 2)
    d.rectangle([(W / 2 - 2) * s, (H * 0.5 - H * 0.36 * k_div) * s, (W / 2 + 2) * s, (H * 0.5 + H * 0.36 * k_div) * s], fill=C.GREY2 + (255,))
    f_h = C.font("head_l", 36 * s)
    f_y = C.font("head", 48 * s)
    f_t = C.font("serif_i", 38 * s)
    a_h = int(255 * k_div)
    C.tracked(d, (W * 0.27) * s, (H * 0.2) * s, "С ТОЧНОЙ ДАТОЙ", f_h, C.WHITE + (a_h,), 0.3, "ms")
    C.tracked(d, (W * 0.73) * s, (H * 0.2) * s, "БЕЗ ДАТЫ", f_h, C.WHITE + (a_h,), 0.3, "ms")
    n = len(LEFT)
    for i, (yr, txt) in enumerate(LEFT):
        ki = C.seg(k_left, i / n, (i + 1) / n + 0.1)
        if ki <= 0:
            continue
        a = int(255 * C.smoother(ki))
        x = SAFE_X + 40 + (1 - C.out_cubic(ki)) * 500
        y = H * 0.30 + i * 96
        C.tracked(d, x * s, y * s, yr, f_y, C.RED + (a,), 0.04)
        C.tracked(d, (x + 130) * s, (y - 4) * s, txt, f_t, C.WHITE + (a,), 0.0)
        ks = C.seg(k_strike, i / n, (i + 1) / n + 0.1)
        if ks > 0:
            x1 = x + (560) * C.out_cubic(ks)
            d.line([((x - 10) * s, (y - 16) * s), (x1 * s, (y - 20) * s)], fill=C.RED + (240,), width=6 * s)
    m = len(RIGHT)
    for i, (txt, sub) in enumerate(RIGHT):
        ki = C.seg(k_right, i / m, (i + 1) / m + 0.1)
        if ki <= 0:
            continue
        a = int(255 * C.smoother(ki))
        x = W / 2 + 70 - (1 - C.out_cubic(ki)) * 500
        y = H * 0.30 + i * 130
        C.tracked(d, x * s, y * s, txt, C.font("head_r", 42 * s), C.WHITE + (a,), 0.04)
        C.tracked(d, x * s, (y + 40) * s, sub.upper(), C.font("head_l", 26 * s), C.GREY + (a,), 0.24)
        kd = C.seg(k_dots, i / m, (i + 1) / m + 0.1)
        if kd > 0:
            r = 12 * s * C.out_back(kd)
            d.ellipse([(x - 40) * s - r, (y - 14) * s - r, (x - 40) * s + r, (y - 14) * s + r], fill=C.WHITE + (255,))
    return C.done(lay)


def kompas(k, tt):
    """стрелка компаса: кольцо с делениями, стрелка мечется и замирает вправо (направление)"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    cx, cy, R = W / 2, H * 0.5, 250
    a = int(255 * C.clamp(k * 3))
    d.ellipse([(cx - R) * s, (cy - R) * s, (cx + R) * s, (cy + R) * s], outline=(150, 150, 156, a), width=3 * s)
    for i in range(36):
        ang = i * 10
        L = 22 if i % 9 == 0 else 10
        x0, y0 = cx + (R - 4) * math.cos(math.radians(ang)), cy + (R - 4) * math.sin(math.radians(ang))
        x1, y1 = cx + (R - 4 - L) * math.cos(math.radians(ang)), cy + (R - 4 - L) * math.sin(math.radians(ang))
        d.line([(x0 * s, y0 * s), (x1 * s, y1 * s)], fill=(150, 150, 156, a), width=2 * s)
    # стрелка: затухающие колебания вокруг 0° (вправо)
    kk = C.clamp(k)
    swing = 140 * math.exp(-3.2 * kk) * math.sin(kk * 22.0) + 400 * (1 - C.smoother(min(1.0, kk * 1.3)))
    ang = math.radians(swing)
    tip = (cx + (R - 40) * math.cos(ang), cy + (R - 40) * math.sin(ang))
    tail = (cx - (R - 60) * math.cos(ang), cy - (R - 60) * math.sin(ang))
    px, py = -math.sin(ang) * 18, math.cos(ang) * 18
    d.polygon([(tip[0] * s, tip[1] * s), ((cx + px) * s, (cy + py) * s), ((cx - px) * s, (cy - py) * s)], fill=C.RED + (a,))
    d.polygon([(tail[0] * s, tail[1] * s), ((cx + px) * s, (cy + py) * s), ((cx - px) * s, (cy - py) * s)], fill=(200, 200, 206, a))
    d.ellipse([(cx - 10) * s, (cy - 10) * s, (cx + 10) * s, (cy + 10) * s], fill=C.WHITE + (a,))
    return C.done(lay)


def tsiferblat(k, tt):
    """циферблат: стрелки крутятся быстро, замедляются и встают; дата в окошке щёлкает"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    cx, cy, R = W / 2, H * 0.5, 250
    a = int(255 * C.clamp(k * 3))
    d.ellipse([(cx - R) * s, (cy - R) * s, (cx + R) * s, (cy + R) * s], outline=(150, 150, 156, a), width=3 * s)
    f = C.font("head_r", 30 * s)
    for i in range(12):
        ang = math.radians(i * 30 - 90)
        x, y = cx + (R - 36) * math.cos(ang), cy + (R - 36) * math.sin(ang)
        C.tracked(d, x * s, (y + 10) * s, str(12 if i == 0 else i), f, C.WHITE + (a,), 0.0, "ms")
    kk = C.clamp(k)
    spin = 1 - C.smoother(kk)
    hour = math.radians(-90 + 300 + 2000 * spin)
    minute = math.radians(-90 + 120 + 9000 * spin)
    for ang, L, wdt, col in ((hour, R * 0.55, 12, C.WHITE), (minute, R * 0.8, 7, C.RED)):
        d.line([(cx * s, cy * s), ((cx + L * math.cos(ang)) * s, (cy + L * math.sin(ang)) * s)], fill=col + (a,), width=wdt * s)
    d.ellipse([(cx - 12) * s, (cy - 12) * s, (cx + 12) * s, (cy + 12) * s], fill=C.WHITE + (a,))
    # окошко даты
    bx, by = cx + 110, cy
    d.rectangle([(bx - 40) * s, (by - 22) * s, (bx + 40) * s, (by + 22) * s], outline=(150, 150, 156, a), width=2 * s)
    day = int(1 + 30 * spin * 7) % 31 + 1
    C.tracked(d, bx * s, (by + 12) * s, "%02d" % day, C.font("head", 34 * s), C.RED + (a,), 0.0, "ms")
    return C.done(lay)


_chert = {}


def chertezh(k, tt):
    """чертёж: тёмное поле с сеткой, пунктирный маршрут по точкам с подписями «план», стрелка"""
    if "bg" not in _chert:
        im = Image.new("RGB", (W, H), (24, 31, 42))
        d = ImageDraw.Draw(im)
        for x in range(0, W, 60):
            d.line([(x, 0), (x, H)], fill=(44, 54, 70), width=1)
        for y in range(0, H, 60):
            d.line([(0, y), (W, y)], fill=(44, 54, 70), width=1)
        _chert["bg"] = C.vignette(im, 0.3)
    img = _chert["bg"].copy()
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    pts = [(W * 0.14, H * 0.70), (W * 0.30, H * 0.42), (W * 0.48, H * 0.56), (W * 0.66, H * 0.30), (W * 0.86, H * 0.40)]
    kk = C.out_cubic(k)
    total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    drawn = total * kk
    acc = 0.0
    for i in range(len(pts) - 1):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        L = math.dist(pts[i], pts[i + 1])
        if acc >= drawn:
            break
        frac = min(1.0, (drawn - acc) / L)
        xe, ye = xa + (xb - xa) * frac, ya + (yb - ya) * frac
        n = int(L * frac / 22)
        for j in range(n):
            u0, u1 = j * 22 / L, (j * 22 + 12) / L
            d.line([((xa + (xb - xa) * u0) * s, (ya + (yb - ya) * u0) * s), ((xa + (xb - xa) * u1) * s, (ya + (yb - ya) * u1) * s)], fill=(200, 205, 215, 255), width=3 * s)
        acc += L
    f = C.font("head_l", 26 * s)
    for i, (x, y) in enumerate(pts):
        ki = C.seg(k, i / len(pts), (i + 0.6) / len(pts))
        if ki <= 0:
            continue
        a = int(255 * C.smoother(ki))
        r = 9 * s
        d.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], outline=C.RED + (a,), width=3 * s)
        C.tracked(d, (x + 18) * s, (y - 16) * s, "ПУНКТ %d" % (i + 1), f, C.GREY + (a,), 0.24)
    if k >= 0.98:
        x, y = pts[-1]
        d.polygon([((x + 34) * s, y * s), ((x + 6) * s, (y - 14) * s), ((x + 6) * s, (y + 14) * s)], fill=C.RED + (255,))
    C.tracked(d, SAFE_X * s, (H - 230) * s, "ПЛАН", C.font("head", 54 * s), (200, 205, 215, int(255 * C.clamp(k * 3))), 0.3)
    return C.over(img, C.done(lay)).convert("RGB")


def perepis(img, k1, k2, tt, t):
    """«ПРОРОКИ» рвётся глитчем и зачёркивается; ниже печатается «НОСИТЕЛИ ИНФОРМАЦИИ»"""
    base = C.over(img, word("ЭТО НЕ ПРОРОКИ", C.clamp(k1 * 3), H * 0.5 - 40, 130, "head", C.WHITE, 0.12, rise=30)).convert("RGB")
    if 0.3 < k1 < 0.9:
        base = fx.glitch(base, 0.5 * math.sin(math.pi * (k1 - 0.3) / 0.6), seed=int(tt * 30), slices=12, shift=70, rgb=12)
    lays = [red_line(C.seg(k1, 0.55, 1.0), W / 2 - 520, W / 2 + 520, H * 0.5 - 84, 10)]
    if k2 > 0:
        lays.append(C.text_layer(["ЭТО"], "head_l", 40, C.GREY, W / 2, H * 0.5 + 90, "ms", 0.3, a=C.clamp(k2 * 3)))
        lays.append(fx.typed("НОСИТЕЛИ ИНФОРМАЦИИ", k2, "head", 110, C.RED, W / 2 - 640, H * 0.5 + 230, 0.08, True, t))
    return C.over(base, *lays).convert("RGB")


def tribuna(k_in, k_x, k_path, tt):
    """трибуна (вектор) с микрофоном, перечёркнутым красным; пунктирная дорожка обходит её по дуге"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    a = int(255 * C.smoother(k_in))
    cx, by = W * 0.5, H * 0.72
    col = (200, 200, 206, a)
    d.polygon([((cx - 150) * s, by * s), ((cx + 150) * s, by * s), ((cx + 120) * s, (by - 260) * s), ((cx - 120) * s, (by - 260) * s)], outline=col, width=4 * s)
    d.rectangle([(cx - 140) * s, (by - 290) * s, (cx + 140) * s, (by - 260) * s], outline=col, width=4 * s)
    d.line([(cx * s, (by - 290) * s), ((cx + 40) * s, (by - 400) * s)], fill=col, width=4 * s)
    d.ellipse([((cx + 40) - 22) * s, ((by - 400) - 22) * s, ((cx + 40) + 22) * s, ((by - 400) + 22) * s], fill=col)
    kx = C.out_cubic(k_x)
    if kx > 0:
        ax = int(255 * C.clamp(k_x * 3))
        d.line([((cx - 90) * s, (by - 470) * s), ((cx - 90 + 260 * kx) * s, (by - 470 + 200 * kx) * s)], fill=C.RED + (ax,), width=10 * s)
        d.line([((cx + 170) * s, (by - 470) * s), ((cx + 170 - 260 * kx) * s, (by - 470 + 200 * kx) * s)], fill=C.RED + (ax,), width=10 * s)
    # обходная дорожка: дуга слева снизу вокруг трибуны вправо
    kp = C.out_cubic(k_path)
    if kp > 0:
        n = int(60 * kp)
        for j in range(n):
            if j % 2:
                continue
            u0, u1 = j / 60, (j + 1) / 60
            p0 = (W * 0.08 + (W * 0.84) * u0, by + 120 - 520 * math.sin(math.pi * u0))
            p1 = (W * 0.08 + (W * 0.84) * u1, by + 120 - 520 * math.sin(math.pi * u1))
            d.line([(p0[0] * s, p0[1] * s), (p1[0] * s, p1[1] * s)], fill=C.RED + (255,), width=5 * s)
        if kp >= 0.99:
            x, y = W * 0.92, by + 120
            d.polygon([((x + 30) * s, y * s), ((x - 2) * s, (y - 14) * s), ((x - 2) * s, (y + 14) * s)], fill=C.RED + (255,))
        C.tracked(d, (W * 0.12) * s, (by + 170) * s, "ЧЕРЕЗ НИХ", C.font("head_r", 30 * s), C.RED + (int(255 * C.clamp(k_path * 3)),), 0.2)
    C.tracked(d, cx * s, (by + 60) * s, "ТРИБУНА", C.font("head_l", 30 * s), C.GREY + (a,), 0.3, "ms")
    return C.done(lay)


def eho_radar(k, tt):
    """эхо-радар: из точки слева уходят кольца; отклик возвращается точкой с правого края"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    cx, cy = W * 0.22, H * 0.52
    a = int(255 * C.clamp(k * 3))
    d.ellipse([(cx - 10) * s, (cy - 10) * s, (cx + 10) * s, (cy + 10) * s], fill=C.WHITE + (a,))
    for j in range(4):
        ph = (tt * 0.45 + j * 0.25) % 1.0
        r = (20 + 1100 * ph) * s
        aa = int(a * (1 - ph) * 0.8)
        if aa > 0:
            d.ellipse([cx * s - r, cy * s - r, cx * s + r, cy * s + r], outline=C.GREY + (aa,), width=2 * s)
    kk = C.smoother(C.seg(k, 0.45, 1.0))
    if kk > 0:
        x = W * 0.86 - (W * 0.86 - cx - 40) * kk
        r = 14 * s
        d.ellipse([x * s - r, cy * s - r, x * s + r, cy * s + r], fill=C.RED + (255,))
        for j in range(2):
            ph = (tt * 0.9 + j * 0.5) % 1.0
            rr = (14 + 60 * ph) * s
            d.ellipse([x * s - rr, cy * s - rr, x * s + rr, cy * s + rr], outline=C.RED + (int(200 * (1 - ph)),), width=2 * s)
        C.tracked(d, (x) * s, (cy - 40) * s, "ОТКЛИК", C.font("head_l", 28 * s), C.RED + (255,), 0.3, "ms")
    return C.done(lay)


def schyot_palochek(k1, k2, k_tally, tt):
    """два слова и счёт палочками под каждым: группы по пять, пятая — наискось"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    for i, (txt, k, x) in enumerate((("ПРОРОК", k1, W * 0.28), ("ИСТОЧНИК", k2, W * 0.72))):
        if k <= 0:
            continue
        a = int(255 * C.smoother(k))
        rise = (1 - C.out_cubic(k)) * 30
        C.tracked(d, x * s, (H * 0.46 + rise) * s, "«%s»" % txt, C.font("head", 110 * s), C.WHITE + (a,), 0.08, "ms")
        n = int(13 * C.clamp(k_tally))
        for j in range(n):
            g, r = j // 5, j % 5
            bx = x - 150 + g * 110 + r * 18
            y0, y1 = H * 0.58, H * 0.66
            if r < 4:
                d.line([(bx * s, y0 * s), (bx * s, y1 * s)], fill=C.RED + (255,), width=5 * s)
            else:
                d.line([((bx - 80) * s, (y1 - 6) * s), ((bx + 8) * s, (y0 + 6) * s)], fill=C.RED + (255,), width=5 * s)
    kd = C.clamp(max(k1, k2) * 3)
    d.rectangle([(W / 2 - 2) * s, (H * 0.36) * s, (W / 2 + 2) * s, (H * 0.70) * s], fill=(90, 90, 96, int(255 * kd)))
    C.tracked(d, (W / 2) * s, (H * 0.54) * s, "ИЛИ", C.font("head_l", 40 * s), C.GREY + (int(255 * kd),), 0.3, "ms")
    return C.done(lay)


def titry(k, tt):
    """титры источников: список едет снизу вверх"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    step = 118
    total = len(TITRY) * step
    y0 = H + 40 - (total + H - 200) * C.clamp(k)
    f1 = C.font("head_r", 36 * s)
    f2 = C.font("head_l", 26 * s)
    for i, (a, b) in enumerate(TITRY):
        y = y0 + i * step
        if y < -80 or y > H + 80:
            continue
        al = int(255 * C.clamp((y - 40) / 120) * C.clamp((H - 40 - y) / 120))
        if i == 0:
            C.tracked(d, (W / 2) * s, y * s, a, C.font("head", 64 * s), C.WHITE + (al,), 0.3, "ms")
            d.rectangle([(W / 2 - 40) * s, (y + 20) * s, (W / 2 + 40) * s, (y + 23) * s], fill=C.RED + (al,))
            continue
        C.tracked(d, (W / 2) * s, y * s, a.upper(), f1, C.WHITE + (al,), 0.12, "ms")
        C.tracked(d, (W / 2) * s, (y + 42) * s, b.upper(), f2, C.GREY + (al,), 0.2, "ms")
    return C.done(lay)
