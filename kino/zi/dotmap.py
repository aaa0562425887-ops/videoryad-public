#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Карта мира ТОЧКАМИ и всё, что на неё кладётся.

Почему точками, а не контуром: растр из точек читается как ДАННЫЕ, а не как
география — спора о границах не возникает, и кадр остаётся спокойным фоном
под текст. Так сделано в образце ЗИ.

    m = DotMap(1920, 1080)          # карта считается один раз
    base = m.render()
    lay  = m.marker(base.size, "BIMINI ROAD", -79.3, 25.8, "ATLANTIC · BAHAMAS")
    arc  = m.arc(base.size, (-79.3, 25.8), (17.1, 42.9), k=0.6)
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import style as S
from typo import SS, track

_HERE = os.path.dirname(os.path.abspath(__file__))
# контуры берём рядом с движком, если положены (так едет в облако),
# иначе — из скилла карты-брифинга на этой машине
GEO = os.path.join(_HERE, "ne50.geojson")
if not os.path.exists(GEO):
    GEO = os.path.expanduser("~/.claude/skills/karta-brifing/data/ne50.geojson")
_feat = None


def _feats():
    global _feat
    if _feat is None:
        with open(GEO, encoding="utf-8") as f:
            _feat = json.load(f)["features"]
    return _feat


def _rings(ft):
    g = ft["geometry"]
    if g["type"] == "Polygon":
        return [g["coordinates"][0]]
    if g["type"] == "MultiPolygon":
        return [p[0] for p in g["coordinates"]]
    return []


class DotMap:
    """Окно карты: градусы → пиксели. lat сжата, как в обычной плоской карте."""

    def __init__(self, w, h, lon=(-168, 192), lat=(-58, 80), step=5, dot=1.7,
                 color=None, bg=None):
        self.w, self.h = w, h
        self.lon, self.lat = lon, lat
        self.step, self.dot = step, dot
        self.color = color or (74, 94, 116)
        self.bg = bg or S.BG
        self._base = None

    def xy(self, lon, lat):
        u = (lon - self.lon[0]) / (self.lon[1] - self.lon[0])
        v = 1.0 - (lat - self.lat[0]) / (self.lat[1] - self.lat[0])
        return u * self.w, v * self.h

    def land_mask(self, scale=1):
        w, h = self.w * scale, self.h * scale
        m = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(m)
        for ft in _feats():
            for ring in _rings(ft):
                pts = []
                for p in ring:
                    x, y = self.xy(p[0], p[1])
                    pts.append((x * scale, y * scale))
                if len(pts) > 2:
                    d.polygon(pts, fill=255)
        return m

    def dots(self):
        """Координаты всех точек суши — считаются один раз."""
        if getattr(self, "_dots", None) is None:
            m = np.asarray(self.land_mask(), np.uint8)
            pts = []
            for y in range(0, self.h, self.step):
                row = m[y]
                for x in range(0, self.w, self.step):
                    if row[x] > 127:
                        pts.append((x, y))
            self._dots = pts
        return self._dots

    def render(self, k=1.0, wave=0.22, seed=3):
        """Суша — сетка точек внутри маски. При k<1 карта ПРОЯВЛЯЕТСЯ волной
        слева направо: фронт мягкий, точки зажигаются вразнобой."""
        if k >= 1.0 and self._base is not None:
            return self._base.copy()
        im = Image.new("RGB", (self.w, self.h), self.bg)
        d = ImageDraw.Draw(im)
        r = self.dot / 2
        pts = self.dots()
        if k >= 1.0:
            for x, y in pts:
                d.ellipse([x - r, y - r, x + r, y + r], fill=self.color)
            self._base = im
            return im.copy()
        rnd = np.random.default_rng(seed)
        jitter = rnd.random(len(pts)).astype(np.float32)
        front = k * (1.0 + wave) - wave
        for i, (x, y) in enumerate(pts):
            t = x / self.w
            a = (front - t) / wave + jitter[i] * 0.55 - 0.2
            if a <= 0:
                continue
            a = min(1.0, a)
            c = tuple(int(self.bg[j] + (self.color[j] - self.bg[j]) * a) for j in range(3))
            rr = r * (0.55 + 0.45 * a)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=c)
        return im

    # ─────────────────────── метка объекта ───────────────────────
    def marker(self, size, name, lon, lat, sub=None, k=1.0, px=23, ring=0.0,
               side="right"):
        """Жёлтая точка, название капсом, под ним океан и страна."""
        im = Image.new("RGBA", (size[0] * SS, size[1] * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x, y = [v * SS for v in self.xy(lon, lat)]
        a = int(255 * min(1.0, max(0.0, k)))
        if ring > 0:                       # расходящееся кольцо-пульс
            rr = (6 + 26 * ring) * SS
            d.ellipse([x - rr, y - rr, x + rr, y + rr],
                      outline=S.ACC + (int(a * (1 - ring) * 0.8),), width=max(1, SS // 2))
        rr = 4.6 * SS
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=S.ACC + (a,))
        d.ellipse([x - rr * 2.4, y - rr * 2.4, x + rr * 2.4, y + rr * 2.4],
                  outline=S.ACC + (int(a * 0.35),), width=max(1, SS // 2))
        if k > 0.35:
            an = int(255 * min(1.0, (k - 0.35) / 0.4))
            fn = S.font(S.SANS_B, px * SS)
            dx = rr * 3.2 if side == "right" else -rr * 3.2
            tx = x + dx
            if side == "right":
                track(d, tx, y + px * 0.34 * SS, name.upper(), fn, S.TXT + (an,), 0.20)
            else:
                f2 = S.font(S.SANS_B, px * SS)
                wname = sum(d.textlength(c, font=f2) for c in name.upper()) + \
                    px * 0.22 * SS * (len(name) - 1)
                track(d, tx - wname, y + px * 0.34 * SS, name.upper(), fn, S.TXT + (an,), 0.20)
            if sub:
                fs = S.font(S.SANS, px * 0.58 * SS)
                sx = tx if side == "right" else tx - wname
                track(d, sx, y + px * 1.45 * SS, sub.upper(), fs, S.TXT3 + (an,), 0.24)
        return im.resize(size, Image.LANCZOS)

    # ─────────────────────── пунктирный маршрут ───────────────────────
    def arc(self, size, a, b, k=1.0, lift=0.26, dash=9, gap=7, px=1.8,
            color=None, head=True):
        """Маршрут из А в Б: дуга вверх, пунктир рисуется от А к Б.

        `k` — сколько уже прорисовано (0…1), `lift` — высота дуги в долях
        расстояния. Пунктир считается ПО ДЛИНЕ кривой, иначе штрихи плывут.
        """
        im = Image.new("RGBA", (size[0] * SS, size[1] * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        p0 = np.array([v * SS for v in self.xy(*a)])
        p2 = np.array([v * SS for v in self.xy(*b)])
        mid = (p0 + p2) / 2
        dist = np.linalg.norm(p2 - p0)
        p1 = mid + np.array([0.0, -dist * lift])      # контрольная точка вверх

        n = 260
        pts = []
        for i in range(n + 1):
            t = i / n
            q = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
            pts.append(q)
        seg = [float(np.linalg.norm(pts[i + 1] - pts[i])) for i in range(n)]
        total = sum(seg)
        want = total * min(1.0, max(0.0, k))

        col = (color or S.ACC) + (210,)
        run, drawn, on = 0.0, 0.0, True
        step = (dash + gap) * SS
        for i in range(n):
            if drawn >= want:
                break
            s = seg[i]
            on = ((run % step) < dash * SS)
            if on:
                d.line([tuple(pts[i]), tuple(pts[i + 1])], fill=col,
                       width=max(2, int(px * SS)))
            run += s
            drawn += s
        if head and k > 0.02:
            i = min(n, int(n * min(1.0, k)))
            hp = pts[i]
            r = 2.6 * SS
            d.ellipse([hp[0] - r, hp[1] - r, hp[0] + r, hp[1] + r],
                      fill=(color or S.ACC) + (255,))
        return im.resize(size, Image.LANCZOS)

    # ─────────────────────── мини-карта в углу ───────────────────────
    def inset(self, size, lon, lat, box=(230, 130), pad=26, span=46.0,
              label=None, k=1.0, ring=0.0):
        """Кроп региона в рамке справа сверху: где именно это на карте."""
        bw, bh = box
        sub = DotMap(bw * 3, bh * 3,
                     lon=(lon - span * 0.5, lon + span * 0.5),
                     lat=(lat - span * 0.5 * bh / bw, lat + span * 0.5 * bh / bw),
                     step=7, dot=2.2, color=(70, 90, 112), bg=(10, 15, 24))
        tile = sub.render().resize((bw, bh), Image.LANCZOS)
        card = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        card.paste(tile, (0, 0))
        d = ImageDraw.Draw(card)
        cx, cy = bw / 2, bh / 2
        if ring > 0:
            rr = 5 + 20 * ring
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                      outline=S.ACC + (int(190 * (1 - ring)),), width=1)
        d.ellipse([cx - 3.2, cy - 3.2, cx + 3.2, cy + 3.2], fill=S.ACC + (255,))
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=S.ACC + (110,), width=1)
        d.rectangle([0, 0, bw - 1, bh - 1], outline=(46, 60, 78, 220), width=1)

        out = Image.new("RGBA", size, (0, 0, 0, 0))
        x0 = size[0] - bw - pad
        y0 = pad
        card.putalpha(card.getchannel("A").point(lambda v: int(v * min(1.0, k))))
        out.alpha_composite(card, (int(x0), int(y0)))
        if label and k > 0.5:
            lab = Image.new("RGBA", (size[0] * SS, size[1] * SS), (0, 0, 0, 0))
            dl = ImageDraw.Draw(lab)
            f = S.font(S.SANS, 15 * SS)
            track(dl, x0 * SS, (y0 + bh + 24) * SS, label.upper(), f,
                  S.TXT3 + (int(255 * min(1.0, (k - .5) * 2)),), 0.3)
            out = Image.alpha_composite(out, lab.resize(size, Image.LANCZOS))
        return out
