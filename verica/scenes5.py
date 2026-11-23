#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Фильм «Верица» — пятый кусок: блок 4 «ДЕЛО ТРЕТЬЕ. РОССИЯ» целиком, сцены 57-81 (≈105 с).

Здесь она говорит сама: врезка v02 (14:07) со словами — 2 с оригинала, потом приглушить,
перевод читает ОЛЬГА (olga_1.mp3, вставка-смесь в sborka.py). Газета sd.rs — живой скриншот
(подпись «sd.rs · 27.06.2016 · скриншот страницы 23.11.2026»), сербские строки показываются
как есть, перевод печатается по букве с пометкой ПЕРЕВОД. Пересказы российских изданий —
подпись «по пересказам · первоисточника в кадре нет». Карты — «карта условная».
Людей в кадре нет, кроме самой Верицы из видео-врезок.

Новые эффекты своей разработки (fx5, низ файла):
  otschet_dney     — отсчёт дней: 92 деления заполняются между двумя датами, счётчик бежит
  oscillo          — осциллограмма живого голоса: огибающая считается из самого звука врезки
  peremotka        — обратная перемотка: кадр рвётся горизонтальными полосами, годы щёлкают назад
  pechat           — печать: страница выходит из-под валика, краска под ним ещё сырая
  shkala_dvuh_dat  — две даты на одной шкале, промежуток растягивается, дни добегают
  otkat_strelok    — стрелки на карте откатываются назад, оставляя тающий след
  strana_layer     — страна на карте наливается цветом (Китай, Прибалтика)
  roscherk         — росчерк: толстый красный штрих рукой через весь кадр
  pereskaz         — пересказ: фраза идёт через четыре панели и в каждой теряет буквы
  mel              — мел на доске: цифры пишутся мелом, крошка сыплется
  kalendar_let     — перекидной календарь на любые годы (месяц + год)
  puls_linii       — импульсы у линии фронта: рвутся вперёд и откатываются
  tsentr_mira      — три свечения на карте появляются по одному
  pustye_grafy     — список с пустыми графами срока, в конце в каждой — прочерк
"""
import math
import os
import random
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import fx
import karta as K
from core import W, H, SS
from scenes import (scene, rel, shots, flash, word, red_line, zoom_at, grade, vid, verica,
                    CAP_V, page_dark, dark_bg, CARD_POS, CARD_H, fit_px)
from scenes2 import EUROPE, label, doc_view, EXTRA, headlines, SD, CAP_SD
from scenes3 import lamp_bg, rukopis
from scenes4 import board4, board_blur_bg

SAFE_X, SAFE_Y = 96, 54

CAP_V_ZVUK = ("Верица Обренович", "Белград · интервью 21.04.2019 · METANOJA TV", "оригинальный звук · перевод за кадром")
CAP_KARTA = ("карта условная", None, None)
CAP_KARTA_GAZ = ("карта условная", "по пересказу газеты sd.rs", None)
CAP_PERESKAZ = ("по пересказам российских изданий", "первоисточника в кадре нет", None)
CAP_LINIYA = ("линия фронта условная", "по открытым картам", None)
CAP_SCHET = ("наш счёт по её словам", "год она не называла", None)

# ── строки на странице sd.rs (пиксели sd_rs_live.png, промерено 23.11)
SUB_1 = (482, 527, 1023, 549)      # «Intervju sa Vericom Obrenović je napravljen prošle»
SUB_2 = (481, 556, 1072, 578)      # «godine u junu, tako da se neke stvari koje je predvidela»
SUB_3 = (482, 585, 820, 607)       # «lako već mogu videti kao tačne.»
DATE_ROW = (481, 626, 711, 635)    # «27.06.2016. 06:08  Piše: Nevena Ostojić»
LINE_RU = (506, 2552, 1036, 2570)  # «Ruska vojska će morati da uđe u Ukrajinu i u ratu koji će početi,»
LINE_NATO = (505, 2578, 1040, 2592)  # «a NATO će se povući kada bude video kakvo oružje ima Rusija. U»
LINE_KIT = (505, 2604, 918, 2622)  # «tom ruskom prodoru priključiće se kineska vojska.»
LINE_EU = (506, 2734, 1075, 2752)  # «Evropska unija će se raspasti, a novu uniju će oformiti Nemačka. U tu»

V02 = "v02_delo3_1336-1420.mp4"
V02_START = 32.0     # 14:08 — «А Русија је најјача сила на свету…»

# ── доска: карточки блока 4
EXTRA["ross"] = ((W * 0.38, H * 0.885, -1.0), "", "РОССИЯ", ["армия войдёт в Украину · sd.rs 2016", "не менее пяти лет · по пересказам"])
EXTRA["posle"] = ((W * 0.62, H * 0.885, 2.0), "?", "ПОСЛЕ", ["Прибалтика · ЕС · НАТО", "центр мира · сроков нет"])

EURASIA = K.Okno(lon=(22.0, 138.0), lat=(10.0, 72.0))
BALTIC = K.Okno(lon=(10.0, 40.0), lat=(52.0, 63.0))
K.CITIES.update({"Москва": (37.62, 55.75), "Пекин": (116.40, 39.90), "Дели": (77.21, 28.61)})


def to_frame(box, geo):
    x0, y0, s = geo
    return ((box[0] - x0) * s, (box[1] - y0) * s, (box[2] - x0) * s, (box[3] - y0) * s)


def sd_line(yc, sc, t, xc=771.0, spot=(640, 300), dark=0.10):
    """окно газеты sd.rs на строке yc под фонарём"""
    img, geo = doc_view(SD, yc, sc, xc)
    img = fx.fonar(img, W * 0.5, H * 0.5, spot[0], spot[1], dark, 0.04, t)
    return page_dark(img, t), geo


def perevod(text, k, t, y=H - 214):
    """пометка ПЕРЕВОД и строка, печатающаяся по букве"""
    if k <= 0:
        return []
    return [C.text_layer(["ПЕРЕВОД"], "head_l", 24, C.GREY, SAFE_X, y - 56, "ls", 0.3, a=C.clamp(k * 3)),
            fx.typed(text, k, "head_r", 46, C.WHITE, SAFE_X, y, 0.02, True, t)]


# ═════════════════════════ 57 · титр ДЕЛО ТРЕТЬЕ · здесь она говорит сама ═════════════════════════
@scene("57")
def s57(t, dur):
    c_zdes = rel("57", 410.26)

    def a_title(tt, d):
        img = board_blur_bg(t, extra=[("kat", 1, 1), ("mar", 1, 1), ("sech", 1, 1), ("dolzh", 1, 1)])
        k = C.seg(tt, 0.0, 0.5)
        sc = 1.3 - 0.3 * C.out_expo(k)
        px = fit_px("ДЕЛО ТРЕТЬЕ", "head", 170, W - 2 * SAFE_X, 0.1)
        lays = [C.text_layer(["ДЕЛО ТРЕТЬЕ"], "head", int(px * sc), C.WHITE, W / 2, H * 0.5 + 40, "ms", 0.1, a=C.clamp(k * 2)),
                red_line(C.seg(tt, 0.4, 0.9), W / 2 - 200, W / 2 + 200, H * 0.5 + 66, 5),
                word("россия", C.seg(tt, 0.6, 1.0), H * 0.5 + 150, 60, "serif_i", C.GREY, 0.0, rise=16)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.1, 0.5)

    def b_sama(tt, d):
        img = verica("v02a", V02, tt + 30.8, zoom=1.8, cx=0.48, cy=0.30, push=0.06, hand=2.5)
        return flash(C.over(img, label("ЗДЕСЬ", C.seg(tt, 0.05, 0.4), 130, 40, C.GREY),
                            word("ОНА ГОВОРИТ САМА", C.seg(tt, 0.2, 0.6), 230, 86, "head", C.WHITE, 0.12, rise=26),
                            C.caption(*CAP_V, k=C.seg(tt, 0.3, 0.8))).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_title), (c_zdes, b_sama)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 58 · запись апреля 2019 · за три месяца до смерти ═════════════════════════
@scene("58")
def s58(t, dur):
    c_tri = rel("58", 414.57)

    def a_zapis(tt, d):
        fr = vid("v02b", V02, 0.0, zoom=1.8, cx=0.48, cy=0.30).at(tt + 20.3)
        hx, hy = fx.handheld(tt, 4.0, 2)
        fr = zoom_at(fr, 1.02 + 0.02 * tt, W / 2 + hx, H / 2 + hy)
        img = fx.vidoiskatel(fr, tt, tc0=13 * 60 + 56.0, zoom_step=1, rec=True, bw=0.5)
        return C.over(img, K.date_tag("АПРЕЛЬ 2019", C.seg(tt, 0.15, 0.6), y=H - 190, sub="опубликовано 21.04.2019"),
                      C.caption(*CAP_V, k=1.0)).convert("RGB")

    def b_tri(tt, d):
        img = C.kb(dark_bg(71), tt / 3.0, 0.05, 0.5, 0.5)
        lay = otschet_dney(C.seg(tt, 0.1, 1.2), tt)
        return C.grain(C.over(img, lay, label("ЗА ТРИ МЕСЯЦА ДО СМЕРТИ", C.seg(tt, 0.05, 0.4), 130, 46, C.WHITE)).convert("RGB"), t, 0.04)

    fn, tt, d = shots(t, [(0.0, a_zapis), (c_tri, b_tri)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 59 · Верица говорит · перевод за кадром (вставка 9,3 с) ═════════════════════════
@scene("59")
def s59(t, dur):
    img = verica("v02c", V02, t + V02_START, zoom=1.8, cx=0.48, cy=0.30, push=0.03, hand=2.0, k_grade=0.85)
    env_v = envelope(V02, V02_START, 9.3)
    env_o = envelope("olga_1.mp3", 0.0, 6.8)
    lay = oscillo([(env_v, 0.0, C.WHITE), (env_o, 2.3, C.RED)], t, H - 150, 54, SAFE_X, W - SAFE_X)
    k_orig = C.seg(t, 0.2, 0.6) * (1 - C.seg(t, 2.0, 2.4))
    k_per = C.seg(t, 2.3, 2.7)
    k1 = C.seg(t, 2.35, 4.9)
    k2 = C.seg(t, 5.0, 8.9)
    lays = [lay, label("ОРИГИНАЛЬНЫЙ ЗВУК", k_orig, 120, 34, C.GREY, x=W - SAFE_X, anchor="rs"),
            label("ПЕРЕВОД ЗА КАДРОМ", k_per, 120, 34, C.RED, x=W - SAFE_X, anchor="rs"),
            fx.typed("Россия — самая сильная держава в мире.", k1, "head_r", 44, C.WHITE, SAFE_X, 196, 0.02, k2 <= 0, t) if k1 > 0 else None,
            fx.typed("У неё есть оружие, которого нет у Америки. И они испугались.", k2, "head_r", 44, C.WHITE, SAFE_X, 252, 0.02, True, t) if k2 > 0 else None,
            C.caption(*CAP_V_ZVUK, k=C.seg(t, 0.4, 0.9))]
    img = C.over(img, *lays).convert("RGB")
    return C.finish(flash(img, t, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 60 · перемотка назад · главное она сказала раньше ═════════════════════════
@scene("60")
def s60(t, dur):
    c_glav = rel("60", 416.41)

    def a(tt, d):
        back = 6.0 * math.floor(min(tt, 1.4) / 0.2) * 0.2                                    # кадр катится назад ступенями (меньше переоткрытий ffmpeg)
        fr = vid("v02d", V02, 0.0, zoom=1.8, cx=0.48, cy=0.30).at(41.2 - back)
        fr = grade(fr, 0.9)
        k = C.seg(tt, 0.1, 1.45)
        img = peremotka(fr, k, tt, ["2019", "2018", "2017", "2016", "2015"])
        kg = C.seg(tt, c_glav, c_glav + 0.45)
        return C.over(img, word("ГЛАВНОЕ ОНА СКАЗАЛА РАНЬШЕ", kg, H - 150, 76, "head", C.WHITE, 0.12, rise=26),
                      C.caption(*CAP_V, k=1.0 - kg * 0.0)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 61 · июнь 2015 · запись для того же канала ═════════════════════════
@scene("61")
def s61(t, dur):
    c_kanal = rel("61", 420.57)

    def a_iyun(tt, d):
        sc = 2.25 + 0.04 * tt
        img, geo = sd_line(567, sc, t, 777, (760, 300))
        b1, b2 = to_frame(SUB_1, geo), to_frame(SUB_2, geo)
        k_tr = C.seg(tt, 0.3, 2.0)
        lays = [red_line(C.seg(tt, 0.1, 0.6), b1[0] - 6, b1[2] + 6, b1[3] + 8, 4),
                red_line(C.seg(tt, 0.4, 0.9), b2[0] - 6, b2[2] + 6, b2[3] + 8, 4),
                K.date_tag("ИЮНЬ 2015", C.seg(tt, 0.15, 0.6), sub="по тексту статьи"),
                C.caption(*CAP_SD, k=1.0)] + perevod("«Интервью с Верицей Обренович сделано в июне прошлого года»", k_tr, t)
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    def b_kanal(tt, d):
        k = C.smoother(C.seg(tt, 0.0, 1.2))
        img, geo = sd_line(C.lerp(640, 930, k), C.lerp(2.2, 1.9, k), t, 782, (700, 420), 0.12)
        return C.over(img, label("ТОТ ЖЕ КАНАЛ · КАДР С ТОЙ ЗАПИСИ — НА СТРАНИЦЕ", C.seg(tt, 0.4, 0.8), 130, 36, C.WHITE),
                      C.caption(*CAP_SD, k=1.0)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_iyun), (c_kanal, b_kanal)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 62 · через год · печатает сербская газета ═════════════════════════
@scene("62")
def s62(t, dur):
    c_gaz = rel("62", 423.6)

    def a(tt, d):
        page, geo = doc_view(SD, 640, 1.15, 960)
        k = C.seg(tt, 0.1, 2.6)
        img = pechat(page, k, tt)
        img = fx.fonar(img, W * 0.45, H * 0.45, 900, 560, 0.14, 0.03, t)
        img = page_dark(img, t)
        kg = C.seg(tt, c_gaz, c_gaz + 0.45)
        return C.over(img, fx.flip_number(["2015", "2016"], C.seg(tt, 0.2, 0.9), W - SAFE_X - 150, 150, 120),
                      label("ЧЕРЕЗ ГОД", C.seg(tt, 0.05, 0.4), 250, 34, C.GREY, x=W - SAFE_X - 150),
                      word("ПЕЧАТАЕТ СЕРБСКАЯ ГАЗЕТА", kg, H - 150, 70, "head", C.WHITE, 0.12, rise=24),
                      C.caption(*CAP_SD, k=C.seg(tt, 1.0, 1.5))).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 63 · 27 июня 2016 · дата стоит на странице ═════════════════════════
@scene("63")
def s63(t, dur):
    c_stoit = rel("63", 428.28)

    def a(tt, d):
        k = C.smoother(C.seg(tt, 0.0, 1.6))
        sc = C.lerp(2.0, 3.4, k) + 0.03 * tt
        img, geo = doc_view(SD, C.lerp(600, 631, k), sc, C.lerp(760, 640, k))
        box = to_frame(DATE_ROW, geo)
        bright = img
        img = fx.fonar(img, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, 620, 240, 0.10, 0.04, t)
        img = page_dark(img, t)
        kv = C.seg(tt, c_stoit, c_stoit + 0.7)
        if kv > 0:
            img = fx.vydelenie(img, page_dark(bright, t), box, kv, C.RED, 0.30, True)
        return flash(C.over(img, K.date_tag("27 ИЮНЯ 2016", C.seg(tt, 0.15, 0.6), sub="дата стоит на странице"),
                            label("ДАТА", C.seg(tt, c_stoit, c_stoit + 0.4), H - 150, 60, C.WHITE),
                            C.caption(*CAP_SD, k=1.0)).convert("RGB"), tt, 0.06, 0.3)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 64 · Верица без слов 3 с ═════════════════════════
@scene("64")
def s64(t, dur):
    img = verica("v06c", "v06_krupno_2400.mp4", t, push=0.10, hand=2.5)
    return C.finish(C.over(img, C.caption(*CAP_V, k=C.seg(t, 0.2, 0.7))).convert("RGB"), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 65 · строка в газете · ОЛЬГА читает ═════════════════════════
@scene("65")
def s65(t, dur):
    def a(tt, d):
        sc = 2.55 + 0.03 * tt
        img, geo = sd_line(2561, sc, t, 771, (700, 260))
        box = to_frame(LINE_RU, geo)
        k_tr = C.seg(tt, 0.15, 2.4)
        lays = [red_line(C.seg(tt, 0.05, 0.6), box[0] - 8, box[2] + 8, box[3] + 10, 5),
                C.caption(*CAP_SD, k=1.0)] + perevod("«Российской армии придётся войти в Украину»", k_tr, t)
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 66 · две даты на одной шкале · 2068 дней ═════════════════════════
@scene("66")
def s66(t, dur):
    c_nap = rel("66", 429.83)
    c_fev = rel("66", 431.9)

    def a(tt, d):
        img = C.kb(dark_bg(72), tt / 6.0, 0.04, 0.5, 0.5)
        lay = shkala_dvuh_dat(C.seg(tt, 0.2, 1.8), C.seg(tt, 1.4, 1.9), C.seg(tt, 1.9, 3.0), C.seg(tt, c_fev, c_fev + 0.5), tt)
        return C.grain(C.over(img, lay, label("НАПЕЧАТАНО", C.seg(tt, c_nap, c_nap + 0.4), 150, 46, C.WHITE),
                              label("ЗА ПЯТЬ С ПОЛОВИНОЙ ЛЕТ ДО", C.seg(tt, c_nap + 0.7, c_nap + 1.1), H - 150, 40, C.GREY),
                              C.caption("sd.rs", "27.06.2016", "дата публикации", k=1.0)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 67 · продолжение, которое не цитируют ═════════════════════════
@scene("67")
def s67(t, dur):
    c_prod = rel("67", 433.42)
    c_ne = rel("67", 435.33)

    def a(tt, d):
        k = C.smoother(C.seg(tt, c_prod, c_prod + 1.3))
        yc = C.lerp(2561, 2592, k)
        sc = C.lerp(2.55, 2.25, k) + 0.02 * tt
        img, geo = doc_view(SD, yc, sc, 771)
        b_ru, b_n, b_k = to_frame(LINE_RU, geo), to_frame(LINE_NATO, geo), to_frame(LINE_KIT, geo)
        fy = C.lerp((b_ru[1] + b_ru[3]) / 2, (b_n[1] + b_k[3]) / 2, k)
        img = fx.fonar(img, W * 0.5, fy, 760, C.lerp(240, 330, k), 0.08, 0.04, t)
        img = page_dark(img, t)
        kb = C.seg(tt, c_ne, c_ne + 0.5)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        if kb > 0:
            a = int(255 * C.smoother(kb))
            x = b_n[0] - 26
            dd.line([(x * SS, (b_n[1] - 6) * SS), (x * SS, (b_k[3] + 6) * SS)], fill=C.RED + (a,), width=4 * SS)
        return flash(C.over(img, red_line(1.0, b_ru[0] - 8, b_ru[2] + 8, b_ru[3] + 10, 5), C.done(lay),
                            label("У ЭТОЙ ФРАЗЫ ЕСТЬ ПРОДОЛЖЕНИЕ", C.seg(tt, c_prod, c_prod + 0.4), 130, 40, C.WHITE),
                            word("ОБЫЧНО НЕ ЦИТИРУЮТ", kb, H - 150, 72, "head", C.RED, 0.12, rise=24),
                            C.caption(*CAP_SD, k=1.0)).convert("RGB"), tt, 0.06, 0.3)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 68 · НАТО отступит, увидев русское оружие ═════════════════════════
@scene("68")
def s68(t, dur):
    c_nato = rel("68", 437.12)
    c_otst = rel("68", 438.85)
    c_oruzh = rel("68", 439.70)

    def a(tt, d):
        base = K.base(EUROPE, hot="")
        base = zoom_at(base, 1.04 + 0.04 * tt / d, W * 0.45, H * 0.5)
        k_in = C.seg(tt, 0.1, 1.0)
        k_back = C.seg(tt, c_otst, c_otst + 1.3)
        k_or = C.seg(tt, c_oruzh, c_oruzh + 0.6)
        lay = otkat_strelok(k_in, k_back, tt)
        glow = C.layer()
        if k_or > 0:
            g = np.zeros((H, W), np.float32)
            xx = np.arange(W, dtype=np.float32)[None, :]
            g += np.clip((xx - W * 0.62) / (W * 0.38), 0, 1) ** 1.6 * 0.75 * C.smoother(k_or)
            arr = np.zeros((H, W, 4), np.uint8)
            arr[:, :, 0], arr[:, :, 1], arr[:, :, 2] = C.RED
            arr[:, :, 3] = (g * 255).astype(np.uint8)
            glow = Image.fromarray(arr, "RGBA")
        return C.over(base, glow, lay,
                      label("НАТО", C.seg(tt, c_nato, c_nato + 0.4), 150, 64, C.WHITE, x=SAFE_X, anchor="ls", track=0.2),
                      label("ГОВОРИЛА ОНА", C.seg(tt, c_nato + 0.7, c_nato + 1.1), 200, 30, C.GREY, x=SAFE_X, anchor="ls"),
                      word("ОТСТУПИТ", C.seg(tt, c_otst, c_otst + 0.45), H - 150, 96, "head", C.WHITE, 0.14, x=W * 0.5, anchor="ms", rise=28),
                      label("УВИДЕВ РУССКОЕ ОРУЖИЕ", k_or, 150, 40, C.RED, x=W - SAFE_X, anchor="rs"),
                      C.caption(*CAP_KARTA_GAZ, k=1.0)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 69 · китайская армия встанет рядом ═════════════════════════
@scene("69")
def s69(t, dur):
    c_ryadom = rel("69", 442.3)

    def a(tt, d):
        k_kit = C.seg(tt, 0.3, 1.3)
        k_r = C.seg(tt, c_ryadom, c_ryadom + 0.5)
        lay = strana_layer(("China",), EURASIA, k_kit, C.RED, 120)
        br = C.layer()
        if k_r > 0:
            dd = ImageDraw.Draw(br)
            a = int(255 * C.smoother(k_r))
            x0, y0 = EURASIA.xy(80.0, 50.0)
            x1, y1 = EURASIA.xy(104.0, 36.0)
            dd.line([(x0 * SS, y0 * SS), (x1 * SS, y1 * SS)], fill=C.WHITE + (a,), width=3 * SS)
            for x, y in ((x0, y0), (x1, y1)):
                dd.ellipse([(x - 7) * SS, (y - 7) * SS, (x + 7) * SS, (y + 7) * SS], fill=C.WHITE + (a,))
        base = zoom_at(C.over(K.base(EURASIA, hot="Russia"), lay, C.done(br)).convert("RGB"), 1.05 + 0.05 * tt / d, W * 0.55, H * 0.45)
        return C.over(base, label("КИТАЙСКАЯ АРМИЯ", C.seg(tt, 0.2, 0.6), 150, 56, C.WHITE, x=SAFE_X, anchor="ls", track=0.16),
                      word("ВСТАНЕТ РЯДОМ", k_r, H - 150, 96, "head", C.WHITE, 0.14, x=SAFE_X, anchor="ls", rise=28),
                      C.caption(*CAP_KARTA_GAZ, k=1.0)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 70 · этого не случилось ═════════════════════════
@scene("70")
def s70(t, dur):
    c_ne = rel("70", 443.43)

    def a(tt, d):
        img = C.kb(dark_bg(73), tt / 2.0, 0.05, 0.5, 0.5)
        kr = C.seg(tt, 0.1, 0.55)
        return C.grain(C.over(img, label("НАТО ОТСТУПИТ", 1.0, H * 0.5 - 120, 56, C.GREY2, x=W * 0.5),
                              label("КИТАЙ ВСТАНЕТ РЯДОМ", 1.0, H * 0.5 - 40, 56, C.GREY2, x=W * 0.5),
                              roscherk(kr, 5),
                              word("НЕ СЛУЧИЛОСЬ", C.seg(tt, c_ne, c_ne + 0.4), H * 0.5 + 200, 130, "head", C.RED, 0.1, rise=30)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 70b · пока не случилось (его дописка, вставка 1,45 с) ═════════════════════════
@scene("70b")
def s70b(t, dur):
    img = C.kb(dark_bg(73), (t + 1.51) / 2.0, 0.05, 0.5, 0.5)
    kp = C.seg(t, 0.12, 0.5)
    lays = [label("НАТО ОТСТУПИТ", 1.0, H * 0.5 - 120, 56, C.GREY2, x=W * 0.5),
            label("КИТАЙ ВСТАНЕТ РЯДОМ", 1.0, H * 0.5 - 40, 56, C.GREY2, x=W * 0.5),
            roscherk(1.0, 5),
            word("НЕ СЛУЧИЛОСЬ", 1.0, H * 0.5 + 200, 130, "head", C.RED, 0.1, rise=30),
            rukopis_layer("пока", kp, 130, H * 0.5 + 205, 110)]
    return C.finish(C.grain(C.over(img, *lays).convert("RGB"), t, 0.04), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


def rukopis_layer(text, k, x, y, px):
    """рукописное слово пером поверх кадра (белым), пишется слева направо"""
    if k <= 0:
        return None
    lay = rukopis(text, k, 0, int(px * 1.1), px, (int(px * len(text) * 0.8), int(px * 1.8)), angle=-6.0, heavy=True)
    a = np.asarray(lay, np.uint8).copy()
    a[:, :, 0:3] = (240, 238, 234)
    lay = Image.fromarray(a, "RGBA")
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(lay, (int(x), int(y - px * 1.1)))
    return out


# ═════════════════════════ 71 · только в пересказах ═════════════════════════
@scene("71")
def s71(t, dur):
    c_dal = rel("71", 444.94)
    c_per = rel("71", 446.6)

    def a(tt, d):
        img = C.kb(dark_bg(74), tt / 4.0, 0.05, 0.5, 0.5)
        return C.grain(C.over(img, headlines(C.seg(tt, 0.1, 1.8), t, 7),
                              label("ДАЛЬШЕ", C.seg(tt, c_dal, c_dal + 0.4), 130, 40, C.GREY),
                              word("ТОЛЬКО В ПЕРЕСКАЗАХ", C.seg(tt, c_per, c_per + 0.45), H * 0.5 + 50, 120, "head", C.WHITE, 0.1, rise=30),
                              C.caption(*CAP_PERESKAZ, k=C.seg(tt, c_per, c_per + 0.5))).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 72 · война продлится не менее пяти лет ═════════════════════════
@scene("72")
def s72(t, dur):
    c_voyna = rel("72", 450.0)
    c_pyat = rel("72", 451.0)

    def a(tt, d):
        img = C.kb(dark_bg(75), tt / 4.0, 0.04, 0.5, 0.5)
        lay = pereskaz("война продлится не менее пяти лет", C.seg(tt, 0.2, 1.9), tt)
        kn = C.seg(tt, c_pyat, c_pyat + 0.8)
        return C.grain(C.over(img, lay, label("РОССИЙСКИЕ ИЗДАНИЯ ПРИВОДЯТ ЕЁ СЛОВА", C.seg(tt, 0.1, 0.5), 130, 36, C.WHITE),
                              C.big_number("5 ЛЕТ", "НЕ МЕНЕЕ", None, kn, cx=W / 2, cy=H * 0.72, px=170, count_from=0, rings=False) if kn > 0 else None,
                              C.caption(*CAP_PERESKAZ, k=1.0)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 73 · победа России · Киев примет все условия ═════════════════════════
@scene("73")
def s73(t, dur):
    c_pob = rel("73", 452.52)
    c_kiev = rel("73", 454.43)

    def a(tt, d):
        img = lamp_bg(47)
        items = [("война продлится не менее пяти лет", 0.0), ("закончится победой России", c_pob), ("Киев примет все условия", c_kiev)]
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        s = SS
        for i, (txt, t0) in enumerate(items):
            k = C.seg(tt, t0, t0 + 0.45)
            if k <= 0:
                continue
            a = int(255 * C.smoother(k))
            dx = (1 - C.out_cubic(k)) * 40
            y = H * 0.36 + i * 150
            C.tracked(dd, (SAFE_X + 40 + dx) * s, y * s, "%02d" % (i + 1), C.font("head_l", 44 * s), C.RED + (a,), 0.1)
            C.tracked(dd, (SAFE_X + 130 + dx) * s, y * s, "«%s»" % txt, C.font("serif_i", 58 * s), C.WHITE + (a,), 0.0)
        img = fx.fonar(img, W * 0.5, H * 0.5, 980, 560, 0.10, 0.04, t)
        return C.grain(C.over(img, C.done(lay), label("ПО ПЕРЕСКАЗАМ", C.seg(tt, 0.05, 0.4), 150, 40, C.GREY, x=SAFE_X + 40, anchor="ls"),
                              C.caption(*CAP_PERESKAZ, k=1.0)).convert("RGB"), t, 0.03)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 74 · считаем: февраль 2022 плюс пять ═════════════════════════
@scene("74")
def s74(t, dur):
    c_fev = rel("74", 457.12)
    c_plus = rel("74", 458.57)

    def a(tt, d):
        img = mel([("02 . 2022", W * 0.22, H * 0.56, 200, C.seg(tt, c_fev, c_fev + 1.1)),
                   ("+ 5", W * 0.70, H * 0.56, 200, C.seg(tt, c_plus, c_plus + 0.5))], tt)
        return C.over(img, label("СЧИТАЕМ", C.seg(tt, 0.1, 0.5), 150, 56, C.WHITE, track=0.3),
                      label("ФЕВРАЛЬ ДВАДЦАТЬ ВТОРОГО", C.seg(tt, c_fev + 0.2, c_fev + 0.6), H - 200, 30, C.GREY, x=W * 0.3),
                      label("ПЛЮС ПЯТЬ ЛЕТ", C.seg(tt, c_plus, c_plus + 0.4), H - 200, 30, C.GREY, x=W * 0.72),
                      C.caption(*CAP_SCHET, k=1.0)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.35)


# ═════════════════════════ 75 · календарь листается · февраль 2027 ═════════════════════════
@scene("75")
def s75(t, dur):
    c_fev = rel("75", 459.40)

    def a(tt, d):
        img = C.kb(dark_bg(76), tt / 4.0, 0.04, 0.5, 0.5)
        lay = kalendar_let(["2022", "2023", "2024", "2025", "2026", "2027"], C.seg(tt, 0.1, 1.9), tt, "ФЕВРАЛЬ", W * 0.34)
        kf = C.seg(tt, c_fev, c_fev + 0.5)
        return C.grain(C.over(img, lay,
                              word("ФЕВРАЛЬ", kf, H * 0.44, 90, "head_l", C.WHITE, 0.14, x=W * 0.72, rise=24),
                              word("2027", kf, H * 0.44 + 200, 220, "head", C.RED, 0.04, x=W * 0.72, rise=40),
                              C.caption(*CAP_SCHET, k=1.0)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 76 · оговорка обязательна · 77 · не прогноз и не призыв ═════════════════════════
OGOV = [("год две тысячи двадцать седьмой она не называла", 463.01),
        ("это наш счёт по её словам", 464.98),
        ("не прогноз и не призыв", 468.92)]


def ogovorka_sheet(tt, t, k_in, ks, k_red=0.0, k_note=0.0, zoom=1.0):
    """лист ОГОВОРКА под лампой: строки печатаются по одной; красная пометка пером"""
    img = lamp_bg(48).convert("RGBA")
    w, h = 1240, 700
    sheet = C.paper(w, h, seed=131, tone=(200, 190, 170), dark=0.0).convert("RGBA")
    d = ImageDraw.Draw(sheet)
    d.rectangle([0, 0, w - 1, h - 1], outline=(110, 100, 86, 255), width=3)
    d.line([(60, 150), (w - 60, 150)], fill=(110, 100, 86, 255), width=2)
    d.text((60, 118), "ОГОВОРКА", font=C.font("head", 64), fill=C.INK + (255,), anchor="ls")
    d.text((w - 60, 118), "обязательна", font=C.font("serif_i", 40), fill=(110, 100, 86, 255), anchor="rs")
    y = 250
    for (ln, _), k in zip(OGOV, ks):
        n = int(len(ln) * C.clamp(k))
        if n > 0:
            d.text((60, y), ln[:n], font=C.font("serif", 46), fill=C.INK + (255,), anchor="ls")
        y += 120
    if k_red > 0:
        kk = C.out_cubic(k_red)
        d.rectangle([60, y - 120 + 16, 60 + int((w - 120) * kk * 0.62), y - 120 + 21], fill=C.RED + (255,))
    if k_note > 0:
        sheet = Image.alpha_composite(sheet, rukopis("2027 — наш счёт", k_note, 700, 600, 54, (w, h), angle=-5.0, heavy=True))
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


@scene("76")
def s76(t, dur):
    c_ogov = rel("76", 461.38)
    cs = [rel("76", v) for _, v in OGOV[:2]]
    c_tish = rel("76", 466.6)

    def a(tt, d):
        ks = [C.seg(tt, c, c + 1.5) for c in cs] + [0.0]
        img = ogovorka_sheet(tt, t, C.seg(tt, 0.1, 0.9), ks, 0.0, C.seg(tt, c_tish, c_tish + 1.2), 1.0 + 0.06 * C.smoother(C.seg(tt, c_tish, d)))
        return C.over(img, label("ОГОВОРКА ОБЯЗАТЕЛЬНА", C.seg(tt, c_ogov, c_ogov + 0.4), 110, 36, C.WHITE),
                      C.caption(*CAP_SCHET, k=1.0)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


@scene("77")
def s77(t, dur):
    c_ne = rel("77", 468.92)

    def a(tt, d):
        ks = [1.0, 1.0, C.seg(tt, c_ne, c_ne + 1.2)]
        img = ogovorka_sheet(tt, t, 1.0, ks, C.seg(tt, c_ne + 1.0, c_ne + 1.5), 1.0, 1.06 + 0.02 * tt)
        return C.over(img, word("НЕ ПРОГНОЗ · НЕ ПРИЗЫВ", C.seg(tt, c_ne + 0.9, c_ne + 1.3), H - 110, 54, "head_l", C.WHITE, 0.16, rise=20),
                      C.caption(*CAP_SCHET, k=1.0)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 78 · пятый год · переговоры идут · прорыва нет ═════════════════════════
@scene("78")
def s78(t, dur):
    c_per = rel("78", 472.61)
    c_pror = rel("78", 473.80)

    def a(tt, d):
        base = K.base(K.UA, hot="Ukraine")
        base = zoom_at(base, 1.08 + 0.05 * tt / d, W * 0.6, H * 0.55)
        k_line = C.seg(tt, 0.1, 1.3)
        die = C.seg(tt, c_pror, c_pror + 0.5)
        lays = [K.line_layer(K.LINE_NOW, k_line, K.UA, C.RED, 5, None, True, False),
                puls_linii(k_line, tt, die),
                K.city_layer(["Киев"], C.seg(tt, 0.3, 0.7), K.UA, 28, {"Киев": "l"}) if "Киев" in K.CITIES else None,
                label("СЕГОДНЯ", C.seg(tt, 0.05, 0.4), 130, 34, C.GREY, x=SAFE_X, anchor="ls"),
                word("ПЯТЫЙ ГОД", C.seg(tt, 0.3, 0.75), 230, 96, "head", C.WHITE, 0.12, x=SAFE_X, anchor="ls", rise=28),
                label("ПЕРЕГОВОРЫ ИДУТ", C.seg(tt, c_per, c_per + 0.4), H - 190, 40, C.WHITE, x=SAFE_X, anchor="ls"),
                word("ПРОРЫВА НЕТ", C.seg(tt, c_pror, c_pror + 0.4), H - 120, 72, "head", C.RED, 0.12, x=SAFE_X, anchor="ls", rise=22),
                C.caption(*CAP_LINIYA, k=1.0, x=W * 0.5)]
        return C.over(base, *lays).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 79 · а что у неё стоит после? ═════════════════════════
@scene("79")
def s79(t, dur):
    c_chto = rel("79", 474.75)

    def a(tt, d):
        kr = C.seg(tt, 0.1, 0.7)
        kp = C.seg(tt, c_chto, c_chto + 0.6)
        img = board4(t, 24.0 + tt, [("kat", 1, 1), ("mar", 1, 1), ("sech", 1, 1), ("dolzh", 1, 1), ("ross", kr, C.seg(tt, 0.4, 1.2)), ("posle", kp, C.seg(tt, c_chto + 0.3, c_chto + 1.0))],
                     threads=[("ross", 2, C.seg(tt, 0.7, 1.3)), ("ross", "posle", C.seg(tt, c_chto + 0.4, c_chto + 1.0))], amp=380.0)
        z = 1.30 - 0.12 * C.smoother(C.seg(tt, 0.0, d))
        img = zoom_at(img, z, W * 0.55, H * 0.80)
        return flash(C.over(img, word("А ЧТО У НЕЁ СТОИТ ПОСЛЕ?", kp, 150, 76, "head", C.WHITE, 0.12, rise=24)).convert("RGB"), tt, 0.08, 0.4)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 80 · Прибалтика · ЕС · НАТО · центр мира ═════════════════════════
@scene("80")
def s80(t, dur):
    c_eu = rel("80", 478.66)
    c_nato = rel("80", 480.61)
    c_centr = rel("80", 482.62)
    c_ros = rel("80", 483.51)
    c_kit = rel("80", 484.36)
    c_ind = rel("80", 485.09)

    def a_balt(tt, d):
        base = K.base(BALTIC, hot="")
        lay = strana_layer(("Estonia", "Latvia", "Lithuania"), BALTIC, C.seg(tt, 0.2, 1.0), C.RED, 110)
        img = zoom_at(C.over(base, lay).convert("RGB"), 1.05 + 0.06 * tt / d, W * 0.5, H * 0.5)
        return C.over(img, label("ПРИБАЛТИКА", C.seg(tt, 0.05, 0.4), 150, 56, C.WHITE, x=SAFE_X, anchor="ls", track=0.16),
                      word("САМА ВЕРНЁТСЯ К РОССИИ", C.seg(tt, 0.8, 1.25), H - 150, 76, "head", C.WHITE, 0.12, x=SAFE_X, anchor="ls", rise=24),
                      C.caption(*CAP_KARTA_GAZ, k=1.0)).convert("RGB")

    def b_eu(tt, d):
        sc = 2.5 + 0.03 * tt
        img, geo = sd_line(2743, sc, t, 790, (720, 260))
        box = to_frame(LINE_EU, geo)
        lays = [red_line(C.seg(tt, 0.05, 0.6), box[0] - 8, box[2] + 8, box[3] + 10, 5),
                C.caption(*CAP_SD, k=1.0)] + perevod("«Европейский союз распадётся»", C.seg(tt, 0.15, 1.3), t)
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    def c_nato_fn(tt, d):
        img = C.kb(dark_bg(77), (tt + 1.0) / 3.0, 0.05, 0.5, 0.5)
        frozen = C.over(img, word("НАТО", 1.0, H * 0.5 + 70, 260, "head", C.WHITE, 0.14)).convert("RGB")
        kr = C.seg(tt, 0.55, 1.75)
        out = fx.raspad(frozen, kr, seed=11, amp=300.0, bg=(9, 9, 11)) if kr > 0 else frozen
        out = flash(out, tt, 0.06, 0.3)
        return C.grain(C.over(out, label("ПЕРЕСТАНЕТ СУЩЕСТВОВАТЬ", C.seg(tt, 0.5, 0.9), H - 150, 46, C.GREY)).convert("RGB"), t, 0.04)

    def d_centr(tt, d):
        base = K.base(EURASIA, hot="")
        base = zoom_at(base, 1.03 + 0.05 * tt / d, W * 0.55, H * 0.5)
        lay = tsentr_mira([("Москва", C.seg(tt, c_ros - c_centr, c_ros - c_centr + 0.6)),
                           ("Пекин", C.seg(tt, c_kit - c_centr, c_kit - c_centr + 0.6)),
                           ("Дели", C.seg(tt, c_ind - c_centr, c_ind - c_centr + 0.6))], tt)
        return C.over(base, lay, label("ЦЕНТР МИРА", C.seg(tt, 0.05, 0.4), 150, 64, C.WHITE, x=SAFE_X, anchor="ls", track=0.2),
                      label("РОССИЯ · КИТАЙ · ИНДИЯ", C.seg(tt, c_ind - c_centr + 0.5, c_ind - c_centr + 0.9), H - 150, 40, C.GREY, x=SAFE_X, anchor="ls"),
                      C.caption(*CAP_KARTA, k=1.0)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_balt), (c_eu, b_eu), (c_nato, c_nato_fn), (c_centr, d_centr)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 81 · сроков нет ни у одного пункта ═════════════════════════
@scene("81")
def s81(t, dur):
    c_srok = rel("81", 485.95)

    def a(tt, d):
        img = C.kb(dark_bg(78), tt / 2.0, 0.04, 0.5, 0.5)
        items = ["Прибалтика вернётся к России", "Европейский союз распадётся", "НАТО перестанет существовать", "центр мира: Россия, Китай, Индия"]
        lay = pustye_grafy(items, C.seg(tt, 0.05, 0.9), C.seg(tt, c_srok + 0.4, c_srok + 0.8), tt)
        return C.grain(C.over(img, lay, word("СРОКОВ НЕТ", C.seg(tt, c_srok, c_srok + 0.4), H - 130, 90, "head", C.RED, 0.12, x=W - SAFE_X, anchor="rs", rise=26),
                              label("НИ У ОДНОГО ПУНКТА", C.seg(tt, c_srok + 0.5, c_srok + 0.9), H - 70, 28, C.GREY, x=W - SAFE_X, anchor="rs")).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.7, grain_k=0.0, vig=0.3)


# ═════════════════════════ fx5 — новые эффекты пятого куска ═════════════════════════
def otschet_dney(k, tt, n=92):
    """отсчёт дней: n делений между двумя датами заполняются слева направо, счётчик добегает до n"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    x0, x1 = SAFE_X + 60, W - SAFE_X - 60
    y = H * 0.56
    kk = C.out_cubic(k)
    m = int(n * kk)
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        on = i < m
        hh = 34 if i % 7 == 0 else 20
        col = C.RED + (255,) if on else (70, 70, 76, 255)
        d.rectangle([(x - 2) * s, (y - hh) * s, (x + 2) * s, (y + hh) * s], fill=col)
    f = C.font("head_r", 34 * s)
    f2 = C.font("head_l", 26 * s)
    a = int(255 * C.clamp(k * 4))
    C.tracked(d, x0 * s, (y - 80) * s, "21.04.2019", f, C.WHITE + (a,), 0.08)
    C.tracked(d, x0 * s, (y - 46) * s, "ИНТЕРВЬЮ ОПУБЛИКОВАНО", f2, C.GREY + (a,), 0.24)
    ar = int(255 * C.seg(k, 0.85, 1.0))
    C.tracked(d, x1 * s, (y - 80) * s, "22.07.2019", f, C.WHITE + (ar,), 0.08, "rs")
    C.tracked(d, x1 * s, (y - 46) * s, "ЕЁ НЕ СТАЛО", f2, C.GREY + (ar,), 0.24, "rs")
    C.tracked(d, (W / 2) * s, (y + 150) * s, "%d" % m, C.font("head", 140 * s), C.RED + (255,), 0.02, "ms")
    C.tracked(d, (W / 2) * s, (y + 200) * s, "ДНЯ" if m % 10 in (2, 3, 4) and m % 100 not in (12, 13, 14) else "ДНЕЙ", C.font("head_l", 36 * s), C.WHITE + (255,), 0.3, "ms")
    return C.done(lay)


_env = {}


def envelope(name, start, dur, sr=50):
    """огибающая громкости звука файла (sr точек в секунду), нормирована к 98-му процентилю"""
    key = (name, round(start, 2), round(dur, 2))
    if key in _env:
        return _env[key]
    p = C.apath(name)
    env = np.zeros(max(1, int(dur * sr)), np.float32)
    if os.path.exists(p):
        try:
            raw = subprocess.run([C.ffmpeg(), "-nostdin", "-loglevel", "error", "-ss", "%.3f" % start, "-t", "%.3f" % dur,
                                  "-i", p, "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
            a = np.abs(np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0)
            n = 8000 // sr
            m = len(a) // n
            if m > 0:
                e = a[:m * n].reshape(m, n).max(axis=1)
                e = e / max(1e-3, float(np.percentile(e, 98)))
                env = np.clip(e, 0, 1).astype(np.float32)
        except Exception:
            pass
    _env[key] = env
    return env


def oscillo(tracks, tt, y, h, x0, x1, window=4.0, sr=50):
    """осциллограмма: tracks=[(env, at, color)] — последние window с бегут справа налево, столбики зеркальные"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    pps = (x1 - x0) / window
    d.line([(x0 * s, y * s), (x1 * s, y * s)], fill=(70, 70, 76, 255), width=1 * s)
    for env, at, color in tracks:
        step = 5
        x = x1
        while x > x0:
            tm = tt - (x1 - x) / pps - at
            v = 0.0
            if tm >= 0:
                i = int(tm * sr)
                if i < len(env):
                    v = float(env[i])
            if v > 0.02:
                hh = max(1.0, v * h)
                a = int(255 * (0.35 + 0.65 * (x - x0) / (x1 - x0)))
                d.rectangle([(x - 1.5) * s, (y - hh) * s, (x + 1.5) * s, (y + hh) * s], fill=color + (a,))
            x -= step
    return C.done(lay)


def peremotka(fr, k, tt, years):
    """обратная перемотка: кадр рвётся горизонтальными полосами со сдвигом, годы щёлкают назад, значок ◀◀"""
    a = np.asarray(fr.convert("RGB"), np.uint8).copy()
    if 0 < k < 1:
        rng = np.random.default_rng(int(tt * 30))
        strength = math.sin(math.pi * k)
        n = int(6 + 18 * strength)
        for _ in range(n):
            y0 = int(rng.integers(0, H - 12))
            hgt = int(rng.integers(4, 40))
            sh = int(rng.integers(-160, 160) * strength)
            a[y0:y0 + hgt] = np.roll(a[y0:y0 + hgt], sh, axis=1)
        # строчки развёртки и обесцвечивание
        a[::4] = (a[::4].astype(np.float32) * 0.7).astype(np.uint8)
        lum = a.mean(axis=2, keepdims=True)
        a = (a * (1 - 0.5 * strength) + lum * 0.5 * strength).astype(np.uint8)
    img = Image.fromarray(a, "RGB")
    if 0 < k < 1:
        img = fx.glitch(img, 0.3 * math.sin(math.pi * k), seed=int(tt * 20), slices=8, shift=50, rgb=10)
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    if k > 0:
        a_ = int(255 * C.clamp(k * 4) * (1 - C.seg(k, 0.9, 1.0)))
        blink = (int(tt * 4) % 2) == 0
        if blink:
            for j in range(2):
                x = SAFE_X + 40 + j * 46
                d.polygon([((x + 40) * s, 120 * s), (x * s, 150 * s), ((x + 40) * s, 180 * s)], fill=C.WHITE + (a_,))
        C.tracked(d, (SAFE_X + 150) * s, 172 * s, "ПЕРЕМОТКА", C.font("head_r", 40 * s), C.WHITE + (a_,), 0.12)
    out = C.over(img, C.done(lay), fx.flip_number(years, k, W - SAFE_X - 180, 150, 120) if k > 0 else None)
    return out.convert("RGB")


_pechat = {}


def pechat(page, k, tt):
    """печать: валик идёт сверху вниз, над ним — отпечатанная страница, под ним — чистая бумага;
    полоса под валиком ещё сырая (темнее, размыта)"""
    if "paper" not in _pechat:
        _pechat["paper"] = C.paper(W, H, seed=77, tone=(226, 220, 206), dark=0.0)
    out = _pechat["paper"].copy()
    y = int(-40 + (H + 120) * C.smoother(k))
    if y > 0:
        out.paste(page.crop((0, 0, W, min(H, y))), (0, 0))
        y0 = max(0, y - 90)
        if y - y0 > 4 and y <= H:
            wet = page.crop((0, y0, W, y)).filter(ImageFilter.GaussianBlur(1.8))
            wa = np.asarray(wet, np.float32) * 0.78
            out.paste(Image.fromarray(np.clip(wa, 0, 255).astype(np.uint8), "RGB"), (0, y0))
    if -40 < y < H + 40:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.rectangle([0, y - 16, W, y + 16], fill=(36, 34, 32, 255))
        d.rectangle([0, y - 10, W, y - 7], fill=(90, 88, 84, 255))
        d.rectangle([0, y + 10, W, y + 16], fill=(16, 15, 14, 255))
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle([0, y + 16, W, y + 50], fill=(0, 0, 0, 120))
        sh = sh.filter(ImageFilter.GaussianBlur(10))
        out = Image.alpha_composite(Image.alpha_composite(out.convert("RGBA"), sh), lay).convert("RGB")
    return out


def shkala_dvuh_dat(k_line, k_right, k_count, k_fev, tt):
    """две даты на одной шкале: левая стоит, линия тянется вправо с делениями по годам, правая дата
    встаёт на место, счётчик дней добегает до 2068; k_fev — правая дата вспыхивает красным"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    x0, x1 = SAFE_X + 80, W - SAFE_X - 80
    y = H * 0.52
    kk = C.out_cubic(k_line)
    xe = x0 + (x1 - x0) * kk
    d.line([(x0 * s, y * s), (xe * s, y * s)], fill=(150, 150, 156, 255), width=3 * s)
    # деления по годам: 2017…2022 (1 января), по дням от 27.06.2016 (2068 дней до 24.02.2022)
    total = 2068.0
    marks = [(188, "2017"), (553, "2018"), (918, "2019"), (1283, "2020"), (1649, "2021"), (2014, "2022")]
    f_y = C.font("head_l", 26 * s)
    for dd, yr in marks:
        x = x0 + (x1 - x0) * dd / total
        if x <= xe:
            d.line([(x * s, (y - 16) * s), (x * s, (y + 16) * s)], fill=(150, 150, 156, 255), width=2 * s)
            C.tracked(d, x * s, (y + 50) * s, yr, f_y, C.GREY + (255,), 0.2, "ms")
    f = C.font("head", 56 * s)
    f2 = C.font("head_l", 26 * s)
    a = int(255 * C.clamp(k_line * 4))
    d.ellipse([(x0 - 9) * s, (y - 9) * s, (x0 + 9) * s, (y + 9) * s], fill=C.WHITE + (a,))
    C.tracked(d, x0 * s, (y - 50) * s, "27.06.2016", f, C.WHITE + (a,), 0.04, "ls")
    C.tracked(d, x0 * s, (y - 120) * s, "ГАЗЕТА", f2, C.GREY + (a,), 0.3, "ls")
    ar = int(255 * C.smoother(k_right))
    if ar > 0:
        col = C.RED if k_fev > 0 else C.WHITE
        pulse = 1.0 + 0.08 * math.sin(tt * 9.0) * C.smoother(k_fev)
        r = 9 * pulse
        d.ellipse([(x1 - r) * s, (y - r) * s, (x1 + r) * s, (y + r) * s], fill=col + (ar,))
        if k_fev > 0:
            for j in range(2):
                ph = (tt * 0.9 + j * 0.5) % 1.0
                rr = (14 + 80 * ph) * s
                d.ellipse([x1 * s - rr, y * s - rr, x1 * s + rr, y * s + rr], outline=C.RED + (int(ar * (1 - ph) * C.smoother(k_fev)),), width=3 * s)
        C.tracked(d, x1 * s, (y - 50) * s, "24.02.2022", f, col + (ar,), 0.04, "rs")
        C.tracked(d, x1 * s, (y - 120) * s, "ФЕВРАЛЬ ДВАДЦАТЬ ВТОРОГО", f2, C.GREY + (ar,), 0.3, "rs")
    if k_count > 0:
        n = int(round(2068 * C.out_expo(k_count)))
        ac = int(255 * C.clamp(k_count * 4))
        C.tracked(d, (W / 2) * s, (y + 230) * s, "%d" % n, C.font("head", 150 * s), C.RED + (ac,), 0.02, "ms")
        C.tracked(d, (W / 2) * s, (y + 285) * s, "ДНЕЙ МЕЖДУ ДАТАМИ", C.font("head_l", 34 * s), C.WHITE + (ac,), 0.3, "ms")
    return C.done(lay)


def otkat_strelok(k_in, k_back, tt, okno=EUROPE):
    """стрелки с запада на восток появляются по одной; на откате уходят назад, оставляя тающий след"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    rows = [(3.0, 57.5), (1.0, 54.5), (2.0, 51.5), (4.0, 48.5), (6.5, 45.5)]
    n = len(rows)
    kb = C.out_cubic(k_back)
    for i, (lon, lat) in enumerate(rows):
        ki = C.seg(k_in, i / n, (i + 1) / n + 0.2)
        if ki <= 0:
            continue
        L = 9.0 * C.out_cubic(ki)
        back = 10.0 * kb
        x0, y0 = okno.xy(lon - back, lat)
        x1, y1 = okno.xy(lon + L - back, lat)
        col = (214, 216, 224)
        a = int(255 * (1 - 0.55 * kb))
        # след: копии позади, тающие
        if kb > 0:
            for j in range(1, 5):
                xa, _ = okno.xy(lon - back + j * 2.2 * kb, lat)
                xb, _ = okno.xy(lon + L - back + j * 2.2 * kb, lat)
                aa = int(a * (0.5 - j * 0.1))
                if aa > 0:
                    d.line([(xa * s, y0 * s), (xb * s, y0 * s)], fill=col + (aa,), width=4 * s)
        d.line([(x0 * s, y0 * s), (x1 * s, y1 * s)], fill=col + (a,), width=9 * s)
        hd = 30
        d.polygon([((x1 + hd) * s, y1 * s), ((x1 - 6) * s, (y1 - hd * 0.7) * s), ((x1 - 6) * s, (y1 + hd * 0.7) * s)], fill=col + (a,))
    return C.done(lay)


_strana = {}


def strana_layer(names, okno, k, color=C.RED, fill_a=110):
    """страны names на окне карты наливаются цветом (заливка + контур) на долю k"""
    key = (names, okno.lon, okno.lat, color, fill_a)
    if key not in _strana:
        lay = C.layer()
        d = ImageDraw.Draw(lay)
        for ft in K.feats():
            if K.name_of(ft) in names:
                for ring in K.rings(ft):
                    pts = okno.pts(ring, SS)
                    if len(pts) > 2:
                        d.polygon(pts, fill=color + (fill_a,))
                        d.line(pts + [pts[0]], fill=color + (255,), width=2 * SS)
        _strana[key] = C.done(lay)
    return C.alpha(_strana[key], C.smoother(k)) if k < 1 else _strana[key]


def roscherk(k, seed=5):
    """росчерк рукой: толстый красный штрих через кадр, нажим гуляет, края рваные"""
    if k <= 0:
        return None
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    rng = random.Random(seed)
    pts = []
    n = 60
    for i in range(n + 1):
        u = i / n
        x = -60 + (W + 120) * u
        y = H * 0.72 - (H * 0.44) * u + 18 * math.sin(u * 9.0 + seed) + rng.uniform(-6, 6)
        pts.append((x, y))
    m = int(n * C.out_cubic(k))
    for i in range(m):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        wdt = 16 + 12 * math.sin(i / n * math.pi) + rng.uniform(-3, 3)
        d.line([(xa * s, ya * s), (xb * s, yb * s)], fill=C.RED + (235,), width=int(wdt * s))
        d.ellipse([(xb - wdt / 2) * s, (yb - wdt / 2) * s, (xb + wdt / 2) * s, (yb + wdt / 2) * s], fill=C.RED + (235,))
    out = C.done(lay)
    return out.filter(ImageFilter.GaussianBlur(0.6))


def pereskaz(text, k, tt, n=4):
    """пересказ: фраза идёт через n панелей слева направо; в каждой следующей теряет буквы и расплывается"""
    if k <= 0:
        return None
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rng = random.Random(7)
    pw, ph = 380, 230
    gap = (W - 2 * SAFE_X - n * pw) / (n - 1)
    y0 = H * 0.30
    words = text.split(" ")
    for i in range(n):
        ki = C.seg(k, i / n, (i + 1) / n + 0.1)
        if ki <= 0:
            break
        kk = C.out_cubic(ki)
        x0 = SAFE_X + i * (pw + gap)
        panel = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        d = ImageDraw.Draw(panel)
        d.rectangle([0, 0, pw - 1, ph - 1], fill=(24, 24, 28, 235), outline=(80, 80, 86, 255), width=2)
        d.rectangle([0, 0, pw - 1, 40], fill=(44, 44, 50, 255))
        d.text((16, 29), "ИЗДАНИЕ %d" % (i + 1), font=C.font("head_l", 22), fill=C.GREY + (255,), anchor="ls")
        # текст теряет буквы: доля потерь растёт с номером панели
        loss = 0.0 if i == 0 else 0.18 * i
        lines = []
        cur = ""
        for w_ in words:
            w2 = "".join(ch if rng.random() > loss else "·" for ch in w_)
            if len(cur) + len(w2) > 20:
                lines.append(cur)
                cur = w2
            else:
                cur = (cur + " " + w2).strip()
        lines.append(cur)
        yy = 90
        for ln in lines:
            d.text((20, yy), ln, font=C.font("serif_i", 36), fill=C.WHITE + (255,), anchor="ls")
            yy += 46
        if i > 0:
            panel = panel.filter(ImageFilter.GaussianBlur(0.6 * i))
        panel = C.alpha(panel, C.clamp(ki * 2))
        lay.alpha_composite(panel, (int(x0 + (1 - kk) * 60), int(y0)))
        if i > 0 and kk > 0.3:
            d2 = ImageDraw.Draw(lay)
            xa = x0 - gap + 10
            xb = x0 - 10
            yc = y0 + ph / 2
            d2.line([(xa, yc), (xb, yc)], fill=C.RED + (int(255 * kk),), width=3)
            d2.polygon([(xb, yc), (xb - 14, yc - 8), (xb - 14, yc + 8)], fill=C.RED + (int(255 * kk),))
    return lay


_mel = {}


def mel(lines, tt):
    """мел на доске: тёмно-зелёная доска с разводами; строки (text, x, y, px, k) пишутся мелом, у пера — крошка"""
    if "bg" not in _mel:
        base = C.paper(W, H, seed=91, tone=(28, 36, 32), dark=0.0)
        n = C.noise(W, H, 92, 3.0).filter(ImageFilter.GaussianBlur(14))
        a = np.asarray(base, np.float32) + (np.asarray(n, np.float32) / 255 - 0.5)[:, :, None] * 30
        bg = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
        _mel["bg"] = C.vignette(bg, 0.5)
        _mel["tex"] = np.asarray(C.noise(W, H, 93, 1.0), np.float32) / 255.0
    img = _mel["bg"].copy()
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dust = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dust)
    for text, x, y, px, k in lines:
        if k <= 0:
            continue
        f = C.font("head", px)
        tw = d.textlength(text, font=f)
        kk = C.out_cubic(k)
        d.text((x, y), text, font=f, fill=(228, 226, 214, 255), anchor="ls")
        # маска написанного
        if k < 1:
            xe = x + tw * kk
            d.rectangle([xe, y - px * 1.2, W, y + px * 0.4], fill=(0, 0, 0, 0))
            rng = random.Random(int(tt * 30))
            for _ in range(14):
                dx, dy = rng.uniform(-10, 10), rng.uniform(0, 70)
                r = rng.uniform(1, 3)
                dd.ellipse([xe + dx - r, y + dy - r, xe + dx + r, y + dy + r], fill=(228, 226, 214, int(rng.uniform(60, 180))))
    # фактура мела: альфа умножается на шум
    al = np.asarray(lay.getchannel("A"), np.float32) * (0.55 + 0.45 * _mel["tex"])
    lay.putalpha(Image.fromarray(np.clip(al, 0, 255).astype(np.uint8), "L"))
    out = Image.alpha_composite(Image.alpha_composite(img.convert("RGBA"), lay), dust).convert("RGB")
    return C.grain(out, tt, 0.03)


def kalendar_let(years, k, tt, month="ФЕВРАЛЬ", cx=W / 2):
    """перекидной календарь: листы с месяцем и годом отрываются один за другим, остаётся последний"""
    n = len(years) - 1
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pw, ph = 560, 500
    cy = H * 0.52
    x0, y0 = int(cx - pw / 2), int(cy - ph / 2)
    base = Image.new("RGBA", (pw + 40, ph + 60), (0, 0, 0, 0))
    ImageDraw.Draw(base).rounded_rectangle([0, 0, pw + 39, ph + 59], radius=14, fill=(40, 36, 34, 255), outline=(70, 66, 62, 255), width=3)
    sh, sx, sy = fx.shadow_of((pw + 40, ph + 60), W / 2, -300, cx, cy + 10, blur=26, a=180)
    lay.alpha_composite(sh, (sx, sy))
    lay.alpha_composite(base, (x0 - 20, y0 - 20))
    pos = C.clamp(k) * n
    cur = min(n, int(pos))
    frac = pos - cur

    def sheet(i):
        im = C.paper(pw, ph, seed=140 + i, tone=(222, 214, 196), dark=0.0).convert("RGBA")
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, pw - 1, 70], fill=(150, 40, 36, 255))
        d.text((pw / 2, 52), month, font=C.font("head_l", 34), fill=(240, 236, 230, 255), anchor="ms")
        d.text((pw / 2, ph * 0.68), years[i], font=C.font("head", 210), fill=C.INK + (255,), anchor="ms")
        for j in range(7):
            d.ellipse([50 + j * 78, 8, 50 + j * 78 + 14, 22], fill=(30, 28, 26, 255))
        return im

    nxt = min(n, cur + 1) if frac > 0 else cur
    lay.alpha_composite(sheet(nxt if frac > 0 else cur), (x0, y0))
    if frac > 0 and cur < n:
        im = sheet(cur)
        e = C.smoother(frac)
        im = im.rotate(-70 * e, Image.BICUBIC, expand=True, center=(0, 0))
        im = C.alpha(im, 1 - C.seg(frac, 0.6, 1.0))
        lay.alpha_composite(im, (int(x0 + 300 * e), int(y0 - 420 * e)))
    return lay


def puls_linii(k, tt, die, okno=K.UA, coords=K.LINE_NOW, n=7):
    """импульсы у линии фронта: точки рвутся на восток и откатываются; die — гаснут"""
    if k <= 0:
        return None
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    m = len(coords)
    for i in range(n):
        j = int((i + 0.5) / n * (m - 1))
        lon, lat = coords[j]
        ph = (tt * 0.7 + i * 0.37) % 1.0
        push = math.sin(ph * math.pi) * 0.9          # вперёд и назад, в градусах
        x, y = okno.xy(lon + push, lat)
        a = int(255 * (1 - ph) * C.clamp(k * 3) * (1 - C.smoother(die)))
        if a <= 0:
            continue
        r = (6 + 10 * ph) * s
        d.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], outline=C.RED + (a,), width=2 * s)
        d.ellipse([x * s - 4 * s, y * s - 4 * s, x * s + 4 * s, y * s + 4 * s], fill=C.WHITE + (a,))
    return C.done(lay)


def tsentr_mira(items, tt, okno=EURASIA):
    """три свечения на карте: точка, расходящиеся кольца, подпись"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    glow = C.layer()
    dg = ImageDraw.Draw(glow)
    for name, k in items:
        if k <= 0:
            continue
        lon, lat = K.CITIES[name]
        x, y = okno.xy(lon, lat)
        a = int(255 * C.smoother(k))
        r = 70 * s
        dg.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], fill=C.RED + (int(a * 0.55),))
        for j in range(3):
            ph = (tt * 0.6 + j * 0.33) % 1.0
            rr = (12 + 120 * ph) * s
            d.ellipse([x * s - rr, y * s - rr, x * s + rr, y * s + rr], outline=C.RED + (int(a * (1 - ph) * 0.9),), width=2 * s)
        d.ellipse([x * s - 7 * s, y * s - 7 * s, x * s + 7 * s, y * s + 7 * s], fill=C.WHITE + (a,))
        C.tracked(d, (x + 18) * s, (y - 14) * s, name.upper(), C.font("head_r", 32 * s), C.WHITE + (a,), 0.14)
    glow = glow.filter(ImageFilter.GaussianBlur(40 * s))
    return C.over(C.done(glow), C.done(lay))


def pustye_grafy(items, k_items, k_flash, tt):
    """список пунктов, у каждого графа «срок:» с пустой линией и мигающим курсором; в конце в каждой — прочерк"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    n = len(items)
    for i, txt in enumerate(items):
        ki = C.seg(k_items, i / n, (i + 1) / n + 0.1)
        if ki <= 0:
            break
        a = int(255 * C.smoother(ki))
        y = H * 0.26 + i * 150
        dx = (1 - C.out_cubic(ki)) * 40
        C.tracked(d, (SAFE_X + 40 + dx) * s, y * s, "%02d" % (i + 1), C.font("head_l", 40 * s), C.RED + (a,), 0.1)
        C.tracked(d, (SAFE_X + 120 + dx) * s, y * s, txt, C.font("head_r", 44 * s), C.WHITE + (a,), 0.04)
        C.tracked(d, (SAFE_X + 120 + dx) * s, (y + 52) * s, "СРОК:", C.font("head_l", 28 * s), C.GREY + (a,), 0.3)
        gx0, gx1 = SAFE_X + 230 + dx, SAFE_X + 560 + dx
        for xx in range(int(gx0), int(gx1), 14):
            d.rectangle([xx * s, (y + 54) * s, (xx + 7) * s, (y + 56) * s], fill=C.GREY2 + (a,))
        if k_flash <= 0 and (int(tt * 2 + i) % 2 == 0):
            d.rectangle([(gx0 + 4) * s, (y + 26) * s, (gx0 + 7) * s, (y + 56) * s], fill=C.WHITE + (a,))
        if k_flash > 0:
            af = int(255 * C.smoother(k_flash))
            C.tracked(d, ((gx0 + gx1) / 2) * s, (y + 52) * s, "—", C.font("head", 44 * s), C.RED + (af,), 0.0, "ms")
    return C.done(lay)
