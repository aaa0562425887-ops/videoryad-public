#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Общее для всех сцен фильма «Верица» (движок — копия Киссинджера, палитра темнее).

Мир фильма: графит · бумага · белый; красный ТОЛЬКО для линии и чисел.
Кадр 1920×1080, 30 к/с. Всё рисуется numpy + PIL, клипы считаются в облаке.
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FPS = 30
SS = 2                                   # суперсэмплинг текстовых слоёв

# ── палитра
BG = (9, 9, 11)             # графит почти чёрный — мир фильма темнее Киссинджера
BG2 = (19, 19, 23)
PAPER = (206, 196, 176)      # бумага под лампой, темнее
PAPER2 = (186, 175, 154)
INK = (30, 28, 26)           # чернила на бумаге
WHITE = (240, 238, 234)
GREY = (150, 150, 154)
GREY2 = (96, 96, 100)
GREY3 = (62, 62, 66)
RED = (204, 34, 30)          # линия и числа — больше ничего
RED2 = (150, 26, 24)

FONTS = os.path.join(HERE, "fonts")
ARCHIV = os.environ.get("KINO_ARCHIV", os.path.join(HERE, "archiv"))

_fc = {}


def font(kind, size):
    """kind: head (Oswald Bold) · head_r (Oswald Regular) · head_l (Light) ·
    serif · serif_b · serif_i · sans_b · black"""
    size = max(4, int(round(size)))
    k = (kind, size)
    if k in _fc:
        return _fc[k]
    if kind in ("head", "head_r", "head_l", "head_m"):
        f = ImageFont.truetype(os.path.join(FONTS, "Oswald-VF.ttf"), size)
        try:
            f.set_variation_by_name({"head": "Bold", "head_r": "Regular",
                                     "head_l": "Light", "head_m": "Medium"}[kind])
        except Exception:
            pass
    else:
        name = {"serif": "PTSerif-Regular.ttf", "serif_b": "PTSerif-Bold.ttf",
                "serif_i": "PTSerif-Italic.ttf", "sans_b": "Arimo-Bold.ttf",
                "black": "ArialBlack.ttf"}[kind]
        f = ImageFont.truetype(os.path.join(FONTS, name), size)
    _fc[k] = f
    return f


# ── ход движения
def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def lerp(a, b, t):
    return a + (b - a) * t


def smoother(x):
    x = clamp(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


ease = smoother


def out_expo(t):
    t = clamp(t)
    return 1.0 if t >= 1 else 1 - pow(2, -10 * t)


def out_back(t, s=1.4):
    t = clamp(t)
    return 1 + (s + 1) * pow(t - 1, 3) + s * pow(t - 1, 2)


def out_cubic(t):
    t = clamp(t)
    return 1 - pow(1 - t, 3)


def in_out(t):
    t = clamp(t)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def seg(t, a, b):
    """0…1 на отрезке времени a…b"""
    return clamp((t - a) / max(1e-6, b - a))


def mix(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], clamp(t)))) for i in range(3))


# ── слои и текст
def layer(w=W, h=H):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


def done(im, w=W, h=H):
    return im.resize((w, h), Image.LANCZOS)


def over(base, *layers):
    out = base.convert("RGBA") if base.mode != "RGBA" else base
    for l in layers:
        if l is None:
            continue
        if l.size != out.size:
            l = l.resize(out.size, Image.LANCZOS)
        out = Image.alpha_composite(out, l)
    return out


def alpha(im, a):
    """умножить альфу слоя на a (0…1)"""
    a = clamp(a)
    if a >= 1.0:
        return im
    r, g, b, al = im.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))


def text_w(d, text, fnt, track=0.0):
    return sum(d.textlength(ch, font=fnt) for ch in text) + \
        track * fnt.size * max(0, len(text) - 1)


def tracked(d, x, y, text, fnt, fill, track=0.0, anchor="ls"):
    """текст с разрядкой; anchor: ls / ms / rs (низ строки)"""
    tw = text_w(d, text, fnt, track)
    if anchor[0] == "m":
        x -= tw / 2
    elif anchor[0] == "r":
        x -= tw
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill, anchor="ls")
        x += d.textlength(ch, font=fnt) + track * fnt.size
    return tw


def text_layer(lines, kind, px, color, x, y, anchor="ls", track=0.0, lead=1.2, a=1.0):
    """строки текста слоем кадра; x,y в пикселях кадра; a — прозрачность"""
    im = layer()
    d = ImageDraw.Draw(im)
    f = font(kind, px * SS)
    col = tuple(color) + (int(255 * clamp(a)),)
    yy = y * SS
    for ln in lines:
        tracked(d, x * SS, yy, ln, f, col, track, anchor)
        yy += px * lead * SS
    return done(im)


def wrap(text, kind, px, maxw):
    """разбить текст по ширине (пиксели кадра)"""
    f = font(kind, px * SS)
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    out, cur = [], ""
    for w in text.split():
        probe = (cur + " " + w).strip()
        if d.textlength(probe, font=f) / SS <= maxw or not cur:
            cur = probe
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


# ── фактуры
def noise(w, h, seed=1, scale=1.0):
    rng = np.random.default_rng(seed)
    sw, sh = max(2, int(w / scale)), max(2, int(h / scale))
    n = rng.random((sh, sw)).astype(np.float32)
    im = Image.fromarray((n * 255).astype(np.uint8), "L")
    if scale != 1.0:
        im = im.resize((w, h), Image.BILINEAR)
    return im


def paper(w=W, h=H, seed=2, tone=PAPER, dark=0.0):
    """лист бумаги: зерно волокон, лёгкие пятна, виньетка по краям"""
    base = Image.new("RGB", (w, h), tone)
    fib = noise(w, h, seed, 1.0).filter(ImageFilter.GaussianBlur(0.6))
    spots = noise(w, h, seed + 7, 90.0).filter(ImageFilter.GaussianBlur(40))
    a = np.asarray(base, np.float32)
    f = (np.asarray(fib, np.float32) / 255.0 - 0.5) * 14
    s = (np.asarray(spots, np.float32) / 255.0 - 0.5) * 22
    a += (f + s)[:, :, None]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    v = 1.0 - 0.22 * np.clip(r - 0.55, 0, 1) ** 1.5 - dark
    a *= v[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


_grain_cache = {}


def grain(img, t, amount=0.045, seed_mod=97):
    """плёночное зерно: меняется каждый кадр"""
    key = int(t * FPS) % seed_mod
    if key not in _grain_cache:
        rng = np.random.default_rng(1000 + key)
        _grain_cache[key] = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = _grain_cache[key]
    g = np.kron(g, np.ones((2, 2), np.float32))[:H, :W]
    a = np.asarray(img.convert("RGB"), np.float32)
    a += g[:, :, None] * amount * 255
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


_vig = {}


def vignette(img, k=0.55):
    w, h = img.size
    if (w, h) not in _vig:
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        _vig[(w, h)] = np.clip(r - 0.45, 0, 1.2) ** 1.6
    a = np.asarray(img.convert("RGB"), np.float32)
    a *= (1.0 - k * _vig[(w, h)])[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def film_look(img, t, k=1.0, scratches=True, seed=5):
    """под хронику: зерно, виньетка, царапины, лёгкое мерцание, тёплый тон"""
    a = np.asarray(img.convert("RGB"), np.float32)
    # цвет плёнки: чуть сепия, приглушённые тени
    lum = a.mean(axis=2, keepdims=True)
    a = a * (1 - 0.35 * k) + lum * 0.35 * k
    a[:, :, 0] += 9 * k
    a[:, :, 2] -= 11 * k
    # мерцание
    fl = 1.0 + 0.035 * k * math.sin(t * 23.0) * math.sin(t * 7.3 + 1.0)
    a *= fl
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img = grain(img, t, 0.07 * k)
    img = vignette(img, 0.7 * k)
    if scratches and k > 0:
        rng = np.random.default_rng(seed + int(t * 3))
        d = ImageDraw.Draw(img)
        for _ in range(rng.integers(0, 3)):
            x = int(rng.uniform(0, W))
            y0 = int(rng.uniform(0, H * 0.6))
            y1 = y0 + int(rng.uniform(60, 500))
            d.line([(x, y0), (x + int(rng.uniform(-3, 3)), y1)],
                   fill=(220, 214, 200), width=1)
        # пыль
        for _ in range(rng.integers(0, 6)):
            x, y = int(rng.uniform(0, W)), int(rng.uniform(0, H))
            d.ellipse([x, y, x + 2, y + 2], fill=(30, 28, 26))
    return img


def fade(img, k):
    """k=1 — кадр как есть, k=0 — чёрное"""
    k = clamp(k)
    if k >= 1:
        return img
    a = np.asarray(img.convert("RGB"), np.float32) * k
    return Image.fromarray(a.astype(np.uint8), "RGB")


def in_out_fade(img, t, dur, fi=0.6, fo=0.8):
    k = 1.0
    if fi > 0:
        k = min(k, seg(t, 0, fi))
    if fo > 0:
        k = min(k, 1 - seg(t, dur - fo, dur))
    return fade(img, smoother(k))


def kb(im, t, zoom=0.06, cx=0.5, cy=0.5, size=(W, H)):
    """медленный наезд: кадр заполняет окно size, центр интереса cx,cy"""
    w, h = size
    iw, ih = im.size
    s = max(w / iw, h / ih) * (1.0 + zoom * t)
    nw, nh = int(iw * s) + 1, int(ih * s) + 1
    big = im.resize((nw, nh), Image.LANCZOS)
    x0 = int((nw - w) * cx)
    y0 = int((nh - h) * cy)
    x0 = max(0, min(nw - w, x0))
    y0 = max(0, min(nh - h, y0))
    return big.crop((x0, y0, x0 + w, y0 + h))


def cover(im, size=(W, H), cx=0.5, cy=0.5):
    return kb(im, 0.0, 0.0, cx, cy, size)


def shadow_box(size, blur=30, a=160):
    """мягкая тень под карточку"""
    w, h = size
    pad = blur * 3
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle([pad, pad, pad + w, pad + h], fill=(0, 0, 0, a))
    return im.filter(ImageFilter.GaussianBlur(blur)), pad


# ── подпись документального кадра (место · дата · источник) — сдержанная
def caption(place, date=None, source=None, k=1.0, y=H - 92, x=96):
    """Тонкая красная черта слева, место крупнее, дата и источник серым.
    Это не плашка новостей: без подложки, без рамки, кегль маленький."""
    if k <= 0:
        return None
    im = layer()
    d = ImageDraw.Draw(im)
    a = int(255 * smoother(k))
    f1 = font("head_r", 30 * SS)
    f2 = font("head_l", 23 * SS)
    # черта растёт сверху вниз
    hh = int(46 * SS * smoother(k))
    d.rectangle([x * SS, (y - 36) * SS, (x + 3) * SS, (y - 36) * SS + hh],
                fill=RED + (a,))
    tracked(d, (x + 22) * SS, (y - 4) * SS, place.upper(), f1, WHITE + (a,), 0.12)
    sub = " · ".join(v for v in (date, source) if v)
    if sub:
        tracked(d, (x + 22) * SS, (y + 26) * SS, sub.upper(), f2, GREY + (a,), 0.14)
    return done(im)


# ── титр акта: номер контуром, название, чёрное до и после
def act_title(num, name, t, dur):
    img = Image.new("RGB", (W, H), (6, 6, 7))
    # подложка-документ в тумане
    k = smoother(seg(t, 0.2, 1.6)) * (1 - smoother(seg(t, dur - 1.0, dur)))
    doc = paper(W, H, seed=11, tone=(70, 66, 60), dark=0.0)
    doc = doc.filter(ImageFilter.GaussianBlur(5))
    doc = fade(doc, 0.22 * k)
    img = Image.blend(img, doc, 1.0)
    lay = layer()
    d = ImageDraw.Draw(lay)
    a = int(255 * k)
    fn = font("head", 300 * SS)
    tracked(d, W / 2 * SS, (H / 2 + 20) * SS, num, fn, (0, 0, 0, 0), 0.0, "ms")
    # контур номера
    tw = text_w(d, num, fn)
    x0 = W / 2 * SS - tw / 2
    d.text((x0, (H / 2 + 20) * SS), num, font=fn, fill=(0, 0, 0, 0),
           stroke_width=3 * SS, stroke_fill=GREY + (a,), anchor="ls")
    f2 = font("head_l", 54 * SS)
    tracked(d, W / 2 * SS, (H / 2 + 110) * SS, name.upper(), f2, WHITE + (a,), 0.32, "ms")
    d.rectangle([(W / 2 - 40) * SS, (H / 2 + 150) * SS, (W / 2 + 40) * SS, (H / 2 + 153) * SS],
                fill=RED + (a,))
    img = over(img, lay).convert("RGB")
    return grain(img, t, 0.03)


# ── заглушка архивного кадра, пока файла нет
def placeholder(label, size=(W, H)):
    w, h = size
    im = Image.new("RGB", (w, h), BG2)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, w - 3, h - 3], outline=GREY3, width=2)
    f = font("head_l", int(min(w, h) * 0.06))
    d.text((w / 2, h / 2), "АРХИВ · " + label.upper(), font=f, fill=GREY2, anchor="mm")
    return im


def apath(name):
    """файл архива: в корне папки архива или в подпапках foto/video/dokumenty"""
    for sub in ("", "foto", "video", "dokumenty"):
        p = os.path.join(ARCHIV, sub, name)
        if os.path.exists(p):
            return p
    return os.path.join(ARCHIV, name)


def foto(name, size=None):
    """архивное фото по имени файла (без пути) — или заглушка"""
    p = apath(name)
    if os.path.exists(p):
        im = Image.open(p).convert("RGB")
    else:
        im = placeholder(os.path.splitext(name)[0], size or (W, H))
    return im


class Vid:
    """Кадры архивного видео по времени сцены (ffmpeg → rgb24).

    v = Vid("wef_2023.mp4", src_start=812.0)   # с какой секунды источника
    v.at(t)   # кадр для момента t сцены
    Читается последовательно; при первом обращении (в каждом процессе) ffmpeg
    открывается с нужного места, прыжок назад или далеко вперёд — переоткрытие.
    """

    def __init__(self, name, src_start=0.0, size=(W, H), fps=FPS, fit="cover", zoom=1.0, cx=0.5, cy=0.5):
        self.zoom, self.cx, self.cy = zoom, cx, cy
        self.path = apath(name)
        self.size = size
        self.fps = fps
        self.fit = fit
        self.src_start = src_start
        self.ok = os.path.exists(self.path)
        self.p = None
        self.i = -1          # индекс последнего прочитанного кадра (от открытия)
        self.t_open = None
        self.last = None
        self.label = os.path.splitext(name)[0]
        self.dur = None
        if self.ok:
            try:
                import re as _re
                err = subprocess.run([ffmpeg(), "-nostdin", "-i", self.path], capture_output=True, text=True).stderr
                m = _re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", err)
                self.dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None
            except Exception:
                self.dur = None

    def _open(self, t):
        if self.p is not None:
            try:
                self.p.kill()
            except Exception:
                pass
        w, h = self.size
        if self.fit == "cover":
            zw, zh = int(w * self.zoom), int(h * self.zoom)
            ox, oy = int((zw - w) * self.cx), int((zh - h) * self.cy)
            vf = "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,crop=%d:%d:%d:%d" % (zw, zh, zw, zh, w, h, ox, oy)
        else:
            vf = "scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black" % (w, h, w, h)
        ss = self.src_start + t
        if self.dur:
            ss = min(ss, max(0.0, self.dur - 0.6))   # за концом записи — держим её последний кадр
        self.p = subprocess.Popen(
            [ffmpeg(), "-nostdin", "-loglevel", "error", "-ss", "%.3f" % ss,
             "-i", self.path, "-vf", vf + ",fps=%d" % self.fps,
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10 ** 7)
        self.t_open = t
        self.i = -1
        self.eof = False

    def at(self, t):
        if not self.ok:
            return placeholder(self.label, self.size)
        want = int(round((t - (self.t_open or 0.0)) * self.fps)) if self.t_open is not None else 0
        if self.p is None or want < self.i or want - self.i > self.fps * 3:
            self._open(t)
            want = 0
        w, h = self.size
        while self.i < want and not getattr(self, "eof", False):
            raw = self.p.stdout.read(w * h * 3)
            if len(raw) < w * h * 3:
                self.eof = True          # запись кончилась — держим последний кадр
                break
            self.last = Image.frombytes("RGB", (w, h), raw)
            self.i += 1
        return self.last if self.last is not None else placeholder(self.label, self.size)


def ffmpeg():
    for p in (os.path.expanduser("~/.local/bin/ffmpeg"), "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if os.path.exists(p):
            return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


# ── число крупно: красное, с бегущим счётчиком и кольцами в такт добеганию
def big_number(value, label_top=None, label_bottom=None, k=1.0, cx=W / 2, cy=H / 2,
               px=260, color=RED, rings=True, count_from=0):
    """value — строка вида «54 МЕСЯЦА»; цифровая часть добегает от count_from."""
    im = layer()
    d = ImageDraw.Draw(im)
    kk = smoother(k)
    a = int(255 * clamp(k * 3))
    # разложить на число и слово
    parts = value.split(" ", 1)
    num, word = parts[0], (parts[1] if len(parts) > 1 else "")
    try:
        target = int(num.replace(" ", ""))
        cur = int(round(lerp(count_from, target, out_expo(k))))
        shown = str(cur)
    except ValueError:
        shown = num
    fn = font("head", px * SS)
    fw = font("head_l", px * 0.42 * SS)
    nw = text_w(d, shown, fn, 0.02)
    ww = text_w(d, word, fw, 0.18) if word else 0
    gap = px * 0.18 * SS if word else 0
    total = nw + gap + ww
    x = cx * SS - total / 2
    y = cy * SS + px * 0.36 * SS
    tracked(d, x, y, shown, fn, color + (a,), 0.02)
    if word:
        tracked(d, x + nw + gap, y, word, fw, WHITE + (a,), 0.18)
    if label_top:
        f = font("head_r", px * 0.17 * SS)
        tracked(d, cx * SS, (cy - px * 0.62) * SS, label_top.upper(), f, GREY + (a,), 0.36, "ms")
    if label_bottom:
        f = font("serif_i", px * 0.16 * SS)
        tracked(d, cx * SS, (cy + px * 0.78) * SS, label_bottom, f, GREY + (a,), 0.0, "ms")
    if rings and 0.0 < k < 1.0:
        for j in range(3):
            r = (px * 0.9 + (1 - kk) * 0.0 + j * px * 0.35) * SS * (0.6 + 0.8 * kk)
            ra = int(90 * (1 - kk) * (1 - j * 0.3))
            if ra > 0:
                d.ellipse([cx * SS - r, cy * SS - r, cx * SS + r, cy * SS + r],
                          outline=color + (ra,), width=2 * SS)
    return done(im)


# ── накладной список 01–04 поверх кадра: строки по одной, старые гаснут до 60%
def overlay_list(items, t, start=0.0, step=1.2, x=120, y=200, px=40, hold=None):
    im = layer()
    d = ImageDraw.Draw(im)
    fn = font("head_l", px * 0.7 * SS)
    ft = font("head_r", px * SS)
    for i, text in enumerate(items):
        t0 = start + i * step
        k = seg(t, t0, t0 + 0.45)
        if k <= 0:
            continue
        later = (t - t0 - 0.45) / step if t > t0 + 0.45 else 0
        is_last = (i == len(items) - 1) or t < start + (i + 1) * step
        a = 1.0 if is_last else 0.6
        a = int(255 * a * smoother(k))
        dx = (1 - out_cubic(k)) * 40
        yy = (y + i * px * 1.55) * SS
        tracked(d, (x + dx) * SS, yy, "%02d" % (i + 1), fn, RED + (a,), 0.1)
        tracked(d, (x + 64 + dx) * SS, yy, text, ft, WHITE + (a,), 0.06)
    return done(im)


def finish(img, t, dur, fi=0.5, fo=0.6, grain_k=0.035, vig=0.0):
    """финальная обработка кадра сцены"""
    img = img.convert("RGB")
    if vig > 0:
        img = vignette(img, vig)
    if grain_k > 0:
        img = grain(img, t, grain_k)
    return in_out_fade(img, t, dur, fi, fo)


# ── реплики диктора: сцена спрашивает «когда произносится фраза»
import json as _json
import re as _re

_TIMING = None
_CUES = None


def _load_timing():
    global _TIMING, _CUES
    if _TIMING is None:
        _TIMING = _json.load(open(os.path.join(HERE, "timing.json"), encoding="utf-8"))
        srt = os.path.join(HERE, "voice.srt")
        _CUES = []
        if os.path.exists(srt):
            import razbivka
            _CUES = razbivka.parse_srt(srt)
    return _TIMING, _CUES


def scene_info(sid):
    tm, _ = _load_timing()
    for s in tm["scenes"]:
        if s["id"] == sid:
            return s
    raise KeyError(sid)


def cue(sid, phrase, default=None):
    """время (с от начала сцены sid), когда диктор начинает фразу phrase"""
    info = scene_info(sid)
    _, cues = _load_timing()
    if not cues:
        return default if default is not None else 0.0
    import razbivka
    t, _ = razbivka.find_start(cues, phrase, info["voice_start"] - 0.2)
    if t is None:
        return default if default is not None else 0.0
    return t - info["voice_start"] + info["insert"]


def dur_of(sid):
    return scene_info(sid)["dur"]
