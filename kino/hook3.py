#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Третий отрезок 6:28 → конец — сцены 19-31 заново по журналу 19.11,
тем же методом, что hook.py / hook2.py: планы ≤5 с (карта и отрисовка —
дольше), живое видео архива, зал убран везде (п.41/53/54/56), любой текст в
полях SAFE_X/SAFE_Y (п.45/48), полка B/H во второй половине (п.55):
B3 зона-свечение, B6 кольцо-пульс, B20 заголовок брифинга, H3 карта фоном
под текстом, H6 число со счётчиком, H7/H8 шкала времени с миниатюрами.
Карточки под портретом (п.47 одобрено): карточка 4 «Китай» = Путин и Си
(п.49), карточка 5 = Каллас (п.52), «ожившее фото» на карточках 1 и 4 (п.50-51).
Сцены 20 (вставка WEF одобрена), 23 (дом) и 25 (хроника) остаются из scenes_c.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import karta as K
import scenes_a as A
import scenes_b as B
import scenes_c as Cc
import hook as Hk
import hook2 as H2
from core import W, H, SS
from cuts import CUTS

scene = A.scene
vid, foto_bw, shots, flash, modern, chronicle = Hk.vid, Hk.foto_bw, Hk.shots, Hk.flash, Hk.modern, Hk.chronicle
word, red_line, fit_px, dark_video = Hk.word, Hk.red_line, Hk.fit_px, Hk.dark_video
cap, act, lines_in, world_map = H2.cap, H2.act, H2.lines_in, H2.world_map
SAFE_X, SAFE_Y = Hk.SAFE_X, Hk.SAFE_Y
_c = {}


# ═════════════════════════ помощники полки ═════════════════════════
def glow_ring(x, y, k, r_max=120, color=C.RED, width=4):
    """B6 кольцо-пульс: расходится от точки и гаснет"""
    if k <= 0 or k >= 1:
        return None
    im = C.layer()
    d = ImageDraw.Draw(im)
    r = (10 + r_max * C.out_cubic(k)) * SS
    a = int(230 * (1 - k))
    d.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], outline=color + (a,), width=width * SS)
    lay = C.done(im)
    return Image.alpha_composite(lay.filter(ImageFilter.GaussianBlur(7)), lay)


def glow_zone(coords, k, okno=K.UA, color=C.RED, fill_a=90, spread=26):
    """B3 зона угрозы: заливка и светящийся край"""
    if k <= 0:
        return None
    z = K.zone_layer(coords, 1.0, okno=okno, color=color, fill_a=fill_a, outline=True)
    g = z.filter(ImageFilter.GaussianBlur(spread))
    g = C.alpha(g, 0.9)
    out = Image.alpha_composite(g, z)
    return C.alpha(out, C.smoother(k))


def title_b20(white, accent, k, x=SAFE_X + 20, y=150, px=56):
    """B20 заголовок брифинга: белое слово, красный акцент, черта растёт"""
    if k <= 0:
        return None
    kk = C.out_cubic(k)
    im = C.layer()
    d = ImageDraw.Draw(im)
    a = int(255 * C.clamp(k * 2))
    f = C.font("head", px * SS)
    yy = (y + (1 - kk) * 16) * SS
    w1 = C.text_w(d, white, f, 0.06)
    C.tracked(d, x * SS, yy, white, f, C.WHITE + (a,), 0.06)
    if accent:
        C.tracked(d, x * SS + w1 + px * 0.35 * SS, yy, accent, f, C.RED + (a,), 0.06)
    d.rectangle([x * SS, (y + 16) * SS, (x + 260 * kk) * SS, (y + 19) * SS], fill=C.RED + (a,))
    return C.done(im)


# ── шкала времени H7/H8: ось 1950-2026, вехи, диапазоны, миниатюры кадров
TL_X0, TL_X1, TL_Y = SAFE_X + 70, W - SAFE_X - 70, H - 230
TL_LO, TL_HI = 1950, 2026


def tl_x(year):
    return TL_X0 + (TL_X1 - TL_X0) * (year - TL_LO) / (TL_HI - TL_LO)


def timeline(k_axis, marks=(), spans=(), thumbs=()):
    """marks: (год, подпись, k) · spans: (год0, год1, подпись, k, обрыв) · thumbs: (год, кадр, k)"""
    if k_axis <= 0:
        return None
    im = C.layer()
    d = ImageDraw.Draw(im)
    a = int(255 * C.clamp(k_axis * 2))
    xe = TL_X0 + (TL_X1 - TL_X0) * C.out_cubic(k_axis)
    d.rectangle([TL_X0 * SS, TL_Y * SS, xe * SS, (TL_Y + 2) * SS], fill=C.GREY2 + (a,))
    f_tick = C.font("head_l", 20 * SS)
    for yr in range(1950, 2030, 10):
        x = tl_x(yr)
        if x <= xe:
            d.rectangle([x * SS, (TL_Y - 6) * SS, (x + 1) * SS, (TL_Y + 8) * SS], fill=C.GREY2 + (a,))
            C.tracked(d, x * SS, (TL_Y + 36) * SS, str(yr), f_tick, C.GREY2 + (a,), 0.16, "ms")
    for y0, y1, label, k, broken in spans:
        if k <= 0:
            continue
        xa, xb = tl_x(y0), tl_x(y0 + (y1 - y0) * C.out_cubic(k))
        d.rectangle([xa * SS, (TL_Y - 22) * SS, xb * SS, (TL_Y - 12) * SS], fill=C.RED + (230,))
        if broken and k >= 1:
            d.line([(xb * SS, (TL_Y - 36) * SS), ((xb + 12) * SS, (TL_Y - 2) * SS)], fill=C.WHITE + (255,), width=3 * SS)
        if k > 0.5:
            ka = int(255 * C.seg(k, 0.5, 1.0))
            C.tracked(d, (xa + xb) / 2 * SS, (TL_Y - 36) * SS, label, C.font("head", 28 * SS), C.WHITE + (ka,), 0.1, "ms")
    for yr, label, k in marks:
        if k <= 0:
            continue
        x = tl_x(yr)
        ka = int(255 * C.smoother(k))
        r = 7 * SS
        d.ellipse([x * SS - r, TL_Y * SS + SS - r, x * SS + r, TL_Y * SS + SS + r], fill=C.RED + (ka,))
        C.tracked(d, x * SS, (TL_Y + 70) * SS, str(yr), C.font("head", 30 * SS), C.WHITE + (ka,), 0.06, "ms")
        C.tracked(d, x * SS, (TL_Y + 96) * SS, label.upper(), C.font("head_l", 20 * SS), C.GREY + (ka,), 0.22, "ms")
    lay = C.done(im)
    for yr, fr, k in thumbs:
        if k <= 0 or fr is None:
            continue
        bw, bh = 176, 99
        x = int(tl_x(yr))
        th = fr.convert("RGB").resize((bw, bh), Image.LANCZOS)
        card = Image.new("RGBA", (bw + 4, bh + 4), C.GREY + (255,))
        card.paste(th, (2, 2))
        card = C.alpha(card, C.smoother(k))
        cx = min(max(x - bw // 2, SAFE_X), W - SAFE_X - bw)
        lay.alpha_composite(card, (cx, TL_Y + 108))
    return lay


def thumb_of(key, name, start):
    if key not in _c:
        _c[key] = vid(key, name, start, size=(352, 198)).at(0.0).copy()
    return _c[key]


def map_dim(base, k=0.42):
    """H3: карта фоном под текстом — притушена и слегка размыта"""
    return dark_video(base.filter(ImageFilter.GaussianBlur(1.2)), k)


# ═════════════════════════ 19 · Спектейтор ═════════════════════════
T_ACT19 = 1.4


@scene("19")
def s19(t, dur):
    c_poz = C.cue("19", "ней меняет позицию", 8.2)
    c_vos = C.cue("19", "которой держался восемь лет", 9.6)

    def title(tt, d):
        return act("III", "РАЗВОРОТ", tt, d)

    def zhurnal(tt, d):
        if "sp" not in Cc._s19:
            Cc._s19["sp"] = Cc.magazine_spread()
        page = Cc._s19["sp"]
        k = C.smoother(C.seg(tt, 0.0, d))
        scale = C.lerp(0.70, 1.25, k)
        cx, cy = C.lerp(1400, 700, k), C.lerp(950, 560, k)
        big = page.resize((int(page.size[0] * scale), int(page.size[1] * scale)), Image.LANCZOS)
        img = Image.new("RGB", (W, H), (40, 38, 36))
        img.paste(big, (int(W / 2 - cx * scale), int(H / 2 - cy * scale)))
        img = C.vignette(img, 0.45)
        return C.grain(C.over(img, cap("The Spectator", "17 декабря 2022", "статья Генри Киссинджера", C.seg(tt, 0.4, 1.2))).convert("RGB"), t, 0.03)

    def portret(tt, d):
        # долли-зум: лицо держит размер, фон наваливается
        if "p" not in Cc._s19:
            Cc._s19["p"] = C.foto("kissinger_portrait_late.jpg").convert("L").convert("RGB")
        p = Cc._s19["p"]
        k = C.smoother(C.seg(tt, 0.0, d))
        face = C.kb(p, 0.0, 0.05, 0.5, 0.28)
        back = C.kb(p, 1.0, 0.05 + 0.55 * k, 0.5, 0.28).filter(ImageFilter.GaussianBlur(3 + 6 * k))
        m = Image.new("L", (W // 4, H // 4), 0)
        ImageDraw.Draw(m).ellipse([W // 4 * 0.33, H // 4 * 0.05, W // 4 * 0.67, H // 4 * 0.9], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(28)).resize((W, H), Image.BILINEAR)
        img = back.copy()
        img.paste(face, (0, 0), m)
        img = C.vignette(C.fade(img, 1 - 0.3 * k), 0.5 + 0.3 * k)
        return C.grain(C.over(img, word("ПОЗИЦИЯ, КОТОРОЙ ДЕРЖАЛСЯ ВОСЕМЬ ЛЕТ", C.seg(tt, c_vos - c_poz, c_vos - c_poz + 0.5), H * 0.84, 54, "head_l", C.GREY, 0.2, rise=16),
                              cap("Генри Киссинджер", "девяносто девять лет", "портрет", C.seg(tt, 0.3, 1.1), y=140)).convert("RGB"), t, 0.035)

    fn, tt, d = shots(t, [(0.0, title), (T_ACT19, zhurnal), (c_poz, portret)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.5, grain_k=0.0)


# ═════════════════════════ 21 · Условия сделки: карта, затем формула (H3) ═════════════════════════
@scene("21")
def s21(t, dur):
    c_uhod = C.cue("21", "Россия уходит со всего", 5.1)
    c_krym = C.cue("21", "Крым и старые районы", 9.2)
    c_ref = C.cue("21", "через референдумы", 13.6)
    c_form = C.cue("21", "здесь и появляется та самая формула", 16.8)
    c_razn = C.cue("21", "разные вопросы", 20.3)
    c_pak = C.cue("21", "но решаются одним пакетом", 21.6)

    base = K.base()
    lays = [K.line_layer(K.LINE_2015, C.seg(t, 0.2, 2.6), width=5)]
    k_zone = C.seg(t, 2.0, 3.2) * (1 - C.seg(t, c_uhod, c_uhod + 2.2))
    if k_zone > 0:
        lays.append(C.alpha(K.zone_layer(K.ZONE_2022, 1.0, color=C.WHITE, fill_a=55, hatch=True), k_zone))
    lays.append(K.city_layer(["Киев", "Донецк", "Луганск", "Херсон", "Севастополь"], C.seg(t, 0.8, 1.6), side={"Херсон": "l", "Севастополь": "t"}))
    kk = C.seg(t, c_krym, c_krym + 1.2)
    if kk > 0:
        lays.append(K.zone_layer(K.CRIMEA, kk, fill_a=110))
        lays.append(K.zone_layer(K.DONBAS_OLD, kk, fill_a=95))
    if t < c_uhod:
        lays.append(K.date_tag("24.02.2022", C.seg(t, 0.2, 0.8), sub="перемирие по линии вторжения"))
    elif t < c_krym:
        lays.append(K.date_tag("УХОДИТ", C.seg(t, c_uhod, c_uhod + 0.5), sub="со всего, что заняла после"))
    else:
        lays.append(K.date_tag("ОТДЕЛЬНО И ПОЗЖЕ", C.seg(t, c_krym, c_krym + 0.5), px=48, sub="Крым и старый Донбасс"))
    lays += lines_in([(c_ref, "референдумы под международным наблюдением")], t, "head_l", 36, SAFE_X + 20, H * 0.86, "ls", C.GREY, track=0.16)
    img = C.over(base, *lays).convert("RGB")
    img = C.kb(img, C.smoother(t / dur), 0.08, 0.62, 0.55)
    kf = C.seg(t, c_form, c_form + 0.8)
    if kf > 0:
        # H3: карта уходит в фон, поверх — формула
        img = Image.blend(img, map_dim(img, 0.38), C.smoother(kf))
        kr = C.seg(t, c_razn, c_razn + 0.5)
        kp = C.seg(t, c_pak, c_pak + 0.6)
        img = C.over(img, word("ТЕРРИТОРИЯ", kf, H * 0.46, 150, x=W * 0.30),
                     word("ЧЛЕНСТВО", C.seg(t, c_form + 0.3, c_form + 1.1), H * 0.46, 150, x=W * 0.72),
                     word("разные вопросы", kr * (1 - kp), H * 0.46 + 70, 44, "serif_i", C.GREY, 0.0, rise=14),
                     red_line(kp, W * 0.30 - 300, W * 0.72 + 260, H * 0.46 + 40, 6),
                     word("ОДИН ПАКЕТ", kp, H * 0.46 + 190, 120, color=C.RED)).convert("RGB")
    return C.finish(C.grain(img, t, 0.03), t, dur, fi=0.4, fo=0.5, grain_k=0.0)


# ═════════════════════════ 22 · Восемь часов, щит и узда ═════════════════════════
@scene("22")
def s22(t, dur):
    c_8 = C.cue("22", "восемь часов разговора", 3.9)
    c_100 = C.cue("22", "сто. Там он сказал вещь", 6.9)
    c_kiev = C.cue("22", "которую в Киеве вряд ли оценили", 8.7)
    c_voor = C.cue("22", "Украину так", 11.6)
    c_samoy = C.cue("22", "что она стала самой вооружённой", 12.7)
    c_naim = C.cue("22", "при этом с наименее опытным", 15.6)
    c_poet = C.cue("22", "руководством. Поэтому", 18.0)
    c_nato = C.cue("22", "её безопаснее держать внутри НАТО", 20.7)
    c_chto = C.cue("22", "чтобы вопросы вроде территориальных", 23.1)
    c_odin = C.cue("22", "одиночку. То есть альянс", 25.7)
    c_shit = C.cue("22", "Украине не только как защита", 28.4)
    c_uzda = C.cue("22", "узда", 30.8)

    def ekonomist(tt, d):
        fr = vid("k100e", "kissinger_100_2023.mp4", 0.5).at(tt)
        img = C.kb(fr.convert("L").convert("RGB"), tt / d, 0.05, 0.5, 0.4)
        img = C.film_look(img, t, 0.35, scratches=False)
        k8 = C.seg(tt, c_8, c_8 + 1.4)
        lays = [cap("Генри Киссинджер", "The Economist · апрель 2023", "хроника CBS", C.seg(tt, 0.3, 1.0))]
        if k8 > 0:
            lays.append(C.big_number("8 ЧАСОВ", "два дня разговора", None, k8, cx=W * 0.30, cy=H * 0.42, px=200))
        lays.append(word("ЧЕРЕЗ МЕСЯЦ — СТО ЛЕТ", C.seg(tt, c_100, c_100 + 0.5), H * 0.80, 46, "head_l", C.GREY, 0.2, x=W * 0.30, rise=14))
        return C.over(img, *lays)

    def vooruzhil(tt, d):
        fr = vid("zel22", "zelensky_2022_05_25.mp4", 6.0, zoom=1.25, cx=0.3, cy=0.3).at(tt)
        img = dark_video(modern(C.kb(fr, tt / d, 0.05, 0.4, 0.4), t, 0.3), 0.45)
        lay = lines_in([(0.1, "«Запад вооружил Украину так,"), (c_samoy - c_kiev, "что она стала самой вооружённой страной Европы —"),
                        (c_naim - c_kiev, "при наименее опытном стратегическом руководстве»")], tt, "serif_i", 54, W / 2, H * 0.40, "ms")
        return flash(C.over(img, *lay, cap("Киев", "май 2022", "Офис президента Украины", C.seg(tt, 0.4, 1.0))), tt, 0.08, 0.5)

    def nato(tt, d):
        fr = vid("natofl", "nato_finland_2023.mp4", 0.0).at(tt)
        img = dark_video(modern(C.kb(fr, tt / d, 0.06, 0.5, 0.4), t, 0.3), 0.5)
        lay = lines_in([(c_nato - c_poet, "«безопаснее держать её внутри НАТО,"), (c_chto - c_poet, "чтобы территориальные вопросы"),
                        (c_chto - c_poet + 0.9, "она не решала в одиночку»")], tt, "serif_i", 54, W / 2, H * 0.40, "ms")
        return C.over(img, *lay, cap("Брюссель", "штаб-квартира НАТО · 2023", "НАТО", C.seg(tt, 0.4, 1.0)))

    def uzda(tt, d):
        fr = vid("k100f", "kissinger_100_2023.mp4", 20.0).at(tt)
        img = dark_video(C.film_look(C.kb(fr.convert("L").convert("RGB"), tt / d, 0.06, 0.5, 0.4), t, 0.35, scratches=False), 0.55)
        ks, ku = C.seg(tt, c_shit - c_odin, c_shit - c_odin + 0.5), C.seg(tt, c_uzda - c_odin, c_uzda - c_odin + 0.5)
        return flash(C.over(img, word("АЛЬЯНС — НЕ ТОЛЬКО ЩИТ", ks, H * 0.42, 110),
                            red_line(C.seg(tt, c_uzda - c_odin - 0.3, c_uzda - c_odin + 0.4), W / 2 - 160, W / 2 + 160, H * 0.42 + 40, 5),
                            word("ЕЩЁ И УЗДА", ku, H * 0.42 + 190, 150, color=C.RED)), tt, 0.08, 0.5)

    fn, tt, d = shots(t, [(0.0, ekonomist), (c_kiev, vooruzhil), (c_poet, nato), (c_odin, uzda)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.4, fo=0.5, grain_k=0.0)


# ═════════════════════════ 24 · Стена улик: карточки в полях, «ожившее фото» ═════════════════════════
CW, CH = 480, 330
PICW, PICH = CW - 60, 156
CARDS3 = [("01", "ЗА СТОЛОМ", "Абу-Даби · Аляска", "alaska_2025_08_15.mp4"),
          ("02", "ЛИНИЯ", "спор о линии, не о справедливости", None),
          ("03", "ФОРМУЛА", "территория за НАТО", None),
          ("04", "КИТАЙ", "союз, которого он боялся", "putin_xi_2023.mp4"),
          ("05", "ЕВРОПА", "место за столом есть, разговора нет", "kallas_2024.jpg")]
LIVE_START = {"alaska_2025_08_15.mp4": 4.0, "putin_xi_2023.mp4": 0.0}
LIVE0, LIVE1 = 1.5, 3.5          # стоп-кадр 1,5 с → живое видео 2 с → стоп-кадр
POS = [(W * 0.185, H * 0.28), (W * 0.185, H * 0.72), (W * 0.50, H * 0.78), (W * 0.815, H * 0.28), (W * 0.815, H * 0.72)]
_w = {}


def _card_base(i):
    """картон карточки без снимка (кэш): рамка, кнопка, номер, заголовок, подпись"""
    if ("base", i) in _w:
        return _w[("base", i)]
    num, title, sub, pic = CARDS3[i]
    w, h = CW, CH
    im = C.paper(w, h, seed=60 + int(num), tone=(228, 222, 208)).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(120, 112, 100, 255), width=2)
    d.ellipse([w / 2 - 11, 12, w / 2 + 11, 34], fill=C.RED + (255,))
    d.ellipse([w / 2 - 5, 18, w / 2 + 5, 28], fill=(255, 120, 110, 255))
    y = 218
    if num == "02":
        mb = K.base(size=(PICW, PICH), relief=False).convert("RGBA")
        o = K.Okno((28.0, 42.0), (44.5, 51.5), PICW, PICH)
        lay = Image.new("RGBA", (PICW * SS, PICH * SS), (0, 0, 0, 0))
        ImageDraw.Draw(lay).line(o.pts(K.LINE_NOW, SS), fill=C.RED + (255,), width=3 * SS, joint="curve")
        mb.alpha_composite(lay.resize((PICW, PICH), Image.LANCZOS))
        im.paste(mb, (30, 48))
    elif num == "03":
        f = C.font("head", 58)
        d.text((w / 2, 100), "ТЕРРИТОРИЯ", font=f, fill=C.INK + (255,), anchor="mm")
        d.text((w / 2, 160), "ЗА НАТО", font=f, fill=C.RED + (255,), anchor="mm")
    d.text((30, y), num, font=C.font("head_r", 28), fill=C.RED + (255,))
    d.text((76, y - 4), title, font=C.font("head", 38), fill=C.INK + (255,))
    fs = C.font("serif_i", 24)
    for j, ln in enumerate(C.wrap(sub, "serif_i", 24, w - 60)[:2]):
        d.text((30, y + 48 + j * 30), ln, font=fs, fill=(70, 66, 60, 255))
    _w[("base", i)] = im
    return im


def _card(i, live_tt=None):
    """карточка целиком; live_tt — секунды с появления для «ожившего фото» (п.50):
    стоп-кадр → живое видео в цвете → стоп-кадр"""
    num, title, sub, pic = CARDS3[i]
    if pic is None:
        return _card_base(i)
    if pic.endswith(".mp4"):
        v = vid("card" + num, pic, LIVE_START.get(pic, 0.0), size=(640, 360))
        if live_tt is None:
            fr, color = v.at(LIVE1 - LIVE0), False
        elif live_tt < LIVE0:
            fr, color = v.at(0.0), False
        elif live_tt < LIVE1:
            fr, color = v.at(live_tt - LIVE0), True
        else:
            fr, color = v.at(LIVE1 - LIVE0), False
        ph = C.cover(fr, (PICW, PICH), 0.5, 0.3)
        if not color:
            ph = ph.convert("L").convert("RGB")
    else:
        if ("pic", i) not in _w:
            _w[("pic", i)] = C.cover(C.foto(pic), (PICW, PICH), 0.5, 0.22).convert("L").convert("RGB")
        ph = _w[("pic", i)]
    im = _card_base(i).copy()
    im.paste(ph, (30, 48))
    return im


def wall(t, cards_k, pull=0.0, live=None):
    """тёмная стена, портрет в центре, пять карточек в полях с нитями к портрету.
    cards_k — появление пяти карточек 0…1; pull — отъезд 0…1; live — {i: секунды с появления}"""
    if "wall" not in _w:
        base = Image.new("RGB", (W, H), (24, 23, 25))
        n = C.noise(W, H, 77, 3.0).filter(ImageFilter.GaussianBlur(1.2))
        a = np.asarray(base, np.float32) + (np.asarray(n, np.float32) - 128)[:, :, None] * 0.12
        _w["wall"] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
        p = C.foto("kissinger_portrait_late.jpg").convert("L").convert("RGB")
        _w["port"] = C.cover(p, (380, 470), 0.5, 0.25)
    live = live or {}
    sc = C.lerp(1.0, 0.80, C.smoother(pull))
    big = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    cx, cy = W / 2, H * 0.44
    for i, k in enumerate(cards_k):
        if k <= 0:
            continue
        kk = C.out_cubic(k)
        px, py = POS[i]
        ex, ey = cx + (px - cx) * (1 - kk), cy + (py - cy) * (1 - kk)
        d.line([(px, py), (ex, ey)], fill=C.RED + (int(220 * min(1, k * 2)),), width=3)
    port = _w["port"].convert("RGBA")
    fr = Image.new("RGBA", (port.size[0] + 24, port.size[1] + 24), (236, 230, 218, 255))
    fr.paste(port, (12, 12))
    sh, pad = C.shadow_box(fr.size, 34, 170)
    big.alpha_composite(sh, (int(cx - fr.size[0] / 2 - pad + 10), int(cy - fr.size[1] / 2 - pad + 16)))
    big.alpha_composite(fr, (int(cx - fr.size[0] / 2), int(cy - fr.size[1] / 2)))
    for i, k in enumerate(cards_k):
        if k <= 0:
            continue
        kk = C.out_back(k)
        tex = _card(i, live.get(i))
        s = 0.86 + 0.14 * kk
        tx = tex.resize((int(tex.size[0] * s), int(tex.size[1] * s)), Image.LANCZOS)
        tx.putalpha(tx.split()[3].point(lambda v: int(v * min(1, k * 3))))
        px, py = POS[i]
        tx = tx.rotate((-4, 3, -2, 4, -3)[i], Image.BICUBIC, expand=True)
        sh, pad = C.shadow_box(tx.size, 26, 150)
        big.alpha_composite(sh, (int(px - tx.size[0] / 2 - pad + 8), int(py - tx.size[1] / 2 - pad + 14)))
        big.alpha_composite(tx, (int(px - tx.size[0] / 2), int(py - tx.size[1] / 2)))
    img = _w["wall"].copy().convert("RGBA")
    if sc != 1.0:
        nw, nh = int(W * sc), int(H * sc)
        img.alpha_composite(big.resize((nw, nh), Image.LANCZOS), ((W - nw) // 2, (H - nh) // 2 + int(10 * (1 - sc))))
    else:
        img.alpha_composite(big)
    return C.vignette(img.convert("RGB"), 0.6)


T_ACT24 = 1.4


@scene("24")
def s24(t, dur):
    c_1 = C.cue("24", "Сбылось первое", 3.1)

    def title(tt, d):
        return act("IV", "СТОЛ", tt, d)

    def stena(tt, d):
        ta = c_1 - T_ACT24
        k1 = C.seg(tt, ta, ta + 0.7)
        img = wall(tt, [k1, 0, 0, 0, 0], live={0: tt - ta} if k1 > 0 else None)
        return C.grain(img, t, 0.03)

    fn, tt, d = shots(t, [(0.0, title), (T_ACT24, stena)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.4, grain_k=0.0)


@scene("24b")
def s24b(t, dur):
    ts = [0.0, C.cue("24b", "Сбылось второе", 0.0), C.cue("24b", "Сбылось третье", 16.3),
          C.cue("24b", "Сбылось четвёртое", 24.1), C.cue("24b", "Сбылось пятое", 44.0)]
    ks = [1.0] + [C.seg(t, ts[i] + 0.2, ts[i] + 0.9) for i in range(1, 5)]
    pull = C.seg(t, ts[4] + 2.0, dur)
    img = wall(t, ks, pull, live={3: t - ts[3] - 0.2} if ks[3] > 0 else None)
    c_tep = C.cue("24b", "Теперь ошибки", 57.4)
    img = C.over(img, word("ТЕПЕРЬ — ОШИБКИ", C.seg(t, c_tep, c_tep + 0.4), H * 0.52, 110)).convert("RGB")
    return C.finish(C.grain(img, t, 0.03), t, dur, fi=0.4, fo=0.5, grain_k=0.0)


# ═════════════════════════ 26 · Три ошибки и слепое пятно ═════════════════════════
CONCERT = [("Лондон", -0.13, 51.5), ("Париж", 2.35, 48.86), ("Берлин", 13.40, 52.52), ("Вена", 16.37, 48.21), ("Петербург", 30.32, 59.94)]


@scene("26")
def s26(t, dur):
    c_dva = C.cue("26", "отводил на начало переговоров два месяца", 2.2)
    c_inache = C.cue("26", "иначе", 4.7)
    c_54 = C.cue("26", "Прошло пятьдесят четыре", 6.3)
    c_voyna = C.cue("26", "Война", 6.3) + 1.8
    c_fin = C.cue("26", "Вторая Финляндия", 11.4)
    c_obr = C.cue("26", "Образец", 11.4) + 2.2
    c_ssyl = C.cue("26", "на который он ссылался", 15.9)
    c_zayav = C.cue("26", "сам подал заявку в НАТО", 18.3)
    c_vstup = C.cue("26", "и вступил в двадцать третьем", 21.0)
    c_poka = C.cue("26", "пока соседа не боятся", 24.1)
    c_tret = C.cue("26", "Третья", 24.1) + 1.4
    c_vern = C.cue("26", "что Россию можно вернуть", 27.8)
    c_mesto = C.cue("26", "если вовремя предложить ей место", 30.9)
    c_xix = C.cue("26", "логика девятнадцатого века", 33.8)
    c_konc = C.cue("26", "концерта великих держав", 35.3)
    c_takih = C.cue("26", "таких держав", 38.3)
    c_neost = C.cue("26", "не осталось", 41.0)
    c_pyatno = C.cue("26", "И одно слепое пятно", 42.3)
    c_mysl = C.cue("26", "которое ошибкой назвать трудно", 43.8)
    c_pole = C.cue("26", "а остальных считал полем", 48.3)
    c_nepole = C.cue("26", "полем", 51.4)
    c_storona = C.cue("26", "а стороной", 52.0)
    c_otkaz = C.cue("26", "которая отказалась играть", 53.1)
    c_4 = C.cue("26", "Из за этого его план опоздал", 58.4)

    def srok(tt, d):
        fr = vid("wef_a", "wef_2023.mp4", 20.0).at(tt)
        img = dark_video(C.film_look(C.kb(fr.convert("L").convert("RGB"), tt / d, 0.05, 0.5, 0.4), t, 0.3, scratches=False), 0.55)
        lay = [title_b20("ОШИБКА 01", "СРОКИ", C.seg(tt, 0.1, 0.6))]
        lay += lines_in([(c_dva, "два месяца на начало переговоров —"), (c_inache, "иначе будет поздно")], tt, "serif_i", 54, W / 2, H * 0.52, "ms")
        lay.append(cap("Генри Киссинджер", "Давос · январь 2023", "Всемирный экономический форум", C.seg(tt, 0.4, 1.0)))
        return C.over(img, *lay)

    def proshlo(tt, d):
        fr = vid("abu_a", "abu_dhabi_2026_11.mp4", 2.0, zoom=1.12).at(tt)
        img = dark_video(modern(C.kb(fr, tt / d, 0.05, 0.5, 0.45), t, 0.3), 0.4)
        lay = [C.big_number("54 МЕСЯЦА", "прошло", None, C.seg(tt, 0.0, 1.6), cx=W / 2, cy=H * 0.40, px=210, count_from=2)]
        lay += lines_in([(c_voyna - c_54, "война продолжается, переговоры тоже — одно другому не мешает")], tt, "head_l", 40, W / 2, H * 0.78, "ms", C.GREY, track=0.14)
        lay.append(cap("Абу-Даби", "ноябрь 2026 · переговоры", "пул", C.seg(tt, 0.4, 1.0)))
        return flash(C.over(img, *lay), tt, 0.08, 0.5)

    def finland(tt, d):
        fr = vid("natofl2", "nato_finland_2023.mp4", 2.0).at(tt)
        img = dark_video(modern(C.kb(fr, tt / d, 0.06, 0.5, 0.4), t, 0.3), 0.6)
        lay = [title_b20("ОШИБКА 02", "ФИНЛЯНДИЯ", C.seg(tt, 0.1, 0.6))]
        lay += lines_in([(c_obr - c_fin, "образец нейтралитета,"), (c_ssyl - c_fin, "на который он ссылался с четырнадцатого года")], tt, "serif_i", 54, W / 2, H * 0.52, "ms")
        lay.append(cap("Брюссель", "4 апреля 2023 · флаг Финляндии у штаб-квартиры НАТО", "НАТО", C.seg(tt, 0.4, 1.0)))
        return flash(C.over(img, *lay), tt, 0.08, 0.5)

    def fin_map(tt, d):
        m, base = world_map("fin3", (-14, 46), (34, 72))
        lays = [m.marker((W, H), "Хельсинки", 24.94, 60.17, "заявка · май 2022", k=C.seg(tt, 0.1, 0.6), px=26, ring=C.seg(tt, 0.1, 1.3)),
                m.marker((W, H), "Брюссель", 4.35, 50.85, "НАТО", k=C.seg(tt, 0.5, 1.0), px=24, side="left"),
                m.arc((W, H), (24.94, 60.17), (4.35, 50.85), C.seg(tt, 0.6, 2.6), lift=0.3),
                K.date_tag("2022 → 2023", C.seg(tt, 0.1, 0.6), px=56, sub="заявка → членство")]
        kv = C.seg(tt, c_vstup - c_zayav, c_vstup - c_zayav + 0.4)
        lays.append(glow_ring(*m.xy(4.35, 50.85), C.seg(tt, c_vstup - c_zayav, c_vstup - c_zayav + 1.2), 160))
        lays += lines_in([(c_poka - c_zayav - 1.2, "НЕЙТРАЛИТЕТ ДЕРЖИТСЯ,"), (c_poka - c_zayav, "ПОКА СОСЕДА НЕ БОЯТСЯ")], tt, "head", 72, W / 2, H * 0.80, "ms", track=0.06, lead=1.2)
        img = C.over(base, *lays).convert("RGB")
        return C.grain(C.kb(img, C.smoother(tt / d), 0.06, 0.45, 0.4), t, 0.03)

    def kontsert(tt, d):
        img = C.kb(foto_bw("kremlin_kissinger_2017_b.jpg"), tt / d, 0.08, 0.5, 0.35)
        img = dark_video(C.film_look(img, t, 0.35, scratches=False), 0.6)
        lay = [title_b20("ОШИБКА 03", "КОНЦЕРТ ДЕРЖАВ", C.seg(tt, 0.1, 0.6))]
        lay += lines_in([(c_vern - c_tret, "Россию можно вернуть в европейское равновесие,"), (c_mesto - c_tret, "если вовремя предложить ей место за столом")],
                        tt, "serif_i", 54, W / 2, H * 0.52, "ms")
        lay.append(cap("Москва, Кремль", "июнь 2017", "kremlin.ru", C.seg(tt, 0.4, 1.0)))
        return flash(C.over(img, *lay), tt, 0.08, 0.5)

    def xix(tt, d):
        m, base = world_map("eu19", (-14, 46), (34, 66))
        t_out = c_takih - c_xix
        lays = []
        for i, (n, lon, lat) in enumerate(CONCERT):
            k_in = C.seg(tt, 0.1 + i * 0.25, 0.6 + i * 0.25)
            k_out = C.seg(tt, t_out + i * 0.5, t_out + i * 0.5 + 0.5)
            k = k_in * (1 - k_out)
            if k > 0:
                lays.append(C.alpha(m.marker((W, H), n, lon, lat, None, k=1.0, px=24, side="left" if n in ("Лондон", "Париж") else "right"), k))
        for i in range(len(CONCERT)):
            a, b = CONCERT[i], CONCERT[(i + 1) % len(CONCERT)]
            k_in = C.seg(tt, 1.2 + i * 0.3, 2.2 + i * 0.3)
            k_out = C.seg(tt, t_out + i * 0.5, t_out + i * 0.5 + 0.5)
            if k_in > 0 and k_out < 1:
                lays.append(C.alpha(m.arc((W, H), (a[1], a[2]), (b[1], b[2]), k_in, lift=0.22, head=False), 1 - k_out))
        lays.append(K.date_tag("XIX ВЕК", C.seg(tt, 0.1, 0.6) * (1 - C.seg(tt, t_out, t_out + 0.5)), sub="концерт великих держав"))
        lays.append(K.date_tag("XXI ВЕК", C.seg(tt, t_out, t_out + 0.5), sub="держав, готовых держать равновесие"))
        lays.append(word("НЕ ОСТАЛОСЬ", C.seg(tt, c_neost - c_xix, c_neost - c_xix + 0.5), H * 0.56, 170, color=C.RED))
        img = C.over(base, *lays).convert("RGB")
        return C.grain(C.kb(img, C.smoother(tt / d), 0.05, 0.5, 0.45), t, 0.03)

    def pyatno(tt, d):
        img = C.kb(foto_bw("kissinger_portrait_late.jpg"), tt / d, 0.07, 0.5, 0.28)
        img = dark_video(C.film_look(img, t, 0.35, scratches=False), 0.5)
        lay = [word("СЛЕПОЕ ПЯТНО", C.seg(tt, 0.1, 0.6), H * 0.30, 64, "head_l", C.GREY, 0.3, rise=16)]
        lay += lines_in([(c_mysl - c_pyatno, "всю жизнь мыслил великими державами,"), (c_pole - c_pyatno, "а остальных считал полем")],
                        tt, "serif_i", 56, W / 2, H * 0.74, "ms")
        return C.over(img, *lay)

    def storona(tt, d):
        fr = vid("zel26", "zelensky_2022_05_25.mp4", 14.0, zoom=1.25, cx=0.3, cy=0.3).at(tt)
        img = modern(C.kb(fr, tt / d, 0.05, 0.4, 0.4), t, 0.25)
        kn, ks = C.seg(tt, c_nepole - c_pole, c_nepole - c_pole + 0.5), C.seg(tt, c_storona - c_pole, c_storona - c_pole + 0.5)
        lay = [word("НЕ ПОЛЕ", kn, H * 0.42, 150),
               red_line(C.seg(tt, c_storona - c_pole - 0.3, c_storona - c_pole + 0.4), W / 2 - 120, W / 2 + 120, H * 0.42 + 40, 5),
               word("А СТОРОНА", ks, H * 0.42 + 190, 150, color=C.RED)]
        lay += lines_in([(c_otkaz - c_pole, "отказалась играть по расписанной ей партии")], tt, "head_l", 40, W / 2, H * 0.80, "ms", C.GREY, track=0.14)
        lay.append(cap("Киев", "25 мая 2022 · ответ Киссинджеру", "Офис президента Украины", C.seg(tt, 0.4, 1.0), y=140))
        return flash(C.over(img, *lay), tt, 0.08, 0.5)

    def chetyre(tt, d):
        img = map_dim(C.kb(K.base(), 1.0, 0.1, 0.6, 0.5), 0.35)
        return C.over(img, C.big_number("4 ГОДА", "план опоздал минимум на", None, C.seg(tt, 0.1, 1.4), cx=W / 2, cy=H * 0.46, px=230, count_from=0)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, srok), (c_54, proshlo), (c_fin, finland), (c_zayav, fin_map), (c_tret, kontsert),
                          (c_xix, xix), (c_pyatno, pyatno), (c_pole, storona), (c_4, chetyre)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.3, fo=0.5, grain_k=0.0)


# ═════════════════════════ 27 · Три заморозки: хроника и шкала времени (H7/H8, B6) ═════════════════════════
@scene("27")
def s27(t, dur):
    c_chto = C.cue("27", "что такое заморозка по линии", 3.0)
    c_ist = C.cue("27", "В истории таких", 5.9)
    c_tri = C.cue("27", "заморозок три", 9.0)
    c_kor = C.cue("27", "Корея", 10.3)
    c_net = C.cue("27", "мирного договора нет до сих пор", 16.1)
    c_70 = C.cue("27", "формально находятся в состоянии войны", 18.8)
    c_metr = C.cue("27", "Линия не сдвинулась ни на метр", 22.2)
    c_voy = C.cue("27", "потому что по одну её сторону", 24.2)
    c_ekon = C.cue("27", "выросла в экономику", 29.3)
    c_zhit = C.cue("27", "заморозка", 31.9)
    c_esli = C.cue("27", "если за линией кто то стоит", 34.0)
    c_kipr = C.cue("27", "Кипр", 36.2)
    c_oon = C.cue("27", "ООН провела буферную зону", 40.9)
    c_polv = C.cue("27", "и она стоит уже полвека", 43.0)
    c_priz = C.cue("27", "признал", 45.7)
    c_priv = C.cue("27", "никто ничего не вернул", 46.6)
    c_minsk = C.cue("27", "И Минск", 50.0)
    c_bez = C.cue("27", "за ней и без гарантов", 54.1)
    c_got = C.cue("27", "готовых воевать", 55.7)
    c_7 = C.cue("27", "лет и кончилось самой большой", 58.8)
    c_razn = C.cue("27", "Разница между тремя", 63.7)
    c_kto = C.cue("27", "кто стоит за линией", 69.3)
    c_spor = C.cue("27", "спор о гарантиях", 71.9)

    def th_kor():
        return thumb_of("th_kor", "panmunjom_1953.mp4", 4.0)

    def th_kipr():
        return thumb_of("th_kipr", "cyprus_1974_un.mp4", 3.0)

    def th_minsk():
        if "th_minsk" not in _c:
            mb = K.base(size=(352, 198), relief=False).convert("RGBA")
            o = K.Okno((28.0, 42.0), (44.5, 51.5), 352, 198)
            lay = Image.new("RGBA", (352 * SS, 198 * SS), (0, 0, 0, 0))
            ImageDraw.Draw(lay).line(o.pts(K.LINE_2015, SS), fill=C.RED + (255,), width=3 * SS, joint="curve")
            mb.alpha_composite(lay.resize((352, 198), Image.LANCZOS))
            _c["th_minsk"] = mb.convert("RGB")
        return _c["th_minsk"]

    def zamorozka(tt, d):
        base = K.base()
        lays = [K.line_layer(K.LINE_NOW, C.seg(tt, 0.2, 2.4), width=6),
                K.city_layer(["Киев", "Донецк", "Херсон"], C.seg(tt, 0.6, 1.2), side={"Херсон": "l"})]
        img = map_dim(C.over(base, *lays).convert("RGB"), C.lerp(1.0, 0.45, C.smoother(C.seg(tt, c_chto, c_chto + 0.8))))
        lays2 = [word("ЗАМОРОЗКА ПО ЛИНИИ", C.seg(tt, c_chto, c_chto + 0.5), H * 0.44, 130)]
        k3 = C.seg(tt, c_ist, c_ist + 1.2)
        if k3 > 0:
            lays2.append(C.big_number("3 ЗАМОРОЗКИ", "в истории", "и все три живы до сих пор", k3, cx=W / 2, cy=H * 0.66, px=150, count_from=0))
        return C.grain(C.over(C.kb(img, C.smoother(tt / d), 0.05, 0.6, 0.5), *lays2).convert("RGB"), t, 0.03)

    def korea_v(tt, d):
        fr = vid("pan1", "panmunjom_1953.mp4", 1.0).at(tt)
        img = chronicle(C.kb(fr, tt / d, 0.06, 0.5, 0.4), t, 0.8)
        return flash(C.over(img, K.date_tag("1953", C.seg(tt, 0.1, 0.6), sub="Пханмунджом · перемирие"),
                            cap("Корея", "27 июля 1953", "архив США", C.seg(tt, 0.3, 0.9))), tt, 0.08, 0.5)

    def shkala(tt, d, marks_k, spans_k, thumbs_k, text=()):
        m, base = world_map("w27", (-10, 150), (5, 68))
        lays = [m.marker((W, H), "Корея", 126.98, 37.95, "1953", k=marks_k[0], px=26, side="left"),
                m.marker((W, H), "Кипр", 33.37, 35.17, "1974", k=marks_k[1], px=26),
                m.marker((W, H), "Минск", 27.56, 53.90, "2015", k=marks_k[2], px=26)]
        for (lon, lat), kk in zip(((126.98, 37.95), (33.37, 35.17), (27.56, 53.90)), marks_k):
            if 0 < kk < 1:
                lays.append(glow_ring(*m.xy(lon, lat), kk, 140))
        lays.append(timeline(C.seg(tt, 0.0, 1.2),
                             marks=[(1953, "Корея", marks_k[0]), (1974, "Кипр", marks_k[1]), (2015, "Минск", marks_k[2])],
                             spans=[(1953, 2023, "70 ЛЕТ", spans_k[0], False), (1974, 2024, "50 ЛЕТ", spans_k[1], False), (2015, 2022, "7 ЛЕТ", spans_k[2], True)],
                             thumbs=[(1953, th_kor() if thumbs_k[0] > 0 else None, thumbs_k[0]), (1974, th_kipr() if thumbs_k[1] > 0 else None, thumbs_k[1]),
                                     (2015, th_minsk() if thumbs_k[2] > 0 else None, thumbs_k[2])]))
        lays += list(text)
        img = C.over(base, *lays).convert("RGB")
        return C.grain(img, t, 0.03)

    def korea_map(tt, d):
        return shkala(tt, d, [C.seg(tt, 0.1, 0.9), 0, 0], [C.seg(tt, 0.8, 2.6), 0, 0], [C.seg(tt, 0.4, 1.0), 0, 0],
                      lines_in([(c_70 - c_net, "формально в состоянии войны — семьдесят лет")], tt, "head_l", 40, W / 2, 130, "ms", C.GREY, track=0.14))

    def korea_v2(tt, d):
        fr = vid("pan2", "panmunjom_1953.mp4", 11.0).at(tt)
        img = dark_video(chronicle(C.kb(fr, tt / d, 0.06, 0.5, 0.4), t, 0.8), 0.6)
        lay = lines_in([(c_voy - c_metr, "по одну сторону линии — американские войска"), (c_ekon - c_metr, "одна из двух Корей выросла в экономику размером с российскую")],
                       tt, "serif_i", 50, W / 2, H * 0.40, "ms")
        return flash(C.over(img, word("НИ НА МЕТР", C.seg(tt, 0.1, 0.6), H * 0.80, 110), *lay), tt, 0.08, 0.5)

    def zhit(tt, d):
        return shkala(tt, d, [1.0, 0, 0], [1.0, 0, 0], [1.0, 0, 0],
                      [word("ЗАМОРОЗКА, В КОТОРОЙ МОЖНО ЖИТЬ", C.seg(tt, 0.1, 0.6), 150, 64),
                       word("если за линией кто-то стоит", C.seg(tt, c_esli - c_zhit, c_esli - c_zhit + 0.5), 215, 44, "serif_i", C.GREY, 0.0, rise=14)])

    def kipr_v(tt, d):
        fr = vid("cy1", "cyprus_1974_un.mp4", 0.0, zoom=1.32, cx=0.1, cy=0.9).at(tt)
        img = chronicle(C.kb(fr, tt / d, 0.05, 0.5, 0.4), t, 0.8)
        lay = lines_in([(c_oon - c_kipr, "ООН провела буферную зону")], tt, "head_l", 44, W / 2, H * 0.84, "ms", C.GREY, track=0.14)
        return flash(C.over(img, K.date_tag("1974", C.seg(tt, 0.1, 0.6), sub="Кипр · север острова занят"), *lay,
                            cap("Никосия, Кипр", "1974", "ООН", C.seg(tt, 0.3, 0.9), y=140)), tt, 0.08, 0.5)

    def kipr_map(tt, d):
        return shkala(tt, d, [1.0, C.seg(tt, 0.1, 0.9), 0], [1.0, C.seg(tt, 0.8, 2.6), 0], [1.0, C.seg(tt, 0.4, 1.0), 0],
                      lines_in([(c_priz - c_polv - 1.5, "никто ничего не признал, никто ничего не вернул —"), (c_priv - c_polv + 1.0, "к этому просто привыкли")],
                               tt, "head_l", 40, W / 2, 130, "ms", C.GREY, track=0.14, lead=1.3))

    def minsk(tt, d):
        base = K.base()
        k7 = C.seg(tt, c_7 - c_minsk, c_7 - c_minsk + 1.6)
        lays = [K.line_layer(K.LINE_2015, C.seg(tt, 0.3, 2.3), width=5),
                K.city_layer(["Донецк", "Луганск", "Мариуполь"], C.seg(tt, 1.0, 1.8), side={"Мариуполь": "l"}),
                glow_zone(K.ZONE_2022, k7, fill_a=70)]
        if tt < c_7 - c_minsk:
            lays.append(K.date_tag("2015", C.seg(tt, 0.2, 0.7), sub="Минск · перемирие по линии фронта"))
        else:
            lays.append(K.date_tag("2022", C.seg(tt, c_7 - c_minsk, c_7 - c_minsk + 0.5), sub="самая большая война в Европе после 1945"))
        lays += lines_in([(c_bez - c_minsk, "без войск за ней"), (c_got - c_minsk, "и без гарантов, готовых воевать")], tt, "head", 64, SAFE_X + 20, H * 0.78, "ls", track=0.06, lead=1.2)
        img = C.over(base, *lays).convert("RGB")
        if 0 < k7 < 0.5:
            sh = int(8 * (1 - 2 * k7) * math.sin(t * 90))
            img = img.transform(img.size, Image.AFFINE, (1, 0, sh, 0, 1, 0))
        return C.grain(C.kb(img, C.smoother(tt / d), 0.07, 0.62, 0.5), t, 0.03)

    def raznitsa(tt, d):
        return shkala(tt, d, [1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0],
                      lines_in([(0.2, "разница не в тексте соглашений —"), (c_kto - c_razn, "а в том, кто стоит за линией")], tt, "serif_i", 50, W / 2, 130, "ms")
                      + [word("СПОР О ГАРАНТИЯХ", C.seg(tt, c_spor - c_razn, c_spor - c_razn + 0.5), H * 0.56, 110, color=C.RED)])

    fn, tt, d = shots(t, [(0.0, zamorozka), (c_kor, korea_v), (c_net, korea_map), (c_metr, korea_v2), (c_zhit, zhit),
                          (c_kipr, kipr_v), (c_polv, kipr_map), (c_minsk, minsk), (c_razn, raznitsa)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.4, fo=0.5, grain_k=0.0)


# ═════════════════════════ 28 · Какие земли: карта с полкой B (B20, B3, B6) ═════════════════════════
@scene("28")
def s28(t, dur):
    c_ogov = C.cue("28", "Оговорка обязательна", 5.4)
    t1 = C.cue("28", "Первое Крым", 10.6)
    t2 = C.cue("28", "Второе Старый Донбасс", 24.6)
    t3 = C.cue("28", "Третье Всё что занято", 44.1)
    c_vozvr = C.cue("28", "возвращается Украине", 52.6)
    tm = C.cue("28", "Москва хочет весь Донбасс", 61.7)
    tu = C.cue("28", "Американцы прощупывают", 65.1)
    tk = C.cue("28", "Киев отказывается", 68.3)
    c_plan = C.cue("28", "что план человека", 75.6)
    c_hud = C.cue("28", "сегодня для Украины далеко не худший", 80.3)
    c_esli = C.cue("28", "Если следовать его логике", 84.3)
    ts = C.cue("28", "Остановятся там где стоят", 88.0)
    c_spor = C.cue("28", "получат статус спорных", 92.9) - 1.0
    c_pered = C.cue("28", "В Киеве никто не подпишет", 92.9)
    c_otkl = C.cue("28", "Подпишут слово", 96.0)

    zoom = 0.12 * C.smoother(t / dur)
    base = C.kb(K.base(), 1.0, zoom, 0.70, 0.60)
    lays = [K.zone_layer(K.CRIMEA, C.seg(t, t1, t1 + 1.0), fill_a=100),
            K.zone_layer(K.DONBAS_OLD, C.seg(t, t2, t2 + 1.0), fill_a=85),
            K.zone_layer(K.ZONE_2022, C.seg(t, t3, t3 + 1.2), color=C.WHITE, fill_a=40, hatch=True),
            K.city_layer(["Киев", "Донецк", "Луганск", "Запорожье", "Херсон", "Севастополь"], C.seg(t, 0.5, 1.5), side={"Херсон": "l", "Севастополь": "t"})]
    # B6: кольцо-пульс в момент появления каждой зоны
    for lonlat, t0 in (((34.0, 45.3), t1), ((38.6, 48.2), t2), ((35.4, 47.0), t3)):
        lays.append(glow_ring(*K.UA.xy(*lonlat), C.seg(t, t0, t0 + 1.4), 150))
    lab = C.layer()
    d = ImageDraw.Draw(lab)
    f = C.font("head_r", 30 * SS)
    for txt, lonlat, t0, col in (("ПЕРВОЕ · КРЫМ", (30.6, 45.3), t1, C.RED), ("ВТОРОЕ · СТАРЫЙ ДОНБАСС", (41.2, 48.2), t2, C.RED),
                                 ("ТРЕТЬЕ · ЗАНЯТОЕ ПОСЛЕ 24.02", (35.4, 46.1), t3, C.WHITE)):
        k = C.smoother(C.seg(t, t0 + 0.8, t0 + 1.6))
        if k > 0:
            x, y = K.UA.xy(*lonlat)
            C.tracked(d, x * SS, y * SS, txt, f, col + (int(255 * k),), 0.2, "ms" if "ДОНБАСС" not in txt else "ls")
    lays.append(C.done(lab))
    # B3: требование Москвы — зона-свечение на всей области, затем линии США и Киева
    lays.append(glow_zone(K.OBLAST_DL, C.seg(t, tm, tm + 1.5), fill_a=60))
    lays.append(K.line_layer(K.OBLAST_DL, C.seg(t, tm, tm + 1.5), width=4, head=False))
    lays.append(K.line_layer(K.LINE_NOW, C.seg(t, tu, tu + 1.5), width=4, dash=(14, 9), color=C.WHITE, head=False))
    kk = C.seg(t, tk, tk + 1.2)
    if kk > 0:
        ua = [ft for ft in K.feats() if K.name_of(ft) == "Ukraine"]
        if ua:
            ring = max(K.rings(ua[0]), key=len)
            lays.append(K.line_layer(ring, kk, width=2, glow=False, head=False, color=C.GREY))
    leg = C.layer()
    dl = ImageDraw.Draw(leg)
    fl = C.font("head_r", 28 * SS)
    for i, (txt, t0, col) in enumerate((("МОСКВА — весь Донбасс", tm, C.RED), ("США — часть Донбасса за НАТО", tu, C.WHITE), ("КИЕВ — ни одной уступки", tk, C.GREY))):
        k = C.smoother(C.seg(t, t0 + 0.6, t0 + 1.2))
        if k > 0:
            y = (H - 190 + i * 44) * SS
            dl.rectangle([110 * SS, y - 16 * SS, 150 * SS, y - 12 * SS], fill=col + (int(255 * k),))
            C.tracked(dl, 170 * SS, y, txt.upper(), fl, C.WHITE + (int(255 * k),), 0.14)
    lays.append(C.done(leg))
    ks = C.seg(t, ts, ts + 1.0)
    if ks > 0:
        lays.append(K.line_layer(K.LINE_NOW, 1.0, width=6 + int(3 * math.sin(t * 6) ** 2), head=False))
        lays.append(K.date_tag("ГДЕ СТОЯТ", ks, px=56, sub="остановка по нынешней линии"))
    img = C.over(base, *[C.kb(l, 1.0, zoom, 0.70, 0.60) if l is not None and l.size == (W, H) else l for l in lays]).convert("RGB")
    # B20: заголовок брифинга в начале
    k_t = C.seg(t, 0.3, 0.9) * (1 - C.seg(t, t1 - 0.8, t1 - 0.2))
    top = [title_b20("ЧТЕНИЕ ПЛАНА", "", k_t, y=150), title_b20("НЕ ПОЖЕЛАНИЕ", "И НЕ ПРИЗЫВ", C.seg(t, c_ogov, c_ogov + 0.5) * (1 - C.seg(t, t1 - 0.8, t1 - 0.2)), y=230, px=40)]
    # H3: карта уходит в фон, реплика про «агента Кремля»
    kh = C.seg(t, c_plan, c_plan + 0.6) * (1 - C.seg(t, c_esli, c_esli + 0.6))
    if kh > 0:
        img = Image.blend(img, map_dim(img, 0.4), C.smoother(kh))
        top += [C.alpha(l, kh) for l in lines_in([(c_plan, "план человека, которого называли «агентом Кремля»,"),
                                                   (c_hud, "сегодня для Украины далеко не худший из лежащих на столе")], t, "serif_i", 54, W / 2, H * 0.44, "ms") if l is not None]
    top.append(word("КРЫМ И ДОНБАСС — СТАТУС СПОРНЫХ", C.seg(t, c_spor, c_spor + 0.5) * (1 - C.seg(t, c_pered, c_pered + 0.3)), H * 0.30, 54, "head_l", C.GREY, 0.2, rise=14))
    kp, ko = C.seg(t, c_pered, c_pered + 0.5), C.seg(t, c_otkl, c_otkl + 0.5)
    top += [word("«ПЕРЕДАЁМ»", kp, H * 0.30, 110, x=W * 0.30),
            red_line(C.seg(t, c_otkl - 0.4, c_otkl + 0.3), W * 0.30 - 260, W * 0.30 + 260, H * 0.30 - 36, 8),
            word("«ОТКЛАДЫВАЕМ»", ko, H * 0.30, 110, x=W * 0.70, color=C.RED)]
    img = C.over(img, *top).convert("RGB")
    return C.finish(img, t, dur, fi=0.5, fo=0.6, grain_k=0.03, vig=0.25)


# ═════════════════════════ 29 · Гарантии: Будапешт, затем Корея или Минск (H3) ═════════════════════════
@scene("29")
def s29(t, dur):
    c_nato = C.cue("29", "Киссинджер видел гарантию в", 0.6) + 1.6
    c_moskva = C.cue("29", "Москва видит в НАТО угрозу", 3.4)
    c_kiev = C.cue("29", "А Киев", 3.4) + 2.2
    c_bud = C.cue("29", "что одна гарантия у него уже была", 7.0)
    c_sig = C.cue("29", "подписи Соединённых Штатов", 11.7)
    c_gran = C.cue("29", "границы в обмен на отказ", 16.3)
    c_posle = C.cue("29", "После этого любой документ", 19.1)
    c_choice = C.cue("29", "Выбор на самом деле один", 25.3)

    def garantii(tt, d):
        base = K.base()
        img = map_dim(C.over(base, K.line_layer(K.LINE_NOW, 1.0, width=5, head=False)).convert("RGB"), 0.45)
        img = C.kb(img, C.smoother(tt / d), 0.05, 0.6, 0.5)
        return C.grain(C.over(img, word("ВСЁ УПРЁТСЯ В ГАРАНТИИ", C.seg(tt, 0.1, 0.6), H * 0.46, 120),
                              word("Киссинджер видел гарантию в НАТО", C.seg(tt, c_nato, c_nato + 0.5), H * 0.46 + 70, 44, "serif_i", C.GREY, 0.0, rise=14)).convert("RGB"), t, 0.03)

    def moskva(tt, d):
        fr = vid("putin29", "ap_putin_kissinger.mp4", 4.0, zoom=1.16, cx=0.0, cy=1.0).at(tt)
        img = dark_video(modern(C.kb(fr, tt / d, 0.06, 0.45, 0.4), t, 0.3), 0.5)
        lay = lines_in([(0.1, "Москва видит в НАТО угрозу"), (c_kiev - c_moskva, "Киев помнит: одна гарантия у него уже была")], tt, "serif_i", 56, W / 2, H * 0.42, "ms")
        return flash(C.over(img, *lay, cap("Москва, Кремль", "архив", "AP", C.seg(tt, 0.3, 0.9))), tt, 0.08, 0.5)

    def budapest(tt, d):
        if "cov" not in _c:
            _c["cov"] = C.foto("budapest_1994_1.png")
            _c["sig"] = C.foto("budapest_1994_3.png")
        page = _c["cov"] if tt < c_sig - c_bud else _c["sig"]
        k = C.smoother(C.seg(tt, 0.0, c_sig - c_bud)) if tt < c_sig - c_bud else C.smoother(C.seg(tt, c_sig - c_bud, d))
        pw, ph = page.size
        scale = W / pw * C.lerp(1.0, 1.45, k)
        big = page.resize((int(pw * scale), int(ph * scale)), Image.LANCZOS)
        y_center = C.lerp(ph * 0.25, ph * 0.80, k) * scale
        img = Image.new("RGB", (W, H), (36, 34, 32))
        img.paste(big, (int(W / 2 - big.size[0] / 2), int(H / 2 - y_center)))
        img = C.vignette(img, 0.5)
        lays = [K.date_tag("1994", C.seg(tt, 0.1, 0.6), sub="Будапештский меморандум"),
                cap("Будапештский меморандум", "5 декабря 1994", "Договорная коллекция ООН", C.seg(tt, 0.3, 1.1))]
        lays += lines_in([(c_sig - c_bud, "подписи США, Британии и России"), (c_gran - c_bud, "границы — в обмен на отказ от ядерного оружия")],
                         tt, "head_l", 40, SAFE_X + 20, H * 0.24, "ls", C.WHITE, track=0.14)
        kp = C.seg(tt, c_posle - c_bud, c_posle - c_bud + 0.6)
        if kp > 0:
            img = Image.blend(img, dark_video(img, 0.45), C.smoother(kp))
            lays += lines_in([(c_posle - c_bud, "любой документ без войск за ним"), (c_posle - c_bud + 1.6, "читается в Киеве как продолжение того меморандума")],
                             tt, "serif_i", 54, W / 2, H * 0.56, "ms")
        return C.grain(C.over(img, *lays).convert("RGB"), t, 0.03)

    def vybor(tt, d):
        m, base = world_map("w29", (-10, 150), (5, 68))
        img = map_dim(C.over(base, m.marker((W, H), "Корея", 126.98, 37.95, "1953", k=1.0, px=24, side="left"),
                             m.marker((W, H), "Минск", 27.56, 53.90, "2015", k=1.0, px=24)).convert("RGB"), 0.5)
        k1, k2 = C.seg(tt, 0.2, 0.8), C.seg(tt, 1.0, 1.6)
        return C.grain(C.over(img, word("ВЫБОР ОДИН", C.seg(tt, 0.0, 0.5), 150, 54, "head_l", C.GREY, 0.3, rise=14),
                              word("КОРЕЯ", k1, H * 0.56, 190, x=W * 0.30),
                              word("или", k2, H * 0.56 - 40, 50, "serif_i", C.GREY, 0.0, rise=10),
                              word("МИНСК", k2, H * 0.56, 190, x=W * 0.70, color=C.RED)).convert("RGB"), t, 0.035)

    fn, tt, d = shots(t, [(0.0, garantii), (c_moskva, moskva), (c_bud, budapest), (c_choice, vybor)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.4, fo=0.5, grain_k=0.0)


# ═════════════════════════ 30 · Шесть недель, цена, Лебедь ═════════════════════════
@scene("30")
def s30(t, dur):
    c_amer = C.cue("30", "американцы хотят результата", 2.8)
    c_6 = C.cue("30", "есть срок годности", 7.2)
    c_prorok = C.cue("30", "Он не был пророком", 10.0)
    c_voyny = C.cue("30", "войны заканчиваются не тогда", 12.3)
    c_prava = C.cue("30", "когда одна из сторон права", 14.2)
    c_vyd = C.cue("30", "когда одна из сторон выдохлась", 16.9)
    c_tyazh = C.cue("30", "в его прогнозе не про территории", 20.0)
    c_cena = C.cue("30", "цену у любого из вариантов", 22.4)
    c_plat = C.cue("30", "и платить её станут не те", 25.0)
    c_podp = C.cue("30", "кто ставит подписи", 26.7)
    c_lebed = C.cue("30", "Как сказал генерал Лебедь", 28.3)
    c_deti = C.cue("30", "детей чиновников", 30.6)
    c_den = C.cue("30", "и война закончится в тот же день", 31.9)
    c_chast = C.cue("30", "та часть прогноза", 33.9)
    c_nemog = C.cue("30", "которую Киссинджер не мог произнести", 35.4)

    def umerov(tt, d):
        fr = vid("abu30", "abu_dhabi_2026_11.mp4", 14.0, zoom=1.12).at(tt)
        img = modern(C.kb(fr, tt / d, 0.05, 0.5, 0.45), t, 0.3)
        lay = lines_in([(c_amer, "результат — до конца года")], tt, "head", 72, W / 2, H * 0.80, "ms", track=0.06)
        return C.over(img, *lay, cap("Абу-Даби", "ноябрь 2026 · делегации России, Украины и США", "пул", C.seg(tt, 0.3, 1.0), y=140))

    def nedeli(tt, d):
        fr = vid("abu30", "abu_dhabi_2026_11.mp4", 14.0, zoom=1.12).at(tt + c_6)
        img = dark_video(modern(C.kb(fr, 0.5, 0.05, 0.5, 0.45), t, 0.3), 0.35)
        return flash(C.over(img, C.big_number("6 НЕДЕЛЬ", "срок годности прогноза", None, C.seg(tt, 0.0, 1.4), cx=W / 2, cy=H * 0.46, px=230, count_from=0)), tt, 0.08, 0.5)

    def prorok(tt, d):
        fr = vid("k100g", "kissinger_100_2023.mp4", 40.0).at(tt)
        img = dark_video(C.film_look(C.kb(fr.convert("L").convert("RGB"), tt / d, 0.05, 0.5, 0.4), t, 0.35, scratches=False), 0.55)
        lay = [word("НЕ ПРОРОК", C.seg(tt, 0.1, 0.6), 150, 54, "head_l", C.GREY, 0.3, rise=14)]
        lay += lines_in([(c_voyny - c_prorok, "войны заканчиваются не тогда,"), (c_prava - c_prorok, "когда одна из сторон права,"),
                         (c_vyd - c_prorok, "а тогда, когда одна из сторон выдохлась")], tt, "serif_i", 54, W / 2, H * 0.42, "ms")
        lay.append(cap("Генри Киссинджер", "май 2023", "CBS", C.seg(tt, 0.3, 0.9)))
        return flash(C.over(img, *lay), tt, 0.08, 0.5)

    def cena(tt, d):
        if "sig30" not in _c:
            _c["sig30"] = C.cover(C.foto("budapest_1994_3.png"), (W, H), 0.5, 0.85)
        img = dark_video(C.kb(_c["sig30"], tt / d, 0.08, 0.5, 0.8), 0.45)
        kc = C.seg(tt, c_cena - c_tyazh, c_cena - c_tyazh + 0.5)
        lay = [word("САМОЕ ТЯЖЁЛОЕ — НЕ ПРО ТЕРРИТОРИИ", C.seg(tt, 0.1, 0.6) * (1 - kc), H * 0.46, 64, "head_l", C.GREY, 0.2),
               word("ЦЕНА", kc, H * 0.46, 210, color=C.RED)]
        lay += lines_in([(c_plat - c_tyazh, "платить её станут не те,"), (c_podp - c_tyazh, "кто ставит подписи")], tt, "serif_i", 54, W / 2, H * 0.66, "ms")
        return C.grain(C.over(img, *lay).convert("RGB"), t, 0.03)

    def lebed(tt, d):
        img = dark_video(C.paper(W, H, seed=23, tone=(60, 56, 50)), 0.7)
        img = C.kb(img, tt / d, 0.04, 0.5, 0.5)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        k = C.smoother(C.seg(tt, 0.1, 0.8))
        a = int(255 * k)
        dd.text(((W * 0.14) * SS, (H * 0.38) * SS), "«", font=C.font("serif_b", 190 * SS), fill=C.GREY3 + (a,), anchor="ls")
        f = C.font("serif", 52 * SS)
        for i, (tl, ln) in enumerate(((0.1, "Соберите две роты из детей чиновников —"), (c_den - c_lebed, "и война закончится в тот же день."))):
            kk = C.smoother(C.seg(tt, tl, tl + 0.6))
            dd.text(((W * 0.17) * SS, (H * 0.44 + i * 72) * SS), ln, font=f, fill=C.WHITE + (int(255 * kk),), anchor="ls")
        dd.rectangle([(W * 0.17) * SS, (H * 0.44 + 160) * SS, (W * 0.17 + 70 * k) * SS, (H * 0.44 + 163) * SS], fill=C.RED + (a,))
        C.tracked(dd, (W * 0.17) * SS, (H * 0.44 + 212) * SS, "АЛЕКСАНДР ЛЕБЕДЬ · ГЕНЕРАЛ", C.font("head_r", 34 * SS), C.WHITE + (a,), 0.16)
        return C.grain(C.over(img, C.done(lay)).convert("RGB"), t, 0.035)

    def nemog(tt, d):
        img = C.kb(foto_bw("kissinger_portrait_late.jpg"), tt / d, 0.06, 0.5, 0.28)
        img = dark_video(C.film_look(img, t, 0.35, scratches=False), 0.5)
        return C.over(img, word("ТА ЧАСТЬ ПРОГНОЗА, КОТОРУЮ ОН НЕ МОГ ПРОИЗНЕСТИ", C.seg(tt, c_nemog - c_chast - 0.8, c_nemog - c_chast - 0.3), H * 0.84, 46, "head_l", C.GREY, 0.2, rise=14))

    fn, tt, d = shots(t, [(0.0, umerov), (c_6, nedeli), (c_prorok, prorok), (c_tyazh, cena), (c_lebed, lebed), (c_chast, nemog)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.4, fo=0.8, grain_k=0.0)


# ═════════════════════════ 31 · Вопрос к вам: три эпохи, титры ═════════════════════════
@scene("31")
def s31(t, dur):
    c_ost = C.cue("31", "Остановка по нынешней линии", 1.7)
    c_bez = C.cue("31", "без признания и без мирного договора", 3.6)
    c_mun = C.cue("31", "Это Мюнхен", 3.6) + 3.0
    c_minsk = C.cue("31", "Минск пятнадцатого", 8.2)
    c_kor = c_minsk + 1.5
    c_odnim = C.cue("31", "Одним словом в комментариях", 11.3)
    c_posch = C.cue("31", "я посчитаю", 12.9)
    t_end = c_posch + 2.0

    def vopros(tt, d):
        base = K.base()
        lays = [K.line_layer(K.LINE_NOW, 1.0, width=6 + int(3 * math.sin(t * 6) ** 2), head=False),
                K.city_layer(["Киев", "Донецк", "Херсон", "Севастополь"], C.seg(tt, 0.3, 1.0), side={"Херсон": "l", "Севастополь": "t"})]
        img = C.kb(C.over(base, *lays).convert("RGB"), C.smoother(tt / d), 0.07, 0.62, 0.52)
        lay = [word("ВОПРОС К ВАМ", C.seg(tt, 0.1, 0.6), 160, 72, "head_l", C.GREY, 0.3, rise=16)]
        lay += lines_in([(c_ost, "остановка по нынешней линии —"), (c_bez, "без признания и без мирного договора")], tt, "serif_i", 56, W / 2, H * 0.78, "ms")
        return C.grain(C.over(img, *lay).convert("RGB"), t, 0.03)

    def munich(tt, d):
        fr = vid("mun31", "munich_1938_pathe.mp4", 2.0, zoom=1.3, cx=0.0, cy=0.7).at(tt)
        img = chronicle(C.kb(fr, tt / d, 0.08, 0.5, 0.4), t, 0.9)
        return flash(C.over(img, word("МЮНХЕН · 1938", C.seg(tt, 0.0, 0.4), H * 0.80, 130),
                            cap("Мюнхен", "30 сентября 1938", "British Pathé", C.seg(tt, 0.2, 0.7), y=140)), tt, 0.1, 0.6)

    def minsk(tt, d):
        base = K.base()
        img = C.kb(C.over(base, K.line_layer(K.LINE_2015, C.seg(tt, 0.0, 0.9), width=5)).convert("RGB"), C.smoother(tt / d), 0.08, 0.66, 0.5)
        return flash(C.grain(C.over(img, word("МИНСК · 2015", C.seg(tt, 0.0, 0.4), H * 0.80, 130)).convert("RGB"), t, 0.03), tt, 0.1, 0.6)

    def korea(tt, d):
        fr = vid("pan31", "panmunjom_1953.mp4", 6.0).at(tt)
        img = chronicle(C.kb(fr, tt / d, 0.08, 0.5, 0.4), t, 0.8)
        return flash(C.over(img, word("КОРЕЯ · 1953", C.seg(tt, 0.0, 0.4), H * 0.80, 130),
                            cap("Пханмунджом", "27 июля 1953", "архив США", C.seg(tt, 0.2, 0.7), y=140)), tt, 0.1, 0.6)

    def slovo(tt, d):
        img = Image.new("RGB", (W, H), C.BG)
        lays = []
        for i, (s, x) in enumerate((("МЮНХЕН", W * 0.22), ("МИНСК", W * 0.50), ("КОРЕЯ", W * 0.78))):
            lays.append(word(s, C.seg(tt, 0.1 + i * 0.25, 0.5 + i * 0.25), H * 0.50, 120, x=x, maxw=W * 0.26))
        lays.append(word("одним словом — в комментариях, я посчитаю", C.seg(tt, c_posch - c_odnim, c_posch - c_odnim + 0.5), H * 0.50 + 80, 44, "serif_i", C.GREY, 0.0, rise=14))
        return C.vignette(C.grain(C.over(img, *lays).convert("RGB"), t, 0.035), 0.4)

    def titry(tt, d):
        img = Image.new("RGB", (W, H), (5, 5, 6))
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        k = C.smoother(C.seg(tt, 0.3, 1.2))
        a = int(255 * k)
        C.tracked(dd, W / 2 * SS, (H / 2 - 40) * SS, "ПОСЛЕДНИЙ ПРОГНОЗ КИССИНДЖЕРА", C.font("head", 64 * SS), C.WHITE + (a,), 0.16, "ms")
        dd.rectangle([(W / 2 - 40) * SS, (H / 2 - 8) * SS, (W / 2 + 40) * SS, (H / 2 - 5) * SS], fill=C.RED + (a,))
        lines = ["Архив: NARA · British Pathé · AP Archive · Всемирный экономический форум · CBS",
                 "Офис президента Украины · kremlin.ru · Европейский союз · ООН · Wikimedia Commons",
                 "Карты условны: линии показаны приблизительно"]
        f = C.font("head_l", 26 * SS)
        for i, ln in enumerate(lines):
            C.tracked(dd, W / 2 * SS, (H / 2 + 50 + i * 40) * SS, ln.upper(), f, C.GREY + (a,), 0.18, "ms")
        img = C.over(img, C.done(lay)).convert("RGB")
        return C.in_out_fade(C.grain(img, t, 0.03), tt, d, 0.0, 1.5)

    fn, tt, d = shots(t, [(0.0, vopros), (c_mun, munich), (c_minsk, minsk), (c_kor, korea), (c_odnim, slovo), (t_end, titry)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.4, fo=0.0, grain_k=0.0)
