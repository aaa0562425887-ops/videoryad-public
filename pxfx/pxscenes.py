#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Шесть клипов: что именно забрано из pixelfx и как это выглядит у нас.

Каждая сцена показывает ОДИН приём и, где можно, сразу сравнение «как было /
как стало» в одном кадре — чтобы разница читалась без слов.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from pxcore import (FPS, H, SANS, SANS_B, SANS_BL, W, Frame, Particles, at, backdrop, ease_in_out,
                    ease_lin, ease_out_expo, ease_out_quart, font, label, loopnoise, plate, ramp, seg)

TXT = (238, 242, 246)
TXT2 = (150, 168, 188)


def title(f, text, sub=None):
    """Подпись приёма — крупно, по-русски, внизу слева."""
    d = f.draw()
    d.text((80, H - 150), text, font=font(SANS_BL, 54), fill=TXT + (255,))
    if sub:
        d.text((80, H - 84), sub, font=font(SANS, 34), fill=TXT2 + (255,))


def _divider(f, xs, col=(255, 255, 255)):
    d = f.draw()
    d.line([xs, 0, xs, H], fill=col + (90,), width=2)


# ── 01. СВЕТОВОЙ БУФЕР: та же сцена без света и со светом
def s01(t):
    bg = backdrop("студия")
    rp = ramp("5 МИНУТ")
    xs = int(W * (0.18 + 0.64 * ease_in_out(seg(t, 0.12, 0.88))))

    # собираем ПОЛНЫЙ кадр со светом и ПОЛНЫЙ кадр без него, потом склеиваем по шторке
    def build(with_light):
        f = Frame()
        d = f.draw()
        cx, cy = W // 2, int(H * 0.46)
        # горячее ядро: тело пиксельными шагами рампы
        for i in range(7, 0, -1):
            r = 26 + i * 13
            d.ellipse([cx - r, cy - r * 0.92, cx + r, cy + r * 0.92], fill=at(rp, 0.3 + 0.1 * (7 - i)) + (255,))
        pul = 1 + 0.08 * math.sin(t * math.tau * 3)
        plate(f, [cx - 300, cy + 190, cx + 300, cy + 262], (10, 14, 22), 230, at(rp, 0.6), 3)
        d.text((cx, cy + 226), "ЭКСПОРТ НЕФТИ", font=font(SANS_B, 38), fill=TXT + (255,), anchor="mm")
        if with_light:
            f.splat(cx, cy, 150 * pul, at(rp, 0.75), 1.05)
            f.splat(cx, cy, 300 * pul, at(rp, 0.5), 0.42)
            f.splat(cx, cy + 226, 210, at(rp, 0.6), 0.16)
        return f.composite(bg, glow=1.0 if with_light else 0.0)

    a, b = build(False), build(True)
    out = a.copy()
    out.paste(b.crop((xs, 0, W, H)), (xs, 0))
    f = Frame()
    _divider(f, xs)
    d = f.draw()
    d.text((xs - 40, 90), "БЕЗ СВЕТА", font=font(SANS_B, 40), fill=(150, 160, 175, 255), anchor="rt")
    d.text((xs + 40, 90), "СО СВЕТОМ", font=font(SANS_B, 40), fill=(255, 226, 150, 255), anchor="lt")
    title(f, "СВЕТОВОЙ БУФЕР", "свечение кладётся отдельным слоем поверх кадра, а не подмешивается в цвет")
    return f.composite(out, glow=0.0)


# ── 02. ИСКРЫ: частицы на фиксированном шаге, каждая своя
_P2 = {}


def s02(t):
    key = "p2"
    if t < 1e-6 or key not in _P2:
        p = Particles(seed=7, grav=1500.0, drag=0.85, bounce=0.42, ground=H * 0.78)
        _P2[key] = {"p": p, "t": 0.0, "fired": set()}
    st = _P2[key]
    p = st["p"]
    dt = 1.0 / FPS
    # три удара по времени: видно, что каждая вспышка живёт своей жизнью
    rp = ramp("ОГОНЬ")
    hits = [(0.08, W * 0.30), (0.40, W * 0.52), (0.70, W * 0.74)]
    for i, (ht, hx_) in enumerate(hits):
        if t >= ht and i not in st["fired"]:
            st["fired"].add(i)
            p.emit(150, hx_, H * 0.52, speed=(240, 1150), ang=(-math.pi, 0.25),
                   life=(0.30, 1.25), size=(2.0, 6.0), rp=rp, drift=40)
            p.emit(26, hx_, H * 0.52, speed=(40, 150), ang=(-math.pi * 0.8, -math.pi * 0.2),
                   life=(0.9, 1.8), size=(10, 22), rp=ramp("ДЫМ"), kind="smoke", delay=(0.0, 0.25))
    while st["t"] < t:
        p.step(dt)
        st["t"] += dt

    f = Frame()
    d = f.draw()
    d.line([0, H * 0.78, W, H * 0.78], fill=(60, 70, 84, 255), width=3)
    p.draw(f)
    # вспышка на кадре удара — «герой-кадр»
    for i, (ht, hx_) in enumerate(hits):
        k = 1 - seg(t, ht, ht + 0.012)      # 0,012 от сцены ≈ 0,08 с — две-три рамки
        if k > 0:
            f.splat(hx_, H * 0.52, 150 * k, (255, 246, 228), 0.75 * k)
            f.splat(hx_, H * 0.52, 60, (255, 255, 255), 0.9 * k)
    d.text((80, 90), "УДАР · ИСКРЫ · ДЫМ", font=font(SANS_B, 40), fill=TXT + (255,))
    d.text((80, 142), "симуляция идёт шагами по 1/120 с — не зависит от частоты кадров",
           font=font(SANS, 30), fill=TXT2 + (255,))
    title(f, "ЧАСТИЦЫ С ХАРАКТЕРОМ", "у каждой искры свой размер, скорость, задержка и срок жизни")
    return f.composite(backdrop("студия"))


# ── 03. ДЫМ И ОГОНЬ: две системы — пламя вверх, дым своей тягой
_P3 = {}


def s03(t):
    if t < 1e-6 or "f" not in _P3:
        _P3["f"] = Particles(seed=11, grav=-760.0, drag=1.45)          # языки пламени
        _P3["s"] = Particles(seed=12, grav=0.0, drag=0.9, lift=165.0)  # дым своей тягой
        _P3["t"] = 0.0
        _P3["e"] = 0.0
        _P3["es"] = 0.0
    dt = 1.0 / FPS
    rpf, rps = ramp("ОГОНЬ"), ramp("ДЫМ")
    bx, by = W * 0.5, H * 0.74
    while _P3["t"] < t:
        _P3["e"] += dt
        _P3["es"] += dt
        n = loopnoise(_P3["t"] / 3.0, seed=3, n=3)
        if _P3["e"] >= 0.035:
            _P3["e"] = 0.0
            _P3["f"].emit(4, bx + n * 18, by, speed=(90, 230), ang=(-math.pi * 0.62, -math.pi * 0.38),
                          life=(0.45, 1.05), size=(4, 11), rp=rpf, drift=55)
        if _P3["es"] >= 0.12:
            _P3["es"] = 0.0
            _P3["s"].emit(2, bx + n * 30, by - 90, speed=(20, 70), ang=(-math.pi * 0.70, -math.pi * 0.30),
                          life=(2.2, 3.8), size=(26, 52), rp=rps, kind="smoke", drift=34)
        _P3["f"].step(dt)
        _P3["s"].step(dt)
        _P3["t"] += dt

    f = Frame()
    d = f.draw()
    _P3["s"].draw(f)          # дым позади пламени
    # очаг: приплюснутое ядро жёсткими шагами рампы
    for i in range(6, 0, -1):
        rx, ry = (10 + i * 11) * 1.7, (10 + i * 11) * 0.45
        d.ellipse([bx - rx, by - ry, bx + rx, by + ry], fill=at(rpf, 0.22 + 0.13 * (6 - i)) + (255,))
    _P3["f"].draw(f)
    pul = 1 + 0.10 * math.sin(t * math.tau * 7) + 0.06 * loopnoise(t, seed=9, n=3)
    f.splat(bx, by - 30, 190 * pul, at(rpf, 0.72), 0.95)
    f.splat(bx, by - 90, 420, at(rpf, 0.45), 0.26)
    # отсвет на земле — свет виден не только на источнике
    f.splat(bx, by + 40, 520, at(rpf, 0.35), 0.16, hard=3.4)
    title(f, "ДЫМ — ЭТО НЕ СЕТОЧКА", "клубы по-настоящему полупрозрачные и подсвечены со стороны огня")
    return f.composite(backdrop("ночь"))


# ── 04. ХОД ДВИЖЕНИЯ: линейно против outExpo + герой-кадр
def s04(t):
    f = Frame()
    d = f.draw()
    rp = ramp("ПЛАНЕТА")
    bg = backdrop("студия")
    LAND = 0.62

    for row, (nm, ez, hero) in enumerate([("ЛИНЕЙНО, БЕЗ ВСПЫШКИ", ease_lin, False),
                                          ("БЫСТРО ВОШЛО — МЕДЛЕННО ВЫШЛО + ВСПЫШКА", ease_out_expo, True)]):
        cy = int(H * (0.33 + row * 0.33))
        k = ez(seg(t, 0.12, LAND))
        x = int(W * 0.14 + (W * 0.52 - W * 0.14) * k)
        # плашка меряется шрифтом, а не на глаз: число слева, подписи справа от него
        fn_num, fn_cap, fn_sub = font(SANS_BL, 92), font(SANS_B, 30), font(SANS, 26)
        num = "47 %"
        wn = d.textlength(num, font=fn_num)
        wc = max(d.textlength("ДОЛЯ ЭКСПОРТА", font=fn_cap), d.textlength("за четвёртый квартал", font=fn_sub))
        pad, gap = 34, 30
        bw, bh = int(pad + wn + gap + wc + pad), 150
        plate(f, [x, cy - bh // 2, x + bw, cy + bh // 2], (9, 13, 21), 235, at(rp, 0.55), 3)
        d.text((x + pad, cy), num, font=fn_num, fill=TXT + (255,), anchor="lm")
        cx2 = x + pad + wn + gap
        d.text((cx2, cy - 30), "ДОЛЯ ЭКСПОРТА", font=fn_cap, fill=at(rp, 0.75) + (255,))
        d.text((cx2, cy + 10), "за четвёртый квартал", font=fn_sub, fill=TXT2 + (255,))
        if hero:
            fl = 1 - seg(t, LAND, LAND + 0.014)    # ≈ 0,1 с: две-три рамки, не зарево
            if fl > 0:
                f.splat(x + bw, cy, 170 * fl, (255, 255, 255), 0.85 * fl)
                d.rectangle([x, cy - bh // 2, x + bw, cy + bh // 2],
                            outline=(255, 255, 255, int(230 * fl)), width=5)
            f.splat(x + bw * 0.5, cy, 230, at(rp, 0.6), 0.10)
        d.text((80, cy - bh // 2 - 54), nm, font=font(SANS_B, 32),
               fill=((255, 226, 150) if hero else (150, 160, 175)) + (255,))
    title(f, "ХОД ДВИЖЕНИЯ И ГЕРОЙ-КАДР", "одно и то же число: сверху без хода, снизу с ходом и вспышкой на упоре")
    return f.composite(bg)


# ── 05. ПЕТЛЯ БЕЗ ШВА: два круга подряд, на стыке не дёргается
def s05(t):
    f = Frame()
    d = f.draw()
    rp = ramp("ХОЛОД")
    loops = 2
    ph = (t * loops) % 1.0          # фаза круга
    lap = int(t * loops) + 1
    rng = np.random.default_rng(5)
    for i in range(130):
        bx, by = rng.uniform(0, W), rng.uniform(0, H)
        n1, n2 = loopnoise(ph, seed=i, n=3), loopnoise(ph, seed=i + 500, n=2)
        x = (bx + n1 * 150 + ph * 90 * (1 + i % 3)) % W
        y = by + n2 * 70
        r = 2.0 + 3.4 * ((i % 7) / 6.0)
        gl = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(ph * math.tau * (1 + i % 3) + i))
        col = at(rp, 0.45 + 0.5 * gl)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (255,))
        f.splat(x, y, r * 5.5, col, 0.32 * gl)
    # полоса прогресса круга — видно момент стыка
    d.text((80, 84), "КРУГ %d ИЗ %d · на стыке рывка нет" % (lap, loops),
           font=font(SANS_B, 36), fill=TXT + (255,))
    plate(f, [80, 158, W - 80, 170], (38, 48, 60), 210)
    plate(f, [80, 158, 80 + int((W - 160) * ph), 170], at(rp, 0.75), 255)
    f.splat(80 + (W - 160) * ph, 164, 26, at(rp, 0.85), 0.5)
    title(f, "ПЕТЛЯ БЕЗ ШВА", "шум берётся по кругу, поэтому последний кадр сходится с первым")
    return f.composite(backdrop("ночь"))


# ── 06. ОДИН ЭФФЕКТ, ТРИ ГАММЫ КАНАЛОВ
_P6 = {}


def s06(t):
    chans = ["ПЛАНЕТА", "5 МИНУТ", "ДИПЛОМАТИЯ"]
    if t < 1e-6 or "ps" not in _P6:
        _P6["ps"] = [Particles(seed=21 + i, grav=820.0, drag=0.7, bounce=0.3, ground=H * 0.70)
                     for i in range(3)]
        _P6["t"] = 0.0
        _P6["fired"] = set()
    dt = 1.0 / FPS
    for i, ch in enumerate(chans):
        if t >= 0.10 + i * 0.16 and i not in _P6["fired"]:
            _P6["fired"].add(i)
            cx = W * (0.2 + 0.3 * i)
            _P6["ps"][i].emit(120, cx, H * 0.46, speed=(200, 820), ang=(-math.pi, 0.2),
                              life=(0.35, 1.2), size=(2, 5.5), rp=ramp(ch), drift=30)
    while _P6["t"] < t:
        for p in _P6["ps"]:
            p.step(dt)
        _P6["t"] += dt

    f = Frame()
    d = f.draw()
    for i, ch in enumerate(chans):
        rp = ramp(ch)
        cx = W * (0.2 + 0.3 * i)
        for j in range(5, 0, -1):
            r = 14 + j * 9
            d.ellipse([cx - r, H * 0.46 - r, cx + r, H * 0.46 + r], fill=at(rp, 0.26 + 0.12 * (5 - j)) + (255,))
        pul = 1 + 0.07 * math.sin(t * math.tau * 3 + i)
        f.splat(cx, H * 0.46, 128 * pul, at(rp, 0.58), 0.42)
        f.splat(cx, H * 0.46, 300 * pul, at(rp, 0.42), 0.20)
        _P6["ps"][i].draw(f)
        plate(f, [cx - 170, H * 0.74, cx + 170, H * 0.74 + 66], (10, 14, 22), 230, at(rp, 0.65), 3)
        d.text((cx, H * 0.74 + 33), ch, font=font(SANS_B, 34), fill=TXT + (255,), anchor="mm")
    d.line([0, H * 0.70, W, H * 0.70], fill=(60, 70, 84, 255), width=3)
    title(f, "ОДИН ЭФФЕКТ, ГАММА ПО КАНАЛУ", "цвет приходит рампой извне — код эффекта не меняется")
    return f.composite(backdrop("студия"))


SCENES = {
    "01": (s01, 7.0),
    "02": (s02, 7.0),
    "03": (s03, 7.0),
    "04": (s04, 7.0),
    "05": (s05, 8.0),
    "06": (s06, 7.0),
}
