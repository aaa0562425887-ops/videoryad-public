#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Фильм «Верица» — седьмой кусок v2: дословные цитаты из интервью + комментарий ПЛАНЕТЫ после каждой.

Его решения 25.11 (журнал ~18:10-18:30): цитаты разносятся по фильму (Украина — после «Пока не случилось», Венгрия,
Германия и центр мира — после «Сроков нет ни у одного пункта»); Сербия (танки на Косово, база) — ИСКЛЮЧЕНА;
из Украины выборы и Порошенко — вырезаны; после каждой цитаты — одна-две фразы ПЛАНЕТЫ от нас: «пока нет» + факт,
без «сбылось / не сбылось». Отдельного титра блока больше нет.

Цитата (frag_scene): врезка с зумом на лицо, оригинал 2 с, потом приглушение, перевод ОЛЬГИ за кадром печатается
строками, осциллограмма живого звука. Фрагмент может быть склеен из двух кусков записи (segs).
Комментарий (komm_scene): тот же кадр замирает в четверть скорости и уходит в тень, крупно красным «ПОКА НЕТ.» /
«СРОКА НЕТ.», ниже строки факта печатаются под голос ПЛАНЕТЫ.
"""
from PIL import Image, ImageEnhance

import core as C
import fx
from core import W, H
from scenes import scene, vid, zoom_at, grade, flash, word, red_line, fit_px
from scenes2 import label
from scenes5 import envelope, oscillo

SAFE_X, SAFE_Y = 96, 54

CAP_R = ("Верица Обренович", "Белград · интервью опубликовано 21.04.2019 · METANOJA TV", "оригинальный звук · перевод за кадром")
CAP_K = ("Верица Обренович", "Белград · интервью опубликовано 21.04.2019 · METANOJA TV", "комментарий автора фильма")


def verica_t(key, name, src, t, zoom=1.8, cx=0.48, cy=0.30, push=0.03, hand=2.0, k_grade=0.85):
    """кадр записи в момент src (секунда файла); наезд и рука — от времени сцены t, не от секунды файла"""
    fr = vid(key, name, 0.0, zoom=zoom, cx=cx, cy=cy).at(src)
    hx, hy = fx.handheld(t, hand, hash(key) % 7)
    img = zoom_at(fr, 1.0 + push * t, W / 2 + hx, H / 2 + hy)
    return grade(img, k_grade)


# ── таблица цитат: id · файл · куски записи [(секунда файла, длина)] · тема · строки перевода (текст, печать с, до) ·
#    слои Ольги [(файл, с какой секунды сцены, длина)] · clear — секунда сцены, с которой прежние строки снимаются (склейка)
FRAG = [
    dict(id="R6", file="r6_ukraina_2401.mp4", segs=[(16.3, 8.7), (35.7, 7.9)], tema="УКРАИНА",
         olga=[("olga_ukr_a.mp3", 2.3, 5.45), ("olga_ukr_b.mp3", 10.5, 3.45)], clear=8.7,
         lines=[("«И Украина максимально сблизится с Россией,", 2.4, 4.9),
                ("и будет сотрудничество, особенно вокруг Крыма.»", 5.0, 7.7),
                ("«Потом Путин посетит Украину,", 10.6, 12.4),
                ("и его хорошо встретят.»", 12.5, 13.9)]),
    dict(id="R2", file="r2_vengriya_1437.mp4", segs=[(1.9, 13.6)], tema="ВЕНГРИЯ", olga=[("olga_r2.mp3", 2.3, 5.86)],
         lines=[("«Вот Венгрия хочет объединиться с Россией,", 2.4, 4.6),
                ("и чтобы русские военные силы пришли в Венгрию.»", 4.7, 7.1),
                ("«Это и случится.»", 7.2, 8.1)]),
    dict(id="R3", file="r3_germaniya_2017.mp4", segs=[(0.2, 20.6)], tema="ГЕРМАНИЯ", olga=[("olga_r3.mp3", 2.3, 7.40)],
         lines=[("«Поэтому произойдёт раздел Германии, который проведёт Россия,", 2.3, 5.7),
                ("на восточную и западную части.", 5.8, 7.9),
                ("И Россия изгонит исламистов.»", 7.9, 9.7)]),
    dict(id="R1", file="r1_centr_1300.mp4", segs=[(27.8, 14.6)], tema="ЦЕНТР МИРА", olga=[("olga_r1.mp3", 2.3, 9.64)],
         lines=[("«Что касается Азии — там будут Индия, Китай и Россия.»", 2.4, 7.1),
                ("«Россия как самая сильная держава — она приведёт в движение многое.»", 7.1, 11.3),
                ("«И сейчас особенно.»", 11.3, 11.9)]),
]

# ── комментарии ПЛАНЕТЫ: после какой цитаты · файл голоса · длина · крупное слово · строки (текст, печать с, до — от начала сцены)
KOMM = [
    dict(id="K6", after="R6", file="komm_ukr.mp3", dur=2.60, big="ПОКА НЕТ.",
         lines=[("Срока у этих слов нет.", 1.5, 2.9)]),
    dict(id="K2", after="R2", file="komm_veng.mp3", dur=8.49, big="ПОКА НЕТ.",
         lines=[("Русских войск в Венгрии нет.", 1.4, 3.0),
                ("Но Будапешт единственный в Евросоюзе,", 3.4, 5.6),
                ("кто блокирует помощь Киеву и держит сделки с Москвой.", 5.8, 8.6)]),
    dict(id="K3", after="R3", file="komm_germ.mp3", dur=8.55, big="ПОКА НЕТ.",
         lines=[("Германия едина.", 1.4, 2.4),
                ("Но карта выборов снова делится на восток и запад.", 2.8, 5.4),
                ("На востоке побеждают те, кто за переговоры с Москвой.", 5.8, 8.7)]),
    dict(id="K1", after="R1", file="komm_centr.mp3", dur=7.12, big="СРОКА НЕТ.",
         lines=[("Но Россия, Китай и Индия уже в одном объединении,", 1.4, 5.2),
                ("где почти половина населения планеты.", 5.4, 7.3)]),
]
KOMM_AT = 0.35   # голос ПЛАНЕТЫ начинается через столько секунд после склейки


def src_time(f, t):
    """секунда файла для момента сцены t — по кускам записи"""
    acc = 0.0
    for s0, d in f["segs"]:
        if t < acc + d or (s0, d) == f["segs"][-1]:
            return s0 + (t - acc)
        acc += d
    return f["segs"][-1][0] + f["segs"][-1][1]


def frag_scene(f):
    def fn(t, dur):
        img = verica_t("r_" + f["id"], f["file"], src_time(f, t), t)
        tracks, acc = [], 0.0
        for s0, d in f["segs"]:
            tracks.append((envelope(f["file"], s0, d), acc, C.WHITE))
            acc += d
        for name, at, d in f["olga"]:
            tracks.append((envelope(name, 0.0, d), at, C.RED))
        lay = oscillo(tracks, t, H - 150, 54, SAFE_X, W - SAFE_X)
        k_orig = C.seg(t, 0.2, 0.6) * (1 - C.seg(t, 2.0, 2.4))
        k_per = C.seg(t, 2.3, 2.7)
        lays = [lay, label("ОРИГИНАЛЬНЫЙ ЗВУК", k_orig, 120, 34, C.GREY, x=W - SAFE_X, anchor="rs"),
                label("ПЕРЕВОД ЗА КАДРОМ", k_per, 120, 34, C.RED, x=W - SAFE_X, anchor="rs"),
                label(f["tema"], C.seg(t, 0.1, 0.5), 120, 40, C.WHITE, x=SAFE_X, anchor="ls", track=0.16)]
        clear = f.get("clear")
        vis = [ln for ln in f["lines"] if clear is None or (ln[1] >= clear) == (t >= clear)]
        n = len(vis)
        for i, (txt, t0, t1) in enumerate(vis):
            k = C.seg(t, t0, t1)
            if k <= 0 or (i + 3 < n and t >= vis[i + 3][1]):
                continue
            y = 196 + (i % 3) * 54
            last = (i == n - 1) or t < vis[i + 1][1]
            lays.append(fx.typed(txt, k, "head_r", 40, C.WHITE, SAFE_X, y, 0.02, last, t))
        lays.append(C.caption(*CAP_R, k=C.seg(t, 0.4, 0.9)))
        img = C.over(img, *lays).convert("RGB")
        fo = 0.0 if any(k["after"] == f["id"] for k in KOMM) else 0.3   # за цитатой сразу комментарий — без затемнения
        return C.finish(flash(img, t, 0.08, 0.35), t, dur, fi=0.0, fo=fo, grain_k=0.03, vig=0.3)
    return fn


def komm_scene(k):
    f = next(x for x in FRAG if x["id"] == k["after"])
    src_end = src_time(f, sum(d for _, d in f["segs"]) - 0.05)
    def fn(t, dur):
        # кадр записи замирает в четверть скорости и уходит в тень
        img = verica_t("r_" + f["id"], f["file"], src_end + 0.25 * t, t, push=0.012, hand=1.0, k_grade=1.0)
        kd = C.seg(t, 0.0, 0.6)
        img = ImageEnhance.Color(img).enhance(1 - 0.6 * kd)
        img = Image.blend(img, Image.new("RGB", img.size, (6, 6, 9)), 0.6 * kd)
        kb = C.seg(t, 0.15, 0.55)
        px = fit_px(k["big"], "head", 150, W - 2 * SAFE_X, 0.06)
        yb = H * 0.40
        lays = [word(k["big"], kb, yb, px, "head", C.RED, 0.06, x=SAFE_X, anchor="ls", rise=30),
                red_line(C.seg(t, 0.5, 0.9), SAFE_X, SAFE_X + 360, yb + 36, 5),
                label(f["tema"], 1.0, 120, 40, C.WHITE, x=SAFE_X, anchor="ls", track=0.16)]
        for i, (txt, t0, t1) in enumerate(k["lines"]):
            kk = C.seg(t, t0 + KOMM_AT, t1 + KOMM_AT)
            if kk <= 0:
                continue
            last = (i == len(k["lines"]) - 1) or t < k["lines"][i + 1][1] + KOMM_AT
            w = fit_px(txt, "serif", 46, W - 2 * SAFE_X, 0.0)
            lays.append(fx.typed(txt, kk, "serif", min(46, w), C.WHITE, SAFE_X, yb + 86 + i * 60, 0.0, last, t))
        lays.append(C.caption(*CAP_K, k=1.0))
        img = C.over(img, *lays).convert("RGB")
        return C.finish(flash(img, t, 0.06, 0.25), t, dur, fi=0.0, fo=0.4, grain_k=0.03, vig=0.35)
    return fn


def register():
    for f in FRAG:
        scene(f["id"])(frag_scene(f))
    for k in KOMM:
        scene(k["id"])(komm_scene(k))
