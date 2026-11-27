# -*- coding: utf-8 -*-
"""ДВЕНАДЦАТЬ КАРТОЧЕК ИЗ «ВЕРИЦЫ», ПЕРЕНЕСЕНЫ В NEWS-VIDEO (27.11.2026).

Его слово 26.11 (принято, план — `~/.claude/skills/effects-library/OPEN-ITEMS.md`,
раздел «ПРИНЯТО 26.11.2026»): раскидать P1-P20 из `~/kino-verica/engine` на
видеоряд. Перенесена ТОЛЬКО чистая отрисовка — источник (`scenes3.py`,
`scenes4.py`, `scenes5.py`, `scenes6.py`) рисует эти сцены под ГЛОБАЛЬНЫЙ
таймлайн фильма (аргументы `k`/`tt` считает `sborka.py`/`timing.py`), а здесь
каждая карточка — САМОСТОЯТЕЛЬНАЯ функция вида `card_put`/`render_cards`
(see `template/kino_dok_text.py` — тот же приём: `out=`/`t=`, без привязки к
фильму). Правка приёма содержательно — в ОБОИХ местах, тут и в исходнике.

Своих шрифтов и `core.py` не тащим — ХВАТАЕТ того, что уже лежит в общей
`template/fonts/` (Oswald-Bold — заголовки, RobotoCondensed-Bold — подписи,
Tinos-Bold — засечки, Caveat-Bold — почерк для письма). Палитра — по каналу
(`template/palitra.py`), не своя графитовая: карточка должна узнаваться как
НАША, а не как кадр чужого фильма.

Возвращает RGB-кадр 1920×1080 (этого ждёт `style_cards.render_anim`).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
_TEMPLATE = os.path.join(os.path.dirname(HERE), "template")
if _TEMPLATE not in sys.path:
    sys.path.insert(0, _TEMPLATE)
try:
    import palitra
except Exception:
    palitra = None

W, H = 1920, 1080
SS = 2                      # суперсэмплинг текстовых/векторных слоёв
SAFE_X, SAFE_Y = 96, 54

FONTS = os.path.join(_TEMPLATE, "fonts")
F_HEAD = os.path.join(FONTS, "Oswald-Bold.ttf")
F_SANS = os.path.join(FONTS, "RobotoCondensed-Bold.ttf")
F_SERIF = os.path.join(FONTS, "Tinos-Bold.ttf")
F_HAND = os.path.join(FONTS, "Caveat-Bold.ttf")

PAPER = (210, 201, 181)
PAPER2 = (190, 180, 159)
INK = (32, 30, 27)
GRAPHITE = (16, 16, 19)
GRAPHITE2 = (26, 26, 30)
WHITE = (240, 238, 234)
GREY = (140, 140, 145)

_fc = {}


def _font(path, size):
    size = max(4, int(round(size)))
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]


def _accent(channel):
    if palitra is not None and channel:
        try:
            return tuple(palitra.accent(channel, tiho=True))
        except Exception:
            pass
    return (204, 34, 30)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def out_cubic(t):
    t = clamp(t)
    return 1 - pow(1 - t, 3)


def layer():
    return Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))


def done(im):
    return im.resize((W, H), Image.LANCZOS)


def text_w(d, text, fnt, track=0.0):
    return sum(d.textlength(ch, font=fnt) for ch in text) + \
        track * fnt.size * max(0, len(text) - 1)


def tracked(d, x, y, text, fnt, fill, track=0.0, anchor="ls"):
    tw = text_w(d, text, fnt, track)
    if anchor[0] == "m":
        x -= tw / 2
    elif anchor[0] == "r":
        x -= tw
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill, anchor="ls")
        x += d.textlength(ch, font=fnt) + track * fnt.size
    return tw


def text_layer(text, px, color, x, y, font_path=F_HEAD, anchor="ms", track=0.02, a=1.0):
    im = layer()
    d = ImageDraw.Draw(im)
    f = _font(font_path, px * SS)
    col = tuple(color) + (int(255 * clamp(a)),)
    tracked(d, x * SS, y * SS, text, f, col, track, anchor)
    return done(im)


def fit_px(text, px, maxw, font_path=F_HEAD, track=0.0):
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    while px > 18 and text_w(d, text, _font(font_path, px * SS), track) / SS > maxw:
        px -= 4
    return px


def wrap(text, px, maxw, font_path=F_SERIF, track=0.0):
    """Перенос по словам в рамку maxw, отдаёт список строк."""
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    f = _font(font_path, px * SS)
    words = (text or "").split()
    lines, cur = [], ""
    for w_ in words:
        cand = (cur + " " + w_).strip()
        if text_w(d, cand, f, track) / SS <= maxw or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def _grain(seed=3):
    rng = np.random.default_rng(seed)
    n = (rng.random((H // 3, W // 3)).astype(np.float32) * 255).astype(np.uint8)
    return Image.fromarray(n, "L").resize((W, H), Image.BILINEAR)


def _fon_paper():
    base = Image.new("RGB", (W, H), PAPER)
    g = _grain(5).point(lambda v: -14 + v // 10)
    arr = np.asarray(base, np.int16) + np.asarray(g, np.int16)[..., None]
    im = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"), "RGB")
    v = Image.new("L", (W, H), 235)
    dv = ImageDraw.Draw(v)
    dv.ellipse([-W * 0.5, -H * 0.6, W * 1.5, H * 1.6], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGB", (W, H), PAPER2)
    return Image.composite(im, dark, v)


def _fon_graphite():
    base = Image.new("RGB", (W, H), GRAPHITE)
    g = _grain(7).point(lambda v: 6 + v // 16)
    arr = np.asarray(base, np.int16) + (np.asarray(g, np.int16)[..., None] - 10)
    im = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"), "RGB")
    v = Image.new("L", (W, H), 40)
    dv = ImageDraw.Draw(v)
    dv.ellipse([-W * 0.6, -H * 0.7, W * 1.6, H * 1.7], fill=95)
    v = v.filter(ImageFilter.GaussianBlur(260))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(im, dark, v)


def _kicker(img, text, channel, color=None, y=SAFE_Y + 26):
    if not text:
        return img
    col = color or _accent(channel)
    lay = text_layer(text.strip().upper(), 34, col, SAFE_X, y,
                      font_path=F_SANS, anchor="ls", track=0.14)
    return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")


def _finish(img, out):
    rgb = img.convert("RGB") if img.mode != "RGB" else img
    if out:
        rgb.save(out, quality=92)
        return out
    return rgb


# ---------------------------------------------------------------------------
# P1 · kalendar — КАЛЕНДАРНЫЙ ЛИСТ, ОБВЕДЕНО ОДНО ЧИСЛО
# ---------------------------------------------------------------------------
_MES = ("ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ", "ИЮЛЬ",
        "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ")


def kalendar(out=None, t=None, accent="", value="", kick="", channel="",
            watermark="", dur=0.0, sfx=None, **_):
    """P1. Лист календаря: месяц крупно сверху, сетка дней, одно число
    обведено акцентом канала. `--accent` — месяц/год («ОКТЯБРЬ 1962»),
    `--value` — число месяца, которое обвести (по умолчанию 17),
    `--kick` — подпись под листом (что случилось в этот день)."""
    tt = 1.0 if t is None else clamp(t / 0.8)
    acc = _accent(channel)
    img = _fon_paper()
    try:
        day = int(str(value).strip() or 17)
    except ValueError:
        day = 17
    day = max(1, min(31, day))
    title = (accent or "ОКТЯБРЬ").strip().upper()

    lay = text_layer(title, 92, INK, W / 2, 230, font_path=F_HEAD, anchor="ms", track=0.05)
    img = Image.alpha_composite(img.convert("RGBA"), lay)

    cols, rows = 7, 5
    gx0, gy0 = W / 2 - 520, 330
    cw, ch_ = 1040 / cols, 480 / rows
    d = ImageDraw.Draw(img)
    for i in range(1, 32):
        r, c = divmod(i - 1, cols)
        if r >= rows:
            break
        cx = gx0 + c * cw + cw / 2
        cy = gy0 + r * ch_ + ch_ / 2
        col = INK if i != day else (0, 0, 0, 0)
        f = _font(F_SANS, 46 * SS)
        if i == day:
            k = out_cubic(clamp(tt * 1.4))
            rad = (cw * 0.34) * k
            d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad],
                      outline=acc, width=max(2, int(6 * SS / SS)))
        d.text((cx, cy), str(i), font=f, fill=col if i != day else acc, anchor="mm")
    img = img.convert("RGB")
    if kick:
        lines = wrap(str(kick), 34, 1000, font_path=F_SERIF)
        y = gy0 + rows * ch_ + 60
        for ln in lines[:2]:
            lay = text_layer(ln, 34, INK, W / 2, y, font_path=F_SERIF, anchor="ms", track=0.0)
            img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
            y += 46
    return _finish(_kicker(img, "КАЛЕНДАРЬ", channel), out)


# ---------------------------------------------------------------------------
# P2 · kartoteka — КАРТОТЕКА, ОДНА КАРТОЧКА ВЫДВИНУТА
# ---------------------------------------------------------------------------
def kartoteka(out=None, t=None, accent="", kick="", channel="",
              watermark="", dur=0.0, sfx=None, **_):
    """P2. Ящик картотеки: ряд карточек-разделителей, одна (с именем из
    `--accent`) выдвинута вперёд и вверх. `--kick` — категория на ярлычке."""
    tt = 1.0 if t is None else clamp(t / 0.9)
    acc = _accent(channel)
    img = _fon_graphite()
    d = ImageDraw.Draw(img)
    n = 9
    box_w, box_h = 150, 640
    gx0 = W / 2 - n * box_w / 2
    gy0 = H - 120
    hero = n // 2
    k = out_cubic(tt)
    for i in range(n):
        x0 = gx0 + i * box_w
        lift = 120 * k if i == hero else 0
        y0 = gy0 - box_h - lift
        col = PAPER if i != hero else (235, 232, 222)
        d.rectangle([x0 + 6, y0, x0 + box_w - 6, gy0], fill=col, outline=(40, 40, 44))
        d.rectangle([x0 + 6, y0, x0 + box_w - 6, y0 + 34],
                    fill=acc if i == hero else (120, 112, 96))
    d.rectangle([0, gy0, W, gy0 + 120], fill=(10, 10, 12))
    img = img.convert("RGB")
    if accent:
        a = clamp((tt - 0.4) / 0.5)
        lay = text_layer(accent.strip().upper(), 58, WHITE, gx0 + hero * box_w + box_w / 2,
                         gy0 - box_h - 120 * k - 40, font_path=F_HEAD, anchor="ms",
                         track=0.02, a=a)
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    return _finish(_kicker(img, kick or "КАРТОТЕКА", channel), out)


# ---------------------------------------------------------------------------
# P3 · oscillo — ОСЦИЛЛОГРАФ, ЗАТУХАЮЩИЙ СИГНАЛ
# ---------------------------------------------------------------------------
def oscillo(out=None, t=None, accent="", value="", channel="", watermark="",
           dur=0.0, sfx=None, **_):
    """P3. Экран осциллографа: сетка, кривая сигнала с огибающей затухания
    бежит слева направо. `--accent` — подпись сигнала, `--value` — число
    (частота/амплитуда) мелким текстом у кривой."""
    tt = 1.0 if t is None else clamp(t / 2.2)
    acc = _accent(channel)
    img = _fon_graphite()
    d = ImageDraw.Draw(img)
    gx0, gx1 = SAFE_X + 40, W - SAFE_X - 40
    gy0, gy1 = 300, 760
    for i in range(0, 11):
        x = gx0 + (gx1 - gx0) * i / 10
        d.line([(x, gy0), (x, gy1)], fill=(40, 70, 48), width=1)
    for j in range(0, 7):
        y = gy0 + (gy1 - gy0) * j / 6
        d.line([(gx0, y), (gx1, y)], fill=(40, 70, 48), width=1)
    n = int(1200 * clamp(tt))
    pts = []
    for i in range(max(2, n)):
        frac = i / 1200
        x = gx0 + (gx1 - gx0) * frac
        env = math.exp(-3.2 * frac)
        yv = env * math.sin(frac * 46)
        y = (gy0 + gy1) / 2 - yv * (gy1 - gy0) * 0.42
        pts.append((x, y))
    if len(pts) >= 2:
        d.line(pts, fill=acc, width=5, joint="curve")
    img = img.convert("RGB")
    if accent:
        lay = text_layer(accent.strip().upper(), 42, WHITE, gx0, gy0 - 40,
                         font_path=F_SANS, anchor="ls", track=0.08)
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    if value:
        lay = text_layer(str(value), 30, (150, 220, 160), gx1, gy1 + 50,
                         font_path=F_SANS, anchor="rs", track=0.02)
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    return _finish(_kicker(img, "СИГНАЛ", channel), out)


# ---------------------------------------------------------------------------
# P8 · pismo — ПИСЬМО ОТ РУКИ
# ---------------------------------------------------------------------------
def pismo(out=None, t=None, text="", kick="", author="", channel="",
         watermark="", dur=0.0, sfx=None, **_):
    """P8. Лист бумаги, текст письма почерком (Caveat), подпись-автор внизу
    справа. `--text` — текст письма, `--author` — подпись (кому/от кого).

    Подпись НАРОЧНО не на `--accent`: та проверяется на дословное совпадение
    с `--text` (маркер цитаты), а подпись — не слово из письма (27.11)."""
    tt = 1.0 if t is None else clamp(t / 1.4)
    img = _fon_paper()
    lines = wrap(text or "", 54, W - 2 * SAFE_X - 160, font_path=F_HAND, track=0.0)
    y = 300
    shown = max(1, int(round(len(lines) * clamp(tt * 1.3))))
    for ln in lines[:shown]:
        lay = text_layer(ln, 64, INK, SAFE_X + 80, y, font_path=F_HAND,
                         anchor="ls", track=0.0)
        img = Image.alpha_composite(img.convert("RGBA"), lay)
        y += 70
    img = img.convert("RGB")
    if author:
        lay = text_layer(("— " + str(author)).strip(), 56, INK, W - SAFE_X - 60,
                         y + 50, font_path=F_HAND, anchor="rs", track=0.0)
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    return _finish(_kicker(img, kick or "ПИСЬМО", channel, color=INK), out)


# ---------------------------------------------------------------------------
# P11 · schyot_palochek — СЧЁТ ПАЛОЧКАМИ
# ---------------------------------------------------------------------------
def schyot_palochek(out=None, t=None, accent="", value="", channel="",
                    watermark="", dur=0.0, sfx=None, **_):
    """P11. Насечки-палочки, группами по пять (четыре вертикальных +
    диагональная), набегают слева направо. `--value` — число насечек
    (по умолчанию 23), `--accent` — подпись, что считаем."""
    tt = 1.0 if t is None else clamp(t / 1.8)
    acc = _accent(channel)
    img = _fon_paper()
    d = ImageDraw.Draw(img)
    try:
        n = max(1, min(60, int(str(value).strip() or 23)))
    except ValueError:
        n = 23
    shown = int(round(n * clamp(tt)))
    gw, gh = 10, 150
    gap = 26
    groups = (shown + 4) // 5 if shown else 0
    per_row = 10
    x0 = SAFE_X + 80
    y0 = 360
    for i in range(shown):
        g, pos = divmod(i, 5)
        row, gcol = divmod(g, per_row)
        bx = x0 + gcol * (5 * gap + 50)
        by = y0 + row * (gh + 60)
        if pos < 4:
            x = bx + pos * gap
            d.line([(x, by), (x, by + gh)], fill=INK, width=10)
        else:
            d.line([(bx - 6, by + gh + 10), (bx + 3 * gap + 6, by - 10)],
                   fill=acc, width=12)
    img = img.convert("RGB")
    lay = text_layer(str(n), 150, acc, W - SAFE_X - 220, H - 200,
                     font_path=F_HEAD, anchor="rs", track=0.0)
    img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    if accent:
        lay = text_layer(accent.strip().upper(), 36, INK, W - SAFE_X - 220, H - 130,
                         font_path=F_SANS, anchor="rs", track=0.04)
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    return _finish(_kicker(img, "СЧЁТ", channel, color=INK), out)


# ---------------------------------------------------------------------------
# P12 · liniya_zhizni — ЛИНИЯ ЖИЗНИ
# ---------------------------------------------------------------------------
def liniya_zhizni(out=None, t=None, accent="", value="", channel="",
                  watermark="", dur=0.0, sfx=None, **_):
    """P12. Горизонтальная линия от рождения, точка идёт по ней и
    останавливается на отметке. `--value` — доля пути 0-100 (по умолчанию
    70), `--accent` — подпись точки."""
    tt = 1.0 if t is None else clamp(t / 1.6)
    acc = _accent(channel)
    img = _fon_graphite()
    d = ImageDraw.Draw(img)
    x0, x1 = SAFE_X + 60, W - SAFE_X - 60
    y = H / 2
    d.line([(x0, y), (x1, y)], fill=(90, 90, 96), width=6)
    for frac, lbl in ((0.0, "НАЧАЛО"), (1.0, "СЕГОДНЯ")):
        x = x0 + (x1 - x0) * frac
        d.line([(x, y - 22), (x, y + 22)], fill=(170, 170, 176), width=4)
        lay = text_layer(lbl, 34, WHITE, x, y + 64, font_path=F_SANS,
                         anchor="ms" if frac else "ls", track=0.08)
        img = Image.alpha_composite(img.convert("RGBA"), lay)
    try:
        target = max(0.0, min(100.0, float(str(value).strip() or 70))) / 100.0
    except ValueError:
        target = 0.7
    frac_now = out_cubic(tt) * target
    xp = x0 + (x1 - x0) * frac_now
    d2 = ImageDraw.Draw(img)
    d2.line([(x0, y), (xp, y)], fill=acc, width=10)
    r = 20 + 4 * math.sin(tt * 10)
    d2.ellipse([xp - r, y - r, xp + r, y + r], fill=acc)
    d2.ellipse([xp - r * 0.4, y - r * 0.4, xp + r * 0.4, y + r * 0.4], fill=WHITE)
    img = img.convert("RGB")
    if accent:
        lay = text_layer(accent.strip().upper(), 52, WHITE, xp, y - 70,
                         font_path=F_SANS, anchor="ms", track=0.04)
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    return _finish(_kicker(img, "ЛИНИЯ ЖИЗНИ", channel), out)


# ---------------------------------------------------------------------------
# P14 · pereskaz — ПЕРЕСКАЗ (блокнот, пункты)
# ---------------------------------------------------------------------------
def pereskaz(out=None, t=None, items=None, channel="", watermark="",
            dur=0.0, sfx=None, **_):
    """P14. Блокнотный лист, пункты пересказа появляются по одному сверху
    вниз. `--item` — один пункт (ключ повторяется 2-4 раза)."""
    tt = 1.0 if t is None else clamp(t / 1.6)
    acc = _accent(channel)
    img = _fon_paper()
    d = ImageDraw.Draw(img)
    for y in range(280, H - 160, 64):
        d.line([(SAFE_X + 40, y), (W - SAFE_X - 40, y)], fill=(170, 160, 140), width=2)
    d.line([(SAFE_X + 110, 220), (SAFE_X + 110, H - 160)], fill=acc, width=4)
    pts = [str(p).strip() for p in (items or []) if str(p).strip()]
    shown = max(1, int(round(len(pts) * clamp(tt * 1.3)))) if pts else 0
    img = img.convert("RGB")
    y = 310
    for i, p in enumerate(pts[:shown]):
        # Чёрная плашка, не акцент канала: яркостный контраст с бумагой
        # важен для гейта читаемости (`chitaemost.py`) — у части каналов
        # акцент слишком светлый (ПЛАНЕТА: L~132 против бумаги L~201, диф
        # меньше порога 110), а тёмно-серый всегда проходит с запасом.
        ImageDraw.Draw(img).ellipse([SAFE_X + 130, y - 56, SAFE_X + 186, y - 0],
                                    fill=(28, 26, 24))
        num_lay = text_layer(str(i + 1), 34, WHITE, SAFE_X + 158, y - 26,
                             font_path=F_SANS, anchor="mm", track=0.0)
        img = Image.alpha_composite(img.convert("RGBA"), num_lay).convert("RGB")
        for ln in wrap(p, 46, W - SAFE_X - 310, font_path=F_SERIF)[:2]:
            lay = text_layer(ln, 58, INK, SAFE_X + 200, y, font_path=F_SERIF,
                             anchor="ls", track=0.0)
            img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
            y += 58
        y += 30
    return _finish(_kicker(img, "ПЕРЕСКАЗ", channel, color=INK), out)


# ---------------------------------------------------------------------------
# P16 · otschet_dney — ОТСЧЁТ ДНЕЙ (пустые графы на фоне)
# ---------------------------------------------------------------------------
def otschet_dney(out=None, t=None, accent="", value="", channel="", watermark="",
                 dur=0.0, sfx=None, **_):
    """P16. Большое число дней бежит вверх до значения на фоне пустой
    сетки графика (данных ещё нет — только оси). `--value` — итоговое
    число дней, `--accent` — подпись."""
    tt = 1.0 if t is None else clamp(t / 1.6)
    acc = _accent(channel)
    img = _fon_graphite()
    d = ImageDraw.Draw(img)
    gx0, gx1 = SAFE_X + 40, W - SAFE_X - 40
    gy0, gy1 = 760, 920
    for i in range(0, 9):
        x = gx0 + (gx1 - gx0) * i / 8
        d.line([(x, gy0), (x, gy1)], fill=(46, 46, 52), width=1)
    d.line([(gx0, gy1), (gx1, gy1)], fill=(80, 80, 86), width=2)
    try:
        target = max(0, int(str(value).strip() or 100))
    except ValueError:
        target = 100
    shown = int(round(target * out_cubic(tt)))
    img = img.convert("RGB")
    lay = text_layer(str(shown), 300, acc, W / 2, 560, font_path=F_HEAD,
                     anchor="ms", track=0.0)
    img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    lay = text_layer((accent or "ДНЕЙ").strip().upper(), 44, WHITE, W / 2, 630,
                     font_path=F_SANS, anchor="ms", track=0.12)
    img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    return _finish(_kicker(img, "ОТСЧЁТ", channel), out)


# ---------------------------------------------------------------------------
# P17 · shtamp_lestnica — ШТАМП + ЛЕСТНИЦА ПРОМАХОВ
# ---------------------------------------------------------------------------
def shtamp_lestnica(out=None, t=None, kick="", accent="", items=None,
                    channel="", watermark="", dur=0.0, sfx=None, **_):
    """P17. Бумага, в углу красный круглый штамп со словом (`--accent`,
    по умолчанию «ОТКАЗ»), слева лестницей вниз — список промахов
    (`--item`, 2-4 штуки). `--kick` — заголовок листа."""
    tt = 1.0 if t is None else clamp(t / 1.5)
    acc_c = _accent(channel)
    img = _fon_paper()
    if kick:
        lay = text_layer(kick.strip().upper(), 44, INK, SAFE_X + 40, 260,
                         font_path=F_HEAD, anchor="ls", track=0.03)
        img = Image.alpha_composite(img.convert("RGBA"), lay)
    img = img.convert("RGB")
    pts = [str(p).strip() for p in (items or []) if str(p).strip()]
    y = 340
    xoff = 0
    shown = max(1, int(round(len(pts) * clamp(tt * 1.3)))) if pts else 0
    for p in pts[:shown]:
        lay = text_layer("— " + p, 46, (110, 26, 24), SAFE_X + 60 + xoff, y,
                         font_path=F_SERIF, anchor="ls", track=0.0)
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
        y += 86
        xoff += 50
    k = out_cubic(clamp((tt - 0.5) / 0.5))
    if k > 0:
        cx, cy, r = W - SAFE_X - 240, 320, int(150 * k)
        stamp_layer = layer()
        sd = ImageDraw.Draw(stamp_layer)
        sd.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS],
                   outline=acc_c + (235,), width=16 * SS)
        # r<24 на старте анимации даёт x1<x0 — `ValueError: x1 must be
        # greater than or equal to x0` (живой случай, упало на раннере
        # 27.11, 0 клипов из 1 при честном "успехе" прогона). Локальный тест
        # по горстке значений t это не поймал — render_anim гонит 30
        # кадров в секунду и проходит через r=1..23 на реальном прогоне.
        r2 = max(1, r - 24)
        sd.ellipse([(cx - r2) * SS, (cy - r2) * SS,
                    (cx + r2) * SS, (cy + r2) * SS],
                   outline=acc_c + (235,), width=4 * SS)
        word = (accent or "ОТКАЗ").strip().upper()
        f = _font(F_SANS, int(52 * k) * SS or 1)
        sd2 = stamp_layer
        tracked(ImageDraw.Draw(sd2), cx * SS, cy * SS, word, f,
                acc_c + (235,), 0.1, anchor="ms")
        rot = stamp_layer.rotate(-14, resample=Image.BICUBIC)
        img = Image.alpha_composite(img.convert("RGBA"), done(rot)).convert("RGB")
    return _finish(_kicker(img, "ШТАМП", channel, color=INK), out)


# ---------------------------------------------------------------------------
# P18 · sortirovka — СОРТИРОВКА ПО ДВУМ СТОПКАМ
# ---------------------------------------------------------------------------
def sortirovka(out=None, t=None, left="", right="", items=None, channel="",
              watermark="", dur=0.0, sfx=None, **_):
    """P18. Два ярлыка-стопки слева/справа (`--left`/`--right`), карточки
    из `--item` (ключ повторяется) разлетаются по стопкам одна за другой."""
    tt = 1.0 if t is None else clamp(t / 1.8)
    acc_c = _accent(channel)
    img = _fon_graphite()
    d = ImageDraw.Draw(img)
    lx, rx, y0 = W * 0.28, W * 0.72, 760
    label_y = y0 - 260              # фикс, выше любого реалистичного стека
    for x, lbl, col in ((lx, left or "ОДНО", GREY), (rx, right or "ДРУГОЕ", acc_c)):
        d.rectangle([x - 150, y0, x + 150, y0 + 14], fill=col)
        lay = text_layer(lbl.strip().upper(), 36, WHITE, x, label_y,
                         font_path=F_SANS, anchor="ms", track=0.08)
        img = Image.alpha_composite(img.convert("RGBA"), lay)
    img = img.convert("RGB")
    pts = [str(p).strip() for p in (items or []) if str(p).strip()][:8]
    shown = max(1, int(round(len(pts) * clamp(tt)))) if pts else 0
    for i, p in enumerate(pts[:shown]):
        side = lx if i % 2 == 0 else rx
        stack_n = i // 2
        cy = y0 - 30 - stack_n * 50
        d2 = ImageDraw.Draw(img)
        d2.rectangle([side - 130, cy - 40, side + 130, cy], fill=(224, 221, 212),
                     outline=(40, 40, 44))
        lay = text_layer(p[:18], 26, INK, side, cy - 20, font_path=F_SANS,
                         anchor="mm", track=0.0)
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    return _finish(_kicker(img, "СОРТИРОВКА", channel), out)


# ---------------------------------------------------------------------------
# P19 · kompas — КОМПАС
# ---------------------------------------------------------------------------
_СТОРОНЫ = {"С": 0, "В": 90, "Ю": 180, "З": 270}


def kompas(out=None, t=None, accent="", value="", channel="", watermark="",
          dur=0.0, sfx=None, **_):
    """P19. Циферблат компаса, стрелка поворачивается и останавливается на
    направлении. `--value` — угол 0-360 либо буква стороны (С/В/Ю/З),
    `--accent` — подпись под циферблатом (куда указывает и почему)."""
    tt = 1.0 if t is None else clamp(t / 1.6)
    acc = _accent(channel)
    img = _fon_graphite()
    d = ImageDraw.Draw(img)
    cx, cy, r = W / 2, 520, 320
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(130, 130, 136), width=6)
    d.ellipse([cx - r + 24, cy - r + 24, cx + r - 24, cy + r - 24],
              outline=(80, 80, 86), width=2)
    for lbl, ang in _СТОРОНЫ.items():
        rad = math.radians(ang - 90)
        x = cx + (r - 54) * math.cos(rad)
        y = cy + (r - 54) * math.sin(rad)
        lay = text_layer(lbl, 36, GREY, x, y + 14, font_path=F_SANS,
                         anchor="mm", track=0.0)
        img = Image.alpha_composite(img.convert("RGBA"), lay)
    img = img.convert("RGB")
    v = str(value).strip().upper()
    target = _СТОРОНЫ.get(v)
    if target is None:
        try:
            target = float(v or 90) % 360
        except ValueError:
            target = 90
    ang_now = out_cubic(tt) * target - 90
    rad = math.radians(ang_now)
    d2 = ImageDraw.Draw(img)
    tip = (cx + (r - 60) * math.cos(rad), cy + (r - 60) * math.sin(rad))
    tail = (cx - (r - 220) * math.cos(rad), cy - (r - 220) * math.sin(rad))
    d2.line([tail, tip], fill=acc, width=10)
    d2.polygon([tip, (tip[0] + 18 * math.cos(rad + 2.6), tip[1] + 18 * math.sin(rad + 2.6)),
                (tip[0] + 18 * math.cos(rad - 2.6), tip[1] + 18 * math.sin(rad - 2.6))],
               fill=acc)
    d2.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(220, 220, 224))
    if accent:
        lay = text_layer(accent.strip().upper(), 38, WHITE, cx, cy + r + 70,
                         font_path=F_SANS, anchor="ms", track=0.05)
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    return _finish(_kicker(img, "КОМПАС", channel), out)


# ---------------------------------------------------------------------------
# P20 · chertezh — ЧЕРТЁЖ (синька)
# ---------------------------------------------------------------------------
def chertezh(out=None, t=None, accent="", items=None, channel="", watermark="",
            dur=0.0, sfx=None, **_):
    """P20. Синька чертежа: сетка, контур объекта из `--accent` (название
    над рамкой) с выносками-подписями из `--item` (ключ повторяется,
    2-3 шт.), проступают по очереди."""
    tt = 1.0 if t is None else clamp(t / 1.8)
    BLUE = (16, 36, 72)
    BLUE2 = (40, 70, 120)
    img = Image.new("RGB", (W, H), BLUE)
    d = ImageDraw.Draw(img)
    step = 54
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=BLUE2, width=1)
    for y in range(0, H, step):
        d.line([(0, y), (W, y)], fill=BLUE2, width=1)
    k = out_cubic(tt)
    bx0, by0, bx1, by1 = W / 2 - 420, 300, W / 2 + 420, 820
    rect_w = (bx1 - bx0) * clamp(k * 2)
    d.rectangle([bx0, by0, bx0 + rect_w, by1], outline=WHITE, width=4)
    if k > 0.5:
        d.line([(bx0, by0), (bx1, by1)], fill=WHITE, width=2)
        d.line([(bx0, by1), (bx1, by0)], fill=WHITE, width=2)
    img_rgba = img.convert("RGBA")
    if accent:
        lay = text_layer(accent.strip().upper(), 46, WHITE, W / 2, by0 - 40,
                         font_path=F_HEAD, anchor="ms", track=0.05)
        img_rgba = Image.alpha_composite(img_rgba, lay)
    img = img_rgba.convert("RGB")
    pts = [str(p).strip() for p in (items or []) if str(p).strip()]
    shown = max(0, int(round(len(pts) * clamp((tt - 0.4) / 0.6)))) if pts else 0
    for i, p in enumerate(pts[:shown]):
        y = by0 + 60 + i * 70
        d2 = ImageDraw.Draw(img)
        d2.line([(bx1 + 10, y), (bx1 + 70, y)], fill=WHITE, width=2)
        lay = text_layer(p, 28, WHITE, bx1 + 80, y + 10, font_path=F_SANS,
                         anchor="ls", track=0.02)
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    return _finish(_kicker(img, "ЧЕРТЁЖ", channel, color=(170, 200, 255)), out)
