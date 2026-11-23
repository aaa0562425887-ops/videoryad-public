#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тайминг сцен фильма «Верица» → timing.json.

Сцена = (id, секунда озвучки ПЛАНЕТА, с которой она начинается, вставка в секундах,
конец голоса сцены или None). Паузы [ПАУЗА N с] по тексту — это вставки В НАЧАЛО
сцены (диктор молчит, картинка идёт). Границы — по тишинам в golos.mp3
(ffmpeg silencedetect −38 дБ), срез за 0,15 с до следующего слова.

    python3 timing.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# блок 0 «ХУК»
SCENES = [
    ("01", 0.000, 1.0, None),    # [ТИШИНА 1 с] курсор в строке веб-архива · «Двадцать пятое мая…Одна строка.»
    ("02", 8.230, 1.0, None),    # [ПАУЗА 1 с] строка проявляется · «Путин будет пожизненным…»
    ("03", 11.020, 1.5, None),   # [ПАУЗА 1,5 с] · «Через четыре года Конституцию перепишут…»
    ("04", 15.450, 1.0, None),   # [ПАУЗА 1 с] · «Строкой ниже вторая фраза…»
    ("05", 20.700, 1.5, None),   # [ПАУЗА 1,5 с] · «В тот год отец не называл их имён. Ни разу.»
    ("06", 23.670, 4.0, None),   # [ВЕРИЦА без слов 4 с] · «Эти слова приписывают…назвал никто.»
    ("07", 36.920, 1.0, None),   # [ПАУЗА 1 с] · «Сегодня три её предсказания…пророком?»
    ("08", 55.550, 7.0, 55.550), # [ПАУЗА 2 с + ТИТР 5 с] — голоса нет
]
VOICE_END = 605.72


def main():
    res = []
    for k, (sid, vs, ins, ve) in enumerate(SCENES):
        if ve is None:
            ve = SCENES[k + 1][1] if k + 1 < len(SCENES) else VOICE_END
        res.append({"id": sid, "voice_start": round(vs, 3), "voice_end": round(ve, 3),
                    "insert": ins, "dur": round(ve - vs + ins, 3)})
    shift = 0.0
    for r in res:
        r["film_start"] = round(r["voice_start"] + shift, 3)
        shift += r["insert"]
        r["film_end"] = round(r["voice_end"] + shift, 3)
    json.dump({"voice_end": VOICE_END, "scenes": res}, open(os.path.join(HERE, "timing.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for r in res:
        print("  %-3s голос %6.2f→%6.2f  фильм %6.2f→%6.2f  (%5.2f с, вставка %.1f)" % (
            r["id"], r["voice_start"], r["voice_end"], r["film_start"], r["film_end"], r["dur"], r["insert"]))
    print("итого %.2f с" % res[-1]["film_end"])


if __name__ == "__main__":
    main()
