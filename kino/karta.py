#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Карта фильма: Украина в графите и одна красная линия в пяти состояниях.

Никаких флагов-заливок: суша тёмный графит с лёгким рельефом, море чернее,
границы тонкие. Красным — только линия и зоны, которые она отделяет.
Координаты линий ПРИБЛИЗИТЕЛЬНЫЕ (наглядность, не картография; его слово:
«не надо какие-то точности, нам наглядно надо показать»).
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
from core import W, H, SS

HERE = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.join(HERE, "geo", "ne50.geojson")
_feat = None


def feats():
    global _feat
    if _feat is None:
        _feat = json.load(open(GEO, encoding="utf-8"))["features"]
    return _feat


def rings(ft):
    g = ft["geometry"]
    if g["type"] == "Polygon":
        return [g["coordinates"][0]]
    if g["type"] == "MultiPolygon":
        return [p[0] for p in g["coordinates"]]
    return []


def name_of(ft):
    p = ft["properties"]
    return p.get("ADMIN") or p.get("NAME") or ""


# ── окно карты Украины (16:9, lat сжата по cos)
class Okno:
    def __init__(self, lon=(21.0, 42.6), lat=(43.6, 53.2), w=W, h=H):
        self.lon, self.lat, self.w, self.h = lon, lat, w, h

    def xy(self, lon, lat):
        u = (lon - self.lon[0]) / (self.lon[1] - self.lon[0])
        v = 1.0 - (lat - self.lat[0]) / (self.lat[1] - self.lat[0])
        return u * self.w, v * self.h

    def pts(self, coords, s=1):
        return [tuple(c * s for c in self.xy(p[0], p[1])) for p in coords]


UA = Okno()

# ── точки и линии (lon, lat)
CITIES = {
    "Киев": (30.52, 50.45), "Донецк": (37.80, 48.00), "Луганск": (39.31, 48.57),
    "Запорожье": (35.14, 47.84), "Херсон": (32.62, 46.64), "Харьков": (36.23, 49.99),
    "Одесса": (30.73, 46.48), "Севастополь": (33.52, 44.60), "Мариуполь": (37.55, 47.10),
    "Днепр": (35.05, 48.46), "Минск": (27.56, 53.90), "Москва": (37.62, 55.75),
}

CRIMEA = [(33.60, 46.15), (33.00, 45.95), (32.55, 45.45), (32.48, 45.35), (33.35, 45.18),
          (33.52, 44.62), (33.75, 44.40), (34.20, 44.50), (34.42, 44.68), (35.00, 44.85),
          (35.40, 45.03), (36.45, 45.30), (36.65, 45.42), (35.85, 45.45), (35.30, 45.52),
          (34.80, 45.95), (34.45, 46.08), (34.10, 46.12), (33.90, 46.20)]

# линия соприкосновения 2015 (Минск-2), с юга на север
LINE_2015 = [(37.72, 47.08), (37.85, 47.40), (37.72, 47.62), (37.76, 47.78), (37.60, 47.95),
             (37.78, 48.14), (37.98, 48.38), (38.20, 48.46), (38.36, 48.64), (38.60, 48.72),
             (39.00, 48.68), (39.42, 48.66), (39.82, 48.72)]

# фронт 2026, с запада (Днепр) на север
LINE_NOW = [(32.30, 46.52), (32.62, 46.66), (33.40, 46.78), (34.00, 47.05), (34.60, 47.48),
            (34.95, 47.50), (35.80, 47.50), (36.30, 47.66), (36.80, 47.86), (37.30, 47.98),
            (37.15, 48.28), (37.10, 48.46), (37.68, 48.52), (37.82, 48.62), (38.10, 48.86),
            (37.80, 48.98), (37.62, 49.70), (37.30, 50.30), (37.00, 50.36)]

# внешняя граница Донецкой и Луганской областей (требование Москвы)
OBLAST_DL = [(38.15, 47.12), (37.55, 47.08), (36.95, 47.08), (36.72, 47.30), (36.60, 47.62),
             (36.62, 48.02), (36.80, 48.32), (36.72, 48.52), (37.20, 49.02), (37.90, 49.25),
             (38.30, 49.62), (39.00, 50.02), (39.80, 49.82), (40.10, 49.60), (40.00, 49.20),
             (39.80, 48.60), (39.70, 48.30), (39.90, 48.00), (39.60, 47.80), (38.90, 47.60),
             (38.30, 47.40), (38.15, 47.12)]

# старый Донбасс (за линией 2015 до границы)
DONBAS_OLD = LINE_2015 + [(40.00, 49.20), (39.80, 48.60), (39.70, 48.30), (39.90, 48.00),
                          (39.60, 47.80), (38.90, 47.60), (38.30, 47.40), (38.15, 47.12)]

# занятое после 24.02.2022: между фронтом, границей, линией 2015 и берегом
ZONE_2022 = LINE_NOW + [(37.60, 50.20), (38.20, 49.95), (39.00, 50.02), (39.80, 49.82),
                        (40.10, 49.60), (39.82, 48.72)] + list(reversed(LINE_2015)) + \
    [(37.50, 47.05), (36.95, 46.92), (36.00, 46.75), (35.30, 46.60), (34.80, 46.28),
     (34.45, 46.10), (34.10, 46.14), (33.60, 46.16), (33.05, 46.12), (32.80, 46.25)]


def _draw_poly(d, pts, fill=None, outline=None, width=1):
    if fill is not None:
        d.polygon(pts, fill=fill)
    if outline is not None:
        d.line(pts + [pts[0]], fill=outline, width=width, joint="curve")


def _relief(w, h, seed=3):
    """лёгкая светотень суши: шум крупного масштаба как высоты, свет с северо-запада"""
    n1 = np.asarray(C.noise(w, h, seed, 120.0).filter(ImageFilter.GaussianBlur(30)), np.float32)
    n2 = np.asarray(C.noise(w, h, seed + 1, 40.0).filter(ImageFilter.GaussianBlur(10)), np.float32)
    z = n1 * 0.7 + n2 * 0.3
    gy, gx = np.gradient(z)
    shade = (-gx - gy) * 0.9
    return np.clip(shade, -14, 14)


_base_cache = {}


def base(okno=UA, hot="Ukraine", size=(W, H), relief=True):
    """подложка: море, суша, Украина чуть светлее, границы, рельеф"""
    key = (okno.lon, okno.lat, size, hot)
    if key in _base_cache:
        return _base_cache[key].copy()
    w, h = size
    s = 2
    im = Image.new("RGB", (w * s, h * s), (12, 12, 15))
    d = ImageDraw.Draw(im)
    o = Okno(okno.lon, okno.lat, w, h)
    for ft in feats():
        land = (40, 41, 45) if name_of(ft) == hot else (28, 29, 33)
        for ring in rings(ft):
            pts = o.pts(ring, s)
            if len(pts) > 2:
                d.polygon(pts, fill=land)
    for ft in feats():
        for ring in rings(ft):
            pts = o.pts(ring, s)
            if len(pts) > 2:
                d.line(pts + [pts[0]], fill=(66, 67, 72), width=2)
    im = im.resize((w, h), Image.LANCZOS)
    if relief:
        a = np.asarray(im, np.float32)
        # маска суши: всё, что не море
        mask = (a[:, :, 0] > 20).astype(np.float32)
        sh = _relief(w, h)
        a += (sh * mask)[:, :, None]
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    im = C.vignette(im, 0.35)
    _base_cache[key] = im
    return im.copy()


_line_cache = {}


def line_layer(coords, k=1.0, okno=UA, color=C.RED, width=5, dash=None, glow=True, head=True):
    """красная линия, прорисованная на долю k по длине; dash=(штрих, зазор)"""
    key = None
    if k >= 1.0:
        key = (tuple(map(tuple, coords)), okno.lon, okno.lat, tuple(color), width, dash, glow)
        if key in _line_cache:
            return _line_cache[key].copy()
    res = _line_layer(coords, k, okno, color, width, dash, glow, head)
    if key is not None:
        _line_cache[key] = res.copy()
    return res


def _line_layer(coords, k, okno, color, width, dash, glow, head):
    im = C.layer()
    d = ImageDraw.Draw(im)
    pts = [np.array(p) for p in okno.pts(coords, SS)]
    segl = [float(np.linalg.norm(pts[i + 1] - pts[i])) for i in range(len(pts) - 1)]
    total = sum(segl)
    want = total * C.clamp(k)
    # накопленные точки до want, последняя интерполирована
    drawn = []
    run = 0.0
    for i in range(len(pts) - 1):
        if run >= want:
            break
        a, b = pts[i], pts[i + 1]
        if run + segl[i] <= want:
            drawn.append(tuple(a))
            run += segl[i]
            if i == len(pts) - 2:
                drawn.append(tuple(b))
        else:
            f = (want - run) / max(1e-6, segl[i])
            drawn.append(tuple(a))
            drawn.append(tuple(a + (b - a) * f))
            run = want
            break
    if len(drawn) < 2:
        return C.done(im)
    if glow:
        g = C.layer()
        dg = ImageDraw.Draw(g)
        dg.line(drawn, fill=color + (120,), width=int(width * 3.2 * SS), joint="curve")
        g = g.filter(ImageFilter.GaussianBlur(10 * SS))
        im = Image.alpha_composite(im, g)
        d = ImageDraw.Draw(im)
    if dash:
        on, off = dash[0] * SS, dash[1] * SS
        pos, flag = 0.0, True
        for i in range(len(drawn) - 1):
            a, b = np.array(drawn[i]), np.array(drawn[i + 1])
            L = float(np.linalg.norm(b - a))
            s = 0.0
            while s < L:
                e = min(L, s + (on if flag else off))
                if flag:
                    p0 = a + (b - a) * (s / L)
                    p1 = a + (b - a) * (e / L)
                    d.line([tuple(p0), tuple(p1)], fill=color + (255,), width=width * SS)
                s = e
                flag = not flag
    else:
        d.line(drawn, fill=color + (255,), width=width * SS, joint="curve")
    if head and 0.02 < k < 1.0:
        hx, hy = drawn[-1]
        r = width * 1.6 * SS
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=C.WHITE + (255,))
    return C.done(im)


_zone_cache = {}


def zone_layer(coords, k=1.0, okno=UA, color=C.RED, fill_a=70, outline=True, hatch=False):
    """зона на карте: полупрозрачная заливка, по желанию штриховка"""
    key = None
    if k >= 1.0:
        key = (tuple(coords), okno.lon, okno.lat, tuple(color), fill_a, outline, hatch)
        if key in _zone_cache:
            return _zone_cache[key].copy()
    res = _zone_layer(coords, k, okno, color, fill_a, outline, hatch)
    if key is not None:
        _zone_cache[key] = res.copy()
    return res


def _zone_layer(coords, k, okno, color, fill_a, outline, hatch):
    im = C.layer()
    d = ImageDraw.Draw(im)
    pts = okno.pts(coords, SS)
    a = int(fill_a * C.smoother(k))
    d.polygon(pts, fill=color + (a,))
    if hatch:
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
        dh = ImageDraw.Draw(hl)
        step = 18 * SS
        for x in range(-im.size[1], im.size[0], step):
            dh.line([(x, 0), (x + im.size[1], im.size[1])], fill=color + (int(80 * C.smoother(k)),), width=SS)
        hl.putalpha(Image.fromarray(np.minimum(np.asarray(hl.getchannel("A")), np.asarray(m))))
        im = Image.alpha_composite(im, hl)
        d = ImageDraw.Draw(im)
    if outline:
        d.line(pts + [pts[0]], fill=color + (int(230 * C.smoother(k)),), width=2 * SS, joint="curve")
    return C.done(im)


_city_cache = {}


def city_layer(names, k=1.0, okno=UA, px=26, side=None, dot=True, color=C.WHITE):
    """точки городов с подписями; side: словарь имя→'l'/'r'"""
    key = None
    if k >= 1.0:
        key = (tuple(names), okno.lon, okno.lat, px, tuple(sorted((side or {}).items())), dot, tuple(color))
        if key in _city_cache:
            return _city_cache[key].copy()
    res = _city_layer(names, k, okno, px, side, dot, color)
    if key is not None:
        _city_cache[key] = res.copy()
    return res


def _city_layer(names, k, okno, px, side, dot, color):
    im = C.layer()
    d = ImageDraw.Draw(im)
    f = C.font("head_r", px * SS)
    a = int(255 * C.smoother(k))
    for n in names:
        lon, lat = CITIES[n]
        x, y = okno.xy(lon, lat)
        x, y = x * SS, y * SS
        if dot:
            r = 4.5 * SS
            d.ellipse([x - r, y - r, x + r, y + r], fill=color + (a,))
            d.ellipse([x - r * 2.2, y - r * 2.2, x + r * 2.2, y + r * 2.2],
                      outline=color + (int(a * 0.35),), width=SS)
        sd = (side or {}).get(n, "r")
        if sd == "r":
            C.tracked(d, x + 14 * SS, y + px * 0.36 * SS, n.upper(), f, color + (a,), 0.14)
        elif sd == "l":
            C.tracked(d, x - 14 * SS, y + px * 0.36 * SS, n.upper(), f, color + (a,), 0.14, "rs")
        else:  # сверху
            C.tracked(d, x, y - 12 * SS, n.upper(), f, color + (a,), 0.14, "ms")
    return C.done(im)


def date_tag(text, k=1.0, x=W - 110, y=120, px=64, sub=None):
    """подпись даты у карты: крупно, справа сверху, тонкая красная черта"""
    im = C.layer()
    d = ImageDraw.Draw(im)
    a = int(255 * C.smoother(k))
    f = C.font("head", px * SS)
    C.tracked(d, x * SS, y * SS, text, f, C.WHITE + (a,), 0.06, "rs")
    d.rectangle([(x - 180) * SS, (y + 14) * SS, x * SS, (y + 17) * SS], fill=C.RED + (a,))
    if sub:
        f2 = C.font("head_l", px * 0.4 * SS)
        C.tracked(d, x * SS, (y + 52) * SS, sub.upper(), f2, C.GREY + (a,), 0.3, "rs")
    return C.done(im)


# ── карта мира точками (из стиля ЗИ), в палитре фильма
def world(size=(W, H), lon=(-20, 150), lat=(-5, 72)):
    import sys
    sys.path.insert(0, os.path.join(HERE, "zi"))
    import dotmap
    import style as S
    S.ACC = C.RED
    S.ACC_DIM = C.RED2
    S.TXT = C.WHITE
    S.TXT2 = C.GREY
    S.TXT3 = C.GREY
    m = dotmap.DotMap(size[0], size[1], lon=lon, lat=lat, step=6, dot=2.3,
                      color=(104, 106, 114), bg=C.BG)
    return m
