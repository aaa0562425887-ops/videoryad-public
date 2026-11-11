# -*- coding: utf-8 -*-
"""Клипы приёмов белого зала: G02, G10, G13. Запуск: shard_zal.py <код> <out.mp4>"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import Cam, quad, paste_quad, room, embers, text_tex, sticker_tex, \
     sheet_tex, extrude, floor_shadow, reflection, wire, out_expo, out_back, out_cubic, seg

FPS = 30

# ---------------- G13 · наклейка влетает с перелётом ----------------
def g13(t):
    cam = Cam(x=0.0, y=1.55, z=0.85 * t)
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
    words = [(0.00, "И МНОГИЕ ИЗ НИХ"), (0.35, "СКАЗАЛИ, ЧТО Я"), (0.75, "ОШИБСЯ.")]
    shown = [w for s, w in words if t >= s]
    if shown:
        hl = {len(" ".join(shown).split(" ")) - 1} if len(shown) == 3 else None
        tex = text_tex(shown, fsize=200, hl=hl)
        h = 0.30 * len(shown) + 0.12
        w = h * tex.size[0] / tex.size[1]
        c = quad((-0.15, 2.78, 9.2), w, h)
        floor_shadow(img, cam, c, tex)
        extrude(img, cam, c, tex, depth=0.055, steps=5)
    img = embers(img, cam, [(2.2, 0.22, 9.5, 0.085), (-2.6, 0.18, 12.0, 0.07)], t)
    # НАКЛЕЙКИ — главный приём
    for word, t0, rot, pos in (("ХАЙП", 1.00, -4.5, (-1.60, 1.50, 9.6)), ("ФЕЙК", 1.60, 3.5, (1.80, 2.18, 10.7))):
        if t < t0: continue
        k = 1.0 + 0.12 * (1.0 - out_expo((t - t0) / 0.10))
        tex = sticker_tex(word)
        h = 1.05 * k
        w = h * tex.size[0] / tex.size[1]
        c = quad((pos[0], pos[1], pos[2]), w, h, roll=math.radians(rot))
        floor_shadow(img, cam, c, tex)
        paste_quad(img, tex, [cam.proj(p) for p in c])
    return img

# ---------------- G10 · объёмное слово вырастает из пола ----------------
def g10(t):
    cam = Cam(x=0.95, y=1.45, z=0.55 * t)
    img = room(cam)
    # кубы-мебель с углями наверху
    cubes = [(-4.3, 0.0, 10.4, 0.62), (4.4, 0.0, 12.6, 0.70), (-4.6, 0.0, 16.0, 0.55)]
    for cx, cy, cz, s in cubes:
        if cz - cam.z < 0.8: continue
        tex = Image.new("RGBA", (120, 120), (58, 55, 52, 255))
        c = quad((cx, s / 2, cz), s, s)
        extrude(img, cam, c, tex, depth=s * 0.9, steps=5, shade=(46, 44, 42))
    small = [(0.0, "И ОНИ"), (0.30, "ПОШЛИ"), (0.60, "В ГОНКУ")]
    sh = [w for s, w in small if t >= s]
    if sh:
        tex = text_tex([" ".join(sh)], fsize=120)
        h = 0.26; w = h * tex.size[0] / tex.size[1]
        c = quad((0.3, 2.62, 8.4), w, h)
        paste_quad(img, tex, [cam.proj(p) for p in c])
    # СЛОВО вырастает из пола
    t0 = 1.15
    if t >= t0:
        k = out_back((t - t0) / 0.30)
        tex = text_tex(["ГОНКА."], fsize=330)
        full_h = 0.98
        h = full_h * k
        if h > 0.02:
            w = full_h * tex.size[0] / tex.size[1]
            c = quad((0.55, h / 2, 8.6), w * (h / full_h), h, yaw=math.radians(15))
            floor_shadow(img, cam, c, tex)
            reflection(img, cam, c, tex, strength=0.07)
            extrude(img, cam, c, tex, depth=0.19, steps=10)
    img = embers(img, cam, [(-4.3, 0.70, 10.4, 0.09), (4.4, 0.78, 12.6, 0.095),
                            (1.9, 0.16, 9.0, 0.07)], t)
    return img

# ---------------- G02 · надпись выброшена в объём ----------------
def g02(t):
    cam = Cam(x=0.35 * t - 0.4, y=1.6, z=1.25 * t)
    img = room(cam)
    tex = text_tex(["ЭТО УЖЕ", "ЗДЕСЬ"], fsize=300, hl={2})
    hit = 1.05
    if t >= hit:
        k = 1.0 + 0.10 * (1.0 - out_expo((t - hit) / 0.14))
        h = (0.52 * 2) * k
        w = h * tex.size[0] / tex.size[1]
        c = quad((1.05, 1.78, 10.2), w, h, yaw=math.radians(-19))
        floor_shadow(img, cam, c, tex)
        reflection(img, cam, c, tex, strength=0.08)
        extrude(img, cam, c, tex, depth=0.14, steps=8)
    sheets = [(-3.9, 2.4, 13.5, 16)]
    for (x, y, z, rot) in sheets:
        if z - cam.z < 0.7: continue
        s = sheet_tex(["Из статьи · февраль", "Не через десять лет."])
        c = quad((x, y, z), 1.5, 0.97, yaw=math.radians(rot))
        wire(img, cam, (x - 0.55, y + 0.48, z)); wire(img, cam, (x + 0.55, y + 0.48, z))
        paste_quad(img, s, [cam.proj(p) for p in c])
    img = embers(img, cam, [(2.0, 0.2, 9.0, 0.08), (-2.4, 0.17, 12.5, 0.075)], t)
    return img

SCENES = {"G13": (g13, 4.0), "G10": (g10, 4.0), "G02": (g02, 4.2)}

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
