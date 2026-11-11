# -*- coding: utf-8 -*-
"""Клипы приёмов белого зала: G02, G10, G13. Запуск: shard_zal.py <код> <out.mp4>"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import Cam, quad, paste_quad, room, embers, cluster, text_tex, sticker_tex, word_tiles, tv_tex, source_line, \
     build_block, hang_block, glass_cube, maket_tex, plate_tex, scale_column, font, put_above_floor, W as SW, H as SH, \
     sheet_tex, extrude, floor_shadow, reflection, wire, out_expo, out_back, out_cubic, seg

FPS = 30

# ---------------- G13 · наклейка влетает с перелётом ----------------
def g13(t):
    cam = Cam(x=0.0, y=1.52, z=1.05 * t)
    img = room(cam)
    sheets = [(-2.9, 2.35, 9.0, 18), (2.6, 2.7, 11.5, -14), (-1.5, 1.75, 14.0, 9),
              (3.1, 1.95, 16.5, -8), (-3.3, 2.9, 19.5, 12), (1.9, 2.45, 22.0, -10)]
    texts = [["Это очередная статья", "про хайп. Всерьёз", "принимать не стоит."],
             ["Что делать: купить", "платную подписку"],
             ["Автор — просто ещё", "один разгонщик ИИ"],
             ["Это называется", "контент-маркетинг"],
             ["Он нагнетает страх,", "чтобы продать курс"],
             ["Похоже на удачный", "пиар-ход"]]
    for (x, y, z, rot), lines in zip(sheets, texts):
        if z - cam.z < 0.6: continue
        tex = sheet_tex(lines)
        c = quad((x, y, z), 1.55, 1.0, yaw=math.radians(rot))
        wire(img, cam, (x - 0.6, y + 0.5, z)); wire(img, cam, (x + 0.6, y + 0.5, z))
        paste_quad(img, tex, [cam.proj(p) for p in c])
    # крупная надпись словами
    words = [(0.00, "И МНОГИЕ ИЗ НИХ"), (0.22, "СКАЗАЛИ, ЧТО Я"), (0.46, "ОШИБСЯ.")]
    shown = [w for s, w in words if t >= s]
    if shown:
        hl = {len(" ".join(shown).split(" ")) - 1} if len(shown) == 3 else None
        tex = text_tex(shown, fsize=200, hl=hl)
        h = 0.30 * len(shown) + 0.12
        w = h * tex.size[0] / tex.size[1]
        c = quad((-0.15, 2.78, 9.2), w, h)
        floor_shadow(img, cam, c, tex)
        extrude(img, cam, c, tex, depth=0.055, steps=5)
    img = embers(img, cam, cluster(2.3, 0.30, 7.6, 0.62, 4, 1) + cluster(-2.8, 0.24, 10.5, 0.52, 3, 2)
                 + cluster(3.4, 0.20, 14.0, 0.44, 3, 3), t)
    # НАКЛЕЙКИ — главный приём
    for word, t0, rot, pos in (("ХАЙП", 0.72, -4.5, (-1.60, 1.50, 9.0)), ("ФЕЙК", 1.18, 3.5, (1.80, 2.18, 10.0))):
        if t < t0: continue
        k = 1.0 + 0.13 * (1.0 - out_expo((t - t0) / 0.075))
        tex = sticker_tex(word)
        h = 1.05 * k
        w = h * tex.size[0] / tex.size[1]
        c = quad((pos[0], pos[1], pos[2]), w, h, roll=math.radians(rot))
        floor_shadow(img, cam, c, tex)
        paste_quad(img, tex, [cam.proj(p) for p in c])
    return img

# ---------------- G10 · слово выезжает из пола ----------------
def g10(t):
    CY = 1.02
    cam = Cam(x=0.10, y=CY, z=0.42 * t)
    img = room(cam)
    slabs = [(-3.5, 10.2, 0.95, 0.5), (3.3, 11.4, 1.05, 0.55), (-1.6, 13.6, 0.80, 0.45),
             (2.0, 15.0, 0.90, 0.5), (4.6, 9.0, 0.85, 0.5)]
    pts = []
    for sx, sz, sh, sw in slabs:
        tex = Image.new("RGBA", (90, 150), (46, 42, 38, 255))
        c = quad((sx, sh / 2, sz), sw, sh)
        floor_shadow(img, cam, c, tex)
        extrude(img, cam, c, tex, depth=sw * 0.8, steps=4, shade=(38, 35, 32))
        pts += cluster(sx, sh + 0.10, sz, 0.42, 2, int(abs(sx * 10)) % 97, False)
    small = [(0.00, "И ОНИ"), (0.30, "ПОШЛИ"), (0.62, "В ГОНКУ")]
    sh2 = [w for s0, w in small if t >= s0]
    if sh2:
        tex = text_tex([" ".join(sh2)], fsize=170, fname="ArialBlack.ttf", cond=0.84)
        h = 0.052 * KY * 9.0 * 2.0; w = h * tex.size[0] / tex.size[1]
        paste_quad(img, tex, [cam.proj(p) for p in quad((0.1, wy(CY, 9.0, 0.10), 9.0), w, h)])
    T0, DUR, D = 1.05, 0.22, 7.6
    if t >= T0:
        k = out_expo((t - T0) / DUR)
        tex = text_tex(["ГОНКА."], fsize=430, fname="ArialBlack.ttf", cond=0.84)
        h = 1.30
        w = h * tex.size[0] / tex.size[1]
        c = quad((0.05, h / 2 - (1.0 - k) * h, D), w, h)
        if k > 0.985:
            floor_shadow(img, cam, c, tex)
        put_above_floor(img, cam, c, tex, depth=0.22, steps=11, shade=(70, 68, 66))
    img = embers(img, cam, pts, t)
    return img

# ---------------- G02 · объёмные слова встают на полу ----------------
def g02(t):
    CY = 1.52
    cam = Cam(x=0.22 * t, y=CY, z=0.30 * t)
    img = room(cam)
    D = 9.4
    rows = [(["МЫ", "НЕДООЦЕНИЛИ"], (16, 16, 18, 255), (72, 74, 78), 0, [0.25, 0.80]),
            (["СКОРОСТЬ."], (252, 196, 32, 255), (176, 136, 22), 1, [1.55])]
    for words, color, shade, lineno, tt in rows:
        shown = [w for w, t0 in zip(words, tt) if t >= t0]
        if not shown: continue
        tex = text_tex([" ".join(shown)], fsize=300, fname="ArialBlack.ttf",
                       cond=0.84, color=color)
        h = 0.76 if lineno == 0 else 0.54
        w = h * tex.size[0] / tex.size[1]
        x0 = -2.35 if lineno == 0 else -2.05
        z = D if lineno == 0 else D - 1.9
        c = quad((x0 + w / 2, h / 2, z), w, h)
        floor_shadow(img, cam, c, tex)
        extrude(img, cam, c, tex, depth=0.17, steps=9, shade=shade)
    img = embers(img, cam, cluster(3.2, 0.24, 12.0, 0.44, 3, 31), t)
    return img

# ---------------- общее: набор блока по словам ----------------
def put_words(img, cam, lines, center, line_h, t, start=0.0, step=0.22,
              fsize=230, fname="Oswald-Bold.ttf", hl=None, pop=0.10, yaw=0.0,
              depth=0.10, steps=6):
    tw, th, tiles = word_tiles(lines, fsize=fsize, fname=fname, hl=hl)
    block_h = line_h * len(lines) + 0.10
    sc = block_h / th
    cx, cy, cz = center
    for i, (tile, px, py) in enumerate(tiles):
        ti = start + i * step
        if t < ti: continue
        k = 1.0 + pop * (1.0 - out_expo((t - ti) / 0.085))
        ox = (px - tw / 2) * sc
        oy = -(py - th / 2) * sc
        w = tile.size[0] * sc * k
        h = tile.size[1] * sc * k
        c = quad((cx + ox * math.cos(yaw), cy + oy, cz + ox * math.sin(yaw)), w, h, yaw=yaw)
        extrude(img, cam, c, tile, depth=depth, steps=steps)
    return tw, th

KX, KY = 0.9754, 0.5487   # W/F и H/F — перевод доли кадра в метры на метр дальности

def wx(camx, d, fx): return camx + (fx - 0.5) * KX * d
def wy(camy, d, fy): return camy + (0.5 - fy) * KY * d

# ---------------- G11 · текст уезжает вверх, куб спускается с потолка ----------------
def g11(t):
    CY = 1.10
    cam = Cam(x=0.0, y=CY, z=0.26 * t)
    img = room(cam)
    sheet = Image.new("RGBA", (320, 320), (250, 250, 249, 255))
    paste_quad(img, sheet, [cam.proj(p) for p in
               [(-0.45, 0.012, 8.25), (1.45, 0.012, 8.25), (1.45, 0.012, 6.55), (-0.45, 0.012, 6.55)]])
    # КУБ СПУСКАЕТСЯ С ПОТОЛКА: 2,05 -> 2,40 с, мягкая посадка
    DROP_T0, DROP_D = 2.05, 0.35
    if t >= DROP_T0:
        k = out_expo((t - DROP_T0) / DROP_D)
        dy = (1.0 - k) * 4.2
        glass_cube(img, cam, (0.50, 0.98 + dy, 7.40), 1.96)
    D = 7.0
    X0, YT, LH = wx(0, D, 0.13), wy(CY, D, 0.07), 0.14 * KY * D
    ph1 = [("w","ОНИ",0),("w","ХОТЕЛИ",0),("w","УЗНАТЬ,",0),("br",),
           ("w","НАСКОЛЬКО",0),("w","УМЁН",1),("br",),
           ("w","САМЫЙ",0),("w","СИЛЬНЫЙ",0),("w","ИЗ",0),("w","НИХ.",0)]
    ph2 = [("w","И",0),("w","ЗАПЕРЛИ",1),("w","ЕГО",0),("br",),("w","В",0),("w","ПЕСОЧНИЦЕ.",0)]
    OUT_T0, OUT_D = 1.95, 0.26          # старый блок уезжает ВВЕРХ
    if t < OUT_T0 + OUT_D:
        lines, hl = build_block(ph1, t, start=0.10, step=0.28, maxlines=3)
        up = 0.0
        if t >= OUT_T0:
            kk = ((t - OUT_T0) / OUT_D) ** 2.0
            up = kk * 3.4
    else:
        lines, hl = build_block(ph2, t, start=2.38, step=0.28, maxlines=3)
        up = 0.0
    if lines:
        tex = text_tex(lines, fsize=250, fname="ArialBlack.ttf", hl=hl, cond=0.84, line_gap=4)
        h = LH * len(lines)
        w = h * tex.size[0] / tex.size[1]
        extrude(img, cam, quad((X0 + w / 2, YT - h / 2 + up, D), w, h), tex, depth=0.07, steps=4)
    img = embers(img, cam, cluster(0.55, 0.32, 7.2, 0.66, 4, 21), t)
    return img

# ---------------- G12 · фраза + три белых макета с подписями ----------------
def g12(t):
    CY = 1.45
    cam = Cam(x=0.0, y=CY, z=0.22 * t)
    img = room(cam)
    mk = [("bank", "БАНКИ", -5.5, 2.5, 15.5), ("hospital", "БОЛЬНИЦЫ", -0.45, 2.55, 13.2),
          ("power", "ЭНЕРГОСЕТИ", 3.6, 2.65, 12.0)]
    for i, (kind, label, x, size, z) in enumerate(mk):
        t0 = 0.95 + i * 0.52
        if t < t0: continue
        tex = maket_tex(kind)
        c = quad((x, size / 2, z), size, size)
        floor_shadow(img, cam, c, tex)
        extrude(img, cam, c, tex, depth=0.55, steps=6,
                shade=(92, 94, 98) if kind == "power" else (188, 191, 196))
        if i:
            pl = text_tex(["+"], fsize=170, fname="ArialBlack.ttf", cond=0.84)
            ph = 0.05 * KY * z * 3.4; pw = ph * pl.size[0] / pl.size[1]
            paste_quad(img, pl, [cam.proj(p) for p in
                       quad(((x + mk[i - 1][2]) / 2, size * 0.52, (z + mk[i - 1][4]) / 2), pw, ph)])
        lab = text_tex([label], fsize=150, fname="ArialBlack.ttf", cond=0.84)
        lh = 0.05 * KY * z; lw = lh * lab.size[0] / lab.size[1]
        paste_quad(img, lab, [cam.proj(p) for p in quad((x, 0.26, z - 1.3), lw, lh)])
    D = 8.0
    X0, YT, LH = wx(0, D, 0.15), wy(CY, D, 0.05), 0.12 * KY * D
    items = [("w","ТЕМ",0),("w","САМЫМ,",0),("w","ЧЕМ",0),("br",),
             ("w","ЛОМАЮТ",1),("w","БАНКИ",0),("w","И",0),("w","СЕТИ.",0)]
    lines, hl = build_block(items, t, start=0.10, step=0.28, maxlines=2)
    if lines:
        tex = text_tex(lines, fsize=250, fname="ArialBlack.ttf", hl=hl, cond=0.84, line_gap=4)
        h = LH * len(lines); w = h * tex.size[0] / tex.size[1]
        extrude(img, cam, quad((X0 + w / 2, YT - h / 2, D), w, h), tex, depth=0.07, steps=4)
    img = embers(img, cam, cluster(-3.6, 0.26, 7.5, 0.44, 3, 22), t)
    return img

# ---------------- G26 · панель заполняет кадр, столбец справа ----------------
def _frame_text(img, x, y, txt, size, color, fname="Arimo-Bold.ttf", shadow=True, stroke=0):
    d = ImageDraw.Draw(img, "RGBA")
    f = font(fname, size)
    if shadow:
        d.text((x + 3, y + 3), txt, font=f, fill=(0, 0, 0, 150))
    if stroke:
        for dx in (-stroke, 0, stroke):
            for dy in (-stroke, 0, stroke):
                if dx or dy: d.text((x + dx, y + dy), txt, font=f, fill=(24, 18, 6, 255))
    d.text((x, y), txt, font=f, fill=color)

# ---------------- G26 · панель заполняет кадр, надписи справа ----------------
def g26(t):
    CY = 1.52
    cam = Cam(x=0.0, y=CY, z=0.20 * t)
    GROW = 0.62
    if t < GROW:
        img = room(cam)
        k = (t / GROW) ** 2.2
        frac = 0.32 + 0.80 * k
        d = 6.8 - 2.2 * k
        pw = frac * KX * d
        ph = pw * 9 / 16
        tex = tv_tex(None)
        fr = Image.new("RGBA", (tex.size[0] + 40, tex.size[1] + 40), (26, 26, 28, 255))
        fr.paste(tex, (20, 20))
        c = quad((wx(0, d, 0.47), wy(CY, d, 0.44), d), pw * 1.05, ph * 1.10)
        paste_quad(img, fr, [cam.proj(p) for p in c])
        hall = [("Я СКАЗАЛ ЭТО", 0.0, 0.085), ("В ПРЯМОМ ЭФИРЕ", 0.32, 0.845)]
        for ln, t0, fy in hall:
            if t < t0: continue
            tx = text_tex([ln], fsize=240, fname="ArialBlack.ttf", cond=0.84)
            hh = 0.085 * KY * (d + 1.0); ww = hh * tx.size[0] / tx.size[1]
            paste_quad(img, tx, [cam.proj(p) for p in
                       quad((wx(0, d + 1.0, 0.46), wy(CY, d + 1.0, fy), d + 1.0), ww, hh)])
        return img
    img = tv_tex(None, w=SW, h=SH).convert("RGBA")
    XC = int(SW * 0.585)
    sh = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([XC - 130, 0, SW, int(SH * 0.78)], fill=(10, 8, 24, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(70)))
    # продолжение фразы из зала — справа вверху, жёлтым выделено слово
    if t < 1.75:
        y = int(SH * 0.055)
        parts = [("В ПРЯМОМ", (255, 255, 255, 255), 0.62), ("ЭФИРЕ.", (255, 198, 30, 255), 0.95)]
        for ln, col, t0 in parts:
            if t < t0: continue
            _frame_text(img, XC, y, ln, 112, col, "ArialBlack.ttf", True, 0)
            y += 126
        return img
    reps = [(1.95, ["Мы рассчитываем,"]), (2.23, ["Мы рассчитываем,", "что соглашение"]),
            (2.51, ["Мы рассчитываем,", "что соглашение", "будет подписано"]),
            (2.79, ["Мы рассчитываем,", "что соглашение", "будет подписано", "до конца недели."]),
            (3.60, ["Остальные вопросы"]), (3.88, ["Остальные вопросы", "вынесены"]),
            (4.16, ["Остальные вопросы", "вынесены", "на следующий раунд."])]
    blocks = []
    for t0, b in reps:
        if t >= t0: blocks = b
    big = None
    if t >= 4.85:
        big = ["НОВЫЙ"] if t < 5.20 else ["НОВЫЙ", "РАУНД"]
        blocks = [] if t < 5.55 else ["а это значит —"]
        if t >= 5.80: blocks = ["а это значит —", "ещё месяц."]
    y = int(SH * 0.045)
    if big:
        for ln in big:
            _frame_text(img, XC, y, ln, 128, (255, 198, 30, 255), "ArialBlack.ttf", True, 4)
            y += 150
        y += 18
    else:
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([XC - 26, y + 6, XC - 18, y + 110], fill=(255, 198, 30, 255))
        _frame_text(img, XC, y, "ОЛЕГ ВОРОНОВ", 56, (255, 255, 255, 255), "ArialBlack.ttf")
        _frame_text(img, XC, y + 68, "Телеканал · 7 ноября 2026", 38, (238, 240, 244, 255))
        y += 150
    for ln in blocks:
        _frame_text(img, XC, y, ln, 44, (255, 255, 255, 255))
        y += 58
    return img

# ---------------- G15 · шкала наливается, плашка едет вверх ----------------
def g15(t):
    CY = 1.45
    cam = Cam(x=0.0, y=CY, z=0.16 * t)
    img = room(cam)
    D = 10.6
    X = wx(0, D, 0.28)
    GT0, GDUR, RISE = 2.30, 1.10, 1.70
    k = out_expo((t - GT0) / GDUR) if t >= GT0 else 0.0
    # столб с делениями
    col = Image.new("RGBA", (36, 900), (58, 48, 40, 255))
    dc = ImageDraw.Draw(col)
    for i in range(30):
        dc.line([(2, 20 + i * 29), (15, 20 + i * 29)], fill=(226, 224, 220, 255), width=3)
    if k > 0:
        fill_h = int(900 * min(1.0, (0.10 + RISE * k) / 4.4))
        glow = Image.new("RGBA", (36, fill_h), (255, 168, 54, 255))
        col.paste(glow, (0, 900 - fill_h))
    cq = quad((X, 2.2, D), 0.16, 4.4)
    extrude(img, cam, cq, col, depth=0.16, steps=3, shade=(46, 38, 32))
    # основание-плита
    base = Image.new("RGBA", (120, 40), (52, 44, 38, 255))
    paste_quad(img, base, [cam.proj(p) for p in
               [(X - 0.45, 0.015, D + 0.45), (X + 0.45, 0.015, D + 0.45),
                (X + 0.45, 0.015, D - 0.45), (X - 0.45, 0.015, D - 0.45)]])
    # плашка со значением
    if t >= 0.70:
        if k <= 0:
            val, col_num, yy = "<1%", (255, 198, 30, 255), 0.55
        else:
            val = "%d%%" % max(1, round(1 + 24 * k)); col_num = (248, 246, 242, 255)
            yy = 0.55 + RISE * k
        pt = plate_tex(val, color=col_num)
        ph = 0.87; pw = ph * pt.size[0] / pt.size[1]
        d2 = ImageDraw.Draw(img, "RGBA")
        aa = cam.proj((X, yy, D)); bb = cam.proj((X + 0.60, yy, D))
        d2.line([(aa[0], aa[1]), (bb[0], bb[1])], fill=(62, 52, 44, 255), width=3)
        paste_quad(img, pt, [cam.proj(p) for p in quad((X + 0.60 + pw / 2, yy, D - 0.2), pw, ph)])
    # пояснение справа
    expl = text_tex(["ДОЛЯ РАБОТЫ ПО СОЗДАНИЮ", "НОВЫХ СИСТЕМ, КОТОРУЮ", "ВЕДЁТ САМ ИИ"],
                    fsize=150, fname="ArialBlack.ttf", cond=0.84, line_gap=6)
    eh = 0.81; ew = eh * expl.size[0] / expl.size[1]
    paste_quad(img, expl, [cam.proj(p) for p in quad((2.74, 0.58 + (0.55 if k > 0.5 else 0.0), D), ew, eh)])
    # фраза сверху
    if k < 0.45:
        items = [("w","ТОГДА",0),("w","ЭТО",0),("w","БЫЛО",0),("br",),
                 ("w","МЕНЬШЕ",1),("w","ПРОЦЕНТА",1),("br",),("w","ВСЕЙ",0),("w","РАБОТЫ.",0)]
        st, hl = 0.45, None
    else:
        items = [("w","А",0),("w","К",0),("w","АВГУСТУ?",0),("br",),
                 ("w","ЧЕТВЕРТЬ",1),("w","ВСЕЙ",0),("w","РАБОТЫ.",0)]
        st = GT0 + 0.50
    lines, hl = build_block(items, t, start=(0.45 if k < 0.45 else GT0 + 0.50), step=0.28, maxlines=4)
    if lines:
        tex = text_tex(lines, fsize=220, fname="ArialBlack.ttf", hl=hl, cond=0.84, line_gap=4)
        LH = 0.085 * KY * D
        h = LH * len(lines); w = h * tex.size[0] / tex.size[1]
        X0 = wx(0, D, 0.38); YT = wy(CY, D, 0.20)
        extrude(img, cam, quad((X0 + w / 2, YT - h / 2, D - 0.3), w, h), tex, depth=0.06, steps=4)
    pts = cluster(X, 0.18, D, 0.52, 3, 24, False)
    if k > 0:
        pts += cluster(X, 0.18 + RISE * k, D, 0.50, 3, 25, False)
        aug = text_tex(["АВГ"], fsize=150, fname="ArialBlack.ttf", cond=0.84)
        fh = 0.30; fw = fh * aug.size[0] / aug.size[1]
        paste_quad(img, aug, [cam.proj(p) for p in quad((X - 0.95, 0.20 + RISE * k, D), fw, fh)])
    feb = text_tex(["ФЕВ"], fsize=150, fname="ArialBlack.ttf", cond=0.84)
    fh = 0.30; fw = fh * feb.size[0] / feb.size[1]
    paste_quad(img, feb, [cam.proj(p) for p in quad((X - 0.95, 0.22, D), fw, fh)])
    img = embers(img, cam, pts, t)
    if t >= 0.70:
        source_line(img, "Институт исследований ИИ · 17 сентября 2026")
    return img

SCENES = {"G13": (g13, 3.3), "G10": (g10, 4.0), "G02": (g02, 3.8),
          "G11": (g11, 4.4), "G12": (g12, 3.8), "G26": (g26, 6.4), "G15": (g15, 5.0)}

def render(code, out):
    fn, dur = SCENES[code]
    n = int(dur * FPS)
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        exe = "ffmpeg"
    p = subprocess.Popen([exe, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{Z.W}x{Z.H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    for i in range(n):
        im = fn(i / FPS).convert("RGB")
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    print("готово:", out, n, "кадров")

if __name__ == "__main__":
    code = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else f"{code}.mp4"
    if os.environ.get("ZAL_FRAME"):
        t = float(os.environ["ZAL_FRAME"])
        SCENES[code][0](t).convert("RGB").save(out)
        print("кадр", t, "->", out)
    else:
        render(code, out)
