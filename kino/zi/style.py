#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Палитра и шрифты образца ЗИ.

Снято пипеткой с присланного ролика. Жёлтого в кадре не больше двух пятен
одновременно — это и держит подачу: всё холодное, тёплый только акцент.
"""
import os

from PIL import ImageFont

# ── цвета
BG = (7, 11, 18)            # почти чёрный с синевой
BG_SOFT = (13, 20, 32)
ACC = (232, 184, 63)        # тёплый янтарь — акцент
ACC_DIM = (150, 118, 42)
TXT = (238, 242, 246)       # основной текст
TXT2 = (154, 172, 192)      # вторичный
TXT3 = (109, 127, 148)      # служебный
AQUA = (63, 191, 174)       # подводная бирюза
STRIKE = (214, 112, 96)     # цвет зачёркивания

WF = "/mnt/c/Windows/Fonts/"
LIB = "/usr/share/fonts/truetype/liberation/"
DJV = "/usr/share/fonts/truetype/dejavu/"


def _pick(*names):
    for n in names:
        if os.path.exists(n):
            return n
    return names[-1]


# антиква для заголовков и реплик, гротеск для служебного
SERIF = _pick(WF + "georgia.ttf", DJV + "DejaVuSerif.ttf")
SERIF_B = _pick(WF + "georgiab.ttf", DJV + "DejaVuSerif-Bold.ttf")
SERIF_I = _pick(WF + "georgiai.ttf", DJV + "DejaVuSerif-Italic.ttf")
SANS = _pick(WF + "segoeui.ttf", LIB + "LiberationSans-Regular.ttf", DJV + "DejaVuSans.ttf")
SANS_B = _pick(WF + "segoeuib.ttf", LIB + "LiberationSans-Bold.ttf", DJV + "DejaVuSans-Bold.ttf")
SANS_SB = _pick(WF + "segoeuisl.ttf", WF + "segoeui.ttf", DJV + "DejaVuSans.ttf")

_cache = {}


def font(path, size):
    k = (path, int(size))
    if k not in _cache:
        _cache[k] = ImageFont.truetype(path, int(size))
    return _cache[k]
