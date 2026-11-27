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
AKTY = [("01", "incoming"), ("09", "tishina"), ("10", "final")]   # хук — «Inception»-тема тихо; В0 — музыка уходит; финал хука и титр — «Eyes of Glory»
MUSIC_DB = -22.0   # как у Киссинджера после п.62 («музыка еле слышно»)
MEAN = {"missing": -12.4, "final": -12.9, "topass": -13.9, "incoming": -17.2}
SFX_DB = -20.0

# события звука: сцена → [(секунда сцены, звук)] — секунды сцены, с учётом вставки
EVENTS = {
    "01": [(0.15, "rise"), (1.05, "thud")],
    "02": [(1.65, "swoosh"), (4.2, "swoosh"), (4.95, "swoosh"), (5.7, "swoosh"), (6.45, "swoosh"), (7.35, "click"), (10.4, "scribble")],
    "03": [(1.7, "thud"), (3.95, "tick"), (4.2, "tick"), (4.45, "tick"), (4.85, "impact"), (5.85, "click"), (6.75, "whoosh"), (7.0, "pop")],
    "04": [(0.1, "rise"), (4.3, "click"), (6.15, "thud"), (8.45, "thud"), (10.3, "thud")],
    "05": [(1.15, "click"), (2.3, "click"), (3.6, "thud"), (5.6, "typewriter"), (7.1, "typewriter"), (7.45, "rise")],
    "06": [(1.15, "click"), (2.15, "thud"), (3.45, "typewriter"), (5.0, "typewriter"), (5.05, "glitch2"), (6.2, "typewriter")],
    "07": [(0.0, "impact"), (0.05, "glitch"), (1.7, "whoosh"), (5.05, "sparkle"), (5.9, "tick"), (6.3, "tick"), (6.7, "tick"), (7.1, "tick"), (8.0, "click")],
    "08": [(1.15, "typewriter"), (3.0, "thud"), (3.5, "click"), (5.4, "tick"), (5.7, "tick"), (6.0, "tick"), (6.4, "impact"), (6.85, "rise"), (9.2, "thud"), (10.5, "shutter"), (10.6, "thud"), (13.4, "click")],
    "09": [(0.05, "click"), (2.35, "typewriter"), (4.35, "typewriter"), (6.0, "typewriter"), (9.0, "thud")],
    "10": [(0.1, "shutter"), (3.8, "thud"), (5.3, "thud"), (6.25, "impact"), (7.9, "thud"), (8.1, "thud"), (8.35, "thud"), (8.55, "thud"), (11.85, "tick"), (12.0, "tick"), (12.15, "tick"), (12.3, "tick"), (12.85, "tick"), (13.0, "tick"), (13.15, "tick"), (13.3, "tick"), (13.8, "whoosh"), (15.05, "typewriter")],
    "11": [(2.0, "impact"), (2.5, "swoosh"), (3.1, "reveal")],
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
