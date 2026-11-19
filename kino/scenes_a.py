#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Пролог и акт I · Человек: сцены 01–09."""
import math

from PIL import Image, ImageDraw, ImageFilter

import core as C
import karta as K
import zal_kino as ZK
from core import W, H, SS

SCENES = {}


def scene(sid):
    def deco(fn):
        SCENES[sid] = fn
        return fn
    return deco


# ───────────────────────── 01 · Лист на столе ─────────────────────────
_s01 = {}


@scene("01")
def s01(t, dur):
    """лист висит на двух тросах посреди зала, опускается с потолка; камера
    идёт к нему, пока строка не заполнит кадр; красная черта — на реплике"""
    cam = ZK.Cam(x=0.0, y=1.30, z=C.lerp(0.0, 6.3, C.smoother(t / dur)))
    img = ZK.hall(cam)
    k_fall = C.out_back(C.seg(t, 0.4, 2.6)) if hasattr(C, "out_back") else C.out_cubic(C.seg(t, 0.4, 2.6))
    red = C.seg(t, C.cue("01", "а взамен получает", 11.5), C.cue("01", "а взамен получает", 11.5) + 1.6)
    key = round(red, 2)
    if key not in _s01:
        _s01[key] = ZK.sheet_tex(["Донбасс", "в обмен на НАТО"], fsize=118, kind="serif_b",
                                 title="Абу-Даби · проект", red_line=red)
    tex = _s01[key]
    sw, sh, cz = 2.3, 1.63, 9.0
    cy = 1.30 + (1 - k_fall) * 4.2
    sway = (1 - C.seg(t, 2.6, 6.0)) * 0.05 * math.sin(t * 3.1)
    c = ZK.Z.quad((0.0, cy, cz), sw, sh, yaw=sway, roll=sway * 0.4)
    ZK.Z.wire(img, cam, (c[0][0] + 0.15, c[0][1], c[0][2]))
    ZK.Z.wire(img, cam, (c[1][0] - 0.15, c[1][1], c[1][2]))
    ZK.Z.floor_shadow(img, cam, c, tex)
    ZK.Z.paste_quad(img, tex, [cam.proj(p) for p in c])
    img = ZK.Z.embers(img, cam, ZK.Z.cluster(2.4, 0.3, 10.5, 0.5, 3, 1) + ZK.Z.cluster(-2.6, 0.25, 12.5, 0.45, 3, 2), t)
    img = img.convert("RGB")
    img = C.vignette(img, 0.3)
    return C.finish(img, t, dur, fi=1.2, fo=0.8, grain_k=0.025)


# ───────────────────────── 02 · Линия, которая будет двигаться ─────────────────────────
@scene("02")
def s02(t, dur):
    base = K.base()
    # медленный наезд на восток
    zoom = 0.10 * C.smoother(t / dur)
    base = C.kb(base, 1.0, zoom, 0.68, 0.55)
    k_line = C.seg(t, 1.0, 7.5)
    lay = [K.line_layer(K.LINE_NOW, k_line, dash=(16, 10), width=5)]
    # после прорисовки линия перестаёт пунктирить — становится сплошной
    k_cities = C.seg(t, 4.0, 6.0)
    lay.append(K.city_layer(["Киев", "Харьков", "Донецк", "Луганск", "Запорожье", "Херсон"],
                            k_cities, side={"Херсон": "l"}))
    lay.append(K.date_tag("2026", C.seg(t, 7.0, 8.2), sub="линия фронта"))
    # окно карты сдвинулось зумом — слои тоже надо сдвинуть: проще рисовать их в том же зуме
    img = C.over(base, *[C.kb(l, 1.0, zoom, 0.68, 0.55) for l in lay])
    img = img.convert("RGB")
    return C.finish(img, t, dur, fi=0.8, fo=0.6, grain_k=0.03, vig=0.2)


# ───────────────────────── 03 · Титр фильма ─────────────────────────
@scene("03")
def s03(t, dur):
    img = Image.new("RGB", (W, H), (5, 5, 6))
    k = C.smoother(C.seg(t, 0.4, 1.8))
    pap = C.paper(W, H, seed=21, tone=(52, 48, 44)).filter(ImageFilter.GaussianBlur(2))
    img = Image.blend(img, pap, 0.5 * k)
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    a = int(255 * k)
    f = C.font("head", 300 * SS)
    C.tracked(d, W / 2 * SS, (H / 2 + 60) * SS, "ЛИНИЯ", f, C.WHITE + (a,), 0.10, "ms")
    # красная черта под словом — сама «линия», прорисовывается
    kl = C.seg(t, 1.2, 2.8)
    x0, x1 = (W / 2 - 330) * SS, (W / 2 + 330) * SS
    d.rectangle([x0, (H / 2 + 92) * SS, x0 + (x1 - x0) * C.out_cubic(kl), (H / 2 + 97) * SS], fill=C.RED + (255,))
    k2 = C.smoother(C.seg(t, 2.0, 3.0))
    f2 = C.font("serif_i", 46 * SS)
    C.tracked(d, W / 2 * SS, (H / 2 + 165) * SS, "последний прогноз Киссинджера", f2,
              C.GREY + (int(255 * k2),), 0.02, "ms")
    img = C.over(img, lay).convert("RGB")
    img = C.vignette(img, 0.6)
    img = C.grain(img, t, 0.05)
    return C.in_out_fade(img, t, dur, 0.0, 1.4)


# ───────────────────────── 04 · Шкала жизни ─────────────────────────
VEHI = [(1923, "Фюрт, Бавария", "рождение"), (1938, "эмиграция", "chamberlain_1938.jpg"),
        (1971, "тайно в Пекин", "kissinger_zhou_1971.jpg"), (1973, "Нобелевская премия", "nobel_1973.jpg"),
        (1994, "НАТО на восток", None), (2014, "колонка о линии", None),
        (2022, "Давос", None), (2023, "сто лет", "kissinger_100_2023.jpg")]
_thumbs = {}


def _thumb(name, size=(220, 124)):
    if name not in _thumbs:
        im = C.foto(name, size) if name else None
        if im is not None:
            im = C.cover(im, size).convert("L").convert("RGB")
        _thumbs[name] = im
    return _thumbs[name]


@scene("04")
def s04(t, dur):
    # титр акта первые 2,2 с
    if t < 2.2:
        return C.act_title("I", "Человек", t, 2.2)
    tt = t - 2.2
    dd = dur - 2.2
    img = Image.new("RGB", (W, H), C.BG)
    # шкала шире кадра: камера едет слева направо
    total = 4200
    x_off = -C.smoother(tt / dd) * (total - W + 240) + 120
    y = 600
    lay = C.layer(total + 400, H)
    d = ImageDraw.Draw(lay)
    d.line([(120 * SS, y * SS), ((total + 120) * SS, y * SS)], fill=C.GREY3 + (255,), width=2 * SS)
    f_year = C.font("head", 56 * SS)
    f_lab = C.font("head_l", 26 * SS)
    for i, (year, label, th) in enumerate(VEHI):
        x = 120 + i / (len(VEHI) - 1) * total
        # веха появляется, когда камера подъезжает
        k = C.seg(x + x_off, W * 0.72, W * 0.55)
        k = C.smoother(k)
        if k <= 0:
            continue
        a = int(255 * k)
        d.line([(x * SS, (y - 10 - 26 * k) * SS), (x * SS, (y + 10) * SS)], fill=C.RED + (a,), width=3 * SS)
        d.ellipse([(x - 6) * SS, (y - 6) * SS, (x + 6) * SS, (y + 6) * SS], fill=C.WHITE + (a,))
        C.tracked(d, x * SS, (y + 70) * SS, str(year), f_year, C.WHITE + (a,), 0.04, "ms")
        C.tracked(d, x * SS, (y + 106) * SS, label.upper(), f_lab, C.GREY + (a,), 0.22, "ms")
    big = C.done(lay, total + 400, H)
    img.paste(big.convert("RGB"), (int(x_off), 0), big)
    # миниатюры кадров над вехами (не через SS, они растровые)
    for i, (year, label, th) in enumerate(VEHI):
        if not th:
            continue
        x = 120 + i / (len(VEHI) - 1) * total + x_off
        k = C.smoother(C.seg(x, W * 0.72, W * 0.55))
        if k <= 0:
            continue
        tm = _thumb(th)
        if tm is None:
            continue
        card = Image.new("RGB", (tm.size[0] + 4, tm.size[1] + 4), C.GREY2)
        card.paste(tm, (2, 2))
        card = card.convert("RGBA")
        card.putalpha(int(255 * k))
        yy = y - 60 - card.size[1] - (1 - k) * 30
        img.paste(card, (int(x - card.size[0] / 2), int(yy)), card)
    return C.finish(img, tt, dd, fi=0.6, fo=0.5, grain_k=0.03, vig=0.35)


# ───────────────────────── 05 · Пекин, 1971 ─────────────────────────
def parallax(photo, t, k_zoom=0.10, depth=0.06, size=(W, H)):
    """фото «дышит» слоями: середина (фигуры) ближе, края дальше.
    Задний слой — размытая копия с большим зумом, передний — резкая середина."""
    w, h = size
    back = C.kb(photo, t, k_zoom * 1.6, 0.5, 0.5, size).filter(ImageFilter.GaussianBlur(2.5))
    front = C.kb(photo, t, k_zoom, 0.5, 0.5, size)
    # маска переднего слоя: мягкий овал по центру
    m = Image.new("L", (w // 4, h // 4), 0)
    ImageDraw.Draw(m).ellipse([w // 16, h // 24, w // 4 - w // 16, h // 4], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(40)).resize((w, h), Image.BILINEAR)
    out = back.copy()
    out.paste(front, (0, 0), m)
    return out


def filmstrip(photos, t, k, size=(W, H)):
    """лента плёнки едет вбок: k 0…1 — переход от первого кадра ко второму"""
    w, h = size
    fh = int(h * 0.78)
    fw = int(fh * 4 / 3)
    gap = 36
    strip_h = fh + 150
    out = Image.new("RGB", (w, h), (8, 8, 9))
    # положение ленты
    x0 = int(w / 2 - fw / 2 - C.smoother(k) * (fw + gap))
    y0 = int(h / 2 - fh / 2)
    strip = Image.new("RGB", (fw * 3 + gap * 3, strip_h), (14, 14, 16))
    d = ImageDraw.Draw(strip)
    for i in range(0, strip.size[0], 48):
        d.rounded_rectangle([i + 8, 18, i + 36, 48], radius=5, fill=(70, 70, 74))
        d.rounded_rectangle([i + 8, strip_h - 48, i + 36, strip_h - 18], radius=5, fill=(70, 70, 74))
    for i, ph in enumerate(photos):
        fr = C.cover(ph, (fw, fh)).convert("L").convert("RGB")
        strip.paste(fr, (i * (fw + gap), 75))
    out.paste(strip, (x0, y0 - 75))
    return out


_s05 = {}


@scene("05")
def s05(t, dur):
    if "a" not in _s05:
        _s05["a"] = C.foto("kissinger_zhou_1971.jpg")
        _s05["b"] = C.foto("nixon_mao_1972.jpg")
    k_strip = C.seg(t, dur * 0.55, dur * 0.55 + 1.4)
    if k_strip <= 0:
        img = parallax(_s05["a"].convert("L").convert("RGB"), t / dur)
        img = C.film_look(img, t, 0.8)
        img = C.over(img, C.caption("Пекин", "июль 1971", "фото архива", C.seg(t, 1.0, 1.8)))
    elif k_strip < 1:
        img = filmstrip([_s05["a"], _s05["b"]], t, k_strip)
        img = C.film_look(img, t, 0.6, scratches=False)
    else:
        tt = (t - dur * 0.55 - 1.4) / max(0.5, dur * 0.45 - 1.4)
        img = parallax(_s05["b"].convert("L").convert("RGB"), tt, 0.08)
        img = C.film_look(img, t, 0.8)
        img = C.over(img, C.caption("Пекин", "февраль 1972", "Никсон и Мао · архив США", C.seg(t, dur * 0.55 + 1.6, dur * 0.55 + 2.4)))
    return C.finish(img.convert("RGB"), t, dur, fi=0.5, fo=0.5, grain_k=0.0)


# ───────────────────────── 06 · Премия без мира ─────────────────────────
def quote_split(photo, name, date, lines, k_photo, k_text, side="left", photo_bw=True):
    """цитата-сплит: слева фото, справа слова; k — появление"""
    img = Image.new("RGB", (W, H), C.BG)
    pw = int(W * 0.44)
    ph = C.cover(photo, (pw, H), 0.5, 0.35)
    if photo_bw:
        ph = ph.convert("L").convert("RGB")
    # фото въезжает слева
    dx = int(-(1 - C.out_cubic(k_photo)) * 160)
    tmp = Image.new("RGB", (W, H), C.BG)
    tmp.paste(ph, (dx, 0))
    img = Image.blend(img, tmp, C.clamp(k_photo * 2))
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    a = int(255 * C.smoother(k_text))
    x = (pw + 110) * SS
    y = (H * 0.30) * SS
    # большая кавычка
    fq = C.font("serif_b", 190 * SS)
    d.text((x - 10 * SS, y - 20 * SS), "«", font=fq, fill=C.GREY3 + (a,), anchor="ls")
    f = C.font("serif", 50 * SS)
    yy = y + 40 * SS
    for ln in lines:
        d.text((x, yy), ln, font=f, fill=C.WHITE + (a,), anchor="ls")
        yy += 68 * SS
    d.rectangle([x, yy + 10 * SS, x + 70 * SS, yy + 13 * SS], fill=C.RED + (a,))
    fn = C.font("head_r", 34 * SS)
    C.tracked(d, x, yy + 62 * SS, name.upper(), fn, C.WHITE + (a,), 0.16)
    fd = C.font("head_l", 26 * SS)
    C.tracked(d, x, yy + 100 * SS, date.upper(), fd, C.GREY + (a,), 0.22)
    return C.over(img, lay).convert("RGB")


_s06 = {}


@scene("06")
def s06(t, dur):
    if "p" not in _s06:
        _s06["p"] = C.foto("le_duc_tho_1973.jpg")
        _s06["k"] = C.foto("kissinger_portrait_1973.jpg")
    t2 = C.cue("06", "Отношение к нему полярное", 11.5)
    if t < t2 - 0.4:
        img = quote_split(_s06["p"], "Ле Дык Тхо · отказ от премии", "Ханой · октябрь 1973",
                          ["Мир в Южном Вьетнаме", "ещё не установлен."],
                          C.seg(t, 0.0, 0.9), C.seg(t, 0.8, 1.8))
        img = C.grain(img, t, 0.03)
        return C.finish(img, t, dur, fi=0.5, fo=0.0, grain_k=0.0)
    # вторая половина: портрет, два полюса
    tt = t - t2
    img = Image.new("RGB", (W, H), C.BG)
    ph = C.kb(_s06["k"].convert("L").convert("RGB"), tt / max(1, dur - t2), 0.06, 0.5, 0.3, (int(W * 0.36), H))
    img.paste(ph, (int(W * 0.32), 0))
    # затемнение краёв портрета
    img = C.vignette(img, 0.5)
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    f = C.font("head", 58 * SS)
    f2 = C.font("head_l", 28 * SS)
    ta = C.cue("06", "Для одних он главный", 13.5) - t2
    tb = C.cue("06", "для других военный", 17.5) - t2
    ka, kb_ = C.smoother(C.seg(tt, ta, ta + 0.7)), C.smoother(C.seg(tt, tb, tb + 0.7))
    if ka > 0:
        a = int(255 * ka)
        x = (W * 0.30 - 30 - (1 - ka) * 60) * SS
        C.tracked(d, x, (H * 0.48) * SS, "ГЛАВНЫЙ", f, C.WHITE + (a,), 0.06, "rs")
        C.tracked(d, x, (H * 0.48 + 64) * SS, "ДИПЛОМАТ", f, C.WHITE + (a,), 0.06, "rs")
        C.tracked(d, x, (H * 0.48 + 128) * SS, "ХХ ВЕКА", f, C.WHITE + (a,), 0.06, "rs")
        C.tracked(d, x, (H * 0.48 + 178) * SS, "для одних", f2, C.GREY + (a,), 0.3, "rs")
    if kb_ > 0:
        a = int(255 * kb_)
        x = (W * 0.70 + 30 + (1 - kb_) * 60) * SS
        C.tracked(d, x, (H * 0.48) * SS, "ВОЕННЫЙ", f, C.WHITE + (a,), 0.06, "ls")
        C.tracked(d, x, (H * 0.48 + 64) * SS, "ПРЕСТУПНИК", f, C.WHITE + (a,), 0.06, "ls")
        C.tracked(d, x, (H * 0.48 + 178) * SS, "для других", f2, C.GREY + (a,), 0.3, "ls")
    # тонкая красная черта между половинами — сама линия раздела
    kl = C.smoother(C.seg(tt, 0.3, 1.2))
    d.rectangle([(W / 2 - 1) * SS, (H / 2 - 260 * kl) * SS, (W / 2 + 1) * SS, (H / 2 + 260 * kl) * SS], fill=C.RED + (200,))
    img = C.over(img, lay).convert("RGB")
    img = C.over(img, C.caption("Генри Киссинджер", "госсекретарь США · 1973", "портрет Госдепартамента", C.seg(tt, 0.4, 1.2))).convert("RGB")
    return C.finish(img, t, dur, fi=0.0, fo=0.6, grain_k=0.03)


# ───────────────────────── 07 · Прогноз или чертёж ─────────────────────────
_s07 = {}


@scene("07")
def s07(t, dur):
    cam = ZK.Cam(x=0.15, y=1.35, z=0.11 * t)
    img = ZK.hall(cam)
    if not _s07:
        _s07["a"] = ZK.word_tex("ПРОГНОЗ", 320)
        _s07["b"] = ZK.word_tex("ЧЕРТЁЖ", 320)
    t_sw = C.cue("07", "он сам всё это устраивал", 7.0) + 2.6   # «Так и есть» → смена
    k_a_up = C.seg(t, 0.3, 1.1)
    k_a_out = C.seg(t, t_sw, t_sw + 0.9)
    k_b_up = C.seg(t, t_sw + 0.5, t_sw + 1.2)
    ZK.standing(img, cam, _s07["a"], 0.0, 9.5, 1.25, k_a_up, k_a_out, depth=0.09)
    ZK.standing(img, cam, _s07["b"], 0.0, 9.5, 1.25, k_b_up, 0.0, depth=0.09)
    img = ZK.Z.embers(img, cam, ZK.Z.cluster(2.6, 0.3, 11.0, 0.5, 3, 4) + ZK.Z.cluster(-3.0, 0.2, 13.0, 0.5, 3, 5), t)
    img = img.convert("RGB")
    return C.finish(img, t, dur, fi=0.5, fo=0.6, grain_k=0.02)


# ───────────────────────── 08 · Разведка, Петербург ─────────────────────────
_s08 = {}


def light_sweep(img, t, k=0.5):
    """светотень: мягкий луч идёт по кадру слева направо"""
    import numpy as np
    a = np.asarray(img.convert("RGB"), np.float32)
    xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    pos = 0.15 + 0.7 * C.smoother(t)
    band = np.exp(-((xx - pos) / 0.28) ** 2)
    g = 0.72 + 0.55 * band
    a *= g[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


@scene("08")
def s08(t, dur):
    if "p" not in _s08:
        import os
        for nm in ("kissinger_petersburg_199x.jpg", "kremlin_kissinger_2012_a.jpg", "kissinger_portrait_late.jpg"):
            if os.path.exists(C.apath(nm)):
                _s08["p"] = C.foto(nm)
                _s08["name"] = nm
                break
        else:
            _s08["p"] = C.foto("kissinger_petersburg_199x.jpg")
            _s08["name"] = "kissinger_petersburg_199x.jpg"
    # медленный push + короткий punch на реплике Киссинджера
    tp = C.cue("08", "Киссинджер отвечает", 11.0)
    punch = 0.04 * (1 - C.out_expo(C.seg(t, tp, tp + 0.5))) if t >= tp else 0.0
    z = 0.07 * (t / dur) + (0.04 - punch if t >= tp else 0.0)
    img = C.kb(_s08["p"].convert("L").convert("RGB"), 1.0, z, 0.5, 0.35)
    img = light_sweep(img, t / dur)
    img = C.vignette(img, 0.6)
    if _s08["name"].startswith("kissinger_petersburg"):
        cap = C.caption("Санкт-Петербург", "начало девяностых", "фото архива", C.seg(t, 1.0, 1.8))
    else:
        cap = C.caption("Санкт-Петербург", "ПМЭФ · июнь 2012", "kremlin.ru", C.seg(t, 1.0, 1.8))
    img = C.over(img, cap).convert("RGB")
    return C.finish(img, t, dur, fi=0.6, fo=0.6, grain_k=0.04)


# ───────────────────────── 09 · 1994: НАТО на восток ─────────────────────────
_s09 = {}


@scene("09")
def s09(t, dur):
    if "m" not in _s09:
        _s09["m"] = K.world(lon=(-14, 46), lat=(34, 64))
        _s09["base"] = _s09["m"].render()
    m = _s09["m"]
    base = _s09["base"].copy()
    lays = []
    cities = [("Варшава", 21.01, 52.23, "Польша"), ("Прага", 14.42, 50.09, "Чехия"), ("Будапешт", 19.04, 47.50, "Венгрия")]
    t0 = C.cue("09", "Польши", 4.5)
    for i, (n, lon, lat, sub) in enumerate(cities):
        k = C.seg(t, t0 + i * 0.9, t0 + i * 0.9 + 0.6)
        if k > 0:
            lays.append(m.marker((W, H), n, lon, lat, sub, k=k, px=26, ring=C.seg(t, t0 + i * 0.9, t0 + i * 0.9 + 1.4)))
    # Москва для масштаба, серым
    lays.append(m.marker((W, H), "Москва", 37.62, 55.75, None, k=C.seg(t, 0.5, 1.2), px=22))
    lays.append(K.date_tag("1994", C.seg(t, 0.8, 1.8), sub="НАТО идёт на восток"))
    img = C.over(base, *lays).convert("RGB")
    return C.finish(img, t, dur, fi=0.6, fo=0.6, grain_k=0.03, vig=0.3)
