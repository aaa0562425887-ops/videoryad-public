#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Приёмы фильма «Ванга 2027» (новые для этого фильма — после приёмки на полку):

* ЦИФРЫ 2027 — четыре красные цифры на чёрном собираются из полос, дышат, светятся.
  Сквозной образ фильма (блоки 0, 7, 8, 12, 14); обратного отсчёта нет нигде.
* КАРТОЧКА ЗАГОЛОВКА — снимок страницы издания карточкой с наклоном и тенью,
  плашка издания и даты; если снимка нет — честная типографская копия строки.
* ОКНО ОРИГИНАЛА — осциллограмма речи и перевод, печатающийся по букве (как у Верицы).
* GRADE / HANDHELD — тёмный строй архивного видео и лёгкая рука.
"""
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import fx
from core import W, H, SS

SAFE_X, SAFE_Y = 96, 54


# ─────────────────────────── общее ───────────────────────────
def fit_px(text, kind, px, maxw, track=0.0):
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    while px > 20 and C.text_w(d, text, C.font(kind, px * SS), track) / SS > maxw:
        px -= 4
    return px


def word(text, k, y, px=160, kind="head", color=C.WHITE, track=0.06, x=W / 2, anchor="ms", rise=40, maxw=W - 2 * SAFE_X):
    if k <= 0:
        return None
    px = fit_px(text, kind, px, maxw, track)
    kk = C.out_cubic(k)
    return C.text_layer([text], kind, px, color, x, y + (1 - kk) * rise, anchor, track, a=C.clamp(k * 2))


def label(text, k, y, px=34, color=C.GREY, x=W / 2, anchor="ms", track=0.36):
    if k <= 0:
        return None
    return C.text_layer([text], "head_l", px, color, x, y, anchor, track, a=k)


def red_line(k, x0, x1, y, w=5, a=255):
    if k <= 0:
        return None
    im = C.layer()
    ImageDraw.Draw(im).rectangle([x0 * SS, y * SS, (x0 + (x1 - x0) * C.out_cubic(k)) * SS, (y + w) * SS], fill=C.RED + (a,))
    return C.done(im)


def flash(img, tt, d=0.1, a=0.6):
    if tt >= d:
        return img
    return Image.blend(img.convert("RGB"), Image.new("RGB", img.size, C.WHITE), a * (1 - tt / d))


def shots(t, lst, dur):
    for i, (t0, fn) in enumerate(lst):
        t1 = lst[i + 1][0] if i + 1 < len(lst) else dur
        if t < t1 or i == len(lst) - 1:
            return fn, max(0.0, t - t0), max(0.2, t1 - t0)
    return lst[-1][1], 0.0, 1.0


_bg = {}


def dark_bg(seed=7, tone=(26, 25, 28)):
    if (seed, tone) not in _bg:
        p = C.paper(W, H, seed=seed, tone=tone, dark=0.0).filter(ImageFilter.GaussianBlur(1.2))
        _bg[(seed, tone)] = C.vignette(p, 0.55)
    return _bg[(seed, tone)]


def black():
    return Image.new("RGB", (W, H), (4, 4, 5))


def zoom_at(img, z, cx, cy):
    if z <= 1.0:
        return img
    w, h = img.size
    cw, ch = w / z, h / z
    x0 = min(max(0, cx - cw / 2), w - cw)
    y0 = min(max(0, cy - ch / 2), h - ch)
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.LANCZOS)


def grade(fr, k=1.0):
    """тёмный строй архивного видео: цвет приглушён, тени провалены, холод в тенях"""
    a = np.asarray(fr.convert("RGB"), np.float32) / 255.0
    lum = a.mean(axis=2, keepdims=True)
    a = a * (1 - 0.40 * k) + lum * 0.40 * k
    a = np.clip((a - 0.05 * k) * (1 + 0.16 * k), 0, 1)
    a = a ** (1 + 0.20 * k)
    a[:, :, 2] += 0.02 * k * (1 - lum[:, :, 0])[:, :, None][:, :, 0]
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), "RGB")


_v = {}


def vid(key, name, start=0.0, **kw):
    if key not in _v:
        _v[key] = C.Vid(name, start, **kw)
    return _v[key]


def vanga(key, name, tt, src=0.0, zoom=1.0, cx=0.5, cy=0.5, push=0.05, hand=2.5, k_grade=0.9, bw=0.0):
    """архивный кадр: кроп (срезает логотип и вшитые субтитры), медленный наезд, лёгкая рука"""
    fr = vid(key, name, src, zoom=zoom, cx=cx, cy=cy).at(tt)
    hx, hy = fx.handheld(tt, hand, hash(key) % 7)
    z = 1.0 + push * tt
    img = zoom_at(fr, z, W / 2 + hx, H / 2 + hy)
    img = grade(img, k_grade)
    if bw > 0:
        a = np.asarray(img, np.float32)
        lum = a.mean(axis=2, keepdims=True)
        img = Image.fromarray(np.clip(a * (1 - bw) + lum * bw, 0, 255).astype(np.uint8), "RGB")
    return img


# ─────────────────────────── ЦИФРЫ 2027 ───────────────────────────
_c27 = {}


def _digits_layer(text, px, color):
    key = (text, px, color)
    if key not in _c27:
        lay = C.layer()
        d = ImageDraw.Draw(lay)
        f = C.font("head", px * SS)
        C.tracked(d, W / 2 * SS, (H / 2 + px * 0.36) * SS, text, f, color + (255,), 0.04, "ms")
        _c27[key] = lay
    return _c27[key]


def cifry(k, t, px=440, text="2027", a=1.0, glow=1.0, breathe=0.015, seed=3, color=C.RED):
    """Четыре цифры собираются из вертикальных полос (k 0→1), светятся и чуть дышат.
    k<1 — сборка: полосы приходят с шумом и сдвигом по вертикали, яркость мерцает."""
    if k <= 0 or a <= 0:
        return None
    sc = 1.0 + breathe * math.sin(t * 1.7)
    lay = _digits_layer(text, int(px * sc), color)
    arr = np.asarray(lay).copy()
    if k < 1.0:
        kk = C.smoother(k)
        rng = np.random.default_rng(seed)
        ncol = arr.shape[1] // (6 * SS)
        order = rng.permutation(ncol)
        thr = rng.random(ncol)
        shift = rng.integers(-90, 90, ncol) * SS
        out = np.zeros_like(arr)
        for i in range(ncol):
            x0, x1 = i * 6 * SS, (i + 1) * 6 * SS
            if thr[i] < kk:
                local = C.clamp((kk - thr[i]) / 0.25)
                sh = int(shift[i] * (1 - local))
                col = np.roll(arr[:, x0:x1], sh, axis=0)
                col[:, :, 3] = (col[:, :, 3].astype(np.float32) * (0.35 + 0.65 * local)).astype(np.uint8)
                out[:, x0:x1] = col
        arr = out
        # мерцание
        fl = 0.75 + 0.25 * abs(math.sin(t * 23.0 + seed))
        arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * fl).astype(np.uint8)
    im = Image.fromarray(arr, "RGBA")
    if a < 1.0:
        al = im.split()[3].point(lambda v: int(v * a))
        im.putalpha(al)
    base = im.resize((W, H), Image.LANCZOS)
    if glow > 0:
        g = base.filter(ImageFilter.GaussianBlur(28))
        ga = g.split()[3].point(lambda v: int(min(255, v * 0.9 * glow)))
        g.putalpha(ga)
        g2 = base.filter(ImageFilter.GaussianBlur(90))
        g2a = g2.split()[3].point(lambda v: int(min(255, v * 0.5 * glow)))
        g2.putalpha(g2a)
        out = Image.alpha_composite(Image.alpha_composite(g2, g), base)
        return out
    return base


def cifry_frame(k, t, bg=None, **kw):
    img = bg if bg is not None else black()
    return C.over(img, cifry(k, t, **kw)).convert("RGB")


# ─────────────────────────── карточки заголовков ───────────────────────────
# издание → (имя файла снимка, название, дата на экране, заголовок, строка про 2027)
SHOTS = {
    "vt": ("shot_vt.png", "VT", "15 октября 2026", "Baba Vanga makes chilling 2027 prediction involving Vladimir Putin",
           "By the start of 2027, Russia's long-term leader would no longer be at the country's helm."),
    "unilad": ("shot_unilad.png", "UNILAD", "2 ноября 2026",
               "Baba Vanga's 'predictions for 2027' include superhuman pandemic survivors and an AI-fuelled gold surge",
               "Russia's leader Vladimir Putin would not be leader of the nation by the beginning of 2027."),
    "newsner": ("shot_newsner.png", "NEWSNER", "2 ноября 2026",
                "Baba Vanga makes predictions for 2027 – 'disease will ravage earth's population'",
                "Some Baba Vanga commentators say she predicted that Vladimir Putin would no longer be Russia's leader by the start of 2027."),
    "skyhistory": ("shot_skyhistory.png", "SKY HISTORY", "2026", "What does Baba Vanga predict for 2027?",
                   "The soothsayer allegedly believed that Russia's longtime president Vladimir Putin would no longer be at the helm by the start of 2027."),
}
# окно снимка для карточки: (y-центр в px снимка, высота окна в px снимка); None — весь верх
SHOT_VIEW = {"vt": (3650, 1300), "unilad": (800, 1300), "newsner": (560, 1100), "skyhistory": (1570, 1110)}
# рамка строки про 2027 на снимке (x0, y0, x1, y1) в px снимка; None — типографская копия
SHOT_LINE = {"vt": (480, 4075, 1660, 4160), "unilad": (20, 6385, 1515, 6465), "newsner": (105, 3590, 1110, 3665), "skyhistory": None}
# рамка ПОСЛЕДНЕЙ строки фразы (там год) — под ней красная черта
SHOT_UNDER = {"vt": (480, 4120, 1180, 4160), "unilad": (20, 6428, 500, 6465), "newsner": (105, 3630, 640, 3665)}

_sh = {}


def shot_img(name):
    if name in _sh:
        return _sh[name]
    fn = SHOTS[name][0]
    p = C.apath(fn)
    im = Image.open(p).convert("RGB") if os.path.exists(p) else None
    _sh[name] = im
    return im


def _wrap(text, kind, px, maxw):
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    f = C.font(kind, px)
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        tst = (cur + " " + w_).strip()
        if d.textlength(tst, font=f) <= maxw:
            cur = tst
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def page_card(name, size=(1280, 760)):
    """картинка карточки: верх снимка страницы либо типографская копия заголовка"""
    key = ("card", name, size)
    if key in _sh:
        return _sh[key]
    cw, ch = size
    im = shot_img(name)
    if im is not None:
        view = SHOT_VIEW.get(name)
        iw, ih = im.size
        if view:
            yc, hh = view
            ww = hh * cw / ch
            if ww > iw:
                ww, hh = iw, iw * ch / cw
            x0 = max(0, (iw - ww) / 2)
            crop = im.crop((int(x0), int(max(0, yc - hh / 2)), int(x0 + ww), int(max(0, yc - hh / 2) + hh)))
        else:
            hh = iw * ch / cw
            crop = im.crop((0, 0, iw, int(hh)))
        card = crop.resize((cw, ch), Image.LANCZOS)
    else:
        _, outlet, date, head, line = SHOTS[name]
        card = Image.new("RGB", (cw, ch), (244, 242, 238))
        d = ImageDraw.Draw(card)
        d.rectangle([0, 0, cw, 92], fill=(22, 22, 26))
        d.text((48, 46), outlet, font=C.font("black", 44), fill=(245, 245, 245), anchor="lm")
        d.text((cw - 48, 46), date.upper(), font=C.font("head_l", 30), fill=(190, 190, 190), anchor="rm")
        y = 150
        for ln in _wrap(head, "sans_b", 54, cw - 96):
            d.text((48, y), ln, font=C.font("sans_b", 54), fill=(20, 20, 24))
            y += 66
        y += 30
        d.rectangle([48, y, cw - 48, y + 2], fill=(200, 200, 200))
        y += 36
        for ln in _wrap(line, "serif", 40, cw - 96):
            d.text((48, y), ln, font=C.font("serif", 40), fill=(40, 40, 44))
            y += 52
        d.text((48, ch - 40), "ЦИТАТА СО СТРАНИЦЫ · ОФОРМЛЕНИЕ НАШЕ", font=C.font("head_l", 22), fill=(150, 150, 150), anchor="lm")
    _sh[key] = card
    return card


def card_layer(card, cx, cy, scale=1.0, tilt=0.0, rot=0.0, a=1.0, shadow=True):
    """карточка на кадре: масштаб, лёгкая перспектива (tilt — доля), поворот, тень"""
    cw, ch = card.size
    w, h = int(cw * scale), int(ch * scale)
    im = card.resize((w, h), Image.LANCZOS).convert("RGBA")
    if abs(tilt) > 1e-3:
        # перспектива: одна сторона ниже другой
        dy = int(h * 0.08 * tilt)
        dx = int(w * 0.03 * abs(tilt))
        src = [(0, 0), (w, 0), (w, h), (0, h)]
        if tilt > 0:
            dst = [(dx, dy), (w, 0), (w, h), (dx, h - dy)]
        else:
            dst = [(0, 0), (w - dx, dy), (w - dx, h - dy), (0, h)]
        coeffs = _persp(dst, src)
        im = im.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    if abs(rot) > 1e-3:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.paste((0, 0, 0, 170), (0, 0, im.size[0], im.size[1]), im.split()[3])
        sh = sh.filter(ImageFilter.GaussianBlur(26))
        lay.alpha_composite(sh, (int(cx - im.size[0] / 2 + 18), int(cy - im.size[1] / 2 + 26)))
    lay.alpha_composite(im, (int(cx - im.size[0] / 2), int(cy - im.size[1] / 2)))
    if a < 1.0:
        al = lay.split()[3].point(lambda v: int(v * a))
        lay.putalpha(al)
    return lay


def _persp(pa, pb):
    A = []
    for (x, y), (X, Y) in zip(pa, pb):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
    A = np.array(A, np.float64)
    B = np.array([v for p in pb for v in p], np.float64)
    res = np.linalg.solve(A, B)
    return tuple(res)


def outlet_tag(name, k, x=W - SAFE_X, y=140):
    """плашка издания и даты — справа сверху, как date_tag карты"""
    if k <= 0:
        return None
    _, outlet, date, _, _ = SHOTS[name]
    im = C.layer()
    d = ImageDraw.Draw(im)
    a = int(255 * C.smoother(k))
    f = C.font("head", 56 * SS)
    C.tracked(d, x * SS, y * SS, outlet, f, C.WHITE + (a,), 0.08, "rs")
    d.rectangle([(x - 170) * SS, (y + 14) * SS, x * SS, (y + 17) * SS], fill=C.RED + (a,))
    f2 = C.font("head_l", 26 * SS)
    C.tracked(d, x * SS, (y + 52) * SS, date.upper(), f2, C.GREY + (a,), 0.3, "rs")
    return C.done(im)


def sentence_view(name, k_zoom=0.0, t=0.0):
    """крупно строка про 2027: кроп снимка по SHOT_LINE (k_zoom 0 — вся строка в кадре, 1 — наезд на её конец,
    где имя и год) либо типографская карточка строки. Возвращает (картинка RGB, рамка строки в px кадра)."""
    im = shot_img(name)
    box = SHOT_LINE.get(name)
    if im is not None and box:
        x0, y0, x1, y1 = box
        bw = (x1 - x0) + 160
        sc_fit = min(W / bw, 3.2)
        kz = C.smoother(C.clamp(k_zoom))
        sc = sc_fit * C.lerp(1.0, 1.14, kz)
        cw, ch = W / sc, H / sc
        xc = (x0 + x1) / 2
        yc = (y0 + y1) / 2 + C.lerp(30, 0, kz)
        iw, ih = im.size
        cx0 = min(max(0, xc - cw / 2), max(0, iw - cw))
        cy0 = min(max(0, yc - ch / 2), max(0, ih - ch))
        crop = im.crop((int(cx0), int(cy0), int(cx0 + cw) + 1, int(cy0 + ch) + 1)).resize((W, H), Image.LANCZOS)
        a = np.asarray(crop, np.float32)
        a *= 0.90
        a[:, :, 0] *= 0.97
        crop = C.vignette(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB"), 0.35)
        u = SHOT_UNDER.get(name, box)
        fb = ((u[0] - cx0) * sc, (u[1] - cy0) * sc, (u[2] - cx0) * sc, (u[3] - cy0) * sc)
        return crop, fb
    # типографская копия: бумага, строка крупно, издание и дата
    _, outlet, date, head, line = SHOTS[name]
    img = C.paper(W, H, seed=11, tone=(236, 232, 224), dark=0.0)
    d = ImageDraw.Draw(img)
    px = 58
    lines = _wrap(line, "serif", px, W - 2 * SAFE_X - 80)
    y = H * 0.40 - len(lines) * px * 0.7
    first = None
    for i, ln in enumerate(lines):
        d.text((SAFE_X + 40, y), ln, font=C.font("serif", px), fill=(28, 28, 32))
        if "2027" in ln and first is None:
            tw = d.textlength(ln, font=C.font("serif", px))
            first = (SAFE_X + 40, y, SAFE_X + 40 + tw, y + px * 1.1)
        y += px * 1.4
    d.text((SAFE_X + 40, H * 0.70), outlet + "  ·  " + date.upper(), font=C.font("head_l", 30), fill=(120, 120, 126))
    d.text((SAFE_X + 40, H * 0.70 + 44), "ЦИТАТА СО СТРАНИЦЫ · ОФОРМЛЕНИЕ НАШЕ", font=C.font("head_l", 22), fill=(160, 160, 164))
    img = C.vignette(img, 0.35)
    if first is None:
        first = (SAFE_X + 40, H * 0.40, W - SAFE_X - 40, H * 0.40 + px)
    return img, first


def top_shade(img, h=300, a=0.6):
    """мягкое затемнение верхней кромки — чтобы надписи читались на светлом кадре"""
    base = img.convert("RGBA")
    grad = Image.new("L", (1, h))
    for y in range(h):
        grad.putpixel((0, y), int(255 * a * (1 - y / h) ** 1.4))
    mask = grad.resize((W, h))
    dark = Image.new("RGBA", (W, h), (0, 0, 0, 255))
    dark.putalpha(mask)
    base.alpha_composite(dark, (0, 0))
    return base.convert("RGB")


# ─────────────────────────── окно оригинала: огибающая и осциллограмма ───────────────────────────
_env = {}


def envelope(name, start, dur, sr=50):
    key = (name, round(start, 2), round(dur, 2))
    if key in _env:
        return _env[key]
    p = C.apath(name)
    env = np.zeros(max(1, int(dur * sr)), np.float32)
    if os.path.exists(p):
        try:
            raw = subprocess.run([C.ffmpeg(), "-nostdin", "-loglevel", "error", "-ss", "%.3f" % start, "-t", "%.3f" % dur,
                                  "-i", p, "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
            a = np.abs(np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0)
            n = 8000 // sr
            m = len(a) // n
            if m > 0:
                e = a[:m * n].reshape(m, n).max(axis=1)
                e = e / max(1e-3, float(np.percentile(e, 98)))
                env = np.clip(e, 0, 1).astype(np.float32)
        except Exception:
            pass
    _env[key] = env
    return env


def oscillo(tracks, tt, y, h, x0, x1, window=4.0, sr=50):
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    s = SS
    pps = (x1 - x0) / window
    d.line([(x0 * s, y * s), (x1 * s, y * s)], fill=(70, 70, 76, 255), width=1 * s)
    for env, at, color in tracks:
        step = 5
        x = x1
        while x > x0:
            tm = tt - (x1 - x) / pps - at
            v = 0.0
            if tm >= 0:
                i = int(tm * sr)
                if i < len(env):
                    v = float(env[i])
            if v > 0.02:
                hh = max(1.0, v * h)
                a = int(255 * (0.35 + 0.65 * (x - x0) / (x1 - x0)))
                d.rectangle([(x - 1.5) * s, (y - hh) * s, (x + 1.5) * s, (y + hh) * s], fill=color + (a,))
            x -= step
    return C.done(lay)


def perevod(text, k, t, y=H - 214, px=46):
    if k <= 0:
        return []
    return [C.text_layer(["ПЕРЕВОД"], "head_l", 24, C.GREY, SAFE_X, y - 56, "ls", 0.3, a=C.clamp(k * 3)),
            fx.typed(text, k, "head_r", px, C.WHITE, SAFE_X, y, 0.02, True, t)]


# ─────────────────────────── цитата на чёрном ───────────────────────────
def quote_lines(lines, ks, y0=H * 0.40, px=74, lead=1.45, num=None, num_k=0.0, src=None, src_k=0.0):
    """строки цитаты по одной (ks — доли появления каждой), номер цитаты сверху слева, источник снизу"""
    lays = []
    if num and num_k > 0:
        lays.append(C.text_layer([num], "head_l", 40, C.GREY, SAFE_X, 150, "ls", 0.3, a=num_k))
        lays.append(red_line(num_k, SAFE_X, SAFE_X + 70, 164, 3))
    y = y0
    for ln, k in zip(lines, ks):
        if k > 0:
            kk = C.out_cubic(k)
            p = fit_px(ln, "serif", px, W - 2 * SAFE_X - 60)
            lays.append(C.text_layer([ln], "serif", p, C.WHITE, SAFE_X + 30, y + (1 - kk) * 26, "ls", 0.0, a=C.clamp(k * 2)))
        y += px * lead
    if src and src_k > 0:
        lays.append(C.text_layer([src], "head_l", 26, C.GREY, SAFE_X + 30, y + 30, "ls", 0.3, a=src_k))
    return lays


def big_quote_mark(k, x=SAFE_X - 10, y=H * 0.40 - 40, px=260):
    if k <= 0:
        return None
    return C.text_layer(["«"], "serif", px, C.GREY3, x, y + px * 0.72, "ls", 0.0, a=0.6 * k)
