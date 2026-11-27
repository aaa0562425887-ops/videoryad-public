#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Блок 1 «ВОЙНА» — сцены 12-29 (второй кусок, 192,8 с). Регистрируются в scenes.SCENES."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import fx
import karta as K
import vfx as V
from core import W, H, SS
from vfx import SAFE_X, SAFE_Y, word, label, red_line, flash, shots, dark_bg, black, fit_px
from scenes import scene, rel, NOVA, NOVA_BW, CAP_ZAPIS, CAP_1974, V0, G1, G1_FACE, BALKAN
from timing import O

# ── архив второго куска (реальное начало кусков — archiv/CUTS.tsv)
V3 = "v3_g2_0938.mp4"       # Горещо 2 с 575,68: 9:38–10:36 (Ванга о 1941 + Атидже Демирева)
V2 = "v2_g2_3050.mp4"       # Горещо 2 с 1848,16: 30:50–31:13 (Прага)
SELO = "b_g1_0920.mp4"      # Горещо 1 с 559,64: чб 1974, Ванга с людьми в доме
DOM = "b_g1_2115.mp4"       # Горещо 1 с 1272,44: чб 1974, очередь у дома
STENA = "b_g1_2755.mp4"     # Горещо 1 с 1673,72: 1974, Ванга у стены с людьми


def src(file_start, mmss):
    """секунда источника (мм:сс.с) → секунда куска"""
    m, s = mmss.split(":")
    return int(m) * 60 + float(s) - file_start


# хроника (кладёт mehanika в archiv/hronika/, реестр REESTR-HRONIKA.tsv); подписи — место · дата · источник
HRON = {
    "yugo": ("hronika/Invasion_of_Yugoslavia_and_Greece.ogv", 168.0, ("Югославия", "апрель 1941", "кинохроника · Мемориальный музей Холокоста США · public domain")),
    "praga": ("hronika/10_Soviet_Invasion_of_Czechoslovakia_CIA.jpg", ("Прага", "август 1968", "фото · ЦРУ · public domain")),
    "boris": ("hronika/Boris_III_of_Bulgaria_portrait.jpg", ("Царь Борис III", "портрет", "Викисклад · CC BY-SA 4.0")),
    "pohorony": ("hronika/Boris_III_funeral_train_1943.jpg", ("Болгария", "траур по царю · август 1943", "Викисклад · public domain")),
    "dvorec": ("hronika/Tzar_Palace_Sofia.jpg", ("София", "бывший царский дворец · современное фото", "Викисклад · CC BY-SA 3.0")),
    "hitler": ("hronika/Hitler_Portrait_Bundesarchiv_S62600.jpg", ("Гитлер", "портрет", "Бундесархив · CC BY-SA 3.0 de")),
    "stalin": ("hronika/Manezhnaya_Square_Stalin_funeral_1953.jpg", ("Москва", "март 1953", "Викисклад · public domain")),
}
CAP_ATIDZHE = ("Атидже Демирева", "подруга Ванги", "фильм Nova «Ванга: между два свята»")
CAP_PROF = ("проф. Н. Шипковенски", "запись беседы с Вангой", "фильм Nova «Ванга: между два свята»")


def r(sid, x):
    return rel(sid, O + x)


def foto_kb(key, tt, d, zoom=0.06, cx=0.5, cy=0.4, k_grade=0.6, cap_k=1.0):
    name, cap = HRON[key][0], HRON[key][-1]
    im = C.foto(name)
    img = C.kb(im, tt / max(d, 0.1), zoom, cx, cy)
    img = V.grade(img, k_grade)
    return C.over(img, C.caption(*cap, k=cap_k)).convert("RGB")


def act(name, num, k, sub=None):
    """титр блока: номер серым, слово крупно, красная черта"""
    lays = [label(num, C.seg(k, 0.0, 0.4), H * 0.5 - 150, 40),
            word(name, C.seg(k, 0.1, 0.6), H * 0.5 + 60, 190, "head", C.WHITE, 0.12, rise=36),
            red_line(C.seg(k, 0.45, 0.9), W / 2 - 200, W / 2 + 200, H * 0.5 + 92, 5)]
    if sub:
        lays.append(word(sub, C.seg(k, 0.6, 1.0), H * 0.5 + 170, 52, "serif_i", C.GREY, 0.0, rise=16))
    return lays


def perevod_lines(lines, ks, t, y0=196, px=44, step=56):
    lays = []
    n = len(lines)
    for i, (ln, k) in enumerate(zip(lines, ks)):
        if k > 0:
            nxt = ks[i + 1] if i + 1 < n else 0.0
            lays.append(fx.typed(ln, k, "head_r", px, C.WHITE, SAFE_X, y0 + i * step, 0.02, nxt <= 0, t))
    return lays


def okno_video(key, name, tt, s0, olga_file, olga_at, olga_dur, lines, line_ks, t, cap=CAP_ZAPIS, bw=0.0, push=0.025, **nova):
    """окно оригинала: архивное видео + осциллограмма + перевод по букве + подписи"""
    img = V.top_shade(V.vanga(key, name, tt, s0, push=push, hand=1.8, k_grade=0.75, bw=bw, **nova), 320, 0.6)
    env_v = V.envelope(name, s0, 12.0)
    env_o = V.envelope(olga_file, 0.0, olga_dur)
    lay = V.oscillo([(env_v, 0.0, C.WHITE), (env_o, olga_at, C.RED)], tt, H - 215, 46, SAFE_X, W - SAFE_X)
    k_orig = C.seg(tt, 0.2, 0.6) * (1 - C.seg(tt, olga_at - 0.3, olga_at + 0.1))
    k_per = C.seg(tt, olga_at, olga_at + 0.4) * (1 - C.seg(tt, olga_at + olga_dur + 0.3, olga_at + olga_dur + 0.9))
    lays = [lay, label("ОРИГИНАЛЬНЫЙ ЗВУК", k_orig, 120, 34, C.GREY, x=W - SAFE_X, anchor="rs"),
            label("ПЕРЕВОД ЗА КАДРОМ", k_per, 120, 34, C.RED, x=W - SAFE_X, anchor="rs"),
            C.caption(*cap, k=C.seg(tt, 0.4, 0.9))] + perevod_lines(lines, line_ks, t)
    return C.over(img, *lays).convert("RGB")


def date_card(text, k, sub=None, px=150):
    """чёрная карточка с датой крупно — перебивка"""
    img = C.kb(dark_bg(12, (12, 12, 14)), k, 0.03, 0.5, 0.5)
    lays = [word(text, C.seg(k, 0.0, 0.5), H * 0.5 + px * 0.36, px, "head", C.WHITE, 0.06, rise=20)]
    if sub:
        lays.append(label(sub, C.seg(k, 0.3, 0.7), H * 0.5 + px * 0.36 + 70, 30))
    return C.grain(C.over(img, *lays).convert("RGB"), k * 10, 0.035)


# ═════════════════════════ 12 · титр ВОЙНА · карта · Струмица ═════════════════════════
STRUM = K.Okno(lon=(19.8, 27.2), lat=(39.6, 43.8))
K.CITIES.update({"Салоники": (22.94, 40.64), "Скопье": (21.43, 41.99)})


@scene("12")
def s12(t, dur):
    c_41 = r("12", 0.12)
    c_strum = r("12", 2.84)
    c_styk = r("12", 3.42)
    c_let = r("12", 7.03)
    c_slepa = r("12", 8.39)
    c_hodyat = r("12", 9.75)
    c_syn = r("12", 11.16)
    c_muzh = r("12", 12.18)

    def a_title(tt, d):
        img = C.kb(dark_bg(9, (12, 12, 14)), tt / d, 0.03, 0.5, 0.5)
        k = C.seg(tt, 0.0, 1.0) * (1 - C.seg(tt, d - 0.5, d))
        img = C.over(img, *act("ВОЙНА", "01", C.seg(tt, 0.0, 1.0))).convert("RGB")
        img = C.fade(img, 1 - C.seg(tt, d - 0.5, d))
        return flash(C.grain(img, t, 0.035), tt, 0.1, 0.5)

    def b_map(tt, d):
        base = K.base(STRUM, hot="Bulgaria")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.8, 0, 255).astype(np.uint8), "RGB")
        x, y = STRUM.xy(*K.CITIES["Струмица"])
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        kr = C.seg(tt, 0.2, 0.6)
        for j in range(3):
            ph = (tt * 0.8 + j * 0.33) % 1.0
            rr = (10 + 150 * ph) * SS
            a = int(210 * (1 - ph) * kr)
            if a > 0:
                dd.ellipse([x * SS - rr, y * SS - rr, x * SS + rr, y * SS + rr], outline=C.RED + (a,), width=3 * SS)
        lays = [C.done(lay), K.city_layer(["Струмица"], C.seg(tt, c_strum - 1.8, c_strum - 1.4), okno=STRUM, px=40),
                K.date_tag("1941", C.seg(tt, 0.05, 0.5), sub="границы условные")]
        # три страны на стыке
        for i, (nm, lon, lat) in enumerate((("БОЛГАРИЯ", 24.6, 42.5), ("ЮГОСЛАВИЯ", 21.2, 42.6), ("ГРЕЦИЯ", 22.6, 40.4))):
            k = C.seg(tt, c_styk - 1.5 + i * 0.35, c_styk - 1.5 + i * 0.35 + 0.4)
            if k > 0:
                px_, py_ = STRUM.xy(lon, lat)
                lays.append(C.text_layer([nm], "head_l", 36, C.WHITE, px_, py_, "ms", 0.4, a=k))
        kl = C.seg(tt, c_let - 1.5, c_let - 1.1)
        if kl > 0:
            lays.append(C.big_number("30 ЛЕТ", None, "слепа с детства" if tt > c_slepa - 1.5 else None, kl, cx=W * 0.78, cy=H * 0.72, px=150, count_from=0, rings=False))
        img = C.over(base, *lays).convert("RGB")
        img = C.kb(img, tt / d, 0.10, x / W, y / H)
        return flash(C.grain(img, t, 0.03), tt, 0.08, 0.3)

    def c_selo(tt, d):
        img = V.vanga("selo", SELO, tt, src(559.64, "9:47"), push=0.05, hand=2.5, k_grade=0.7, bw=1.0, **NOVA_BW)
        lays = [C.caption(*CAP_1974, k=C.seg(tt, 0.3, 0.9)),
                label("К НЕЙ УЖЕ ХОДЯТ", C.seg(tt, 0.1, 0.5), 150, 40, x=SAFE_X, anchor="ls", track=0.3),
                red_line(C.seg(tt, 0.1, 0.5), SAFE_X, SAFE_X + 70, 164, 3)]
        k1 = C.seg(tt, c_syn - c_hodyat, c_syn - c_hodyat + 0.4)
        k2 = C.seg(tt, c_muzh - c_hodyat, c_muzh - c_hodyat + 0.4)
        lays.append(word("жив ли сын", k1, H * 0.60, 60, "serif_i", C.WHITE, 0.0, x=W - SAFE_X, anchor="rs", rise=16))
        lays.append(word("вернётся ли муж", k2, H * 0.60 + 80, 60, "serif_i", C.WHITE, 0.0, x=W - SAFE_X, anchor="rs", rise=16))
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    fn, tt, d = shots(t, [(0.0, a_title), (1.5, b_map), (c_hodyat, c_selo)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 13 · рассказала сама · профессору · под запись ═════════════════════════
@scene("13")
def s13(t, dur):
    c_chto = r("13", 13.58)
    c_prof = r("13", 18.15)
    c_zapis = r("13", 19.94)

    def a_sama(tt, d):
        img = V.vanga("v0l2", V0, tt, src(660.16, "11:14.2"), push=0.04, hand=2.0, k_grade=0.8, **NOVA)
        kw = C.seg(tt, c_chto + 1.6, c_chto + 2.0)   # «рассказала сама»
        lays = [C.caption(*CAP_ZAPIS, k=C.seg(tt, 0.3, 0.9)),
                word("РАССКАЗАЛА САМА", kw, H * 0.80, 90, "head", C.WHITE, 0.12, rise=24)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    def b_prof(tt, d):
        img = V.vanga("v0p", V0, tt, src(660.16, "11:10.3"), push=0.04, hand=2.0, k_grade=0.8, zoom=1.42, cx=0.42, cy=0.46)
        return flash(C.over(img, C.caption(*CAP_PROF, k=C.seg(tt, 0.1, 0.6))).convert("RGB"), tt, 0.06, 0.3)

    def c_rec(tt, d):
        fr = V.top_shade(V.vanga("v0l3", V0, tt, src(660.16, "11:16.0"), push=0.02, hand=1.5, k_grade=0.8, **NOVA), 260, 0.5)
        fr = fx.vidoiskatel(fr, tt, tc0=11 * 60 + 16, zoom_step=1, rec=True, bw=0.35)
        return flash(C.over(fr, word("ПОД ЗАПИСЬ", C.seg(tt, 0.1, 0.5), H - 150, 70, "head", C.WHITE, 0.14, rise=20),
                            C.caption(*CAP_ZAPIS, k=1.0)).convert("RGB"), tt, 0.06, 0.3)

    fn, tt, d = shots(t, [(0.0, a_sama), (c_prof, b_prof), (c_zapis, c_rec)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 14 · В1а ═════════════════════════
@scene("14")
def s14(t, dur):
    img = okno_video("v1a", V0, t, src(660.16, "11:13.5"), "olga_b1a.mp3", 2.3, 4.65,
                     ["Этот голос всегда со мной.", "И сейчас здесь. И вчера был. И завтра будет."],
                     [C.seg(t, 2.35, 3.9), C.seg(t, 4.0, 6.9)], t, **NOVA)
    return C.finish(flash(img, t, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 15 · МАРТ 1941 · В1б ═════════════════════════
@scene("15")
def s15(t, dur):
    T0 = 1.3
    if t < T0:
        return C.finish(date_card("МАРТ 1941", t / T0, "голос заговорил сильнее"), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)
    tt = t - T0
    img = okno_video("v1b", V0, tt, src(660.16, "11:27.0"), "olga_b1b.mp3", 2.3, 6.24,
                     ["Сильнее всего он заговорил в сорок первом году. С марта.", "Всё говорил и говорил: придёт время, будет война."],
                     [C.seg(tt, 2.35, 5.3), C.seg(tt, 5.5, 8.5)], t, **NOVA)
    return C.finish(flash(img, tt, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 16 · 5 АПРЕЛЯ 1941 · В1в ═════════════════════════
@scene("16")
def s16(t, dur):
    T0 = 1.3
    if t < T0:
        return C.finish(date_card("5 АПРЕЛЯ 1941", t / T0, "суббота"), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)
    tt = t - T0
    tv = min(tt, 15.3)
    img = okno_video("v1v", V0, tv, src(660.16, "12:05.0"), "olga_b1v.mp3", 2.3, 12.62,
                     ["Пятого апреля, в субботу, передо мной встал человек. На коне.",
                      "Он сказал мне, кто он. Вам я не скажу. И сказал: слушай.",
                      "Завтра начинается война. Ты будешь говорить людям, кто жив, а кто умер."],
                     [C.seg(tt, 2.35, 5.7), C.seg(tt, 6.0, 9.6), C.seg(tt, 9.9, 14.9)], t, **NOVA)
    if tt > 15.3:
        img = C.fade(img, 1 - 0.5 * C.seg(tt, 15.3, dur - T0))
    return C.finish(flash(img, tt, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 17 · 6 апреля 1941 · хроника вторжения ═════════════════════════
@scene("17")
def s17(t, dur):
    c_6 = r("17", 21.21)

    def a_cal(tt, d):
        img = C.kb(dark_bg(12, (12, 12, 14)), tt / d, 0.04, 0.5, 0.5)
        k = C.seg(tt, 0.1, 1.4)
        num = fx.flip_number(["3 АПРЕЛЯ", "4 АПРЕЛЯ", "5 АПРЕЛЯ", "6 АПРЕЛЯ"], k, W / 2, H * 0.47, 170)
        lays = [num, label("1941", C.seg(tt, 0.0, 0.4), H * 0.47 - 190, 44)]
        if k >= 1:
            lays.append(C.text_layer(["6 АПРЕЛЯ"], "head", 170, C.RED, W / 2, H * 0.47 + 170 * 0.36, "ms", 0.02, a=C.seg(tt, 1.4, 1.7)))
            lays.append(label("ВОСКРЕСЕНЬЕ", C.seg(tt, 1.5, 1.9), H * 0.47 + 130, 34))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    def b_hron(tt, d):
        name, s0, cap = HRON["yugo"]
        fr = V.vanga("yugo", name, tt, s0, zoom=1.0, cx=0.5, cy=0.5, push=0.03, hand=2.0, k_grade=0.8, bw=1.0)
        lays = [K.date_tag("6 АПРЕЛЯ 1941", C.seg(tt, 0.1, 0.5), sub="вторжение в Югославию"),
                C.caption(*cap, k=C.seg(tt, 0.3, 0.9))]
        return flash(C.over(fr, *lays).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_cal), (c_6, b_hron)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 18 · двор · солдаты · офицеры · ответ ═════════════════════════
@scene("18")
def s18(t, dur):
    c_dvor = r("18", 25.42)
    c_ofic = r("18", 27.75)
    c_odin = r("18", 29.58)
    c_otvet = r("18", 31.56)

    def a_stena(tt, d):
        img = V.vanga("stena", STENA, tt, src(1673.72, "28:00.5"), push=0.05, hand=2.5, k_grade=0.7, bw=0.9, **NOVA_BW)
        lays = [C.caption(*CAP_1974, k=C.seg(tt, 0.3, 0.9))]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    def b_ochered(tt, d):
        img = V.vanga("dom2", DOM, tt, src(1272.44, "21:36.0"), push=0.05, hand=2.5, k_grade=0.7, bw=0.9, **NOVA_BW)
        lays = [C.caption(*CAP_1974, k=1.0)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    def c_face(tt, d):
        img = V.vanga("g1a2", G1, tt, G1_FACE + 4.0, push=0.06, hand=2.5, k_grade=0.7, bw=1.0, **NOVA_BW)
        kw = C.seg(tt, c_otvet - c_odin, c_otvet - c_odin + 0.5)
        img = C.fade(img, 1 - 0.3 * kw)
        lays = [C.caption(*CAP_1974, k=1.0),
                word("ОТВЕТ, О КОТОРОМ ПОМНЯТ ДО СИХ ПОР", kw, H * 0.80, 76, "head", C.WHITE, 0.1, rise=24)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    fn, tt, d = shots(t, [(0.0, a_stena), (c_ofic, b_ochered), (c_odin, c_face)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 19 · В3: та держава проиграет ═════════════════════════
@scene("19")
def s19(t, dur):
    T_V = 11.0
    tv = min(t, T_V - 0.04)
    img = okno_video("v3", V3, tv, src(575.68, "9:52.5"), "olga_b3.mp3", 2.3, 9.48,
                     ["Сорок первый год. Во дворе полно солдат.", "И она говорит офицеру: скажи сегодня же.",
                      "Та держава, которая объявит войну большой России, эту войну проиграет."],
                     [C.seg(t, 2.35, 4.6), C.seg(t, 4.8, 7.2), C.seg(t, 7.4, 11.6)], t, **NOVA)
    if t > T_V:
        img = C.fade(img, 1 - 0.5 * C.seg(t, T_V, dur))
    return C.finish(flash(img, t, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 20-21 · шкала: апрель 1941 → 22 июня → май 1945 · Прага ═════════════════════════
def shkala(k_line, k_marks, k_ptr, k_brace=0.0, k_45=0.0):
    """горизонтальная шкала с тремя вехами; стрелка идёт от апреля к июню; скобка «больше двух месяцев»"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    x0, x1, y = SAFE_X + 60, W - SAFE_X - 60, H * 0.55
    xa, xb, xc = x0 + (x1 - x0) * 0.08, x0 + (x1 - x0) * 0.42, x1 - (x1 - x0) * 0.06
    d.line([(x0 * s, y * s), ((x0 + (x1 - x0) * C.out_cubic(k_line)) * s, y * s)], fill=(90, 90, 96, 255), width=2 * s)
    marks = [(xa, "АПРЕЛЬ 1941", "слова во дворе"), (xb, "22 ИЮНЯ 1941", "война"), (xc, "МАЙ 1945", "та держава проиграла")]
    for i, (x, big, small) in enumerate(marks):
        k = k_marks[i]
        if k <= 0:
            continue
        a = int(255 * C.smoother(k))
        col = C.RED if i == 2 and k_45 > 0 else C.WHITE
        d.ellipse([(x - 9) * s, (y - 9) * s, (x + 9) * s, (y + 9) * s], fill=col + (a,))
        f = C.font("head", 44 * s)
        C.tracked(d, x * s, (y - 36) * s, big, f, C.WHITE + (a,), 0.06, "ms")
        f2 = C.font("head_l", 26 * s)
        C.tracked(d, x * s, (y + 62) * s, small.upper(), f2, C.GREY + (a,), 0.3, "ms")
    if k_ptr > 0:
        xp = xa + (xb - xa) * C.smoother(k_ptr)
        d.line([(xa * s, (y + 4) * s), (xp * s, (y + 4) * s)], fill=C.RED + (255,), width=6 * s)
    if k_brace > 0:
        a = int(255 * k_brace)
        yb = y + 120
        d.line([(xa * s, yb * s), (xb * s, yb * s)], fill=C.GREY + (a,), width=2 * s)
        d.line([(xa * s, (yb - 12) * s), (xa * s, yb * s)], fill=C.GREY + (a,), width=2 * s)
        d.line([(xb * s, (yb - 12) * s), (xb * s, yb * s)], fill=C.GREY + (a,), width=2 * s)
        f = C.font("head_r", 40 * s)
        C.tracked(d, ((xa + xb) / 2) * s, (yb + 56) * s, "БОЛЬШЕ ДВУХ МЕСЯЦЕВ", f, C.WHITE + (a,), 0.1, "ms")
    if k_45 > 0:
        d.line([(xb * s, (y + 4) * s), ((xb + (xc - xb) * C.out_cubic(k_45)) * s, (y + 4) * s)], fill=C.RED + (255,), width=6 * s)
    return C.done(lay)


@scene("20")
def s20(t, dur):
    c_do = r("20", 34.12)
    c_mes = r("20", 36.2)
    img = C.kb(dark_bg(13, (14, 14, 17)), t / dur, 0.03, 0.5, 0.5)
    lay = shkala(C.seg(t, 0.1, 1.2), [C.seg(t, 0.6, 1.0), C.seg(t, 1.1, 1.5), C.seg(t, 1.5, 1.9)],
                 C.seg(t, c_do, c_do + 1.8), C.seg(t, c_mes, c_mes + 0.4))
    return C.finish(C.grain(C.over(img, lay).convert("RGB"), t, 0.035), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


@scene("21")
def s21(t, dur):
    c_pozhe = r("21", 37.39)
    c_praga = r("21", 41.0)
    c_tanki = r("21", 42.6)

    def a_shk(tt, d):
        img = C.kb(dark_bg(13, (14, 14, 17)), 1.0 + tt / d, 0.03, 0.5, 0.5)
        lay = shkala(1.0, [1.0, 1.0, 1.0], 1.0, 1.0, C.seg(tt, 0.1, 1.4))
        lays = [lay, label("ПО ЕЁ ЖЕ СЛОВАМ — ЗАРАНЕЕ", C.seg(tt, c_pozhe + 0.4, c_pozhe + 0.8), H - 120, 30)]
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.035)

    def b_praga(tt, d):
        img = foto_kb("praga", tt, d, 0.08, 0.5, 0.45, 0.7, C.seg(tt, 0.3, 0.9))
        lays = [K.date_tag("АВГУСТ 1968", C.seg(tt, c_tanki - c_praga, c_tanki - c_praga + 0.4), sub="танки в Праге"),
                word("ПРАГА", C.seg(tt, 0.05, 0.4), H * 0.80, 120, "head", C.WHITE, 0.12, rise=30)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_shk), (c_praga, b_praga)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 22 · В2: запомните Прагу ═════════════════════════
@scene("22")
def s22(t, dur):
    T_A = 4.0
    if t < T_A:
        img = okno_video("v2a", V2, t, src(1848.16, "31:05.0"), "olga_b2.mp3", 3.3, 6.01, [], [], t, **NOVA)
    else:
        tt = t - T_A
        img = okno_video("v2b", V2, tt, src(1848.16, "31:00.0"), "olga_b2.mp3", 3.3 - T_A, 6.01,
                         ["Голос сказал мне: запомните Прагу.", "Запомните, что там будет."],
                         [C.seg(t, 3.35, 6.3), C.seg(t, 6.5, 9.2)], t, **NOVA)
        img = flash(img, tt, 0.06, 0.3)
    return C.finish(flash(img, t, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 23 · слух идёт вверх · до дворца ═════════════════════════
@scene("23")
def s23(t, dur):
    c_sluh = r("23", 44.94)
    c_vverh = r("23", 47.3)
    c_dvorca = r("23", 48.1)

    def a_map(tt, d):
        base = K.base(BALKAN, hot="Bulgaria")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.8, 0, 255).astype(np.uint8), "RGB")
        kl = C.seg(tt, c_sluh + 0.3, c_vverh + 0.8)
        lays = [K.city_layer(["Петрич"], 1.0, okno=BALKAN, px=32),
                K.city_layer(["София"], C.seg(tt, c_vverh - 0.3, c_vverh + 0.2), okno=BALKAN, px=40),
                K.line_layer([K.CITIES["Петрич"], K.CITIES["София"]], kl, okno=BALKAN, width=4, dash=(16, 12), glow=True, head=True),
                K.date_tag("СЛУХ", C.seg(tt, 0.1, 0.5), sub="идёт вверх"),
                label("ДО САМОГО ДВОРЦА", C.seg(tt, c_dvorca - 0.2, c_dvorca + 0.3), H - 120, 34, C.WHITE)]
        img = C.over(base, *lays).convert("RGB")
        img = C.kb(img, tt / d, 0.08, 0.45, 0.35)
        return C.grain(img, t, 0.03)

    def b_dvorec(tt, d):
        img = foto_kb("dvorec", tt, d, 0.06, 0.5, 0.45, 0.6, C.seg(tt, 0.3, 0.9))
        return flash(img, tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_map), (c_dvorca + 0.3, b_dvorec)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 24 · 8 апреля 1942 · царь Борис · ореховая скорлупа · 28 августа ═════════════════════════
# условные границы: Вардарская Македония и Западная Фракия под болгарским управлением с 1941 — линии приблизительные
ZONE_MAK = [(20.55, 42.45), (21.6, 42.75), (22.4, 42.3), (23.0, 41.35), (22.9, 40.9), (21.8, 40.85), (20.6, 41.1)]
ZONE_FRAK = [(24.0, 41.45), (26.25, 41.5), (26.0, 40.75), (25.0, 40.85), (24.0, 40.95)]


@scene("24")
def s24(t, dur):
    c_8 = r("24", 49.03)
    c_plem = r("24", 52.83)
    c_vhod = r("24", 54.6)
    c_boris = r("24", 59.3)
    c_tayno = r("24", 60.4)
    c_rot = r("24", 61.4)
    c_pervoy = r("24", 62.9)
    c_rastet = r("24", 64.4)
    c_oreh = r("24", 66.0)
    c_den = r("24", 69.0)
    c_28 = r("24", 69.8)

    def a_dvorec(tt, d):
        img = foto_kb("dvorec", 1.0 + tt, d + 1.0, 0.05, 0.5, 0.45, 0.6, 1.0)
        lays = [K.date_tag("8 АПРЕЛЯ 1942", C.seg(tt, c_8, c_8 + 0.5)),
                label("ПО РАССКАЗУ ПЛЕМЯННИЦЫ ВАНГИ", C.seg(tt, c_plem, c_plem + 0.4), H - 120, 30),
                word("ЧЕЛОВЕК, КОТОРОГО ЗНАЕТ КАЖДЫЙ", C.seg(tt, c_vhod + 1.4, c_vhod + 1.9), H * 0.80, 70, "head", C.WHITE, 0.1, rise=24)]
        return C.over(img, *lays).convert("RGB")

    def b_boris(tt, d):
        name, cap = HRON["boris"][0], HRON["boris"][-1]
        im = C.foto(name)
        true = C.kb(im, tt / d, 0.05, 0.5, 0.3)
        base = Image.new("RGB", (W, H), (10, 10, 12))
        img = fx.proyavka(base, true, (W * 0.25, 0, W * 0.75, H), C.seg(tt, 0.0, 1.3), seed=7)
        img = V.grade(img, 0.5)
        lays = [C.caption(*cap, k=C.seg(tt, 0.6, 1.1)),
                word("ЦАРЬ БОРИС III", C.seg(tt, 0.2, 0.6), H * 0.80, 96, "head", C.WHITE, 0.12, rise=26),
                label("ПРИЕХАЛ ТАЙНО", C.seg(tt, c_tayno - c_boris, c_tayno - c_boris + 0.4), H * 0.80 + 60, 34),
                label("ОНА ГОВОРИТ ПЕРВОЙ", C.seg(tt, c_pervoy - c_boris, c_pervoy - c_boris + 0.4), H * 0.80 + 60, 34, C.WHITE)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.1, 0.5)

    def c_oreh_map(tt, d):
        base = K.base(BALKAN, hot="Bulgaria")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.8, 0, 255).astype(np.uint8), "RGB")
        kg = C.seg(tt, 0.1, 1.3)                                   # держава растёт
        ks = C.seg(tt, c_oreh - c_rastet + 0.6, c_oreh - c_rastet + 2.4)   # ореховая скорлупа: зона тает
        kz = kg * (1 - ks)
        lays = [K.zone_layer(ZONE_MAK, kz, okno=BALKAN, fill_a=80, outline=True, hatch=True),
                K.zone_layer(ZONE_FRAK, kz, okno=BALKAN, fill_a=80, outline=True, hatch=True),
                K.city_layer(["София"], 1.0, okno=BALKAN, px=34),
                K.date_tag("1942", C.seg(tt, 0.05, 0.4), sub="границы приблизительные"),
                word("ТВОЯ ДЕРЖАВА РАСТЁТ", C.seg(tt, 0.1, 0.5) * (1 - C.seg(tt, c_oreh - c_rastet, c_oreh - c_rastet + 0.3)), H - 150, 70, "head", C.WHITE, 0.12, rise=20),
                word("УМЕСТИТЬ В ОРЕХОВОЙ СКОРЛУПЕ", C.seg(tt, c_oreh - c_rastet + 0.3, c_oreh - c_rastet + 0.7), H - 150, 70, "head", C.WHITE, 0.12, rise=20)]
        img = C.over(base, *lays).convert("RGB")
        img = C.kb(img, tt / d, 0.06, 0.5, 0.45)
        return flash(C.grain(img, t, 0.03), tt, 0.06, 0.3)

    def d_den(tt, d):
        img = C.kb(dark_bg(14, (12, 12, 14)), tt / d, 0.04, 0.5, 0.5)
        k = C.seg(tt, c_28 - c_den, c_28 - c_den + 1.2)
        lays = [label("И ЗАПОМНИ ДЕНЬ", C.seg(tt, 0.0, 0.4), H * 0.5 - 220, 44)]
        if k > 0:
            lays.append(fx.flip_number(["3 ФЕВРАЛЯ", "17 МАЯ", "9 ИЮЛЯ", "28 АВГУСТА"], k, W / 2, H * 0.5, 190))
        if k >= 1:
            lays.append(C.text_layer(["28 АВГУСТА"], "head", 190, C.RED, W / 2, H * 0.5 + 190 * 0.36, "ms", 0.02, a=C.seg(tt, c_28 - c_den + 1.2, c_28 - c_den + 1.5)))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    fn, tt, d = shots(t, [(0.0, a_dvorec), (c_boris, b_boris), (c_rastet, c_oreh_map), (c_den, d_den)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 25 · портрет царя · В4 (подруга Ванги) ═════════════════════════
@scene("25")
def s25(t, dur):
    T0 = 1.5
    if t < T0:
        name, cap = HRON["boris"][0], HRON["boris"][-1]
        img = C.kb(C.foto(name), 0.5 + t, 0.05, 0.5, 0.3)
        img = V.grade(img, 0.5)
        img = C.over(img, C.caption(*cap, k=1.0), label("ПО РАССКАЗУ ПЛЕМЯННИЦЫ ВАНГИ", 1.0, H - 150, 30)).convert("RGB")
        return C.finish(img, t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)
    tt = t - T0
    img = okno_video("v4", V3, tt, src(575.68, "10:12.0"), "olga_b4.mp3", 2.3, 5.93,
                     ["Что царь Борис ездил к ней? А как же. Это все знают.", "А о чём говорили, не знает никто. Это было между ними двумя."],
                     [C.seg(tt, 2.35, 5.0), C.seg(tt, 5.2, 8.2)], t, cap=CAP_ATIDZHE, **NOVA)
    return C.finish(flash(img, tt, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 26 · 28 августа 1943 · София · 49 лет ═════════════════════════
def traur(k, date="28 АВГУСТА 1943", city="СОФИЯ"):
    """газетная полоса с траурной рамкой — оформление наше"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    a = int(255 * C.smoother(k))
    x0, y0, x1, y1 = SAFE_X + 120, SAFE_Y + 70, W - SAFE_X - 120, H - SAFE_Y - 70
    d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], outline=(230, 228, 224, a), width=14 * s)
    d.rectangle([(x0 + 26) * s, (y0 + 26) * s, (x1 - 26) * s, (y1 - 26) * s], outline=(230, 228, 224, a), width=3 * s)
    f = C.font("serif_b", 150 * s)
    C.tracked(d, W / 2 * s, (H * 0.47) * s, date, f, (236, 234, 230, a), 0.02, "ms")
    f2 = C.font("head_l", 40 * s)
    C.tracked(d, W / 2 * s, (H * 0.47 + 80) * s, city, f2, C.GREY + (a,), 0.5, "ms")
    f3 = C.font("head_l", 22 * s)
    C.tracked(d, W / 2 * s, (y1 - 48) * s, "ОФОРМЛЕНИЕ НАШЕ", f3, C.GREY2 + (a,), 0.3, "ms")
    return C.done(lay)


@scene("26")
def s26(t, dur):
    c_28 = r("26", 71.64)
    c_sofia = r("26", 75.0)
    c_umir = r("26", 76.08)
    c_49 = r("26", 77.54)

    def a_gazeta(tt, d):
        img = C.kb(dark_bg(15, (10, 10, 12)), tt / d, 0.04, 0.5, 0.5)
        return C.grain(C.over(img, traur(C.seg(tt, 0.0, 0.9))).convert("RGB"), t, 0.04)

    def b_pohorony(tt, d):
        img = foto_kb("pohorony", tt, d, 0.07, 0.5, 0.45, 0.6, C.seg(tt, 0.3, 0.9))
        lays = [word("ЦАРЬ БОРИС УМИРАЕТ", C.seg(tt, 0.1, 0.5), H * 0.80, 86, "head", C.WHITE, 0.12, rise=24)]
        k49 = C.seg(tt, c_49 - c_umir, c_49 - c_umir + 0.9)
        if k49 > 0:
            img = C.fade(img, 1 - 0.4 * k49)
            lays.append(C.big_number("49 ЛЕТ", None, None, k49, cx=W / 2, cy=H * 0.45, px=300, count_from=0))
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_gazeta), (c_umir, b_pohorony)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 27 · легенда ещё выше · Гитлер · по легенде ═════════════════════════
EUROPE = K.Okno(lon=(-11.0, 42.0), lat=(34.5, 61.0))


@scene("27")
def s27(t, dur):
    c_dalshe = r("27", 79.08)
    c_vyshe = r("27", 81.2)
    c_chel = r("27", 82.39)
    c_rassk = r("27", 86.39)
    c_gitler = r("27", 87.4)
    c_uslysh = r("27", 89.9)
    c_ne = r("27", 91.0)
    c_proigr = r("27", 92.4)
    c_vyshel = r("27", 93.3)

    def a_vyshe(tt, d):
        base = K.base(EUROPE, hot="Germany")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.5, 0, 255).astype(np.uint8), "RGB")
        kd = C.seg(tt, c_chel - 0.2, c_chel + 1.5)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        bx, by = EUROPE.xy(13.4, 52.5)
        for j in range(3):
            ph = (tt * 0.45 + j * 0.33) % 1.0
            rr = (20 + 900 * ph) * SS
            a = int(140 * (1 - ph) * kd)
            if a > 0:
                dd.ellipse([bx * SS - rr, by * SS - rr, bx * SS + rr, by * SS + rr], outline=C.RED + (a,), width=3 * SS)
        lays = [C.done(lay), K.date_tag("ЛЕГЕНДА", C.seg(tt, c_dalshe, c_dalshe + 0.5), sub="идёт ещё выше"),
                word("КОТОРОГО БОЯЛАСЬ ВСЯ ЕВРОПА", C.seg(tt, c_chel + 0.3, c_chel + 0.8), H - 150, 76, "head", C.WHITE, 0.1, rise=24)]
        img = C.over(base, *lays).convert("RGB")
        img = C.kb(img, tt / d, 0.08, 0.5, 0.45)
        return C.grain(img, t, 0.03)

    def b_gitler(tt, d):
        img = foto_kb("hitler", tt, d, 0.06, 0.5, 0.3, 0.7, C.seg(tt, 0.4, 0.9))
        img = C.fade(img, 0.75)
        k_leg = C.seg(tt, 0.05, 0.45)
        lays = [C.text_layer(["ПО ЛЕГЕНДЕ"], "head", 64, C.GREY, W - SAFE_X, 150, "rs", 0.2, a=k_leg),
                red_line(k_leg, W - SAFE_X - 330, W - SAFE_X, 164, 3)]
        k1 = C.seg(tt, c_ne - c_gitler, c_ne - c_gitler + 0.9)
        k2 = C.seg(tt, c_proigr - c_gitler, c_proigr - c_gitler + 0.6)
        if k1 > 0:
            lays.append(fx.typed("«Не трогай Россию.", k1, "serif", 66, C.WHITE, SAFE_X, H * 0.62, 0.0, k2 <= 0, t))
        if k2 > 0:
            lays.append(fx.typed("Проиграешь».", k2, "serif", 66, C.WHITE, SAFE_X, H * 0.62 + 90, 0.0, True, t))
        out = C.over(img, *lays).convert("RGB")
        kv = C.seg(tt, c_vyshel - c_gitler, c_vyshel - c_gitler + 1.6)
        if kv > 0:
            out = C.fade(out, 1 - 0.85 * kv)
            if kv < 0.5:
                out = fx.glitch(out, 0.3 * kv, seed=int(t * 30), slices=8, shift=40, rgb=8)
        return flash(out, tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_vyshe), (c_gitler, b_gitler)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 28 · 1952 · смерть Сталина · сажают · март 1953 ═════════════════════════
@scene("28")
def s28(t, dur):
    c_esche = r("28", 95.43)
    c_52 = r("28", 97.0)
    c_vidit = r("28", 98.34)
    c_sazh = r("28", 101.0)
    c_mart = r("28", 102.3)
    c_vypusk = r("28", 104.3)

    def a_52(tt, d):
        img = C.kb(dark_bg(16, (12, 12, 14)), tt / d, 0.04, 0.5, 0.5)
        lays = [label("ЕЩЁ ОДИН РАССКАЗ", C.seg(tt, c_esche, c_esche + 0.4), 150, 40, x=SAFE_X, anchor="ls", track=0.3),
                red_line(C.seg(tt, c_esche, c_esche + 0.4), SAFE_X, SAFE_X + 70, 164, 3)]
        k52 = C.seg(tt, c_52, c_52 + 0.5)
        lays.append(word("1952", k52, H * 0.5 + 100, 300, "head", C.WHITE, 0.02, rise=30))
        kv = C.seg(tt, c_vidit + 0.9, c_vidit + 1.4)
        lays.append(word("ВИДИТ СМЕРТЬ СТАЛИНА", kv, H * 0.5 + 200, 70, "head", C.WHITE, 0.12, rise=20))
        ks = C.seg(tt, c_sazh, c_sazh + 0.5)
        if ks > 0:
            # решётка: вертикальные полосы падают сверху
            lay = C.layer()
            dd = ImageDraw.Draw(lay)
            for i in range(9):
                x = SAFE_X + 60 + i * (W - 2 * SAFE_X - 120) / 8
                hh = H * C.out_cubic(C.clamp(ks * 1.3 - i * 0.03))
                dd.rectangle([(x - 7) * SS, 0, (x + 7) * SS, hh * SS], fill=(40, 40, 44, 230))
            lays.append(C.done(lay))
            lays.append(word("ЗА ЭТО ЕЁ САЖАЮТ", C.seg(tt, c_sazh + 0.3, c_sazh + 0.7), H - 150, 70, "head", C.WHITE, 0.12, rise=20))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    def b_1953(tt, d):
        img = foto_kb("stalin", tt, d, 0.06, 0.5, 0.4, 0.7, C.seg(tt, 0.3, 0.9))
        kv = C.seg(tt, c_vypusk - c_mart, c_vypusk - c_mart + 0.5)
        lays = [K.date_tag("МАРТ 1953", C.seg(tt, 0.1, 0.5)),
                word("И ЕЁ ВЫПУСКАЮТ", kv, H - 150, 70, "head", C.WHITE, 0.12, rise=20)]
        if kv > 0:
            img = Image.blend(img, Image.new("RGB", (W, H), (236, 234, 230)), 0.25 * kv)
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_52), (c_mart, b_1953)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 29 · царь приезжал тайно · тридцать лет · с милицией ═════════════════════════
@scene("29")
def s29(t, dur):
    c_car = r("29", 105.86)
    c_30 = r("29", 107.46)
    c_dveri = r("29", 108.84)
    c_mil = r("29", 111.3)

    def a_tayno(tt, d):
        img = V.vanga("dom3", DOM, tt, src(1272.44, "21:16.0"), push=0.05, hand=2.5, k_grade=0.7, bw=0.9, **NOVA_BW)
        lays = [C.caption(*CAP_1974, k=C.seg(tt, 0.3, 0.9)),
                word("ТАЙНО", C.seg(tt, c_car + 0.9, c_car + 1.3), H * 0.80, 96, "head", C.WHITE, 0.14, rise=24)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    def b_30(tt, d):
        img = V.vanga("dom4", DOM, tt, src(1272.44, "21:25.0"), push=0.05, hand=2.5, k_grade=0.7, bw=0.9, **NOVA_BW)
        k = C.seg(tt, 0.1, 1.2)
        lays = [C.caption(*CAP_1974, k=1.0),
                fx.flip_number(["1942", "1952", "1962", "1972"], k, W * 0.75, H * 0.40, 200),
                label("ТРИДЦАТЬ ЛЕТ СПУСТЯ", C.seg(tt, 0.2, 0.6), H * 0.40 + 100, 34, x=W * 0.75)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    def c_mil_(tt, d):
        img = V.vanga("dom5", DOM, tt, src(1272.44, "21:36.5"), push=0.06, hand=2.5, k_grade=0.7, bw=0.9, **NOVA_BW)
        km = C.seg(tt, c_mil - c_dveri, c_mil - c_dveri + 0.4)
        img = C.fade(img, 1 - 0.45 * km)
        lays = [C.caption(*CAP_1974, k=1.0),
                word("НЕ ПРЯЧАСЬ", C.seg(tt, 1.0, 1.4) * (1 - km), H * 0.80, 86, "head", C.WHITE, 0.12, rise=24),
                word("С МИЛИЦИЕЙ", km, H * 0.80, 120, "head", C.WHITE, 0.12, rise=30)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    fn, tt, d = shots(t, [(0.0, a_tayno), (c_30, b_30), (c_dveri, c_mil_)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.6, grain_k=0.03, vig=0.3)
