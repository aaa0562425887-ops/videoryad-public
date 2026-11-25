#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Фильм «Верица» — четвёртый кусок: блок 3 «ДЕЛО ВТОРОЕ. ДОЧЕРИ», сцены 40-56 (≈134 с).

Людей в кадре нет (фото дочерей из интернета не качаем — его слово): дочери живут на
доске карточками и в документах. Числа — счётчиками. Подписи честные: цифры фонда —
«по публикациям расследователей», база геномов и военные — «версия издания „Система“»,
закон — «по публикациям», указы — kremlin.ru / pravo.gov.ru с номером и датой.

Новые эффекты своей разработки (fx4, низ файла):
  lestnica_let   — лестница лет: годы бегут столбцом, рядом одна и та же фраза
  kalendar       — перекидной календарь: листы с годами отрываются и улетают
  neuroset       — нейросеть: узлы зажигаются, рёбра прорастают, по ним бегут импульсы
  dnk            — спираль ДНК: две нити с перекладинами, вращается, светится
  genom_pole     — поле геномов: сетка точек заполняется под счётчик
  grif           — гриф: строки документа закрываются чёрными полосами одна за другой
  polosa_deneg   — полоса денег: сумма делится пополам, половина уходит в черноту
  shkala_programmy — шкала программы: годы, заливка до «сейчас», красная метка на конце
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
import scenes3 as S3
from core import W, H, SS
from scenes import (scene, rel, shots, flash, word, red_line, zoom_at, grade, vid, verica,
                    CAP_V, CAP_B, page_view, to_frame, page_dark, dark_bg, LINE_PUTIN, LINE_DAUGHTERS,
                    card_tex, pin_at, thread, board_bg, CARD_POS, CARD_W, CARD_H, fit_px)
from scenes2 import EUROPE, label, doc_view, card_extra, EXTRA
from scenes3 import foto, lamp_bg, haus_dark, CAP_HAUS06, DRESDEN, GER

SAFE_X, SAFE_Y = 96, 54

CAP_680 = ("Указ Президента № 680", "28.11.2018 · kremlin.ru", "действующая редакция")
CAP_192 = ("Указ Президента № 192", "25.04.2019 · pravo.gov.ru", "официальное опубликование")
CAP_RASSL = ("по публикациям расследователей", "документов фонда в кадре нет", None)
CAP_SIST = ("версия издания «Система»", "по публикациям", None)
CAP_ZAKON = ("закон о генетических данных", "февраль 2026 · по публикациям", "текст в кадре условный")
CAP_SHEMA = ("схема условная", None, None)

# ── доска: новые карточки блока 3
EXTRA["kat"] = ((W * 0.40, H * 0.19, 1.5), "", "МЛАДШАЯ", ["Катерина Тихонова", "фонд «Иннопрактика» · МГУ", "институт ИИ"])
EXTRA["mar"] = ((W * 0.62, H * 0.19, -1.5), "", "СТАРШАЯ", ["Мария Воронцова", "врач · генетика", "совет госпрограммы"])
EXTRA["sech"] = ((W * 0.84, H * 0.21, 2.0), "", "СЕЧИН", ["«Роснефть»", "партнёр программы"])
EXTRA["dolzh"] = ((W * 0.51, H * 0.19, 0.5), "", "ДОЛЖНОСТЬ", ["политической — нет", "пока"])


# ── фото-улика (финал, его слово 23.11 ~13:35: «как журналистское расследование — фото как улика»)
_fp = {}


def foto_print(name, w, h, lines, empty=False, bw=False):
    """фотоотпечаток на доске: белое поле, снимок в тёмном строе, подпись от руки внизу; empty — пустая рамка «снимка нет»"""
    key = ("fp", name, w, h, tuple(lines), empty, bw)
    if key in _fp:
        return _fp[key]
    s = 2
    m = 12 * s
    px = max(13, int(w / 13))
    cap_h = (int(px * 1.25) * len(lines) + 10) * s
    W2, H2 = w * s, h * s
    im = C.paper(W2, H2, seed=7 + len(name) + len(lines), tone=(236, 232, 222), dark=0.0).convert("RGBA")
    d = ImageDraw.Draw(im)
    box = (m, m, W2 - m, H2 - m - cap_h)
    bw_, bh_ = box[2] - box[0], box[3] - box[1]
    if empty:
        d.rectangle(box, fill=(58, 54, 50, 255), outline=(120, 110, 95, 255), width=2)
        d.line([(box[0], box[1]), (box[2], box[3])], fill=(96, 90, 84, 255), width=2)
        d.line([(box[2], box[1]), (box[0], box[3])], fill=(96, 90, 84, 255), width=2)
        C.tracked(d, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + px * s * 0.4, "ФОТО НЕТ", C.font("head_l", int(px * 1.6) * s), (150, 142, 134, 255), 0.2, "ms")
    else:
        ph = foto(name).convert("RGB")
        r = max(bw_ / ph.size[0], bh_ / ph.size[1])
        ph = ph.resize((max(1, int(ph.size[0] * r)), max(1, int(ph.size[1] * r))), Image.LANCZOS)
        x0 = (ph.size[0] - bw_) // 2
        y0 = int((ph.size[1] - bh_) * 0.25)
        ph = ph.crop((x0, y0, x0 + bw_, y0 + bh_))
        if bw:
            ph = ph.convert("L").convert("RGB")
        ph = grade(ph, 0.7)
        im.paste(ph, (box[0], box[1]))
        d.rectangle(box, outline=(120, 110, 95, 255), width=2)
    y = H2 - m - cap_h + int(px * 1.15) * s
    for ln in lines:
        d.text((m + 4 * s, y), ln, font=C.font("serif_i", px * s), fill=(74, 66, 58, 255), anchor="ls")
        y += int(px * 1.25) * s
    out = im.resize((w, h), Image.LANCZOS)
    _fp[key] = out
    return out


def pin_foto(img, tex, cx, cy, ang, k, lx=W / 2, ly=-300.0):
    """приколоть отпечаток к тёмному фону (не к доске): тень, поворот, булавка; возвращает RGBA-слой"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if k <= 0:
        return lay
    kk = C.out_cubic(k)
    sc = 1.25 - 0.25 * kk
    yy = cy - 70 * (1 - kk)
    t2 = tex.rotate(ang, Image.BICUBIC, expand=True)
    if sc != 1.0:
        t2 = t2.resize((int(t2.size[0] * sc), int(t2.size[1] * sc)), Image.LANCZOS)
    sh, sx, sy = fx.shadow_of(t2.size, lx, ly, cx, yy, blur=18 + int(30 * (1 - kk)), a=int(190 * kk))
    lay.alpha_composite(sh, (sx, sy))
    lay.alpha_composite(C.alpha(t2, C.clamp(k * 2)), (int(cx - t2.size[0] / 2), int(yy - t2.size[1] / 2)))
    if k >= 1:
        pl = C.layer()
        pin_at(ImageDraw.Draw(pl), cx, cy - tex.size[1] / 2 + 24)
        lay = Image.alpha_composite(lay, C.done(pl))
    return lay


def board4(t, lamp_t, extra, threads=(), amp=0.0, dark=0.10, prior=("lich", "zachem", "mitr", "dres"), fotos=()):
    """вся доска фильма: 3 карточки хука + prior пришпилены; extra=[(key, k_drop, k_text)];
    threads=[(keyA, keyB, k)] — нити между карточками (ключ None/0/1/2 — карточки хука);
    fotos=[(key, tex, cx, cy, ang, k)] — фотоотпечатки-улики, приколоты как карточки (финал)"""
    lx, ly = fx.lampa_pos(lamp_t, W / 2, amp, 3.6)
    img = board_bg().copy().convert("RGBA")
    pins = {}
    items = [(CARD_POS[i], card_tex(i, 1.0), 1.0, i) for i in range(3)]
    for key in prior:
        items.append((EXTRA[key][0], card_extra(key, 1.0), 1.0, key))
    for key, kd, kt in extra:
        if kd > 0:
            items.append((EXTRA[key][0], card_extra(key, kt), kd, key))
    for key, tex, cx, cy, ang, k in fotos:
        if k > 0:
            items.append(((cx, cy, ang), tex, k, key))
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
            pins[key] = (cx, cy - tex0.size[1] / 2 + 26)
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    base = [pins[i] for i in range(3)]
    thread(d, base, 1.0)
    if "lich" in pins:
        thread(d, [base[0], pins["lich"]], 1.0, sag=30)
    if "zachem" in pins:
        thread(d, [base[0], pins["zachem"]], 1.0, sag=60)
        x, y = pins["zachem"]
        thread(d, [(x, y), (W + 80, y - 160)], 1.0, sag=20)
    if "mitr" in pins:
        thread(d, [pins["mitr"], base[1]], 1.0, sag=20)
    if "dres" in pins:
        thread(d, [pins["dres"], base[0]], 1.0, sag=24)
    for a, b, k in threads:
        if a in pins and b in pins and k > 0:
            thread(d, [pins[a], pins[b]], k, sag=26)
    for x, y in pins.values():
        pin_at(d, x, y)
    img = C.over(img, C.done(lay)).convert("RGB")
    return fx.lampa(img, lx, ly, 1150, dark)


def board_blur_bg(t, extra=()):
    img = board4(t, 10.0, extra, amp=0.0)
    cx, cy, _ = CARD_POS[1]
    return C.fade(zoom_at(img, 2.3 + 0.03 * t, cx, cy), 0.35).filter(ImageFilter.GaussianBlur(3))


# ═════════════════════════ 40 · титр ДЕЛО ВТОРОЕ · строка ═════════════════════════
@scene("40")
def s40(t, dur):
    c_doch = rel("40", 287.61)

    def a_title(tt, d):
        img = board_blur_bg(t, extra=[("dres", 1, 1)])
        k = C.seg(tt, 0.0, 0.5)
        sc = 1.3 - 0.3 * C.out_expo(k)
        px = fit_px("ДЕЛО ВТОРОЕ", "head", 170, W - 2 * SAFE_X, 0.1)
        lays = [C.text_layer(["ДЕЛО ВТОРОЕ"], "head", int(px * sc), C.WHITE, W / 2, H * 0.5 + 40, "ms", 0.1, a=C.clamp(k * 2)),
                red_line(C.seg(tt, 0.4, 0.9), W / 2 - 200, W / 2 + 200, H * 0.5 + 66, 5),
                word("дочери", C.seg(tt, 0.6, 1.0), H * 0.5 + 150, 60, "serif_i", C.GREY, 0.0, rise=16)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.1, 0.5)

    def b_line(tt, d):
        sc = 2.8 + 0.05 * tt
        img, geo = page_view(7037, sc, 805)
        box = to_frame(LINE_DAUGHTERS, geo)
        img = fx.fonar(img, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 30, 640, 330, 0.10, 0.05, t)
        img = page_dark(img, t)
        k_tr = C.seg(tt, 0.2, 2.4)
        lays = [red_line(1.0, box[0] - 8, box[2] + 8, box[3] + 12, 4), C.caption(*CAP_B, k=1.0),
                C.text_layer(["ПЕРЕВОД"], "head_l", 24, C.GREY, SAFE_X, H - 270, "ls", 0.3, a=C.clamp(k_tr * 3)),
                fx.typed("«Дочери Путина станут успешными политиками в России»", k_tr, "head_r", 46, C.WHITE, SAFE_X, H - 214, 0.02, True, t)]
        return flash(C.over(img, *lays).convert("RGB"), tt, 0.06, 0.3)

    fn, tt, d = shots(t, [(0.0, a_title), (c_doch, b_line)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 41 · 2016, другие фамилии, одна фраза годами ═════════════════════════
@scene("41")
def s41(t, dur):
    c_fam = rel("41", 292.16)
    c_vopr = rel("41", 293.43)
    c_fraza = rel("41", 296.2)

    def a_2016(tt, d):
        img = C.kb(dark_bg(41), tt / 3.0, 0.05, 0.5, 0.5)
        k = C.seg(tt, 0.05, 0.7)
        lay = C.big_number("2016", None, "год записи", k, W / 2, H * 0.46, 300, C.WHITE, rings=False, count_from=2006)
        return C.grain(C.over(img, lay).convert("RGB"), t, 0.04)

    def b_fam(tt, d):
        img = C.kb(dark_bg(42), tt / 3.0, 0.05, 0.5, 0.5)
        # две таблички: фамилия закрыта чёрной полосой
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        s = SS
        for i, (name, x) in enumerate((("МЛАДШАЯ", W * 0.30), ("СТАРШАЯ", W * 0.70))):
            k = C.seg(tt, 0.05 + i * 0.25, 0.5 + i * 0.25)
            if k <= 0:
                continue
            a = int(255 * C.smoother(k))
            y = H * 0.5 - 40 * (1 - C.out_cubic(k))
            C.tracked(dd, x * s, (y - 60) * s, name, C.font("head_l", 40 * s), C.GREY + (a,), 0.3, "ms")
            wbar = 440 * C.out_cubic(C.seg(tt, 0.3 + i * 0.25, 0.9 + i * 0.25))
            dd.rectangle([(x - wbar / 2) * s, (y - 10) * s, (x + wbar / 2) * s, (y + 62) * s], fill=(14, 14, 16, a))
            dd.rectangle([(x - 220) * s, (y - 10) * s, (x + 220) * s, (y + 62) * s], outline=C.GREY2 + (a,), width=2 * s)
        return C.grain(C.over(img, C.done(lay), label("У НИХ ДРУГИЕ ФАМИЛИИ", C.seg(tt, 0.1, 0.5), H * 0.5 + 170, 46, C.WHITE)).convert("RGB"), t, 0.04)

    def c_years(tt, d):
        img = C.kb(dark_bg(43), tt / 4.0, 0.04, 0.5, 0.5)
        lay = lestnica_let(tt, c_fraza - c_vopr)
        return C.grain(C.over(img, lay, label("НА ПРЯМОЙ ВОПРОС ЖУРНАЛИСТОВ · КРЕМЛЬ ГОДАМИ", C.seg(tt, 0.1, 0.5), 110, 34, C.WHITE)).convert("RGB"), t, 0.04)

    fn, tt, d = shots(t, [(0.0, a_2016), (c_fam, b_fam), (c_vopr, c_years)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 42 · прошло десять лет · календарь ═════════════════════════
@scene("42")
def s42(t, dur):
    c_posm = rel("42", 300.11)

    def a(tt, d):
        img = C.kb(dark_bg(44), tt / 4.0, 0.05, 0.5, 0.5)
        k = C.seg(tt, 1.0, c_posm + 0.6)
        lay = kalendar(k, tt)
        return C.grain(C.over(img, lay,
                              label("ПРОШЛО ДЕСЯТЬ ЛЕТ", C.seg(tt, 1.0, 1.4), 120, 46, C.WHITE),
                              label("ПОСМОТРИМ, ГДЕ ОНИ СЕЙЧАС", C.seg(tt, c_posm + 0.3, c_posm + 0.7), H - 110, 40, C.WHITE)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 43 · младшая · Дрезден 1986 ═════════════════════════
@scene("43")
def s43(t, dur):
    c_kat = rel("43", 302.88)
    c_rod = rel("43", 304.02)
    c_tom = rel("43", 305.6)
    c_86 = rel("43", 306.4)

    def a_card(tt, d):
        kd = C.seg(tt, 0.0, 0.5)
        kt = C.seg(tt, c_kat - 0.2, c_kat + 0.5)
        kf = C.seg(tt, c_kat + 0.2, c_kat + 0.8)   # финал: фото уликой — его слово 23.11 ~13:35 (взрослого свободного снимка нет, детское из архива kremlin.ru)
        ft = foto_print("foto/tikhonova_1.jpg", 260, 330, ["Катерина Путина · 1988", "личный архив В. Путина", "kremlin.ru · CC BY 4.0"], bw=True)
        img = board4(t, 12.0 + tt, [("kat", kd, kt)], threads=[("kat", 1, C.seg(tt, 0.5, 1.1)), ("kat", "f_kat", C.seg(tt, c_kat + 0.7, c_kat + 1.2))],
                     amp=300.0, fotos=[("f_kat", ft, W * 0.585, H * 0.19, 4.0, kf)])
        cx, cy, _ = EXTRA["kat"][0]
        img = zoom_at(img, 1.7, cx + 60, cy + 60)
        return flash(C.over(img, label("МЛАДШАЯ", C.seg(tt, 0.1, 0.5), H - 120, 50, C.WHITE)).convert("RGB"), tt, 0.08, 0.4)

    def b_dresden(tt, d):
        img = haus_dark("haus_2006.jpg", tt + 1.0, 0.5, 0.4, 0.07, 0.6)
        img = fx.fonar(img, W * 0.45, H * 0.42, 820, 520, 0.22, 0.04, t)
        return flash(C.over(img, K.date_tag("1986", C.seg(tt, c_86 - c_rod, c_86 - c_rod + 0.5), sub="родилась в Дрездене"),
                            label("В ТОМ САМОМ", C.seg(tt, c_tom - c_rod, c_tom - c_rod + 0.4), H - 150, 44, C.WHITE),
                            C.caption(*CAP_HAUS06, k=C.seg(tt, 0.2, 0.6))).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_card), (c_rod, b_dresden)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.25)


# ═════════════════════════ 44 · фонд при МГУ · Иннопрактика ═════════════════════════
def dossier(title, lines, k_in, k_text, t, tone=(200, 190, 170), w=1180, h=720):
    """лист-досье на столе под лампой: заголовок, строки печатаются"""
    img = lamp_bg(45).convert("RGBA")
    sheet = C.paper(w, h, seed=101 + len(title), tone=tone, dark=0.0).convert("RGBA")
    d = ImageDraw.Draw(sheet)
    d.rectangle([0, 0, w - 1, h - 1], outline=(110, 100, 86, 255), width=3)
    d.line([(60, 150), (w - 60, 150)], fill=(110, 100, 86, 255), width=2)
    d.text((60, 118), title, font=C.font("head", 64), fill=C.INK + (255,), anchor="ls")
    total = sum(len(l) for l in lines)
    budget = int(total * C.clamp(k_text))
    y = 240
    for ln in lines:
        n = min(len(ln), budget)
        budget -= n
        if n > 0:
            d.text((60, y), ln[:n], font=C.font("serif", 44), fill=C.INK + (255,), anchor="ls")
        y += 78
    kk = C.out_cubic(k_in)
    x0, y0 = int(W / 2 - w / 2), int(H * 0.52 - h / 2 + (1 - kk) * 400)
    sh, sx, sy = fx.shadow_of((w, h), W / 2, -300, x0 + w / 2, y0 + h / 2, blur=24, a=180)
    img.alpha_composite(sh, (sx, sy))
    img.alpha_composite(C.alpha(sheet, C.clamp(k_in * 2)), (x0, y0))
    out = img.convert("RGB")
    out = fx.fonar(out, W * 0.5, H * 0.5, 900, 560, 0.10, 0.045, t)
    return C.grain(out, t, 0.03)


@scene("44")
def s44(t, dur):
    c_fond = rel("44", 310.18)
    c_inno = rel("44", 311.0)

    def a(tt, d):
        img = dossier("ФОНД ПРИ МГУ", ["руководитель — младшая дочь", "название: «Иннопрактика»"],
                      C.seg(tt, 0.0, 0.6), C.seg(tt, 0.6, c_inno + 0.8), t)
        z = 1.0 + 0.5 * C.smoother(C.seg(tt, c_inno, c_inno + 1.6))
        img = zoom_at(img, z, W * 0.5, H * 0.56)
        return C.over(img, word("«ИННОПРАКТИКА»", C.seg(tt, c_inno + 0.6, c_inno + 1.0), H - 120, 80, "head", C.WHITE, 0.1, rise=26),
                      C.caption("Московский университет", "фонд «Иннопрактика»", "по публикациям", k=C.seg(tt, 0.3, 0.7))).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 45 · 900 миллионов · контракты · половина · отчёта нет ═════════════════════════
@scene("45")
def s45(t, dur):
    c_dva = rel("45", 315.8)
    c_900 = rel("45", 317.3)
    c_kontr = rel("45", 318.97)
    c_trans = rel("45", 320.4)
    c_polov = rel("45", 321.87)
    c_istoch = rel("45", 323.64)
    c_otch = rel("45", 325.56)
    c_nepubl = rel("45", 327.55)

    def a_900(tt, d):
        img = C.kb(dark_bg(46), tt / 5.0, 0.05, 0.5, 0.5)
        k = C.seg(tt, c_900 - 0.3, c_900 + 1.2)
        lay = C.big_number("900 МИЛЛИОНОВ", "ТОЛЬКО ЗА ДВА ГОДА", "рублей · по подсчётам расследователей", k, W / 2, H * 0.46, 250, C.RED, rings=True, count_from=0)
        return C.grain(C.over(img, lay, label("РАССЛЕДОВАТЕЛИ ПОДСЧИТАЛИ", C.seg(tt, 0.1, 0.5), 110, 36, C.WHITE),
                              C.caption(*CAP_RASSL, k=1.0)).convert("RGB"), t, 0.04)

    def b_kontr(tt, d):
        img = C.kb(dark_bg(47), tt / 4.0, 0.05, 0.5, 0.5)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        s = SS
        for i, (name, t0) in enumerate((("«РОСНЕФТЬ»", 0.05), ("«ТРАНСНЕФТЬ»", c_trans - c_kontr))):
            k = C.seg(tt, t0, t0 + 0.5)
            if k <= 0:
                continue
            a = int(255 * C.smoother(k))
            x = W * (0.3 + 0.4 * i)
            y = H * 0.5
            wdt = 560 * C.out_cubic(k)
            dd.rectangle([(x - wdt / 2) * s, (y - 110) * s, (x + wdt / 2) * s, (y + 110) * s], fill=(26, 26, 30, a), outline=(80, 80, 86, a), width=2 * s)
            C.tracked(dd, x * s, (y + 22) * s, name, C.font("head", 64 * s), C.WHITE + (a,), 0.08, "ms")
            C.tracked(dd, x * s, (y + 72) * s, "КОНТРАКТ", C.font("head_l", 26 * s), C.GREY + (a,), 0.3, "ms")
        return C.grain(C.over(img, C.done(lay), label("КОНТРАКТЫ", C.seg(tt, 0.0, 0.4), 110, 46, C.WHITE),
                              C.caption(*CAP_RASSL, k=1.0)).convert("RGB"), t, 0.04)

    def c_polovina(tt, d):
        img = C.kb(dark_bg(48), tt / 4.0, 0.05, 0.5, 0.5)
        lay = polosa_deneg(C.seg(tt, 0.1, 1.2), C.seg(tt, c_istoch - c_polov, c_istoch - c_polov + 0.8), tt)
        return C.grain(C.over(img, lay, label("ПОЛОВИНА ДЕНЕГ — ВЗНОСАМИ", C.seg(tt, 0.1, 0.5), 110, 46, C.WHITE),
                              C.caption(*CAP_RASSL, k=1.0)).convert("RGB"), t, 0.04)

    def d_otchet(tt, d):
        img = dossier("ОТЧЁТ О РАСХОДАХ", [], C.seg(tt, 0.0, 0.5), 0.0, t)
        # фонарь ищет по пустому листу
        k = C.smoother(C.seg(tt, 0.6, 2.6))
        lx = W * 0.5 + 300 * math.sin(k * math.pi * 2)
        ly = H * 0.4 + 220 * k
        img = fx.fonar(img, lx, ly, 520, 340, 0.25, 0.05, t)
        return C.over(img, word("НЕ ПУБЛИКУЕТ", C.seg(tt, c_nepubl - c_otch, c_nepubl - c_otch + 0.45), H - 120, 90, "head", C.WHITE, 0.14, rise=30),
                      C.caption(*CAP_RASSL, k=1.0)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_900), (c_kontr, b_kontr), (c_polov, c_polovina), (c_otch, d_otchet)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 46 · институт искусственного интеллекта ═════════════════════════
@scene("46")
def s46(t, dur):
    c_inst = rel("46", 331.7)

    def a(tt, d):
        img = C.kb(dark_bg(49), tt / 4.0, 0.04, 0.5, 0.5)
        lay = neuroset(C.seg(tt, 0.0, 2.8), tt, seed=3)
        return C.grain(C.over(img, lay, K.date_tag("2020", C.seg(tt, 0.1, 0.5), sub="возглавляет ещё и"),
                              label("ИНСТИТУТ ИСКУССТВЕННОГО ИНТЕЛЛЕКТА", C.seg(tt, c_inst, c_inst + 0.4), H - 120, 46, C.WHITE),
                              C.caption("Московский университет", "институт искусственного интеллекта", "по публикациям", k=C.seg(tt, 0.3, 0.7))).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 47 · старшая · генетика · указ ═════════════════════════
@scene("47")
def s47(t, dur):
    c_mar = rel("47", 334.81)
    c_gen = rel("47", 336.59)
    c_ukaz = rel("47", 338.03)
    c_sovet = rel("47", 339.4)
    c_tech = rel("47", 341.0)

    def a_card(tt, d):
        kd = C.seg(tt, 1.5, 2.0)
        kt = C.seg(tt, c_mar - 0.2, c_mar + 0.5)
        img = board4(t, 14.0 + tt, [("kat", 1, 1), ("mar", kd, kt)], threads=[("kat", 1, 1.0), ("mar", 1, C.seg(tt, 2.0, 2.6))], amp=300.0)
        cx, cy, _ = EXTRA["mar"][0]
        img = zoom_at(img, 1.7, C.lerp(W * 0.5, cx, C.smoother(C.seg(tt, 0.0, 1.5))), cy + 60)
        return C.over(img, label("СТАРШАЯ", C.seg(tt, 1.5, 1.9), H - 120, 50, C.WHITE)).convert("RGB")

    def b_dnk(tt, d):
        img = C.kb(dark_bg(50), tt / 4.0, 0.04, 0.5, 0.5)
        lay = dnk(C.seg(tt, 0.0, 1.2), tt, W * 0.5, H * 0.5, 760)
        return C.grain(C.over(img, lay, label("ВРАЧ · ГЕНЕТИКА", C.seg(tt, 0.1, 0.5), H - 120, 46, C.WHITE)).convert("RGB"), t, 0.04)

    def c_ukaz_fn(tt, d):
        sc = 1.9 + 0.05 * tt
        img, geo = doc_view("ukaz_680_kremlin.png", 330, sc, 1400)
        img = fx.fonar(img, W * 0.5, H * 0.35, 760, 300, 0.12, 0.04, t)
        img = page_dark(img, t)
        return flash(C.over(img, label("УКАЗОМ ПРЕЗИДЕНТА", C.seg(tt, 0.1, 0.5), 92, 40, C.WHITE),
                            C.caption(*CAP_680, k=C.seg(tt, 0.2, 0.6))).convert("RGB"), tt, 0.08, 0.4)

    def d_sovet(tt, d):
        sc = 2.4 + 0.06 * tt
        img, geo = doc_view("ukaz_192_pravo_gov_str2.png", 830, sc, 960)
        k = C.seg(tt, 0.3, 0.8)
        # рамка строки «Воронцова М.В.»: пиксели страницы → кадр
        x0, y0, s_ = geo
        bx = ((718 - x0) * s_, (790 - y0) * s_, (1200 - x0) * s_, (818 - y0) * s_)
        img = fx.fonar(img, (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2, 700, 260, 0.12, 0.04, t)
        img = page_dark(img, t)
        return flash(C.over(img, red_line(k, bx[0] - 6, bx[2] + 6, bx[3] + 4, 4),
                            label("ВКЛЮЧЕНА В СОВЕТ ГОСПРОГРАММЫ ГЕНЕТИЧЕСКИХ ТЕХНОЛОГИЙ", C.seg(tt, c_tech - c_sovet, c_tech - c_sovet + 0.4), 92, 32, C.WHITE),
                            C.caption(*CAP_192, k=C.seg(tt, 0.2, 0.6))).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_card), (c_gen, b_dnk), (c_ukaz, c_ukaz_fn), (c_sovet, d_sovet)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 48 · бюджет 127 миллиардов · Роснефть · Сечин ═════════════════════════
@scene("48")
def s48(t, dur):
    c_127 = rel("48", 343.3)
    c_part = rel("48", 345.80)
    c_ros = rel("48", 347.2)
    c_sech = rel("48", 348.10)

    def a_127(tt, d):
        img = C.kb(dark_bg(51), tt / 4.0, 0.05, 0.5, 0.5)
        k = C.seg(tt, c_127 - 0.3, c_127 + 1.3)
        lay = C.big_number("127 МИЛЛИАРДОВ", "БЮДЖЕТ ПРОГРАММЫ", "рублей", k, W / 2, H * 0.46, 250, C.RED, rings=True, count_from=0)
        return C.grain(C.over(img, lay, C.caption("госпрограмма генетических технологий", "бюджет · по публикациям", None, k=1.0)).convert("RGB"), t, 0.04)

    def b_partner(tt, d):
        img = C.kb(dark_bg(52), tt / 4.0, 0.05, 0.5, 0.5)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        s = SS
        k = C.seg(tt, c_ros - c_part - 0.2, c_ros - c_part + 0.4)
        if k > 0:
            a = int(255 * C.smoother(k))
            x, y = W * 0.5, H * 0.5
            wdt = 700 * C.out_cubic(k)
            dd.rectangle([(x - wdt / 2) * s, (y - 120) * s, (x + wdt / 2) * s, (y + 120) * s], fill=(26, 26, 30, a), outline=(80, 80, 86, a), width=2 * s)
            C.tracked(dd, x * s, (y + 26) * s, "«РОСНЕФТЬ»", C.font("head", 80 * s), C.WHITE + (a,), 0.08, "ms")
            C.tracked(dd, x * s, (y + 80) * s, "ГЛАВНЫЙ ПАРТНЁР ПРОГРАММЫ", C.font("head_l", 28 * s), C.GREY + (a,), 0.3, "ms")
        return C.grain(C.over(img, C.done(lay), label("ГЛАВНЫЙ ПАРТНЁР", C.seg(tt, 0.0, 0.4), 110, 46, C.WHITE)).convert("RGB"), t, 0.04)

    def c_sechin(tt, d):
        kd = C.seg(tt, 0.0, 0.5)
        kt = C.seg(tt, 0.3, 0.9)
        fs = foto_print("foto/sechin_17.jpg", 260, 310, ["Игорь Сечин · 2016", "пресс-служба Президента", "kremlin.ru · CC BY 4.0"])   # финал: фото уликой, его слово 23.11
        img = board4(t, 16.0 + tt, [("kat", 1, 1), ("mar", 1, 1), ("sech", kd, kt)],
                     threads=[("kat", 1, 1.0), ("mar", 1, 1.0), ("sech", "mar", C.seg(tt, 0.5, 1.1)), ("sech", "f_sech", C.seg(tt, 0.9, 1.4))],
                     amp=300.0, fotos=[("f_sech", fs, W * 0.72, H * 0.40, 3.0, C.seg(tt, 0.4, 0.95))])
        cx, cy, _ = EXTRA["sech"][0]
        img = zoom_at(img, 1.6, cx - 120, cy + 80)
        return flash(C.over(img, label("ИГОРЬ СЕЧИН", C.seg(tt, 0.1, 0.5), H - 120, 50, C.WHITE)).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_127), (c_part, b_partner), (c_sech, c_sechin)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 49 · база: сто тысяч геномов ═════════════════════════
@scene("49")
def s49(t, dur):
    c_100 = rel("49", 350.84)
    c_gen = rel("49", 352.67)

    def a(tt, d):
        img = C.kb(dark_bg(53), tt / 4.0, 0.04, 0.5, 0.5)
        k = C.seg(tt, c_100 - 0.2, c_100 + 2.0)
        lay = genom_pole(k, tt)
        return C.grain(C.over(img, lay, label("ЗАДАЧА · СОБРАТЬ БАЗУ", C.seg(tt, 0.1, 0.5), 92, 40, C.WHITE),
                              label("РАСШИФРОВАННЫХ ГЕНОМОВ ЖИТЕЛЕЙ РОССИИ", C.seg(tt, c_gen - 0.3, c_gen + 0.2), H - 110, 36, C.WHITE)).convert("RGB"), t, 0.04)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 50 · зачем? лечить · закон · военным ═════════════════════════
@scene("50")
def s50(t, dur):
    c_zach = rel("50", 354.17)
    c_ofic = rel("50", 355.14)
    c_no = rel("50", 357.87)
    c_zakon = rel("50", 359.7)
    c_dann = rel("50", 360.82)
    c_zakr = rel("50", 362.2)
    c_tayna = rel("50", 363.55)
    c_zhur = rel("50", 365.24)
    c_voen = rel("50", 368.6)

    def a_zachem(tt, d):
        img = C.kb(dark_bg(54), tt / 4.0, 0.05, 0.5, 0.5)
        return C.grain(C.over(img, word("ЗАЧЕМ?", C.seg(tt, c_zach, c_zach + 0.45), H * 0.5 + 80, 240, "head", C.WHITE, 0.1, rise=40)).convert("RGB"), t, 0.04)

    def b_ofic(tt, d):
        img = C.kb(dark_bg(55), tt / 4.0, 0.05, 0.5, 0.5)
        lay = dnk(1.0, tt + 3.0, W * 0.5, H * 0.5, 620, dim=0.5)
        return C.grain(C.over(img, lay, label("ОФИЦИАЛЬНО", C.seg(tt, 0.0, 0.4), 110, 40),
                              word("ЛЕЧИТЬ НАСЛЕДСТВЕННЫЕ БОЛЕЗНИ", C.seg(tt, 0.4, 0.9), H - 120, 64, "head_l", C.WHITE, 0.16, rise=24)).convert("RGB"), t, 0.04)

    def c_zakon_fn(tt, d):
        k_bars = C.seg(tt, c_zakr - c_no, c_tayna - c_no + 1.0)
        img = grif(C.seg(tt, 0.0, 0.5), k_bars, t)
        return flash(C.over(img, K.date_tag("ФЕВРАЛЬ 2026", C.seg(tt, 0.3, 0.8), px=54, sub="подписан закон"),
                            label("ДАННЫЕ ГРАЖДАН — ЗАКРЫТЫ", C.seg(tt, c_zakr - c_no, c_zakr - c_no + 0.4), 92, 36, C.WHITE, x=W * 0.42),
                            word("ПОЧТИ КАК ГОСУДАРСТВЕННАЯ ТАЙНА", C.seg(tt, c_tayna - c_no, c_tayna - c_no + 0.45), H - 120, 60, "head", C.WHITE, 0.12, rise=24),
                            C.caption(*CAP_ZAKON, k=C.seg(tt, 0.2, 0.6))).convert("RGB"), tt, 0.08, 0.4)

    def d_voen(tt, d):
        img = C.kb(dark_bg(56), tt / 4.0, 0.05, 0.5, 0.5)
        lay = genom_pole(1.0, tt + 5.0, dim=0.45)
        kv = C.seg(tt, c_voen - c_zhur, c_voen - c_zhur + 0.45)
        return C.grain(C.over(img, lay, label("ЖУРНАЛИСТЫ-РАССЛЕДОВАТЕЛИ УТВЕРЖДАЮТ", C.seg(tt, 0.1, 0.5), 92, 36, C.WHITE),
                              word("В ПЕРВУЮ ОЧЕРЕДЬ — ВОЕННЫМ", kv, H * 0.5 + 50, 110, "head", C.WHITE, 0.1, rise=36),
                              C.caption(*CAP_SIST, k=1.0)).convert("RGB"), t, 0.04)

    fn, tt, d = shots(t, [(0.0, a_zachem), (c_ofic, b_ofic), (c_no, c_zakon_fn), (c_zhur, d_voen)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 51 · две колонки · ближний круг · форум ═════════════════════════
@scene("51")
def s51(t, dur):
    c_odna = rel("51", 369.60)
    c_vtor = rel("51", 371.79)
    c_vokrug = rel("51", 373.98)
    c_2024 = rel("51", 376.31)
    c_tri = rel("51", 379.49)

    def a_cols(tt, d):
        img = C.kb(dark_bg(57), tt / 6.0, 0.03, 0.5, 0.5)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        s = SS
        k_div = C.seg(tt, 0.2, 1.0)
        dd.rectangle([(W / 2 - 2) * s, (H * 0.5 - H * 0.4 * k_div) * s, (W / 2 + 2) * s, (H * 0.5 + H * 0.4 * k_div) * s], fill=C.GREY2 + (255,))
        left = neuroset(C.seg(tt, 0.3, 2.0), tt, seed=5, cx=W * 0.25, cy=H * 0.52, rx=360, ry=300)
        right = dnk(C.seg(tt, 0.5, 1.8), tt, W * 0.75, H * 0.52, 520)
        kl = C.seg(tt, c_odna, c_odna + 0.4)
        kr = C.seg(tt, c_vtor, c_vtor + 0.4)
        return C.grain(C.over(img, C.done(lay), left, right,
                              label("ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ", C.seg(tt, 1.0, 1.4), 120, 40, C.WHITE, x=W * 0.25),
                              label("ГЕНЕТИЧЕСКИЙ КОД", C.seg(tt, 1.2, 1.6), 120, 40, C.WHITE, x=W * 0.75),
                              label("ОДНА СЕСТРА", kl, H - 110, 34, C.GREY, x=W * 0.25),
                              label("ВТОРАЯ", kr, H - 110, 34, C.GREY, x=W * 0.75)).convert("RGB"), t, 0.04)

    def b_krug(tt, d):
        img = board4(t, 18.0 + tt, [("kat", 1, 1), ("mar", 1, 1), ("sech", 1, 1)], threads=[("kat", 1, 1.0), ("mar", 1, 1.0), ("sech", "mar", 1.0)], amp=360.0)
        z = 1.45 - 0.2 * C.smoother(C.seg(tt, 0.0, d))
        img = zoom_at(img, z, W * 0.55, H * 0.3)
        return flash(C.over(img, label("ВОКРУГ — ЛЮДИ САМОГО БЛИЖНЕГО КРУГА", C.seg(tt, 0.1, 0.5), H - 110, 40, C.WHITE)).convert("RGB"), tt, 0.08, 0.4)

    def c_forum(tt, d):
        img = C.kb(dark_bg(58), tt / 5.0, 0.04, 0.5, 0.5)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        s = SS
        t_tri = c_tri - c_2024
        for i, yr in enumerate(("2024", "2025", "2026")):
            k = C.seg(tt, t_tri + i * 0.35, t_tri + i * 0.35 + 0.4)
            if k <= 0:
                continue
            a = int(255 * C.smoother(k))
            x = W * (0.25 + 0.25 * i)
            y = H * 0.52 - 30 * (1 - C.out_cubic(k))
            C.tracked(dd, x * s, (y + 40) * s, yr, C.font("head", 150 * s), (C.RED if i == 2 else C.WHITE) + (a,), 0.04, "ms")
            dd.rectangle([(x - 90) * s, (y + 62) * s, (x + 90) * s, (y + 66) * s], fill=C.RED + (a,))
        kf = C.seg(tt, 0.4, 1.0)   # финал: фото обеих дочерей — его слово 23.11 ~13:35; у Тихоновой свободного снимка нет — честная пустая рамка
        f_mar = pin_foto(img, foto_print("foto/vorontsova_14.jpg", 250, 320, ["Мария Воронцова · 2024", "ФФМ МГУ / МФТИ · CC BY 4.0"]), W * 0.14, H * 0.71, -3.0, kf)
        f_kat = pin_foto(img, foto_print("", 250, 320, ["Катерина Тихонова", "свободного снимка нет"], empty=True), W * 0.86, H * 0.71, 3.0, kf)
        return C.grain(C.over(img, C.done(lay), f_mar, f_kat, K.date_tag("2024", C.seg(tt, 0.1, 0.5), sub="обе выходят на публику"),
                              label("ТРИ ГОДА ПОДРЯД · ГЛАВНЫЙ ЭКОНОМИЧЕСКИЙ ФОРУМ СТРАНЫ", C.seg(tt, t_tri, t_tri + 0.4), H - 110, 34, C.WHITE)).convert("RGB"), t, 0.04)

    fn, tt, d = shots(t, [(0.0, a_cols), (c_vokrug, b_krug), (c_2024, c_forum)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 52 · должности нет · 53 · пока ═════════════════════════
@scene("52")
def s52(t, dur):
    def a(tt, d):
        kd = C.seg(tt, 0.0, 0.5)
        kt = C.seg(tt, 0.4, 1.0)
        img = board4(t, 20.0 + tt, [("kat", 1, 1), ("mar", 1, 1), ("sech", 1, 1), ("dolzh", kd, kt)],
                     threads=[("kat", 1, 1.0), ("mar", 1, 1.0), ("sech", "mar", 1.0)], amp=200.0)
        cx, cy, _ = EXTRA["dolzh"][0]
        img = zoom_at(img, 2.0, cx, cy + 40)
        return C.over(img, label("ПОЛИТИЧЕСКОЙ ДОЛЖНОСТИ НЕТ НИ У ОДНОЙ", C.seg(tt, 0.2, 0.6), H - 110, 36, C.WHITE)).convert("RGB")

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.03, vig=0.25)


@scene("53")
def s53(t, dur):
    c_poka = rel("53", 385.09)

    def a(tt, d):
        img = C.kb(dark_bg(59), tt / 3.0, 0.05, 0.5, 0.5)
        lay = fx.typed("ПОКА", C.seg(tt, c_poka, c_poka + 0.3), "head", 240, C.WHITE, W / 2 - 330, H * 0.5 + 90, 0.1, cur=True, t=tt)
        return C.grain(C.over(img, lay).convert("RGB"), t, 0.05)

    return C.finish(a(t, dur), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.35)


# ═════════════════════════ 54 · одна деталь · 2019…2027 ═════════════════════════
@scene("54")
def s54(t, dur):
    c_det = rel("54", 386.35)
    c_prog = rel("54", 389.34)
    c_2019 = rel("54", 391.98)
    c_2027 = rel("54", 393.6)

    def a_detail(tt, d):
        img = C.kb(dark_bg(60), tt / 4.0, 0.05, 0.5, 0.5)
        return C.grain(C.over(img, word("И ОДНА ДЕТАЛЬ", C.seg(tt, c_det, c_det + 0.45), H * 0.5 + 50, 120, "head_l", C.WHITE, 0.16, rise=30)).convert("RGB"), t, 0.04)

    def b_doc(tt, d):
        sc = 2.4 + 0.05 * tt
        img, geo = doc_view("ukaz_192_pravo_gov_str1.png", 860, sc, 960)
        x0, y0, s_ = geo
        bx = ((760 - x0) * s_, (818 - y0) * s_, (1160 - x0) * s_, (850 - y0) * s_)
        k19 = C.seg(tt, c_2019 - c_prog, c_2019 - c_prog + 0.5)
        k27 = C.seg(tt, c_2027 - c_prog, c_2027 - c_prog + 0.6)
        img = fx.fonar(img, (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2 + 20, 720, 300, 0.12, 0.04, t)
        img = page_dark(img, t)
        z = 1.0 + 0.6 * C.smoother(C.seg(tt, c_2027 - c_prog, c_2027 - c_prog + 1.5))
        img = zoom_at(img, z, (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2)
        return flash(C.over(img, label("ПО ДОКУМЕНТАМ · РАССЧИТАНА", C.seg(tt, 0.1, 0.5), 92, 36, C.WHITE),
                            K.date_tag("2019", k19, x=W * 0.42, y=H - 150, px=96, sub="с"),
                            K.date_tag("2027", k27, x=W * 0.9, y=H - 150, px=96, sub="по"),
                            C.caption(*CAP_192, k=C.seg(tt, 0.2, 0.6))).convert("RGB"), tt, 0.08, 0.4)

    fn, tt, d = shots(t, [(0.0, a_detail), (c_prog, b_doc)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 55 · шкала программы · Северная Корея · здесь тишина ═════════════════════════
ASIA = K.Okno(lon=(100.0, 150.0), lat=(30.0, 52.0))
RUS = K.Okno(lon=(20.0, 110.0), lat=(40.0, 75.0))
K.CITIES.update({"Пхеньян": (125.75, 39.03)})


@scene("55")
def s55(t, dur):
    c_korea = rel("55", 395.98)
    c_raket = rel("55", 397.90)
    c_zdes = rel("55", 400.02)
    c_fondy = rel("55", 401.27)
    c_fam = rel("55", 402.4)
    c_podg = rel("55", 403.52)
    c_rab = rel("55", 404.70)

    def a_shkala(tt, d):
        img = C.kb(dark_bg(61), tt / 4.0, 0.04, 0.5, 0.5)
        lay = shkala_programmy(C.seg(tt, 0.1, 1.3), C.seg(tt, 1.2, 1.8), tt)
        return C.grain(C.over(img, lay, label("ШКАЛА ПРОГРАММЫ · ПО ДОКУМЕНТАМ", C.seg(tt, 0.1, 0.5), 110, 36, C.WHITE)).convert("RGB"), t, 0.04)

    def b_korea(tt, d):
        base = K.base(ASIA, hot="North Korea")
        base = Image.fromarray(np.clip(np.asarray(base, np.float32) * 1.7, 0, 255).astype(np.uint8), "RGB")
        x, y = ASIA.xy(125.75, 39.03)
        lay = C.layer()
        dd = ImageDraw.Draw(lay)
        for j in range(3):
            ph = (tt * 0.8 + j * 0.33) % 1.0
            r = (10 + 110 * ph) * SS
            dd.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], outline=C.RED + (int(200 * (1 - ph)),), width=3 * SS)
        img = C.over(base, C.done(lay), K.city_layer(["Пхеньян"], C.seg(tt, 0.2, 0.6), okno=ASIA, px=30),
                     label("СЕВЕРНАЯ КОРЕЯ", C.seg(tt, 0.0, 0.4), 110, 46, C.WHITE),
                     word("ВОЖДЬ ВЫВОДИТ ДОЧЬ К РАКЕТАМ", C.seg(tt, c_raket - c_korea - 0.6, c_raket - c_korea), H - 150, 64, "head_l", C.WHITE, 0.14, rise=24),
                     label("НА ГЛАЗАХ У ВСЕГО МИРА · КАРТА УСЛОВНАЯ", C.seg(tt, c_raket - c_korea + 0.5, c_raket - c_korea + 0.9), H - 70, 24))
        return C.grain(zoom_at(img.convert("RGB"), 1.2 + 0.25 * C.smoother(tt / d), x, y), t, 0.03)

    def c_zdes_fn(tt, d):
        base = K.base(RUS, hot="Russia")
        base = C.fade(base, 0.85)
        items = [("ТИШИНА", 0.05), ("ЗАКРЫТЫЕ ФОНДЫ", c_fondy - c_zdes), ("ЧУЖИЕ ФАМИЛИИ", c_fam - c_zdes)]
        lays = [word(txt, C.seg(tt, t0, t0 + 0.45), 330 + i * 120, 80, "head_l" if i < 2 else "head", C.WHITE, 0.16, x=SAFE_X, anchor="ls", rise=26) for i, (txt, t0) in enumerate(items)]
        base = zoom_at(base, 1.05 + 0.08 * tt / d, W * 0.6, H * 0.5)
        img = C.over(base, *lays, label("ЗДЕСЬ", C.seg(tt, 0.0, 0.3), 200, 40, C.GREY, x=SAFE_X, anchor="ls"),
                     label("КАРТА УСЛОВНАЯ", 1.0, H - 70, 24))
        return C.grain(img.convert("RGB"), t, 0.03)

    def d_vopros(tt, d):
        img = board_blur_bg(t, extra=[("kat", 1, 1), ("mar", 1, 1), ("sech", 1, 1), ("dolzh", 1, 1)])
        return C.over(img, word("ЭТО ПОДГОТОВКА?", C.seg(tt, 0.0, 0.45), H * 0.5 - 20, 120, "head", C.WHITE, 0.1, rise=30),
                      word("ИЛИ ПРОСТО РАБОТА?", C.seg(tt, c_rab - c_podg, c_rab - c_podg + 0.45), H * 0.5 + 130, 80, "head_l", C.GREY, 0.14, rise=24)).convert("RGB")

    fn, tt, d = shots(t, [(0.0, a_shkala), (c_korea, b_korea), (c_zdes, c_zdes_fn), (c_podg, d_vopros)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.0, grain_k=0.0, vig=0.3)


# ═════════════════════════ 56 · ответа нет · строка десять лет назад ═════════════════════════
@scene("56")
def s56(t, dur):
    c_net = rel("56", 406.01)
    c_stroka = rel("56", 407.39)
    c_10 = rel("56", 408.38)

    def a_net(tt, d):
        img = C.kb(dark_bg(62), tt / 3.0, 0.05, 0.5, 0.5)
        return C.grain(C.over(img, word("ОТВЕТА НЕТ", C.seg(tt, c_net, c_net + 0.45), H * 0.5 + 60, 150, "head", C.WHITE, 0.12, rise=36)).convert("RGB"), t, 0.04)

    def b_line(tt, d):
        sc = 2.6 + 0.05 * tt
        img, geo = page_view(7037, sc, 805)
        box = to_frame(LINE_DAUGHTERS, geo)
        img = fx.fonar(img, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 30, 640, 330, 0.10, 0.05, t)
        img = page_dark(img, t)
        return flash(C.over(img, red_line(1.0, box[0] - 8, box[2] + 8, box[3] + 12, 4),
                            K.date_tag("2016", C.seg(tt, c_10 - c_stroka, c_10 - c_stroka + 0.5), sub="написано десять лет назад"),
                            label("ЕСТЬ СТРОКА", C.seg(tt, 0.1, 0.5), 92, 40, C.WHITE),
                            C.caption(*CAP_B, k=1.0)).convert("RGB"), tt, 0.06, 0.3)

    fn, tt, d = shots(t, [(0.0, a_net), (c_stroka, b_line)], dur)
    return C.finish(fn(tt, d), t, dur, fi=0.0, fo=0.7, grain_k=0.0, vig=0.3)


# ═════════════════════════ fx4 — новые эффекты четвёртого куска ═════════════════════════
def lestnica_let(tt, t_phrase):
    """годы 2016…2026 бегут столбцом вверх, рядом одна и та же фраза; годы красные, фраза серая"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    years = [str(y) for y in range(2016, 2027)]
    step = 96
    n = len(years)
    k = C.seg(tt, 0.2, 0.2 + n * 0.42)
    shown = k * n
    scroll = max(0.0, shown - 5.5) * step
    f_y = C.font("head", 72 * s)
    f_p = C.font("serif_i", 40 * s)
    for i, yr in enumerate(years):
        ki = C.clamp(shown - i)
        if ki <= 0:
            break
        a = int(255 * C.out_cubic(ki))
        y = H * 0.32 + i * step - scroll + (1 - C.out_cubic(ki)) * 30
        if y < SAFE_Y + 60 or y > H - 120:
            continue
        C.tracked(d, (SAFE_X + 160) * s, y * s, yr, f_y, C.RED + (a,), 0.04, "rs")
        kp = C.clamp((shown - i - 0.3) * 1.5)
        if kp > 0 and tt >= t_phrase - 0.3:
            C.tracked(d, (SAFE_X + 230) * s, (y - 6) * s, "— На такие вопросы не отвечаем", f_p, C.GREY + (int(220 * kp),), 0.0, "ls")
            d.line([((SAFE_X + 190) * s, (y - 20) * s), ((SAFE_X + 214) * s, (y - 20) * s)], fill=C.GREY2 + (a,), width=2 * s)
    return C.done(lay)


def kalendar(k, tt):
    """перекидной календарь: лист с годом; k 0…1 — отрываются листы 2016…2025, остаётся 2026"""
    years = [str(y) for y in range(2016, 2027)]
    n = len(years) - 1
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pw, ph = 620, 520
    cx, cy = W / 2, H * 0.52
    x0, y0 = int(cx - pw / 2), int(cy - ph / 2)
    # подложка-блок
    base = Image.new("RGBA", (pw + 40, ph + 60), (0, 0, 0, 0))
    ImageDraw.Draw(base).rounded_rectangle([0, 0, pw + 39, ph + 59], radius=14, fill=(40, 36, 34, 255), outline=(70, 66, 62, 255), width=3)
    sh, sx, sy = fx.shadow_of((pw + 40, ph + 60), W / 2, -300, cx, cy + 10, blur=26, a=180)
    lay.alpha_composite(sh, (sx, sy))
    lay.alpha_composite(base, (x0 - 20, y0 - 20))
    pos = C.clamp(k) * n
    cur = min(n, int(pos))
    frac = pos - cur

    def sheet(i):
        im = C.paper(pw, ph, seed=120 + i, tone=(222, 214, 196), dark=0.0).convert("RGBA")
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, pw - 1, 70], fill=(150, 40, 36, 255))
        d.text((pw / 2, 52), "ГОД", font=C.font("head_l", 32), fill=(240, 236, 230, 255), anchor="ms")
        d.text((pw / 2, ph * 0.66), years[i], font=C.font("head", 230), fill=C.INK + (255,), anchor="ms")
        for j in range(7):
            d.ellipse([60 + j * 85, 8, 60 + j * 85 + 14, 22], fill=(30, 28, 26, 255))
        return im

    # нижний (следующий) лист
    nxt = min(n, cur + 1) if frac > 0 else cur
    lay.alpha_composite(sheet(nxt if frac > 0 else cur), (x0, y0))
    if frac > 0 and cur < n:
        # верхний лист отрывается: поворот вокруг верхнего края и улёт вверх-вправо
        im = sheet(cur)
        e = C.smoother(frac)
        ang = -70 * e
        im = im.rotate(ang, Image.BICUBIC, expand=True, center=(0, 0))
        im = C.alpha(im, 1 - C.seg(frac, 0.6, 1.0))
        lay.alpha_composite(im, (int(x0 + 300 * e), int(y0 - 420 * e)))
    return lay


_net = {}


def neuroset(k, tt, seed=3, cx=W * 0.5, cy=H * 0.5, rx=620, ry=360, n=46):
    """нейросеть: узлы зажигаются, рёбра к ближайшим прорастают, по рёбрам бегут импульсы"""
    key = (seed, n)
    if key not in _net:
        rng = np.random.default_rng(seed)
        pts = []
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            r = math.sqrt(rng.uniform(0.05, 1.0))
            pts.append((math.cos(a) * r, math.sin(a) * r))
        edges = []
        for i in range(n):
            dists = sorted(((math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]), j) for j in range(n) if j != i))
            for _, j in dists[:3]:
                if (j, i) not in edges:
                    edges.append((i, j))
        _net[key] = (pts, edges)
    pts, edges = _net[key]
    P = [(cx + x * rx, cy + y * ry) for x, y in pts]
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    kk = C.clamp(k)
    m_nodes = kk * len(pts)
    m_edges = C.seg(kk, 0.25, 1.0) * len(edges)
    for e, (i, j) in enumerate(edges):
        ke = C.clamp(m_edges - e)
        if ke <= 0:
            continue
        x0, y0 = P[i]
        x1, y1 = P[j]
        xe, ye = x0 + (x1 - x0) * C.out_cubic(ke), y0 + (y1 - y0) * C.out_cubic(ke)
        d.line([(x0 * s, y0 * s), (xe * s, ye * s)], fill=(140, 142, 150, 200), width=2 * s)
        if ke >= 1:
            ph = (tt * 0.7 + e * 0.173) % 1.0
            px, py = x0 + (x1 - x0) * ph, y0 + (y1 - y0) * ph
            r = 4 * s
            d.ellipse([px * s - r, py * s - r, px * s + r, py * s + r], fill=C.RED + (230,))
    for i, (x, y) in enumerate(P):
        kn = C.clamp(m_nodes - i)
        if kn <= 0:
            continue
        r = (5 + 3 * C.out_back(kn)) * s
        a = int(255 * kn)
        d.ellipse([x * s - r * 2, y * s - r * 2, x * s + r * 2, y * s + r * 2], fill=C.WHITE + (int(a * 0.12),))
        d.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], fill=C.WHITE + (a,))
    return C.done(lay)


def dnk(k, tt, cx, cy, height, dim=1.0, turns=2.2):
    """спираль ДНК: две нити синусом, перекладины между ними, вращение по времени"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    kk = C.clamp(k)
    n = 64
    amp = height * 0.14
    pts1, pts2 = [], []
    top = cy - height / 2
    for i in range(n + 1):
        u = i / n
        if u > kk:
            break
        y = top + u * height
        ph = u * turns * 2 * math.pi + tt * 1.2
        x1 = cx + amp * math.sin(ph)
        x2 = cx + amp * math.sin(ph + math.pi)
        z1 = math.cos(ph)
        pts1.append((x1, y, z1))
        pts2.append((x2, y, -z1))
        if i % 4 == 2:
            a = int(140 * dim)
            d.line([(x1 * s, y * s), (x2 * s, y * s)], fill=(170, 172, 180, a), width=3 * s)
    for pts, col in ((pts1, C.WHITE), (pts2, C.RED)):
        for i in range(len(pts) - 1):
            (xa, ya, za), (xb, yb, zb) = pts[i], pts[i + 1]
            a = int((150 + 105 * (za + 1) / 2) * dim)
            w = int((4 + 3 * (za + 1) / 2) * s)
            d.line([(xa * s, ya * s), (xb * s, yb * s)], fill=col + (a,), width=w)
        for xa, ya, za in pts[::4]:
            r = (5 + 3 * (za + 1) / 2) * s
            d.ellipse([xa * s - r, ya * s - r, xa * s + r, ya * s + r], fill=col + (int(255 * dim),))
    out = C.done(lay)
    g = out.filter(ImageFilter.GaussianBlur(8))
    return Image.alpha_composite(C.alpha(g, 0.6), out)


def genom_pole(k, tt, dim=1.0):
    """поле геномов: сетка точек заполняется слева направо построчно, счётчик до ста тысяч"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    cols, rows = 50, 16
    x0, y0 = SAFE_X + 60, H * 0.27
    gx, gy = (W - 2 * SAFE_X - 120) / (cols - 1), (H * 0.36) / (rows - 1)
    kk = C.clamp(k)
    total = cols * rows
    m = kk * total
    for i in range(total):
        ki = C.clamp(m - i)
        if ki <= 0:
            break
        r, c = divmod(i, cols)
        x, y = x0 + c * gx, y0 + r * gy
        rad = (3.2 + 2.5 * (1 - ki)) * s
        fresh = C.clamp(1 - (m - i) / 60.0)
        col = C.mix(C.WHITE, C.RED, fresh)
        d.ellipse([x * s - rad, y * s - rad, x * s + rad, y * s + rad], fill=col + (int(255 * dim * (0.55 + 0.45 * ki)),))
    out = C.done(lay)
    if dim >= 1.0:
        v = int(round(100000 * C.out_expo(kk)))
        txt = "{:,}".format(v).replace(",", " ")
        num = C.text_layer([txt], "head", 150, C.RED, W / 2, H * 0.78, "ms", 0.04, a=C.clamp(kk * 3))
        sub = label("ГЕНОМОВ", C.clamp(kk * 3), H * 0.78 + 56, 36)
        out = C.over(out, num, sub)
    return out


def grif(k_in, k_bars, t):
    """документ на столе: строки текста; чёрные полосы закрывают их одна за другой слева направо"""
    img = lamp_bg(63).convert("RGBA")
    w, h = 1240, 820
    sheet = C.paper(w, h, seed=131, tone=(200, 192, 174), dark=0.0).convert("RGBA")
    d = ImageDraw.Draw(sheet)
    d.rectangle([0, 0, w - 1, h - 1], outline=(110, 100, 86, 255), width=3)
    d.text((w / 2, 110), "ФЕДЕРАЛЬНЫЙ ЗАКОН", font=C.font("head", 48), fill=C.INK + (255,), anchor="ms")
    d.text((w / 2, 150), "о генетических данных граждан · текст условный", font=C.font("serif_i", 26), fill=(100, 90, 80, 255), anchor="ms")
    rng = random.Random(7)
    lines_y = [230 + i * 62 for i in range(9)]
    for i, y in enumerate(lines_y):
        wl = rng.randint(620, 1080)
        d.line([(80, y), (80 + wl, y)], fill=(120, 110, 96, 255), width=5)
        d.line([(80, y + 18), (80 + rng.randint(300, 900), y + 18)], fill=(140, 130, 116, 255), width=3)
    n = len(lines_y)
    m = C.clamp(k_bars) * n
    for i, y in enumerate(lines_y):
        ki = C.clamp(m - i)
        if ki <= 0:
            break
        wl = int((w - 150) * C.out_cubic(ki))
        d.rectangle([70, y - 24, 70 + wl, y + 32], fill=(16, 14, 14, 255))
    kk = C.out_cubic(k_in)
    x0, y0 = int(W / 2 - w / 2), int(H * 0.52 - h / 2 + (1 - kk) * 400)
    sh, sx, sy = fx.shadow_of((w, h), W / 2, -300, x0 + w / 2, y0 + h / 2, blur=24, a=180)
    img.alpha_composite(sh, (sx, sy))
    img.alpha_composite(C.alpha(sheet, C.clamp(k_in * 2)), (x0, y0))
    out = img.convert("RGB")
    out = fx.fonar(out, W * 0.5, H * 0.5, 900, 560, 0.10, 0.045, t)
    return C.grain(out, t, 0.03)


def polosa_deneg(k_bar, k_split, tt):
    """полоса денег: растёт слева направо; потом правая половина уходит в черноту с вопросом"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    x0, x1 = SAFE_X + 40, W - SAFE_X - 40
    y = H * 0.5
    hh = 120
    kb = C.out_cubic(k_bar)
    xe = x0 + (x1 - x0) * kb
    d.rectangle([x0 * s, (y - hh / 2) * s, xe * s, (y + hh / 2) * s], fill=(190, 186, 178, 255))
    if kb >= 1:
        xm = (x0 + x1) / 2
        ks = C.smoother(k_split)
        a = int(255 * ks)
        d.rectangle([xm * s, (y - hh / 2) * s, (xm + (x1 - xm) * ks) * s, (y + hh / 2) * s], fill=(12, 12, 14, 255))
        d.rectangle([(xm - 3) * s, (y - hh / 2 - 30) * s, (xm + 3) * s, (y + hh / 2 + 30) * s], fill=C.RED + (255,))
        C.tracked(d, ((x0 + xm) / 2) * s, (y + 16) * s, "КОНТРАКТЫ", C.font("head", 44 * s), (30, 28, 26, 255), 0.1, "ms")
        if ks > 0.5:
            C.tracked(d, ((xm + x1) / 2) * s, (y + 24) * s, "?", C.font("head", 90 * s), C.RED + (a,), 0.0, "ms")
            C.tracked(d, ((xm + x1) / 2) * s, (y + hh / 2 + 60) * s, "ВЗНОСЫ · ИСТОЧНИК НЕ РАСКРЫТ", C.font("head_l", 30 * s), C.WHITE + (a,), 0.24, "ms")
    else:
        C.tracked(d, x0 * s, (y - hh / 2 - 24) * s, "900 МИЛЛИОНОВ РУБЛЕЙ", C.font("head_l", 32 * s), C.GREY + (255,), 0.24, "ls")
    return C.done(lay)


def shkala_programmy(k_fill, k_mark, tt):
    """шкала 2019…2027: деления по годам, заливка до «сейчас», красная метка на 2027"""
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    x0, x1 = SAFE_X + 60, W - SAFE_X - 60
    y = H * 0.55
    years = list(range(2019, 2028))
    n = len(years) - 1
    d.rectangle([x0 * s, (y - 26) * s, x1 * s, (y + 26) * s], fill=(34, 34, 38, 255), outline=(90, 90, 96, 255), width=2 * s)
    now = (2026 - 2019 + 0.9) / n
    xf = x0 + (x1 - x0) * now * C.out_cubic(k_fill)
    if xf > x0 + 6:
        d.rectangle([(x0 + 4) * s, (y - 22) * s, xf * s, (y + 22) * s], fill=(170, 166, 158, 255))
    f = C.font("head_r", 34 * s)
    for i, yr in enumerate(years):
        x = x0 + (x1 - x0) * i / n
        d.line([(x * s, (y - 40) * s), (x * s, (y + 40) * s)], fill=(140, 140, 146, 255), width=2 * s)
        col = C.RED if yr == 2027 else C.WHITE
        C.tracked(d, x * s, (y + 86) * s, str(yr), C.font("head" if yr == 2027 else "head_r", (54 if yr == 2027 else 34) * s), col + (255,), 0.04, "ms")
    if k_fill > 0.95:
        C.tracked(d, xf * s, (y - 60) * s, "СЕЙЧАС", C.font("head_l", 26 * s), C.GREY + (255,), 0.3, "ms")
    km = C.smoother(k_mark)
    if km > 0:
        a = int(255 * km)
        d.rectangle([(x1 - 5) * s, (y - 80 - 30 * km) * s, (x1 + 5) * s, (y + 60) * s], fill=C.RED + (a,))
        for j in range(2):
            ph = (tt * 0.9 + j * 0.5) % 1.0
            r = (14 + 90 * ph) * s
            d.ellipse([x1 * s - r, y * s - r, x1 * s + r, y * s + r], outline=C.RED + (int(a * (1 - ph)),), width=3 * s)
        C.tracked(d, x1 * s, (y + 136) * s, "КОНЕЦ ПРОГРАММЫ", C.font("head_l", 28 * s), C.WHITE + (a,), 0.3, "rs")
    return C.done(lay)
