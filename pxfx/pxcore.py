#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Приёмы, забранные из pixelfx (MIT, patch.gg), переложенные на наш стек.

Четыре вещи, которых у нас не было:

1. СВЕТОВОЙ БУФЕР. Кадр держит два слоя: `color` — пиксели (плашки, текст,
   тела частиц) и `light` — аддитивное свечение, которое кладётся СВЕРХУ уже
   после подмешивания фона. Горячее выглядит горячим не потому, что оно
   белое, а потому, что светит на соседние пиксели.
2. ЧАСТИЦЫ НА ФИКСИРОВАННОМ ШАГЕ. Симуляция идёт по 1/120 с независимо от
   fps клипа, поэтому искры и дым выглядят одинаково на 25 и на 50 кадрах.
   Каждая частица своя: размер, скорость, задержка, срок жизни.
3. ПЕТЛЯ БЕЗ ШВА. Шум берётся по кругу (целые частоты от фазы), поэтому
   последний кадр стыкуется с первым без рывка — фон можно крутить вечно.
4. ХОД «БЫСТРО ВОШЛО — МЕДЛЕННО ВЫШЛО» + ГЕРОЙ-КАДР. Удар читается, если
   движение садится по outExpo, а на кадре контакта стоит одна-две белые вспышки.

Детерминизм обязателен: всё случайное идёт от seed, поэтому кадр 40 всегда
один и тот же и правку видно сразу.
"""
import math
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FPS = 25

# ── гаммы каналов: рампа от тёмного к яркому, как в pixelfx
RAMPS = {
    "ПЛАНЕТА":   ["#0a1222", "#123a63", "#1f74b8", "#49b4ec", "#b8e8ff", "#ffffff"],
    "5 МИНУТ":   ["#1a0d05", "#5a2608", "#b85a0e", "#f2991f", "#ffd98a", "#ffffff"],
    "ДИПЛОМАТИЯ": ["#17060b", "#4d0f1c", "#99203a", "#e04a62", "#ffb3bd", "#ffffff"],
    "ОГОНЬ":     ["#180600", "#5e1a02", "#bf4a06", "#ff8c1a", "#ffd37a", "#ffffff"],
    "ХОЛОД":     ["#04101c", "#0b2c4d", "#1668a0", "#45b6e0", "#c4ecff", "#ffffff"],
    "ДЫМ":       ["#0a0c10", "#1b2028", "#333b47", "#525d6c", "#7a8694", "#a6b1be"],
}

WF = "/mnt/c/Windows/Fonts/"
LIB = "/usr/share/fonts/truetype/liberation/"
DJV = "/usr/share/fonts/truetype/dejavu/"


def _pick(*names):
    for n in names:
        if os.path.exists(n):
            return n
    return names[-1]


SANS = _pick(WF + "segoeui.ttf", LIB + "LiberationSans-Regular.ttf", DJV + "DejaVuSans.ttf")
SANS_B = _pick(WF + "segoeuib.ttf", LIB + "LiberationSans-Bold.ttf", DJV + "DejaVuSans-Bold.ttf")
SANS_BL = _pick(WF + "ariblk.ttf", WF + "segoeuib.ttf", LIB + "LiberationSans-Bold.ttf", DJV + "DejaVuSans-Bold.ttf")

_fc = {}


def font(path, size):
    k = (path, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def ramp(name, n=6):
    """Рампа канала как список RGB. Шаги жёсткие — мягкость живёт в свете."""
    cs = [hx(c) for c in RAMPS[name]]
    if n == len(cs):
        return cs
    out = []
    for i in range(n):
        u = i * (len(cs) - 1) / (n - 1)
        a, b, f = cs[int(u)], cs[min(int(u) + 1, len(cs) - 1)], u - int(u)
        out.append(tuple(int(a[j] + (b[j] - a[j]) * f) for j in range(3)))
    return out


def at(rp, u):
    """Шаг рампы по 0..1 — БЕЗ интерполяции: квантование и держит пиксельный характер."""
    return rp[max(0, min(len(rp) - 1, int(u * len(rp))))]


# ── ход движения
def ease_out_expo(t):
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def ease_out_quart(t):
    return 1 - (1 - t) ** 4


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def ease_lin(t):
    return t


def pulse(t, t0, dur):
    """Герой-кадр: ДО события нуля, на событии единица, дальше быстрый спад.

    Мина, на которую легко сесть: `1 - seg(t, t0, t0+dur)` до t0 даёт единицу,
    и вспышка горит всю сцену до самого удара. Проверено живьём 07.11.
    """
    if t < t0 or t >= t0 + dur:
        return 0.0
    return 1.0 - (t - t0) / dur


def seg(t, a, b):
    """Отрезок времени a..b как 0..1."""
    return 0.0 if t <= a else 1.0 if t >= b else (t - a) / (b - a)


def loopnoise(phase, seed=0, n=4):
    """Шум, который СХОДИТСЯ сам с собой: целые частоты от фазы 0..1.

    Это и есть лечение шва на петле: последний кадр равен первому.
    """
    rng = np.random.default_rng(1000 + seed)
    v = 0.0
    for k in range(1, n + 1):
        v += math.sin(2 * math.pi * k * phase + rng.random() * math.tau) / k
    return v / sum(1.0 / k for k in range(1, n + 1))


class Frame:
    """Кадр из двух буферов: пиксели и свет.

    `color` — обычная RGBA-картинка (плашки, текст, тела частиц).
    `light` — float32-слой, который складывается АДДИТИВНО после подмешивания
    фона, плюс его размытая копия: отсюда ореол вокруг горячего.
    """

    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.color = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.light = np.zeros((h, w, 3), np.float32)

    def draw(self):
        return ImageDraw.Draw(self.color, "RGBA")

    def splat(self, x, y, r, col, k=1.0, hard=1.8):
        """Пятно света: гауссовый спад, складывается с тем, что уже есть."""
        if r <= 0 or k <= 0:
            return
        x0, x1 = max(0, int(x - r * 2)), min(self.w, int(x + r * 2) + 1)
        y0, y1 = max(0, int(y - r * 2)), min(self.h, int(y + r * 2) + 1)
        if x1 <= x0 or y1 <= y0:
            return
        gx = np.arange(x0, x1, dtype=np.float32) - x
        gy = np.arange(y0, y1, dtype=np.float32) - y
        d2 = (gx[None, :] ** 2 + gy[:, None] ** 2) / (r * r)
        fall = np.exp(-d2 * hard).astype(np.float32)
        self.light[y0:y1, x0:x1] += fall[:, :, None] * np.float32([col[0] * k, col[1] * k, col[2] * k])

    def line_light(self, p0, p1, r, col, k=1.0, step=4):
        """Светящаяся линия — цепочка пятен (луч, росчерк, трасса)."""
        n = max(2, int(math.dist(p0, p1) / step))
        for i in range(n + 1):
            u = i / n
            self.splat(p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u, r, col, k)

    def composite(self, bg, glow=1.0, halo=1.15, blur=26):
        """Фон → пиксели → свет (жёсткий) → размытый ореол. Порядок важен."""
        base = np.asarray(bg.convert("RGB"), np.float32)
        c = np.asarray(self.color, np.float32)
        a = c[:, :, 3:4] / 255.0
        out = c[:, :, :3] * a + base * (1 - a)
        L = self.light
        if glow > 0 and L.any():
            soft = np.asarray(
                Image.fromarray(np.clip(L, 0, 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(blur)),
                np.float32)
            out = out + L * glow + soft * halo
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


class Particles:
    """Искры, обломки и дым на ФИКСИРОВАННОМ шаге 1/120 с.

    Симуляция не зависит от fps клипа: шаг всегда один, кадры только снимают
    её состояние. Каждая частица своя — размер, скорость, задержка, срок.
    """

    STEP = 1.0 / 120.0

    def __init__(self, seed=1, grav=900.0, drag=0.55, bounce=0.0, ground=None, lift=260.0):
        self.rng = np.random.default_rng(seed)
        self.grav, self.drag, self.bounce, self.ground = grav, drag, bounce, ground
        self.lift = lift   # дым не падает: своя тяга вверх, отдельная от гравитации
        self.p = []
        self.acc = 0.0
        self.t = 0.0

    def emit(self, n, x, y, speed=(260, 760), ang=(-math.pi, math.pi), life=(0.35, 1.1),
             size=(2.0, 5.5), delay=(0.0, 0.0), rp=None, kind="spark", drift=0.0):
        R = self.rng
        for _ in range(n):
            a = R.uniform(*ang)
            v = R.uniform(*speed)
            self.p.append({
                "x": x, "y": y, "vx": math.cos(a) * v, "vy": math.sin(a) * v,
                "age": -R.uniform(*delay), "life": R.uniform(*life),
                "sz": R.uniform(*size), "rp": rp or ramp("ОГОНЬ"), "kind": kind,
                "sp": R.uniform(0.6, 1.5), "dr": R.uniform(-drift, drift), "ph": R.random(),
            })

    def step(self, dt):
        """Догоняем время ровно шагами по 1/120 — отскок и трение не плывут."""
        self.acc += dt
        self.t += dt
        while self.acc >= self.STEP - 1e-9:
            self.acc -= self.STEP
            h = self.STEP
            for q in self.p:
                q["age"] += h
                if q["age"] < 0:
                    continue
                smoke = q["kind"] == "smoke"
                k = math.exp(-(self.drag * (0.22 if smoke else 1.0)) * h)
                q["vx"] = q["vx"] * k
                q["vy"] = q["vy"] * k + (-self.lift if smoke else self.grav) * h
                # боковое блуждание: клуб идёт не по линейке
                q["x"] += (q["vx"] + (q["dr"] * math.sin(q["age"] * 1.7 + q["ph"] * 6.2) if smoke else q["dr"])) * h
                q["y"] += q["vy"] * h
                if self.ground is not None and q["y"] > self.ground and q["vy"] > 0:
                    q["y"] = self.ground
                    q["vy"] = -q["vy"] * self.bounce
                    q["vx"] *= 0.72
            self.p = [q for q in self.p if q["age"] < q["life"]]

    def draw(self, f, glow=1.0):
        d = f.draw()
        for q in self.p:
            if q["age"] < 0:
                continue
            u = q["age"] / q["life"]
            if q["kind"] == "smoke":
                # дым — по-настоящему полупрозрачный клуб из трёх комков, не ровный круг
                r = q["sz"] * (1 + 3.6 * u)
                a = int(104 * (1 - u) ** 1.15 * (0.25 + 0.75 * min(1.0, q["age"] / 0.5)))
                if a <= 2:
                    continue
                col = at(q["rp"], 0.42 + 0.34 * (1 - u))
                for lx, ly, lr in ((0.0, 0.0, 1.0), (-0.55, 0.22, 0.72), (0.52, 0.30, 0.64)):
                    rr = r * lr
                    ox, oy = q["x"] + lx * r * (0.7 + q["ph"]), q["y"] + ly * r
                    d.ellipse([ox - rr, oy - rr * 0.86, ox + rr, oy + rr * 0.86], fill=col + (a,))
                # снизу его подхватывает свет очага — пока клуб молодой
                warm = max(0.0, 1.0 - u * 2.2)
                if warm > 0:
                    f.splat(q["x"], q["y"] + r * 0.45, r * 1.15, at(q["rp"], 0.55), 0.11 * warm * glow)
                continue
            if q["kind"] == "flame":
                hot = (1 - u) ** 0.8
                col = at(q["rp"], 0.26 + 0.42 * hot)
                r = max(1.0, q["sz"] * (0.5 + 0.7 * hot) * (1 - 0.45 * u))
                a = int(235 * min(1.0, hot * 1.6))
                d.ellipse([q["x"] - r, q["y"] - r * 1.25, q["x"] + r, q["y"] + r * 1.25], fill=col + (a,))
                f.splat(q["x"], q["y"], r * 2.6, col, 0.16 * hot * glow)
                continue
            # искра: тело жёстким шагом рампы, свет отдельно
            hot = 1 - u
            col = at(q["rp"], 0.35 + 0.6 * hot)
            r = max(0.8, q["sz"] * (0.45 + 0.55 * hot))
            tx, ty = q["x"] - q["vx"] * 0.016, q["y"] - q["vy"] * 0.016
            d.line([tx, ty, q["x"], q["y"]], fill=col + (255,), width=max(1, int(r)))
            f.splat(q["x"], q["y"], r * 3.2, col, 0.55 * hot * glow)


def backdrop(name="студия", t=0.0):
    """Фон рисуется кодом: тёмная студия с виньеткой и сеткой, без чужих картинок."""
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    if name == "студия":
        top, bot = np.float32([14, 19, 28]), np.float32([5, 7, 11])
    elif name == "ночь":
        top, bot = np.float32([8, 14, 26]), np.float32([3, 4, 8])
    else:
        top, bot = np.float32([18, 18, 20]), np.float32([6, 6, 7])
    im = top[None, None, :] * (1 - y[:, :, None]) + bot[None, None, :] * y[:, :, None]
    im = np.repeat(im, W, axis=1) if im.shape[1] == 1 else im
    # сетка, чтобы движение и свет было с чем сравнивать
    g = np.zeros((H, W), np.float32)
    g[::60, :] = 1.0
    g[:, ::60] = 1.0
    im += g[:, :, None] * 5.0
    vig = (1 - ((x - 0.5) ** 2 + (y - 0.5) ** 2) * 1.25).clip(0.25, 1.0)
    im *= vig[:, :, None]
    return Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), "RGB")


def label(f, x, y, text, size=40, col=(238, 242, 246), fnt=None, anchor="lt", light=None):
    d = f.draw()
    d.text((x, y), text, font=font(fnt or SANS_B, size), fill=col + (255,), anchor=anchor)
    if light:
        f.splat(x, y, size * 1.1, light, 0.25)


def plate(f, box, col=(12, 16, 24), a=225, edge=None, ew=3):
    d = f.draw()
    d.rectangle(box, fill=col + (a,))
    if edge:
        d.rectangle(box, outline=edge + (255,), width=ew)
