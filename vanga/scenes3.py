#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Блок 2 «ЗАПРЕТНАЯ ДВЕРЬ» — сцены 30-40 (третий кусок, ~133 с). Регистрируются в scenes.SCENES."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import fx
import karta as K
import vfx as V
from core import W, H, SS
from vfx import SAFE_X, SAFE_Y, word, label, red_line, flash, shots, dark_bg, black, fit_px
from scenes import scene, rel, NOVA, NOVA_BW, CAP_1974, G1, G1_FACE, BALKAN, EURASIA
from scenes2 import src, r, act, okno_video, date_card, foto_kb, HRON, DOM, shkala

V5 = "v5_g1_4105.mp4"      # Горещо 1 с 2460,28: соседки, дом-музей, Витка
V7 = "v7_g1_4400.mp4"      # Горещо 1 с 2639,80: Витка о Стоянове
TEL = "b_g2_2110.mp4"      # Горещо 2 с 1267,36: телефон и радиоточка в доме-музее

CAP_ELENA = ("Елена Козарова", "соседка Ванги", "фильм Nova «Ванга: между два свята»")
CAP_MARIYKA = ("Марийка Стоянова", "соседка Ванги", "фильм Nova «Ванга: между два свята»")
CAP_VITKA = ("Витка Петреска", "помощница Ванги", "фильм Nova «Ванга: между два свята»")
CAP_MUZEY = ("Петрич", "дом-музей Ванги", "фильм Nova «Ванга: между два свята»")

# материалы блока 2 (archiv/hronika, реестр REESTR-HRONIKA.tsv); имена заполняются по реестру
HRON.update({
    "sofia70": ("hronika/Sofia_1970_Konigschloss.jpg", ("София", "около 1970", "Викисклад · CC BY-SA 3.0")),
    "zhivkov": ("hronika/Todor_Zhivkov_1971_color.png", ("Тодор Живков", "1971", "Nationaal Archief · CC0")),
    "zhivkova": ("hronika/Zhivkova_Order_1976.jpg", ("Людмила Живкова", "София · 1976", "Викисклад · CC BY-SA 4.0")),
    "doc1980": ("hronika/wilson_1980.png", ("Политбюро ЦК БКП", "август 1980", "Wilson Center Digital Archive")),
    "stoyanov": ("hronika/Petar_Stoyanov_portrait.jpg", ("Пётр Стоянов", "президент Болгарии 1997–2002", "Викисклад · public domain")),
    "dver": ("hronika/vanga_house.jpg", ("Петрич", "дом Ванги", "Викисклад")),
})
BREZH = ("hronika/Brezhnev_Signing_Agreements.webm", 280.0, ("Леонид Брежнев", "1973", "Nixon Library · public domain"))


def perevod_ks(tt, spans):
    return [C.seg(tt, a, b) for a, b in spans]


# ═════════════════════════ 30 · титр · Болгария семидесятых ═════════════════════════
@scene("30")
def s30(t, dur):
    c_bolg = r("30", 112.35)
    c_soyuz = r("30", 114.0)
    c_partiya = r("30", 116.2)
    c_vera = r("30", 117.3)
    c_gad = r("30", 119.97)
    c_znah = r("30", 120.9)
    c_yasn = r("30", 121.7)
    c_net = r("30", 122.8)
    c_pohod = r("30", 124.4)

    def a_title(tt, d):
        img = C.kb(dark_bg(9, (12, 12, 14)), tt / d, 0.03, 0.5, 0.5)
        img = C.over(img, *act("ЗАПРЕТНАЯ ДВЕРЬ", "02", C.seg(tt, 0.0, 1.0))).convert("RGB")
        img = C.fade(img, 1 - C.seg(tt, d - 0.5, d))
        return flash(C.grain(img, t, 0.035), tt, 0.1, 0.5)

    def b_sofia(tt, d):
        img = foto_kb("sofia70", tt, d, 0.07, 0.5, 0.5, 0.55, C.seg(tt, 0.3, 0.9))
        img = C.fade(img, 1 - 0.35 * C.seg(tt, c_soyuz - 1.6, c_soyuz - 1.2))
        lays = [K.date_tag("1970-е", C.seg(tt, 0.1, 0.5), sub="Болгария"),
                word("САМАЯ ВЕРНАЯ СОЮЗНИЦА МОСКВЫ", C.seg(tt, c_soyuz - 1.5, c_soyuz - 1.1), H * 0.80, 70, "head", C.WHITE, 0.1, rise=24)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.08, 0.4)

    def c_odna(tt, d):
        img = C.kb(dark_bg(17, (14, 14, 17)), tt / d, 0.04, 0.5, 0.5)
        kp = C.seg(tt, 0.1, 0.5)
        kv = C.seg(tt, c_vera - c_partiya, c_vera - c_partiya + 0.5)
        lays = [label("ПАРТИЯ", kp, H * 0.42 - 120, 40, x=W * 0.32), C.big_number("1", None, None, kp, cx=W * 0.32, cy=H * 0.5, px=320, count_from=1, rings=False),
                label("ВЕРА", kv, H * 0.42 - 120, 40, x=W * 0.68), C.big_number("1", None, None, kv, cx=W * 0.68, cy=H * 0.5, px=320, count_from=1, rings=False),
                label("В ПАРТИЮ", C.seg(tt, c_vera - c_partiya + 1.4, c_vera - c_partiya + 1.8), H * 0.5 + 200, 34, C.WHITE, x=W * 0.68)]
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    def d_gadalki(tt, d):
        img = C.kb(dark_bg(18, (14, 14, 17)), tt / d, 0.04, 0.5, 0.5)
        lays = []
        for i, (w_, c) in enumerate((("ГАДАЛКИ", c_gad), ("ЗНАХАРКИ", c_znah), ("ЯСНОВИДЯЩИЕ", c_yasn))):
            k = C.seg(tt, c - c_gad, c - c_gad + 0.35)
            y = H * 0.30 + i * 150
            lays.append(word(w_, k, y, 110, "head", C.WHITE, 0.1, x=SAFE_X + 30, anchor="ls", rise=24))
            kx = C.seg(tt, c_net - c_gad + i * 0.15, c_net - c_gad + i * 0.15 + 0.35)
            if kx > 0:
                tw = C.text_w(ImageDraw.Draw(Image.new("RGBA", (4, 4))), w_, C.font("head", 110 * SS), 0.1) / SS
                lays.append(red_line(kx, SAFE_X + 20, SAFE_X + 40 + tw, y - 38, 8))
        lays.append(label("ДЛЯ ГАЗЕТ НЕ СУЩЕСТВУЮТ", C.seg(tt, c_net - c_gad + 0.8, c_net - c_gad + 1.2), H * 0.30 + 3 * 150 - 40, 40, C.GREY, x=SAFE_X + 30, anchor="ls"))
        kp = C.seg(tt, c_pohod - c_gad + 1.6, c_pohod - c_gad + 2.0)
        lays.append(word("ОТВЕТИТЬ НА ПАРТСОБРАНИИ", kp, H - 150, 64, "head", C.WHITE, 0.12, x=W - SAFE_X, anchor="rs", rise=20))
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.04)

    fn, tt, d = shots(t, [(0.0, a_title), (1.5, b_sofia), (c_partiya, c_odna), (c_gad, d_gadalki)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 31 · каждую неделю · Людмила Живкова · досье ═════════════════════════
@scene("31")
def s31(t, dur):
    c_vremya = r("31", 127.10)
    c_ezdit = r("31", 130.2)
    c_zhiv = r("31", 132.97)
    c_doch = r("31", 134.37)
    c_oxf = r("31", 139.08)
    c_mgu = r("31", 139.9)
    c_kult = r("31", 141.1)
    c_polit = r("31", 143.0)

    def a_map(tt, d):
        base = K.base(BALKAN, hot="Bulgaria")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.8, 0, 255).astype(np.uint8), "RGB")
        # пунктир София → Петрич бежит каждые 1,6 с — «каждую неделю»
        per = 1.6
        ph = ((tt - 0.3) % per) / per if tt > 0.3 else 0.0
        lays = [K.city_layer(["София", "Петрич"], C.seg(tt, 0.1, 0.5), okno=BALKAN, px=34),
                K.line_layer([K.CITIES["София"], K.CITIES["Петрич"]], C.clamp(ph * 1.15), okno=BALKAN, width=4, dash=(16, 12), glow=True, head=True),
                K.date_tag("КАЖДУЮ НЕДЕЛЮ", C.seg(tt, c_ezdit - 0.3, c_ezdit + 0.2), px=48, sub="из Софии в Петрич"),
                label("ЖЕНЩИНА ИЗ ПЕРВОГО ДЕСЯТКА СТРАНЫ", C.seg(tt, c_ezdit + 1.5, c_ezdit + 1.9), H - 120, 34, C.WHITE)]
        img = C.over(base, *lays).convert("RGB")
        img = C.kb(img, tt / d, 0.08, 0.5, 0.4)
        return C.grain(img, t, 0.03)

    def b_dossier(tt, d):
        name, cap = HRON["zhivkova"][0], HRON["zhivkova"][-1]
        im = C.foto(name)
        true = C.kb(im, tt / d, 0.05, 0.3, 0.4, size=(W // 2, H))
        canvas = Image.new("RGB", (W, H), (12, 12, 14))
        box = (0, 0, W // 2, H)
        base = canvas.copy()
        true_full = canvas.copy()
        true_full.paste(true, (0, 0))
        img = fx.proyavka(base, true_full, box, C.seg(tt, 0.0, 1.2), seed=11)
        img = V.grade(img, 0.4)
        items = [("ДОЧЬ ТОДОРА ЖИВКОВА", c_doch), ("ХОЗЯИНА БОЛГАРИИ 35 ЛЕТ", c_doch + 1.8), ("ОКСФОРД", c_oxf), ("МОСКОВСКИЙ УНИВЕРСИТЕТ", c_mgu),
                 ("ГЛАВА ВСЕЙ КУЛЬТУРЫ", c_kult), ("ЧЛЕН ПОЛИТБЮРО", c_polit)]
        lays = [C.caption(*cap, k=C.seg(tt, 0.8, 1.3)),
                word("ЛЮДМИЛА ЖИВКОВА", C.seg(tt, 0.2, 0.6), 200, 86, "head", C.WHITE, 0.1, x=W / 2 + 60, anchor="ls", rise=24),
                red_line(C.seg(tt, 0.5, 0.9), W / 2 + 60, W / 2 + 260, 222, 4)]
        for i, (txt, c) in enumerate(items):
            k = C.seg(tt, c - c_zhiv, c - c_zhiv + 0.4)
            if k > 0:
                kk = C.out_cubic(k)
                lays.append(C.text_layer(["%02d" % (i + 1)], "head_l", 30, C.RED, W / 2 + 60, 300 + i * 92, "ls", 0.1, a=k))
                lays.append(C.text_layer([txt], "head_r", 44, C.WHITE, W / 2 + 120 + (1 - kk) * 40, 300 + i * 92, "ls", 0.06, a=k))
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_map), (c_zhiv, b_dossier)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 32 · шепчутся · Восток · Москва косо · принимает всерьёз ═════════════════════════
@scene("32")
def s32(t, dur):
    c_shep = r("32", 143.98)
    c_vostok = r("32", 146.14)
    c_ind = r("32", 148.6)
    c_tayn = r("32", 149.3)
    c_moskva = r("32", 151.51)
    c_ne_pr = r("32", 153.5)
    c_vser = r("32", 154.53)

    def a_shep(tt, d):
        img = foto_kb("zhivkova", 1.0 + tt, d + 1.0, 0.05, 0.32, 0.42, 0.5, 1.0)
        img = C.fade(img, 0.7)
        lays = [label("В СОЦЛАГЕРЕ О НЕЙ ШЕПЧУТСЯ", C.seg(tt, 0.1, 0.5), 150, 40, x=SAFE_X, anchor="ls", track=0.3),
                red_line(C.seg(tt, 0.1, 0.5), SAFE_X, SAFE_X + 70, 164, 3)]
        for i, (w_, c) in enumerate((("ВОСТОК", c_vostok + 1.9), ("ИНДИЯ", c_ind), ("ТАЙНЫЕ УЧЕНИЯ", c_tayn))):
            lays.append(word(w_, C.seg(tt, c, c + 0.4), H * 0.45 + i * 130, 96, "head", C.WHITE, 0.12, x=W - SAFE_X, anchor="rs", rise=24))
        return C.over(img, *lays).convert("RGB")

    def b_moskva(tt, d):
        name, s0, cap = BREZH
        fr = V.vanga("brezh", name, tt, s0, zoom=1.0, cx=0.5, cy=0.5, push=0.04, hand=2.0, k_grade=0.8)
        lays = [word("В МОСКВЕ СМОТРЯТ КОСО", C.seg(tt, 0.1, 0.5), H * 0.80, 76, "head", C.WHITE, 0.1, rise=24), C.caption(*cap, k=C.seg(tt, 0.3, 0.9))]
        return flash(C.over(fr, *lays).convert("RGB"), tt, 0.08, 0.4)

    def c_vser_(tt, d):
        img = V.vanga("g1a3", G1, tt, G1_FACE + 8.0, push=0.06, hand=2.5, k_grade=0.7, bw=1.0, **NOVA_BW)
        kw = C.seg(tt, c_vser - c_ne_pr + 0.9, c_vser - c_ne_pr + 1.3)
        lays = [C.caption(*CAP_1974, k=C.seg(tt, 0.3, 0.9)),
                label("ОНА НЕ ПРЯЧЕТСЯ", C.seg(tt, 0.1, 0.5) * (1 - kw), H * 0.80, 44, C.WHITE, track=0.3),
                word("ПРИНИМАЕТ ВСЕРЬЁЗ", kw, H * 0.80, 86, "head", C.WHITE, 0.12, rise=24)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    fn, tt, d = shots(t, [(0.0, a_shep), (c_moskva, b_moskva), (c_ne_pr, c_vser_)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 33 · протокол Политбюро 1980 · В5а Елена Козарова ═════════════════════════
def doc_card(k, t):
    """страница документа: снимок Wilson Center, фамилия Живковой подчёркнута; если снимка нет — карточка-опись"""
    name, cap = HRON["doc1980"][0], HRON["doc1980"][-1]
    p = C.apath(name)
    if __import__("os").path.exists(p):
        im = Image.open(p).convert("RGB")
        img = C.kb(im, k, 0.06, 0.5, 0.12)
        img = C.vignette(Image.fromarray((np.asarray(img, np.float32) * 0.9).astype(np.uint8), "RGB"), 0.35)
    else:
        img = C.paper(W, H, seed=21, tone=(226, 222, 212), dark=0.0)
        d = ImageDraw.Draw(img)
        d.text((SAFE_X + 60, H * 0.22), "ПРОТОКОЛ ЗАСЕДАНИЯ ПОЛИТБЮРО ЦК БКП", font=C.font("serif_b", 54), fill=(30, 30, 34))
        d.text((SAFE_X + 60, H * 0.22 + 80), "август 1980 · о встрече Т. Живкова с Л. И. Брежневым 7 августа 1980", font=C.font("serif", 40), fill=(60, 60, 64))
        d.text((SAFE_X + 60, H * 0.22 + 170), "Присутствовали: … Людмила Живкова …", font=C.font("serif", 44), fill=(30, 30, 34))
        d.text((SAFE_X + 60, H * 0.70), "ОПИСЬ ПО ДОКУМЕНТУ WILSON CENTER DIGITAL ARCHIVE · ОФОРМЛЕНИЕ НАШЕ", font=C.font("head_l", 24), fill=(140, 140, 144))
        img = C.vignette(img, 0.35)
    return C.over(V.top_shade(img, 240, 0.5), K.date_tag("АВГУСТ 1980", C.seg(k, 0.1, 0.5), sub="Политбюро ЦК БКП"),
                  C.caption(*cap, k=C.seg(k, 0.3, 0.8))).convert("RGB")


@scene("33")
def s33(t, dur):
    T0 = 3.0
    if t < T0:
        return C.finish(flash(doc_card(t / T0, t), t, 0.08, 0.4), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.0)
    tt = t - T0
    img = okno_video("v5a", V5, tt, src(2460.28, "41:09.0"), "olga_b5a.mp3", 2.3, 10.14,
                     ["Идём вечером домой. Перед нами милиционеры: стойте, куда?", "Домой, говорим. А они: Тодор Живков или Людмила Живкова",
                      "в гостях у бабы Ванги. Пропустить не можем."],
                     perevod_ks(tt, [(2.35, 5.4), (5.6, 9.4), (9.6, 12.3)]), t, cap=CAP_ELENA, zoom=1.35, cx=0.5, cy=0.45)
    return C.finish(flash(img, tt, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 34 · В5б: Марийка — по средам · Витка — телефон и асфальт ═════════════════════════
@scene("34")
def s34(t, dur):
    T1 = 10.0
    if t < T1:
        img = okno_video("v5b", V5, t, src(2460.28, "41:47.0"), "olga_b5b.mp3", 2.3, 7.42,
                         ["Людмила приезжала по средам. Целый день наверху с Вангой разговаривают.", "Уезжает поздно вечером. Через неделю опять."],
                         perevod_ks(t, [(2.35, 6.6), (6.8, 9.6)]), t, cap=CAP_MARIYKA, zoom=1.35, cx=0.5, cy=0.45)
        return C.finish(flash(img, t, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)
    tt = t - T1
    img = okno_video("v5c", V5, tt, src(2460.28, "42:29.0"), "olga_b5c.mp3", 2.0, 3.92,
                     ["Она ей и телефон провела.", "И дорогу заасфальтировали."],
                     perevod_ks(tt, [(2.05, 3.8), (4.0, 5.8)]), t, cap=CAP_VITKA, zoom=1.35, cx=0.5, cy=0.45)
    return C.finish(flash(img, tt, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 35 · улицу перекрывают · кабель · асфальт · десять левов ═════════════════════════
@scene("35")
def s35(t, dur):
    c_ulicu = r("35", 157.49)
    c_kabel = r("35", 159.0)
    c_asf = r("35", 160.97)
    c_zhivkov = r("35", 162.0)
    c_ofic = r("35", 166.37)
    c_10 = r("35", 167.46)

    def a_ulica(tt, d):
        img = V.vanga("dom6", DOM, tt, src(1272.44, "21:28.0"), push=0.05, hand=2.5, k_grade=0.7, bw=0.9, **NOVA_BW)
        lays = [C.caption(*CAP_1974, k=C.seg(tt, 0.3, 0.9)),
                word("УЛИЦУ ПЕРЕКРЫВАЮТ", C.seg(tt, c_ulicu + 0.4, c_ulicu + 0.8), H * 0.80, 80, "head", C.WHITE, 0.12, rise=24)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    def b_tel(tt, d):
        img = V.vanga("tel", TEL, tt, src(1267.36, "21:16.0"), push=0.06, hand=2.0, k_grade=0.7, **NOVA)
        lays = [C.caption(*CAP_MUZEY, k=C.seg(tt, 0.3, 0.9)), word("ТЕЛЕФОН", C.seg(tt, 0.1, 0.5), H * 0.80, 86, "head", C.WHITE, 0.12, rise=24)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    def c_asf_(tt, d):
        img = V.vanga("v5m", V5, tt, src(2460.28, "41:05.0"), push=0.05, hand=2.0, k_grade=0.7, zoom=1.35, cx=0.5, cy=0.45)
        lays = [C.caption(*CAP_MUZEY, k=1.0), word("АСФАЛЬТ", C.seg(tt, 0.1, 0.5), H * 0.80, 86, "head", C.WHITE, 0.12, rise=24)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    def d_zhivkov(tt, d):
        img = foto_kb("zhivkov", tt, d, 0.05, 0.5, 0.3, 0.55, C.seg(tt, 0.3, 0.9))
        img = C.fade(img, 0.8)
        k10 = C.seg(tt, c_10 - c_zhivkov, c_10 - c_zhivkov + 1.0)
        lays = [label("ПО СЛОВАМ СОСЕДЕЙ", C.seg(tt, 1.0, 1.4), 150, 40, x=SAFE_X, anchor="ls", track=0.3), red_line(C.seg(tt, 1.0, 1.4), SAFE_X, SAFE_X + 70, 164, 3),
                word("РАЗРЕШАЕТ ПРИНИМАТЬ", C.seg(tt, 2.2, 2.6), H * 0.80, 70, "head", C.WHITE, 0.12, x=W - SAFE_X, anchor="rs", rise=22),
                label("ОФИЦИАЛЬНО", C.seg(tt, c_ofic - c_zhivkov, c_ofic - c_zhivkov + 0.4), H * 0.80 + 60, 40, C.WHITE, x=W - SAFE_X, anchor="rs")]
        if k10 > 0:
            lays.append(C.big_number("10 ЛЕВОВ", None, "за приём · по словам соседей", k10, cx=W * 0.62, cy=H * 0.42, px=260, count_from=0))
        return C.over(img, *lays).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_ulica), (c_kabel, b_tel), (c_asf, c_asf_), (c_zhivkov, d_zhivkov)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 36 · июль 1981 · внезапно · 38 лет · дверь не закрылась ═════════════════════════
@scene("36")
def s36(t, dur):
    c_umerla = r("36", 170.58)
    c_iyul = r("36", 172.2)
    c_vnez = r("36", 173.83)
    c_39 = r("36", 174.78)
    c_dver = r("36", 176.6)
    c_otkr = r("36", 177.8)

    def a_zh(tt, d):
        img = foto_kb("zhivkova", tt, d, 0.05, 0.32, 0.42, 0.5, 1.0)
        kb_ = C.seg(tt, c_iyul, c_iyul + 1.5)
        if kb_ > 0:
            a = np.asarray(img, np.float32)
            lum = a.mean(axis=2, keepdims=True)
            img = Image.fromarray(np.clip(a * (1 - kb_) + lum * kb_, 0, 255).astype(np.uint8), "RGB")
        lays = [K.date_tag("ИЮЛЬ 1981", C.seg(tt, c_iyul, c_iyul + 0.5)),
                word("ВНЕЗАПНО", C.seg(tt, c_vnez, c_vnez + 0.4), H * 0.80, 96, "head", C.WHITE, 0.14, rise=24)]
        k39 = C.seg(tt, c_39 + 0.6, c_39 + 1.5)
        if k39 > 0:
            img = C.fade(img, 1 - 0.4 * k39)
            lays.append(C.big_number("38 ЛЕТ", None, None, k39, cx=W * 0.68, cy=H * 0.42, px=260, count_from=0))
        return C.over(img, *lays).convert("RGB")

    def b_dver(tt, d):
        img = V.vanga("dom7", DOM, tt, src(1272.44, "21:16.5"), push=0.06, hand=2.0, k_grade=0.7, bw=0.9, **NOVA_BW)
        img = C.over(img, C.caption(*CAP_1974, k=C.seg(tt, 0.3, 0.9))).convert("RGB")
        lays = [word("ДВЕРЬ", C.seg(tt, 0.1, 0.5), H * 0.5 + 60, 170, "head", C.WHITE, 0.14, rise=30),
                label("УЖЕ НЕ ЗАКРЫЛАСЬ", C.seg(tt, c_otkr - c_dver + 0.9, c_otkr - c_dver + 1.3), H * 0.5 + 130, 40, C.WHITE)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_zh), (c_dver, b_dver)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 37 · будущая власть · Пётр Стоянов ═════════════════════════
@scene("37")
def s37(t, dur):
    c_cherez = r("37", 179.73)
    c_stoy = r("37", 182.30)
    c_togda = r("37", 183.4)

    def a_dver(tt, d):
        img = V.vanga("dom8", DOM, tt, src(1272.44, "21:19.5"), push=0.06, hand=2.0, k_grade=0.7, bw=0.9, **NOVA_BW)
        img = C.over(img, C.caption(*CAP_1974, k=1.0)).convert("RGB")
        return C.over(img, label("ЧЕРЕЗ ЭТУ ДВЕРЬ — И БУДУЩАЯ ВЛАСТЬ", C.seg(tt, 0.3, 0.7), H - 120, 36, C.WHITE)).convert("RGB")

    def b_stoy(tt, d):
        name, cap = HRON["stoyanov"][0], HRON["stoyanov"][-1]
        im = C.foto(name)
        true = C.kb(im, tt / d, 0.05, 0.5, 0.2)
        img = fx.proyavka(Image.new("RGB", (W, H), (10, 10, 12)), true, (W * 0.2, 0, W * 0.8, H), C.seg(tt, 0.0, 1.1), seed=13)
        img = V.grade(img, 0.4)
        lays = [C.caption(*cap, k=C.seg(tt, 0.6, 1.1)),
                word("ПЁТР СТОЯНОВ", C.seg(tt, 0.2, 0.6), H * 0.80, 96, "head", C.WHITE, 0.12, rise=26),
                label("ТОГДА ЕЩЁ НЕ ПРЕЗИДЕНТ", C.seg(tt, c_togda - c_stoy, c_togda - c_stoy + 0.4), H * 0.80 + 60, 34)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.1, 0.5)

    fn, tt, d = shots(t, [(0.0, a_dver), (c_stoy, b_stoy)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 38 · В7: президентом станешь ═════════════════════════
@scene("38")
def s38(t, dur):
    img = V.top_shade(V.vanga("v7", V7, t, src(2639.8, "44:13.0"), push=0.03, hand=1.8, k_grade=0.75, zoom=1.35, cx=0.5, cy=0.45), 320, 0.6)
    env_v = V.envelope(V7, src(2639.8, "44:13.0"), 7.5)
    env_a = V.envelope("olga_b7a.mp3", 0.0, 1.07)
    env_b = V.envelope("olga_b7b.mp3", 0.0, 3.11)
    lay = V.oscillo([(env_v, 0.0, C.WHITE), (env_a, 2.3, C.RED), (env_b, 3.7, C.RED)], t, H - 215, 46, SAFE_X, W - SAFE_X)
    k_orig = C.seg(t, 0.2, 0.6) * (1 - C.seg(t, 2.0, 2.4))
    k_per = C.seg(t, 2.3, 2.7) * (1 - C.seg(t, 7.0, 7.5))
    lays = [lay, label("ОРИГИНАЛЬНЫЙ ЗВУК", k_orig, 120, 34, C.GREY, x=W - SAFE_X, anchor="rs"),
            label("ПЕРЕВОД ЗА КАДРОМ", k_per, 120, 34, C.RED, x=W - SAFE_X, anchor="rs"),
            C.caption(*CAP_VITKA, k=C.seg(t, 0.4, 0.9))]
    from scenes2 import perevod_lines
    lays += perevod_lines(["Она сказала ему так.", "Президентом станешь.", "Только смотри потом, что будешь делать с государством."],
                          [C.seg(t, 2.35, 3.3), C.seg(t, 3.75, 4.8), C.seg(t, 5.0, 6.9)], t)
    img = C.over(img, *lays).convert("RGB")
    return C.finish(flash(img, t, 0.08, 0.35), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 39 · осень 1996 · три месяца ═════════════════════════
@scene("39")
def s39(t, dur):
    c_osen = r("39", 185.15)
    c_vybory = r("39", 186.3)
    c_ne_dozh = r("39", 187.76)

    def a_vybory(tt, d):
        img = foto_kb("stoyanov", 1.0 + tt, d + 1.0, 0.04, 0.5, 0.2, 0.4, 1.0)
        lays = [K.date_tag("ОСЕНЬ 1996", C.seg(tt, 0.1, 0.5), sub="выборы президента Болгарии"),
                word("ВЫИГРАЛ ВЫБОРЫ", C.seg(tt, c_vybory - c_osen, c_vybory - c_osen + 0.4), H * 0.80, 86, "head", C.WHITE, 0.12, rise=24)]
        return C.over(img, *lays).convert("RGB")

    def b_tri(tt, d):
        img = C.kb(dark_bg(19, (14, 14, 17)), tt / d, 0.03, 0.5, 0.5)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        s = SS
        x0, x1, y = SAFE_X + 120, W - SAFE_X - 120, H * 0.55
        k = C.seg(tt, 0.1, 1.0)
        dd.line([(x0 * s, y * s), ((x0 + (x1 - x0) * C.out_cubic(k)) * s, y * s)], fill=C.RED + (255,), width=6 * s)
        for x, big, small, kk in ((x0, "11 АВГУСТА 1996", "её не стало", C.seg(tt, 0.0, 0.4)), (x1, "ОСЕНЬ 1996", "он выиграл выборы", C.seg(tt, 0.8, 1.2))):
            a = int(255 * kk)
            if a <= 0:
                continue
            dd.ellipse([(x - 10) * s, (y - 10) * s, (x + 10) * s, (y + 10) * s], fill=C.WHITE + (a,))
            C.tracked(dd, x * s, (y - 40) * s, big, C.font("head", 48 * s), C.WHITE + (a,), 0.06, "ms")
            C.tracked(dd, x * s, (y + 66) * s, small.upper(), C.font("head_l", 26 * s), C.GREY + (a,), 0.3, "ms")
        img = C.over(img, C.done(lay), C.big_number("3 МЕСЯЦА", None, "не дожила", C.seg(tt, 1.0, 1.8), cx=W / 2, cy=H * 0.30, px=200, count_from=0, rings=False)).convert("RGB")
        return C.grain(img, t, 0.035)

    fn, tt, d = shots(t, [(0.0, a_vybory), (c_ne_dozh, b_tri)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 40 · по средам · Живков и Брежнев · один шаг до Кремля ═════════════════════════
K.CITIES.update({"Москва": (37.62, 55.75)})
PUT = K.Okno(lon=(18.0, 46.0), lat=(39.5, 58.5))


@scene("40")
def s40(t, dur):
    c_doch = r("40", 190.11)
    c_sredam = r("40", 192.2)
    c_pervyi = r("40", 193.58)
    c_obnim = r("40", 195.3)
    c_sssr = r("40", 196.2)
    c_dveri = r("40", 198.14)
    c_shag = r("40", 199.8)

    def a_sredy(tt, d):
        img = foto_kb("zhivkova", 2.0 + tt, d + 2.0, 0.05, 0.32, 0.42, 0.5, 1.0)
        lays = [word("ПО СРЕДАМ", C.seg(tt, c_sredam, c_sredam + 0.4), H * 0.80, 110, "head", C.WHITE, 0.14, rise=26),
                label("ДОЧЬ ПЕРВОГО ЧЕЛОВЕКА БОЛГАРИИ", C.seg(tt, c_doch + 0.2, c_doch + 0.6), 150, 36, x=SAFE_X, anchor="ls", track=0.3),
                red_line(C.seg(tt, c_doch + 0.2, c_doch + 0.6), SAFE_X, SAFE_X + 70, 164, 3)]
        return C.over(img, *lays).convert("RGB")

    def b_dvoe(tt, d):
        # два портрета рядом: Живков (фото CC0) и Брежнев (кадр Nixon Library) — совместного снимка со свободными правами нет
        canvas = Image.new("RGB", (W, H), (10, 10, 12))
        half = (W // 2, H)
        zh = C.kb(C.foto(HRON["zhivkov"][0]), tt / d, 0.05, 0.5, 0.25, size=half)
        name, s0, cap_b = BREZH
        br = V.vid("brezh2", name, 158.0, zoom=1.25, cx=0.5, cy=0.45).at(tt)
        br = C.kb(br, 0.0, 0.0, 0.5, 0.5, size=half)
        kz = C.seg(tt, 0.0, 0.5)
        kbr = C.seg(tt, c_sssr - c_pervyi, c_sssr - c_pervyi + 0.5)
        canvas.paste(V.grade(zh, 0.5), (int(-W / 2 * (1 - C.out_cubic(kz))), 0))
        if kbr > 0:
            canvas.paste(V.grade(br, 0.8), (W // 2 + int(W / 2 * (1 - C.out_cubic(kbr))), 0))
        lay = C.layer()
        ImageDraw.Draw(lay).rectangle([(W / 2 - 3) * SS, 0, (W / 2 + 3) * SS, H * SS], fill=(10, 10, 12, 255))
        lays = [C.done(lay), C.caption(*HRON["zhivkov"][-1], k=C.seg(tt, 0.4, 0.9)),
                C.caption(*cap_b, k=kbr, x=W / 2 + SAFE_X),
                label("ПЕРВЫЙ ЧЕЛОВЕК БОЛГАРИИ", C.seg(tt, 0.3, 0.7), 150, 34, x=SAFE_X, anchor="ls", track=0.3),
                label("ПЕРВЫЙ ЧЕЛОВЕК СОВЕТСКОГО СОЮЗА", C.seg(tt, c_sssr - c_pervyi + 0.3, c_sssr - c_pervyi + 0.7), 150, 34, x=W / 2 + SAFE_X, anchor="ls", track=0.3)]
        return flash(C.over(canvas, *lays).convert("RGB"), tt, 0.08, 0.35)

    def c_shag_(tt, d):
        base = K.base(PUT, hot="Bulgaria")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.7, 0, 255).astype(np.uint8), "RGB")
        kl = C.seg(tt, 0.3, 2.0)
        lays = [K.city_layer(["Петрич", "София", "Москва"], C.seg(tt, 0.1, 0.5), okno=PUT, px=34),
                K.line_layer([K.CITIES["Петрич"], K.CITIES["София"], K.CITIES["Москва"]], kl, okno=PUT, width=5, dash=(18, 14), glow=True, head=True),
                K.date_tag("ОДИН ШАГ", C.seg(tt, c_shag - c_dveri, c_shag - c_dveri + 0.5), sub="от этой двери до Кремля")]
        img = C.over(base, *lays).convert("RGB")
        img = C.kb(img, tt / d, 0.08, 0.6, 0.35)
        return flash(C.grain(img, t, 0.03), tt, 0.08, 0.35)

    fn, tt, d = shots(t, [(0.0, a_sredy), (c_pervyi, b_dvoe), (c_dveri, c_shag_)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.6, grain_k=0.0, vig=0.3)
