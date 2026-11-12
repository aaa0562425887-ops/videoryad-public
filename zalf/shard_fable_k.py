# -*- coding: utf-8 -*-
"""Белый зал, вторая реализация (часть K: G20, G21, G23).
Запуск: shard_fable_k.py <код> <out.mp4>  ·  один кадр: ZAL_FRAME=1.9 shard_fable_k.py G20 k.png

Числа сняты с плёнки (polosy/G20_vhod, G20_ranshe, G21_vhod, G21_perehod, G23_panel,
G23_hvost + сетки G20/G21/G21b/G23/G23b), перевод доли кадра в метры:
X = (fx-0.5)*0.975*d, Y = 1.55 + (0.5-fy)*0.549*d.

  G20  облако листов 11.5-15.9 и 18.0-19.9: 35-40 белых листов на 1-2 тросах каждый,
       три слоя глубины, лист ~1.0×1.1 м (сетка 18.50: «Same old grift» 34% ширины на
       d≈3), широкие ~2.2×0.7 м; камера идёт сквозь ровно ~1.8 м/с (наклейка от d≈6 до
       d≈1.5 за 2.6 с, 13.3→15.9), ближние уходят за край, не исчезают; фраза «I WASN'T»
       18.5 · «EXAGGERATING.» 18.9 висит выше глаз, камера проходит под ней.
  G21  19.8→20.05 листы ЛОЖАТСЯ: поворот вокруг нижней кромки назад от камеры (на 19.90
       наклон ~35°), за ~0.3 с, с разбросом; камера за те же 0.3 с ныряет с 1.55 до
       ~0.55 м и клюёт вниз ~13° (горизонт выше кадра на 20.0, 10% на 20.1, 22% на 20.3),
       дальше идёт низко ~0.45 м/с и медленно поднимает взгляд до ~7.5°;
       «IF» 20.167 · «ANYTHING...» 20.267 — мелкие тёмные буквы (~0.2 м) висят на тросах
       в 10-15 см над листами (сетка 20.50: y 0.33-0.37 при горизонте 0.22).
  G23  панель эфира 61.467→61.500 входит за один кадр; на сетке 61.50 x 0.07-0.43,
       y 0.12-0.64, правая кромка на 8% выше левой → поворот ~9°, правый край ближе;
       пропорция панели ~1.25:1, на двух тросах; подпись источника внизу кадра
       (y≈0.93, Oswald-подобный серый, ~3.5% высоты) ВЪЕЗЖАЕТ слева за ~0.4 с
       (на 61.600 видна только её вторая половина); справа слова по одному:
       THIS 61.5 · WAS 61.6 · THE 61.8 · FIRST(жёлт.) 62.0 · TIME 62.3 · SOMETHING 62.7 ·
       LIKE 62.9 · THIS 63.0 · HAPPENED. 63.2 · «ACCESS RESTORED · JUL 1, 2026» 63.4.
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zal_core as Z
from zal_core import *

FPS = 30
INK = (18, 18, 20, 255)
PAPER = (251, 251, 250, 255)
YEL = (255, 208, 0, 255)


# ----------------------------------------------------------------- камера с наклоном

class PCam(Cam):
    """та же камера, плюс наклон вниз (pitch > 0 — смотрим в пол)"""
    def __init__(s, x=0.0, y=1.55, z=0.0, yaw=0.0, pitch=0.0):
        Cam.__init__(s, x, y, z, yaw)
        s.pitch = pitch
    def proj(s, p):
        dx, dy, dz = p[0] - s.x, p[1] - s.y, p[2] - s.z
        if s.yaw:
            c, si = math.cos(-s.yaw), math.sin(-s.yaw)
            dx, dz = dx * c - dz * si, dx * si + dz * c
        if s.pitch:
            c, si = math.cos(s.pitch), math.sin(s.pitch)
            dy, dz = dy * c + dz * si, dz * c - dy * si
        if dz < 0.08: dz = 0.08
        k = F / dz
        return (W / 2 + dx * k, H / 2 - dy * k, dz)


def room_p(cam, windows=True, shafts=True, ropes=True):
    """зал из zal_core.room, но горизонт считается от наклона камеры
    (room() держит его на середине кадра; при клевке в пол появился бы шов)"""
    pitch = getattr(cam, "pitch", 0.0)
    hor = H / 2 - F * math.tan(pitch)
    g = Image.new("L", (1, H))
    for y in range(H):
        t = y / H
        g.putpixel((0, y), int(234 - 24 * abs(t - 0.5) * 2))
    base = g.resize((W, H))
    img = Image.merge("RGBA", (base, base, base.point(lambda v: min(255, v + 3)),
                               Image.new("L", (W, H), 255)))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, hor, W, H], fill=(197, 200, 204, 255))
    d.rectangle([0, 0, W, hor], fill=(230, 232, 235, 255))
    for sx in (-1, 1):
        p = [cam.proj((sx * WALL, CEIL, cam.z + 2.0)), cam.proj((sx * WALL, CEIL, cam.z + FAR)),
             cam.proj((sx * WALL, 0.0, cam.z + FAR)), cam.proj((sx * WALL, 0.0, cam.z + 2.0))]
        d.polygon([(q[0], q[1]) for q in p], fill=(222, 225, 229, 255))
    if windows:
        z0 = math.floor((cam.z + 3) / 7.0) * 7.0
        for i in range(10):
            zz = z0 + i * 7.0
            for sx in (-1, 1):
                p = [cam.proj((sx * WALL, 3.75, zz)), cam.proj((sx * WALL, 3.75, zz + 3.1)),
                     cam.proj((sx * WALL, 1.15, zz + 3.1)), cam.proj((sx * WALL, 1.15, zz))]
                d.polygon([(q[0], q[1]) for q in p], fill=(251, 252, 253, 255))
                for k in range(1, 4):
                    yy = 1.15 + 2.6 * k / 4
                    a = cam.proj((sx * WALL, yy, zz)); b = cam.proj((sx * WALL, yy, zz + 3.1))
                    d.line([(a[0], a[1]), (b[0], b[1])], fill=(226, 229, 233, 255), width=2)
    if shafts:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay, "RGBA")
        z0 = math.floor((cam.z + 3) / 7.0) * 7.0
        for i in range(9):
            zz = z0 + i * 7.0
            for sx in (-1, 1):
                p = [cam.proj((sx * (WALL - 0.2), 0.0, zz + 0.6)),
                     cam.proj((sx * (WALL - 0.2), 0.0, zz + 3.5)),
                     cam.proj((sx * (WALL - 3.4), 0.0, zz + 5.2)),
                     cam.proj((sx * (WALL - 3.4), 0.0, zz + 2.3))]
                dl.polygon([(q[0], q[1]) for q in p], fill=(255, 255, 255, 120))
        lay = lay.filter(ImageFilter.GaussianBlur(9))
        img.alpha_composite(lay)
    if ropes:
        rng = np.random.default_rng(5)
        dr = ImageDraw.Draw(img, "RGBA")
        z0 = math.floor((cam.z + 4) / 3.0) * 3.0
        for i in range(26):
            zz = z0 + (i % 13) * 3.0 + float(rng.uniform(-1.0, 1.0))
            xx = float(rng.uniform(-4.6, 4.6))
            yy = float(rng.uniform(0.9, 2.4))
            if zz - cam.z < 1.5: continue
            a = cam.proj((xx, CEIL, zz)); b = cam.proj((xx, yy, zz))
            dr.line([(a[0], a[1]), (b[0], b[1])], fill=(150, 152, 156, 255), width=1)
    return img


# ----------------------------------------------------------------- общие вещи

def pop(t0, t, dur=0.10, k0=1.15):
    """вход как на плёнке: первый кадр крупнее и прозрачнее, за 3 кадра садится"""
    if t < t0 - 1e-6: return None
    u = seg(t, t0, t0 + dur)
    return k0 + (1.0 - k0) * out_cubic(u), 0.55 + 0.45 * clamp01(u * 2.2)

def thin_wire(canvas, cam, p, color=(112, 114, 118, 230), width=1):
    a = cam.proj((p[0], CEIL, p[2])); b = cam.proj(p)
    if b[2] < 0.12: return
    ImageDraw.Draw(canvas, "RGBA").line([(a[0], a[1]), (b[0], b[1])], fill=color, width=width)

def clip_mark(canvas, cam, p, size=0.035):
    """чёрный зажим на кромке листа, где крепится трос (на сетке 18.50 — точки на тросах)"""
    c = quad((p[0], p[1] + size * 0.4, p[2]), size, size * 0.8)
    if min(q[2] for q in c) - cam.z < 0.15: return
    tex = Image.new("RGBA", (8, 8), (28, 28, 30, 255))
    paste_quad(canvas, tex, [cam.proj(q) for q in c])

def rush_blur(img, k):
    if k <= 0.01: return img
    base = img.convert("RGB")
    for z in (1.010, 1.022):
        sw, sh = int(W * z), int(H * z)
        big = base.resize((sw, sh), Image.BILINEAR).crop(((sw - W) // 2, (sh - H) // 2,
                                                            (sw - W) // 2 + W, (sh - H) // 2 + H))
        base = Image.blend(base, big, 0.28 * k)
    return base.convert("RGBA")


# ----------------------------------------------------------------- листы с репликами

HEADS = ["Same old hype cycle.", "This is called\ncontent marketing.", "Stop being so\ncredulous to this\nkind of propaganda.",
         "A lot of fear\nmongering.", "...it's a joke of an\nessay. Dude is just\ntrying to hype AI", "It's an ad for some\nguy's hypeman\nstartup. Ignore.",
         "Reads like a\npress release.", "Wake me up\nwhen it ships.", "Classic PR stunt.", "Benchmarks or it\ndidn't happen.",
         "Cool story.\nSource?", "This will age\nbadly.", "Who paid\nfor this?", "Another vested\ninterest talking.",
         "Nobody asked\nfor this.", "Pure doom\nposting.", "AI slop, again.", "Not even wrong."]
METAS = ["Reddit · r/agi · Feb 12, 2026", "Reddit · r/ArtificialInteligence · Feb 14, 2026", "Reddit · r/samharris · Feb 22, 2026",
         "Reddit · r/ChatGPT · Feb 15, 2026", "Reddit · r/ProductManagement · Feb 13, 2026", "Reddit · r/BetterOffline · Feb 11, 2026",
         "Hacker News · Feb 12, 2026", "Reddit · r/technology · Feb 16, 2026", "Reddit · r/singularity · Feb 18, 2026",
         "Reddit · r/programming · Feb 20, 2026", "Reddit · r/Futurology · Feb 19, 2026", "Hacker News · Feb 21, 2026"]
BODIES = [
    ["I've seen this exact post every six months since 2023.", "Big claims, a vague demo, and a link to a waitlist.",
     "Call me when it does something my laptop can't."],
    ["Making a model good at writing code is the easy part.", "The hard part is everything around it: trust, cost,",
     "and someone who answers when it breaks at 3 am."],
    ["Nothing grows exponentially forever. Physics still", "applies, even to venture capital slide decks."],
    ["The author is a founder with a product to sell.", "That doesn't make him wrong, but it does make",
     "this a sales pitch with extra steps."],
    ["Covid comparison is apt. Everyone knew something", "was coming, nobody agreed on what, and the loudest",
     "voices were mostly wrong about the details."],
    ["Honest question: who is the audience for this?", "People who already agree? They don't need it.",
     "People who don't? They won't read 4,000 words."],
    ["I'm not convinced this person knows what", "they're talking about. Half of the claims are",
     "unsourced and the other half are vibes."],
    ["They focused on coding first because coding", "is where the money is. Everything else is",
     "a footnote in the pitch deck."],
    ["What's the point of using these tools if they're", "going to replace us anyway? Weird to say that",
     "and then conclude \"go spend money on my stuff\"."],
    ["Every year it's the same: a chart that goes up,", "a quote from a CEO, and a deadline that moves.",
     "I'll believe it when my rent does."],
]
THREAD = ["8 months ago | parent | context | favorite | on: The Long Post",
          "9 months ago | prev | next | favorite | on: Something Is Happening",
          "7 months ago | parent | context | favorite | on: The Letter"]

_TEX = {}
def reply_tex(kind, i):
    """лист с репликой: 'a' — заголовок+мета+абзац (760×820), 'b' — широкий тред (1200×420),
    'c' — короткая реплика (640×360). Бумага чуть теплее белого, тонкая серая кромка."""
    key = (kind, i)
    if key in _TEX: return _TEX[key]
    rng = np.random.default_rng(1000 + i * 7 + ord(kind))
    head = HEADS[i % len(HEADS)]; meta = METAS[(i * 5 + 1) % len(METAS)]; body = BODIES[(i * 3) % len(BODIES)]
    if kind == "a":
        w, h = 760, 820
        img = Image.new("RGBA", (w, h), PAPER); d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w - 1, h - 1], outline=(222, 222, 220, 255), width=2)
        fh = font("Arimo-Bold.ttf", 74); y = 40
        for ln in head.split("\n"):
            d.text((42, y), ln, font=fh, fill=INK); y += 82
        y += 16
        d.text((42, y), meta, font=font("Oswald-Bold.ttf", 30), fill=(132, 132, 134, 255)); y += 62
        fb = font("Arimo-Bold.ttf", 27)
        for par in (body, BODIES[(i * 3 + 1) % len(BODIES)], BODIES[(i * 3 + 2) % len(BODIES)]):
            for ln in par:
                if y > h - 60: break
                d.text((42, y), ln, font=fb, fill=(84, 84, 86, 255)); y += 35
            y += 20
    elif kind == "b":
        w, h = 1200, 420
        img = Image.new("RGBA", (w, h), PAPER); d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w - 1, h - 1], outline=(222, 222, 220, 255), width=2)
        d.text((40, 30), THREAD[i % len(THREAD)], font=font("Arimo-Bold.ttf", 22), fill=(168, 168, 170, 255))
        y = 86
        fb = font("Arimo-Bold.ttf", 30)
        q = BODIES[(i * 3 + 1) % len(BODIES)]
        d.text((40, y), "> " + q[0], font=fb, fill=(70, 70, 72, 255)); y += 40
        for ln in q[1:]:
            d.text((40, y), ln, font=fb, fill=(70, 70, 72, 255)); y += 40
        y += 22
        for ln in body:
            if y > h - 44: break
            d.text((40, y), ln, font=fb, fill=(70, 70, 72, 255)); y += 40
    else:
        w, h = 640, 360
        img = Image.new("RGBA", (w, h), PAPER); d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w - 1, h - 1], outline=(222, 222, 220, 255), width=2)
        fh = font("Arimo-Bold.ttf", 60); y = 36
        for ln in head.split("\n")[:3]:
            d.text((36, y), ln, font=fh, fill=INK); y += 68
        d.text((36, h - 62), meta, font=font("Oswald-Bold.ttf", 24), fill=(132, 132, 134, 255))
    _TEX[key] = img
    return img

# один сид на G20 и G21 — одно облако в двух состояниях
_SHEETS = None
def sheets():
    """38 листов: 10 ближних (z 2.5-7), 14 средних (7-13), 14 дальних (13-24).
    Ни один не пересекает коридор камеры |x|<0.5, 1.1<y<2.0 — ближние уходят за край кадра."""
    global _SHEETS
    if _SHEETS is not None: return _SHEETS
    rng = np.random.default_rng(20262021)
    out = []
    plan = [("near", 13, 2.5, 7.0), ("mid", 14, 7.0, 13.0), ("far", 13, 13.0, 24.0)]
    i = 0
    for layer, n, z0, z1 in plan:
        k = 0
        while k < n:
            kind = rng.choice(["a", "a", "a", "b", "c", "c"])
            if kind == "a":
                w = float(rng.uniform(1.2, 1.7)); h = w * 820 / 760
            elif kind == "b":
                w = float(rng.uniform(2.2, 3.0)); h = w * 420 / 1200
            else:
                w = float(rng.uniform(0.9, 1.2)); h = w * 360 / 640
            x = float(rng.uniform(-3.0, 3.0)); z = float(rng.uniform(z0, z1))
            y = float(rng.uniform(max(h / 2 + 0.15, 0.8), min(4.2 - h / 2, 3.2)))
            yaw = math.radians(float(rng.uniform(-14, 14))); roll = math.radians(float(rng.uniform(-2.5, 2.5)))
            c = quad((x, y, z), w, h, yaw, roll)
            xs = [q[0] for q in c]; ys = [q[1] for q in c]
            if max(xs) > -0.5 and min(xs) < 0.5 and max(ys) > 1.1 and min(ys) < 2.0:
                continue
            # не лепить листы друг на друга в одном слое
            bad = False
            for s in out:
                if abs(s["z"] - z) < 0.7 and abs(s["x"] - x) < (s["w"] + w) / 2 * 0.5 and abs(s["y"] - y) < (s["h"] + h) / 2 * 0.5:
                    bad = True; break
            if bad: continue
            out.append(dict(i=i, kind=kind, x=x, y=y, z=z, w=w, h=h, yaw=yaw, roll=roll, layer=layer,
                            fall=float(rng.uniform(0.0, 0.16))))
            i += 1; k += 1
    _SHEETS = out
    return out

def draw_sheet(img, cam, s, corners, wires=True, opacity=1.0):
    if min(q[2] for q in corners) - cam.z < 0.12: return
    tex = reply_tex(s["kind"], s["i"])
    pts = [cam.proj(q) for q in corners]
    if wires:
        tl, tr = corners[0], corners[1]
        fr = (0.5,) if s["kind"] == "c" else (0.22, 0.78)
        for f in fr:
            p = (tl[0] + (tr[0] - tl[0]) * f, tl[1] + (tr[1] - tl[1]) * f, tl[2] + (tr[2] - tl[2]) * f)
            thin_wire(img, cam, p)
    paste_quad(img, tex, pts, opacity)
    if wires:
        for f in fr:
            p = (tl[0] + (tr[0] - tl[0]) * f, tl[1] + (tr[1] - tl[1]) * f, tl[2] + (tr[2] - tl[2]) * f)
            clip_mark(img, cam, p)

def hang_phrase(img, cam, t, words, center, cap, depth=0.12, starts=None, k0=1.15, cond=0.80):
    """тёмные объёмные слова (ArialBlack сжат COND) на тросах, строки центрированы;
    words — список строк, starts — время появления каждой строки"""
    f = 200
    texs = [text_tex([ln], fsize=f, cond=cond, color=INK) for ln in words]
    sc = cap / (0.715 * f)       # метров на пиксель
    hline = f * 1.02 * sc + 0.08
    cx, cy, cz = center
    for j, (ln, tex) in enumerate(zip(words, texs)):
        p = pop(starts[j], t, k0=k0)
        if p is None: continue
        s, op = p
        w = tex.size[0] * sc * s; h = tex.size[1] * sc * s
        yc = cy - j * hline
        c = quad((cx, yc, cz), w, h)
        if min(q[2] for q in c) - cam.z < 0.15: continue
        for fr in (0.18, 0.82):
            thin_wire(img, cam, (c[0][0] + (c[1][0] - c[0][0]) * fr, c[0][1] + 0.02, cz), color=(96, 98, 102, 230), width=2)
        if s > 1.06:
            for sh in (-0.04, 0.04):
                paste_quad(img, tex, [cam.proj(q) for q in quad((cx + sh * w, yc, cz), w, h)], 0.2)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        extrude(lay, cam, c, tex, depth=depth, steps=6, shade=(34, 33, 35))
        if op < 1.0:
            a = lay.split()[3].point(lambda v: int(v * op)); lay.putalpha(a)
        img.alpha_composite(lay)


# ----------------------------------------------------------------- G20

def g20_cam_z(t):
    """разгон за ~0.5 с до 1.8 м/с и ровный ход (на плёнке камера не останавливается)"""
    v, tau = 1.8, 0.35
    return v * (t - tau * (1 - math.exp(-t / tau)))

def g20(t):
    """облако листов, камера летит сквозь: ближние читаются, дальние — массой"""
    cz = g20_cam_z(t)
    # к концу камера пригибается, как на плёнке 19.7-19.9 — проходит ПОД фразой
    cy = 1.55 - 0.35 * out_cubic(seg(t, 2.3, 3.3))
    cam = Cam(0.04 * math.sin(t * 0.9), cy + 0.02 * math.sin(t * 1.3 + 1.0), cz, 0.0)
    img = room(cam)
    sh = sorted(sheets(), key=lambda s: -s["z"])
    phrase_z = 5.6
    done_phrase = False
    for s in sh:
        if not done_phrase and s["z"] < phrase_z:
            hang_phrase(img, cam, t, ["I WASN'T", "EXAGGERATING."], (0.0, 2.55, phrase_z), 0.42,
                        starts=[0.50, 0.90])
            done_phrase = True
        c = quad((s["x"], s["y"], s["z"]), s["w"], s["h"], s["yaw"], s["roll"])
        draw_sheet(img, cam, s, c)
    if not done_phrase:
        hang_phrase(img, cam, t, ["I WASN'T", "EXAGGERATING."], (0.0, 2.55, phrase_z), 0.42, starts=[0.50, 0.90])
    v = 1.8 * (1 - math.exp(-t / 0.35))
    return rush_blur(img, 0.22 * clamp01(v / 1.8))


# ----------------------------------------------------------------- G21

def lying_corners(s, u):
    """лист поворачивается вокруг нижней кромки назад от камеры и ложится на пол.
    u — ход падения 0..1: кромка падает с ускорением, наклон 90°·u^1.4 (на 19.90 ~35°)"""
    ux = (math.cos(s["yaw"]), 0.0, math.sin(s["yaw"]))
    nz = (-math.sin(s["yaw"]), 0.0, math.cos(s["yaw"]))
    yb0 = s["y"] - s["h"] / 2
    yb = yb0 * (1 - u * u) + 0.004 * (s["i"] % 5)
    th = math.radians(90.0) * (u ** 1.4)
    up = (nz[0] * math.sin(th), math.cos(th), nz[2] * math.sin(th))
    g = out_cubic(u)
    bx = s["x"] - math.copysign(min(0.75, abs(s["x"]) * 0.45), s["x"]) * g
    bz = s["z"] + 0.25 * g
    w, h = s["w"], s["h"]
    bl = (bx - ux[0] * w / 2, yb, bz - ux[2] * w / 2)
    br = (bx + ux[0] * w / 2, yb, bz + ux[2] * w / 2)
    tl = (bl[0] + up[0] * h, bl[1] + up[1] * h, bl[2] + up[2] * h)
    tr = (br[0] + up[0] * h, br[1] + up[1] * h, br[2] + up[2] * h)
    return [tl, tr, br, bl]

FALL0, FALLD = 0.30, 0.32

def g21(t):
    """те же листы ложатся на пол, камера ныряет и идёт низко над ними"""
    # камера: 0-0.3 стоит; 0.3-0.8 ныряет с 1.55 до 0.55 м и клюёт на 13°; дальше низко вперёд
    k = out_cubic(seg(t, FALL0, FALL0 + 0.5))
    cy = 1.55 - 1.0 * k
    pitch = math.radians(13.0 * k - 5.5 * seg(t, 0.8, 4.5) ** 0.8)
    cz = 1.5 * k + 0.45 * max(0.0, t - 0.8)
    cam = PCam(0.03 * math.sin(t * 0.9), cy + 0.012 * math.sin(t * 1.7), cz, 0.0, pitch)
    img = room_p(cam)
    sh = sheets()
    # тросы остаются висеть, когда листы сорвались — тонкие, до прежней точки крепления
    for s in sh:
        u = seg(t, FALL0 + s["fall"], FALL0 + s["fall"] + FALLD)
        if u <= 0: continue
        c = quad((s["x"], s["y"], s["z"]), s["w"], s["h"], s["yaw"], s["roll"])
        tl, tr = c[0], c[1]
        for f in ((0.5,) if s["kind"] == "c" else (0.22, 0.78)):
            thin_wire(img, cam, (tl[0] + (tr[0] - tl[0]) * f, tl[1] + (tr[1] - tl[1]) * f - 0.03, tl[2] + (tr[2] - tl[2]) * f))
    # сами листы: от дальних к ближним; лежащие — по дальности нижней кромки
    order = []
    for s in sh:
        u = seg(t, FALL0 + s["fall"], FALL0 + s["fall"] + FALLD)
        order.append((s["z"] + (s["h"] if u >= 1 else 0.0), s, u))
    order.sort(key=lambda o: -o[0])
    for _, s, u in order:
        if u <= 0:
            c = quad((s["x"], s["y"], s["z"]), s["w"], s["h"], s["yaw"], s["roll"])
            draw_sheet(img, cam, s, c, wires=True)
        else:
            c = lying_corners(s, u)
            if min(q[2] for q in c) - cam.z < 0.12: continue
            if u < 1.0:
                # смаз падения: лёгкая копия чуть выше
                c2 = lying_corners(s, max(0.0, u - 0.12))
                paste_quad(img, reply_tex(s["kind"], s["i"]), [cam.proj(q) for q in c2], 0.25)
            draw_sheet(img, cam, s, c, wires=False)
    # «IF» «ANYTHING...» — мелкие буквы на тросах, в 12 см над листами, с тенью на пол
    if t >= 1.0:
        f = 200
        tex_if = text_tex(["IF"], fsize=f, cond=0.80, color=INK)
        tex_an = text_tex(["ANYTHING..."], fsize=f, cond=0.80, color=INK)
        sc = 0.22 / (0.715 * f)
        zc = 6.6
        x0 = -0.55
        for tex, t0, xoff in ((tex_if, 1.0, 0.0), (tex_an, 1.1, tex_if.size[0] * sc + 0.10)):
            p = pop(t0, t, k0=1.15)
            if p is None: continue
            s_, op = p
            w = tex.size[0] * sc * s_; h = tex.size[1] * sc * s_
            c = quad((x0 + xoff + w / 2, 0.12 + h / 2, zc), w, h)
            # тень на пол (свет сверху): плоская копия под буквами
            shd = [(c[3][0] + 0.03, 0.012, c[0][2] + 0.10), (c[2][0] + 0.03, 0.012, c[1][2] + 0.10),
                   (c[2][0] + 0.03, 0.012, c[2][2] - 0.06), (c[3][0] + 0.03, 0.012, c[3][2] - 0.06)]
            a = tex.split()[3].point(lambda v: int(v * 0.30))
            dark = Image.new("RGBA", tex.size, (40, 40, 42, 255)); dark.putalpha(a)
            paste_quad(img, dark.filter(ImageFilter.GaussianBlur(10)), [cam.proj(q) for q in shd])
            for fr in (0.2, 0.8):
                thin_wire(img, cam, (c[0][0] + (c[1][0] - c[0][0]) * fr, c[0][1], zc), color=(96, 98, 102, 230), width=2)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            extrude(lay, cam, c, tex, depth=0.05, steps=4, shade=(34, 33, 35))
            if op < 1.0:
                lay.putalpha(lay.split()[3].point(lambda v: int(v * op)))
            img.alpha_composite(lay)
    dive = seg(t, FALL0, FALL0 + 0.5)
    blur = math.sin(dive * math.pi) * 0.5
    return rush_blur(img, blur)


# ----------------------------------------------------------------- G23

_TV = {}
def tv_panel_tex():
    """наша панель эфира из библиотеки (tv_tex), пропорция образца ~1.25:1, тонкая чёрная рама"""
    if "p" not in _TV:
        core = tv_tex(w=960, h=768)
        b = 14
        img = Image.new("RGBA", (960 + 2 * b, 768 + 2 * b), (22, 22, 24, 255))
        img.alpha_composite(core, (b, b))
        _TV["p"] = img
    return _TV["p"]

G23_WORDS = [[("THIS", 0.00, False), ("WAS", 0.10, False), ("THE", 0.30, False), ("FIRST", 0.50, True)],
             [("TIME", 0.80, False), ("SOMETHING", 1.20, False)],
             [("LIKE", 1.40, False), ("THIS", 1.50, False), ("HAPPENED.", 1.70, False)]]

def words_now(t):
    lines, hl, idx = [], set(), 0
    for row in G23_WORDS:
        ws = []
        for w, t0, y in row:
            if t < t0: continue
            ws.append(w)
            if y: hl.add(idx)
            idx += 1
        if ws: lines.append(" ".join(ws))
    return lines, hl

def g23(t):
    """панель эфира висит плоско, повёрнута на 9°, подпись источника въезжает снизу слева"""
    cam = Cam(0.0, 1.55, 0.12 * t, 0.0)
    img = room(cam)
    # панель: d=5, центр x=-1.25, y=1.9; 1.84×1.47 м; правый край ближе (yaw -9°)
    tex = tv_panel_tex()
    p = pop(0.0, t, k0=1.10)
    if p is not None:
        s, op = p
        w = 1.84 * s; h = w * tex.size[1] / tex.size[0]
        c = quad((-1.25, 1.90, 5.0), w, h, math.radians(-9.0))
        for fr in (0.22, 0.78):
            thin_wire(img, cam, (c[0][0] + (c[1][0] - c[0][0]) * fr, c[0][1], c[0][2] + (c[1][2] - c[0][2]) * fr),
                      color=(92, 94, 98, 235), width=2)
        reflection(img, cam, c, tex, strength=0.09)
        floor_shadow(img, cam, c, tex)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        extrude(lay, cam, c, tex, depth=0.06, steps=4, shade=(36, 36, 40))
        if op < 1.0:
            lay.putalpha(lay.split()[3].point(lambda v: int(v * op)))
        img.alpha_composite(lay)
    # слова справа, по одному, FIRST с жёлтым маркером; блок висит на тросах
    lines, hl = words_now(t)
    if lines:
        hang_block(img, cam, lines, hl, (0.38, 2.87, 6.0), 0.27, fsize=170, fname="Oswald-Bold.ttf", depth=0.05)
    if t >= 1.90:
        sub = text_tex(["ACCESS RESTORED · JUL 1, 2026"], fsize=110, fname="Oswald-Bold.ttf",
                       color=(118, 120, 124, 255))
        sc = 0.17 / 110
        w = sub.size[0] * sc; h = sub.size[1] * sc
        c = quad((0.38 + w / 2, 2.87 - 3 * 0.27 - 0.10 - h / 2 - 0.06, 6.0), w, h)
        k = out_cubic(seg(t, 1.90, 2.00))
        paste_quad(img, sub, [cam.proj(q) for q in c], 0.3 + 0.7 * k)
    # подпись источника: внизу кадра, въезжает слева за 0.45 с с торможением
    u = out_expo(seg(t, 0.05, 0.50))
    if t >= 0.05:
        f = font("Oswald-Bold.ttf", 40)
        d = ImageDraw.Draw(img, "RGBA")
        txt = "Studio guest · The Morning Desk · on Channel 7 Evening News, June 2026"
        x = 54 - (1 - u) * W * 0.48
        d.text((x, H - 88), txt, font=f, fill=(84, 86, 90, 255))
    return img


SCENES = {"G20": (g20, 4.5), "G21": (g21, 4.5), "G23": (g23, 4.5)}

def render(code, out):
    fn, dur = SCENES[code]
    n = int(dur * FPS)
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        exe = "ffmpeg"
    p = subprocess.Popen([exe, "-y", "-nostdin", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(fn(i / FPS).convert("RGB").tobytes())
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
