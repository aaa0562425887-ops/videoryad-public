#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Линтер эффекта — пятый приём, забранный у pixelfx (их tools/check.mjs).

Ловит ровно то, на чём спотыкаемся мы сами, и ловит ДО круга правок:

  вылез за кадр      — эффект упирается в край, значит обрезан;
  пересвет           — белое пятно съело кадр (на этом я обжёгся дважды за час);
  шов на петле       — последний кадр не сходится с первым;
  мёртвый кадр       — между соседними кадрами ничего не изменилось;
  незасеянный рандом — random.random() без seed: кадр 40 завтра будет другим;
  медленный кадр     — дороже порога, облако будет считать слишком долго.

  python3 lint_fx.py 01 02 05        # проверить сцены
  python3 lint_fx.py --all
"""
import os
import re
import sys
import time

import numpy as np

import pxscenes as SC

EDGE = 6          # полоса у края, px
WHITE = 250       # что считаем выжженным
SLOW = 1.2        # с на кадр
SAMPLES = 14      # сколько кадров смотрим


def _arr(im):
    return np.asarray(im.convert("RGB"), np.float32)


def check(name):
    fn, secs = SC.SCENES[name]
    n = int(SC.FPS * secs)
    idx = sorted(set([0] + [int(i * (n - 1) / (SAMPLES - 1)) for i in range(SAMPLES)] + [n - 1]))
    bad, prev, first, last, slowest = [], None, None, None, 0.0
    flashy = 0          # сколько проверенных кадров несут крупное белое пятно
    # сцены с частицами копят состояние — идём подряд, замеряя только нужные кадры
    for i in range(n):
        t0 = time.time()
        im = fn(i / (n - 1))
        dt = time.time() - t0
        slowest = max(slowest, dt)
        if i not in idx:
            continue
        a = _arr(im)
        if i == 0:
            first = a
        last = a
        hot = ((a >= WHITE).all(axis=2)).mean()
        if hot > 0.004:
            flashy += 1
        if hot > 0.16:
            bad.append("кадр %d: пересвет — %.0f%% кадра выжжено в белый" % (i, hot * 100))
        for nm, strip in (("слева", a[:, :EDGE]), ("справа", a[:, -EDGE:]),
                          ("сверху", a[:EDGE, :]), ("снизу", a[-EDGE:, :])):
            # сравниваем с фоном того же кадра по центру: яркая кромка = эффект обрезан
            if strip.max() > 215 and strip.mean() > a.mean() * 1.25:
                bad.append("кадр %d: эффект упирается в край (%s)" % (i, nm))
                break
        if prev is not None and i > 0 and np.abs(a - prev).mean() < 0.12:
            bad.append("кадр %d: мёртвый кадр — от предыдущего не отличается" % i)
        prev = a
    # вспышка-герой обязана быть РЕДКОЙ: если белое пятно висит на трети кадров,
    # значит она зажглась раньше события и горит всю сцену (живая мина 07.11)
    if flashy > len(idx) * 0.34:
        bad.append("вспышка висит на %d кадрах из %d — похоже, горит до события" % (flashy, len(idx)))
    if getattr(SC.SCENES[name][0], "loop", False) or name in getattr(SC, "LOOPS", ()):
        d = np.abs(first - last).mean()
        if d > 2.0:
            bad.append("шов на петле: первый и последний кадр расходятся на %.1f" % d)
    if slowest > SLOW:
        bad.append("медленный кадр: %.2f с при пороге %.2f" % (slowest, SLOW))
    return bad


def unseeded():
    out = []
    here = os.path.dirname(os.path.abspath(__file__))
    for f in sorted(os.listdir(here)):
        if not f.endswith(".py") or f == os.path.basename(__file__):
            continue
        src = open(os.path.join(here, f), encoding="utf-8").read()
        for m in re.finditer(r"np\.random\.default_rng\(\s*\)|(?<![\w.])random\.(random|uniform|randint|choice)\(", src):
            line = src[:m.start()].count("\n") + 1
            out.append("%s:%d незасеянный рандом — кадр перестанет повторяться" % (f, line))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    names = sorted(SC.SCENES) if ("--all" in sys.argv or not args) else args
    bad = unseeded()
    for nm in names:
        for b in check(nm):
            bad.append("сцена %s: %s" % (nm, b))
    if bad:
        print("БРАК (%d):" % len(bad))
        for b in bad:
            print(" •", b)
        sys.exit(1)
    print("чисто: %s" % ", ".join(names))


if __name__ == "__main__":
    main()
