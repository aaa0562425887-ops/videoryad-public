#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Акт III · Разворот (19–23) и акт IV · Стол и финал (24–31)."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import core as C
import karta as K
import zal_kino as ZK
from core import W, H, SS
from cuts import CUTS, PEREVOD
from scenes_a import scene, SCENES, quote_split
from scenes_b import speech_frame, _read


# ───────────────────────── 19 · Спектейтор ─────────────────────────
_s19 = {}


def magazine_spread():
    """разворот журнала: слева крупный заголовок и лид, справа колонки"""
    w, h = 2800, 1900
    im = C.paper(w, h, seed=41, tone=(236, 231, 220))
    d = ImageDraw.Draw(im)
    ink = C.INK
    # корешок
    d.rectangle([w // 2 - 6, 0, w // 2 + 6, h], fill=(200, 194, 182))
    d.text((160, 110), "THE SPECTATOR", font=C.font("serif_b", 40), fill=(120, 30, 30))
    d.text((w // 2 - 160, 110), "17 DECEMBER 2022", font=C.font("serif", 32), fill=(90, 86, 80), anchor="ra")
    fh = C.font("serif_b", 150)
    for i, ln in enumerate(["How to avoid", "another", "world war"]):
        d.text((160, 300 + i * 165), ln, font=fh, fill=ink)
    d.text((160, 840), "Henry Kissinger", font=C.font("serif_i", 56), fill=ink)
    d.line([(160, 930), (w // 2 - 160, 930)], fill=(120, 114, 104), width=2)
    txt = _read("spectator_2022_12_17.txt")
    paras = [p.strip() for p in (txt or "").split("\n") if len(p.strip()) > 60]
    ft = C.font("serif", 31)
    lines = []
    for p in paras[1:12]:
        lines += C.wrap(p, "serif", 31, 1080) + [""]
    # левая нижняя часть: лид
    y = 980
    for ln in lines[:20]:
        if ln:
            d.text((160, y), ln, font=ft, fill=(44, 40, 36))
        y += 42
    # правая полоса: две колонки
    cw = 560
    rest = lines[20:]
    for ci in range(2):
        x = w // 2 + 160 + ci * (cw + 60)
        y = 200
        while rest and y < h - 160:
            ln = rest.pop(0)
            if ln:
                d.text((x, y), ln, font=ft, fill=(44, 40, 36))
            y += 42
    return im


@scene("19")
def s19(t, dur):
    if t < 2.2:
        return C.act_title("III", "Разворот", t, 2.2)
    tt = t - 2.2
    dd = dur - 2.2
    if "sp" not in _s19:
        _s19["sp"] = magazine_spread()
        _s19["p"] = C.foto("kissinger_portrait_late.jpg").convert("L").convert("RGB")
    t_port = C.cue("19", "меняет позицию", 7.0) - 2.2
    if tt < t_port:
        page = _s19["sp"]
        k = C.smoother(C.seg(tt, 0.0, t_port))
        scale = C.lerp(0.70, 1.25, k)
        cx, cy = C.lerp(1400, 700, k), C.lerp(950, 560, k)
        big = page.resize((int(page.size[0] * scale), int(page.size[1] * scale)), Image.LANCZOS)
        img = Image.new("RGB", (W, H), (40, 38, 36))
        img.paste(big, (int(W / 2 - cx * scale), int(H / 2 - cy * scale)))
        img = C.vignette(img, 0.45)
        img = C.over(img, C.caption("The Spectator", "17 декабря 2022", "статья Генри Киссинджера", C.seg(tt, 0.8, 1.6))).convert("RGB")
        return C.finish(img, tt, dd, fi=0.6, fo=0.0, grain_k=0.03)
    # долли-зум: лицо держит размер, фон наваливается
    k = C.smoother(C.seg(tt, t_port, dd))
    p = _s19["p"]
    face = C.kb(p, 0.0, 0.05, 0.5, 0.28)
    back = C.kb(p, 1.0, 0.05 + 0.55 * k, 0.5, 0.28).filter(ImageFilter.GaussianBlur(3 + 6 * k))
    m = Image.new("L", (W // 4, H // 4), 0)
    ImageDraw.Draw(m).ellipse([W // 4 * 0.33, H // 4 * 0.05, W // 4 * 0.67, H // 4 * 0.9], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(28)).resize((W, H), Image.BILINEAR)
    img = back.copy()
    img.paste(face, (0, 0), m)
    img = C.fade(img, 1 - 0.3 * k)
    img = C.vignette(img, 0.5 + 0.3 * k)
    img = C.over(img, C.caption("Генри Киссинджер", "девяносто девять лет", "портрет", C.seg(tt, t_port + 0.3, t_port + 1.1))).convert("RGB")
    return C.finish(img, tt, dd, fi=0.0, fo=0.6, grain_k=0.035)


# ───────────────────────── 20 · Нельзя или подходящий исход ─────────────────────────
def plate_tex(year, word, sub, w=1000, h=560, red=False):
    im = C.paper(w, h, seed=50 + len(word), tone=(232, 226, 212)).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(110, 104, 96, 255), width=3)
    fy = C.font("head_r", 54)
    d.text((60, 56), year, font=fy, fill=C.GREY2)
    fw = C.font("head", 120)
    while d.textlength(word, font=fw) > w - 120 and fw.size > 40:
        fw = C.font("head", fw.size - 6)
    d.text((60, 150), word, font=fw, fill=C.RED if red else C.INK)
    fs = C.font("serif_i", 40)
    for i, ln in enumerate(C.wrap(sub, "serif_i", 40, w - 120)):
        d.text((60, 330 + i * 50), ln, font=fs, fill=C.INK)
    return im


_s20 = {}


def perspective_in(img, tex, cx, cy, w_px, k, side=1):
    """табличка входит с перспективой: повёрнута, за 0,3 с разворачивается; side ±1"""
    kk = C.out_cubic(k)
    yaw = (1 - kk) * 62 * side
    h_px = w_px * tex.size[1] / tex.size[0]
    # четыре угла в псевдо-3D: сжимаем дальнюю сторону
    f = math.cos(math.radians(yaw))
    near = 1.0 + (1 - f) * 0.35
    far = 1.0 - (1 - f) * 0.35
    xl, xr = cx - w_px / 2 * f, cx + w_px / 2 * f
    if side > 0:
        hl, hr = h_px * near, h_px * far
    else:
        hl, hr = h_px * far, h_px * near
    pts = [(xl, cy - hl / 2), (xr, cy - hr / 2), (xr, cy + hr / 2), (xl, cy + hl / 2)]
    dx = (1 - kk) * 120 * side
    pts = [(x + dx, y) for x, y in pts]
    tex2 = tex.copy()
    tex2.putalpha(tex2.split()[3].point(lambda v: int(v * min(1.0, k * 3))))
    sh, pad = C.shadow_box((int(w_px * f), int(h_px)), blur=30, a=int(150 * kk))
    img.alpha_composite(sh, (int(xl + dx - pad + 14), int(cy - h_px / 2 - pad + 22)))
    ZK.Z.paste_quad(img, tex2, pts)


@scene("20")
def s20(t, dur):
    if not _s20:
        _s20["a"] = plate_tex("2014 · «Вашингтон пост»", "НЕЛЬЗЯ", "Украине не следует вступать в НАТО. Образец — Финляндия.")
        _s20["b"] = plate_tex("2023 · Давос", "ПОДХОДЯЩИЙ ИСХОД", "Идея нейтральной Украины потеряла смысл. Членство в альянсе — подходящий исход.", red=True)
        _s20["v"] = C.Vid("wef_2023_b.mp4", CUTS.get("wef_2023_s20", 0.0), size=(1280, 720))
    ins = C.scene_info("20")["insert"]
    if ins > 0 and t < ins + 1.4:
        img = speech_frame(_s20["v"], t, ins, "Генри Киссинджер", "Давос", "17 января 2023", PEREVOD["20"],
                           tag_src="запись Всемирного экономического форума")
        img = C.fade(img, 1 - C.seg(t, ins + 0.8, ins + 1.4))
        return C.finish(img, t, dur, fi=0.5, fo=0.0, grain_k=0.025)
    tt = t - (ins + 1.4 if ins > 0 else 0.0)
    img = Image.new("RGBA", (W, H), C.BG + (255,))
    ta = 0.3
    tb = C.cue("20", "Теперь мирный процесс", 6.0) - (ins + 1.4 if ins > 0 else 0.0)
    tb = max(ta + 1.2, tb)
    ka = C.seg(tt, ta, ta + 0.3)
    kb_ = C.seg(tt, tb, tb + 0.4)
    perspective_in(img, _s20["a"], W * 0.25, H * 0.5, 700, ka, side=1)
    perspective_in(img, _s20["b"], W * 0.75, H * 0.5, 700, kb_, side=-1)
    # между ними — годы бегут от 2014 к 2023
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    ky = C.seg(tt, ta + 0.3, tb + 0.4)
    if ky > 0:
        yr = int(round(C.lerp(2014, 2023, C.smoother(ky))))
        f = C.font("head_l", 70 * SS)
        C.tracked(d, W / 2 * SS, (H * 0.5 + 26) * SS, str(yr), f, C.GREY + (255,), 0.06, "ms")
        f2 = C.font("head_l", 24 * SS)
        C.tracked(d, W / 2 * SS, (H * 0.5 + 70) * SS, "ВОСЕМЬ ЛЕТ", f2, C.GREY2 + (255,), 0.3, "ms")
        d.line([((W / 2 - 60) * SS, (H * 0.5 - 20) * SS), ((W / 2 + 60) * SS, (H * 0.5 - 20) * SS)], fill=C.GREY3 + (255,), width=SS)
    img = C.over(img, C.done(lay)).convert("RGB")
    return C.finish(img, t, dur, fi=0.5 if ins == 0 else 0.0, fo=0.6, grain_k=0.03, vig=0.3)


# ───────────────────────── 21 · Формула ─────────────────────────
_s21 = {}


@scene("21")
def s21(t, dur):
    cam = ZK.Cam(x=0.0, y=1.45, z=0.06 * t)
    img = ZK.hall(cam)
    if not _s21:
        _s21["a"] = ZK.word_tex("ТЕРРИТОРИЯ", 300)
        _s21["b"] = ZK.word_tex("НАТО", 300)
        _s21["f"] = ZK.word_tex("= ОДИН ПАКЕТ", 220, color=C.RED, kind="head", cond=1.0)
    t_terr = C.cue("21", "Крым и старые районы", 6.0)
    t_form = C.cue("21", "территория и членство", 15.0)
    t_pak = C.cue("21", "одним пакетом", 20.0)
    ZK.standing(img, cam, _s21["a"], -2.3, 11.0, 0.7, C.seg(t, 0.4, 1.2), 0.0, max_w=2.8)
    ZK.standing(img, cam, _s21["b"], 2.4, 11.0, 0.7, C.seg(t, t_terr, t_terr + 0.8), 0.0, max_w=2.8)
    kc = C.seg(t, t_form, t_form + 1.6)
    if kc > 0:
        ZK.cube(img, cam, (0.0, 1.6, 11.0), 3.3, kc)
    kp = C.seg(t, t_pak, t_pak + 0.7)
    if kp > 0:
        ZK.standing(img, cam, _s21["f"], 0.0, 7.6, 0.42, kp, 0.0, depth=0.03, reflect=False)
    img = ZK.Z.embers(img, cam, ZK.Z.cluster(3.0, 0.3, 12.0, 0.5, 3, 9), t)
    return C.finish(img.convert("RGB"), t, dur, fi=0.5, fo=0.6, grain_k=0.02)


# ───────────────────────── 22 · Восемь часов ─────────────────────────
_s22 = {}
ECON_LINES = ["Два дня разговора, восемь часов.",
              "«Запад вооружил Украину так, что она стала",
              "самой вооружённой страной Европы —",
              "при наименее опытном стратегическом руководстве.»",
              "«Поэтому её безопаснее держать внутри НАТО,",
              "чтобы территориальные вопросы",
              "она не решала в одиночку.»"]


@scene("22")
def s22(t, dur):
    if "v" not in _s22:
        name = "economist_2023.mp4" if os.path.exists(C.apath("economist_2023.mp4")) else "kissinger_100_2023.mp4"
        _s22["v"] = C.Vid(name, CUTS.get(name, 0.0), size=(1152, 648))
        _s22["name"] = name
    ins = C.scene_info("22")["insert"]
    # панель эфира заполняет кадр: слева запись, справа расшифровка бежит
    k_in = C.smoother(C.seg(t, 0.0, 1.2))
    img = Image.new("RGB", (W, H), (9, 9, 11))
    fr = _s22["v"].at(t)
    vw, vh = 1152, 648
    x0 = int(96 - (1 - k_in) * 300)
    y0 = int(H / 2 - vh / 2)
    img.paste(C.fade(fr, 0.9), (x0, y0))
    d = ImageDraw.Draw(img)
    d.rectangle([x0 - 1, y0 - 1, x0 + vw, y0 + vh], outline=(90, 90, 96), width=1)
    lay = C.layer()
    dl = ImageDraw.Draw(lay)
    # расшифровка справа: строки появляются по времени реплик диктора
    xr = (x0 + vw + 70) * SS
    fh = C.font("head_r", 26 * SS)
    C.tracked(dl, xr, (y0 + 16) * SS, "THE ECONOMIST · МАЙ 2023", fh, C.GREY + (int(255 * k_in),), 0.26)
    dl.rectangle([xr, (y0 + 30) * SS, xr + 50 * SS, (y0 + 33) * SS], fill=C.RED + (int(255 * k_in),))
    t_lines = [C.cue("22", "восемь часов разговора", 5.0),
               C.cue("22", "Запад вооружил Украину", 12.0), C.cue("22", "самой вооружённой", 14.0),
               C.cue("22", "при этом с наименее", 16.0), C.cue("22", "её безопаснее держать", 21.0),
               C.cue("22", "чтобы вопросы вроде", 24.0), C.cue("22", "она не решала", 27.0)]
    fs = C.font("serif", 34 * SS)
    yy = (y0 + 90) * SS
    for ln, tl in zip(ECON_LINES, t_lines):
        k = C.seg(t, tl, tl + 0.5)
        if k > 0:
            n = int(len(ln) * min(1.0, C.seg(t, tl, tl + 1.2)))
            dl.text((xr, yy), ln[:n], font=fs, fill=C.WHITE + (int(255 * C.smoother(k)),), anchor="ls")
            if n < len(ln):
                cw = dl.textlength(ln[:n], font=fs)
                dl.rectangle([xr + cw + 4 * SS, yy - 28 * SS, xr + cw + 7 * SS, yy], fill=C.RED + (255,))
        yy += 52 * SS
    # щит и узда
    t_sh = C.cue("22", "не только как защита", 36.0)
    t_uz = C.cue("22", "Ещё и как узда", 39.0)
    fb = C.font("head", 110 * SS)
    for lbl, tl, x in (("ЩИТ", t_sh, x0 + vw * 0.32), ("УЗДА", t_uz, x0 + vw * 0.68)):
        k = C.seg(t, tl, tl + 0.5)
        if k > 0:
            a = int(255 * C.smoother(k))
            dl.rectangle([(x - 170) * SS, (y0 + vh - 200) * SS, (x + 170) * SS, (y0 + vh - 50) * SS], fill=(0, 0, 0, int(150 * C.smoother(k))))
            C.tracked(dl, x * SS, (y0 + vh - 80) * SS, lbl, fb, (C.WHITE if lbl == "ЩИТ" else C.RED) + (a,), 0.1, "ms")
    img = C.over(img, C.done(lay)).convert("RGB")
    src = "The Economist" if _s22["name"].startswith("economist") else "хроника · сто лет Киссинджеру · май 2023"
    img = C.over(img, C.caption("Генри Киссинджер", "весна 2023", src, C.seg(t, 1.0, 1.8), y=H - 60, x=96)).convert("RGB")
    return C.finish(img, t, dur, fi=0.5, fo=0.6, grain_k=0.025)


# ───────────────────────── 23 · 29 ноября 2023 ─────────────────────────
_s23 = {}


@scene("23")
def s23(t, dur):
    if "p" not in _s23:
        nm = "kent_ct_house.jpg" if os.path.exists(C.apath("kent_ct_house.jpg")) else "kissinger_portrait_late.jpg"
        _s23["p"] = C.foto(nm).convert("L").convert("RGB")
        _s23["house"] = nm.startswith("kent")
    p = C.kb(_s23["p"], t / dur, 0.04, 0.5, 0.3)
    # живой свет: тёплое пятно, мерцает, гаснет на последней трети
    a = np.asarray(p, np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = W * 0.68, H * 0.42
    r = np.sqrt(((xx - cx) / 520) ** 2 + ((yy - cy) / 420) ** 2)
    fl = 1.0 + 0.08 * math.sin(t * 17) * math.sin(t * 5.3 + 1)
    off = 1 - C.smoother(C.seg(t, dur * 0.55, dur * 0.80))
    light = np.exp(-r ** 2) * 0.9 * fl * off
    a = a * (0.42 + light[:, :, None]) + light[:, :, None] * np.array([38, 26, 10], np.float32)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    img = C.vignette(img, 0.7)
    cap = C.caption("Кент, Коннектикут", "29 ноября 2023", None, C.seg(t, 0.6, 1.4))
    img = C.over(img, cap).convert("RGB")
    return C.finish(img, t, dur, fi=0.6, fo=2.0, grain_k=0.04)


# ───────────────────────── 24 · Стена улик ─────────────────────────
_s24 = {}
CARDS = [("01", "ЗА СТОЛОМ", "Абу-Даби · Аляска", "alaska_2025_b.jpg"),
         ("02", "ЛИНИЯ", "спор о линии, не о справедливости", None),
         ("03", "ФОРМУЛА", "территория за НАТО", None),
         ("04", "КИТАЙ", "союз, которого он боялся", "kissinger_xi_2023.mp4"),
         ("05", "ЕВРОПА", "место за столом есть, разговора нет", "nato_finland_2023.mp4")]


def _card_tex(num, title, sub, pic, w=520, h=360):
    im = C.paper(w, h, seed=60 + int(num), tone=(228, 222, 208)).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(120, 112, 100, 255), width=2)
    # кнопка
    d.ellipse([w / 2 - 11, 12, w / 2 + 11, 34], fill=C.RED + (255,))
    d.ellipse([w / 2 - 5, 18, w / 2 + 5, 28], fill=(255, 120, 110, 255))
    if pic is not None:
        ph = C.cover(pic, (w - 60, 170)).convert("L").convert("RGB")
        im.paste(ph, (30, 52))
        y = 240
    else:
        y = 90
        if num == "02":
            # миниатюра карты с линией
            mb = K.base(size=(w - 60, 150), relief=False)
            o = K.Okno((28.0, 42.0), (44.5, 51.5), w - 60, 150)
            ln = K.line_layer(K.LINE_NOW, 1.0, okno=o, width=2, glow=False, head=False)
            ln = ln.resize((w - 60, 150), Image.LANCZOS) if ln.size != (w - 60, 150) else ln
            mb = mb.convert("RGBA")
            # line_layer рисует в полном кадре — перерисуем прямо здесь
            lay = Image.new("RGBA", ((w - 60) * SS, 150 * SS), (0, 0, 0, 0))
            dd = ImageDraw.Draw(lay)
            dd.line(o.pts(K.LINE_NOW, SS), fill=C.RED + (255,), width=3 * SS, joint="curve")
            mb.alpha_composite(lay.resize((w - 60, 150), Image.LANCZOS))
            im.paste(mb, (30, 52))
            y = 240
        elif num == "03":
            f = C.font("head", 64)
            d.text((w / 2, 140), "ТЕРРИТОРИЯ", font=f, fill=C.INK + (255,), anchor="mm")
            d.text((w / 2, 200), "ЗА НАТО", font=f, fill=C.RED + (255,), anchor="mm")
            y = 240
    d.text((30, y), num, font=C.font("head_r", 30), fill=C.RED + (255,))
    d.text((80, y - 4), title, font=C.font("head", 40), fill=C.INK + (255,))
    d.text((30, y + 52), sub, font=C.font("serif_i", 26), fill=(70, 66, 60, 255))
    return im


def _card(i):
    if i not in _s24:
        num, title, sub, pic = CARDS[i]
        img = None
        if pic:
            if pic.endswith(".mp4"):
                v = C.Vid(pic, CUTS.get(pic, 4.0), size=(640, 360), zoom=1.25, cy=0.2)
                img = v.at(0.0)
            else:
                img = C.foto(pic)
        _s24[i] = _card_tex(num, title, sub, img)
    return _s24[i]


def wall(t, cards_k, pull=0.0):
    """тёмная стена, портрет в центре, карточки по кругу с нитями к портрету.
    cards_k — список 0…1 появления пяти карточек; pull — отъезд камеры 0…1"""
    if "wall" not in _s24:
        base = Image.new("RGB", (W, H), (24, 23, 25))
        n = C.noise(W, H, 77, 3.0).filter(ImageFilter.GaussianBlur(1.2))
        a = np.asarray(base, np.float32) + (np.asarray(n, np.float32) - 128)[:, :, None] * 0.12
        _s24["wall"] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
        p = C.foto("kissinger_portrait_late.jpg").convert("L").convert("RGB")
        _s24["port"] = C.cover(p, (440, 560), 0.5, 0.25)
    sc = C.lerp(1.0, 0.78, C.smoother(pull))
    big = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    cx, cy = W / 2, H / 2 + 20
    pos = [(W * 0.17, H * 0.30), (W * 0.17, H * 0.74), (W * 0.50, H * 0.88 + 40), (W * 0.83, H * 0.30), (W * 0.83, H * 0.74)]
    # нити
    for i, k in enumerate(cards_k):
        if k <= 0:
            continue
        kk = C.out_cubic(k)
        px, py = pos[i]
        ex, ey = cx + (px - cx) * (1 - kk), cy + (py - cy) * (1 - kk)
        d.line([(px, py), (ex, ey)], fill=C.RED + (int(220 * min(1, k * 2)),), width=3)
    # портрет
    port = _s24["port"].convert("RGBA")
    fr = Image.new("RGBA", (port.size[0] + 24, port.size[1] + 24), (236, 230, 218, 255))
    fr.paste(port, (12, 12))
    sh, pad = C.shadow_box(fr.size, 34, 170)
    big.alpha_composite(sh, (int(cx - fr.size[0] / 2 - pad + 10), int(cy - fr.size[1] / 2 - pad + 16)))
    big.alpha_composite(fr, (int(cx - fr.size[0] / 2), int(cy - fr.size[1] / 2)))
    # карточки
    for i, k in enumerate(cards_k):
        if k <= 0:
            continue
        kk = C.out_back(k)
        tex = _card(i)
        s = 0.86 + 0.14 * kk
        tw, th = int(tex.size[0] * s), int(tex.size[1] * s)
        tx = tex.resize((tw, th), Image.LANCZOS)
        tx.putalpha(tx.split()[3].point(lambda v: int(v * min(1, k * 3))))
        px, py = pos[i]
        rot = (-4, 3, -2, 4, -3)[i]
        tx = tx.rotate(rot, Image.BICUBIC, expand=True)
        sh, pad = C.shadow_box(tx.size, 26, 150)
        big.alpha_composite(sh, (int(px - tx.size[0] / 2 - pad + 8), int(py - tx.size[1] / 2 - pad + 14)))
        big.alpha_composite(tx, (int(px - tx.size[0] / 2), int(py - tx.size[1] / 2)))
    img = _s24["wall"].copy().convert("RGBA")
    if sc != 1.0:
        nw, nh = int(W * sc), int(H * sc)
        small = big.resize((nw, nh), Image.LANCZOS)
        img.alpha_composite(small, ((W - nw) // 2, (H - nh) // 2 + int(10 * (1 - sc))))
    else:
        img.alpha_composite(big)
    # луч света сверху
    img = img.convert("RGB")
    img = C.vignette(img, 0.6)
    return img


@scene("24")
def s24(t, dur):
    if t < 2.2:
        return C.act_title("IV", "Стол", t, 2.2)
    tt = t - 2.2
    k1 = C.seg(tt, C.cue("24", "Сбылось первое", 3.5) - 2.2, C.cue("24", "Сбылось первое", 3.5) - 2.2 + 0.7)
    img = wall(tt, [k1, 0, 0, 0, 0])
    return C.finish(img, tt, dur - 2.2, fi=0.6, fo=0.4, grain_k=0.03)


@scene("24b")
def s24b(t, dur):
    ts = [0.0, C.cue("24b", "Сбылось второе", 0.0), C.cue("24b", "Сбылось третье", 14.0),
          C.cue("24b", "Сбылось четвёртое", 26.0), C.cue("24b", "Сбылось пятое", 42.0)]
    ks = [1.0] + [C.seg(t, ts[i] + 0.2, ts[i] + 0.9) for i in range(1, 5)]
    pull = C.seg(t, ts[4] + 2.0, dur)
    img = wall(t, ks, pull)
    return C.finish(img, t, dur, fi=0.4, fo=0.6, grain_k=0.03)


# ───────────────────────── 25 · Абу-Даби и Аляска ─────────────────────────
_s25 = {}


@scene("25")
def s25(t, dur):
    if "a" not in _s25:
        _s25["a"] = C.Vid("abu_dhabi_2026_11.mp4", CUTS.get("abu_dhabi_2026_11.mp4", 0.0), zoom=1.12)
        _s25["b"] = C.Vid("alaska_2025_08_15.mp4", CUTS.get("alaska_2025_08_15.mp4", 0.0), zoom=1.12)
    t_al = C.cue("25", "Перед этим была Аляска", 10.0)
    if t < t_al:
        img = C.fade(_s25["a"].at(t), 0.9)
        cap = C.caption("Абу-Даби", "ноябрь 2026 · переговоры", "пул", C.seg(t, 0.6, 1.4))
    else:
        img = C.fade(_s25["b"].at(t - t_al), 0.9)
        cap = C.caption("Анкоридж, Аляска", "15 августа 2025", "Associated Press", C.seg(t, t_al + 0.4, t_al + 1.2))
    img = C.over(img, cap).convert("RGB")
    img = C.vignette(img, 0.35)
    # склейка между двумя хрониками — короткий провал
    k_cut = 1 - 0.9 * (1 - abs(C.clamp((t - t_al) / 0.3, -1, 1))) if abs(t - t_al) < 0.3 else 1.0
    img = C.fade(img, k_cut)
    return C.finish(img, t, dur, fi=0.5, fo=0.6, grain_k=0.03)


# ───────────────────────── 26 · Три ошибки уезжают вверх ─────────────────────────
_s26 = {}


@scene("26")
def s26(t, dur):
    cam = ZK.Cam(x=0.0, y=1.45, z=0.05 * t)
    img = ZK.hall(cam)
    if not _s26:
        _s26["a"] = ZK.word_tex("ДВА МЕСЯЦА", 300)
        _s26["b"] = ZK.word_tex("ФИНЛЯНДИЯ", 300)
        _s26["c"] = ZK.word_tex("КОНЦЕРТ ДЕРЖАВ", 300)
        _s26["p"] = ZK.word_tex("ПОЛЕ", 300)
    t1 = C.cue("26", "Первая сроки", 1.5)
    t54 = C.cue("26", "Прошло пятьдесят четыре", 8.0)
    t2 = C.cue("26", "Вторая Финляндия", 14.0)
    t3 = C.cue("26", "Третья главная", 26.0)
    t4 = C.cue("26", "И одно слепое пятно", 44.0)
    tp = C.cue("26", "а остальных считал полем", 49.0)
    t4y = C.cue("26", "минимум на четыре года", 58.0)
    # три слова встают сразу (0,4 с), уезжают каждое на своей реплике
    ZK.standing(img, cam, _s26["a"], -3.6, 12.0, 0.7, C.seg(t, 0.4, 1.2), C.seg(t, t2 - 0.6, t2 + 0.3), max_w=2.6)
    ZK.standing(img, cam, _s26["b"], 0.0, 16.0, 0.8, C.seg(t, 0.7, 1.5), C.seg(t, t3 - 0.6, t3 + 0.3), max_w=2.8)
    ZK.standing(img, cam, _s26["c"], 3.7, 12.0, 0.7, C.seg(t, 1.0, 1.8), C.seg(t, t4 - 0.6, t4 + 0.3), max_w=2.6)
    kp = C.seg(t, tp, tp + 0.8)
    if kp > 0:
        ZK.standing(img, cam, _s26["p"], 0.0, 10.0, 0.9, kp, 0.0)
    img = ZK.Z.embers(img, cam, ZK.Z.cluster(2.6, 0.3, 14.0, 0.5, 3, 11) + ZK.Z.cluster(-3.2, 0.2, 15.5, 0.5, 3, 12), t)
    img = img.convert("RGB")
    k54 = C.seg(t, t54, t54 + 1.6) * (1 - C.seg(t, t2 - 0.5, t2))
    if k54 > 0:
        img = C.over(img, C.big_number("54 МЕСЯЦА", "он отводил два", None, C.seg(t, t54, t54 + 1.6), cx=W / 2, cy=H * 0.30, px=190, count_from=2)).convert("RGB")
        img = C.fade(img, 1.0)
    k4 = C.seg(t, t4y, t4y + 1.2)
    if k4 > 0:
        img = C.over(img, C.big_number("4 ГОДА", "план опоздал минимум на", None, k4, cx=W / 2, cy=H * 0.30, px=190, count_from=0)).convert("RGB")
    return C.finish(img, t, dur, fi=0.5, fo=0.6, grain_k=0.02)


# ───────────────────────── 27 · Три заморозки ─────────────────────────
_s27 = {}


@scene("27")
def s27(t, dur):
    if "m" not in _s27:
        _s27["m"] = K.world(lon=(-10, 150), lat=(5, 68))
        _s27["b"] = _s27["m"].render()
        _s27["kor"] = C.foto("panmunjom_1953.jpg").convert("L").convert("RGB")
        _s27["cy"] = C.Vid("cyprus_1974_un.mp4", CUTS.get("cyprus_1974_un.mp4", 0.0), zoom=1.32, cx=0.1, cy=0.9)
    m = _s27["m"]
    tk = C.cue("27", "Корея пятьдесят третий", 10.0)
    tc = C.cue("27", "Кипр семьдесят четвёртый", 32.0)
    tm = C.cue("27", "И Минск пятнадцатый", 46.0)
    tr = C.cue("27", "Разница между тремя", 60.0)
    # вставки хроники: Корея 7 с, Кипр 7 с
    if tk + 0.3 <= t < tk + 7.5:
        tt = t - tk - 0.3
        img = C.film_look(C.kb(_s27["kor"], tt / 7.2, 0.08, 0.5, 0.45), t, 0.9)
        img = C.over(img, C.caption("Пханмунджом", "27 июля 1953", "перемирие · архив США", C.seg(tt, 0.4, 1.2))).convert("RGB")
        return C.finish(img, tt, 7.2, fi=0.4, fo=0.5, grain_k=0.0)
    if tc + 0.3 <= t < tc + 7.5:
        tt = t - tc - 0.3
        img = C.film_look(_s27["cy"].at(tt), t, 0.9)
        img = C.over(img, C.caption("Никосия · Кипр", "1974", "ООН", C.seg(tt, 0.4, 1.2))).convert("RGB")
        return C.finish(img, tt, 7.2, fi=0.4, fo=0.5, grain_k=0.0)
    lays = []
    pts = [("Корея", 126.98, 37.95, "1953", tk, 70, "70 ЛЕТ"), ("Кипр", 33.37, 35.17, "1974", tc, 50, "50 ЛЕТ"),
           ("Минск", 27.56, 53.90, "2015", tm, 7, "7 ЛЕТ")]
    lab = C.layer()
    d = ImageDraw.Draw(lab)
    for name, lon, lat, yr, t0, years, txt in pts:
        k = C.seg(t, t0, t0 + 0.6)
        if k <= 0:
            continue
        lays.append(m.marker((W, H), name, lon, lat, yr, k=k, px=26, ring=C.seg(t, t0, t0 + 1.4), side="left" if name == "Корея" else "right"))
        # мини-шкала под меткой: полоса растёт пропорционально годам; у Минска обрывается
        x, y = m.xy(lon, lat)
        x, y = x * SS, (y + 60) * SS
        kb_ = C.seg(t, t0 + 7.8 if name != "Минск" else t0 + 1.0, (t0 + 7.8 if name != "Минск" else t0 + 1.0) + 2.0)
        L = years * 4.6 * SS * C.out_cubic(kb_)
        if kb_ > 0:
            x0 = x - 120 * SS if name != "Корея" else x - 320 * SS
            d.rectangle([x0, y, x0 + L, y + 6 * SS], fill=C.RED + (230,))
            if name == "Минск" and kb_ >= 1:
                # обрыв: короткая зазубрина
                d.line([(x0 + L, y - 8 * SS), (x0 + L + 10 * SS, y + 14 * SS)], fill=C.WHITE + (255,), width=2 * SS)
            if kb_ > 0.5:
                f = C.font("head", 30 * SS)
                C.tracked(d, x0, y + 44 * SS, txt, f, C.WHITE + (int(255 * C.seg(kb_, 0.5, 1.0)),), 0.1)
    lays.append(C.done(lab))
    kr = C.seg(t, tr, tr + 0.8)
    if kr > 0:
        lays.append(C.text_layer(["РАЗНИЦА — КТО СТОИТ ЗА ЛИНИЕЙ"], "head_l", 40, C.GREY, W / 2, H - 100, "ms", 0.3, a=C.smoother(kr)))
    img = C.over(_s27["b"], *lays).convert("RGB")
    return C.finish(img, t, dur, fi=0.5, fo=0.6, grain_k=0.03, vig=0.3)


# ───────────────────────── 28 · Какие земли ─────────────────────────
@scene("28")
def s28(t, dur):
    t1 = C.cue("28", "Первое Крым", 8.0)
    t2 = C.cue("28", "Второе Старый Донбасс", 20.0)
    t3 = C.cue("28", "Третье Всё что занято", 44.0)
    tm = C.cue("28", "Москва хочет весь Донбасс", 62.0)
    tu = C.cue("28", "Американцы прощупывают", 66.0)
    tk = C.cue("28", "Киев отказывается", 70.0)
    ts = C.cue("28", "Остановятся там где стоят", 86.0)
    zoom = 0.12 * C.smoother(t / dur)
    base = C.kb(K.base(), 1.0, zoom, 0.70, 0.60)
    lays = [K.zone_layer(K.CRIMEA, C.seg(t, t1, t1 + 1.0), fill_a=100),
            K.zone_layer(K.DONBAS_OLD, C.seg(t, t2, t2 + 1.0), fill_a=85),
            K.zone_layer(K.ZONE_2022, C.seg(t, t3, t3 + 1.2), color=C.WHITE, fill_a=40, hatch=True),
            K.city_layer(["Киев", "Донецк", "Луганск", "Запорожье", "Херсон", "Севастополь"], C.seg(t, 0.5, 1.5), side={"Херсон": "l", "Севастополь": "t"})]
    lab = C.layer()
    d = ImageDraw.Draw(lab)
    f = C.font("head_r", 30 * SS)
    for txt, lonlat, t0, col in (("ПЕРВОЕ · КРЫМ", (30.6, 45.3), t1, C.RED), ("ВТОРОЕ · СТАРЫЙ ДОНБАСС", (41.2, 48.2), t2, C.RED),
                                 ("ТРЕТЬЕ · ЗАНЯТОЕ ПОСЛЕ 24.02", (35.4, 46.1), t3, C.WHITE)):
        k = C.smoother(C.seg(t, t0 + 0.8, t0 + 1.6))
        if k > 0:
            x, y = K.UA.xy(*lonlat)
            C.tracked(d, x * SS, y * SS, txt, f, col + (int(255 * k),), 0.2, "ms" if "ДОНБАСС" not in txt else "ls")
    lays.append(C.done(lab))
    # три линии: Москва (вся область), США (пунктир по требованию обмена), Киев (граница)
    lays.append(K.line_layer(K.OBLAST_DL, C.seg(t, tm, tm + 1.5), width=4, head=False))
    lays.append(K.line_layer(K.LINE_NOW, C.seg(t, tu, tu + 1.5), width=4, dash=(14, 9), color=C.WHITE, head=False))
    kk = C.seg(t, tk, tk + 1.2)
    if kk > 0:
        # Киев: граница 1991 — контур всей страны тонкой белой чертой
        ua = [ft for ft in K.feats() if K.name_of(ft) == "Ukraine"]
        if ua:
            ring = max(K.rings(ua[0]), key=len)
            lays.append(K.line_layer(ring, kk, width=2, glow=False, head=False, color=C.GREY))
    leg = C.layer()
    dl = ImageDraw.Draw(leg)
    fl = C.font("head_r", 28 * SS)
    for i, (txt, t0, col) in enumerate((("МОСКВА — весь Донбасс", tm, C.RED), ("США — часть Донбасса за НАТО", tu, C.WHITE), ("КИЕВ — ни одной уступки", tk, C.GREY))):
        k = C.smoother(C.seg(t, t0 + 0.6, t0 + 1.2))
        if k > 0:
            y = (H - 190 + i * 44) * SS
            dl.rectangle([110 * SS, y - 16 * SS, 150 * SS, y - 12 * SS], fill=col + (int(255 * k),))
            C.tracked(dl, 170 * SS, y, txt.upper(), fl, C.WHITE + (int(255 * k),), 0.14)
    lays.append(C.done(leg))
    ks = C.seg(t, ts, ts + 1.0)
    if ks > 0:
        lays.append(K.line_layer(K.LINE_NOW, 1.0, width=6 + int(3 * math.sin(t * 6) ** 2), head=False))
        lays.append(K.date_tag("ГДЕ СТОЯТ", ks, px=56, sub="остановка по нынешней линии"))
    img = C.over(base, *[C.kb(l, 1.0, zoom, 0.70, 0.60) if l.size == (W, H) else l for l in lays]).convert("RGB")
    return C.finish(img, t, dur, fi=0.6, fo=0.6, grain_k=0.03, vig=0.25)


# ───────────────────────── 29 · Будапешт ─────────────────────────
_s29 = {}


@scene("29")
def s29(t, dur):
    if "p" not in _s29:
        nm = None
        for cand in ("budapest_1994_3.png", "budapest_1994_2.png", "budapest_1994_1.png"):
            if os.path.exists(C.apath(cand)):
                nm = cand
                break
        _s29["p"] = C.foto(nm) if nm else C.paper(1105, 1615)
        _s29["cover"] = C.foto("budapest_1994_1.png") if os.path.exists(C.apath("budapest_1994_1.png")) else _s29["p"]
    t_b = C.cue("29", "Будапештский меморандум", 5.0)
    t_sig = C.cue("29", "подписи Соединённых Штатов", 8.0)
    t_choice = C.cue("29", "Выбор на самом деле один", 24.0)
    if t < t_choice:
        page = _s29["cover"] if t < t_sig else _s29["p"]
        k = C.smoother(C.seg(t, t_b, t_sig)) if t < t_sig else C.smoother(C.seg(t, t_sig, t_choice))
        # камера: сверху страницы вниз к подписям
        pw, ph = page.size
        scale = W / pw * C.lerp(1.0, 1.45, k)
        big = page.resize((int(pw * scale), int(ph * scale)), Image.LANCZOS)
        y_center = C.lerp(ph * 0.25, ph * 0.80, k) * scale
        img = Image.new("RGB", (W, H), (36, 34, 32))
        img.paste(big, (int(W / 2 - big.size[0] / 2), int(H / 2 - y_center)))
        img = C.vignette(img, 0.5)
        img = C.over(img, C.caption("Будапештский меморандум", "5 декабря 1994", "Договорная коллекция ООН", C.seg(t, t_b + 0.3, t_b + 1.1))).convert("RGB")
        return C.finish(img, t, dur, fi=0.6, fo=0.0, grain_k=0.03)
    # «Корея или Минск»: два слова на тёмном
    tt = t - t_choice
    img = Image.new("RGB", (W, H), C.BG)
    k1 = C.smoother(C.seg(tt, 0.3, 0.9))
    k2 = C.smoother(C.seg(tt, 1.2, 1.8))
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    f = C.font("head", 170 * SS)
    C.tracked(d, (W * 0.30) * SS, (H / 2 + 60) * SS, "КОРЕЯ", f, C.WHITE + (int(255 * k1),), 0.08, "ms")
    C.tracked(d, (W * 0.70) * SS, (H / 2 + 60) * SS, "МИНСК", f, C.RED + (int(255 * k2),), 0.08, "ms")
    fi = C.font("serif_i", 46 * SS)
    C.tracked(d, (W / 2) * SS, (H / 2 + 60) * SS, "или", fi, C.GREY + (int(255 * k2),), 0.0, "ms")
    img = C.over(img, C.done(lay)).convert("RGB")
    return C.finish(img, t, dur, fi=0.0, fo=0.6, grain_k=0.035, vig=0.4)


# ───────────────────────── 30 · Шесть недель ─────────────────────────
_s30 = {}


@scene("30")
def s30(t, dur):
    if not _s30:
        _s30["n"] = ZK.word_tex("6 НЕДЕЛЬ", 320, color=C.RED, kind="head", cond=1.0)
    t6 = C.cue("30", "шесть недель", 6.0)
    t_q = C.cue("30", "вспомнил слова генерала Лебедя", 28.0)
    if t < t_q:
        cam = ZK.Cam(x=0.0, y=1.45, z=0.07 * t)
        img = ZK.hall(cam)
        ZK.standing(img, cam, _s30["n"], 0.0, 10.0, 1.15, C.seg(t, t6, t6 + 0.9), 0.0, depth=0.1)
        img = ZK.Z.embers(img, cam, ZK.Z.cluster(2.8, 0.3, 12.0, 0.5, 3, 13), t)
        return C.finish(img.convert("RGB"), t, dur, fi=0.5, fo=0.0, grain_k=0.02)
    tt = t - t_q
    img = Image.new("RGB", (W, H), C.BG)
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    k = C.smoother(C.seg(tt, 0.2, 1.0))
    a = int(255 * k)
    fq = C.font("serif_b", 190 * SS)
    d.text(((W * 0.14) * SS, (H * 0.36) * SS), "«", font=fq, fill=C.GREY3 + (a,), anchor="ls")
    f = C.font("serif", 52 * SS)
    for i, ln in enumerate(["Соберите две роты из детей чиновников —", "и война закончится в тот же день."]):
        d.text(((W * 0.17) * SS, (H * 0.42 + i * 72) * SS), ln, font=f, fill=C.WHITE + (a,), anchor="ls")
    d.rectangle([(W * 0.17) * SS, (H * 0.42 + 160) * SS, (W * 0.17 + 70) * SS, (H * 0.42 + 163) * SS], fill=C.RED + (a,))
    C.tracked(d, (W * 0.17) * SS, (H * 0.42 + 212) * SS, "АЛЕКСАНДР ЛЕБЕДЬ · ГЕНЕРАЛ", C.font("head_r", 34 * SS), C.WHITE + (a,), 0.16)
    C.tracked(d, (W * 0.17) * SS, (H * 0.42 + 250) * SS, "ИЗ КОММЕНТАРИЕВ К ПРОШЛОМУ ВЫПУСКУ", C.font("head_l", 26 * SS), C.GREY + (a,), 0.22)
    img = C.over(img, C.done(lay)).convert("RGB")
    return C.finish(img, t, dur, fi=0.4, fo=0.8, grain_k=0.035, vig=0.4)


# ───────────────────────── 31 · Три слова ─────────────────────────
_s31 = {}


@scene("31")
def s31(t, dur):
    if not _s31:
        _s31["a"] = ZK.word_tex("МЮНХЕН", 300)
        _s31["b"] = ZK.word_tex("МИНСК", 300)
        _s31["c"] = ZK.word_tex("КОРЕЯ", 300)
    t_end = C.cue("31", "я посчитаю", 20.0) + 1.5
    if t < t_end:
        # камера уходит дугой назад и вбок
        k = C.smoother(t / t_end)
        cam = ZK.Cam(x=-2.6 * k, y=1.45 + 0.4 * k, z=1.5 - 2.2 * k, yaw=math.radians(-11 * k))
        img = ZK.hall(cam)
        tw = [C.cue("31", "Это Мюнхен", 6.0), C.cue("31", "Минск пятнадцатого", 8.5), C.cue("31", "или Корея", 10.5)]
        ZK.standing(img, cam, _s31["a"], -3.8, 11.0, 0.8, C.seg(t, tw[0], tw[0] + 0.8), 0.0, max_w=2.6)
        ZK.standing(img, cam, _s31["b"], 0.0, 11.0, 0.8, C.seg(t, tw[1], tw[1] + 0.8), 0.0, max_w=2.6)
        ZK.standing(img, cam, _s31["c"], 3.8, 11.0, 0.8, C.seg(t, tw[2], tw[2] + 0.8), 0.0, max_w=2.6)
        img = ZK.Z.embers(img, cam, ZK.Z.cluster(2.4, 0.3, 13.0, 0.5, 3, 15) + ZK.Z.cluster(-3.0, 0.2, 14.0, 0.5, 3, 16), t)
        img = img.convert("RGB")
        return C.finish(img, t, t_end, fi=0.5, fo=1.5, grain_k=0.02)
    # титры на чёрном
    tt = t - t_end
    img = Image.new("RGB", (W, H), (5, 5, 6))
    lay = C.layer()
    d = ImageDraw.Draw(lay)
    k = C.smoother(C.seg(tt, 0.3, 1.2))
    a = int(255 * k)
    C.tracked(d, W / 2 * SS, (H / 2 - 40) * SS, "ПОСЛЕДНИЙ ПРОГНОЗ КИССИНДЖЕРА", C.font("head", 64 * SS), C.WHITE + (a,), 0.16, "ms")
    d.rectangle([(W / 2 - 40) * SS, (H / 2 - 8) * SS, (W / 2 + 40) * SS, (H / 2 - 5) * SS], fill=C.RED + (a,))
    lines = ["Архив: NARA · British Pathé · AP Archive · Всемирный экономический форум",
             "Офис президента Украины · kremlin.ru · Договорная коллекция ООН · Wikimedia Commons",
             "Карты условны: линии показаны приблизительно"]
    f = C.font("head_l", 26 * SS)
    for i, ln in enumerate(lines):
        C.tracked(d, W / 2 * SS, (H / 2 + 50 + i * 40) * SS, ln.upper(), f, C.GREY + (a,), 0.18, "ms")
    img = C.over(img, C.done(lay)).convert("RGB")
    return C.in_out_fade(C.grain(img, t, 0.03), tt, dur - t_end, 0.0, 1.5)
