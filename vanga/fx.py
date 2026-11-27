#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Новые эффекты фильма «Верица» — своей разработки, 23.11.2026.

  fonar        — фонарь следователя: тёмный документ, читается только пятно света
  scroll_blur  — быстрый скролл страницы с размытием движения
  proyavka     — проявка: текст выступает из бумаги, как снимок в проявителе
  vydelenie    — выделение курсором: красная полоса идёт по строке слева направо
  glitch       — перепись: строки кадра рвутся, каналы расходятся, слово переписано
  vidoiskatel  — видоискатель оператора: REC, таймкод, скобки, дрожь руки, зум ступенями
  raspad       — распад в зерно: застывший кадр рассыпается вверх пылью
  lampa        — качающаяся лампа над доской: свет ходит, тени карточек плывут
  flip_number  — механический счётчик: цифры перещёлкиваются с размытием
Всё numpy + PIL, кадр 1920×1080.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
from core import W, H, SS

_cache = {}


def _grid(w=W, h=H):
    key = ("grid", w, h)
    if key not in _cache:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _cache[key] = (xx, yy)
    return _cache[key]


def _noise(w, h, seed, scale):
    key = ("noise", w, h, seed, scale)
    if key not in _cache:
        _cache[key] = np.asarray(C.noise(w, h, seed, scale), np.float32) / 255.0
    return _cache[key]


# ── 1. фонарь следователя
def fonar(img, x, y, rx=520, ry=330, dark=0.14, flicker=0.0, t=0.0, warm=True):
    """img затемняется до dark, пятно света вокруг (x, y) эллипсом rx×ry."""
    xx, yy = _grid(*img.size)
    d2 = ((xx - x) / rx) ** 2 + ((yy - y) / ry) ** 2
    spot = np.exp(-d2 * 1.6)
    if flicker > 0:
        spot *= 1.0 + flicker * (math.sin(t * 37.0) * 0.5 + math.sin(t * 91.0 + 1.3) * 0.5)
    g = dark + (1.0 - dark) * np.clip(spot, 0, 1)
    a = np.asarray(img.convert("RGB"), np.float32) * g[:, :, None]
    if warm:
        a[:, :, 2] *= 0.90    # лампа тёплая: синий чуть прибрать
        a[:, :, 0] *= 1.03
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


# ── 2. скролл с размытием движения
def scroll_blur(crop_fn, y, vy, n=5, dt=1 / 60.0):
    """crop_fn(y) → кадр страницы при положении y; vy — скорость (px/с) — усредняем копии вдоль хода"""
    if abs(vy) < 40 or n <= 1:
        return crop_fn(y)
    acc = None
    for i in range(n):
        off = (i / (n - 1) - 0.5) * vy * dt * 2.0
        fr = np.asarray(crop_fn(y + off), np.float32)
        acc = fr if acc is None else acc + fr
    return Image.fromarray((acc / n).astype(np.uint8), "RGB")


# ── 3. проявка
def proyavka(base, true_img, box, k, seed=5):
    """base — кадр без строки (закрашена), true_img — кадр со строкой. box=(x0,y0,x1,y1)
    в кадре. k 0…1: строка проступает пятнами, сначала тёмная и мутная, потом чистая."""
    if k <= 0:
        return base
    x0, y0, x1, y1 = [int(v) for v in box]
    if k >= 1:
        out = base.copy()
        out.paste(true_img.crop((x0, y0, x1, y1)), (x0, y0))
        return out
    w, h = x1 - x0, y1 - y0
    n1 = _noise(w, h, seed, 26.0)
    n2 = _noise(w, h, seed + 3, 5.0)
    n = 0.65 * n1 + 0.35 * n2
    kk = C.smoother(k)
    m = np.clip((kk * 1.35 - n) / 0.22, 0, 1)
    tr = np.asarray(true_img.crop((x0, y0, x1, y1)), np.float32)
    bs = np.asarray(base.crop((x0, y0, x1, y1)), np.float32)
    # «мокрый» этап: проявившееся темнее и слегка расплывчато
    wet = np.asarray(Image.fromarray(tr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6 * (1 - kk))), np.float32)
    wet = wet * (0.72 + 0.28 * kk)
    res = bs * (1 - m[:, :, None]) + wet * m[:, :, None]
    out = base.copy()
    out.paste(Image.fromarray(np.clip(res, 0, 255).astype(np.uint8), "RGB"), (x0, y0))
    return out


# ── 4. выделение курсором
def vydelenie(base, true_img, box, k, color=C.RED, a=0.32, cursor=True):
    """строка открывается слева направо под красной полосой выделения; впереди I-курсор"""
    x0, y0, x1, y1 = [int(v) for v in box]
    out = base.copy()
    if k <= 0:
        return out
    kk = C.out_cubic(k)
    xe = int(x0 + (x1 - x0) * kk)
    if xe > x0:
        out.paste(true_img.crop((x0, y0, xe, y1)), (x0, y0))
    lay = Image.new("RGBA", out.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    pad = int((y1 - y0) * 0.35)
    d.rectangle([x0, y0 - pad, xe, y1 + pad], fill=color + (int(255 * a),))
    if cursor and k < 1:
        d.rectangle([xe - 1, y0 - pad - 6, xe + 1, y1 + pad + 6], fill=C.WHITE + (230,))
        d.rectangle([xe - 6, y0 - pad - 8, xe + 6, y0 - pad - 6], fill=C.WHITE + (230,))
        d.rectangle([xe - 6, y1 + pad + 6, xe + 6, y1 + pad + 8], fill=C.WHITE + (230,))
    return Image.alpha_composite(out.convert("RGBA"), lay).convert("RGB")


# ── 5. глитч-перепись
def glitch(img, k, seed=1, slices=14, shift=90, rgb=14):
    """k — сила 0…1: кадр рвётся на горизонтальные полосы со сдвигом, R и B расходятся"""
    if k <= 0:
        return img
    a = np.asarray(img.convert("RGB"), np.uint8)
    h, w = a.shape[:2]
    rng = np.random.default_rng(seed)
    out = a.copy()
    ys = np.sort(rng.integers(0, h, slices))
    for i in range(len(ys)):
        y0 = ys[i]
        y1 = ys[i + 1] if i + 1 < len(ys) else h
        if y1 - y0 < 2:
            continue
        if rng.random() < 0.55:
            dx = int(rng.uniform(-shift, shift) * k)
            out[y0:y1] = np.roll(a[y0:y1], dx, axis=1)
    # расхождение каналов
    off = int(rgb * k)
    if off > 0:
        r = np.roll(out[:, :, 0], off, axis=1)
        b = np.roll(out[:, :, 2], -off, axis=1)
        out = np.stack([r, out[:, :, 1], b], axis=2)
    # пара ярких строк
    for _ in range(int(3 * k) + 1):
        y = int(rng.integers(0, h))
        out[y:y + 2] = np.clip(out[y:y + 2].astype(np.int16) + 70, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGB")


# ── 6. видоискатель оператора
def handheld(t, amp=7.0, seed=0.0):
    """дрожь руки: гладкая сумма синусов, не покадровый джиттер"""
    x = amp * (math.sin(t * 1.7 + seed) * 0.5 + math.sin(t * 4.3 + seed * 2) * 0.3 + math.sin(t * 9.1 + 1) * 0.2)
    y = amp * (math.cos(t * 2.1 + seed) * 0.5 + math.sin(t * 5.7 + seed) * 0.3 + math.cos(t * 11.3) * 0.2)
    return x, y


def vidoiskatel(fr, t, tc0=847.0, zoom_step=0, rec=True, bw=0.55):
    """fr — кадр камеры (уже с дрожью). Поверх: скобки, REC с мигающей точкой, таймкод,
    батарея, шкала зума W…T. Картинка чуть обесцвечена и в строчках развёртки."""
    a = np.asarray(fr.convert("RGB"), np.float32)
    lum = a.mean(axis=2, keepdims=True)
    a = a * (1 - bw) + lum * bw
    a[:, :, 1] *= 1.03
    a[::3] *= 0.86                      # развёртка
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img = C.vignette(img, 0.5)
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    col = (235, 235, 230, 235)
    ix, iy, L, lw = 150, 84, 70, 4
    for cx, cy, sx, sy in ((ix, iy, 1, 1), (W - ix, iy, -1, 1), (ix, H - iy, 1, -1), (W - ix, H - iy, -1, -1)):
        d.line([(cx * s, cy * s), ((cx + sx * L) * s, cy * s)], fill=col, width=lw * s)
        d.line([(cx * s, cy * s), (cx * s, (cy + sy * L) * s)], fill=col, width=lw * s)
    # центр
    cx, cy = W / 2, H / 2
    d.line([((cx - 26) * s, cy * s), ((cx + 26) * s, cy * s)], fill=col, width=2 * s)
    d.line([(cx * s, (cy - 26) * s), (cx * s, (cy + 26) * s)], fill=col, width=2 * s)
    f = C.font("head_r", 34 * s)
    f2 = C.font("head_l", 26 * s)
    if rec:
        blink = (int(t * 2) % 2) == 0
        if blink:
            d.ellipse([(ix + 10) * s, (iy + 24) * s, (ix + 34) * s, (iy + 48) * s], fill=C.RED + (255,))
        C.tracked(d, (ix + 48) * s, (iy + 48) * s, "REC", f, col, 0.1)
    tc = tc0 + t
    hh, mm, ss = int(tc // 3600), int(tc % 3600 // 60), int(tc % 60)
    ff = int((tc - int(tc)) * 25)
    C.tracked(d, (W - ix) * s, (iy + 48) * s, "%02d:%02d:%02d:%02d" % (hh, mm, ss, ff), f, col, 0.08, "rs")
    # батарея
    bx, by = W - ix - 70, H - iy - 36
    d.rectangle([bx * s, by * s, (bx + 64) * s, (by + 28) * s], outline=col, width=2 * s)
    d.rectangle([(bx + 64) * s, (by + 9) * s, (bx + 69) * s, (by + 19) * s], fill=col)
    d.rectangle([(bx + 4) * s, (by + 4) * s, (bx + 40) * s, (by + 24) * s], fill=col)
    # шкала зума
    zx, zy = ix + 10, H - iy - 22
    C.tracked(d, zx * s, zy * s, "W", f2, col, 0.0)
    d.line([((zx + 30) * s, (zy - 9) * s), ((zx + 330) * s, (zy - 9) * s)], fill=col, width=2 * s)
    C.tracked(d, (zx + 342) * s, zy * s, "T", f2, col, 0.0)
    px = zx + 30 + 300 * min(1.0, 0.18 + 0.24 * zoom_step)
    d.rectangle([(px - 3) * s, (zy - 20) * s, (px + 3) * s, (zy + 2) * s], fill=C.RED + (255,))
    return C.over(img, C.done(lay)).convert("RGB")


# ── 7. распад в зерно
def raspad(frozen, k, seed=9, amp=260.0, bg=(6, 6, 7)):
    """застывший кадр рассыпается: пиксели уходят вверх с разной скоростью и гаснут"""
    if k <= 0:
        return frozen
    w, h = frozen.size
    if k >= 1:
        return Image.new("RGB", (w, h), bg)
    xx, yy = _grid(w, h)
    n_speed = _noise(w, h, seed, 7.0)           # мелкие комки
    n_dir = _noise(w, h, seed + 1, 120.0)       # общий ветер
    n_life = _noise(w, h, seed + 2, 4.0)
    kk = k * k
    dy = (0.35 + 0.65 * n_speed) * amp * kk * (0.6 + 0.8 * n_dir)
    dx = (n_dir - 0.5) * amp * 0.5 * kk + (n_speed - 0.5) * 30 * k
    sy = np.clip(yy + dy, 0, h - 1).astype(np.int32)
    sx = np.clip(xx + dx, 0, w - 1).astype(np.int32)
    src = np.asarray(frozen.convert("RGB"), np.float32)
    moved = src[sy, sx]
    alive = np.clip((n_life + 0.15 - k * 1.3) / 0.18, 0, 1)
    # пыль не уходит за край: что уехало снизу — гаснет
    alive *= np.clip((h - 1 - (yy + dy)) / 40.0, 0, 1)
    out = moved * alive[:, :, None] + np.array(bg, np.float32) * (1 - alive[:, :, None])
    out = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    return C.grain(out, k * 10, 0.06 * k)


# ── 8. качающаяся лампа
def lampa_pos(t, cx=W * 0.5, amp=520.0, period=3.4, phase=0.0):
    return cx + amp * math.sin(2 * math.pi * t / period + phase), -260.0


def lampa(img, lx, ly, r=1150.0, dark=0.10, cone=0.9):
    """свет от точки (lx, ly) над кадром: яркое пятно, края во тьме"""
    xx, yy = _grid(*img.size)
    d2 = ((xx - lx) / r) ** 2 + ((yy - ly) / (r * 1.25)) ** 2
    g = dark + (1 - dark) * np.exp(-d2 * cone)
    a = np.asarray(img.convert("RGB"), np.float32) * g[:, :, None]
    a[:, :, 2] *= 0.92
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def shadow_of(size, lx, ly, cx, cy, blur=18, a=170, depth=0.07):
    """тень карточки size с центром (cx, cy): уходит от лампы"""
    w, h = size
    dx = (cx - lx) * depth
    dy = (cy - ly) * depth * 0.6 + 10
    lay = Image.new("RGBA", (w + 120, h + 120), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle([60, 60, 60 + w, 60 + h], fill=(0, 0, 0, a))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return lay, int(cx - w / 2 - 60 + dx), int(cy - h / 2 - 60 + dy)


# ── 9. механический счётчик
def flip_number(values, k, cx, cy, px=220, color=C.WHITE, kind="head"):
    """values — список строк; k 0…1 — пробег по списку; цифры перещёлкиваются вверх с размытием"""
    n = len(values)
    pos = C.clamp(k) * (n - 1)
    i = min(n - 1, int(pos))
    frac = pos - i
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    f = C.font(kind, px * SS)
    step = px * 1.15 * SS
    # окно: клип по высоте через альфу (рисуем, потом режем маской)
    y = cy * SS + px * 0.36 * SS
    e = C.smoother(frac) if frac < 1 else 1
    blur = 1 if 0.05 < frac < 0.95 else 0
    cur_a = int(255 * (1 - e))
    nxt_a = int(255 * e)
    C.tracked(d, cx * SS, y - e * step, values[i], f, color + (cur_a if blur else 255,), 0.02, "ms")
    if i + 1 < n and frac > 0:
        C.tracked(d, cx * SS, y + (1 - e) * step, values[i + 1], f, color + (nxt_a,), 0.02, "ms")
    out = C.done(lay)
    if blur:
        out = out.filter(ImageFilter.GaussianBlur(3))
    # маска окна
    m = Image.new("L", out.size, 0)
    ImageDraw.Draw(m).rectangle([0, cy - px * 0.46, W, cy + px * 0.46], fill=255)
    r, g, b, al = out.split()
    al = Image.fromarray((np.asarray(al, np.float32) * np.asarray(m, np.float32) / 255).astype(np.uint8), "L")
    return Image.merge("RGBA", (r, g, b, al))


# ── курсор-прочерк (мигает)
def cursor(x, y, h=48, t=0.0, w=4, period=1.0, color=C.WHITE):
    if (t % period) > period * 0.5:
        return None
    im = C.layer()
    ImageDraw.Draw(im).rectangle([x * SS, (y - h) * SS, (x + w) * SS, y * SS], fill=color + (255,))
    return C.done(im)


def typed(text, k, kind="head_r", px=46, color=C.WHITE, x=96, y=H - 150, track=0.02, cur=True, t=0.0):
    """текст печатается по буквам до доли k; за последней буквой — курсор"""
    n = int(round(len(text) * C.clamp(k)))
    s = text[:n]
    lay = C.text_layer([s], kind, px, color, x, y, "ls", track)
    if cur:
        d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        tw = C.text_w(d, s, C.font(kind, px * SS), track) / SS
        c = cursor(x + tw + 6, y + px * 0.1, int(px * 0.95), t if k >= 1 else 0.0, 4, 1.0, color)
        lay = C.over(lay, c)
    return lay
