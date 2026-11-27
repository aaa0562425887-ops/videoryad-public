#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Фильм «Будущее Путина и России 2027. Что предсказала Ванга» — блок 0 «ХУК»,
сцены 01-11 (первая минута, 110,5 с, до титра названия).

Правила: план ≤5 с (карта и отрисовка — исключение), движение с первого кадра,
без субтитров, текст в полях 96/54, подписи честные (место · дата · источник),
красный — только линия и числа. Паузы и врезки — вставки в начало сцены
(timing.py). Времена фраз — секунды озвучки golos/golos.mp3 (по тишинам и .srt),
переводятся в секунды сцены rel().
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import fx
import karta as K
import vfx as V
from core import W, H, SS
from vfx import SAFE_X, SAFE_Y, word, label, red_line, flash, shots, dark_bg, black, fit_px

SCENES = {}


def scene(sid):
    def deco(fn):
        SCENES[sid] = fn
        return fn
    return deco


def rel(sid, v):
    """секунда озвучки → секунда сцены (с учётом вставки в начале)"""
    s = C.scene_info(sid)
    mid = sum(m for vm, m in s.get("mid", []) if v >= vm - 0.2)
    return v - s["voice_start"] + s["insert"] + mid


# ── архив (куски без перекодирования, реальное начало — archiv/CUTS.tsv)
V0 = "v0_g2_1103.mp4"        # Горещо 2, кусок с 660,16 с: беседа с проф. Шипковенски
V0_B0 = 703.0 - 660.16       # 11:43 — «ще дойде време, ще има война…»
V0_LISTEN = 674.0 - 660.16   # 11:14 — слушает вопрос
G1 = "b_g1_2438.mp4"         # Горещо 1, кусок с 1473,08 с: чб Петрич 1974
G1_FACE = 1484.0 - 1473.08   # 24:44 лицо крупно
G1_PRIEM = 1505.0 - 1473.08  # 25:05 принимает посетителя
FE = "b_fe_1556.mp4"         # Феномен, кусок с 951,24: 16:00 лицо в платке
FE_FACE = 960.0 - 951.24

CAP_1974 = ("Ванга", "Петрич · 1974", "архив · фильм Nova «Ванга: между два свята»")
CAP_ZAPIS = ("Ванга", "запись беседы с проф. Шипковенски", "фильм Nova «Ванга: между два свята»")
# кроп 720p-кадра Nova: логотип сверху слева и вшитые субтитры снизу остаются за краем
NOVA = dict(zoom=1.42, cx=0.5, cy=0.46)
NOVA_BW = dict(zoom=1.46, cx=0.5, cy=0.45)


# ═════════════════════════ 01 · 2027 ═════════════════════════
@scene("01")
def s01(t, dur):
    c_god = rel("01", 0.12)
    k = C.seg(t, 0.12, 1.05)
    img = V.cifry_frame(k, t, px=440, glow=1.0 if k >= 1 else 0.6 * k)
    kl = C.seg(t, c_god + 0.9, c_god + 1.4)
    img = C.over(img, label("ГОД, КОТОРЫЙ ЕЙ ПРИПИСЫВАЮТ", kl, H * 0.5 + 300, 30)).convert("RGB")
    return C.finish(img, t, dur, fi=0.0, fo=0.0, grain_k=0.04, vig=0.0)


# ═════════════════════════ 02 · заголовки одно за другим ═════════════════════════
ORDER = ["vt", "unilad", "newsner", "skyhistory"]


def stack_cards(tt, k_list, focus=None):
    """стопка карточек изданий: приходят по одной с наклоном, верхняя — в фокусе"""
    img = dark_bg(5, (16, 16, 19))
    img = C.kb(img, tt, 0.03, 0.5, 0.5)
    lays = []
    pos = [(W * 0.50, H * 0.50, 0.92, 0.0, 0.0), (W * 0.56, H * 0.52, 1.0, -0.6, -2.5),
           (W * 0.46, H * 0.50, 1.0, 0.6, 2.0), (W * 0.52, H * 0.54, 1.02, -0.3, -1.0)]
    for i, (name, k) in enumerate(zip(ORDER, k_list)):
        if k <= 0:
            continue
        kk = C.out_cubic(k)
        cx, cy, sc, tilt, rot = pos[i]
        dx = (1 - kk) * (W * 0.55 if i % 2 else -W * 0.55)
        card = V.page_card(name)
        lays.append(V.card_layer(card, cx + dx, cy, scale=sc * (0.88 + 0.12 * kk), tilt=tilt * (1 - 0.5 * kk), rot=rot, a=min(1.0, k * 2)))
    return C.over(img, *lays).convert("RGB")


@scene("02")
def s02(t, dur):
    c_osen = rel("02", 2.43)
    c_odno = rel("02", 5.40)
    c_knach = rel("02", 8.54)
    c_putin = rel("02", 10.60)
    c_ne = rel("02", 11.55)

    def a_first(tt, d):
        # остаток цифр гаснет, первая карточка влетает
        img = V.cifry_frame(1.0, t, px=440, a=1 - C.seg(tt, 0.0, 0.7), glow=0.4)
        k1 = C.seg(tt, 0.65, 1.2)
        if k1 > 0:
            over = stack_cards(tt, [k1, 0, 0, 0])
            img = Image.blend(img, over, C.clamp(k1 * 3))
            img = C.over(img, V.outlet_tag("vt", C.seg(tt, 0.9, 1.3))).convert("RGB")
        return flash(img, tt - 0.65, 0.08, 0.5) if tt >= 0.65 else img

    def b_stack(tt, d):
        step = 0.75
        ks = [1.0] + [C.seg(tt, i * step, i * step + 0.5) for i in range(1, 4)]
        img = stack_cards(tt + 1.2, ks)
        top = max(i for i, k in enumerate(ks) if k > 0)
        name = ORDER[top]
        img = C.over(img, V.outlet_tag(name, C.seg(tt, top * step + 0.05, top * step + 0.4) if top else 1.0),
                     label("ОСЕНЬ 2026 · ОДНА И ТА ЖЕ СТРОКА", C.seg(tt, 1.8, 2.3), H - 120, 30)).convert("RGB")
        return flash(img, tt - top * step, 0.06, 0.25) if top else img

    def c_line(tt, d):
        img, box = V.sentence_view("newsner", C.seg(tt, 0.6, d - 0.3), t)
        img = V.top_shade(img, 240, 0.5)
        x0, y0, x1, y1 = box
        k_u = C.seg(tt, c_ne - c_knach, c_ne - c_knach + 0.7)
        lays = [red_line(k_u, x0 - 6, x1 + 6, y1 + 6, 5),
                V.outlet_tag("newsner", 1.0, y=120),
                label("ПЕРЕВОД — В ТЕКСТЕ ДИКТОРА", C.seg(tt, 0.4, 0.9), H - 120, 26, C.GREY2)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_first), (c_odno, b_stack), (c_knach, c_line)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.25)


# ═════════════════════════ 03 · строка подчёркнута · женщина · 1996 · город ═════════════════════════
K.CITIES.update({"Петрич": (23.21, 41.40), "Струмица": (22.64, 41.44), "София": (23.32, 42.70),
                 "Москва": (37.62, 55.75), "Киев": (30.52, 50.45), "Минск": (27.56, 53.90), "Тбилиси": (44.80, 41.72),
                 "Кишинёв": (28.86, 47.01), "Астана": (71.43, 51.17), "Баку": (49.87, 40.41), "Ереван": (44.51, 40.18),
                 "Вильнюс": (25.28, 54.69), "Рига": (24.11, 56.95), "Таллин": (24.75, 59.44), "Ташкент": (69.24, 41.30),
                 "Бишкек": (74.59, 42.87)})
BALKAN = K.Okno(lon=(17.5, 30.5), lat=(38.8, 46.0))
EURASIA = K.Okno(lon=(14.0, 92.0), lat=(34.0, 68.0))


@scene("03")
def s03(t, dur):
    c_stroku = rel("03", 13.73)
    c_umerla = rel("03", 15.90)
    c_god96 = rel("03", 16.80)
    c_slep = rel("03", 17.90)
    c_gorod = rel("03", 18.80)

    def a_hold(tt, d):
        img, box = V.sentence_view("newsner", 1.0, t)
        img = V.top_shade(C.kb(img, tt / 4, 0.03, 0.6, 0.45), 240, 0.5)
        x0, y0, x1, y1 = box
        pulse = 0.75 + 0.25 * math.sin(tt * 6)
        lays = [red_line(1.0, x0 - 6, x1 + 6, y1 + 6, 5, int(255 * pulse)),
                V.outlet_tag("newsner", 1.0, y=120)]
        k_w = C.seg(tt, c_stroku + 0.1, c_stroku + 0.6)
        if k_w > 0:
            img = C.fade(img, 1 - 0.45 * k_w)
            lays.append(word("ПРИПИСЫВАЮТ ЖЕНЩИНЕ", k_w, H * 0.78, 96, "head", C.WHITE, 0.1, rise=30))
        return C.over(img, *lays).convert("RGB")

    def b_1996(tt, d):
        img = C.kb(dark_bg(8), tt / d, 0.06, 0.5, 0.5)
        k = C.seg(tt, 0.05, 0.9)
        num = fx.flip_number(["1911", "1941", "1979", "1996"], k, W / 2, H * 0.48, 300)
        lays = [num, label("УМЕРЛА", C.seg(tt, 0.0, 0.4), H * 0.48 - 250, 40)]
        if k >= 1:
            lays.append(C.text_layer(["1996"], "head", 300, C.RED, W / 2, H * 0.48 + 300 * 0.36, "ms", 0.02, a=C.seg(tt, 0.9, 1.2)))
        ks = C.seg(tt, c_slep - c_umerla, c_slep - c_umerla + 0.4)
        lays.append(word("СЛЕПАЯ", ks, H * 0.48 + 300 * 0.36 + 120, 86, "head", C.WHITE, 0.14, rise=24))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    def c_map(tt, d):
        base = K.base(BALKAN, hot="Bulgaria")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.8, 0, 255).astype(np.uint8), "RGB")
        x, y = BALKAN.xy(*K.CITIES["Петрич"])
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        for j in range(3):
            ph = (tt * 0.9 + j * 0.33) % 1.0
            r = (12 + 160 * ph) * SS
            a = int(210 * (1 - ph))
            dd.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], outline=C.RED + (a,), width=3 * SS)
        img = C.over(base, C.done(lay), K.city_layer(["Петрич"], C.seg(tt, 0.15, 0.55), okno=BALKAN, px=36),
                     K.date_tag("БОЛГАРИЯ", C.seg(tt, 0.05, 0.5), sub="карта условная"),
                     label("МАЛЕНЬКИЙ ГОРОД У ГРАНИЦЫ", C.seg(tt, 0.7, 1.1), H - 120, 30))
        img = C.kb(img.convert("RGB"), tt / d, 0.12, x / W, y / H)
        return C.grain(img, t, 0.03)

    fn, tt, d = shots(t, [(0.0, a_hold), (c_umerla, b_1996), (c_gorod, c_map)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 04 · Ванга без слов · цитата 02 ═════════════════════════
@scene("04")
def s04(t, dur):
    c_ei = rel("04", 21.00)
    c_vse = rel("04", 23.00)
    c_ost = rel("04", 25.26)
    c_slava = rel("04", 27.10)

    def a_silent(tt, d):
        img = V.vanga("g1a", G1, tt, G1_FACE, push=0.05, hand=2.5, k_grade=0.7, bw=1.0, **NOVA_BW)
        lays = [C.caption(*CAP_1974, k=C.seg(tt, 0.6, 1.3))]
        k_ei = C.seg(tt, c_ei + 0.1, c_ei + 0.5)
        if k_ei > 0:
            img = C.fade(img, 1 - 0.35 * k_ei)
            lays.append(label("ЕЙ ЖЕ ПРИПИСЫВАЮТ ДРУГОЕ", k_ei, H * 0.5, 44, C.WHITE, track=0.3))
        return C.over(img, *lays).convert("RGB")

    def b_quote(tt, d):
        img = C.kb(dark_bg(9, (14, 14, 17)), tt / d, 0.04, 0.5, 0.5)
        ks = [C.seg(tt, 0.0, 0.5), C.seg(tt, c_ost - c_vse, c_ost - c_vse + 0.5), C.seg(tt, c_slava - c_vse, c_slava - c_vse + 0.5)]
        lays = V.quote_lines(["Всё растает, словно лёд.", "Останется слава Владимира.", "Слава России."], ks,
                             num="02", num_k=C.seg(tt, 0.0, 0.3), src="приписывают Ванге · кто записал — через несколько минут",
                             src_k=C.seg(tt, c_slava - c_vse + 1.0, c_slava - c_vse + 1.5))
        return C.grain(C.over(img, V.big_quote_mark(C.seg(tt, 0.0, 0.4)), *lays).convert("RGB"), t, 0.035)

    fn, tt, d = shots(t, [(0.0, a_silent), (c_vse, b_quote)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 05 · цитата 03 · долго · до самой смерти ═════════════════════════
@scene("05")
def s05(t, dur):
    c_tretie = rel("05", 28.54)
    c_chel = rel("05", 29.59)
    c_dolgo = rel("05", 33.00)
    c_smert = rel("05", 34.50)
    img = C.kb(dark_bg(9, (14, 14, 17)), t / dur, 0.04, 0.5, 0.5)
    k_pred = C.seg(t, c_chel, c_chel + 0.5)
    k_posle = C.seg(t, c_chel + 1.4, c_chel + 1.9)
    k1 = C.seg(t, c_dolgo, c_dolgo + 1.0)
    k2 = C.seg(t, c_smert, c_smert + 0.9)
    lays = [label("03", C.seg(t, c_tretie, c_tretie + 0.3), 150, 40, x=SAFE_X, anchor="ls", track=0.3),
            red_line(C.seg(t, c_tretie, c_tretie + 0.3), SAFE_X, SAFE_X + 70, 164, 3),
            label("О ЧЕЛОВЕКЕ, КОТОРЫЙ ПРИДЁТ В КРЕМЛЬ", k_pred, H * 0.34, 34, C.GREY, x=SAFE_X + 30, anchor="ls", track=0.3),
            word("ПОСЛЕ ЕЛЬЦИНА", k_posle, H * 0.34 + 96, 84, "head", C.WHITE, 0.1, x=SAFE_X + 30, anchor="ls", rise=22)]
    if k1 > 0:
        lays.append(fx.typed("«Он будет править долго.", k1, "serif", 66, C.WHITE, SAFE_X + 30, H * 0.62, 0.0, k2 <= 0, t))
    if k2 > 0:
        lays.append(fx.typed("До самой смерти».", k2, "serif", 66, C.WHITE, SAFE_X + 30, H * 0.62 + 96, 0.0, True, t))
        # черта «долго» уходит за край кадра
        kl = C.seg(t, c_smert + 0.3, c_smert + 2.4)
        lays.append(red_line(kl, SAFE_X + 30, W + 400, H * 0.62 + 130, 4))
    return C.finish(C.grain(C.over(img, *lays).convert("RGB"), t, 0.035), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 06 · цитата 04 · восьмой ═════════════════════════
@scene("06")
def s06(t, dur):
    c_chet = rel("06", 35.95)
    c_temn = rel("06", 36.94)
    c_novy = rel("06", 38.26)
    c_vos = rel("06", 39.81)
    c_vse = rel("06", 41.00)
    kd = C.seg(t, c_temn, c_temn + 1.2)
    img = C.kb(dark_bg(9, (14, 14, 17)), t / dur, 0.04, 0.5, 0.5)
    img = C.fade(img, 1 - 0.6 * kd)
    k8 = C.seg(t, c_vos, dur)
    k8a = C.seg(t, c_temn, c_vos)          # с «Самое тёмное» восьмёрка едва проступает и медленно растёт
    lays = []
    if k8a > 0:
        lays.append(V.cifry(1.0, t, px=int(760 + 140 * C.smoother(k8a) - 120 * C.smoother(k8)), text="8",
                            a=0.03 + 0.07 * k8a + 0.48 * k8, glow=0.25 * k8a + 0.6 * k8, breathe=0.01))
    k1 = C.seg(t, c_novy, c_novy + 0.9)
    k2 = C.seg(t, c_vos, c_vos + 0.6)
    k3 = C.seg(t, c_vse, c_vse + 0.7)
    lays += [label("04", C.seg(t, c_chet, c_chet + 0.3), 150, 40, x=SAFE_X, anchor="ls", track=0.3),
             red_line(C.seg(t, c_chet, c_chet + 0.3), SAFE_X, SAFE_X + 70, 164, 3),
             word("САМОЕ ТЁМНОЕ", C.seg(t, c_temn, c_temn + 0.45), H * 0.34, 72, "head", C.WHITE, 0.12, x=SAFE_X + 30, anchor="ls", rise=22)]
    if k1 > 0:
        lays.append(fx.typed("«Новый человек грядёт.", k1, "serif", 66, C.WHITE, SAFE_X + 30, H * 0.50, 0.0, k2 <= 0, t))
    if k2 > 0:
        lays.append(fx.typed("Придёт восьмой.", k2, "serif", 66, C.WHITE, SAFE_X + 30, H * 0.50 + 96, 0.0, k3 <= 0, t))
    if k3 > 0:
        lays.append(fx.typed("И всё изменит».", k3, "serif", 66, C.WHITE, SAFE_X + 30, H * 0.50 + 192, 0.0, True, t))
    out = C.over(img, *lays).convert("RGB")
    if 0 < k8 < 0.25:
        out = fx.glitch(out, 0.5 * (1 - k8 / 0.25), seed=int(t * 30), slices=10, shift=60, rgb=10)
    return C.finish(C.grain(out, t, 0.035), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.35)


# ═════════════════════════ 07 · 8 во весь экран · карта «соберутся» ═════════════════════════
CAPS_BACK = ["Киев", "Минск", "Кишинёв", "Тбилиси", "Ереван", "Баку", "Астана", "Ташкент", "Бишкек", "Вильнюс", "Рига", "Таллин"]


@scene("07")
def s07(t, dur):
    c_apro = rel("07", 42.45)
    c_kgod = rel("07", 45.83)
    c_ushli = rel("07", 48.84)

    def a_eight(tt, d):
        k = C.seg(tt, 0.0, 0.35)
        px = int(1400 - 420 * C.out_expo(k))
        img = V.cifry_frame(1.0, t, px=px, text="8", glow=1.0, breathe=0.02)
        if tt < 0.3:
            img = fx.glitch(img, 0.7 * (1 - tt / 0.3), seed=int(t * 30), slices=14, shift=120, rgb=18)
        img = C.over(img, label("ВОСЬМОЙ", C.seg(tt, 0.4, 0.8), H * 0.5 + 440, 34)).convert("RGB")
        return flash(img, tt, 0.1, 0.7)

    def b_map(tt, d):
        base = K.base(EURASIA, hot="Russia")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.7, 0, 255).astype(np.uint8), "RGB")
        mx, my = EURASIA.xy(*K.CITIES["Москва"])
        lays = []
        k_r = C.seg(tt, 0.3, 0.7)
        if k_r > 0:
            lay = C.layer()
            dd = ImageDraw.Draw(lay)
            for j in range(3):
                ph = ((tt - 0.3) * 0.5 + j * 0.33) % 1.0
                r = (10 + 260 * ph) * SS
                a = int(170 * (1 - ph) * k_r)
                dd.ellipse([mx * SS - r, my * SS - r, mx * SS + r, my * SS + r], outline=C.RED + (a,), width=3 * SS)
            lays.append(C.done(lay))
        # пунктиры от столиц к Москве — «снова соберутся»
        t_lines = c_kgod - c_apro + 0.8
        for i, name in enumerate(CAPS_BACK):
            k = C.seg(tt, t_lines + i * 0.16, t_lines + i * 0.16 + 1.1)
            if k > 0:
                lays.append(K.line_layer([K.CITIES[name], K.CITIES["Москва"]], k, okno=EURASIA, width=3, dash=(14, 12), glow=False, head=True))
        lays.append(K.city_layer(["Москва"], C.seg(tt, 0.3, 0.7), okno=EURASIA, px=34))
        lays.append(K.city_layer([n for n in CAPS_BACK], C.seg(tt, t_lines, t_lines + 0.8), okno=EURASIA, px=22, dot=True, color=C.GREY))
        lays.append(K.date_tag("2027", C.seg(tt, 0.05, 0.5), sub="по пересказу · карта условная"))
        kw = C.seg(tt, c_ushli - c_apro, c_ushli - c_apro + 0.5)
        lays.append(label("СТРАНЫ, КОТОРЫЕ ОТ НЕЁ УШЛИ", kw, H - 120, 30))
        img = C.over(base, *lays).convert("RGB")
        img = C.kb(img, tt / d, 0.08, 0.42, 0.42)
        return flash(C.grain(img, t, 0.03), tt, 0.08, 0.35)

    fn, tt, d = shots(t, [(0.0, a_eight), (c_apro, b_map)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 08 · почему слушают · царь · 2% · 1941 ═════════════════════════
@scene("08")
def s08(t, dur):
    c_pochemu = rel("08", 50.38)
    c_rassk = rel("08", 52.22)
    c_den = rel("08", 54.60)
    c_prez = rel("08", 56.04)
    c_pobeda = rel("08", 58.40)
    c_41 = rel("08", 59.70)
    c_zapis = rel("08", 62.62)

    def a_q(tt, d):
        img = C.kb(dark_bg(9, (14, 14, 17)), tt / d, 0.03, 0.5, 0.5)
        k = C.seg(tt, c_pochemu, c_pochemu + 1.3)
        lays = [fx.typed("Почему её слушают до сих пор?", k, "head_r", 72, C.WHITE, SAFE_X, H * 0.52, 0.02, True, t)] if k > 0 else []
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.035)

    def b_tsar(tt, d):
        img = C.kb(dark_bg(10), tt / d, 0.06, 0.5, 0.5)
        k_l = C.seg(tt, 0.0, 0.4)
        k_t = C.seg(tt, 0.5, 0.9)
        k_d = C.seg(tt, c_den - c_rassk, c_den - c_rassk + 1.0)
        lays = [label("РАССКАЗЫВАЮТ", k_l, 150, 40, x=SAFE_X, anchor="ls", track=0.3), red_line(k_l, SAFE_X, SAFE_X + 70, 164, 3),
                word("ЦАРЮ — ДЕНЬ ЕГО СМЕРТИ", k_t, H * 0.40, 90, "head", C.WHITE, 0.1, x=SAFE_X + 30, anchor="ls", rise=24)]
        if k_d > 0:
            num = fx.flip_number(["12.07.1942", "03.05.1943", "28.08.1943"], k_d, W / 2, H * 0.66, 150)
            lays.append(num)
            if k_d >= 1:
                lays.append(C.text_layer(["28.08.1943"], "head", 150, C.RED, W / 2, H * 0.66 + 150 * 0.36, "ms", 0.02, a=C.seg(tt, c_den - c_rassk + 1.0, c_den - c_rassk + 1.3)))
            lays.append(label("ЦАРЬ БОРИС III · ПО РАССКАЗУ ПЛЕМЯННИЦЫ", C.seg(tt, c_den - c_rassk + 0.6, c_den - c_rassk + 1.1), H * 0.66 + 130, 28))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    def c_two(tt, d):
        img = C.kb(dark_bg(11), tt / d, 0.06, 0.5, 0.5)
        k = C.seg(tt, 0.1, 1.5)
        lays = [C.big_number("2 %", "РЕЙТИНГ ЕЛЬЦИНА · ВЕСНА 1996", "по рассказу Кирсана Илюмжинова", k, px=340, count_from=54)]
        kp = C.seg(tt, c_pobeda - c_prez, c_pobeda - c_prez + 0.4)
        lays.append(word("ПООБЕЩАЛА ПОБЕДУ", kp, H - 150, 70, "head", C.WHITE, 0.14, rise=20))
        return flash(C.grain(C.over(img, *lays).convert("RGB"), t, 0.04), tt, 0.06, 0.3)

    def d_41(tt, d):
        # кадр плёнки в видоискателе: запись сохранилась
        fr = V.top_shade(V.vanga("v0l", V0, tt, V0_LISTEN, push=0.02, hand=1.5, k_grade=0.8, **NOVA), 260, 0.5)
        fr = fx.vidoiskatel(fr, tt, tc0=11 * 60 + 14, zoom_step=1, rec=True, bw=0.35)
        k41 = C.seg(tt, 0.05, 0.5)
        kz = C.seg(tt, c_zapis - c_41, c_zapis - c_41 + 0.5)
        lays = [word("1941", k41, H * 0.5 + 90, 260, "head", C.RED, 0.02, rise=0),
                label("ОНА РАССКАЗАЛА САМА", C.seg(tt, 0.4, 0.8), H * 0.5 + 150, 34, C.WHITE, track=0.3),
                word("ЗАПИСЬ СОХРАНИЛАСЬ", kz, H - 150, 70, "head", C.WHITE, 0.14, rise=20),
                C.caption(*CAP_ZAPIS, k=C.seg(tt, 0.3, 0.9), y=H - 92)]
        img = C.over(fr, *lays).convert("RGB")
        return flash(img, tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_q), (c_rassk, b_tsar), (c_prez, c_two), (c_41, d_41)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 09 · В0: окно оригинала, перевод ОЛЬГИ ═════════════════════════
@scene("09")
def s09(t, dur):
    T_V = 9.0   # Ванга в кадре 11:43–11:52; дальше стоп-кадр, темнеет
    tv = min(t, T_V - 0.04)
    img = V.top_shade(V.vanga("v0b", V0, tv, V0_B0, push=0.025, hand=1.8, k_grade=0.75, **NOVA), 320, 0.6)
    env_v = V.envelope(V0, V0_B0, T_V)
    env_o = V.envelope("olga_v0.mp3", 0.0, 5.3)
    lay = V.oscillo([(env_v, 0.0, C.WHITE), (env_o, 2.3, C.RED)], t, H - 215, 46, SAFE_X, W - SAFE_X)
    k_orig = C.seg(t, 0.2, 0.6) * (1 - C.seg(t, 2.0, 2.4))
    k_per = C.seg(t, 2.3, 2.7) * (1 - C.seg(t, 8.0, 8.6))
    k1 = C.seg(t, 2.35, 4.2)
    k2 = C.seg(t, 4.35, 5.9)
    k3 = C.seg(t, 6.0, 7.5)
    lays = [lay, label("ОРИГИНАЛЬНЫЙ ЗВУК", k_orig, 120, 34, C.GREY, x=W - SAFE_X, anchor="rs"),
            label("ПЕРЕВОД ЗА КАДРОМ", k_per, 120, 34, C.RED, x=W - SAFE_X, anchor="rs"),
            fx.typed("Придёт время, будет война.", k1, "head_r", 46, C.WHITE, SAFE_X, 196, 0.02, k2 <= 0, t) if k1 > 0 else None,
            fx.typed("Одна держава объявит войну.", k2, "head_r", 46, C.WHITE, SAFE_X, 252, 0.02, k3 <= 0, t) if k2 > 0 else None,
            fx.typed("И она эту войну проиграет.", k3, "head_r", 46, C.WHITE, SAFE_X, 308, 0.02, True, t) if k3 > 0 else None,
            C.caption(*CAP_ZAPIS, k=C.seg(t, 0.4, 0.9))]
    img = C.over(img, *lays).convert("RGB")
    if t > T_V:
        kk = C.seg(t, T_V, dur)
        img = V.zoom_at(img, 1.0 + 0.06 * kk, W / 2, H * 0.45)
        img = C.fade(img, 1 - 0.7 * kk)
    return C.finish(flash(img, t, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 10 · сегодня соберём всё · подряд · проверим ═════════════════════════
QUOTES = [("01", "не будет править Россией к 2027"), ("02", "останется слава Владимира"),
          ("03", "будет править до самой смерти"), ("04", "придёт восьмой — и всё изменит")]


@scene("10")
def s10(t, dur):
    c_seg = rel("10", 63.91)
    c_vanga = rel("10", 65.73)
    c_ross = rel("10", 67.56)
    c_putin = rel("10", 69.06)
    c_27 = rel("10", 70.00)
    c_vse = rel("10", 71.64)
    c_podr = rel("10", 73.40)
    c_prov = rel("10", 74.30)
    c_slysh = rel("10", 75.60)
    c_zap = rel("10", 76.59)
    c_konec = rel("10", 77.50)
    c_chto = rel("10", 78.80)

    def three_words(tt, base_t):
        lays = []
        for i, (txt, c, col) in enumerate((("РОССИЯ", c_ross, C.WHITE), ("ПУТИН", c_putin, C.WHITE), ("2027", c_27, C.RED))):
            k = C.seg(base_t, c, c + 0.35)
            if k > 0:
                lays.append(word(txt, k, H * 0.36 + i * 170, 150, "head", col, 0.08, x=W - SAFE_X, anchor="rs", rise=30))
        return lays

    def a_priem(tt, d):
        img = V.vanga("g1p", G1, tt, G1_PRIEM, push=0.05, hand=2.5, k_grade=0.7, bw=1.0, **NOVA_BW)
        kd = C.seg(tt, c_ross - 0.2, c_ross + 0.3)
        img = C.fade(img, 1 - 0.5 * kd)
        lays = [C.caption(*CAP_1974, k=C.seg(tt, 0.3, 0.9)),
                label("СЕГОДНЯ СОБЕРЁМ ВСЁ", C.seg(tt, c_seg, c_seg + 0.5), 150, 40, x=SAFE_X, anchor="ls", track=0.3)]
        lays += three_words(tt, tt)
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    def b_words(tt, d):
        img = C.kb(dark_bg(9, (14, 14, 17)), tt / d, 0.03, 0.5, 0.5)
        lays = three_words(tt, tt + c_putin)
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.035)

    def c_stack(tt, d):
        img = C.kb(dark_bg(9, (14, 14, 17)), tt / d, 0.03, 0.5, 0.5)
        lays = []
        y0 = H * 0.30
        for i, (n, q) in enumerate(QUOTES):
            k = C.seg(tt, i * 0.22, i * 0.22 + 0.3)
            if k <= 0:
                continue
            kk = C.out_cubic(k)
            y = y0 + i * 150
            lays.append(C.text_layer([n], "head_l", 40, C.GREY, SAFE_X, y, "ls", 0.3, a=k))
            lays.append(C.text_layer([q], "serif", 54, C.WHITE, SAFE_X + 90 + (1 - kk) * 60, y, "ls", 0.0, a=k))
            # проверим: кто слышал · кто записал — красные знаки вопроса
            k_s = C.seg(tt, c_slysh - c_podr + i * 0.12, c_slysh - c_podr + i * 0.12 + 0.25)
            k_z = C.seg(tt, c_zap - c_podr + i * 0.12, c_zap - c_podr + i * 0.12 + 0.25)
            for j, (kq, xx) in enumerate(((k_s, W - SAFE_X - 300), (k_z, W - SAFE_X - 60))):
                if kq > 0:
                    lays.append(C.text_layer(["?"], "head", int(70 * (1.6 - 0.6 * C.out_cubic(kq))), C.RED, xx, y, "ms", 0.0, a=kq))
        kh = C.seg(tt, c_slysh - c_podr - 0.3, c_slysh - c_podr)
        kh2 = C.seg(tt, c_zap - c_podr - 0.3, c_zap - c_podr)
        lays.append(label("КТО СЛЫШАЛ", kh, y0 - 70, 24, C.GREY, x=W - SAFE_X - 300, track=0.3))
        lays.append(label("КТО ЗАПИСАЛ", kh2, y0 - 70, 24, C.GREY, x=W - SAFE_X - 60, track=0.3))
        lays.append(label("ВСЕ ГРОМКИЕ СЛОВА · ПОДРЯД", C.seg(tt, 0.0, 0.4), 150, 40, x=SAFE_X, anchor="ls", track=0.3))
        lays.append(red_line(C.seg(tt, 0.0, 0.4), SAFE_X, SAFE_X + 70, 164, 3))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.035)

    def d_question(tt, d):
        img = C.kb(dark_bg(9, (12, 12, 14)), tt / d, 0.03, 0.5, 0.5)
        kq = C.seg(tt, c_chto - c_konec, c_chto - c_konec + 1.4)
        lays = [label("И В КОНЦЕ — ОДИН ВОПРОС", C.seg(tt, 0.1, 0.5) * (1 - C.seg(tt, c_chto - c_konec, c_chto - c_konec + 0.3)), H * 0.5, 40, C.GREY, track=0.3)]
        if kq > 0:
            px = fit_px("Что она сказала на самом деле?", "head_r", 84, W - 2 * SAFE_X, 0.02)
            lays.append(fx.typed("Что она сказала на самом деле?", kq, "head_r", px, C.WHITE, SAFE_X, H * 0.52, 0.02, True, t))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.035)

    fn, tt, d = shots(t, [(0.0, a_priem), (c_putin, b_words), (c_vse, c_stack), (c_konec, d_question)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 11 · титр названия ═════════════════════════
@scene("11")
def s11(t, dur):
    T_T = 2.0
    img = C.kb(dark_bg(9, (12, 12, 14)), t / dur, 0.03, 0.5, 0.5)
    if t < T_T:
        k = C.smoother(t / T_T)
        px = fit_px("Что она сказала на самом деле?", "head_r", 84, W - 2 * SAFE_X, 0.02)
        lays = [fx.typed("Что она сказала на самом деле?", 1.0, "head_r", px, C.WHITE, SAFE_X, H * 0.52, 0.02, False, t)]
        out = C.over(img, *lays).convert("RGB")
        out = C.fade(out, 1 - 0.9 * k)
        out = C.over(out, V.cifry(1.0, t, px=440, a=0.25 * k, glow=0.3)).convert("RGB")
        return C.finish(out, t, dur, fi=0.0, fo=0.0, grain_k=0.035, vig=0.3)
    tt = t - T_T
    k1 = C.seg(tt, 0.0, 0.55)
    px1 = fit_px("БУДУЩЕЕ ПУТИНА И РОССИИ", "head", 124, W - 2 * SAFE_X, 0.08)
    lays = []
    if k1 > 0:
        sc = 1.5 - 0.5 * C.out_expo(k1)
        lays.append(V.cifry(1.0, t, px=int(300 * sc), a=C.clamp(k1 * 2), glow=0.9, breathe=0.01))
    lays.append(word("БУДУЩЕЕ ПУТИНА И РОССИИ", C.seg(tt, 0.45, 1.0), H * 0.5 - 190, px1, "head", C.WHITE, 0.08, rise=30))
    lays.append(red_line(C.seg(tt, 0.9, 1.5), W / 2 - 330, W / 2 + 330, H * 0.5 + 150, 5))
    lays.append(word("что предсказала Ванга", C.seg(tt, 1.1, 1.7), H * 0.5 + 225, 56, "serif_i", C.GREY, 0.0, rise=16))
    out = C.over(img, *lays).convert("RGB")
    out = flash(out, tt, 0.1, 0.5)
    return C.finish(out, t, dur, fi=0.0, fo=0.7, grain_k=0.04, vig=0.35)


import scenes2  # noqa: E402,F401 — блок 1 «ВОЙНА», сцены 12-29
import scenes3  # noqa: E402,F401 — блок 2 «ЗАПРЕТНАЯ ДВЕРЬ», сцены 30-40
