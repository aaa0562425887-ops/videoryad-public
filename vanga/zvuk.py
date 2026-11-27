#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Звуковой слой фильма «Верица»: одна тема с вариациями по актам и звук на движении
графики. Кладётся ПОВЕРХ собранного файла (видео копируется, пересводится
только звук).

    python3 zvuk.py <film.mp4> <out.mp4>

Музыка — ЕГО четыре трека из D:\\YouTube\\МЕДИОТЕКА (zvuk/music/*.mp3), ~20% громкости
(−14 дБ), раскладка по актам в AKTY. Звуки — банк ~/.claude/audio-gen/sfx, −20 дБ.
Отрезок фильма: KINO_SCENES="01,02,03,04" (как у sborka.py).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import core as C  # noqa: E402

FF = C.ffmpeg()
MUS = os.path.join(HERE, "zvuk", "music")
SFX = os.path.join(HERE, "zvuk", "sfx")

# «Верица»: один трек на хук — «Missing Persons» (Jeremy Blake, его медиатека), тихо
AKTY = [("01", "missing"), ("09", "final"), ("21", "missing"), ("27", "topass"), ("37", "missing"), ("40", "incoming"), ("54", "final"),
        ("57", "topass"), ("66", "tishina"), ("67", "missing"),
        ("R2", "topass"), ("82", "incoming"), ("96", "topass"), ("111", "missing"), ("116", "tishina"), ("117", "missing")]   # Дрезден — «To Pass Time» (Godmode); «tishina» — файла нет, музыка уходит ([ПАУЗА 3 с. Тишина] блока 4)
MUSIC_DB = -22.0   # как у Киссинджера после п.62 («музыка еле слышно»)
MEAN = {"missing": -12.4, "final": -12.9, "topass": -13.9, "incoming": -17.2}
SFX_DB = -20.0

# события звука: сцена → [(секунда сцены, звук)] — секунды сцены, с учётом вставки
EVENTS = {
    "01": [(0.55, "typewriter"), (2.55, "whoosh"), (5.0, "click"), (7.85, "tick")],
    "02": [(0.05, "rise"), (1.2, "click"), (1.3, "typewriter")],
    "03": [(1.8, "tick"), (2.0, "tick"), (2.2, "tick"), (2.4, "tick"), (2.65, "thud"), (3.45, "glitch2"), (4.3, "impact")],
    "04": [(1.15, "swoosh"), (2.9, "scribble"), (3.4, "typewriter")],
    "05": [(0.3, "click"), (0.65, "click"), (3.75, "impact")],
    "06": [(5.45, "pop"), (7.9, "thud"), (9.55, "click"), (11.0, "tick"), (11.8, "tick"), (12.6, "tick"),
           (13.65, "shutter"), (14.4, "rise"), (15.7, "click")],
    "07": [(1.35, "thud"), (1.65, "thud"), (1.95, "thud"), (2.6, "scribble"), (3.5, "swoosh"), (4.75, "swoosh"), (6.05, "swoosh"),
           (7.4, "whoosh"), (7.55, "tick"), (8.95, "click"), (9.85, "scribble"), (11.0, "rise"), (18.3, "impact")],
    "08": [(2.0, "impact"), (2.5, "swoosh")],
    "09": [(4.0, "click"), (9.2, "thud"), (12.35, "swoosh"), (14.75, "swoosh")],
    "10": [(0.3, "thud"), (5.15, "impact"), (6.8, "click")],
    "11": [(0.2, "click"), (1.6, "click")],
    "12": [(0.25, "thud"), (1.1, "scribble"), (2.7, "swoosh"), (5.2, "whoosh")],
    "13": [(0.2, "door"), (2.1, "rise"), (5.05, "reveal")],
    "14": [(0.2, "click"), (1.2, "scribble"), (3.25, "click"), (5.8, "tick"), (6.6, "tick"), (7.85, "impact")],
    "15": [(0.35, "thud"), (1.2, "scribble"), (2.65, "whoosh")],
    "16": [(3.25, "swoosh"), (5.25, "thud"), (8.15, "click")],
    "17": [(0.3, "click"), (4.5, "impact"), (5.65, "whoosh"), (8.0, "tick"), (10.15, "swoosh"), (11.9, "thud")],
    "18": [(0.1, "click"), (1.25, "tick"), (5.7, "swoosh"), (6.3, "impact")],
    "19": [(1.7, "rise"), (3.45, "whoosh"), (6.5, "whoosh"), (8.9, "click"), (10.05, "click")],
    "20": [(0.1, "sparkle"), (2.2, "pop"), (4.1, "thud"), (5.95, "impact")],
    "21": [(0.05, "impact"), (1.25, "tick"), (3.7, "pop"), (4.65, "swoosh"), (6.4, "click"), (8.1, "whoosh"), (10.1, "scribble")],
    "22": [(0.4, "tick"), (1.4, "tick"), (2.5, "tick")],
    "23": [(1.8, "tick"), (3.95, "thud"), (5.35, "glitch2"), (7.7, "rise"), (10.2, "tick"), (10.5, "tick"), (10.8, "tick"), (14.0, "impact")],
    "24": [(0.2, "swoosh"), (0.6, "swoosh"), (1.0, "swoosh"), (3.1, "impact")],
    "25": [(1.7, "click"), (3.35, "rise"), (6.5, "thud")],
    "26": [(3.2, "whoosh"), (3.4, "tick"), (3.8, "tick"), (4.2, "tick"), (4.6, "tick"), (5.0, "tick"), (5.7, "pop")],
    # третий кусок (scenes3.py)
    "27": [(0.3, "rise"), (1.2, "scribble"), (2.2, "impact"), (3.1, "click"), (4.5, "thud"), (4.7, "shutter")],
    "28": [(0.2, "typewriter"), (3.45, "swoosh"), (3.7, "impact")],
    "29": [(0.1, "shutter"), (2.3, "impact"), (3.05, "click"), (3.25, "click"), (3.45, "click"), (3.65, "click"), (3.85, "click"), (4.05, "click"), (4.2, "thud"), (6.2, "shutter")],
    "30": [(0.2, "door"), (0.9, "scribble"), (2.75, "swoosh"), (3.1, "thud"), (4.4, "tick")],
    "31": [(0.3, "typewriter"), (3.0, "typewriter"), (6.75, "click"), (7.2, "typewriter"), (9.95, "scribble"), (11.5, "scribble"), (11.9, "impact")],
    "32": [(2.2, "tick"), (5.4, "buzz"), (6.65, "rise")],
    "33": [(0.3, "click"), (1.0, "thud"), (4.2, "click"), (6.65, "click"), (6.8, "impact"), (9.2, "swoosh"), (10.1, "swoosh"), (11.35, "door"), (12.0, "pop"), (12.5, "pop"), (12.8, "thud")],
    "34": [(0.2, "clock"), (1.1, "click"), (3.6, "whoosh")],
    "35": [(0.1, "click"), (24.3, "thud"), (25.6, "impact"), (27.3, "thud"), (28.4, "door")],
    "36": [(1.3, "rise"), (1.5, "tick"), (2.3, "tick"), (3.1, "tick"), (3.4, "click"), (5.85, "impact")],
    "37": [(0.3, "click"), (4.85, "thud"), (5.3, "scribble"), (5.9, "pop"), (6.3, "swoosh")],
    "38": [(0.7, "rise"), (1.75, "tick"), (3.5, "tick"), (5.0, "tick"), (5.95, "impact"), (7.0, "whoosh")],
    "39": [(0.3, "click"), (1.6, "tick"), (2.45, "scribble"), (3.4, "thud")],
    # четвёртый кусок (scenes4.py)
    "40": [(0.05, "impact"), (1.2, "click"), (1.4, "typewriter"), (3.3, "tick")],
    "41": [(0.2, "click"), (1.75, "thud"), (2.0, "thud"), (3.0, "tick"), (4.0, "tick"), (4.8, "tick"), (5.6, "tick"), (6.4, "tick"), (7.2, "tick")],
    "42": [(0.3, "swoosh"), (1.4, "swoosh"), (1.55, "swoosh"), (1.7, "swoosh"), (1.85, "swoosh"), (2.0, "swoosh"), (2.15, "swoosh"), (2.3, "swoosh"), (2.45, "swoosh"), (2.6, "swoosh"), (2.9, "impact")],
    "43": [(0.1, "scribble"), (0.9, "thud"), (2.1, "click"), (3.6, "shutter"), (4.4, "tick")],
    "44": [(0.2, "click"), (1.0, "scribble"), (2.7, "thud"), (3.5, "typewriter")],
    "45": [(0.2, "click"), (3.0, "rise"), (4.4, "impact"), (4.75, "thud"), (6.2, "thud"), (7.65, "swoosh"), (9.4, "buzz"), (11.3, "click"), (12.5, "tick"), (13.3, "tick")],
    "46": [(0.2, "sparkle"), (1.0, "pop"), (1.5, "pop"), (2.0, "pop"), (2.6, "rise"), (3.5, "click")],
    "47": [(1.5, "scribble"), (2.7, "thud"), (3.0, "tick"), (4.4, "sparkle"), (5.9, "click"), (6.2, "scribble"), (7.3, "click"), (8.9, "tick")],
    "48": [(0.1, "rise"), (0.7, "impact"), (3.2, "thud"), (4.6, "click"), (5.5, "thud")],
    "49": [(0.2, "click"), (1.85, "rise"), (3.0, "tick"), (3.3, "tick"), (3.6, "tick"), (3.9, "impact")],
    "50": [(1.15, "impact"), (2.1, "click"), (3.9, "typewriter"), (6.3, "thud"), (6.8, "swoosh"), (7.3, "swoosh"), (7.8, "swoosh"), (8.3, "swoosh"), (9.5, "impact"), (11.2, "click"), (13.0, "thud"), (14.6, "rise")],
    "51": [(0.2, "swoosh"), (0.6, "swoosh"), (2.2, "pop"), (4.3, "sparkle"), (6.5, "thud"), (7.0, "thud"), (7.4, "thud"), (8.9, "click"), (12.0, "tick"), (12.6, "tick"), (13.2, "tick")],
    "52": [(0.2, "click"), (1.1, "scribble"), (1.9, "thud")],
    "53": [(1.0, "tick"), (1.15, "impact")],
    "54": [(1.5, "click"), (3.2, "scribble"), (4.7, "rise"), (6.6, "tick"), (7.4, "tick"), (7.9, "impact")],
    "55": [(0.1, "rise"), (0.6, "tick"), (1.2, "tick"), (1.8, "impact"), (2.2, "click"), (4.2, "swoosh"), (6.2, "thud"), (7.5, "click"), (8.7, "thud"), (9.7, "pop")],
    "56": [(0.2, "thud"), (1.6, "click"), (2.6, "scribble"), (3.4, "tick")],
    # пятый кусок (scenes5.py)
    "57": [(0.05, "impact"), (0.5, "click"), (1.2, "shutter"), (1.4, "typewriter")],
    "58": [(0.1, "click"), (0.3, "tick"), (1.3, "tick"), (2.3, "tick"), (2.9, "rise"), (3.3, "tick"), (3.6, "tick"), (3.9, "tick"), (4.2, "impact")],
    "59": [(0.1, "click"), (2.3, "tick"), (9.0, "thud")],
    "60": [(0.1, "glitch"), (0.4, "whoosh"), (0.8, "tick"), (1.0, "tick"), (1.2, "tick"), (1.4, "tick"), (1.55, "thud"), (1.9, "click")],
    "61": [(0.2, "typewriter"), (0.6, "scribble"), (2.4, "swoosh"), (2.6, "click")],
    "62": [(0.2, "rise"), (0.6, "typewriter"), (1.6, "typewriter"), (2.7, "impact")],
    "63": [(0.3, "click"), (1.1, "swoosh"), (2.1, "impact"), (3.1, "scribble"), (3.4, "tick")],
    "64": [(0.2, "click")],
    "65": [(0.1, "scribble"), (0.3, "typewriter")],
    "66": [(0.2, "click"), (0.5, "swoosh"), (1.6, "click"), (2.0, "tick"), (2.3, "tick"), (2.6, "tick"), (2.9, "impact"), (3.2, "thud"), (5.3, "rise")],
    "67": [(0.2, "click"), (1.2, "swoosh"), (1.5, "rise"), (3.0, "scribble"), (3.3, "thud")],
    "68": [(0.15, "thud"), (0.4, "swoosh"), (0.6, "swoosh"), (0.8, "swoosh"), (1.9, "whoosh"), (2.75, "rise"), (3.3, "impact")],
    "69": [(0.2, "thud"), (0.7, "rise"), (1.4, "impact"), (1.8, "click")],
    "70": [(0.15, "scribble"), (0.25, "impact")],
    "70b": [(0.08, "thud"), (0.3, "scribble")],
    "71": [(0.2, "swoosh"), (0.45, "swoosh"), (0.7, "swoosh"), (0.95, "swoosh"), (1.2, "swoosh"), (1.7, "thud"), (2.2, "click")],
    "72": [(0.2, "click"), (0.6, "whoosh"), (1.0, "whoosh"), (1.4, "whoosh"), (2.1, "rise"), (2.5, "tick"), (2.8, "tick"), (3.1, "tick"), (3.4, "impact")],
    "73": [(0.2, "typewriter"), (0.5, "thud"), (2.1, "typewriter"), (2.3, "thud")],
    "74": [(0.2, "click"), (1.1, "scribble"), (2.0, "scribble"), (2.6, "scribble"), (3.0, "thud")],
    "75": [(0.1, "swoosh"), (0.45, "swoosh"), (0.8, "swoosh"), (1.15, "swoosh"), (1.5, "swoosh"), (2.2, "impact"), (2.6, "tick")],
    "76": [(0.3, "door"), (1.6, "typewriter"), (3.3, "typewriter"), (5.2, "typewriter"), (7.1, "scribble"), (7.4, "thud")],
    "77": [(0.2, "typewriter"), (1.0, "impact")],
    "78": [(0.1, "rise"), (0.6, "click"), (1.2, "tick"), (1.6, "tick"), (2.1, "tick"), (2.7, "thud"), (3.3, "buzz")],
    "79": [(0.3, "thud"), (0.6, "click"), (1.2, "scribble"), (1.7, "pop"), (2.0, "thud")],
    "80": [(0.2, "click"), (0.5, "rise"), (2.5, "swoosh"), (2.7, "scribble"), (4.5, "click"), (5.0, "whoosh"), (6.5, "thud"), (7.4, "pop"), (8.2, "pop"), (9.0, "pop")],
    "81": [(0.1, "typewriter"), (0.4, "typewriter"), (0.7, "typewriter"), (1.0, "typewriter"), (1.4, "buzz"), (1.5, "impact")],
    # седьмой кусок (scenes7.py)
    "R1": [(0.1, "click"), (2.3, "tick")], "R2": [(0.1, "click"), (2.3, "tick")], "R3": [(0.1, "click"), (2.3, "tick")],
    "R6": [(0.1, "click"), (2.3, "tick"), (8.7, "click"), (10.5, "tick")],
    "K6": [(0.05, "thud")], "K2": [(0.05, "thud")], "K3": [(0.05, "thud")], "K1": [(0.05, "thud")],
    "82": [(0.05, "impact"), (0.5, "click"), (1.2, "swoosh"), (1.5, "thud")],
    "83": [(0.2, "click"), (0.5, "thud"), (2.6, "tick"), (3.4, "tick"), (4.8, "impact"), (4.95, "thud")],
    "84": [(0.2, "click"), (0.5, "thud"), (1.7, "scribble"), (3.35, "impact"), (3.5, "thud")],
    "85": [(0.2, "click"), (0.5, "thud"), (1.5, "impact"), (1.65, "thud"), (2.4, "impact"), (2.55, "thud")],
    "86": [(0.3, "rise"), (1.6, "impact"), (2.4, "click"), (3.2, "typewriter")],
    "87": [(0.2, "thud"), (0.3, "tick"), (2.2, "thud"), (2.3, "tick"), (4.4, "thud"), (4.5, "tick"), (6.4, "thud"), (6.5, "tick"), (8.2, "thud"), (8.3, "tick")],
    "88": [(0.2, "click"), (0.6, "rise"), (1.3, "pop"), (2.5, "thud"), (2.6, "tick")],
    "89": [(0.05, "impact"), (0.2, "impact"), (0.35, "impact"), (0.5, "impact"), (0.65, "impact"), (0.8, "impact"), (1.0, "thud"), (1.2, "buzz")],
    "90": [(0.3, "click"), (1.0, "door"), (2.1, "rise"), (2.6, "whoosh")],
    "91": [(0.2, "swoosh"), (0.5, "swoosh"), (0.8, "swoosh"), (1.1, "swoosh"), (1.4, "swoosh"), (1.9, "scribble"), (2.3, "scribble"), (2.7, "thud")],
    "92": [(0.3, "pop"), (0.9, "pop"), (1.5, "pop"), (2.0, "sparkle")],
    "93": [(0.2, "rise"), (0.6, "tick"), (0.9, "tick"), (1.2, "tick"), (1.6, "click"), (2.4, "impact")],
    "94": [(0.3, "clock"), (1.0, "clock2"), (1.5, "clock"), (2.4, "thud")],
    "95": [(0.2, "scribble"), (0.8, "scribble"), (1.5, "tick"), (2.2, "tick"), (2.9, "impact")],
    "96": [(0.5, "door"), (2.0, "click")],
    "97": [(0.2, "rise"), (0.6, "thud"), (1.8, "scribble"), (3.5, "click"), (4.6, "whoosh")],
    "98": [(0.2, "thud"), (0.5, "pop"), (0.9, "impact")],
    "99": [(0.3, "door"), (0.9, "typewriter"), (2.4, "tick"), (3.3, "tick")],
    "100": [(0.2, "cash"), (0.7, "typewriter")],
    "101": [(0.2, "typewriter"), (1.6, "scribble")],
    "102": [(0.2, "typewriter"), (0.8, "swoosh"), (1.1, "swoosh")],
    "103": [(0.3, "thud"), (0.6, "thud"), (1.4, "scribble"), (2.9, "rise"), (3.8, "impact")],
    "104": [(0.3, "click"), (1.2, "buzz"), (1.4, "thud")],
    "105": [(0.4, "tick"), (1.1, "tick"), (1.8, "tick"), (2.1, "rise"), (2.8, "impact")],
    "106": [(0.2, "glitch2"), (0.6, "scribble"), (1.1, "typewriter"), (1.9, "impact")],
    "107": [(0.2, "thud"), (0.9, "buzz"), (1.6, "swoosh"), (2.4, "swoosh"), (3.0, "pop")],
    "108": [(0.1, "rise"), (0.8, "ding"), (1.4, "ding"), (1.9, "thud")],
    "109": [(0.3, "door"), (0.9, "typewriter"), (1.6, "scribble"), (2.1, "thud")],
    "110": [(0.3, "click"), (1.7, "thud"), (1.8, "tick"), (3.4, "thud"), (3.5, "tick"), (4.7, "thud"), (4.8, "tick")],
    "111": [(0.5, "click"), (1.0, "typewriter"), (2.1, "tick"), (3.4, "scribble")],
    "112": [(0.2, "scribble"), (0.5, "rise"), (1.3, "thud")],
    "113": [(0.2, "scribble"), (1.5, "tick"), (2.1, "tick"), (2.6, "tick")],
    "114": [(0.3, "click"), (1.9, "thud"), (2.6, "whoosh"), (2.9, "impact")],
    "115": [(0.2, "click"), (1.6, "thud"), (3.0, "rise"), (3.75, "impact"), (4.5, "impact"), (6.0, "tick")],
    "116": [],
    "117": [(0.2, "click"), (2.3, "typewriter"), (3.0, "typewriter"), (4.1, "tick"), (4.3, "tick"), (4.5, "tick")],
    "118": [(0.3, "click")],
}


def main():
    src, out = sys.argv[1], sys.argv[2]
    tm = json.load(open(os.path.join(HERE, "timing.json"), encoding="utf-8"))
    scenes = {s["id"]: s for s in tm["scenes"]}
    order = [s["id"] for s in tm["scenes"]]
    only = [x.strip() for x in os.environ.get("KINO_SCENES", "").split(",") if x.strip()]
    if only:
        order = [s for s in order if s in only]
        t_shift = scenes[order[0]]["film_start"]           # отрезок начинается с нуля
        total = scenes[order[-1]]["film_end"] - t_shift
    else:
        t_shift = 0.0
        total = tm["scenes"][-1]["film_end"]
    inputs = ["-i", src]
    filters = []
    mixes = ["[0:a]"]
    n = 1
    # музыка по актам: каждый отрезок — свой вход, подрезан и с фейдами
    bounds = []
    for i, (sid, mood) in enumerate(AKTY):
        t0 = scenes[sid]["film_start"] - t_shift
        t1 = (scenes[AKTY[i + 1][0]]["film_start"] - t_shift) if i + 1 < len(AKTY) else total
        t0, t1 = max(0.0, t0), min(total, t1)
        if t1 - t0 > 1.0:
            bounds.append((t0, t1, mood))
    for t0, t1, mood in bounds:
        path = os.path.join(MUS, mood + ".mp3")
        if not os.path.exists(path):
            continue
        dur = t1 - t0
        gain = MUSIC_DB + (-17.0 - MEAN.get(mood, -17.0))
        inputs += ["-stream_loop", "-1", "-i", path]
        filters.append("[%d:a]atrim=0:%.2f,asetpts=PTS-STARTPTS,afade=t=in:d=1.5,afade=t=out:st=%.2f:d=3.0,"
                       "volume=%.1fdB,adelay=%d|%d,aresample=48000[m%d]"
                       % (n, dur, max(0, dur - 3.0), gain, int(t0 * 1000), int(t0 * 1000), n))
        mixes.append("[m%d]" % n)
        n += 1
    # звуки на движении
    for sid in order:
        for when, snd in EVENTS.get(sid, []):
            path = os.path.join(SFX, snd + ".mp3")
            if not os.path.exists(path):
                continue
            rel = when if isinstance(when, (int, float)) else C.cue(sid, when, None)
            if rel is None:
                continue
            t = scenes[sid]["film_start"] - t_shift + rel
            inputs += ["-i", path]
            filters.append("[%d:a]volume=%.1fdB,adelay=%d|%d,aresample=48000[s%d]" % (n, SFX_DB, int(t * 1000), int(t * 1000), n))
            mixes.append("[s%d]" % n)
            n += 1
    fc = ";".join(filters + ["%samix=inputs=%d:normalize=0:duration=first[aout]" % ("".join(mixes), len(mixes))])
    cmd = [FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-y"] + inputs + \
          ["-filter_complex", fc, "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("звук положен:", out, "· входов", n)


if __name__ == "__main__":
    main()
