#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Звуковой слой фильма: одна тема с вариациями по актам и звук на движении
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

# ЕГО ЧЕТЫРЕ ТРЕКА (19.11, журнал п.26-32), раскладка по актам моя, недостающее — повтором:
# eyes «Eyes of Glory» тревожный · topass «To Pass Time» тревожное · inception энергичный · immortality помпезный
AKTY = [("01", "eyes"), ("10", "topass"), ("13", "inception"), ("19", "eyes"),
        ("24", "immortality"), ("26", "topass"), ("28", "inception"), ("30", "immortality")]
# «если сейчас это 100%, то процентов 20» → −14 дБ от его исходника; треки сперва выравниваются к −17 дБ средней
MUSIC_DB = -22.0   # 19.11 п.62: «если сейчас 100%, делай 40%» — было −14
MEAN = {"eyes": -17.7, "topass": -14.1, "inception": -15.5, "immortality": -22.7, "mystery": -17.0, "calm": -17.0, "tense": -17.0}
SFX_DB = -20.0     # «шелест… чуть тише» (п.4): было −14

# события звука: сцена → [(время от начала сцены или фраза, звук)]
EVENTS = {
    "01": [("Четырнадцатого ноября", "tick"), ("Украина уходит", "scribble"), ("а взамен получает", "whoosh"),
           ("Киев отказался", "thud")],
    "02": [(0.0, "tick"), (0.45, "tick"), (0.9, "tick"), (1.35, "tick"), (1.8, "tick"), (2.25, "tick"),
           ("Её автор", "whoosh"), (4.9, "swoosh"), (6.0, "swoosh"), ("голосом Кремля", "pop"),
           ("Теперь обе редакции", "thud"), ("что именно он говорил", "click"), ("что из этого уже", "click"),
           ("в чём он промахнулся", "click"), ("и главное", "click"), ("какие территории", "scribble")],
    "03": [(0.0, "click"), (2.0, "click"), (4.2, "scribble"), (6.0, "impact")],
    "04": [(1.4, "whoosh"), (2.6, "tick"), (3.8, "tick"), (5.0, "tick"), (6.2, "tick"), (7.4, "tick"), (8.6, "tick"),
           (9.8, "tick"), (11.0, "tick")],
    "05": [("затем госсекретарь", "click"), ("Это он в семьдесят первом", "tick"), ("Пекин и подготовил", "click")],
    "06": [(0.2, "tick"), ("и это его вьетнамский партнёр", "swoosh"), ("потому что война", "thud"), ("Для одних он главный", "whoosh"),
           ("для других военный", "whoosh"), ("полвека его оценки", "swoosh")],
    "07": [(0.3, "pop"), ("Киссинджер был не наблюдателем", "click"), ("а участником", "click"), ("и во многих сюжетах главным", "thud"),
           ("лучше других знает", "tick"), ("где у неё слабое место", "impact")],
    "08": [("Начало девяностых", "click"), ("что до этого служил", "scribble"), ("Киссинджер отвечает", "click"), ("почему в Кремле", "tick")],
    "09": [(0.2, "scribble"), ("Польши", "tick"), ("Чехии", "tick"), ("Венгрии", "tick"), ("Другом Москвы", "thud")],
    "10": [(1.2, "whoosh"), ("Крым только что перешёл", "scribble"), ("Киссинджер публикует", "click"), ("начните с конца", "scribble"),
           ("каким должен быть итог", "thud"), ("и только потом вводите санкции", "thud")],
    "11": [(0.2, "click"), ("мост", "scribble"), ("Второй Украине не следует", "click"), ("Финляндия", "tick"), ("Третий", "click"),
           ("а алиби", "thud"), ("назвал присоединение Крыма", "scribble"), ("не кто прав", "thud"), ("а чем это закончится", "impact")],
    "12": [("Через полгода после неё", "scribble"), ("Семь лет она стояла", "tick"), ("сместилась на тысячу", "impact"),
           ("спор о словах", "thud"), ("спор о памяти", "impact")],
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
