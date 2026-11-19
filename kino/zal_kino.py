#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Белый зал фильма: слова и числа, которые встают из пола, уезжают вверх,
листы на полу, куб с потолка. Поверх ядра зала (belyy-zal/zal_core)."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "zal"))
import zal_core as Z                      # noqa: E402
import core as C                          # noqa: E402

Cam = Z.Cam


def hall(cam, dark=0.0):
    return Z.room(cam, dark=dark)


def word_tex(text, fsize=300, color=C.INK, kind="black", cond=0.9):
    """текстура слова: чёрный гротеск по умолчанию, красный — для чисел"""
    fname = {"black": "ArialBlack.ttf", "head": "Oswald-Bold.ttf", "sans": "Arimo-Bold.ttf"}[kind]
    return Z.text_tex([text], fsize=fsize, fname=fname, cond=cond, color=tuple(color) + (255,))


def standing(img, cam, tex, x, z, h, k_up=1.0, k_out=0.0, depth=0.06, shadow=True,
             reflect=True, roll=0.0, max_w=3.4):
    """объёмное слово стоит на полу. k_up: 0 — под полом, 1 — встало;
    k_out: 0 — стоит, 1 — уехало вверх и растаяло."""
    if k_up <= 0 or k_out >= 1:
        return
    w = h * tex.size[0] / tex.size[1]
    if w > max_w:                              # длинное слово — ниже, но не шире зала
        h = h * max_w / w
        w = max_w
    ku = C.out_expo(k_up)
    y = -h / 2 + h * ku                       # центр: из-под пола к h/2
    if k_out > 0:
        y += C.smoother(k_out) * 4.2
    c = Z.quad((x, y, z), w, h, roll=roll)
    if k_out > 0:
        t2 = tex.copy()
        t2.putalpha(t2.split()[3].point(lambda v: int(v * (1 - C.smoother(k_out)))))
        tex = t2
    if shadow and k_out < 0.3:
        Z.floor_shadow(img, cam, c, tex)
    if ku < 1.0 or k_out > 0:
        Z.put_above_floor(img, cam, c, tex, depth=depth, steps=4)
    else:
        if reflect:
            Z.reflection(img, cam, c, tex, 0.08)
        Z.extrude(img, cam, c, tex, depth=depth, steps=5)


def flat_sheet(img, cam, tex, cx, cz, w, h, y=0.012, yaw=0.0):
    """лист лежит на полу (плоскость xz)"""
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    pts = [(-w / 2, h / 2), (w / 2, h / 2), (w / 2, -h / 2), (-w / 2, -h / 2)]
    c = []
    for ux, uz in pts:
        rx, rz = ux * cy_ - uz * sy_, ux * sy_ + uz * cy_
        c.append((cx + rx, y, cz + rz))
    # тень под листом
    sh = Image.new("RGBA", tex.size, (0, 0, 0, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    cs = [(p[0] + 0.03, 0.004, p[2] - 0.03) for p in c]
    Z.paste_quad(img, sh, [cam.proj(p) for p in cs])
    Z.paste_quad(img, tex, [cam.proj(p) for p in c])
    return c


def sheet_tex(lines, w=1400, h=990, fsize=72, kind="serif", title=None, seed=3,
              red_line=0.0, ink=C.INK):
    """лист бумаги с текстом; red_line 0…1 — красная черта, проведённая по листу"""
    im = C.paper(w, h, seed=seed).convert("RGBA")
    d = ImageDraw.Draw(im)
    y = int(h * 0.16)
    if title:
        ft = C.font("head_r", int(fsize * 0.55))
        C.tracked(d, int(w * 0.09), y, title.upper(), ft, C.GREY2 + (255,), 0.3)
        y += int(fsize * 1.2)
    f = C.font(kind, fsize)
    for ln in lines:
        d.text((int(w * 0.09), y), ln, font=f, fill=tuple(ink) + (255,))
        y += int(fsize * 1.35)
    if red_line > 0:
        x0, x1 = int(w * 0.09), int(w * 0.91)
        xe = x0 + (x1 - x0) * C.clamp(red_line)
        yl = int(h * 0.62)
        d.line([(x0, yl), (xe, yl + 6)], fill=C.RED + (230,), width=7)
    return im


def cube(img, cam, center, size, k_down=1.0, wires=True):
    """стеклянный куб спускается с потолка: k_down 0 — под потолком, 1 — сел"""
    cx, cy, cz = center
    y = cy + (Z.CEIL + size) * (1 - C.out_cubic(k_down))
    Z.glass_cube(img, cam, (cx, y, cz), size, wires=wires)


def source(img, text):
    Z.source_line(img, text)
