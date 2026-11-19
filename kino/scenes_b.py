#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Акт II · Линия: сцены 10–18."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import karta as K
import zal_kino as ZK
from core import W, H, SS
from cuts import CUTS, PEREVOD
from scenes_a import scene, SCENES  # общий реестр

def _read(name):
    p = C.apath(name)
    if os.path.exists(p):
        return open(p, encoding="utf-8", errors="replace").read()
    return None


# ───────────────────────── 10 · Колонка, 2014 ─────────────────────────
_s10 = {}


def newspaper_page():
    """газетная полоса: шапка, заголовок, подпись автора, колонки текста"""
    w, h = 2600, 1800
    im = C.paper(w, h, seed=31, tone=(226, 219, 203))
    d = ImageDraw.Draw(im)
    ink = C.INK
    # шапка
    fm = C.font("serif_b", 44)
    d.text((140, 90), "OPINIONS", font=fm, fill=ink)
    d.text((w - 140, 90), "WEDNESDAY, MARCH 5, 2014", font=C.font("serif", 34), fill=(90, 86, 80), anchor="ra")
    d.line([(140, 150), (w - 140, 150)], fill=ink, width=3)
    d.line([(140, 158), (w - 140, 158)], fill=ink, width=1)
    # заголовок
    fh = C.font("serif_b", 118)
    d.text((140, 250), "To settle the Ukraine crisis,", font=fh, fill=ink)
    d.text((140, 385), "start at the end", font=fh, fill=ink)
    fb = C.font("serif_i", 42)
    d.text((140, 545), "By Henry A. Kissinger", font=fb, fill=ink)
    d.line([(140, 610), (w - 140, 610)], fill=(120, 114, 104), width=1)
    # текст колонки — настоящий, если есть
    txt = _read("wapo_2014_03_05.txt")
    if txt:
        paras = [p.strip() for p in txt.split("\n") if len(p.strip()) > 40]
    else:
        paras = []
    ft = C.font("serif", 31)
    cols = 4
    cw = (w - 280 - (cols - 1) * 50) // cols
    x = 140
    y0 = 650
    y = y0
    ci = 0
    words_lines = []
    for p in paras[:14]:
        words_lines += C.wrap(p, "serif", 31, cw) + [""]
    if not words_lines:
        words_lines = [""] * 0
    for ln in words_lines:
        if y > h - 120:
            ci += 1
            if ci >= cols:
                break
            x = 140 + ci * (cw + 50)
            y = y0
        if ln:
            d.text((x, y), ln, font=ft, fill=(44, 40, 36))
        y += 40
    if not paras:
        # нет текста — серые строки как набор
        for c in range(cols):
            xx = 140 + c * (cw + 50)
            yy = y0
            rng = np.random.default_rng(5 + c)
            while yy < h - 120:
                d.rectangle([xx, yy + 12, xx + cw * rng.uniform(0.8, 1.0), yy + 26], fill=(150, 144, 134))
                yy += 40
    return im


@scene("10")
def s10(t, dur):
    if t < 2.2:
        return C.act_title("II", "Линия", t, 2.2)
    tt = t - 2.2
    dd = dur - 2.2
    if "page" not in _s10:
        _s10["page"] = newspaper_page()
    page = _s10["page"]
    # камера: от общего плана полосы к заголовку, потом к строке «start at the end»
    k1 = C.smoother(C.seg(tt, 0.0, 6.0))
    k2 = C.smoother(C.seg(tt, 7.5, 11.0))
    scale = C.lerp(0.72, 1.35, k1) * C.lerp(1.0, 1.55, k2)
    cx = C.lerp(1300, 900, k1) * (1 - k2) + 760 * k2
    cy = C.lerp(900, 420, k1) * (1 - k2) + 440 * k2
    pw, ph = int(page.size[0] * scale), int(page.size[1] * scale)
    big = page.resize((pw, ph), Image.LANCZOS)
    x0 = int(cx * scale - W / 2)
    y0 = int(cy * scale - H / 2)
    img = Image.new("RGB", (W, H), (40, 38, 36))
    img.paste(big, (-x0, -y0))
    # глубина резкости: вне полосы заголовка размыто, когда близко
    if k2 > 0.1:
        bl = img.filter(ImageFilter.GaussianBlur(4 * k2))
        m = Image.new("L", (W, H), 0)
        hy = int((440 - cy) * scale + H / 2)
        ImageDraw.Draw(m).rectangle([0, hy - 120 * scale, W, hy + 60 * scale], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(60))
        img = Image.composite(img, bl, m)
    # маркер по строке «start at the end»
    km = C.seg(tt, C.cue("10", "начните с конца", 9.0) - 2.2 + 0.3, C.cue("10", "начните с конца", 9.0) - 2.2 + 1.5)
    if km > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        # строка в координатах полосы: x 140…1180, y 385…500
        ax = (140 - cx) * scale + W / 2
        bx = (140 + 1040 * C.out_cubic(km) - cx) * scale + W / 2
        ay = (392 - cy) * scale + H / 2
        by = (496 - cy) * scale + H / 2
        dl.rectangle([ax, ay, bx, by], fill=(255, 214, 0, 95))
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    img = C.vignette(img, 0.45)
    img = C.over(img, C.caption("The Washington Post", "5 марта 2014", "колонка Генри Киссинджера", C.seg(tt, 1.0, 1.8))).convert("RGB")
    return C.finish(img, tt, dd, fi=0.6, fo=0.6, grain_k=0.03)


# ───────────────────────── 11 · Три тезиса из пола ─────────────────────────
_s11 = {}


@scene("11")
def s11(t, dur):
    cam = ZK.Cam(x=0.0, y=1.40, z=0.05 * t)
    img = ZK.hall(cam)
    if not _s11:
        _s11["a"] = ZK.word_tex("МОСТ", 300)
        _s11["b"] = ZK.word_tex("ВНЕ БЛОКОВ", 300)
        _s11["c"] = ZK.word_tex("АЛИБИ", 300)
        _s11["q"] = ZK.sheet_tex(["Демонизация Путина —", "не политика,", "а алиби для её отсутствия."],
                                 fsize=64, kind="serif_i", title="Вашингтон пост · 2014", w=1100, h=620)
    ta = C.cue("11", "её роль мост", 5.5)
    tb = C.cue("11", "военно вне блоков", 12.0)
    tc = C.cue("11", "а алиби", 19.0)
    ZK.standing(img, cam, _s11["b"], 0.0, 17.0, 0.8, C.seg(t, tb, tb + 0.8), 0.0, max_w=3.0)
    ZK.standing(img, cam, _s11["a"], -3.6, 12.0, 0.7, C.seg(t, ta, ta + 0.8), 0.0, max_w=2.4)
    ZK.standing(img, cam, _s11["c"], 3.7, 12.0, 0.7, C.seg(t, tc, tc + 0.8), 0.0, max_w=2.4)
    # лист с цитатой висит правее, когда прозвучала третья мысль
    kq = C.seg(t, tc + 1.2, tc + 2.2)
    if kq > 0:
        tex = _s11["q"].copy()
        tex.putalpha(tex.split()[3].point(lambda v: int(v * C.smoother(kq))))
        c = ZK.Z.quad((2.3, 2.0 + (1 - C.out_cubic(kq)) * 1.2, 7.6), 2.4, 1.35, yaw=math.radians(-18))
        ZK.Z.wire(img, cam, (c[0][0] + 0.1, c[0][1], c[0][2]))
        ZK.Z.wire(img, cam, (c[1][0] - 0.1, c[1][1], c[1][2]))
        ZK.Z.paste_quad(img, tex, [cam.proj(p) for p in c])
    img = ZK.Z.embers(img, cam, ZK.Z.cluster(3.2, 0.3, 12.0, 0.5, 3, 7) + ZK.Z.cluster(-3.4, 0.2, 14.5, 0.5, 3, 8), t)
    return C.finish(img.convert("RGB"), t, dur, fi=0.5, fo=0.6, grain_k=0.02)


# ───────────────────────── 12 · Минск: линия первая ─────────────────────────
def morph_line(a, b, k):
    """переход между двумя ломаными: по доле длины"""
    def resample(pts, n=60):
        pts = [np.array(p, float) for p in pts]
        seg = [np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)]
        tot = sum(seg)
        out = []
        for i in range(n):
            want = tot * i / (n - 1)
            run = 0.0
            for j, s in enumerate(seg):
                if run + s >= want or j == len(seg) - 1:
                    f = (want - run) / max(1e-6, s)
                    out.append(pts[j] + (pts[j + 1] - pts[j]) * min(1.0, f))
                    break
                run += s
        return out
    ra, rb = resample(a), resample(list(reversed(b)) if False else b)
    kk = C.out_expo(k)
    return [tuple(pa + (pb - pa) * kk) for pa, pb in zip(ra, rb)]


@scene("12")
def s12(t, dur):
    t_draw = 1.2
    t_seven = C.cue("12", "Семь лет она стояла", 15.0)
    t_jump = C.cue("12", "сместилась на тысячу", 19.0)
    base = K.base()
    lays = []
    kj = C.seg(t, t_jump, t_jump + 0.7)
    if kj <= 0:
        lays.append(K.line_layer(K.LINE_2015, C.seg(t, t_draw, t_draw + 4.0), width=5))
    else:
        lays.append(K.line_layer(morph_line(K.LINE_2015, list(reversed(K.LINE_NOW)), kj), 1.0, width=5, head=False))
    lays.append(K.city_layer(["Донецк", "Луганск", "Мариуполь"], C.seg(t, t_draw + 1.5, t_draw + 2.5), side={"Мариуполь": "l"}))
    if kj <= 0:
        lays.append(K.date_tag("2015", C.seg(t, 0.6, 1.4), sub="Минск-2 · линия соприкосновения"))
    else:
        lays.append(K.date_tag("2022", C.seg(t, t_jump, t_jump + 0.5), sub="через семь лет"))
    # число «7 ЛЕТ» слева от карты, потом «1000 КМ»
    k7 = C.seg(t, t_seven, t_seven + 1.6)
    if k7 > 0 and kj < 1:
        lays.append(C.alpha(C.big_number("7 ЛЕТ", "линия стояла", None, k7, cx=W * 0.27, cy=H * 0.42, px=230, count_from=0), 1 - kj))
    k1000 = C.seg(t, t_jump + 0.8, t_jump + 2.6)
    if k1000 > 0:
        lays.append(C.big_number("1000 КМ", "за несколько недель", "сдвиг линии на запад", k1000, cx=W * 0.27, cy=H * 0.42, px=230, count_from=0))
    # удар на прыжке: короткая встряска кадра
    img = C.over(base, *lays).convert("RGB")
    if 0 < kj < 1:
        sh = int(10 * (1 - kj) * math.sin(t * 90))
        img = img.transform(img.size, Image.AFFINE, (1, 0, sh, 0, 1, 0))
    return C.finish(img, t, dur, fi=0.6, fo=0.6, grain_k=0.03, vig=0.25)


# ───────────────────────── 13 · Давос, его голос ─────────────────────────
_s13 = {}


def speech_frame(vid, t, t_insert, name, place, date, lines, k_win=1.0, win=(1280, 720), tag_src=None):
    """режим оригинальной речи: окно записи на тёмном поле, светящаяся рамка,
    перевод особым начертанием внизу, имя и дата в углу. После вставки окно
    приглушается и уходит чуть меньше."""
    img = Image.new("RGB", (W, H), (9, 9, 11))
    fr = vid.at(t)
    ww, wh = win
    # после вставки окно сжимается и темнеет
    after = C.smoother(C.seg(t, t_insert, t_insert + 1.2))
    sc = C.lerp(1.0, 0.82, after)
    ww2, wh2 = int(ww * sc), int(wh * sc)
    fr = fr.resize((ww2, wh2), Image.LANCZOS)
    fr = C.fade(fr, C.lerp(1.0, 0.55, after))
    x0, y0 = (W - ww2) // 2, int((H - wh2) // 2 - 30 * (1 - after))
    # свечение рамки
    glow, pad = C.shadow_box((ww2, wh2), blur=40, a=int(140 * k_win))
    glow_img = Image.new("RGBA", glow.size, (0, 0, 0, 0))
    # белое свечение вместо чёрной тени
    g = glow.split()[3]
    glow_img = Image.merge("RGBA", (Image.new("L", g.size, 200), Image.new("L", g.size, 200),
                                    Image.new("L", g.size, 205), g.point(lambda v: int(v * 0.45))))
    img = img.convert("RGBA")
    img.alpha_composite(glow_img, (x0 - pad, y0 - pad))
    img.paste(fr, (x0, y0))
    d = ImageDraw.Draw(img)
    d.rectangle([x0 - 1, y0 - 1, x0 + ww2, y0 + wh2], outline=(120, 120, 126, 255), width=1)
    img = img.convert("RGB")
    lay = C.layer()
    dl = ImageDraw.Draw(lay)
    # имя и дата в углу окна (сверху слева над окном)
    a = int(255 * k_win)
    fn = C.font("head_r", 30 * SS)
    fd = C.font("head_l", 24 * SS)
    C.tracked(dl, x0 * SS, (y0 - 26) * SS, name.upper(), fn, C.WHITE + (a,), 0.14)
    C.tracked(dl, (x0 + ww2) * SS, (y0 - 26) * SS, (place + " · " + date).upper(), fd, C.GREY + (a,), 0.16, "rs")
    # перевод: курсивная антиква, строки появляются по времени вставки
    if t < t_insert + 0.8:
        n = len(lines)
        per = t_insert / max(1, n)
        # кегль перевода подбирается по самой длинной строке — в поля 96 px (журнал п.36/38)
        px = 40
        dm = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        while px > 22 and max(C.text_w(dm, ln, C.font("serif_i", px * SS)) for ln in lines) / SS > W - 2 * 96:
            px -= 2
        fi = C.font("serif_i", px * SS)
        yb = (y0 + wh2 + 70) * SS
        for i, ln in enumerate(lines):
            k = C.seg(t, i * per, i * per + 0.35)
            if k <= 0:
                continue
            k_out = C.seg(t, t_insert, t_insert + 0.8)
            aa = int(255 * C.smoother(k) * (1 - k_out))
            C.tracked(dl, W / 2 * SS, yb + i * px * 1.3 * SS, ln, fi, C.WHITE + (aa,), 0.0, "ms")
        # тонкая полоска хода оригинала
        kp = C.seg(t, 0, t_insert)
        dl.rectangle([x0 * SS, (y0 + wh2 + 14) * SS, (x0 + ww2 * kp) * SS, (y0 + wh2 + 16) * SS], fill=C.RED + (200,))
    if tag_src:
        fs = C.font("head_l", 22 * SS)
        C.tracked(dl, x0 * SS, (y0 + wh2 + 40) * SS, tag_src.upper(), fs, C.GREY2 + (int(255 * after),), 0.2)
    return C.over(img, lay).convert("RGB")


@scene("13")
def s13(t, dur):
    if "v" not in _s13:
        name = "wef_2023.mp4"
        _s13["v"] = C.Vid(name, CUTS.get("wef_2023_s13", 0.0), size=(1280, 720))
        _s13["name"] = name
    ins = C.scene_info("13")["insert"]
    img = speech_frame(_s13["v"], t, ins, "Генри Киссинджер", "Давос, видеосвязь", "январь 2023", PEREVOD["13"],
                       tag_src="запись Всемирного экономического форума")
    return C.finish(img, t, dur, fi=0.6, fo=0.6, grain_k=0.025)


# ───────────────────────── 14 · Линия 24 февраля ─────────────────────────
@scene("14")
def s14(t, dur):
    base = K.base()
    t_stay = C.cue("14", "остаются за ней", 5.0)
    t_back = C.cue("14", "возвращается Украине", 9.0)
    t_war = C.cue("14", "война против самой России", 19.0)
    lays = [K.zone_layer(K.CRIMEA, C.seg(t, t_stay, t_stay + 1.0), fill_a=95),
            K.zone_layer(K.DONBAS_OLD, C.seg(t, t_stay + 0.4, t_stay + 1.4), fill_a=80),
            K.zone_layer(K.ZONE_2022, C.seg(t, t_back, t_back + 1.2), color=C.WHITE, fill_a=38, hatch=True),
            K.line_layer(K.LINE_2015, C.seg(t, 0.6, 3.0), width=5),
            K.line_layer(K.CRIMEA + [K.CRIMEA[0]], C.seg(t, 1.5, 3.5), width=3, glow=False, head=False),
            K.city_layer(["Донецк", "Луганск", "Севастополь", "Херсон", "Запорожье"], C.seg(t, 2.0, 3.0), side={"Севастополь": "t", "Херсон": "l"}),
            K.date_tag("24.02.2022", C.seg(t, 0.4, 1.2), sub="линия раздела по Киссинджеру")]
    # подписи зон
    lab = C.layer()
    d = ImageDraw.Draw(lab)
    f = C.font("head_r", 30 * SS)
    ks = C.smoother(C.seg(t, t_stay + 1.0, t_stay + 1.8))
    kb_ = C.smoother(C.seg(t, t_back + 1.0, t_back + 1.8))
    if ks > 0:
        x, y = K.UA.xy(30.6, 45.3)
        C.tracked(d, x * SS, y * SS, "ОСТАЁТСЯ ЗА РОССИЕЙ", f, C.RED + (int(255 * ks),), 0.2, "ms")
    if kb_ > 0:
        x, y = K.UA.xy(35.4, 47.1)
        C.tracked(d, (x - 160) * SS, (y + 120) * SS, "ВОЗВРАЩАЕТСЯ УКРАИНЕ", f, C.WHITE + (int(255 * kb_),), 0.2, "ms")
    lays.append(C.done(lab))
    img = C.over(base, *lays).convert("RGB")
    # «война против самой России»: карта темнеет, линия пульсирует
    kw = C.seg(t, t_war, t_war + 1.0)
    if kw > 0:
        img = C.fade(img, 1 - 0.35 * C.smoother(kw))
    return C.finish(img, t, dur, fi=0.6, fo=0.6, grain_k=0.03, vig=0.25)


# ───────────────────────── 15 · Москва — Пекин ─────────────────────────
_s15 = {}


@scene("15")
def s15(t, dur):
    if "m" not in _s15:
        _s15["m"] = K.world(lon=(5, 150), lat=(5, 72))
        _s15["b"] = _s15["m"].render()
    m = _s15["m"]
    lays = [m.marker((W, H), "Москва", 37.62, 55.75, "Россия", k=C.seg(t, 0.3, 0.9), px=26, side="left"),
            m.marker((W, H), "Пекин", 116.4, 39.9, "Китай", k=C.seg(t, 1.0, 1.6), px=26),
            m.arc((W, H), (37.62, 55.75), (116.4, 39.9), k=C.seg(t, 1.4, 5.0), lift=0.22, px=3.2, dash=14, gap=9)]
    k_ret = C.seg(t, C.cue("15", "Мы к этому вернёмся", 7.5), C.cue("15", "Мы к этому вернёмся", 7.5) + 0.8)
    if k_ret > 0:
        lays.append(C.text_layer(["МЫ К ЭТОМУ ВЕРНЁМСЯ"], "head_l", 34, C.GREY, W / 2, H - 120, "ms", 0.34, a=C.smoother(k_ret)))
    img = C.over(_s15["b"], *lays).convert("RGB")
    return C.finish(img, t, dur, fi=0.5, fo=0.5, grain_k=0.03, vig=0.3)


# ───────────────────────── 16 · Ответ Киева ─────────────────────────
_s16 = {}


def tear(img_a, img_b, k, seed=4):
    """переход «разрыв»: рваный край идёт слева направо, по краю светлая полоса"""
    if k <= 0:
        return img_a
    if k >= 1:
        return img_b
    rng = np.random.default_rng(seed)
    ys = np.linspace(0, H, 40)
    edge = (W + 200) * C.out_cubic(k) - 100
    xs = edge + rng.normal(0, 1, 40).cumsum() * 9
    m = Image.new("L", (W, H), 0)
    pts = [(xs[i], ys[i]) for i in range(40)]
    ImageDraw.Draw(m).polygon([(-10, -10)] + pts + [(-10, H + 10)], fill=255)
    out = Image.composite(img_b, img_a, m)
    d = ImageDraw.Draw(out)
    d.line(pts, fill=(235, 232, 226), width=5)
    return out


@scene("16")
def s16(t, dur):
    if "v" not in _s16:
        _s16["v"] = C.Vid("zelensky_2022_05_25.mp4", CUTS.get("zelensky_2022_05_25.mp4", 0.0), zoom=1.45, cx=0.30, cy=0.30)
        _s16["m"] = C.Vid("munich_1938_pathe.mp4", CUTS.get("munich_1938_pathe.mp4", 0.0), zoom=1.3, cx=0.0, cy=0.7)
    ins = C.scene_info("16")["insert"]
    fr = _s16["v"].at(t)
    img = C.fade(fr, 0.85)
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    if t < ins + 0.6:
        n = len(PEREVOD["16"])
        per = ins / n
        fi = C.font("serif_i", 42 * SS)
        for i, ln in enumerate(PEREVOD["16"]):
            k = C.seg(t, i * per, i * per + 0.35)
            if k <= 0:
                continue
            aa = int(255 * C.smoother(k) * (1 - C.seg(t, ins, ins + 0.6)))
            # подложка-тень под строкой для читаемости
            tw = C.text_w(d, ln, fi)
            d.rectangle([W / 2 * SS - tw / 2 - 20 * SS, (H - 150 + i * 54 - 36) * SS, W / 2 * SS + tw / 2 + 20 * SS, (H - 150 + i * 54 + 14) * SS], fill=(0, 0, 0, int(140 * C.smoother(k))))
            C.tracked(d, W / 2 * SS, (H - 150 + i * 54) * SS, ln, fi, C.WHITE + (aa,), 0.0, "ms")
        kp = C.seg(t, 0, ins)
        d.rectangle([(W * 0.2) * SS, (H - 60) * SS, (W * 0.2 + W * 0.6 * kp) * SS, (H - 58) * SS], fill=C.RED + (200,))
    img = C.over(img, lay, C.caption("Владимир Зеленский", "обращение · 25 мая 2022", "Офис президента Украины", C.seg(t, 0.4, 1.2), y=130)).convert("RGB")
    # разрыв в архив в последние 0,9 с
    kt = C.seg(t, dur - 0.9, dur - 0.05)
    if kt > 0:
        arch = C.film_look(_s16["m"].at(0.0), t, 1.0)
        img = tear(img, arch, kt)
    return C.finish(img, t, dur, fi=0.5, fo=0.0, grain_k=0.02)


# ───────────────────────── 17 · Мюнхен, 11 месяцев ─────────────────────────
_s17 = {}


@scene("17")
def s17(t, dur):
    if "m" not in _s17:
        _s17["m"] = C.Vid("munich_1938_pathe.mp4", CUTS.get("munich_1938_pathe.mp4", 0.0), zoom=1.3, cx=0.0, cy=0.7)
    img = C.film_look(_s17["m"].at(t), t, 1.0)
    t_sh = C.cue("17", "через одиннадцать месяцев", 9.5)
    k_ax = C.seg(t, t_sh - 2.5, t_sh - 1.0)
    lays = [C.caption("Хестон · Лондон", "30 сентября 1938", "British Pathé", C.seg(t, 0.6, 1.4))]
    if k_ax > 0:
        img = C.fade(img, 1 - 0.45 * C.smoother(k_ax))
        lay = C.layer()
        d = ImageDraw.Draw(lay)
        y = H * 0.40
        x0, x1 = W * 0.22, W * 0.78
        a = int(255 * C.smoother(k_ax))
        d.line([(x0 * SS, y * SS), ((x0 + (x1 - x0) * C.out_cubic(k_ax)) * SS, y * SS)], fill=C.GREY + (a,), width=2 * SS)
        fdt = C.font("head", 44 * SS)
        flb = C.font("head_l", 26 * SS)
        for xx, dt, lb, kk in ((x0, "30.09.1938", "«Мир для нашего поколения»", C.seg(t, t_sh - 2.2, t_sh - 1.6)),
                               (x1, "01.09.1939", "Вторая мировая", C.seg(t, t_sh - 1.2, t_sh - 0.6))):
            if kk <= 0:
                continue
            aa = int(255 * C.smoother(kk))
            d.line([(xx * SS, (y - 30) * SS), (xx * SS, (y + 30) * SS)], fill=C.RED + (aa,), width=3 * SS)
            C.tracked(d, xx * SS, (y + 80) * SS, dt, fdt, C.WHITE + (aa,), 0.04, "ms")
            C.tracked(d, xx * SS, (y + 116) * SS, lb.upper(), flb, C.GREY + (aa,), 0.2, "ms")
        lays.append(C.done(lay))
        k_n = C.seg(t, t_sh - 0.2, t_sh + 1.4)
        if k_n > 0:
            lays.append(C.big_number("11 МЕСЯЦЕВ", None, None, k_n, cx=W / 2, cy=H * 0.66, px=200, count_from=0))
    img = C.over(img, *lays).convert("RGB")
    return C.finish(img, t, dur, fi=0.0, fo=0.6, grain_k=0.0)


# ───────────────────────── 18 · Минск-три ─────────────────────────
@scene("18")
def s18(t, dur):
    base = K.base()
    t_m = C.cue("18", "собственный Минск", 5.0)
    t_3 = C.cue("18", "Минск-три", 12.0)
    t_end = C.cue("18", "Линия", 21.0)
    lays = [K.line_layer(K.LINE_2015, C.seg(t, 0.3, 2.0), width=5),
            K.line_layer(K.LINE_NOW, C.seg(t, 0.3, 2.0), width=4, dash=(14, 9), color=C.GREY),
            K.city_layer(["Донецк", "Луганск", "Запорожье", "Херсон"], C.seg(t, 0.8, 1.6), side={"Херсон": "l"})]
    km = C.seg(t, t_m, t_m + 0.8)
    if km > 0:
        lay = C.layer()
        d = ImageDraw.Draw(lay)
        x, y = K.UA.xy(38.6, 48.95)
        a = int(255 * C.smoother(km))
        f = C.font("head_r", 34 * SS)
        C.tracked(d, x * SS, y * SS, "МИНСК-2 · 2015", f, C.RED + (a,), 0.2, "ms")
        d.line([(x * SS, (y + 12) * SS), (x * SS, (y + 60) * SS)], fill=C.RED + (a,), width=2 * SS)
        lays.append(C.done(lay))
    k3 = C.seg(t, t_3, t_3 + 0.8)
    if k3 > 0:
        lays.append(C.text_layer(["МИНСК-ТРИ"], "head", 120, C.WHITE, W * 0.30, H * 0.80, "ms", 0.08, a=C.smoother(k3)))
    ke = C.seg(t, t_end, t_end + 0.6)
    if ke > 0:
        lays.append(C.text_layer(["ЛИНИЯ."], "head", 120, C.RED, W * 0.30, H * 0.80 + 130, "ms", 0.08, a=C.smoother(ke)))
    img = C.over(base, *lays).convert("RGB")
    # конец акта: провал в чёрный длиннее обычного
    return C.finish(img, t, dur, fi=0.6, fo=1.6, grain_k=0.03, vig=0.25)
