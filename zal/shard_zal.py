# -*- coding: utf-8 -*-
"""Клипы приёмов белого зала: G02, G10, G13. Запуск: shard_zal.py <код> <out.mp4>"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import Cam, quad, paste_quad, room, embers, cluster, text_tex, sticker_tex, word_tiles, tv_tex, source_line, \
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

# ---------------- G11 · набор фразы по словам ----------------
def g11(t):
    cam = Cam(x=0.0, y=1.46, z=0.62 * t)
    img = room(cam)
    for (x, y, z, rot) in ((-4.0, 2.5, 14.0, 15), (4.3, 2.3, 18.0, -12)):
        if z - cam.z < 0.8: continue
        sh = sheet_tex(["Разбор · ноябрь", "Сначала не поверили."])
        c = quad((x, y, z), 1.5, 0.97, yaw=math.radians(rot))
        wire(img, cam, (x - 0.55, y + 0.48, z)); wire(img, cam, (x + 0.55, y + 0.48, z))
        paste_quad(img, sh, [cam.proj(p) for p in c])
    put_words(img, cam, ["СНАЧАЛА ЭТО КАЗАЛОСЬ", "ШУМОМ.", "ПОТОМ СТАЛО РАБОТОЙ."],
              (0.0, 1.80, 9.6), 0.36, t, start=0.10, step=0.22, fsize=230)
    img = embers(img, cam, cluster(2.4, 0.26, 7.0, 0.60, 4, 11) + cluster(-2.6, 0.22, 10.0, 0.5, 3, 12), t)
    return img

# ---------------- G12 · жёлтый маркер приходит вместе со словом ----------------
def g12(t):
    cam = Cam(x=0.0, y=1.44, z=0.42 * t)
    img = room(cam)
    put_words(img, cam, ["ОНИ НАЗВАЛИ ЭТО ОШИБКОЙ.", "ЧЕРЕЗ МЕСЯЦ — СТРАТЕГИЕЙ."],
              (0.0, 1.78, 8.2), 0.42, t, start=0.10, step=0.24, fsize=250,
              hl={3, 7}, pop=0.09)
    img = embers(img, cam, cluster(-2.9, 0.24, 8.0, 0.58, 4, 13) + cluster(3.1, 0.20, 11.0, 0.5, 3, 14), t)
    return img

# ---------------- G26 · расшифровка строкой поверх эфира ----------------
def g26(t):
    cam = Cam(x=0.0, y=1.52, z=0.34 * t)
    img = room(cam)
    reps = [(0.15, ["Мы рассчитываем, что соглашение"]),
            (1.45, ["Мы рассчитываем, что соглашение", "будет подписано до конца недели"]),
            (2.75, ["Остальные вопросы", "вынесены на следующий раунд"])]
    cap = None
    for t0, c in reps:
        if t >= t0: cap = c
    tex = tv_tex(cap)
    pw = 3.3; ph = pw * 540 / 960
    c = quad((0.0, 1.92, 7.6), pw, ph, yaw=math.radians(-7))
    wire(img, cam, (-1.3, 1.92 + ph / 2, 7.6)); wire(img, cam, (1.3, 1.92 + ph / 2, 7.6))
    floor_shadow(img, cam, c, tex)
    paste_quad(img, tex, [cam.proj(p) for p in c])
    small = text_tex(["ПРЯМАЯ РЕЧЬ"], fsize=110, fname="Oswald-Bold.ttf")
    h = 0.20; w = h * small.size[0] / small.size[1]
    paste_quad(img, small, [cam.proj(p) for p in quad((-1.05, 0.72, 7.4), w, h)])
    img = embers(img, cam, cluster(2.8, 0.22, 9.0, 0.55, 4, 15), t)
    source_line(img, "Наша панель · демонстрация приёма, чужой эфир не используется")
    return img

# ---------------- G15 · подпись-источник в углу ----------------
def g15(t):
    cam = Cam(x=0.0, y=1.40, z=0.30 * t)
    img = room(cam)
    first = t < 2.0
    num = "54 836" if first else "116 175"
    cap = ["СОКРАЩЕНО ЗА ВЕСЬ 2025 ГОД"] if first else ["ЗА ЯНВАРЬ — АВГУСТ 2026"]
    t0 = 0.25 if first else 2.0
    k = 1.0 + 0.09 * (1.0 - out_expo((t - t0) / 0.10)) if t >= t0 else 0.0
    if k > 0:
        tex = text_tex([num], fsize=430, fname="Oswald-Bold.ttf")
        h = 0.95 * k; w = h * tex.size[0] / tex.size[1]
        c = quad((0.0, 1.95, 8.4), w, h)
        floor_shadow(img, cam, c, tex)
        extrude(img, cam, c, tex, depth=0.14, steps=8)
        sub = text_tex(cap, fsize=120, fname="Oswald-Bold.ttf")
        hs = 0.21; ws = hs * sub.size[0] / sub.size[1]
        paste_quad(img, sub, [cam.proj(p) for p in quad((0.0, 1.18, 8.4), ws, hs)])
    img = embers(img, cam, cluster(-3.0, 0.22, 9.5, 0.55, 4, 16) + cluster(3.2, 0.20, 12.5, 0.48, 3, 17), t)
    source_line(img, "Challenger, Gray & Christmas · 2026" if first else "Росстат · 7 ноября 2026")
    return img

SCENES = {"G13": (g13, 3.3), "G10": (g10, 4.0), "G02": (g02, 3.8),
          "G11": (g11, 3.6), "G12": (g12, 3.2), "G26": (g26, 4.2), "G15": (g15, 4.0)}

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
