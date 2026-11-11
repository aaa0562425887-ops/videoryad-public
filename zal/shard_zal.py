# -*- coding: utf-8 -*-
"""Клипы приёмов белого зала: G02, G10, G13. Запуск: shard_zal.py <код> <out.mp4>"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import Cam, quad, paste_quad, room, embers, cluster, text_tex, sticker_tex, word_tiles, tv_tex, source_line, \
     build_block, hang_block, glass_cube, maket_tex, plate_tex, scale_column, font, W as SW, H as SH, \
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

# ---------------- G10 · объёмное слово вырастает из пола ----------------
def g10(t):
    cam = Cam(x=0.30, y=1.02, z=0.50 * t)
    img = room(cam)
    # кубы-мебель с углями наверху
    cubes = [(-4.6, 0.0, 11.5, 0.60), (4.7, 0.0, 13.8, 0.68)]
    for cx, cy, cz, s in cubes:
        if cz - cam.z < 0.8: continue
        tex = Image.new("RGBA", (120, 120), (58, 55, 52, 255))
        c = quad((cx, s / 2, cz), s, s)
        extrude(img, cam, c, tex, depth=s * 0.9, steps=5, shade=(46, 44, 42))
    small = [(0.0, "И ОНИ"), (0.30, "ПОШЛИ"), (0.60, "В ГОНКУ")]
    sh = [w for s, w in small if t >= s]
    if sh:
        tex = text_tex([" ".join(sh)], fsize=150, fname="Oswald-Bold.ttf")
        h = 0.26; w = h * tex.size[0] / tex.size[1]
        c = quad((0.1, 2.70, 8.6), w, h)
        paste_quad(img, tex, [cam.proj(p) for p in c])
    # СЛОВО вырастает из пола
    t0 = 1.15
    if t >= t0:
        k = out_back((t - t0) / 0.30)
        tex = text_tex(["ГОНКА."], fsize=460, fname="Oswald-Bold.ttf")
        full_h = 1.30
        h = full_h * k
        if h > 0.02:
            w = full_h * tex.size[0] / tex.size[1]
            c = quad((0.10, h / 2, 7.4), w * (h / full_h), h, yaw=math.radians(9))
            floor_shadow(img, cam, c, tex)
            reflection(img, cam, c, tex, strength=0.07)
            extrude(img, cam, c, tex, depth=0.21, steps=11)
    img = embers(img, cam, cluster(-4.6, 0.72, 11.5, 0.60, 3, 4, False) + cluster(4.7, 0.80, 13.8, 0.62, 3, 5, False)
                 + cluster(2.6, 0.22, 6.2, 0.58, 4, 6), t)
    return img

# ---------------- G02 · надпись выброшена в объём ----------------
def g02(t):
    cam = Cam(x=0.0, y=1.38, z=1.30 * t)
    img = room(cam)
    sheets = [(-4.1, 2.5, 15.0, 15), (4.4, 2.3, 19.5, -12)]
    for (x, y, z, rot) in sheets:
        if z - cam.z < 0.8: continue
        sh = sheet_tex(["Из статьи · февраль", "Не через десять лет."])
        c = quad((x, y, z), 1.5, 0.97, yaw=math.radians(rot))
        wire(img, cam, (x - 0.55, y + 0.48, z)); wire(img, cam, (x + 0.55, y + 0.48, z))
        paste_quad(img, sh, [cam.proj(p) for p in c])
    rows = [(0.00, "ОНИ ХОТЕЛИ ПРОВЕРИТЬ,"), (0.42, "НАСКОЛЬКО ОН УМЁН.")]
    shown = [w for s0, w in rows if t >= s0]
    if shown:
        hl = {len(" ".join(shown).split(" ")) - 1} if len(shown) == 2 else None
        tex = text_tex(shown, fsize=250, fname="Oswald-Bold.ttf", hl=hl)
        hit = 0.0 if len(shown) < 2 else 0.42
        k = 1.0 + 0.09 * (1.0 - out_expo((t - hit) / 0.13)) if t >= hit else 1.0
        h = (0.40 * len(shown) + 0.14) * k
        w = h * tex.size[0] / tex.size[1]
        c = quad((0.05, 1.74, 10.4), w, h, yaw=math.radians(-11))
        floor_shadow(img, cam, c, tex)
        reflection(img, cam, c, tex, strength=0.08)
        extrude(img, cam, c, tex, depth=0.13, steps=8)
    img = embers(img, cam, cluster(1.6, 0.26, 6.0, 0.72, 5, 7) + cluster(-1.9, 0.22, 8.4, 0.60, 4, 8)
                 + cluster(3.0, 0.18, 12.0, 0.48, 3, 9), t)
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

# ---------------- G11 · слова спускаются на нитях, в центре стеклянный куб ----------------
def g11(t):
    cam = Cam(x=1.25, y=1.02, z=0.30 * t)
    img = room(cam)
    # белый лист на полу и угли на нём
    sheet = Image.new("RGBA", (300, 300), (250, 250, 249, 255))
    paste_quad(img, sheet, [cam.proj(p) for p in
               [(-1.15, 0.012, 10.05), (0.65, 0.012, 10.05), (0.65, 0.012, 8.35), (-1.15, 0.012, 8.35)]])
    if t >= 2.05:
        glass_cube(img, cam, (-0.25, 1.22, 9.2), 2.44)
    items = [("w","ОНИ",0),("w","ХОТЕЛИ",0),("w","ПРОВЕРИТЬ,",0),("br",),
             ("w","НАСКОЛЬКО",0),("w","УМЁН",1),("br",),
             ("w","САМЫЙ",0),("w","СИЛЬНЫЙ",0),("w","ИЗ",0),("w","НИХ.",0)]
    lines, hl = build_block(items, t, start=0.15, step=0.25, maxlines=2)
    if t < 2.05:
        hang_block(img, cam, lines, hl, (-1.05, 2.45, 7.2), 0.30, fsize=180)
    else:
        it2 = [("w","И",0),("w","ЗАПЕРЛИ",1),("w","ЕГО",0),("br",),("w","В",0),("w","ПЕСОЧНИЦЕ.",0)]
        l2, h2 = build_block(it2, t, start=2.20, step=0.25, maxlines=2)
        hang_block(img, cam, l2, h2, (-1.05, 2.45, 7.2), 0.30, fsize=180)
    img = embers(img, cam, cluster(-0.25, 0.16, 9.2, 0.52, 6, 21), t)
    return img

# ---------------- G12 · маркер со словом + макеты вырастают с подписями ----------------
def g12(t):
    cam = Cam(x=0.0, y=1.34, z=0.26 * t)
    img = room(cam)
    items = [("w","ТЕМ",0),("w","САМЫМ,",0),("w","ЧЕМ",0),("br",),
             ("w","ЛОМАЮТ",1),("w","БАНКИ",0),("w","И",0),("w","БОЛЬНИЦЫ.",0)]
    lines, hl = build_block(items, t, start=0.12, step=0.24, maxlines=2)
    hang_block(img, cam, lines, hl, (-1.9, 2.82, 7.6), 0.32, fsize=190, wires=False)
    mk = [("bank", "БАНКИ", -2.05, 1.18, 9.0), ("hospital", "БОЛЬНИЦЫ", 0.0, 1.10, 9.0),
          ("power", "ЭНЕРГОСЕТИ", 2.15, 1.26, 9.0)]
    for i, (kind, label, x, size, z) in enumerate(mk):
        t0 = 1.05 + i * 0.52
        if t < t0: continue
        k = out_back((t - t0) / 0.34)
        hh = size * max(0.02, k)
        tex = maket_tex(kind)
        c = quad((x, hh / 2, z), size * (hh / size), hh)
        floor_shadow(img, cam, c, tex)
        extrude(img, cam, c, tex, depth=0.30, steps=6, shade=(176, 179, 184))
        lab = text_tex([label], fsize=110, fname="Oswald-Bold.ttf")
        lh = 0.17; lw = lh * lab.size[0] / lab.size[1]
        paste_quad(img, lab, [cam.proj(p) for p in quad((x, 0.16, z - 0.35), lw, lh)])
        if i and t >= t0:
            plus = text_tex(["+"], fsize=150, fname="Oswald-Bold.ttf")
            ph = 0.22; pw = ph * plus.size[0] / plus.size[1]
            paste_quad(img, plus, [cam.proj(p) for p in quad(((x + mk[i-1][2]) / 2, 0.62, z), pw, ph)])
    img = embers(img, cam, cluster(-3.4, 0.22, 7.0, 0.52, 4, 22), t)
    return img

# ---------------- G26 · панель заполняет кадр, надписи справа столбиком ----------------
def _tv_column(img, t, header, sub, blocks, big=None):
    d = ImageDraw.Draw(img, "RGBA")
    x = SW - 640
    lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rectangle([x - 26, 150, x - 22, 150 + 520], fill=(255, 255, 255, 150))
    img.alpha_composite(lay)
    y = 168
    if big:
        fb = font("Oswald-Bold.ttf", 118)
        for ln in big:
            d.text((x + 2, y + 3), ln, font=fb, fill=(0, 0, 0, 120))
            d.text((x, y), ln, font=fb, fill=(255, 205, 40, 255))
            y += 126
    elif header:
        fh = font("Oswald-Bold.ttf", 54)
        d.text((x, y), header, font=fh, fill=(255, 255, 255, 255)); y += 62
        fs = font("Arimo-Bold.ttf", 30)
        d.text((x, y), sub, font=fs, fill=(226, 228, 232, 235)); y += 64
    ft = font("Arimo-Bold.ttf", 38)
    for ln in blocks:
        d.text((x + 2, y + 2), ln, font=ft, fill=(0, 0, 0, 130))
        d.text((x, y), ln, font=ft, fill=(255, 255, 255, 255))
        y += 48

def g26(t):
    cam = Cam(x=0.0, y=1.50, z=0.30 * t)
    if t < 0.70:
        img = room(cam)
        k = out_cubic(t / 0.70)
        pw = 3.0 + 9.0 * k
        z = 7.4 - 5.6 * k
        ph = pw * 540 / 960
        tex = tv_tex(None)
        c = quad((0.0, cam.y + (1.95 - cam.y) * (1 - k), z), pw, ph)
        if k < 0.5:
            wire(img, cam, (-pw * 0.4, cam.y + ph / 2, z)); wire(img, cam, (pw * 0.4, cam.y + ph / 2, z))
        paste_quad(img, tex, [cam.proj(p) for p in c])
        img = embers(img, cam, cluster(2.8, 0.22, 9.0, 0.5, 3, 23), t)
        return img
    img = tv_tex(None, w=SW, h=SH).convert("RGBA")
    reps = [(0.85, None, []),
            (1.05, "ОЛЕГ ВОРОНОВ", ["Мы рассчитываем,"]),
            (1.30, "ОЛЕГ ВОРОНОВ", ["Мы рассчитываем,", "что соглашение"]),
            (1.58, "ОЛЕГ ВОРОНОВ", ["Мы рассчитываем,", "что соглашение", "будет подписано"]),
            (1.86, "ОЛЕГ ВОРОНОВ", ["Мы рассчитываем,", "что соглашение", "будет подписано", "до конца недели."]),
            (2.55, "ОЛЕГ ВОРОНОВ", ["Остальные вопросы"]),
            (2.80, "ОЛЕГ ВОРОНОВ", ["Остальные вопросы", "вынесены"]),
            (3.05, "ОЛЕГ ВОРОНОВ", ["Остальные вопросы", "вынесены", "на следующий раунд."])]
    head, blocks = None, []
    for t0, h, b in reps:
        if t >= t0: head, blocks = h, b
    big = None
    if t >= 3.45:
        big = ["ДО КОНЦА"] if t < 3.75 else ["ДО КОНЦА", "НЕДЕЛИ"]
        head = None
        blocks = ["а по остальному —"] if t >= 3.95 else []
        if t >= 4.20: blocks = ["а по остальному —", "новый раунд."]
    _tv_column(img, t, head, "Телеканал · 7 ноября 2026", blocks, big)
    return img

# ---------------- G15 · шкала-столб: плашка едет вверх, число добегает ----------------
def g15(t):
    cam = Cam(x=0.35, y=1.34, z=0.22 * t)
    img = room(cam)
    X, Z = -1.55, 8.6
    scale_column(img, cam, X, Z, wdt=0.10)
    # пояснение справа, прижатое вправо
    expl = text_tex(["ДОЛЯ РАБОТЫ ПО СОЗДАНИЮ", "НОВЫХ СИСТЕМ, КОТОРУЮ", "ВЕДЁТ САМ ИИ"], fsize=92,
                    fname="Oswald-Bold.ttf")
    eh = 0.50; ew = eh * expl.size[0] / expl.size[1]
    paste_quad(img, expl, [cam.proj(p) for p in quad((1.55, 1.05, Z), ew, eh)])
    # фраза слева сверху по словам
    items = [("w","ТОГДА",0),("w","ЭТО",0),("w","БЫЛО",0),("br",),
             ("w","МЕНЬШЕ",0),("w","ПРОЦЕНТА",1),("w","РАБОТЫ.",0)]
    lines, hl = build_block(items, t, start=0.30, step=0.26, maxlines=2)
    hang_block(img, cam, lines, hl, (-2.25, 3.05, 7.2), 0.27, fsize=175, wires=False)
    # значение: сначала внизу «<1%», потом едет вверх и число добегает
    grow_t0, grow_dur = 2.15, 1.05
    if t >= 0.55:
        if t < grow_t0:
            val, yy = "<1%", 0.42
        else:
            k = out_expo((t - grow_t0) / grow_dur)
            val = "%d%%" % max(1, round(1 + 25 * k))
            yy = 0.42 + 1.55 * k
        pt = plate_tex(val)
        ph = 0.52; pw = ph * pt.size[0] / pt.size[1]
        c = quad((X + 0.12 + pw / 2, yy, Z - 0.1), pw, ph)
        paste_quad(img, pt, [cam.proj(p) for p in c])
    # подписи месяцев и угли на шкале
    feb = text_tex(["ФЕВ"], fsize=90, fname="Oswald-Bold.ttf")
    fh = 0.21; fw = fh * feb.size[0] / feb.size[1]
    paste_quad(img, feb, [cam.proj(p) for p in quad((X - 0.52, 0.24, Z), fw, fh)])
    pts = cluster(X, 0.16, Z, 0.46, 3, 24, False)
    if t >= grow_t0:
        k = out_expo((t - grow_t0) / grow_dur)
        aug = text_tex(["АВГ"], fsize=90, fname="Oswald-Bold.ttf")
        paste_quad(img, aug, [cam.proj(p) for p in quad((X - 0.52, 0.28 + 1.55 * k, Z), fw, fh)])
        pts += cluster(X, 0.20 + 1.55 * k, Z, 0.46, 3, 25, False)
    img = embers(img, cam, pts, t)
    if t >= 0.55:
        source_line(img, "Институт исследований ИИ · 17 сентября 2026")
    return img

SCENES = {"G13": (g13, 3.3), "G10": (g10, 4.0), "G02": (g02, 3.8),
          "G11": (g11, 4.0), "G12": (g12, 3.6), "G26": (g26, 4.6), "G15": (g15, 4.2)}

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
