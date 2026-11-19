#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Звуковой слой фильма: одна тема с вариациями по актам и звук на движении
графики. Кладётся ПОВЕРХ собранного файла (видео копируется, пересводится
только звук).

    python3 zvuk.py <film.mp4> <out.mp4>

Музыка — наши треки кодом (~/.claude/audio-gen/music): mystery как тема,
calm/tense как вариации по актам, −24 дБ под голосом, провалы в тишину
перед поворотами. Звуки — банк ~/.claude/audio-gen/sfx, −14 дБ.
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

# акты → настроение темы (вариации одной темы: разные дорожки одного синтезатора)
AKTY = [("01", "mystery"), ("04", "calm"), ("10", "tense"), ("19", "mystery"), ("24", "tense"), ("30", "calm")]
MUSIC_DB = -24.0
SFX_DB = -14.0

# события звука: сцена → [(время от начала сцены или фраза, звук)]
EVENTS = {
    "01": [(0.4, "whoosh"), ("а взамен получает", "scribble")],
    "02": [(1.0, "scribble"), (7.0, "tick")],
    "03": [(1.2, "impact")],
    "04": [(2.2, "tick"), (5.0, "tick"), (7.5, "tick"), (10.0, "tick")],
    "05": [(0.5, "pop")],
    "07": [(0.4, "thud"), ("он сам всё это устраивал", "rise")],
    "09": [("Польши", "tick"), ("Чехии", "tick"), ("Венгрии", "tick")],
    "10": [(2.4, "pop"), ("начните с конца", "scribble")],
    "11": [("её роль мост", "thud"), ("военно вне блоков", "thud"), ("а алиби", "thud")],
    "12": [(1.2, "scribble"), ("Семь лет она стояла", "tick"), ("сместилась на тысячу", "impact")],
    "14": [(0.6, "scribble"), ("остаются за ней", "tick"), ("возвращается Украине", "tick")],
    "15": [(1.4, "scribble")],
    "17": [("через одиннадцать месяцев", "impact")],
    "18": [("Минск-три", "thud"), ("Линия", "impact")],
    "20": [("Теперь мирный процесс", "pop")],
    "21": [(0.4, "thud"), ("Крым и старые районы", "thud"), ("территория и членство", "whoosh"), ("одним пакетом", "click")],
    "23": [(0.3, "heartbeat")],
    "24": [("Сбылось первое", "click")],
    "24b": [("Сбылось второе", "click"), ("Сбылось третье", "click"), ("Сбылось четвёртое", "click"), ("Сбылось пятое", "click")],
    "26": [(0.4, "thud"), ("Прошло пятьдесят четыре", "impact"), ("Вторая Финляндия", "rise"), ("Третья главная", "rise"), ("И одно слепое пятно", "rise")],
    "27": [("Корея пятьдесят третий", "tick"), ("Кипр семьдесят четвёртый", "tick"), ("И Минск пятнадцатый", "tick")],
    "28": [("Первое Крым", "thud"), ("Второе Старый Донбасс", "thud"), ("Третье Всё что занято", "thud"), ("Остановятся там где стоят", "impact")],
    "29": [("Выбор на самом деле один", "thud")],
    "30": [("шесть недель", "impact")],
    "31": [("Это Мюнхен", "thud"), ("Минск пятнадцатого", "thud"), ("или Корея", "thud"), ("я посчитаю", "impact")],
}


def main():
    src, out = sys.argv[1], sys.argv[2]
    tm = json.load(open(os.path.join(HERE, "timing.json"), encoding="utf-8"))
    scenes = {s["id"]: s for s in tm["scenes"]}
    order = [s["id"] for s in tm["scenes"]]
    total = tm["scenes"][-1]["film_end"]
    inputs = ["-i", src]
    filters = []
    mixes = ["[0:a]"]
    n = 1
    # музыка по актам: каждый отрезок — свой вход, подрезан и с фейдами
    bounds = []
    for i, (sid, mood) in enumerate(AKTY):
        t0 = scenes[sid]["film_start"]
        t1 = scenes[AKTY[i + 1][0]]["film_start"] if i + 1 < len(AKTY) else total
        bounds.append((t0, t1, mood))
    for t0, t1, mood in bounds:
        path = os.path.join(MUS, mood + ".mp3")
        if not os.path.exists(path):
            continue
        dur = t1 - t0
        inputs += ["-stream_loop", "-1", "-i", path]
        filters.append("[%d:a]atrim=0:%.2f,asetpts=PTS-STARTPTS,afade=t=in:d=2.5,afade=t=out:st=%.2f:d=3.0,"
                       "volume=%.1fdB,adelay=%d|%d,aresample=48000[m%d]"
                       % (n, dur, max(0, dur - 3.0), MUSIC_DB, int(t0 * 1000), int(t0 * 1000), n))
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
            t = scenes[sid]["film_start"] + rel
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
