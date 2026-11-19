#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Первая минута фильма — сцены 01-04, переделка 19.11 по журналу замечаний.

Правила этой минуты (его слово 19.11): план не дольше 5 с, кроме карты и
отрисовки; белого зала нет; субтитров нет; секунда паузы перед речью (она
сидит в timing.json вставкой сцены 01); лента фотографий едет одним
непрерывным движением; любой текст — внутри полей SAFE_X/SAFE_Y.
Сцена = список планов (секунда начала, функция плана), склейка жёсткая,
на части склеек короткий засвет.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import karta as K
import scenes_a as A
from core import W, H, SS
from cuts import CUTS

scene = A.scene
SAFE_X, SAFE_Y = 96, 54

# ── карта: Донбасс крупно и незанятая часть областей
K.CITIES.update({"Краматорск": (37.55, 48.72), "Славянск": (37.62, 48.85), "Покровск": (37.18, 48.28)})
DON = K.Okno(lon=(32.2, 43.0), lat=(46.0, 50.8))
# часть Донецкой и Луганской областей, которую армия России не заняла (приблизительно, руками)
FREE_DL = [(36.60, 47.62), (36.62, 48.02), (36.80, 48.32), (36.72, 48.52), (37.20, 49.02), (37.75, 49.10),
           (37.80, 48.98), (38.10, 48.86), (37.82, 48.62), (37.68, 48.52), (37.10, 48.46), (37.15, 48.28),
           (37.30, 47.98), (36.80, 47.86)]

_v = {}
_f = {}


def vid(key, name, start, **kw):
    if key not in _v:
        _v[key] = C.Vid(name, start, **kw)
    return _v[key]


def foto_bw(name):
    """фото архива, покрывающее кадр, чёрно-белое (кэш)"""
    if name not in _f:
        _f[name] = C.cover(C.foto(name), (W, H), 0.5, 0.2).convert("L").convert("RGB")
    return _f[name]


def shots(t, lst, dur):
    """lst: [(t0, fn), …] по порядку → (fn, время внутри плана, длина плана)"""
    for i, (t0, fn) in enumerate(lst):
        t1 = lst[i + 1][0] if i + 1 < len(lst) else dur
        if t < t1 or i == len(lst) - 1:
            return fn, max(0.0, t - t0), max(0.2, t1 - t0)
    return lst[-1][1], 0.0, 1.0


def flash(img, tt, d=0.1, a=0.7):
    """засвет на склейке: первые d секунд плана"""
    if tt >= d:
        return img
    k = a * (1 - tt / d)
    return Image.blend(img.convert("RGB"), Image.new("RGB", img.size, C.WHITE), k)


def modern(fr, t, k=0.22):
    """современная запись: чуть приглушить цвет, зерно, без царапин"""
    return C.film_look(fr, t, k, scratches=False)


def chronicle(fr, t, k=0.9):
    """хроника: чёрно-белая, зерно, царапины"""
    return C.film_look(fr.convert("L").convert("RGB"), t, k, scratches=True)


def fit_px(text, kind, px, maxw, track=0.0):
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    while px > 20 and C.text_w(d, text, C.font(kind, px * SS), track) / SS > maxw:
        px -= 4
    return px


def word(text, k, y, px=160, kind="head", color=C.WHITE, track=0.06, x=W / 2, anchor="ms", rise=40, maxw=W - 2 * SAFE_X):
    """крупное слово: всплывает снизу на rise px, внутри полей"""
    if k <= 0:
        return None
    px = fit_px(text, kind, px, maxw, track)
    kk = C.out_cubic(k)
    return C.text_layer([text], kind, px, color, x, y + (1 - kk) * rise, anchor, track, a=C.clamp(k * 2))


def red_line(k, x0, x1, y, w=5, a=255):
    if k <= 0:
        return None
    im = C.layer()
    d = ImageDraw.Draw(im)
    d.rectangle([x0 * SS, y * SS, (x0 + (x1 - x0) * C.out_cubic(k)) * SS, (y + w) * SS], fill=C.RED + (a,))
    return C.done(im)


def panel_look(fr, bw=False, k=0.3):
    """окно мозаики: зерно и плёнка ядра работают только на полном кадре — тут проще"""
    g = fr.convert("L").convert("RGB")
    return g if bw else Image.blend(fr, g, k)


def dark_video(fr, k=0.35):
    return C.fade(fr, k)


# ═════════════════════════ 01 · Абу-Даби, сделка ═════════════════════════
@scene("01")
def s01(t, dur):
    c_avtor = C.cue("01", "автора которой", 3.6)
    c_zel = C.cue("01", "Четырнадцатого ноября", 6.1)
    c_usa = C.cue("01", "что американская сторона", 9.0)
    c_ukr = C.cue("01", "Украина уходит", 11.56)
    c_nato = C.cue("01", "а взамен получает", 17.14)
    c_zem = C.cue("01", "Земля за гарантии", 19.33)
    c_kiev = C.cue("01", "Киев отказался", 20.76)

    def a_stol(tt, d):      # стол переговоров — движение с первого кадра
        fr = vid("abu0", "abu_dhabi_2026_11.mp4", 0.0, zoom=1.08).at(tt)
        img = C.kb(fr, tt / d, 0.07, 0.5, 0.45)
        img = modern(img, t)
        return C.over(img, C.caption("Абу-Даби", "ноябрь 2026", "Reuters", C.seg(tt, 0.3, 0.9)))

    def b_avtor(tt, d):     # Киссинджер, 1923–2023
        fr = vid("k100", "kissinger_100_2023.mp4", 10.0).at(tt)
        img = C.kb(fr.convert("L").convert("RGB"), tt / d, 0.06, 0.5, 0.4)
        img = C.film_look(img, t, 0.45, scratches=False)
        img = C.over(img, C.caption("Генри Киссинджер", "1923 — 2023", "CBS · май 2023", C.seg(tt, 0.2, 0.8)),
                     C.big_number("3 ГОДА", "его нет уже", None, C.seg(tt, 0.7, 1.5), cx=W * 0.70, cy=H * 0.40, px=190))
        return flash(img, tt, 0.08, 0.5)

    def c_zelensky(tt, d):  # Зеленский, Давос, январь 2026
        fr = vid("zel26", "abu_dhabi_2026_11.mp4", 15.0, zoom=1.16, cx=0.5, cy=0.0).at(tt)
        img = C.kb(fr, tt / d, 0.05, 0.5, 0.3)
        img = modern(img, t)
        return C.over(img, K.date_tag("14 ноября", C.seg(tt, 0.15, 0.7), sub="заявление журналистам"),
                      C.caption("Владимир Зеленский", "Давос · январь 2026", "Reuters", C.seg(tt, 0.3, 0.9)))

    def d_sdelka(tt, d):    # американская сторона: Трамп, Аляска
        fr = vid("alaska", "alaska_2025_08_15.mp4", 8.0, zoom=1.1, cx=0.5, cy=0.35).at(tt)
        img = C.kb(fr, tt / d, 0.06, 0.5, 0.4)
        img = modern(img, t)
        return C.over(img, word("СДЕЛКА", C.seg(tt, 0.25, 0.75), H * 0.46, 210),
                      red_line(C.seg(tt, 0.6, 1.3), W / 2 - 220, W / 2 + 220, H * 0.46 + 26),
                      C.caption("Анкоридж, Аляска", "август 2025", "AP", C.seg(tt, 0.3, 0.9)))

    def e_karta(tt, d):     # карта: линия и незанятая часть Донбасса — отрисовка, план длинный по праву
        base = K.base(DON)
        lay = [K.line_layer(K.LINE_NOW, C.seg(tt, 0.0, 1.4), okno=DON, dash=(16, 10), width=5),
               K.zone_layer(FREE_DL, C.seg(tt, 1.1, 2.3), okno=DON, hatch=True, fill_a=50),
               K.city_layer(["Донецк", "Луганск", "Краматорск", "Славянск", "Покровск"], C.seg(tt, 1.6, 2.4),
                            okno=DON, side={"Покровск": "l", "Краматорск": "l"}),
               K.date_tag("2026", C.seg(tt, 0.2, 0.9), sub="линия фронта")]
        c_ne = C.cue("01", "которую российская армия", 14.35) - c_ukr
        k_lab = C.seg(tt, c_ne, c_ne + 0.6)
        if k_lab > 0:
            x, y = DON.xy(36.45, 48.95)
            lay.append(C.text_layer(["ПОД КОНТРОЛЕМ КИЕВА"], "head_r", 30, C.WHITE, x, y, "rs", 0.16, a=k_lab))
        img = C.over(base, *lay).convert("RGB")
        img = C.kb(img, C.smoother(tt / d), 0.14, 0.52, 0.42)
        return C.grain(img, t, 0.03)

    def g_nato(tt, d):      # флаги НАТО
        fr = vid("nato", "nato_finland_2023.mp4", 3.0, zoom=1.05).at(tt)
        img = C.kb(fr, tt / d, 0.06, 0.5, 0.4)
        img = modern(img, t)
        return flash(C.over(img, word("ЧЛЕНСТВО В НАТО", C.seg(tt, 0.2, 0.7), H * 0.46, 150),
                            C.caption("Штаб-квартира НАТО", "Брюссель · апрель 2023", "NATO", C.seg(tt, 0.3, 0.9))),
                     tt, 0.1, 0.6)

    def h_otkaz(tt, d):     # «Земля за гарантии» — и красная черта поперёк
        fr = vid("abu20", "abu_dhabi_2026_11.mp4", 20.0, zoom=1.3, cx=0.5, cy=1.0).at(tt)   # сверху справа титр агентства — срезан
        img = dark_video(C.kb(fr, tt / d, 0.05, 0.5, 0.5), 0.3)
        k1 = C.seg(tt, 0.0, 0.5)
        tk = c_kiev - c_zem
        k2 = C.seg(tt, tk, tk + 0.45)
        k3 = C.seg(tt, tk + 0.15, tk + 0.75)
        px = fit_px("ЗЕМЛЯ ЗА ГАРАНТИИ", "head", 170, W - 2 * SAFE_X, 0.06)
        d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        tw = C.text_w(d0, "ЗЕМЛЯ ЗА ГАРАНТИИ", C.font("head", px * SS), 0.06) / SS
        return C.over(img, word("ЗЕМЛЯ ЗА ГАРАНТИИ", k1, H * 0.47, px),
                      red_line(k2, W / 2 - tw / 2 - 30, W / 2 + tw / 2 + 30, H * 0.47 - px * 0.36, 9),
                      word("КИЕВ ОТКАЗАЛСЯ", k3, H * 0.47 + 110, 64, "head_l", C.GREY, 0.3))

    fn, tt, d = shots(t, [(0.0, a_stol), (c_avtor, b_avtor), (c_zel, c_zelensky), (c_usa, d_sdelka),
                          (c_ukr, e_karta), (c_nato, g_nato), (c_zem, h_otkaz)], dur)
    img = fn(tt, d)
    return C.finish(img, t, dur, fi=0.0, fo=0.4, grain_k=0.0)


# ═════════════════════════ 02 · Автор и две редакции ═════════════════════════
REWIND = [("alaska_2025_a.jpg", "2025"), ("kremlin_kissinger_2017_a.jpg", "2017"), ("kremlin_kissinger_2016_a.jpg", "2016"),
          ("kremlin_kissinger_2013_a.jpg", "2013"), ("kremlin_kissinger_2012_a.jpg", "2012"), ("kremlin_kissinger_2008_a.jpg", "2008")]
REW_STEP = 0.45
_s02 = {}


def _plates():
    if "a" not in _s02:
        from scenes_c import plate_tex
        _s02["a"] = plate_tex("2022", "ЛИНИЯ 24 ФЕВРАЛЯ", "Давос, май: перемирие по линии до вторжения, Украина вне НАТО")
        _s02["b"] = plate_tex("2023", "УКРАИНА В НАТО", "Давос, январь: членство в НАТО — подходящий исход")
    return _s02["a"], _s02["b"]


def _mosaic_map():
    if "map" not in _s02:
        base = K.base()
        img = C.over(base, K.line_layer(K.LINE_NOW, 1.0), K.zone_layer(K.ZONE_2022, 1.0, hatch=True, fill_a=40),
                     K.zone_layer(K.CRIMEA, 1.0, fill_a=90, outline=False), K.zone_layer(K.DONBAS_OLD, 1.0, fill_a=90, outline=False))
        _s02["map"] = img.convert("RGB").resize((960, 540), Image.LANCZOS)
    return _s02["map"]


@scene("02")
def s02(t, dur):
    c_avtor = C.cue("02", "Её автор", 2.93)
    c_prich = C.cue("02", "Причём он изложил", 4.52)
    c_za = C.cue("02", "за первую его", 8.06)
    c_golos = C.cue("02", "голосом Кремля", 8.96)
    c_23 = C.cue("02", "в двадцать третьем", 10.59)
    c_teper = C.cue("02", "Теперь обе редакции", 13.04)
    c_segod = C.cue("02", "Сегодня разберём", 15.78)
    c_p = [C.cue("02", "что именно он говорил", 16.95), C.cue("02", "что из этого уже", 18.59),
           C.cue("02", "в чём он промахнулся", 20.48), C.cue("02", "и главное", 21.92)]
    c_terr = C.cue("02", "какие территории", 22.88)

    def s1_rewind(tt, d):   # назад по годам: несколько кадров подряд
        i = min(len(REWIND) - 1, int(tt / REW_STEP))
        name, year = REWIND[i]
        k = (tt - i * REW_STEP) / REW_STEP
        img = C.kb(foto_bw(name), k, 0.10, 0.5, 0.35)
        img = C.film_look(img, t, 0.4, scratches=False)
        img = C.over(img, K.date_tag(year, 1.0, y=150, px=120),
                     C.text_layer(["НЕ НА ПРОШЛОЙ НЕДЕЛЕ"], "head_l", 28, C.GREY, W - 110, 215, "rs", 0.3,
                                  a=C.seg(tt, 0.3, 0.8)))
        return flash(img, tt - i * REW_STEP, 0.06, 0.35)

    def s2_portret(tt, d):  # автор
        img = C.kb(foto_bw("kissinger_portrait_late.jpg"), tt / d, 0.08, 0.5, 0.3)
        img = C.film_look(img, t, 0.35, scratches=False)
        kn = C.seg(tt, 0.8, 1.3)
        return C.over(img, C.caption("Давос", "Всемирный экономический форум", "фото архива", C.seg(tt, 0.2, 0.8), y=140),
                      word("ГЕНРИ КИССИНДЖЕР", kn, H * 0.80, 120),
                      red_line(C.seg(tt, 1.1, 1.7), W / 2 - 330, W / 2 + 330, H * 0.80 + 22, 6))

    def s3_plates(tt, d):   # две редакции — две таблички
        from scenes_c import perspective_in
        pa, pb = _plates()
        bg = C.paper(W, H, seed=33, tone=(34, 32, 30)).filter(ImageFilter.GaussianBlur(2))
        img = bg.convert("RGBA")
        perspective_in(img, pa, W * 0.28 + 10 * math.sin(tt * 0.7), H * 0.50, 760, C.seg(tt, 0.2, 0.9), side=1)
        perspective_in(img, pb, W * 0.72 - 10 * math.sin(tt * 0.7 + 1), H * 0.50, 760, C.seg(tt, 1.3, 2.0), side=-1)
        img = img.convert("RGB")
        return C.over(img, word("ДВЕ РЕДАКЦИИ", C.seg(tt, 0.0, 0.5), 150, 56, "head_l", C.GREY, 0.3),
                      red_line(C.seg(tt, 0.3, 0.9), W / 2 - 60, W / 2 + 60, 166, 3))

    def s4_kreml(tt, d):    # голос Кремля
        fr = vid("putin", "ap_putin_kissinger.mp4", 1.0, zoom=1.16, cx=0.0, cy=1.0).at(tt)
        img = C.kb(fr, tt / d, 0.06, 0.4, 0.4)
        img = modern(img, t, 0.3)
        kq = C.seg(tt, c_golos - c_za, c_golos - c_za + 0.5)
        return C.over(img, C.caption("Москва, Кремль", "архив", "AP", C.seg(tt, 0.3, 0.9)),
                      word("«ГОЛОС КРЕМЛЯ»", kq, H * 0.30, 96, "serif_i", C.WHITE, 0.0))

    def s5_wef(tt, d):      # 2023, он сам переделал
        fr = vid("wef_b", "wef_2023_b.mp4", CUTS.get("wef_2023_s20", 3.5), zoom=1.06).at(tt)
        img = C.kb(fr, tt / d, 0.05, 0.5, 0.4)
        img = modern(img, t)
        return C.over(img, K.date_tag("2023", C.seg(tt, 0.15, 0.7), sub="вторая редакция"),
                      C.caption("Давос, видеосвязь", "январь 2023", "WEF", C.seg(tt, 0.3, 0.9)))

    def s6_stol(tt, d):     # обе редакции на одном столе
        from scenes_c import perspective_in
        pa, pb = _plates()
        fr = vid("abu9", "abu_dhabi_2026_11.mp4", 9.0, zoom=1.1).at(tt)
        img = modern(C.kb(fr, tt / d, 0.06, 0.5, 0.5), t).convert("RGBA")
        perspective_in(img, pa, W * 0.36, H * 0.62, 440, C.seg(tt, 0.3, 0.9), side=1)
        perspective_in(img, pb, W * 0.64, H * 0.62, 440, C.seg(tt, 0.7, 1.3), side=-1)
        img = img.convert("RGB")
        return C.over(img, C.caption("Абу-Даби", "ноябрь 2026", "Reuters", C.seg(tt, 0.2, 0.8)))

    def s7_mosaic(tt, d):   # четыре окна: что говорил · что сбылось · где ошибся · главное
        img = Image.new("RGB", (W, H), (9, 9, 11))
        words = ["ЧТО ГОВОРИЛ", "ЧТО СБЫЛОСЬ", "ГДЕ ОШИБСЯ", "ГЛАВНОЕ · ТЕРРИТОРИИ"]
        pos = [(0, 0), (962, 0), (0, 542), (962, 542)]
        lays = [C.text_layer(["СЕГОДНЯ РАЗБЕРЁМ"], "head_l", 40, C.GREY, W / 2, H / 2 + 14, "ms", 0.34,
                             a=C.seg(tt, 0.0, 0.4) * (1 - C.seg(tt, c_p[0] - c_segod - 0.3, c_p[0] - c_segod)))]
        for i in range(4):
            k = C.seg(tt, c_p[i] - c_segod, c_p[i] - c_segod + 0.35)
            if k <= 0:
                continue
            if i == 0:
                fr = panel_look(vid("rose", "charlie_rose_2014.mp4", 0.0, size=(958, 538)).at(tt), bw=True)
            elif i == 1:
                fr = panel_look(vid("alaska_m", "alaska_2025_08_15.mp4", 14.0, size=(958, 538), zoom=1.1, cx=0.5, cy=0.35).at(tt))
            elif i == 2:
                fr = panel_look(vid("nato_m", "nato_finland_2023.mp4", 5.0, size=(958, 538)).at(tt))
            else:
                fr = C.kb(_mosaic_map(), tt / d, 0.08, 0.7, 0.5, (958, 538))
            fr = C.fade(fr, 0.62)
            kk = C.out_cubic(k)
            sc = 0.9 + 0.1 * kk
            fw, fh = int(958 * sc), int(538 * sc)
            frs = fr.resize((fw, fh), Image.LANCZOS).convert("RGBA")
            frs.putalpha(int(255 * C.clamp(k * 2)))
            x, y = pos[i]
            img.paste(frs, (x + (958 - fw) // 2, y + (538 - fh) // 2), frs)
            lays.append(C.text_layer([words[i]], "head", 58, C.WHITE, x + 479, y + 269 + 20, "ms", 0.08, a=k))
            lays.append(red_line(C.seg(tt, c_p[i] - c_segod + 0.2, c_p[i] - c_segod + 0.7), x + 479 - 40, x + 479 + 40, y + 269 + 40, 3))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.03)

    def s8_karta(tt, d):    # карта: кто первым станет разменной монетой — линия рисуется
        base = K.base()
        lay = [K.line_layer(K.LINE_NOW, C.seg(tt, 0.1, 1.6), dash=(16, 10), width=5),
               K.zone_layer(K.CRIMEA, C.seg(tt, 1.2, 1.8), fill_a=90, outline=False),
               K.zone_layer(K.DONBAS_OLD, C.seg(tt, 1.6, 2.2), fill_a=90, outline=False),
               K.zone_layer(K.ZONE_2022, C.seg(tt, 2.0, 2.8), hatch=True, fill_a=40),
               K.city_layer(["Киев", "Харьков", "Донецк", "Луганск", "Запорожье", "Херсон"], C.seg(tt, 0.8, 1.6), side={"Херсон": "l"}),
               K.date_tag("2026", C.seg(tt, 0.3, 1.0), sub="разменная монета — кто первым")]
        img = C.over(base, *lay).convert("RGB")
        img = C.kb(img, C.smoother(tt / d), 0.07, 0.68, 0.55)
        return C.grain(img, t, 0.03)

    fn, tt, d = shots(t, [(0.0, s1_rewind), (c_avtor, s2_portret), (c_prich, s3_plates), (c_za, s4_kreml),
                          (c_23, s5_wef), (c_teper, s6_stol), (c_segod, s7_mosaic), (c_terr, s8_karta)], dur)
    img = fn(tt, d)
    return C.finish(img, t, dur, fi=0.0, fo=0.4, grain_k=0.0)


# ═════════════════════════ 03 · Три заморозки и титр ═════════════════════════
@scene("03")
def s03(t, dur):
    t_cy, t_minsk, t_title = 2.0, 4.1, 6.0

    def korea(tt, d):
        fr = vid("kor", "panmunjom_1953.mp4", 12.0, zoom=1.22, cx=0.0, cy=1.0).at(tt)
        img = chronicle(C.kb(fr, tt / d, 0.05, 0.5, 0.4), t)
        return C.over(img, K.date_tag("1953", C.seg(tt, 0.1, 0.6), sub="Корея · перемирие в Пханмунджоме"),
                      C.caption("Пханмунджом", "июль 1953", "British Pathé", C.seg(tt, 0.3, 0.9)))

    def cyprus(tt, d):
        fr = vid("cy", "cyprus_1974_un.mp4", 2.0, zoom=1.32, cx=0.1, cy=0.9).at(tt)
        img = chronicle(C.kb(fr, tt / d, 0.05, 0.5, 0.5), t, 0.8)
        return flash(C.over(img, K.date_tag("1974", C.seg(tt, 0.1, 0.6), sub="Кипр · зелёная линия ООН"),
                            C.caption("Никосия", "1974", "AP Archive", C.seg(tt, 0.3, 0.9))), tt, 0.08, 0.5)

    def minsk_map(tt, k_dark=1.0):
        base = K.base(DON)
        img = C.over(base, K.line_layer(K.LINE_2015, C.seg(tt, 0.0, 1.3), okno=DON, dash=(16, 10), width=5),
                     K.city_layer(["Донецк", "Луганск", "Мариуполь"], C.seg(tt, 0.5, 1.1), okno=DON),
                     K.date_tag("2015", C.seg(tt, 0.1, 0.6), sub="Минск · линия соприкосновения") if k_dark >= 1 else None).convert("RGB")
        return C.kb(img, tt / 4.5, 0.08, 0.6, 0.5)

    def minsk(tt, d):
        return C.grain(minsk_map(tt), t, 0.03)

    def title(tt, d):
        img = C.fade(minsk_map(tt + (t_title - t_minsk), 0.0), 0.32)
        k = C.seg(tt, 0.0, 0.7)
        px = int(300 * (1.12 - 0.12 * C.out_cubic(k)))
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        C.tracked(dd, W / 2 * SS, (H / 2 + 60) * SS, "ЛИНИЯ", C.font("head", px * SS), C.WHITE + (int(255 * C.clamp(k * 1.5)),), 0.10, "ms")
        img = C.over(img, lay, red_line(C.seg(tt, 0.5, 1.4), W / 2 - 330, W / 2 + 330, H / 2 + 92, 5),
                     word("последний прогноз Киссинджера", C.seg(tt, 0.9, 1.5), H / 2 + 165, 46, "serif_i", C.GREY, 0.02, rise=16))
        return C.vignette(img, 0.5)

    fn, tt, d = shots(t, [(0.0, korea), (t_cy, cyprus), (t_minsk, minsk), (t_title, title)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.6, grain_k=0.0)


# ═════════════════════════ 04 · Титр акта и лента жизни ═════════════════════════
T_ACT = 1.4
VEHI = [(1923, "Фюрт, Бавария", None), (1938, "эмиграция", "chamberlain_1938.jpg"),
        (1971, "тайно в Пекин", "kissinger_zhou_1971.jpg"), (1973, "Нобелевская премия", "nobel_1973.jpg"),
        (1994, "НАТО на восток", None), (2014, "колонка о линии", None),
        (2022, "Давос", "kissinger_portrait_late.jpg"), (2023, "сто лет", "kissinger_100_2023.jpg")]
STEP = 486          # шаг вех по ленте, px
X_FIRST = 120       # первая веха внутри ленты
OFF0 = W * 0.75 - X_FIRST                       # где лента в начале (первая веха входит справа)
OFF1 = 80 - (X_FIRST + STEP * (len(VEHI) - 1))  # где в конце (последняя веха у левого края)
_s04 = {}


def _strip():
    """вся лента одним слоем RGBA (рисуется один раз на процесс)"""
    if "strip" in _s04:
        return _s04["strip"]
    total = X_FIRST + STEP * (len(VEHI) - 1) + 400
    y = 600
    lay = C.layer(total, H)
    d = ImageDraw.Draw(lay)
    d.line([(0, y * SS), (total * SS, y * SS)], fill=C.GREY3 + (255,), width=2 * SS)
    f_year = C.font("head", 60 * SS)
    f_lab = C.font("head_l", 26 * SS)
    for i, (year, label, th) in enumerate(VEHI):
        x = X_FIRST + i * STEP
        d.line([(x * SS, (y - 36) * SS), (x * SS, (y + 10) * SS)], fill=C.RED + (255,), width=3 * SS)
        d.ellipse([(x - 6) * SS, (y - 6) * SS, (x + 6) * SS, (y + 6) * SS], fill=C.WHITE + (255,))
        C.tracked(d, x * SS, (y + 74) * SS, str(year), f_year, C.WHITE + (255,), 0.04, "ms")
        C.tracked(d, x * SS, (y + 110) * SS, label.upper(), f_lab, C.GREY + (255,), 0.22, "ms")
    big = C.done(lay, total, H)
    for i, (year, label, th) in enumerate(VEHI):
        tm = A._thumb(th, (360, 202)) if th else None
        if tm is None:
            continue
        card = Image.new("RGB", (tm.size[0] + 4, tm.size[1] + 4), C.GREY2)
        card.paste(tm, (2, 2))
        x = X_FIRST + i * STEP
        big.paste(card, (int(x - card.size[0] / 2), int(y - 70 - card.size[1])))
    _s04["strip"] = big
    return big


@scene("04")
def s04(t, dur):
    if t < T_ACT:   # титр акта — короткий и живой
        img = Image.new("RGB", (W, H), (6, 6, 7))
        doc = C.paper(W, H, seed=11, tone=(70, 66, 60)).filter(ImageFilter.GaussianBlur(5))
        img = Image.blend(img, doc, 0.22)
        img = C.kb(img, t / T_ACT, 0.04, 0.5, 0.5)
        k = C.seg(t, 0.0, 0.45)
        px = int(300 * (1.3 - 0.3 * C.out_cubic(k)))
        lay = C.layer()
        d = ImageDraw.Draw(lay)
        fn = C.font("serif_b", px * SS)
        tw = C.text_w(d, "I", fn)
        d.text((W / 2 * SS - tw / 2, (H / 2 + 20) * SS), "I", font=fn, fill=(0, 0, 0, 0),
               stroke_width=3 * SS, stroke_fill=C.GREY + (int(255 * k),), anchor="ls")
        img = C.over(img, lay, word("ЧЕЛОВЕК", C.seg(t, 0.25, 0.7), H / 2 + 110, 54, "head_l", C.WHITE, 0.32, rise=20),
                     red_line(C.seg(t, 0.5, 1.0), W / 2 - 40, W / 2 + 40, H / 2 + 150, 3))
        return C.grain(img, t, 0.03)
    tt = t - T_ACT
    dd = dur - T_ACT
    k = tt / dd                              # линейно: лента не останавливается
    x_off = OFF0 + (OFF1 - OFF0) * k
    img = Image.new("RGB", (W, H), C.BG)
    # задний план едет медленнее — параллакс
    pap = C.paper(W + 400, H, seed=23, tone=(30, 29, 32)).filter(ImageFilter.GaussianBlur(1.5))
    img.paste(pap, (int(-400 * k), 0))
    strip = _strip()
    img.paste(strip, (int(x_off), 0), strip)
    # неподвижная красная вертикаль по центру — вехи проходят сквозь линию
    img = C.over(img, red_line(1.0, W / 2 - 1, W / 2 + 1, 0, H, 150)).convert("RGB")
    img = A.light_sweep(img, k) if hasattr(A, "light_sweep") else img
    return C.finish(img, t, dur, fi=0.0, fo=0.5, grain_k=0.03, vig=0.3)
