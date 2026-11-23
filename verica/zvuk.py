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
AKTY = [("01", "missing")]
MUSIC_DB = -22.0   # как у Киссинджера после п.62 («музыка еле слышно»)
MEAN = {"missing": -12.4}
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
