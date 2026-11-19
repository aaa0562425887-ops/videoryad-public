#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Страница показа: клипы ПО НОМЕРАМ СЦЕН, как на странице разбора.

    python3 pokaz.py <папка клипов> [порт]
Пишет index.html рядом с клипами и поднимает сервер на первом свободном порту
от указанного (по умолчанию 8840). Он смотрит и правит по номерам.
"""
import html
import json
import os
import socket
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

NAMES = {
    "01": "Лист на тросах", "02": "Линия, которая будет двигаться", "03": "Титр фильма",
    "04": "Шкала жизни", "05": "Пекин, 1971", "06": "Премия без мира", "07": "Прогноз или чертёж",
    "08": "Разведка, Петербург", "09": "1994: НАТО на восток", "10": "Колонка, 2014",
    "11": "Три тезиса из пола", "12": "Минск: линия первая", "13": "Давос, его голос",
    "14": "Линия 24 февраля", "15": "Москва — Пекин", "16": "Ответ Киева", "17": "Мюнхен, 11 месяцев",
    "18": "Минск-три", "19": "Спектейтор", "20": "Нельзя или подходящий исход", "21": "Формула",
    "22": "Восемь часов", "23": "29 ноября 2023", "24": "Стена улик", "24b": "Стена улик · карточки 2–5",
    "25": "Абу-Даби и Аляска", "26": "Три ошибки уезжают вверх", "27": "Три заморозки",
    "28": "Какие земли", "29": "Будапешт", "30": "Шесть недель", "31": "Три слова",
}
AKTY = {"01": "Пролог", "04": "Акт I · Человек", "10": "Акт II · Линия", "19": "Акт III · Разворот",
        "24": "Акт IV · Стол", "31": "Финал"}


def free_port(p):
    while True:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
        p += 1


def main():
    folder = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8840
    tm = json.load(open(os.path.join(HERE, "timing.json"), encoding="utf-8"))
    cards = []
    n_ok = 0
    for sc in tm["scenes"]:
        sid = sc["id"]
        f = None
        for cand in ("kino_%s.mp4" % sid, "%s.mp4" % sid):
            if os.path.exists(os.path.join(folder, cand)):
                f = cand
                break
        if sid in AKTY:
            cards.append('<h2>%s</h2>' % html.escape(AKTY[sid]))
        m0, s0 = divmod(int(sc["film_start"]), 60)
        body = ('<video controls preload="metadata" src="%s"></video>' % html.escape(f)) if f else \
            '<div class="net">клип ещё считается</div>'
        if f:
            n_ok += 1
        cards.append('''<section class="sc" id="s%s">
  <div class="num">%s</div>
  <div class="body">%s
    <div class="cap"><b>%s</b> · %d:%02d · %.0f с%s</div></div>
</section>''' % (sid, sid, body, html.escape(NAMES.get(sid, "")), m0, s0, sc["dur"],
                 (" · вставка оригинала %d с" % sc["insert"]) if sc["insert"] else ""))
    page = '''<!doctype html><html lang="ru"><head><meta charset="utf-8">
<title>ЛИНИЯ · клипы по сценам</title>
<style>
body{background:#121215;color:#eee;font-family:Arial,sans-serif;margin:0;padding:24px 40px}
h1{font-weight:400;letter-spacing:.08em;font-size:22px;color:#aaa}
h1 b{color:#fff}
h2{font-weight:400;font-size:16px;letter-spacing:.3em;color:#888;margin:40px 0 12px;text-transform:uppercase}
.sc{display:flex;gap:18px;margin:14px 0;align-items:flex-start}
.num{width:64px;font-size:40px;font-weight:700;color:#cc221e;flex:none;padding-top:4px}
video{width:720px;max-width:100%%;background:#000;display:block}
.net{width:720px;height:405px;background:#1c1c20;color:#666;display:flex;align-items:center;justify-content:center}
.cap{color:#999;font-size:14px;margin-top:6px}
.cap b{color:#eee;font-weight:600}
</style></head><body>
<h1><b>ПОСЛЕДНИЙ ПРОГНОЗ КИССИНДЖЕРА</b> · клипы по номерам сцен · готово %d из %d</h1>
%s
</body></html>''' % (n_ok, len(tm["scenes"]), "\n".join(cards))
    open(os.path.join(folder, "index.html"), "w", encoding="utf-8").write(page)
    p = free_port(port)
    srv = os.path.join(HERE, "pokaz_server.py")
    subprocess.Popen([sys.executable, srv, str(p)], cwd=folder,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("http://localhost:%d/index.html  (%d из %d клипов)" % (p, n_ok, len(tm["scenes"])))


if __name__ == "__main__":
    main()
