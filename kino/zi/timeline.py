#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Шкала времени: ось, вехи, диапазон и миниатюра кадра на ней.

В образце это главный аргумент ролика. Работает так: сперва появляется
пустая ось с делениями (ожидание), потом по очереди встают две вехи с
датами, между ними растягивается янтарная полоса с подписью длительности —
и зритель сам видит, что два события почти совпали. Третья веха снизу несёт
МИНИАТЮРУ раннего кадра: факт из первой половины ролика возвращается уже
как доказательство.
"""
import math

from PIL import Image, ImageDraw

import style as S
from typo import SS, track


class Timeline:
    def __init__(self, size, x0, x1, y, lo, hi, invert=True):
        """lo..hi — подписи оси (например 12000…5000 лет назад).
        invert=True: время убывает слева направо, как в образце."""
        self.size = size
        self.x0, self.x1, self.y = x0, x1, y
        self.lo, self.hi = lo, hi
        self.invert = invert

    def px(self, v):
        t = (v - self.lo) / (self.hi - self.lo)
        return self.x0 + (self.x1 - self.x0) * t

    # ─────────────────────── ось ───────────────────────
    def axis(self, k=1.0, step=1000, unit="YEARS AGO", px=13, group=None):
        w, h = self.size
        im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        a = int(255 * min(1.0, max(0.0, k)))
        xe = self.x0 + (self.x1 - self.x0) * min(1.0, k)
        d.line([(self.x0 * SS, self.y * SS), (xe * SS, self.y * SS)],
               fill=(120, 140, 162, a), width=max(1, SS // 2))
        f = S.font(S.SANS, px * SS)
        v = self.lo
        stepv = -abs(step) if self.lo > self.hi else abs(step)
        while (stepv < 0 and v >= self.hi) or (stepv > 0 and v <= self.hi):
            x = self.px(v)
            if x <= xe + 1:
                d.line([(x * SS, (self.y - 5) * SS), (x * SS, (self.y + 5) * SS)],
                       fill=(120, 140, 162, a), width=max(1, SS // 2))
                # годы пишем без разделителя тысяч: «2010», а не «2,010»
                grp = group if group is not None else (abs(v) >= 10000)
                lab = "{:,}".format(int(abs(v))) if grp else str(int(abs(v)))
                track(d, (x - 24) * SS, (self.y + px * 1.7) * SS, lab, f,
                      S.TXT3 + (a,), 0.16)
            v += stepv
        fu = S.font(S.SANS, px * 0.86 * SS)
        track(d, (self.x1 - 60) * SS, (self.y + px * 3.1) * SS, unit, fu,
              S.TXT3 + (a,), 0.30)
        return im.resize(self.size, Image.LANCZOS)

    # ─────────────────────── веха ───────────────────────
    def mark(self, value, date, title, k=1.0, up=True, px=14, stem=64):
        """Жёлтая метка на оси: дата капсом и название события."""
        w, h = self.size
        im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        a = int(255 * min(1.0, max(0.0, k)))
        x = self.px(value) * SS
        y = self.y * SS
        sgn = -1 if up else 1
        d.line([(x, y), (x, y + sgn * stem * SS * min(1.0, k * 1.3))],
               fill=S.ACC + (a,), width=max(2, int(SS * 0.8)))
        r = 4.2 * SS
        d.ellipse([x - r, y - r, x + r, y + r], fill=S.ACC + (a,))
        d.ellipse([x - r * 2.3, y - r * 2.3, x + r * 2.3, y + r * 2.3],
                  outline=S.ACC + (int(a * 0.35),), width=max(1, SS // 2))
        if k > 0.45:
            ta = int(255 * min(1.0, (k - 0.45) / 0.4))
            ty = y + sgn * (stem + 12) * SS
            fd = S.font(S.SANS_B, px * SS)
            track(d, x + 10 * SS, ty, date.upper(), fd, S.ACC + (ta,), 0.26)
            ft = S.font(S.SANS, px * 1.25 * SS)
            d.text((x + 10 * SS, ty + px * 1.6 * SS), title, font=ft,
                   fill=S.TXT + (ta,), anchor="ls")
        return im.resize(self.size, Image.LANCZOS)

    # ─────────────────────── диапазон ───────────────────────
    def span(self, a_val, b_val, label, k=1.0, px=13, th=22, lift=12):
        """Янтарная полоса между вехами с подписью длительности."""
        w, h = self.size
        im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        xa, xb = self.px(a_val), self.px(b_val)
        xe = xa + (xb - xa) * min(1.0, max(0.0, k))
        y0 = (self.y - lift - th) * SS
        y1 = (self.y - lift) * SS
        d.rectangle([xa * SS, y0, xe * SS, y1], fill=S.ACC_DIM + (205,))
        if k > 0.55:
            ta = int(255 * min(1.0, (k - 0.55) / 0.35))
            f = S.font(S.SANS_B, px * SS)
            track(d, (xa + xb) / 2 * SS, (self.y - lift - th * 0.32) * SS,
                  label.upper(), f, S.ACC + (ta,), 0.34, anchor="ms")
        return im.resize(self.size, Image.LANCZOS)

    # ─────────────────────── миниатюра кадра ───────────────────────
    def thumb(self, value, frame, note, title, k=1.0, box=(150, 84), drop=92,
              px=12, color=None):
        """Веха вниз с превью кадра: ранний факт возвращается доказательством."""
        w, h = self.size
        out = Image.new("RGBA", self.size, (0, 0, 0, 0))
        a = min(1.0, max(0.0, k))
        x = self.px(value)
        lay = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        col = color or S.AQUA
        d.line([(x * SS, self.y * SS), (x * SS, (self.y + drop * min(1.0, k * 1.4)) * SS)],
               fill=col + (int(220 * a),), width=max(2, int(SS * 0.7)))
        lay = lay.resize(self.size, Image.LANCZOS)
        out = Image.alpha_composite(out, lay)
        if k > 0.4:
            bw, bh = box
            th_ = frame.convert("RGB").resize((bw, bh), Image.LANCZOS)
            card = Image.new("RGBA", (bw + 2, bh + 2), (col[0], col[1], col[2], 220))
            card.paste(th_, (1, 1))
            ka = int(255 * min(1.0, (k - 0.4) / 0.4))
            card.putalpha(card.getchannel("A").point(lambda v: int(v * ka / 255)))
            # если слева не помещается — кладём карточку справа от вехи
            left = x - bw - 24
            px_card = int(left if left > 24 else x + 24)
            out.alpha_composite(card, (px_card, int(self.y + drop - bh / 2)))
            txt = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
            dt = ImageDraw.Draw(txt)
            fd = S.font(S.SANS_B, px * SS)
            tx = (px_card + bw + 18) if left <= 24 else (x + 14)
            track(dt, tx * SS, (self.y + drop - 8) * SS, note.upper(), fd,
                  col + (ka,), 0.26)
            ft = S.font(S.SANS, px * 1.3 * SS)
            dt.text((tx * SS, (self.y + drop + px * 1.3) * SS), title,
                    font=ft, fill=S.TXT + (ka,), anchor="ls")
            out = Image.alpha_composite(out, txt.resize(self.size, Image.LANCZOS))
        return out
