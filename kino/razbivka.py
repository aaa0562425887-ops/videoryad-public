#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тайминг 31 сцены фильма по субтитрам озвучки.

Сцена задаётся ПЕРВЫМИ СЛОВАМИ своего текста; начало берётся из .srt,
конец — начало следующей сцены. Вставки оригинальной речи героя (сц. 13,
16, 22) добавляются В НАЧАЛО сцены: диктор на это время молчит, финальная
сборка режет дорожку в этом месте.

    python3 razbivka.py <файл.srt> <timing.json>
"""
import json
import re
import sys

# (номер, первые слова сцены, вставка оригинала в секундах)
SCENES = [
    ("01", "В Абу Даби на столе переговоров", 0),
    ("02", "Эта конструкция не родилась", 0),
    ("03", "И отдельно чем заканчивались заморозки", 0),
    ("04", "Несколько слов о том почему", 0),
    ("05", "Советник Никсона по национальной", 0),
    ("06", "Это ему дали Нобелевскую", 0),
    ("07", "Здесь сразу об одном возражении", 0),
    ("08", "О его отношениях с Москвой", 0),
    ("09", "При этом в девяносто четвёртом", 0),
    ("10", "Март четырнадцатого", 0),
    ("11", "В колонке три тезиса", 0),
    ("12", "И вот деталь которую в пересказах", 0),
    ("13", "Май двадцать второго", 12),
    ("14", "В переводе на простой язык", 0),
    ("15", "Там же он предупредил о Китае", 0),
    ("16", "Киев ответил через два дня", 11),
    ("17", "Напомню о чём речь", 0),
    ("18", "Сравнение сильное", 0),
    ("19", "Декабрь двадцать второго", 0),
    ("20", "Раньше Украине не место в НАТО", 13),
    ("21", "Но условия сделки он оставил", 0),
    ("22", "Весной двадцать третьего журналисты", 0),
    ("23", "Двадцать девятого ноября", 0),
    ("24", "Теперь по пунктам", 0),
    ("25", "Делегации России Украины и Соединённых", 0),
    ("24b", "Сбылось второе", 0),
    ("26", "Теперь ошибки", 0),
    ("27", "Прежде чем перейти к территориям", 0),
    ("28", "Главный вопрос Какие территории", 0),
    ("29", "И всё упрётся в гарантии", 0),
    ("30", "По словам главного переговорщика", 0),
    ("31", "Вопрос к вам", 0),
]

TAIL = 8.0   # хвост после последней фразы: чёрное и титры


def norm(s):
    s = s.lower().replace("ё", "е")
    return re.sub(r"[^а-яa-z0-9 ]+", " ", s)


def parse_srt(path):
    raw = open(path, encoding="utf-8-sig").read()
    cues = []
    for block in re.split(r"\n\s*\n", raw.strip()):
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+) --> (\d+):(\d+):(\d+)[,.](\d+)", lines[1])
        if not m:
            continue
        g = [int(v) for v in m.groups()]
        t0 = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        t1 = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        cues.append((t0, t1, " ".join(lines[2:])))
    return cues


def find_start(cues, phrase, after=0.0):
    want = norm(phrase).split()
    n = len(want)
    # идём по репликам, сшивая соседние — фраза может начинаться в конце одной
    for i, (t0, t1, txt) in enumerate(cues):
        if t0 < after:
            continue
        words = norm(" ".join(c[2] for c in cues[i:i + 3])).split()
        head = norm(txt).split()
        # фраза должна начинаться в ЭТОЙ реплике
        for off in range(0, len(head)):
            if words[off:off + n] == want:
                # фраза началась внутри реплики — время по доле слов
                return t0 + (t1 - t0) * off / max(1, len(head)), i
    return None, None


def main():
    srt, out = sys.argv[1], sys.argv[2]
    cues = parse_srt(srt)
    voice_end = cues[-1][1]
    starts = []
    after = 0.0
    for sid, phrase, ins in SCENES:
        t, i = find_start(cues, phrase, after)
        if t is None:
            # мягче: первые три слова
            t, i = find_start(cues, " ".join(phrase.split()[:3]), after)
        if t is None:
            raise SystemExit("не нашёл начало сцены %s: «%s»" % (sid, phrase))
        starts.append((sid, t, ins))
        after = t + 0.5
    res = []
    for k, (sid, t, ins) in enumerate(starts):
        t_next = starts[k + 1][1] if k + 1 < len(starts) else voice_end + TAIL
        res.append({"id": sid, "voice_start": round(t, 3), "voice_end": round(t_next, 3),
                    "insert": ins, "dur": round(t_next - t + ins, 3)})
    # абсолютный тайминг в ФИЛЬМЕ (с учётом вставок, сдвигающих всё дальше)
    shift = 0.0
    for r in res:
        r["film_start"] = round(r["voice_start"] + shift, 3)
        shift += r["insert"]
        r["film_end"] = round(r["voice_end"] + shift, 3)
    json.dump({"voice_end": voice_end, "scenes": res}, open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    total = res[-1]["film_end"]
    print("сцен %d · голос %d:%02d · фильм %d:%02d" % (
        len(res), voice_end // 60, voice_end % 60, total // 60, total % 60))
    for r in res:
        print("  %-3s %6.1f → %6.1f  (%5.1f с%s)" % (
            r["id"], r["film_start"], r["film_end"], r["dur"],
            "  +вставка %d с" % r["insert"] if r["insert"] else ""))


if __name__ == "__main__":
    main()
