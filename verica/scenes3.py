#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Фильм «Верица» — третий кусок: Дрезден → конец блока 2, сцены 27-39 (≈122 с).

Правила те же: план ≤5 с (карта, врезка оригинала и отрисовка — исключение), движение
с первого кадра, текст в полях 96/54, подписи честные, стиль мрачнее Киссинджера.
Люди в кадре — только из видео-врезок и утверждённых им фото Бундесархива (малые,
в рамке слайда). Письмо 1987 года — РЕКОНСТРУКЦИЯ по публикациям, так и подписано.

Новые эффекты своей разработки (fx3, низ файла):
  proektor      — слайд-проектор: фото в рамке слайда, щелчок, кадр садится с перелётом,
                  пыль в луче, мерцание лампы, тёплый тон
  obuglivanie   — бумага обугливается с угла: тлеющая кромка, чернота, пепел
  rukopis       — рукописная пометка: строка пишется пером, перо-точка бежит впереди
  signal        — сигнал без ответа: пунктир Дрезден→Москва, бегущий импульс, Москва
                  не отвечает — линия гаснет
  plan_kab      — план особняка: шесть кабинетов загораются по одному, рядом — блок
                  Штази, схема условная
  liniya_zhizni — линия жизни: красный бегунок идёт по шкале, вехи-вопросы, шкала
                  уходит за край
  kartoteka     — картотечный ящик: выезжает, карточки с замазанными именами
                  перелистываются, ящик задвигается
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import fx
import karta as K
import scenes as S
import scenes2 as S2
from core import W, H, SS
from scenes import (scene, rel, shots, flash, word, red_line, zoom_at, grade, vid, verica,
                    CAP_V, CAP_B, page_view, to_frame, page_dark, dark_bg, LINE_PUTIN, LINE_DAUGHTERS,
                    card_tex, pin_at, thread, board_bg, CARD_POS, CARD_W, CARD_H, fit_px)
from scenes2 import EUROPE, label, doc_view, card_extra, EXTRA

SAFE_X, SAFE_Y = 96, 54

# ── подписи (честные: место · дата · источник)
CAP_HAUS06 = ("Ангеликаштрассе, 4 · Дрезден", "фото 2006", "Jörg Blobelt · Wikimedia Commons · CC BY-SA 4.0")
CAP_HAUS12 = ("Ангеликаштрассе, 4 · Дрезден", "фото 2012", "Brücke-Osteuropa · Wikimedia Commons · CC0")
CAP_AUSW = ("удостоверение МГБ ГДР", "Wikimedia Commons", "общественное достояние")
CAP_PUTIN = ("фильм «Путин»", "А. Кондрашов · 2018", "оригинальный звук")
CAP_PISMO = ("письмо 1987 года · реконструкция по публикациям", "подлинника в кадре нет", "BStU · Der Spiegel")
BA = {  # фото Бундесархива: файл → (дата, подпись источника)
    "ba_1112.jpg": ("12.11.1989", "Bundesarchiv, Bild 183-1989-1112-019 · Hiekel · CC BY-SA 3.0"),
    "ba_1203.jpg": ("03.12.1989", "Bundesarchiv, Bild 183-1989-1203-009 · Haessler · CC BY-SA 3.0"),
    "ba_1204.jpg": ("04.12.1989", "Bundesarchiv, Bild 183-1989-1204-037 · Haessler · CC BY-SA 3.0"),
    "ba_1211.jpg": ("11.12.1989", "Bundesarchiv, Bild 183-1989-1211-028 · Haessler · CC BY-SA 3.0"),
}

# ГДР — границы ПРИБЛИЗИТЕЛЬНЫЕ (наглядность), так и подписано
GDR = [(10.9, 54.0), (11.5, 54.1), (12.5, 54.45), (13.5, 54.6), (14.2, 53.9), (14.3, 53.3), (14.65, 52.9),
       (14.6, 52.4), (14.75, 52.0), (14.65, 51.6), (15.0, 51.3), (14.8, 50.9), (14.3, 51.0), (13.5, 50.6),
       (12.9, 50.4), (12.3, 50.2), (11.9, 50.4), (11.5, 50.4), (11.3, 50.5), (10.7, 50.3), (10.0, 50.5),
       (10.1, 50.9), (9.7, 51.3), (10.2, 51.6), (10.6, 51.6), (10.7, 52.0), (10.95, 52.3), (10.9, 52.8),
       (11.1, 53.1), (10.75, 53.4)]
GER = K.Okno(lon=(4.0, 24.0), lat=(46.5, 56.0))
DRESDEN = (13.74, 51.05)
MOSKVA = (37.62, 55.75)

_ph = {}


def foto(name):
    if name not in _ph:
        _ph[name] = Image.open(C.apath(name)).convert("RGB")
    return _ph[name]


def haus_dark(name, t, cx=0.5, cy=0.45, zoom=0.05, film=0.55):
    """дом в прошлом: тёмный строй, плёнка, холод"""
    img = C.kb(foto(name), t, zoom, cx, cy)
    img = grade(img, 1.0)
    img = C.fade(img, 0.72)
    return C.film_look(img, t, film, scratches=False)


def lamp_bg(seed=5):
    return dark_bg(seed)


# ═════════════════════════ 27 · Дрезден, ГДР, 1985 ═════════════════════════
@scene("27")
def s27(t, dur):
    c_dr = rel("27", 197.97)
    c_vost = rel("27", 198.75)
    c_god = rel("27", 200.28)

    def a_map(tt, d):
        base = K.base(GER, hot="Germany")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.7, 0, 255).astype(np.uint8), "RGB")
        x, y = GER.xy(*DRESDEN)
        k_gdr = C.seg(tt, 0.3, 1.6)
        zone = K.zone_layer(GDR, k_gdr, okno=GER, color=C.RED, fill_a=46, outline=True, hatch=True)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        for j in range(3):
            ph = (tt * 0.8 + j * 0.33) % 1.0
            r = (10 + 120 * ph) * SS
            dd.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], outline=C.RED + (int(200 * (1 - ph)),), width=3 * SS)
        gx, gy = GER.xy(11.9, 51.85)
        img = C.over(base, zone, C.done(lay),
                     K.city_layer(["Дрезден", "Берлин"], C.seg(tt, 0.2, 0.6), okno=GER, px=32),
                     C.text_layer(["ГДР"], "head", 86, C.WHITE, gx, gy, "ms", 0.3, a=C.seg(tt, 1.0, 1.5)),
                     label("ГРАНИЦЫ ПРИБЛИЗИТЕЛЬНЫЕ · КАРТА УСЛОВНАЯ", C.seg(tt, 1.0, 1.5), H - 70, 24),
                     word("ДРЕЗДЕН", C.seg(tt, c_dr, c_dr + 0.5), H * 0.74, 190, "head", C.WHITE, 0.12, rise=50),
                     word("ВОСТОЧНАЯ ГЕРМАНИЯ", C.seg(tt, c_vost, c_vost + 0.5), H * 0.74 + 72, 56, "head_l", C.GREY, 0.3, rise=20))
        z = 1.0 + 0.5 * C.smoother(C.seg(tt, 0.0, d))
        return C.grain(zoom_at(img.convert("RGB"), z, x, y), t, 0.03)

    def b_1985(tt, d):
        img = haus_dark("haus_2006.jpg", tt + 0.4, 0.5, 0.4, 0.06, 0.6)
        img = fx.fonar(img, W * 0.45, H * 0.4, 820, 520, 0.22, 0.04, t)
        return flash(C.over(img, K.date_tag("1985", C.seg(tt, 0.05, 0.5), sub="тридцать лет назад"),
                            C.caption(*CAP_HAUS06, k=C.seg(tt, 0.3, 0.8))).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_map), (c_god, b_1985)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 28 · официально / на деле ═════════════════════════
@scene("28")
def s28(t, dur):
    c_nadele = rel("28", 205.81)

    def a(tt, d):
        img = haus_dark("haus_2006.jpg", tt + 2.0, 0.42, 0.55, 0.07, 0.6)
        # фонарь ищет: от окон к двери
        k = C.smoother(C.seg(tt, 0.4, 3.2))
        lx = C.lerp(W * 0.62, W * 0.40, k)
        ly = C.lerp(H * 0.36, H * 0.62, k)
        img = fx.fonar(img, lx, ly, 560, 380, 0.16, 0.05, t)
        k1 = C.seg(tt, 0.1, 1.6)
        t1 = "ОФИЦИАЛЬНО · ДОМ СОВЕТСКО-ГЕРМАНСКОЙ ДРУЖБЫ"
        px1 = fit_px(t1, "head_l", 44, W - 2 * SAFE_X, 0.14)
        lay1 = fx.typed(t1, k1, "head_l", px1, C.GREY, SAFE_X, 170, 0.14, cur=k1 < 1, t=tt)
        d_ = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        tw = C.text_w(d_, t1, C.font("head_l", px1 * SS), 0.14) / SS
        ks = C.seg(tt, c_nadele, c_nadele + 0.35)
        strike = red_line(ks, SAFE_X - 6, SAFE_X + tw + 6, 170 - px1 * 0.36, 6)
        t2 = "НА ДЕЛЕ · ОФИЦЕР КГБ"
        lay2 = word(t2, C.seg(tt, c_nadele + 0.2, c_nadele + 0.6), 300, 92, "head", C.WHITE, 0.1, x=SAFE_X, anchor="ls", rise=30)
        out = C.over(img, lay1, strike, lay2, C.caption(*CAP_HAUS06, k=1.0)).convert("RGB")
        if ks > 0:
            out = flash(out, tt - c_nadele, 0.08, 0.35)
        return out

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.3)


# ═════════════════════════ 29 · особняк, шесть кабинетов, Штази рядом ═════════════════════════
@scene("29")
def s29(t, dur):
    c_4 = rel("29", 209.65)
    c_6 = rel("29", 210.41)
    c_stasi = rel("29", 211.54)
    c_nem = rel("29", 213.56)

    def a_haus(tt, d):
        img = haus_dark("haus_2012_1.jpg", tt, 0.35, 0.5, 0.08, 0.45)
        img = fx.fonar(img, W * 0.42, H * 0.45, 900, 600, 0.3, 0.03, t)
        k4 = C.seg(tt, c_4, c_4 + 0.6)
        return flash(C.over(img, C.big_number("4", None, None, k4, W * 0.78, H * 0.42, 300, C.RED, rings=True, count_from=0),
                            label("АНГЕЛИКАШТРАССЕ", C.seg(tt, 0.2, 0.6), H * 0.42 + 300 * 0.78, 40, C.WHITE, x=W * 0.78),
                            C.caption(*CAP_HAUS12, k=1.0)).convert("RGB"), tt, 0.08, 0.4)

    def b_plan(tt, d):
        img = lamp_bg(21)
        k_rooms = C.seg(tt, 0.05, 1.1)
        k_st = C.seg(tt, c_stasi - c_6, c_stasi - c_6 + 0.9)
        lay = plan_kab(k_rooms, k_st, tt)
        return C.over(img, lay,
                      label("ШЕСТЬ КАБИНЕТОВ", C.seg(tt, 0.0, 0.4), 130, 46, C.WHITE),
                      label("РЯДОМ · УПРАВЛЕНИЕ ШТАЗИ", C.seg(tt, c_stasi - c_6, c_stasi - c_6 + 0.4), H - 150, 40, C.WHITE),
                      label("СХЕМА УСЛОВНАЯ · РАССТОЯНИЯ НЕ В МАСШТАБЕ", C.seg(tt, 0.2, 0.6), H - 70, 24)).convert("RGB")

    def c_ausweis(tt, d):
        sc = 1.35 + 0.06 * tt
        img, geo = doc_view("stasi_ausweis.jpg", 150, sc, 1000)
        img = fx.fonar(img, W * 0.62, H * 0.3, 760, 300, 0.12, 0.04, t)
        img = page_dark(img, t)
        return flash(C.over(img, label("НЕМЕЦКАЯ ТАЙНАЯ ПОЛИЦИЯ", C.seg(tt, 0.1, 0.5), H - 150, 40, C.WHITE),
                            C.caption(*CAP_AUSW, k=C.seg(tt, 0.2, 0.6))).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_haus), (c_6, b_plan), (c_nem, c_ausweis)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.25)


# ═════════════════════════ 30 · следы в архивах, пропуск ═════════════════════════
@scene("30")
def s30(t, dur):
    c_prop = rel("30", 217.74)
    c_vyd = rel("30", 219.42)

    def a_kart(tt, d):
        img = lamp_bg(22)
        lx, ly = W * 0.5, -200
        img = fx.lampa(img, lx, ly, 1300, 0.25)
        lay = kartoteka(C.seg(tt, 0.0, 0.9), C.seg(tt, 0.9, 2.6), 1.0, tt, bars=False)
        return C.over(img, lay, label("НЕМЕЦКИЕ АРХИВЫ · СЛЕДЫ", C.seg(tt, 0.3, 0.7), 130, 46, C.WHITE),
                      label("АРХИВ ШТАЗИ · ПО ПУБЛИКАЦИЯМ", C.seg(tt, 0.5, 0.9), H - 70, 24)).convert("RGB")

    def b_ausweis(tt, d):
        img = lamp_bg(23)
        k_in = C.out_cubic(C.seg(tt, 0.0, 0.45))
        doc = foto("stasi_ausweis.jpg")
        dw = 1150
        dh = int(doc.size[1] * dw / doc.size[0])
        doc = doc.resize((dw, dh), Image.LANCZOS)
        z = 1.0 + 0.25 * C.smoother(C.seg(tt, 0.6, d))
        doc = doc.resize((int(dw * z), int(dh * z)), Image.LANCZOS)
        cx = W / 2 - (doc.size[0] / 2) * 0.25 * (z - 1) / 0.25 if z > 1 else W / 2
        x0 = int(W / 2 - doc.size[0] / 2 - 160 * (z - 1))
        y0 = int(H / 2 - doc.size[1] / 2 + (1 - k_in) * (H * 0.8) - 120 * (z - 1))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh, sx, sy = fx.shadow_of(doc.size, W / 2, -300, x0 + doc.size[0] / 2, y0 + doc.size[1] / 2, blur=26, a=190)
        lay.alpha_composite(sh, (sx, sy))
        lay.alpha_composite(doc.convert("RGBA"), (x0, y0))
        img = C.over(img, lay).convert("RGB")
        img = fx.fonar(img, W * 0.5 + 120 * C.smoother(C.seg(tt, 0.6, d)), H * 0.48, 980, 640, 0.10, 0.04, t)
        img = C.grain(img, t, 0.03)
        return C.over(img, label("ПРОПУСК В ЗДАНИЕ ШТАЗИ", C.seg(tt, 0.3, 0.7), 110, 44, C.WHITE),
                      C.caption(*CAP_AUSW, k=C.seg(tt, 0.4, 0.8))).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_kart), (c_prop, b_ausweis)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 31 · письмо 1987 года ═════════════════════════
PISMO_LINES = [
    ("Окружное управление МГБ · Дрезден", "head_l", 36),
    ("", "serif", 26),
    ("Просьба оказать содействие", "serif", 50),
    ("в вербовке гражданина,", "serif", 50),
    ("проживающего рядом", "serif", 50),
    ("с партийной гостиницей.", "serif", 50),
    ("", "serif", 26),
    ("Исполнитель:  товарищ Путин", "serif_b", 54),
]
_pis = {}


def pismo(k_type, k_note1=0.0, k_note2=0.0):
    """лист письма (реконструкция): машинопись по буквам, две рукописные пометки"""
    key = (round(k_type, 3), round(k_note1, 3), round(k_note2, 3))
    if key in _pis:
        return _pis[key]
    pw, ph = 1240, 1500
    im = C.paper(pw, ph, seed=81, tone=(192, 183, 164), dark=0.0).convert("RGBA")
    d = ImageDraw.Draw(im)
    total = sum(len(l[0]) for l in PISMO_LINES)
    budget = int(total * C.clamp(k_type))
    y = 200
    for text, kind, px in PISMO_LINES:
        n = min(len(text), budget)
        budget -= n
        if n > 0:
            d.text((120, y), text[:n], font=C.font(kind, px), fill=C.INK + (255,), anchor="ls")
        y += px * 1.75 if text else px
    d.line([(120, 150), (pw - 120, 150)], fill=(120, 110, 95, 255), width=2)
    d.text((pw - 120, 120), "1987", font=C.font("head_l", 34), fill=(90, 80, 70, 255), anchor="rs")
    if k_note1 > 0:
        im = Image.alpha_composite(im, rukopis("Вернуть невыполненным", k_note1, 150, 880, 66, (pw, ph), angle=-4))
    if k_note2 > 0:
        im = Image.alpha_composite(im, rukopis("уничтожить", k_note2, 520, 1130, 110, (pw, ph), angle=-7, heavy=True))
    _pis[key] = im
    return im


def pismo_frame(k_type, k_n1, k_n2, zoom, cx, cy, t, lx=None, ly=None):
    """письмо на тёмном столе под фонарём; zoom и центр (cx, cy) — в пикселях листа"""
    sheet = pismo(k_type, k_n1, k_n2)
    img = lamp_bg(24).convert("RGBA")
    base_w = 1240
    s = (H * 0.92 / 1500) * zoom
    sw, sh = int(1240 * s), int(1500 * s)
    small = sheet.resize((sw, sh), Image.LANCZOS)
    x0 = int(W / 2 - cx * s)
    y0 = int(H / 2 - cy * s)
    shd, sx, sy = fx.shadow_of((sw, sh), W / 2, -300, x0 + sw / 2, y0 + sh / 2, blur=24, a=180)
    img.alpha_composite(shd, (sx, sy))
    img.alpha_composite(small, (x0, y0))
    img = img.convert("RGB")
    if lx is None:
        lx, ly = W * 0.5, H * 0.5
    img = fx.fonar(img, lx, ly, 760, 480, 0.10, 0.045, t)
    return C.grain(img, t, 0.03)


@scene("31")
def s31(t, dur):
    c_pros = rel("31", 223.42)
    c_fam = rel("31", 227.65)
    c_pom = rel("31", 229.79)
    c_vern = rel("31", 230.88)
    c_un = rel("31", 232.45)

    def a_type(tt, d):
        k = C.seg(tt, 0.2, 5.6)
        # фонарь идёт за строкой: по доле напечатанного
        ly = C.lerp(H * 0.24, H * 0.66, C.smoother(k))
        img = pismo_frame(k, 0, 0, 1.45, 620, 520, t, W * 0.5, ly)
        return C.over(img, label("ПИСЬМО · ПРОСЬБА ЗАВЕРБОВАТЬ", C.seg(tt, c_pros, c_pros + 0.4), H - 150, 40, C.WHITE),
                      C.caption(*CAP_PISMO, k=1.0)).convert("RGB")

    def b_fam(tt, d):
        z = 1.9 + 0.3 * C.smoother(C.seg(tt, 0.0, d))
        img = pismo_frame(1.0, 0, 0, z, 600, 720, t, W * 0.52, H * 0.5)
        return flash(C.over(img, label("НА ПИСЬМЕ ФАМИЛИЯ", C.seg(tt, 0.1, 0.5), H - 150, 40, C.WHITE),
                            C.caption(*CAP_PISMO, k=1.0)).convert("RGB"), tt, 0.06, 0.3)

    def c_notes(tt, d):
        k1 = C.seg(tt, c_vern - c_pom, c_vern - c_pom + 1.3)
        k2 = C.seg(tt, c_un - c_pom, c_un - c_pom + 1.0)
        zoom = 1.35 + 0.75 * C.smoother(C.seg(tt, c_un - c_pom + 0.3, c_un - c_pom + 2.2))
        cx = C.lerp(620, 800, C.smoother(C.seg(tt, c_un - c_pom + 0.3, c_un - c_pom + 2.2)))
        cy = C.lerp(900, 1080, C.smoother(C.seg(tt, c_un - c_pom + 0.3, c_un - c_pom + 2.2)))
        lx = C.lerp(W * 0.4, W * 0.55, C.smoother(C.seg(tt, 0.0, 1.0)))
        img = pismo_frame(1.0, k1, k2, zoom, cx, cy, t, lx, H * 0.5)
        return C.over(img, label("ДВЕ ПОМЕТКИ", C.seg(tt, 0.1, 0.5) * (1 - C.seg(tt, c_un - c_pom + 0.5, c_un - c_pom + 1.0)), H - 150, 40, C.WHITE),
                      C.caption(*CAP_PISMO, k=1.0)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_type), (c_fam, b_fam), (c_pom, c_notes)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 32 · «уничтожить» крупно · бумаги сожгли ═════════════════════════
@scene("32")
def s32(t, dur):
    c_chem = rel("32", 235.55)
    c_nikto = rel("32", 237.34)
    c_bum = rel("32", 238.76)
    c_sozh = rel("32", 240.02)

    def a_hold(tt, d):
        zoom = 2.1 + 0.12 * tt
        img = pismo_frame(1.0, 1, 1, zoom, 800, 1080, t, W * 0.55, H * 0.5)
        return C.over(img, C.caption(*CAP_PISMO, k=1.0)).convert("RGB")

    def b_nikto(tt, d):
        z = 1.15 + 0.04 * tt
        img = pismo_frame(1.0, 1, 1, z, 620, 700, t, W * 0.5, H * 0.5 + 40 * math.sin(tt * 0.7))
        return flash(C.over(img, label("ЧЕМ ОН ЗАНИМАЛСЯ · НЕ ЗНАЕТ НИКТО", C.seg(tt, c_nikto - c_chem, c_nikto - c_chem + 0.4), 92, 40, C.WHITE),
                            C.caption(*CAP_PISMO, k=1.0)).convert("RGB"), tt, 0.06, 0.3)

    def c_burn(tt, d):
        img = pismo_frame(1.0, 1, 1, 1.15, 620, 700, t, W * 0.5, H * 0.5)
        k = C.seg(tt, 0.0, d - 0.1)
        k = 0.15 * C.smoother(C.seg(tt, 0.0, c_sozh - c_bum)) + 0.85 * C.smoother(C.seg(tt, c_sozh - c_bum, d - 0.1))
        img = obuglivanie(img, k, t)
        return C.over(img, label("ВЫВЕЗЛИ ИЛИ СОЖГЛИ", C.seg(tt, 0.1, 0.5) * (1 - C.seg(k, 0.75, 0.95)), 92, 40, C.WHITE)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_hold), (c_chem, b_nikto), (c_bum, c_burn)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 33 · 5 декабря 1989: слайды, штурм, картотека ═════════════════════════
@scene("33")
def s33(t, dur):
    c_mes = rel("33", 244.17)
    c_tolpa = rel("33", 246.63)
    c_idet = rel("33", 249.14)
    c_kgb = rel("33", 250.09)
    c_vnutri = rel("33", 251.32)
    c_imena = rel("33", 252.77)

    def slide(name, tt, title, k_title, zoom=1.0, cx=0.5, cy=0.5, sub=None):
        date, src = BA[name]
        img = proektor(foto(name), tt, t, zoom, cx, cy)
        return C.over(img, label(title, k_title, 92, 40, C.WHITE),
                      C.caption("Дрезден", date, src, k=C.seg(tt, 0.3, 0.7))).convert("RGB")

    def a_s1(tt, d):
        img = slide("ba_1112.jpg", tt, "ПЯТОЕ ДЕКАБРЯ", C.seg(tt, 1.0, 1.4), 1.0 + 0.04 * tt)
        return C.over(img, K.date_tag("1989", C.seg(tt, 1.0, 1.5), sub="месяц после падения стены")).convert("RGB")

    def b_s2(tt, d):
        return slide("ba_1203.jpg", tt, "МЕСЯЦ НАЗАД ПАЛА БЕРЛИНСКАЯ СТЕНА", C.seg(tt, 0.3, 0.7), 1.0 + 0.05 * tt, 0.5, 0.5)

    def c_s3(tt, d):
        return slide("ba_1204.jpg", tt, "ТОЛПА БЕРЁТ ШТУРМОМ ЗДАНИЕ ШТАЗИ", C.seg(tt, 0.3, 0.7), 1.0 + 0.09 * tt, 0.5, 0.55)

    def d_plan(tt, d):
        img = lamp_bg(25)
        k_arrow = C.seg(tt, 0.1, c_kgb - c_idet + 0.5)
        lay = plan_kab(1.0, 1.0, tt + 4.0, arrow=k_arrow)
        return flash(C.over(img, lay, label("И ИДЁТ ДАЛЬШЕ", C.seg(tt, 0.0, 0.3), 130, 46, C.WHITE),
                            label("К ОСОБНЯКУ КГБ", C.seg(tt, c_kgb - c_idet, c_kgb - c_idet + 0.4), H - 150, 40, C.WHITE),
                            label("СХЕМА УСЛОВНАЯ", 1.0, H - 70, 24)).convert("RGB"), tt, 0.08, 0.4)

    def e_kart(tt, d):
        img = fx.lampa(lamp_bg(22), W * 0.5, -200, 1300, 0.25)
        lay = kartoteka(1.0, C.seg(tt, 0.0, d), 1.0, tt + 3.0, bars=True, pulse=C.seg(tt, c_imena - c_vnutri, c_imena - c_vnutri + 0.5))
        return C.over(img, lay, label("ВНУТРИ · ДЕЛА АГЕНТОВ", C.seg(tt, 0.1, 0.5), 130, 46, C.WHITE),
                      word("ИМЕНА", C.seg(tt, c_imena - c_vnutri, c_imena - c_vnutri + 0.5), H - 120, 90, "head", C.WHITE, 0.2, rise=30)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_s1), (c_mes, b_s2), (c_tolpa, c_s3), (c_idet, d_plan), (c_vnutri, e_kart)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 34 · с его собственных слов ═════════════════════════
def haus_night(name, tt, t, cx=0.42, cy=0.5, zoom=0.05, window=(0.56, 0.47)):
    """особняк ночью: синяя тьма, одно тёплое окно"""
    img = C.kb(foto(name), tt, zoom, cx, cy)
    a = np.asarray(grade(img, 1.0), np.float32)
    lum = a.mean(axis=2, keepdims=True)
    a = a * 0.18 + lum * 0.10
    a[:, :, 2] += 14
    a[:, :, 0] -= 4
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    # тёплое окно
    xx, yy = fx._grid(W, H)
    wx, wy = W * window[0], H * window[1]
    g = np.exp(-(((xx - wx) / 140) ** 2 + ((yy - wy) / 110) ** 2) * 1.4)
    g *= 1.0 + 0.08 * math.sin(t * 7.0) * math.sin(t * 3.1)
    a = np.asarray(img, np.float32)
    a[:, :, 0] += g * 150
    a[:, :, 1] += g * 105
    a[:, :, 2] += g * 40
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    return C.grain(img, t, 0.05)


@scene("34")
def s34(t, dur):
    def a(tt, d):
        img = haus_night("haus_2006.jpg", tt + 1.0, t)
        img = C.over(img, label("ЧТО БЫЛО ДАЛЬШЕ", C.seg(tt, 1.0, 1.4), 130, 46, C.WHITE),
                     label("С ЕГО СОБСТВЕННЫХ СЛОВ", C.seg(tt, 2.2, 2.6), H - 150, 40, C.WHITE),
                     C.caption(*CAP_HAUS06, k=C.seg(tt, 0.2, 0.6))).convert("RGB")
        k = C.seg(tt, d - 0.25, d)
        if k > 0:
            img = Image.blend(img, Image.new("RGB", (W, H), (230, 228, 224)), C.smoother(k) * 0.9)
        return img

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.35)


# ═════════════════════════ 35 · врезка Путина · вышел к толпе · архив ═════════════════════════
@scene("35")
def s35(t, dur):
    INS = 24.2
    c_ohr = rel("35", 257.95)
    c_ushla = rel("35", 259.62)
    c_arh = rel("35", 260.73)

    def a_video(tt, d):
        fr = vid("putin", "putin_2018_dresden.mp4", 0.0).at(tt)
        z = 1.0 + 0.004 * tt
        img = zoom_at(fr, z, W / 2, H * 0.45)
        img = grade(img, 0.55)
        img = C.grain(img, t, 0.02)
        img = C.over(img, C.caption(*CAP_PUTIN, k=C.seg(tt, 0.5, 1.0))).convert("RGB")
        k = C.seg(tt, 0.0, 0.35)
        if k < 1:
            img = Image.blend(Image.new("RGB", (W, H), (230, 228, 224)), img, C.smoother(k))
        return img

    def b_tri(tt, d):
        img = haus_night("haus_2006.jpg", tt + 3.0, t, 0.5, 0.45, 0.04)
        items = [("ОН ВЫШЕЛ К ТОЛПЕ", 0.05), ("ОХРАНА ПОКАЗАЛА ОРУЖИЕ", c_ohr - INS), ("ТОЛПА УШЛА", c_ushla - INS)]
        lays = []
        for i, (txt, t0) in enumerate(items):
            lays.append(word(txt, C.seg(tt, t0, t0 + 0.45), 300 + i * 120, 72, "head_l" if i < 2 else "head", C.WHITE, 0.14, x=SAFE_X, anchor="ls", rise=26))
        return C.over(img, *lays, C.caption(*CAP_HAUS06, k=1.0)).convert("RGB")

    def c_arhiv(tt, d):
        img = fx.lampa(lamp_bg(22), W * 0.5, -200, 1300, 0.25)
        lay = kartoteka(1.0 - C.seg(tt, 0.2, 1.1), 0.0, 1.0, tt + 8.0, bars=True, closing=True)
        return C.over(img, lay, label("АРХИВ НЕ ДОСТАЛСЯ НИКОМУ", C.seg(tt, 0.3, 0.7), H - 150, 44, C.WHITE)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_video), (INS, b_tri), (c_arh, c_arhiv)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.25)


# ═════════════════════════ 36 · «А Москва молчит» ═════════════════════════
@scene("36")
def s36(t, dur):
    c_noch = rel("36", 263.5)
    c_otv = rel("36", 265.60)
    c_mos = rel("36", 266.3)
    c_molch = rel("36", 268.09)

    def a(tt, d):
        base = K.base(EUROPE, hot="Germany")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.6, 0, 255).astype(np.uint8), "RGB")
        k_line = C.seg(tt, c_noch, c_otv)
        k_dead = C.seg(tt, c_molch, c_molch + 0.8)
        lay = signal(k_line, k_dead, tt, t)
        img = C.over(base, lay,
                     K.city_layer(["Дрезден", "Москва"], C.seg(tt, 0.1, 0.5), okno=EUROPE, px=30, side={"Москва": "l"}),
                     label("В ТУ НОЧЬ ОН ПРОСИЛ ПОМОЩИ У ВОЕННЫХ", C.seg(tt, c_noch, c_noch + 0.4) * (1 - C.seg(tt, c_otv, c_otv + 0.3)), 130, 40, C.WHITE),
                     label("БЕЗ ПРИКАЗА ИЗ МОСКВЫ — НИЧЕГО", C.seg(tt, c_mos, c_mos + 0.4) * (1 - C.seg(tt, c_molch, c_molch + 0.3)), 130, 40, C.WHITE),
                     word("МОСКВА МОЛЧИТ", C.seg(tt, c_molch, c_molch + 0.5), H * 0.5 + 60, 150, "head", C.WHITE, 0.12, rise=40))
        dx, dy = EUROPE.xy(*DRESDEN)
        mx, my = EUROPE.xy(*MOSKVA)
        cx = C.lerp(dx, (dx + mx) / 2, C.smoother(C.seg(tt, 0.0, c_otv)))
        cy = C.lerp(dy, (dy + my) / 2, C.smoother(C.seg(tt, 0.0, c_otv)))
        z = C.lerp(1.5, 1.15, C.smoother(C.seg(tt, 0.0, c_otv)))
        out = C.grain(zoom_at(img.convert("RGB"), z, cx, cy), t, 0.03)
        if k_dead > 0:
            out = C.fade(out, 1 - 0.3 * C.smoother(k_dead))
        return out

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 37 · особняк сегодня · доска · ясновидящая ═════════════════════════
EXTRA["dres"] = ((W * 0.17, H * 0.21, -2.0), "", "ДРЕЗДЕН · 1989", ["центр молчит", "архив не достался никому"])


def board3(t, lamp_t, k_drop, k_text, k_thread, amp=0.0, dark=0.10):
    """доска второго куска целиком + карточка ДРЕЗДЕН сверху слева, нить к карточке 01 ЧЕЛОВЕК"""
    lx, ly = fx.lampa_pos(lamp_t, W / 2, amp, 3.6)
    img = board_bg().copy().convert("RGBA")
    pins = []
    items = [(CARD_POS[i], card_tex(i, 1.0), 1.0, None) for i in range(3)]
    for key in ("lich", "zachem", "mitr"):
        items.append((EXTRA[key][0], card_extra(key, 1.0), 1.0, key))
    if k_drop > 0:
        items.append((EXTRA["dres"][0], card_extra("dres", k_text), k_drop, "dres"))
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
    ex = {k: p for k, p in pins if k}
    thread(d, base_pins, 1.0)
    thread(d, [base_pins[0], ex["lich"]], 1.0, sag=30)
    thread(d, [base_pins[0], ex["zachem"]], 1.0, sag=60)
    x, y = ex["zachem"]
    thread(d, [(x, y), (W + 80, y - 160)], 1.0, sag=20)
    thread(d, [ex["mitr"], base_pins[1]], 1.0, sag=20)
    if "dres" in ex and k_thread > 0:
        thread(d, [ex["dres"], base_pins[0]], k_thread, sag=24)
    for _, (x, y) in pins:
        pin_at(d, x, y)
    img = C.over(img, C.done(lay)).convert("RGB")
    return fx.lampa(img, lx, ly, 1150, dark)


@scene("37")
def s37(t, dur):
    c_chel = rel("37", 269.39)
    c_videl = rel("37", 270.16)
    c_centr = rel("37", 271.56)
    c_imenno = rel("37", 272.99)
    c_obesh = rel("37", 275.03)

    def a_today(tt, d):
        img = C.kb(foto("haus_2012_2.jpg"), tt, 0.06, 0.55, 0.5)
        img = grade(img, 0.45)
        img = C.fade(img, 0.9)
        return C.over(img, K.date_tag("СЕГОДНЯ", C.seg(tt, 0.4, 0.9), sub="тот же особняк · тихая улица"),
                      label("ЧЕЛОВЕК, КОТОРЫЙ ОДНАЖДЫ ВИДЕЛ", C.seg(tt, c_videl, c_videl + 0.4), H - 150, 40, C.WHITE),
                      C.caption(*CAP_HAUS12, k=C.seg(tt, 0.2, 0.6))).convert("RGB")

    def b_board(tt, d):
        kd = C.seg(tt, 0.0, 0.5)
        kt = C.seg(tt, 0.35, 0.9)
        kth = C.seg(tt, 0.6, 1.3)
        img = board3(t, 12.0 + tt, kd, kt, kth, amp=300.0)
        cx, cy, _ = EXTRA["dres"][0]
        z = 1.6 - 0.25 * C.smoother(C.seg(tt, 0.4, d))
        img = zoom_at(img, z, C.lerp(cx, W * 0.3, C.smoother(C.seg(tt, 0.4, d))), C.lerp(cy, H * 0.4, C.smoother(C.seg(tt, 0.4, d))))
        return flash(C.over(img, word("КАК МОЛЧИТ ЦЕНТР", C.seg(tt, 0.1, 0.5), H - 100, 58, "head_l", C.WHITE, 0.16, rise=24)).convert("RGB"), tt, 0.08, 0.4)

    def c_ver(tt, d):
        img = verica("v13c", "v13_krupno_2015.mp4", tt + 0.4, push=0.08, hand=2.5)
        img = C.fade(img, 0.75)
        return C.over(img, label("ИМЕННО ЕМУ", C.seg(tt, 0.1, 0.5), 130, 46, C.WHITE),
                      label("ОБЕЩАЕТ ВЛАСТЬ ПОЖИЗНЕННУЮ", C.seg(tt, c_obesh - c_imenno, c_obesh - c_imenno + 0.4), H - 150, 40, C.WHITE),
                      C.caption(*CAP_V, k=1.0)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_today), (c_centr, b_board), (c_imenno, c_ver)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.25)


# ═════════════════════════ 38 · что значит «пожизненно»? линия жизни ═════════════════════════
@scene("38")
def s38(t, dur):
    c_pozh = rel("38", 277.83)
    c_2036 = rel("38", 278.86)
    c_posl = rel("38", 280.62)
    c_ili = rel("38", 282.07)
    c_svoim = rel("38", 283.05)

    def a(tt, d):
        img = C.kb(lamp_bg(26), tt / 4.0, 0.05, 0.5, 0.5)
        lay = liniya_zhizni(tt, c_2036, c_posl, c_svoim, t)
        return C.over(img, lay,
                      word("НО ЧТО ЗНАЧИТ", C.seg(tt, 0.05, 0.45), 190, 50, "head_l", C.GREY, 0.3, rise=16),
                      word("«ПОЖИЗНЕННО»?", C.seg(tt, c_pozh, c_pozh + 0.45), 300, 120, "head", C.WHITE, 0.08, rise=30)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.035, vig=0.3)


# ═════════════════════════ 39 · вторая строка — о своих ═════════════════════════
@scene("39")
def s39(t, dur):
    c_vtor = rel("39", 285.9)
    c_svo = rel("39", 286.8)

    def a(tt, d):
        sc = 2.0 + 0.04 * tt
        k = C.smoother(C.seg(tt, 0.2, 1.5))
        img, geo = page_view(6890, sc, 805)
        b1 = to_frame(LINE_PUTIN, geo)
        b2 = to_frame(LINE_DAUGHTERS, geo)
        ly = C.lerp((b1[1] + b1[3]) / 2, (b2[1] + b2[3]) / 2, k)
        lx = C.lerp((b1[0] + b1[2]) / 2, (b2[0] + b2[2]) / 2, k)
        img = fx.fonar(img, lx, ly, 640, 300, 0.10, 0.05, t)
        img = page_dark(img, t)
        ku = C.seg(tt, c_vtor, c_vtor + 0.5)
        return C.over(img, red_line(ku, b2[0] - 8, b2[2] + 8, b2[3] + 6, 5),
                      label("ВТОРАЯ СТРОКА", C.seg(tt, c_vtor, c_vtor + 0.4), 130, 46, C.WHITE),
                      word("О СВОИХ", C.seg(tt, c_svo, c_svo + 0.45), H - 130, 100, "head", C.WHITE, 0.14, rise=30),
                      C.caption(*CAP_B, k=1.0)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.7, grain_k=0.0, vig=0.3)


# ═════════════════════════ fx3 — новые эффекты третьего куска ═════════════════════════
_dust = None


def proektor(photo, tt, t, zoom=1.0, cx=0.5, cy=0.5, box=(1300, 720)):
    """слайд-проектор: фото в рамке слайда на тёмной стене, щелчок — кадр садится с перелётом,
    в луче пыль, лампа чуть мерцает, тон тёплый, края мягкие"""
    global _dust
    bw, bh = box
    pw, ph = photo.size
    s = min(bw / pw, bh / ph)
    iw, ih = int(pw * s), int(ph * s)
    im = photo.resize((iw, ih), Image.LANCZOS)
    if zoom > 1.0:
        im = zoom_at(im, zoom, iw * cx, ih * cy)
    # тёплый тон, мягкость проекции
    a = np.asarray(im, np.float32)
    lum = a.mean(axis=2, keepdims=True)
    a = lum * np.array([1.0, 0.93, 0.80], np.float32)[None, None, :]
    fl = 1.0 + 0.035 * math.sin(t * 29.0) * math.sin(t * 5.3 + 0.7)
    a = np.clip(a * 0.92 * fl, 0, 255)
    im = Image.fromarray(a.astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(0.8))
    # посадка слайда: перелёт сверху, лёгкий перекос
    k = C.seg(tt, 0.0, 0.42)
    kb_ = C.out_back(k, 2.2)
    dy = int((1 - kb_) * 90)
    tilt = (1 - C.out_cubic(k)) * 2.5
    frame_w, frame_h = iw + 56, ih + 56
    sl = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    ImageDraw.Draw(sl).rounded_rectangle([0, 0, frame_w - 1, frame_h - 1], radius=10, fill=(44, 42, 40, 255), outline=(80, 78, 74, 255), width=3)
    sl.paste(im, (28, 28))
    if tilt:
        sl = sl.rotate(tilt, Image.BICUBIC, expand=True)
    bg = Image.new("RGB", (W, H), (7, 7, 8))
    # свечение экрана вокруг слайда
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gx0, gy0 = int(W / 2 - frame_w / 2), int(H * 0.47 - frame_h / 2 + dy)
    ImageDraw.Draw(glow).rectangle([gx0 - 30, gy0 - 30, gx0 + frame_w + 30, gy0 + frame_h + 30], fill=(170, 150, 110, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    out = C.over(bg, glow)
    out.alpha_composite(sl, (int(W / 2 - sl.size[0] / 2), int(H * 0.47 - sl.size[1] / 2 + dy)))
    out = out.convert("RGB")
    # пыль в луче
    if _dust is None:
        rng = np.random.default_rng(12)
        _dust = rng.random((70, 4))
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    for i in range(_dust.shape[0]):
        px, py, sp, ph_ = _dust[i]
        x = (px * W + 40 * math.sin(t * (0.3 + sp * 0.5) + ph_ * 6.28)) % W
        y = (py * H + t * (8 + sp * 20)) % H
        r = (1.2 + sp * 1.6) * SS
        al = int(120 + 100 * math.sin(t * 3.0 + ph_ * 6.28))
        d.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], fill=(230, 215, 180, max(30, al)))
    out = C.over(out, C.done(lay)).convert("RGB")
    out = flash(out, tt, 0.12, 0.7)
    return C.grain(out, t, 0.05)


def obuglivanie(img, k, t, seed=7):
    """бумага обугливается с правого нижнего угла: чернота, тлеющая кромка, обугленная кайма"""
    if k <= 0:
        return img
    xx, yy = fx._grid(W, H)
    n = fx._noise(W, H, seed, 46.0)
    n2 = fx._noise(W, H, seed + 1, 9.0)
    dist = np.sqrt(((W - xx) / W) ** 2 + ((H - yy) / H) ** 2) / 1.42
    f = 0.55 * dist + 0.33 * n + 0.12 * n2
    kk = k * 1.25
    a = np.asarray(img.convert("RGB"), np.float32)
    burned = f < kk - 0.045
    ember = (f >= kk - 0.045) & (f < kk + 0.012)
    scorch = (f >= kk + 0.012) & (f < kk + 0.11)
    # обугленная кайма: темнеет к кромке
    sc = np.clip((kk + 0.11 - f) / 0.098, 0, 1) * scorch
    a *= (1 - 0.85 * sc)[:, :, None]
    a[:, :, 0] += 18 * sc
    # тлеющая кромка
    e = np.clip((f - (kk - 0.045)) / 0.057, 0, 1) * ember
    fl = 1.0 + 0.25 * math.sin(t * 31.0) * math.sin(t * 13.0 + 1.0)
    a[:, :, 0] = np.where(ember, 255 * fl * (0.6 + 0.4 * e), a[:, :, 0])
    a[:, :, 1] = np.where(ember, 120 * fl * e ** 1.5, a[:, :, 1])
    a[:, :, 2] = np.where(ember, 20 * e ** 2, a[:, :, 2])
    a[burned] = (5, 5, 6)
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    # свечение от кромки
    gl = Image.fromarray((np.clip(e * 255, 0, 255)).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(22))
    g = np.asarray(gl, np.float32) / 255.0 * 0.9
    b = np.asarray(out, np.float32)
    b[:, :, 0] += g * 160
    b[:, :, 1] += g * 50
    return Image.fromarray(np.clip(b, 0, 255).astype(np.uint8), "RGB")


def rukopis(text, k, x, y, px, size, angle=0.0, heavy=False):
    """рукописная пометка на листе size: строка курсивом пишется слева направо, перо-точка впереди"""
    pw, ph = size
    lay = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    if k <= 0:
        return lay
    f = C.font("serif_i", px)
    d = ImageDraw.Draw(lay)
    col = (38, 30, 60, 255) if not heavy else (28, 22, 48, 255)
    tw = d.textlength(text, font=f)
    base = int(px * 1.05)
    d.text((0, base), text, font=f, fill=col, anchor="ls")
    if heavy:
        d.text((1, base + 1), text, font=f, fill=col, anchor="ls")
    # маска: написано до доли k
    kk = C.out_cubic(k)
    m = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(m).rectangle([0, 0, int(tw * kk) + 2, int(px * 1.6)], fill=255)
    al = Image.fromarray(np.minimum(np.asarray(lay.getchannel("A")), np.asarray(m)).astype(np.uint8), "L")
    lay.putalpha(al)
    if k < 1:
        dd = ImageDraw.Draw(lay)
        xe = tw * kk
        dd.ellipse([xe - 4, base - px * 0.3 - 4, xe + 4, base - px * 0.3 + 4], fill=col)
    # поворот вокруг начала строки и перенос на место (x, y — левый край строки)
    lay = lay.rotate(angle, Image.BICUBIC, center=(0, base), translate=(x, y - base))
    return lay


def signal(k_line, k_dead, tt, t):
    """сигнал Дрезден→Москва: пунктир прорисовывается, по нему бежит импульс; Москва не
    отвечает — кольцо серое; при k_dead линия гаснет"""
    coords = [DRESDEN, (20.0, 53.4), (28.0, 55.2), MOSKVA]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if k_line <= 0:
        return lay
    col = C.mix(C.RED, C.GREY2, 0.8 * k_dead)
    line = K.line_layer(coords, k_line, okno=EUROPE, color=col, width=4, dash=(22, 14), glow=k_dead < 0.5, head=False)
    lay = Image.alpha_composite(lay, line)
    d = ImageDraw.Draw(lay)
    mx, my = EUROPE.xy(*MOSKVA)
    # импульсы бегут по линии
    if k_line > 0.05 and k_dead < 1:
        pts = [EUROPE.xy(*c) for c in coords]
        segl = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
        total = sum(segl)
        for j in range(3):
            u = ((tt * 0.55 + j * 0.33) % 1.0) * k_line
            want = total * u
            run = 0.0
            for i in range(len(pts) - 1):
                if run + segl[i] >= want:
                    fr = (want - run) / max(1e-6, segl[i])
                    x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * fr
                    y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * fr
                    break
                run += segl[i]
            r = 7 * (1 - 0.6 * k_dead)
            al = int(255 * (1 - k_dead))
            d.ellipse([x - r * 2.2, y - r * 2.2, x + r * 2.2, y + r * 2.2], fill=C.WHITE + (int(al * 0.25),))
            d.ellipse([x - r, y - r, x + r, y + r], fill=C.WHITE + (al,))
    # Москва: серое кольцо, не отвечает
    if k_line >= 0.98:
        for j in range(2):
            ph = (tt * 0.6 + j * 0.5) % 1.0
            r = 10 + 70 * ph
            d.ellipse([mx - r, my - r, mx + r, my + r], outline=C.GREY2 + (int(160 * (1 - ph) * (1 - 0.5 * k_dead)),), width=3)
    return lay


def plan_kab(k_rooms, k_stasi, tt, arrow=0.0):
    """план особняка: контур и шесть кабинетов, загораются по одному; блок Штази рядом;
    стрелка (красная линия) от Штази к особняку"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    bx, by, bw, bh = W * 0.12, H * 0.28, 900, 470
    line = (150, 148, 140, 230)
    d.rectangle([bx * s, by * s, (bx + bw) * s, (by + bh) * s], outline=line, width=3 * s)
    rw, rh = bw / 3, bh / 2
    for i in range(6):
        kx, ky = i % 3, i // 3
        x0, y0 = bx + kx * rw, by + ky * rh
        ki = C.seg(k_rooms, i / 6, (i + 1) / 6)
        if ki > 0:
            a = int(120 * C.smoother(ki))
            d.rectangle([(x0 + 6) * s, (y0 + 6) * s, (x0 + rw - 6) * s, (y0 + rh - 6) * s], fill=(222, 190, 120, a))
        d.rectangle([x0 * s, y0 * s, (x0 + rw) * s, (y0 + rh) * s], outline=line, width=2 * s)
        # дверь
        d.rectangle([(x0 + rw * 0.4) * s, (y0 + rh - 4) * s, (x0 + rw * 0.6) * s, (y0 + rh + 4) * s], fill=(12, 12, 15, 255))
    C.tracked(d, (bx + bw / 2) * s, (by + bh + 58) * s, "ОСОБНЯК · АНГЕЛИКАШТРАССЕ, 4", C.font("head_l", 30 * s), C.WHITE + (255,), 0.24, "ms")
    if k_stasi > 0:
        a = int(255 * C.smoother(k_stasi))
        sx, sy, sw, sh = W * 0.70, H * 0.22, 420, 560
        d.rectangle([sx * s, sy * s, (sx + sw) * s, (sy + sh) * s], outline=(150, 148, 140, a), width=3 * s)
        for j in range(4):
            yy = sy + 20 + j * 135
            d.rectangle([(sx + 20) * s, yy * s, (sx + sw - 20) * s, (yy + 110) * s], outline=(110, 108, 100, a), width=2 * s)
        C.tracked(d, (sx + sw / 2) * s, (sy + sh / 2 + 20) * s, "ШТАЗИ", C.font("head", 64 * s), C.WHITE + (a,), 0.2, "ms")
        C.tracked(d, (sx + sw / 2) * s, (sy + sh + 58) * s, "ОКРУЖНОЕ УПРАВЛЕНИЕ", C.font("head_l", 26 * s), C.GREY + (a,), 0.24, "ms")
        # пунктир «рядом»
        x0, x1 = bx + bw + 20, sx - 20
        yy = H * 0.5
        on, off = 16, 12
        x = x0
        while x < x1:
            d.line([(x * s, yy * s), (min(x1, x + on) * s, yy * s)], fill=C.GREY + (a,), width=2 * s)
            x += on + off
        C.tracked(d, ((x0 + x1) / 2) * s, (yy - 16) * s, "РЯДОМ", C.font("head_l", 26 * s), C.GREY + (a,), 0.3, "ms")
    if arrow > 0:
        # толпа идёт: красная линия от Штази к особняку
        x0, x1 = W * 0.70 - 20, bx + bw + 20
        yy = H * 0.5 + 40
        kk = C.out_cubic(arrow)
        xe = x0 + (x1 - x0) * kk
        g = C.layer()
        dg = ImageDraw.Draw(g)
        dg.line([(x0 * s, yy * s), (xe * s, yy * s)], fill=C.RED + (110,), width=22 * s)
        g = g.filter(ImageFilter.GaussianBlur(12 * s))
        lay = Image.alpha_composite(lay, g)
        d = ImageDraw.Draw(lay)
        d.line([(x0 * s, yy * s), (xe * s, yy * s)], fill=C.RED + (255,), width=6 * s)
        if kk < 1:
            r = 10 * s
            d.ellipse([xe * s - r, yy * s - r, xe * s + r, yy * s + r], fill=C.WHITE + (255,))
        else:
            d.polygon([(xe * s, yy * s), ((xe + 26) * s, (yy - 14) * s), ((xe + 26) * s, (yy + 14) * s)], fill=C.RED + (255,))
    return C.done(lay)


def liniya_zhizni(tt, c1, c2, c3, t):
    """линия жизни: шкала слева направо, красный бегунок, вехи-вопросы; шкала уходит за край"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    y = H * 0.62
    k_line = C.seg(tt, 0.1, 1.2)
    x0 = SAFE_X
    x_end = x0 + (W + 200 - x0) * C.out_cubic(k_line)
    # сдвиг камеры вправо со временем
    shift = 160 * C.smoother(C.seg(tt, c3, c3 + 2.0))
    d.line([((x0 - shift) * s, y * s), ((x_end - shift) * s, y * s)], fill=C.GREY2 + (255,), width=3 * s)
    # вехи
    marks = [(W * 0.30, c1, "2036", "head", 110, True), (W * 0.58, c2, "ПОСЛЕДНИЙ ДЕНЬ", "head_l", 54, False),
             (W * 0.86, c3, "СВОИМ?", "head", 96, False)]
    # бегунок: едет к очередной вехе
    cur = x0
    for mx, mc, txt, kind, px, red in marks:
        prev = cur
        k = C.seg(tt, mc - 0.6, mc)
        if k <= 0:
            break
        cur = C.lerp(prev, mx, C.out_cubic(k))
    if tt > c3 + 0.3:
        cur = C.lerp(W * 0.86, W + 300, C.smoother(C.seg(tt, c3 + 0.3, c3 + 2.4)))
    bx = cur - shift
    g = C.layer()
    dg = ImageDraw.Draw(g)
    dg.ellipse([(bx - 30) * s, (y - 30) * s, (bx + 30) * s, (y + 30) * s], fill=C.RED + (140,))
    g = g.filter(ImageFilter.GaussianBlur(10 * s))
    lay = Image.alpha_composite(lay, g)
    d = ImageDraw.Draw(lay)
    d.ellipse([(bx - 11) * s, (y - 11) * s, (bx + 11) * s, (y + 11) * s], fill=C.RED + (255,))
    # пройденный путь красный
    d.line([((x0 - shift) * s, y * s), (bx * s, y * s)], fill=C.RED + (255,), width=4 * s)
    for mx, mc, txt, kind, px, red in marks:
        k = C.seg(tt, mc, mc + 0.45)
        if k <= 0:
            continue
        a = int(255 * C.smoother(k))
        x = mx - shift
        d.line([(x * s, (y - 26) * s), (x * s, (y + 26) * s)], fill=C.WHITE + (a,), width=3 * s)
        f = C.font(kind, px * s)
        col = (C.RED if red else C.WHITE) + (a,)
        rise = (1 - C.out_cubic(k)) * 30
        if red:
            # счётчик добегает до 2036
            v = int(round(C.lerp(2024, 2036, C.out_expo(k))))
            txt = str(v)
        C.tracked(d, x * s, (y - 60 - rise) * s, txt, f, col, 0.06, "ms")
        if txt == "СВОИМ?":
            C.tracked(d, x * s, (y + 80) * s, "ДО ДНЯ, КОГДА ВЛАСТЬ МОЖНО ПЕРЕДАТЬ", C.font("head_l", 30 * s), C.GREY + (a,), 0.24, "ms")
        elif txt == "ПОСЛЕДНИЙ ДЕНЬ":
            C.tracked(d, x * s, (y + 80) * s, "ДО", C.font("head_l", 30 * s), C.GREY + (a,), 0.24, "ms")
        else:
            C.tracked(d, x * s, (y + 80) * s, "ДО ДВЕ ТЫСЯЧИ ТРИДЦАТЬ ШЕСТОГО", C.font("head_l", 30 * s), C.GREY + (a,), 0.24, "ms")
    return C.done(lay)


_kart = {}


def _card_img(i, bars):
    key = ("c", i, bars)
    if key in _kart:
        return _kart[key]
    cw, ch = 520, 330
    im = C.paper(cw, ch, seed=90 + i, tone=(214, 206, 186), dark=0.02).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, cw - 1, ch - 1], outline=(130, 120, 100, 255), width=2)
    d.rectangle([0, 0, cw - 1, 14], fill=(150, 60, 50, 255) if i % 3 == 0 else (120, 110, 90, 255))
    d.text((26, 62), "ДЕЛО", font=C.font("head_l", 28), fill=(90, 80, 70, 255), anchor="ls")
    rng = random.Random(i)
    for j in range(4):
        yy = 96 + j * 52
        if bars:
            wl = rng.randint(160, 380)
            d.rectangle([26, yy, 26 + wl, yy + 26], fill=(20, 18, 16, 255))
        else:
            wl = rng.randint(160, 380)
            d.line([(26, yy + 20), (26 + wl, yy + 20)], fill=(150, 140, 120, 255), width=2)
    _kart[key] = im
    return im


def kartoteka(k_out, k_flip, k_a, tt, bars=True, pulse=0.0, closing=False):
    """картотечный ящик: выезжает сверху (k_out), внутри стопка карточек, k_flip листает их
    вперёд; bars — имена замазаны; closing — ящик задвигается"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if k_out <= 0:
        return lay
    kk = C.out_cubic(k_out)
    bw, bh = 1180, 620
    bx = int(W / 2 - bw / 2)
    by = int(H * 0.58 - bh / 2 - (1 - kk) * (H * 0.9))
    box = C.paper(bw, bh, seed=95, tone=(84, 70, 54), dark=0.1).convert("RGBA")
    d = ImageDraw.Draw(box)
    d.rectangle([0, 0, bw - 1, bh - 1], outline=(40, 32, 24, 255), width=5)
    d.rectangle([14, 14, bw - 15, bh - 15], fill=(30, 24, 18, 255))
    # карточки в глубину
    n = 9
    for i in range(n - 1, -1, -1):
        prog = C.clamp(k_flip * n - i, 0, 1)   # эта карточка улетает
        depth = i / (n - 1)
        cw, ch = 520, 330
        scl = 1.0 - 0.18 * depth
        card = _card_img(i, bars).resize((int(cw * scl), int(ch * scl)), Image.LANCZOS)
        cx = bw / 2 + depth * 40
        cy = bh * 0.62 - depth * 120
        if prog > 0:
            cy -= C.out_cubic(prog) * 520
            card = C.alpha(card, 1 - C.seg(prog, 0.55, 1.0))
            card = card.rotate(-8 * prog, Image.BICUBIC, expand=True)
        card = C.alpha(card, 1.0 - 0.45 * depth)
        box.alpha_composite(card, (int(cx - card.size[0] / 2), int(cy - card.size[1] / 2)))
    # передняя стенка с ручкой
    d.rectangle([0, bh - 150, bw - 1, bh - 1], fill=(96, 80, 60, 255), outline=(40, 32, 24, 255), width=5)
    d.rounded_rectangle([bw / 2 - 90, bh - 95, bw / 2 + 90, bh - 55], radius=16, fill=(150, 130, 100, 255))
    d.rounded_rectangle([bw / 2 - 180, bh - 135, bw / 2 + 180, bh - 105], radius=6, fill=(205, 195, 175, 255))
    if pulse > 0:
        # имена: чёрные полосы вспыхивают
        gl = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        ImageDraw.Draw(gl).rectangle([40, 40, bw - 40, bh - 160], fill=(204, 34, 30, int(70 * math.sin(pulse * math.pi))))
        box = Image.alpha_composite(box, gl)
    sh, sx, sy = fx.shadow_of((bw, bh), W / 2, -300, bx + bw / 2, by + bh / 2, blur=30, a=190)
    lay.alpha_composite(sh, (sx, sy))
    lay.alpha_composite(C.alpha(box, k_a), (bx, by))
    return lay
