#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Типографика ЗИ: разрежённый капс, антиква, абзацы, метки.

Весь текст рисуется в буфер вчетверо крупнее и ужимается — PIL не умеет
сглаживание, и без этого края букв идут лесенкой.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

import style as S

SS = int(os.environ.get("ZI_SS", "2"))


def _layer(size):
    w, h = size
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _done(im, size):
    return im.resize(size, Image.LANCZOS)


def track(d, x, y, text, fnt, fill, track=0.18, anchor="ls"):
    """Капс с разбивкой: служебные строки образца набраны именно так."""
    adv = [d.textlength(c, font=fnt) for c in text]
    extra = fnt.size * track
    total = sum(adv) + extra * (len(text) - 1)
    if anchor.startswith("m"):
        x -= total / 2
    cur = x
    for c, a in zip(text, adv):
        d.text((cur, y), c, font=fnt, fill=fill, anchor="l" + anchor[1])
        cur += a + extra
    return total


def caps(size, x, y, text, px=15, color=None, tr=0.26, center=False, alpha=255):
    """Надстрочная служебная строка («3 SUBMERGED SITES · 3 CONTINENTS»)."""
    im, d = _layer(size)
    f = S.font(S.SANS_B, px * SS)
    col = (color or S.ACC) + (alpha,)
    track(d, x * SS, y * SS, text.upper(), f, col, tr, "ms" if center else "ls")
    return _done(im, size)


def head(size, x, y, lines, px=58, color=None, lead=1.18, bold_first=True,
         alpha=255, center=False):
    """Заголовок антиквой: первая строка плотная, вторая светлее."""
    im, d = _layer(size)
    col = (color or S.TXT)
    for i, ln in enumerate(lines):
        f = S.font(S.SERIF_B if (i == 0 and bold_first) else S.SERIF, px * SS)
        a = alpha if i == 0 else int(alpha * 0.92)
        d.text((x * SS, (y + i * px * lead) * SS), ln, font=f,
               fill=col + (a,), anchor="ms" if center else "ls")
    return _done(im, size)


def para(size, x, y, lines, px=19, color=None, lead=1.45, alpha=255, serif=False):
    """Абзац-пояснение: короткие строки, светло-серым."""
    im, d = _layer(size)
    f = S.font(S.SERIF if serif else S.SANS, px * SS)
    col = (color or S.TXT2) + (alpha,)
    for i, ln in enumerate(lines):
        d.text((x * SS, (y + i * px * lead) * SS), ln, font=f, fill=col, anchor="ls")
    return _done(im, size)


def big_number(size, x, y, value, px=74, sub=None, color=None, alpha=255):
    """Крупное число со служебной подписью под ним."""
    im, d = _layer(size)
    f = S.font(S.SANS_B, px * SS)
    txt = "{:,}".format(int(value)) if isinstance(value, (int, float)) else str(value)
    d.text((x * SS, y * SS), txt, font=f, fill=(color or S.ACC) + (alpha,), anchor="ls")
    if sub:
        fs = S.font(S.SANS_B, px * 0.21 * SS)
        track(d, x * SS, (y + px * 0.30) * SS, sub.upper(), fs,
              S.TXT2 + (int(alpha * 0.9),), 0.30)
    return _done(im, size)


def mark(size, x, y, text, px=19, label="MY VIEW", lines=None, alpha=255):
    """Метка «MY VIEW» и своя версия под ней — ядро жанра."""
    im, d = _layer(size)
    fl = S.font(S.SANS_B, px * 0.66 * SS)
    track(d, x * SS, y * SS, label.upper(), fl, S.ACC + (alpha,), 0.30)
    f = S.font(S.SERIF, px * SS)
    for i, ln in enumerate(lines or [text]):
        d.text((x * SS, (y + px * 1.35 + i * px * 1.4) * SS), ln, font=f,
               fill=S.TXT + (alpha,), anchor="ls")
    return _done(im, size)


def highlight(size, x, y, text, px=17, pad=7, alpha=255):
    """Жёлтая плашка-маркер на одной строке."""
    im, d = _layer(size)
    f = S.font(S.SANS, px * SS)
    w = d.textlength(text, font=f)
    d.rounded_rectangle([x * SS - pad * SS, (y - px * 0.95) * SS,
                         x * SS + w + pad * SS, (y + px * 0.38) * SS],
                        radius=2 * SS, fill=S.ACC + (alpha,))
    d.text((x * SS, y * SS), text, font=f, fill=(20, 18, 12, 255), anchor="ls")
    return _done(im, size)


def strike(size, x, y, text, px=18, k=1.0, alpha=255):
    """Зачёркнутая официальная версия: линия ползёт по строке."""
    im, d = _layer(size)
    f = S.font(S.SANS, px * SS)
    d.text((x * SS, y * SS), text, font=f, fill=S.TXT2 + (alpha,), anchor="ls")
    w = d.textlength(text, font=f)
    if k > 0:
        d.line([(x * SS - 2 * SS, (y - px * 0.30) * SS),
                (x * SS + w * min(1.0, k) + 2 * SS, (y - px * 0.30) * SS)],
               fill=S.STRIKE + (alpha,), width=max(2, int(SS * 0.9)))
    return _done(im, size)


def rule(size, x, y, w=62, color=None, alpha=255, th=2):
    """Тонкая черта-разделитель перед блоком вопросов."""
    im, d = _layer(size)
    d.line([(x * SS, y * SS), ((x + w) * SS, y * SS)],
           fill=(color or S.ACC) + (alpha,), width=int(th * SS))
    return _done(im, size)


def scrim(size, side="left", power=0.86, span=0.62):
    """Затемнение под текст: кадр не трогаем, текст читается."""
    import numpy as np
    w, h = size
    if side == "left":
        g = np.clip(1.0 - np.linspace(0, 1, w) / span, 0, 1)[None, :]
    elif side == "bottom":
        g = np.clip(np.linspace(0, 1, h)[:, None] / (1 - span) - span / (1 - span), 0, 1)
        g = np.clip(g, 0, 1)
    else:
        g = np.zeros((h, w), np.float32)
    g = np.broadcast_to(g, (h, w)).astype(np.float32) * power
    lay = Image.new("RGBA", (w, h), S.BG + (0,))
    lay.putalpha(Image.fromarray((g * 255).astype("uint8"), "L"))
    return lay
