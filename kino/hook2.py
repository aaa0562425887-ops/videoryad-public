#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Второй отрезок 1:10 → 4:18 — сцены 05-12 заново по журналу 19.11 (п.40),
тем же методом, что hook.py: планы ≤5 с, живое видео архива, карты рисуются,
зал убран, текст в полях. Сцена 13 (вставка WEF 2023) не трогается — одобрена.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import karta as K
import scenes_a as A
import scenes_b as B
import hook as Hk
from core import W, H, SS
from cuts import CUTS

scene = A.scene
vid, foto_bw, shots, flash, modern, chronicle = Hk.vid, Hk.foto_bw, Hk.shots, Hk.flash, Hk.modern, Hk.chronicle
word, red_line, fit_px, dark_video = Hk.word, Hk.red_line, Hk.fit_px, Hk.dark_video
SAFE_X = Hk.SAFE_X
_c = {}


def cap(*a, **kw):
    return C.caption(*a, **kw)


def act(num, name, t, d):
    """титр акта: короткий, номер садится, черта рисуется"""
    img = Image.new("RGB", (W, H), (6, 6, 7))
    doc = C.paper(W, H, seed=11, tone=(70, 66, 60)).filter(ImageFilter.GaussianBlur(5))
    img = C.kb(Image.blend(img, doc, 0.22), t / d, 0.04, 0.5, 0.5)
    k = C.seg(t, 0.0, 0.45)
    px = int(300 * (1.3 - 0.3 * C.out_cubic(k)))
    lay = C.layer()
    dd = ImageDraw.Draw(lay)
    fn = C.font("serif_b", px * SS)
    tw = C.text_w(dd, num, fn)
    dd.text((W / 2 * SS - tw / 2, (H / 2 + 20) * SS), num, font=fn, fill=(0, 0, 0, 0),
            stroke_width=3 * SS, stroke_fill=C.GREY + (int(255 * k),), anchor="ls")
    img = C.over(img, lay, word(name, C.seg(t, 0.25, 0.7), H / 2 + 110, 54, "head_l", C.WHITE, 0.32, rise=20),
                 red_line(C.seg(t, 0.5, 1.0), W / 2 - 40, W / 2 + 40, H / 2 + 150, 3))
    return C.grain(img.convert("RGB"), t, 0.03)


def lines_in(lines, t, kind="serif_i", px=60, x=W / 2, y=H * 0.40, anchor="ms", color=C.WHITE, lead=1.35, track=0.0):
    """строки появляются по своему времени: lines = [(t0, текст), …]"""
    out = []
    px = min([px] + [fit_px(s, kind, px, W - 2 * SAFE_X, track) for _, s in lines])
    for i, (t0, s) in enumerate(lines):
        k = C.seg(t, t0, t0 + 0.45)
        if k > 0:
            out.append(C.text_layer([s], kind, px, color, x, y + i * px * lead + (1 - C.out_cubic(k)) * 24, anchor, track, a=k))
    return out


def num_tag(n, k, x=SAFE_X + 10, y=150):
    """номер тезиса: красная цифра и тонкая черта"""
    if k <= 0:
        return None
    im = C.layer()
    d = ImageDraw.Draw(im)
    a = int(255 * C.smoother(k))
    C.tracked(d, x * SS, y * SS, n, C.font("head", 72 * SS), C.RED + (a,), 0.04)
    d.rectangle([x * SS, (y + 12) * SS, (x + 60) * SS, (y + 15) * SS], fill=C.WHITE + (a,))
    return C.done(im)


def tv(img, frame, k=1.0, cx=W * 0.40, cy=H * 0.50, w_px=1180, yaw=26.0):
    """телевизор наискосок в тёмной комнате: экран в перспективе, свечение, отражение на полу"""
    import zal_kino as ZK
    h_px = w_px * 9 / 16
    f = math.cos(math.radians(yaw))
    near, far = 1.0 + (1 - f) * 0.42, 1.0 - (1 - f) * 0.42
    xl, xr = cx - w_px / 2 * f, cx + w_px / 2 * f
    hl, hr = h_px * near, h_px * far
    pts = [(xl, cy - hl / 2), (xr, cy - hr / 2), (xr, cy + hr / 2), (xl, cy + hl / 2)]
    img = img.convert("RGBA")
    # свечение экрана на стене
    glow, pad = C.shadow_box((int(xr - xl), int(h_px)), blur=70, a=int(120 * k))
    g = glow.split()[3]
    glow = Image.merge("RGBA", (Image.new("L", g.size, 190), Image.new("L", g.size, 192), Image.new("L", g.size, 200), g))
    img.alpha_composite(glow, (int(xl - pad), int(cy - h_px / 2 - pad)))
    # отражение на полу: перевёрнутый кадр, тёмный, под экраном
    refl = frame.transpose(Image.FLIP_TOP_BOTTOM).convert("RGBA")
    refl.putalpha(int(70 * k))
    rp = [(xl, cy + hl / 2 + 10), (xr, cy + hr / 2 + 10), (xr, cy + hr / 2 + hr * 0.7), (xl, cy + hl / 2 + hl * 0.7)]
    ZK.Z.paste_quad(img, refl, rp)
    # рамка
    bez = Image.new("RGBA", (frame.size[0] + 40, frame.size[1] + 40), (22, 22, 25, int(255 * k)))
    bp = [(x + (-22 if i in (0, 3) else 22), y + (-22 if i in (0, 1) else 22)) for i, (x, y) in enumerate(pts)]
    ZK.Z.paste_quad(img, bez, bp)
    fr = frame.convert("RGBA")
    fr.putalpha(int(255 * k))
    ZK.Z.paste_quad(img, fr, pts)
    return img.convert("RGB")


def room(t, seed=41):
    """тёмная комната: стена с градиентом, пол чуть светлее"""
    key = ("room", seed)
    if key not in _c:
        a = np.zeros((H, W, 3), np.float32)
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        wall = 14 + 10 * np.exp(-((yy - 0.45) / 0.35) ** 2)
        a[:, :, :] = wall[:, :, None]
        a[int(H * 0.72):, :, :] += 6
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
        im = Image.blend(im, C.paper(W, H, seed=seed, tone=(26, 25, 28)), 0.35)
        _c[key] = C.vignette(im, 0.5)
    return _c[key].copy()


def strip_photos(items, key, fw=560, fh=400, gap=44):
    """лента: кадры с годами в одном слое (кэш)"""
    if key in _c:
        return _c[key]
    total = len(items) * (fw + gap)
    lay = Image.new("RGBA", (total, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y0 = int(H / 2 - fh / 2) - 20
    f_year = C.font("head", 44)
    f_lab = C.font("head_l", 22)
    for i, (name, year, label) in enumerate(items):
        ph = C.cover(C.foto(name), (fw, fh), 0.5, 0.25).convert("L").convert("RGB")
        card = Image.new("RGB", (fw + 6, fh + 6), C.GREY2)
        card.paste(ph, (3, 3))
        x = i * (fw + gap)
        lay.paste(card, (x, y0))
        d.text((x + 4, y0 + fh + 24), year, font=f_year, fill=C.WHITE)
        d.text((x + 4, y0 + fh + 76), label.upper(), font=f_lab, fill=C.GREY)
        d.rectangle([x + 4, y0 + fh + 70, x + 70, y0 + fh + 72], fill=C.RED)
    _c[key] = lay
    return lay


def truck(items, key, k, t):
    """лента едет линейно справа налево через весь кадр"""
    lay = strip_photos(items, key)
    total = lay.size[0]
    x = W * 0.55 + (W * 0.45 - total - W * 0.55) * k
    img = Image.new("RGB", (W, H), C.BG)
    pap = C.paper(W + 300, H, seed=29, tone=(30, 29, 32)).filter(ImageFilter.GaussianBlur(1.5))
    img.paste(pap, (int(-300 * k), 0))
    img.paste(lay, (int(x), 0), lay)
    img = A.light_sweep(img, k)
    return C.vignette(img, 0.35)


_world = {}


def world_map(key, lon, lat):
    if key not in _world:
        m = K.world(lon=lon, lat=lat)
        _world[key] = (m, m.render())
    m, base = _world[key]
    return m, base.copy()


# ═════════════════════════ 05 · Советник → госсекретарь → Пекин ═════════════════════════
@scene("05")
def s05(t, dur):
    c_gos = C.cue("05", "затем госсекретарь", 2.8)
    c_71 = C.cue("05", "Это он в семьдесят первом", 6.2)
    c_mao = C.cue("05", "Пекин и подготовил", 8.4)

    def sovetnik(tt, d):
        img = C.kb(foto_bw("kissinger_portrait_1973.jpg"), tt / d, 0.07, 0.5, 0.3)
        img = C.film_look(img, t, 0.4, scratches=False)
        return C.over(img, word("СОВЕТНИК НИКСОНА", C.seg(tt, 0.2, 0.7), H * 0.80, 110),
                      cap("Генри Киссинджер", "Белый дом · 1969", "портрет Госдепартамента", C.seg(tt, 0.3, 0.9), y=140))

    def gossek(tt, d):
        img = C.kb(foto_bw("kissinger_le_duc_tho_1973.jpg"), tt / d, 0.09, 0.5, 0.3)
        img = C.film_look(img, t, 0.45, scratches=False)
        return flash(C.over(img, word("ГОССЕКРЕТАРЬ", C.seg(tt, 0.1, 0.6), H * 0.80, 110),
                            cap("Генри Киссинджер", "Белый дом · 1973", "фото архива", C.seg(tt, 0.3, 0.9), y=140)), tt, 0.08, 0.5)

    def pekin(tt, d):
        img = C.kb(foto_bw("kissinger_zhou_1971.jpg"), tt / d, 0.09, 0.5, 0.4)
        img = C.film_look(img, t, 0.5, scratches=False)
        return C.over(img, K.date_tag("1971", C.seg(tt, 0.1, 0.6), sub="тайный визит в Пекин"),
                      cap("Пекин", "июль 1971 · с Чжоу Эньлаем", "Национальный архив США", C.seg(tt, 0.3, 0.9)))

    def mao(tt, d):
        fr = vid("nm72", "nixon_1972_mao.mp4", 15.0).at(tt)
        img = chronicle(C.kb(fr, tt / d, 0.06, 0.5, 0.4), t, 0.7)
        return C.over(img, K.date_tag("1972", C.seg(tt, 0.1, 0.6), sub="визит Никсона в Китай"),
                      cap("Китай · Никсон и Чжоу Эньлай", "февраль 1972", "Библиотека Никсона", C.seg(tt, 0.3, 0.9)))

    fn, tt, d = shots(t, [(0.0, sovetnik), (c_gos, gossek), (c_71, pekin), (c_mao, mao)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0)


# ═════════════════════════ 06 · Премия без мира · два полюса · полвека ═════════════════════════
STRIP06 = [("kissinger_zhou_1971.jpg", "1971", "Пекин"), ("kissinger_sadat_197x.jpg", "1970-е", "Ближний Восток"),
           ("kremlin_kissinger_2008_a.jpg", "2008", "Москва"), ("kremlin_kissinger_2017_a.jpg", "2017", "Кремль"),
           ("kissinger_100_2023.jpg", "2023", "сто лет")]


@scene("06")
def s06(t, dur):
    c_tho = C.cue("06", "и это его вьетнамский партнёр", 4.7)
    c_war = C.cue("06", "потому что война", 9.1)
    c_pol = C.cue("06", "Отношение к нему полярное", 11.5)
    c_dip = C.cue("06", "Для одних он главный", 14.3)
    c_crim = C.cue("06", "для других военный", 16.1)
    c_kamb = C.cue("06", "Камбоджи", 18.3)
    c_chile = C.cue("06", "переворот в Чили", 19.0)
    c_half = C.cue("06", "полвека его оценки", 21.7)

    def nobel(tt, d):
        fr = vid("nobel", "nobel_1973.mp4", 0.0, zoom=1.16, cx=0.0, cy=1.0).at(tt)
        img = chronicle(C.kb(fr, tt / d, 0.05, 0.5, 0.4), t, 0.8)
        return C.over(img, K.date_tag("1973", C.seg(tt, 0.1, 0.6), sub="Нобелевская премия мира"),
                      cap("Осло", "декабрь 1973", "AP Archive", C.seg(tt, 0.3, 0.9)))

    def tho(tt, d):
        img = A.quote_split(C.foto("le_duc_tho_1973.jpg"), "Ле Дык Тхо · отказ от премии", "Ханой · октябрь 1973",
                            ["Мир в Южном Вьетнаме", "ещё не установлен."], C.seg(tt, 0.0, 0.7), C.seg(tt, 0.5, 1.3))
        return C.grain(img, t, 0.03)

    def war(tt, d):
        fr = vid("nobel2", "nobel_1973.mp4", 14.0, zoom=1.16, cx=0.0, cy=1.0).at(tt)
        img = chronicle(C.kb(fr, tt / d, 0.06, 0.5, 0.5), t, 0.8)
        return flash(C.over(img, word("ВОЙНА НЕ КОНЧИЛАСЬ", C.seg(tt, 0.15, 0.65), H * 0.47, 150)), tt, 0.08, 0.5)

    def poles(tt, d):
        img = Image.new("RGB", (W, H), C.BG)
        ph = C.kb(foto_bw("kissinger_portrait_1973.jpg"), tt / d, 0.10, 0.5, 0.3, (int(W * 0.36), H))
        img.paste(ph, (int(W * 0.32), 0))
        img = A.light_sweep(img, tt / d)
        img = C.vignette(img, 0.5)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        f = C.font("head", 58 * SS)
        f2 = C.font("head_l", 28 * SS)
        ka = C.smoother(C.seg(tt, c_dip - c_pol, c_dip - c_pol + 0.5))
        kb_ = C.smoother(C.seg(tt, c_crim - c_pol, c_crim - c_pol + 0.5))
        if ka > 0:
            a = int(255 * ka)
            x = (W * 0.30 - 30 - (1 - ka) * 60) * SS
            for i, s in enumerate(["ГЛАВНЫЙ", "ДИПЛОМАТ", "ХХ ВЕКА"]):
                C.tracked(dd, x, (H * 0.44 + 64 * i) * SS, s, f, C.WHITE + (a,), 0.06, "rs")
            C.tracked(dd, x, (H * 0.44 + 178) * SS, "для одних", f2, C.GREY + (a,), 0.3, "rs")
        if kb_ > 0:
            a = int(255 * kb_)
            x = (W * 0.70 + 30 + (1 - kb_) * 60) * SS
            C.tracked(dd, x, (H * 0.44) * SS, "ВОЕННЫЙ", f, C.WHITE + (a,), 0.06, "ls")
            C.tracked(dd, x, (H * 0.44 + 64) * SS, "ПРЕСТУПНИК", f, C.WHITE + (a,), 0.06, "ls")
            C.tracked(dd, x, (H * 0.44 + 178) * SS, "для других", f2, C.GREY + (a,), 0.3, "ls")
            for j, (tc, s) in enumerate([(c_kamb, "Камбоджа · 1969-73"), (c_chile, "Чили · 1973")]):
                kk = C.seg(tt, tc - c_pol, tc - c_pol + 0.4)
                if kk > 0:
                    C.tracked(dd, x, (H * 0.44 + 230 + 40 * j) * SS, s, f2, C.WHITE + (int(255 * kk),), 0.16, "ls")
        kl = C.smoother(C.seg(tt, 0.2, 1.0))
        dd.rectangle([(W / 2 - 1) * SS, (H / 2 - 260 * kl) * SS, (W / 2 + 1) * SS, (H / 2 + 260 * kl) * SS], fill=C.RED + (200,))
        img = C.over(img, lay, cap("Генри Киссинджер", "госсекретарь США · 1973", "портрет Госдепартамента", C.seg(tt, 0.3, 1.0)))
        return C.grain(img.convert("RGB"), t, 0.03)

    def polveka(tt, d):
        img = truck(STRIP06, "s06", tt / d, t)
        return C.over(img, word("ПОЛВЕКА ПРОГНОЗОВ", C.seg(tt, 0.2, 0.7), 150, 56, "head_l", C.GREY, 0.3, rise=16)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, nobel), (c_tho, tho), (c_war, war), (c_pol, poles), (c_half, polveka)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0)


# ═════════════════════════ 07 · Прогноз или чертёж: телевизор в тёмной комнате ═════════════════════════
@scene("07")
def s07(t, dur):
    c_quote = C.cue("07", "Он не предсказывал", 2.0)
    c_sam = C.cue("07", "он сам всё это устраивал", 4.9)
    c_tak = C.cue("07", "Так и есть", 6.6)
    c_nabl = C.cue("07", "Киссинджер был не наблюдателем", 7.4)
    c_uch = C.cue("07", "а участником", 9.3)
    c_gl = C.cue("07", "и во многих сюжетах главным", 10.3)
    c_no = C.cue("07", "Но от этого", 12.0)
    c_chel = C.cue("07", "человек", 15.2)
    c_luch = C.cue("07", "лучше других знает", 17.7)
    c_slab = C.cue("07", "где у неё слабое место", 19.2)

    def televizor(tt, d):
        fr = vid("rose12", "charlie_rose_2012.mp4", 0.0, size=(1280, 720)).at(tt)
        fr = Hk.panel_look(fr, bw=True)
        img = tv(room(t), fr, 1.0, cx=W * 0.38 + 14 * C.smoother(tt / d), cy=H * 0.50, w_px=1150, yaw=24)
        lay = lines_in([(c_quote, "«Он не предсказывал —"), (c_sam, "он сам всё это устраивал»")], tt,
                       "serif_i", 54, W * 0.985 - SAFE_X, H * 0.40, "rs")
        lay += [word("ТАК И ЕСТЬ", C.seg(tt, c_tak, c_tak + 0.4), H * 0.40 + 170, 40, "head_l", C.GREY, 0.3, x=W - SAFE_X - 30, anchor="rs", rise=14)]
        lay += [cap("Генри Киссинджер", "интервью · 2012", "Charlie Rose", C.seg(tt, 0.4, 1.0))]
        return C.grain(C.over(img, *lay).convert("RGB"), t, 0.03)

    def nabl(tt, d):
        fr = vid("n72c", "nixon_1972_china.mp4", 1.0).at(tt)
        img = chronicle(C.kb(fr, tt / d, 0.06, 0.5, 0.4), t, 0.7)
        return flash(C.over(img, word("НЕ НАБЛЮДАТЕЛЬ", C.seg(tt, 0.1, 0.5), H * 0.47, 150),
                            cap("Пекин", "1972", "Библиотека Никсона", C.seg(tt, 0.3, 0.9))), tt, 0.08, 0.5)

    def uch(tt, d):
        fr = vid("xi_b", "kissinger_xi_2023_b.mp4", 6.0, zoom=1.28, cx=1.0, cy=0.55).at(tt)
        img = modern(C.kb(fr, tt / d, 0.05, 0.5, 0.4), t)
        return C.over(img, word("УЧАСТНИК", C.seg(tt, 0.1, 0.5), H * 0.47, 150),
                      cap("Пекин · с Си Цзиньпином", "июль 2023", "CGTN", C.seg(tt, 0.3, 0.9)))

    def glav(tt, d):
        img = C.kb(foto_bw("kissinger_sadat_197x.jpg"), tt / d, 0.09, 0.5, 0.3)
        img = C.film_look(img, t, 0.5, scratches=False)
        return C.over(img, word("ГЛАВНЫЙ", C.seg(tt, 0.1, 0.5), H * 0.47, 190),
                      cap("Каир · с Анваром Садатом", "1970-е", "Библиотека Конгресса", C.seg(tt, 0.3, 0.9)))

    def vesomee(tt, d):
        fr = vid("k100b", "kissinger_100_2023.mp4", 30.0).at(tt)
        img = C.kb(fr.convert("L").convert("RGB"), tt / d, 0.06, 0.5, 0.4)
        img = C.film_look(img, t, 0.4, scratches=False)
        lay = lines_in([(c_chel - c_no, "человек, который строил систему,"), (c_luch - c_no - 0.01, "лучше других знает её слабое место")],
                       tt, "serif_i", 50, W / 2, H * 0.78, "ms")
        return C.over(img, *lay, cap("Генри Киссинджер", "100 лет · май 2023", "CBS", C.seg(tt, 0.3, 0.9), y=140))

    def slaboe(tt, d):
        m, base = world_map("w1", (-130, 150), (-5, 72))
        pts = [("Вашингтон", -77.04, 38.9), ("Москва", 37.62, 55.75), ("Пекин", 116.4, 39.9), ("Киев", 30.52, 50.45)]
        lays = []
        for i, (n, lon, lat) in enumerate(pts):
            k = C.seg(tt, 0.1 + i * 0.3, 0.6 + i * 0.3)
            if k > 0:
                lays.append(m.marker((W, H), n, lon, lat, None, k=k, px=24, ring=C.seg(tt, 0.1 + i * 0.3, 1.2 + i * 0.3)))
        img = C.over(base, *lays, word("ГДЕ У НЕЁ СЛАБОЕ МЕСТО", C.seg(tt, c_slab - c_luch, c_slab - c_luch + 0.5), H * 0.86, 72)).convert("RGB")
        return C.grain(C.kb(img, tt / d, 0.05, 0.5, 0.5), t, 0.03)

    fn, tt, d = shots(t, [(0.0, televizor), (c_nabl, nabl), (c_uch, uch), (c_gl, glav), (c_no, vesomee), (c_luch, slaboe)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0)


# ═════════════════════════ 08 · Разведка, Петербург ═════════════════════════
@scene("08")
def s08(t, dur):
    c_90 = C.cue("08", "Начало девяностых", 4.0)
    c_priz = C.cue("08", "что до этого служил", 10.1)
    c_otv = C.cue("08", "Киссинджер отвечает", 12.0)
    c_vse = C.cue("08", "что все приличные люди", 13.5)
    c_sam = C.cue("08", "и он сам тоже", 16.3)
    c_zap = C.cue("08", "Эту сцену стоит запомнить", 19.3)
    c_kreml = C.cue("08", "почему в Кремле", 22.0)

    def putin(tt, d):
        fr = vid("putin2", "ap_putin_kissinger.mp4", 12.0, zoom=1.16, cx=0.0, cy=1.0).at(tt)
        img = modern(C.kb(fr, tt / d, 0.06, 0.45, 0.4), t, 0.3)
        return C.over(img, cap("Москва, Кремль", "Путин и Киссинджер · архив", "AP", C.seg(tt, 0.3, 0.9)))

    def piter(tt, d):
        img = C.kb(foto_bw("kremlin_kissinger_2012_a.jpg"), tt / d, 0.08, 0.5, 0.35)
        img = C.film_look(img, t, 0.4, scratches=False)
        return flash(C.over(img, K.date_tag("1990-е", C.seg(tt, 0.1, 0.6), sub="Петербург, мэрия"),
                            cap("Санкт-Петербург", "ПМЭФ · июнь 2012", "kremlin.ru", C.seg(tt, 0.3, 0.9))), tt, 0.08, 0.5)

    def priznanie(tt, d):
        img = dark_video(C.kb(foto_bw("kremlin_kissinger_2012_b.jpg"), tt / d, 0.06, 0.5, 0.4), 0.35)
        lay = lines_in([(0.1, "— До этого я служил в разведке.")], tt, "serif_i", 66, W / 2, H * 0.50, "ms")
        return C.over(img, *lay)

    def otvet(tt, d):
        img = C.kb(foto_bw("kissinger_portrait_late.jpg"), tt / d, 0.08, 0.5, 0.3)
        img = dark_video(C.film_look(img, t, 0.35, scratches=False), 0.6)
        lay = lines_in([(c_vse - c_otv, "— Все приличные люди начинали в разведке."), (c_sam - c_otv, "И я тоже.")],
                       tt, "serif_i", 60, W / 2, H * 0.70, "ms")
        return C.over(img, *lay)

    def medvedev(tt, d):
        fr = vid("medv", "ap_kissinger_medvedev.mp4", 14.0, zoom=1.16, cx=0.0, cy=1.0).at(tt)
        img = modern(C.kb(fr, tt / d, 0.06, 0.5, 0.4), t, 0.3)
        return C.over(img, cap("Москва", "Медведев и Киссинджер · архив", "AP", C.seg(tt, 0.3, 0.9)))

    def kreml(tt, d):
        img = C.kb(foto_bw("kremlin_kissinger_2016_b.jpg"), tt / d, 0.09, 0.5, 0.35)
        img = C.film_look(img, t, 0.35, scratches=False)
        return C.over(img, K.date_tag("2016", C.seg(tt, 0.1, 0.6), sub="Кремль · ему девяносто три"),
                      cap("Москва, Кремль", "февраль 2016", "kremlin.ru", C.seg(tt, 0.3, 0.9)))

    fn, tt, d = shots(t, [(0.0, putin), (c_90, piter), (c_priz, priznanie), (c_otv, otvet), (c_zap, medvedev), (c_kreml, kreml)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0)


# ═════════════════════════ 09 · 1994: НАТО на восток ═════════════════════════
@scene("09")
def s09(t, dur):
    c_dv = C.cue("09", "двигать ли НАТО", 3.1)
    c_drug = C.cue("09", "Другом Москвы", 8.7)
    c_rab = C.cue("09", "Он работал на интересы", 10.6)

    def budapest(tt, d):
        if "bud" not in _c:
            _c["bud"] = C.cover(C.foto("budapest_1994_1.png"), (W, H), 0.5, 0.15)
        img = C.kb(_c["bud"], tt / d, 0.08, 0.5, 0.2)
        img = C.vignette(img, 0.55)
        return C.over(img, K.date_tag("1994", C.seg(tt, 0.1, 0.6), sub="Вашингтон решает"),
                      cap("Будапештский меморандум", "декабрь 1994", "Договорная серия ООН", C.seg(tt, 0.3, 0.9)))

    def nato(tt, d):
        m, base = world_map("eu", (-14, 46), (34, 64))
        cities = [("Варшава", 21.01, 52.23, "Польша"), ("Прага", 14.42, 50.09, "Чехия"), ("Будапешт", 19.04, 47.50, "Венгрия")]
        t0 = C.cue("09", "Польши", 5.1) - c_dv
        lays = [m.marker((W, H), "Москва", 37.62, 55.75, None, k=C.seg(tt, 0.3, 0.9), px=22)]
        for i, (n, lon, lat, sub) in enumerate(cities):
            k = C.seg(tt, t0 + i * 0.9, t0 + i * 0.9 + 0.5)
            if k > 0:
                lays.append(m.marker((W, H), n, lon, lat, sub, k=k, px=26, ring=C.seg(tt, t0 + i * 0.9, t0 + i * 0.9 + 1.4)))
        lays.append(K.date_tag("1994", C.seg(tt, 0.0, 0.5), sub="НАТО идёт на восток"))
        lays += lines_in([(c_drug - c_dv, "ДРУГОМ МОСКВЫ НЕ БЫЛ НИКОГДА"), (c_rab - c_dv, "работал на интересы Америки — как он их понимал")],
                         tt, "head_r", 44, SAFE_X + 20, H * 0.80, "ls", track=0.08)
        img = C.over(base, *lays).convert("RGB")
        return C.grain(C.kb(img, C.smoother(tt / d), 0.08, 0.45, 0.45), t, 0.03)

    fn, tt, d = shots(t, [(0.0, budapest), (c_dv, nato)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0)


# ═════════════════════════ 10 · 2014: начните с конца ═════════════════════════
T_ACT10 = 1.2


def crimea_map(tt, d, k_zone, tag=None, extra=()):
    base = K.base()
    lays = [K.zone_layer(K.CRIMEA, k_zone, fill_a=110, outline=True),
            K.city_layer(["Севастополь", "Херсон", "Одесса"], C.seg(tt, 0.4, 1.0), side={"Севастополь": "l", "Одесса": "l"})]
    if tag:
        lays.append(tag)
    img = C.over(base, *lays).convert("RGB")
    img = C.kb(img, 0.6 + 0.4 * C.smoother(tt / d), 0.9, 0.56, 0.86)
    return C.grain(C.over(img, *extra).convert("RGB"), t_dummy(tt), 0.03)


def t_dummy(tt):
    return tt


@scene("10")
def s10(t, dur):
    c_krym = C.cue("10", "Крым только что перешёл", 0.8)
    c_zap = C.cue("10", "западные столицы", 4.3)
    c_pub = C.cue("10", "Киссинджер публикует", 6.0)
    c_zag = C.cue("10", "Чтобы разрешить украинский", 10.3)
    c_nach = C.cue("10", "начните с конца", 12.2)
    c_smysl = C.cue("10", "Смысл в названии", 13.8)
    c_itog = C.cue("10", "каким должен быть итог", 16.3)
    c_sank = C.cue("10", "и только потом вводите санкции", 17.7)

    def title(tt, d):
        return act("II", "ЛИНИЯ", tt, d)

    def krym(tt, d):
        return crimea_map(tt, d, C.seg(tt, 0.2, 1.4), K.date_tag("март 2014", C.seg(tt, 0.1, 0.6), sub="Крым под контролем России"))

    def rasteryannost(tt, d):
        fr = vid("rose14", "charlie_rose_2014.mp4", 4.0).at(tt)
        img = C.film_look(C.kb(fr.convert("L").convert("RGB"), tt / d, 0.06, 0.5, 0.4), t, 0.3, scratches=False)
        return flash(C.over(img, cap("Генри Киссинджер", "6 марта 2014", "Charlie Rose", C.seg(tt, 0.3, 0.9))), tt, 0.08, 0.5)

    def gazeta(tt, d):
        if "page" not in B._s10:
            B._s10["page"] = B.newspaper_page()
        page = B._s10["page"]
        k1 = C.smoother(C.seg(tt, 0.0, 3.0))
        k2 = C.smoother(C.seg(tt, c_zag - c_pub, c_nach - c_pub + 0.4))
        scale = C.lerp(0.72, 1.35, k1) * C.lerp(1.0, 1.55, k2)
        cx = C.lerp(1300, 900, k1) * (1 - k2) + 760 * k2
        cy = C.lerp(900, 420, k1) * (1 - k2) + 440 * k2
        pw, ph = int(page.size[0] * scale), int(page.size[1] * scale)
        big = page.resize((pw, ph), Image.LANCZOS)
        x0 = int(cx * scale - W / 2)
        y0 = int(cy * scale - H / 2)
        img = Image.new("RGB", (W, H), (40, 38, 36))
        img.paste(big, (-x0, -y0))
        km = C.seg(tt, c_nach - c_pub + 0.1, c_nach - c_pub + 1.2)
        if km > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dl = ImageDraw.Draw(lay)
            ax = (140 - cx) * scale + W / 2
            bx = (140 + 1040 * C.out_cubic(km) - cx) * scale + W / 2
            ay = (392 - cy) * scale + H / 2
            by = (496 - cy) * scale + H / 2
            dl.rectangle([ax, ay, bx, by], fill=(255, 214, 0, 95))
            img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
        img = C.vignette(img, 0.45)
        return C.grain(C.over(img, cap("The Washington Post", "5 марта 2014", "колонка Генри Киссинджера", C.seg(tt, 0.6, 1.4))).convert("RGB"), t, 0.03)

    def smysl(tt, d):
        # фон — та же газетная полоса, притушенная и медленно плывущая (пустого кадра нет)
        if "page" not in B._s10:
            B._s10["page"] = B.newspaper_page()
        page = B._s10["page"]
        pg = page.crop((0, 150, page.size[0], 150 + int(page.size[0] * 9 / 16))).resize((W, H), Image.LANCZOS)
        img = dark_video(C.kb(pg.filter(ImageFilter.GaussianBlur(2)), tt / d, 0.08, 0.3, 0.3), 0.28)
        k1, k2 = C.seg(tt, c_itog - c_smysl, c_itog - c_smysl + 0.5), C.seg(tt, c_sank - c_smysl, c_sank - c_smysl + 0.5)
        return C.over(img, C.alpha(word("СМЫСЛ — В НАЗВАНИИ", C.seg(tt, 0.1, 0.5), H * 0.42, 110, "head_l", C.GREY, 0.1), 1 - k1),
                      word("СНАЧАЛА — ИТОГ", k1, H * 0.42, 150),
                      red_line(C.seg(tt, c_itog - c_smysl + 0.3, c_itog - c_smysl + 1.0), W / 2 - 160, W / 2 + 160, H * 0.42 + 40, 5),
                      word("ПОТОМ — САНКЦИИ", k2, H * 0.42 + 190, 110, "head_l", C.GREY, 0.1))

    fn, tt, d = shots(t, [(0.0, title), (T_ACT10, krym), (c_zap, rasteryannost), (c_pub, gazeta), (c_smysl, smysl)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0)


# ═════════════════════════ 11 · Три тезиса ═════════════════════════
BRIDGE = [(22.5, 48.6), (25.0, 49.2), (28.0, 49.6), (31.0, 49.9), (34.0, 49.7), (37.0, 49.4), (40.0, 49.2)]


@scene("11")
def s11(t, dur):
    c_forp = C.cue("11", "форпостом", 3.9)
    c_zapad = C.cue("11", "ни западным", 4.8)
    c_ross = C.cue("11", "ни российским", 6.7)
    c_most = C.cue("11", "мост", 9.2)
    c_vtor = C.cue("11", "Второй Украине не следует", 9.6)
    c_fin = C.cue("11", "Финляндия", 14.0)
    c_vne = C.cue("11", "военно вне блоков", 16.5)
    c_tret = C.cue("11", "Третий", 17.5)
    c_dem = C.cue("11", "демонизация Путина", 18.5)
    c_nepol = C.cue("11", "это не политика", 20.9)
    c_alibi = C.cue("11", "а алиби", 22.2)
    c_tam = C.cue("11", "Там же он", 23.5)
    c_krym = C.cue("11", "назвал присоединение Крыма", 24.5)
    c_neopr = C.cue("11", "Он не оправдывал Москву", 28.0)
    c_kto = C.cue("11", "не кто прав", 30.8)
    c_chem = C.cue("11", "а чем это закончится", 32.4)

    def most(tt, d):
        base = K.base()
        lays = [num_tag("01", C.seg(tt, 0.0, 0.5)),
                K.city_layer(["Киев"], C.seg(tt, 0.3, 0.8))]
        kf = C.seg(tt, c_forp, c_forp + 0.5)
        km = C.seg(tt, c_most, c_most + 1.2)
        if kf > 0 and km < 1:
            lays.append(C.alpha(word("НЕ ФОРПОСТ", kf, H * 0.80, 110, x=W / 2, rise=20), 1 - C.seg(tt, c_most, c_most + 0.4)))
        lays += lines_in([(c_zapad, "← ЗАПАД")], tt, "head_r", 40, SAFE_X + 20, H * 0.52, "ls", C.GREY, track=0.2)
        lays += lines_in([(c_ross, "РОССИЯ →")], tt, "head_r", 40, W - SAFE_X - 20, H * 0.52, "rs", C.GREY, track=0.2)
        if km > 0:
            lays.append(K.line_layer(BRIDGE, km, width=6, dash=None, head=True))
            lays.append(word("МОСТ", C.seg(tt, c_most + 0.3, c_most + 0.8), H * 0.80, 130))
        img = C.over(base, *lays).convert("RGB")
        return C.grain(C.kb(img, C.smoother(tt / d), 0.06, 0.5, 0.5), t, 0.03)

    def finland(tt, d):
        m, base = world_map("fin", (-14, 46), (34, 72))
        lays = [num_tag("02", C.seg(tt, 0.0, 0.5)),
                m.marker((W, H), "Киев", 30.52, 50.45, "Украина", k=C.seg(tt, 0.3, 0.8), px=24)]
        kf = C.seg(tt, c_fin - c_vtor, c_fin - c_vtor + 0.5)
        if kf > 0:
            lays.append(m.marker((W, H), "Хельсинки", 24.94, 60.17, "Финляндия", k=kf, px=26, ring=C.seg(tt, c_fin - c_vtor, c_fin - c_vtor + 1.4)))
        lays += lines_in([(c_vtor - c_vtor + 0.2, "НЕ В НАТО"), (c_fin - c_vtor, "образец — Финляндия"), (c_vne - c_vtor, "экономически в Европе, военно вне блоков")],
                         tt, "head_r", 46, SAFE_X + 20, H * 0.72, "ls", track=0.08)
        img = C.over(base, *lays).convert("RGB")
        return C.grain(C.kb(img, C.smoother(tt / d), 0.06, 0.45, 0.4), t, 0.03)

    def alibi(tt, d):
        fr = vid("putin3", "ap_putin_kissinger.mp4", 16.0, zoom=1.16, cx=0.0, cy=1.0).at(tt)
        img = dark_video(modern(C.kb(fr, tt / d, 0.06, 0.45, 0.4), t, 0.3), 0.55)
        lays = [num_tag("03", C.seg(tt, 0.0, 0.5))]
        lays += lines_in([(c_dem - c_tret, "ДЕМОНИЗАЦИЯ ПУТИНА —"), (c_nepol - c_tret, "НЕ ПОЛИТИКА,"), (c_alibi - c_tret, "А АЛИБИ ДЛЯ ЕЁ ОТСУТСТВИЯ")],
                         tt, "head", 84, W / 2, H * 0.36, "ms", track=0.06, lead=1.25)
        return C.over(img, *lays, cap("Москва, Кремль", "архив", "AP", C.seg(tt, 0.3, 0.9)))

    def krym(tt, d):
        k = C.seg(tt, c_krym - c_tam, c_krym - c_tam + 0.6)
        return crimea_map(tt, d, C.seg(tt, 0.0, 0.8), K.date_tag("2014", C.seg(tt, 0.1, 0.6), sub="колонка о Крыме"),
                          [word("КРЫМ: НЕСОВМЕСТИМО С МИРОВЫМ ПОРЯДКОМ", k, H * 0.30, 72)])

    def vopros(tt, d):
        fr = vid("rose14b", "charlie_rose_2014.mp4", 12.0).at(tt)
        img = dark_video(C.film_look(C.kb(fr.convert("L").convert("RGB"), tt / d, 0.06, 0.5, 0.4), t, 0.3, scratches=False), 0.6)
        return C.over(img, word("НЕ КТО ПРАВ", C.seg(tt, c_kto - c_neopr, c_kto - c_neopr + 0.5), H * 0.42, 130),
                      red_line(C.seg(tt, c_kto - c_neopr + 0.3, c_kto - c_neopr + 1.0), W / 2 - 120, W / 2 + 120, H * 0.42 + 40, 5),
                      word("А ЧЕМ ЭТО ЗАКОНЧИТСЯ", C.seg(tt, c_chem - c_neopr, c_chem - c_neopr + 0.5), H * 0.42 + 170, 110),
                      cap("Генри Киссинджер", "6 марта 2014", "Charlie Rose", C.seg(tt, 0.3, 0.9)))

    fn, tt, d = shots(t, [(0.0, most), (c_vtor, finland), (c_tret, alibi), (c_tam, krym), (c_neopr, vopros)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0)


# ═════════════════════════ 12 · Минск: линия, которая сместилась ═════════════════════════
@scene("12")
def s12(t, dur):
    c_pol = C.cue("12", "Через полгода после неё", 6.4)
    c_vtor = C.cue("12", "Затем второй Минск", 13.5)
    c_sem = C.cue("12", "Семь лет она стояла", 17.5)
    c_jump = C.cue("12", "сместилась на тысячу", 20.5)
    c_bez = C.cue("12", "Без этого факта", 23.0)
    c_slov = C.cue("12", "спор о словах", 28.0)
    c_pam = C.cue("12", "спор о памяти", 30.5)

    def detal(tt, d):
        if "page" not in B._s10:
            B._s10["page"] = B.newspaper_page()
        pg = B._s10["page"].resize((W, int(W * B._s10["page"].size[1] / B._s10["page"].size[0])), Image.LANCZOS)
        img = Image.new("RGB", (W, H), (40, 38, 36))
        img.paste(pg, (0, -200))
        img = dark_video(C.kb(img.filter(ImageFilter.GaussianBlur(3)), tt / d, 0.06, 0.5, 0.4), 0.45)
        lay = lines_in([(0.2, "деталь, которую обычно опускают")], tt, "serif_i", 64, W / 2, H * 0.50, "ms")
        return C.over(img, *lay)

    def karta(tt, d, nums=True):
        base = K.base()
        lays = []
        kj = C.seg(tt, c_jump - c_pol, c_jump - c_pol + 0.7)
        if kj <= 0:
            lays.append(K.line_layer(K.LINE_2015, C.seg(tt, 0.2, 3.2), width=5))
        else:
            lays.append(K.line_layer(B.morph_line(K.LINE_2015, list(reversed(K.LINE_NOW)), kj), 1.0, width=5, head=False))
        lays.append(K.city_layer(["Донецк", "Луганск", "Мариуполь"], C.seg(tt, 1.2, 2.0), side={"Мариуполь": "l"}))
        if kj <= 0:
            if tt < c_vtor - c_pol:
                lays.append(K.date_tag("сентябрь 2014", C.seg(tt, 0.3, 0.9), sub="Минск-1 · перемирие по линии"))
            else:
                lays.append(K.date_tag("февраль 2015", C.seg(tt, c_vtor - c_pol, c_vtor - c_pol + 0.5), sub="Минск-2 · линию зафиксировали"))
        else:
            lays.append(K.date_tag("2022", C.seg(tt, c_jump - c_pol, c_jump - c_pol + 0.5), sub="через семь лет"))
        k7 = C.seg(tt, c_sem - c_pol, c_sem - c_pol + 1.6)
        if nums and k7 > 0 and kj < 1:
            lays.append(C.alpha(C.big_number("7 ЛЕТ", "линия стояла", None, k7, cx=W * 0.27, cy=H * 0.42, px=230), 1 - kj))
        k1000 = C.seg(tt, c_jump - c_pol + 0.8, c_jump - c_pol + 2.6)
        if nums and k1000 > 0:
            lays.append(C.big_number("1000 КМ", "за несколько недель", "сдвиг линии на запад", k1000, cx=W * 0.27, cy=H * 0.42, px=230))
        img = C.over(base, *lays).convert("RGB")
        if 0 < kj < 1:
            sh = int(10 * (1 - kj) * math.sin(t * 90))
            img = img.transform(img.size, Image.AFFINE, (1, 0, sh, 0, 1, 0))
        return C.kb(img, C.smoother(tt / 25.0), 0.08, 0.66, 0.5)

    def minsk(tt, d):
        return C.grain(karta(tt, d), t, 0.03)

    def spor(tt, d):
        img = dark_video(karta(tt + (c_bez - c_pol), d, nums=False), 0.78)
        k0 = C.seg(tt, 0.1, 0.5) * (1 - C.seg(tt, c_slov - c_bez - 0.3, c_slov - c_bez))
        return C.over(img, word("БЕЗ ЭТОГО ФАКТА", k0, H * 0.42, 110, "head_l", C.GREY, 0.1),
                      word("СПОР О СЛОВАХ", C.seg(tt, c_slov - c_bez, c_slov - c_bez + 0.5), H * 0.42, 150),
                      red_line(C.seg(tt, c_pam - c_bez - 0.3, c_pam - c_bez + 0.4), W / 2 - 400, W / 2 + 400, H * 0.42 - 50, 9),
                      word("СПОР О ПАМЯТИ", C.seg(tt, c_pam - c_bez, c_pam - c_bez + 0.5), H * 0.42 + 170, 150))

    fn, tt, d = shots(t, [(0.0, detal), (c_pol, minsk), (c_bez, spor)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0)
