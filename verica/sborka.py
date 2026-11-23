#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка фильма «Верица» из клипов сцен: видео подряд, голос диктора с паузами под
вставки оригинальной речи, звук оригинала в этих паузах, субтитры.

    python3 sborka.py <папка клипов> <озвучка.mp3> <озвучка.srt> <out.mp4> [--akty]

Считается локально, но это склейка: видео клипов без перекодирования не
обойтись (разные файлы → один поток), поэтому один проход x264 на 15 минут —
около 5-8 минут на его машине. Всё остальное — копирование дорожек.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import core as C          # noqa: E402

FF = C.ffmpeg()

# откуда брать звук оригинала для вставок: (файл в большом архиве, секунда)
# «Верица»: (файл врезки в archiv, секунда, целевая средняя громкость дБ — «без слов» значит тихо)
INSERT_AUDIO = {
    "06": ("v05_krupno_1500.mp4", 0.0, -30.0),
    "09": ("v01_intro_0000-0014.mp4", 5.0, -22.0),   # заставка канала, звук оригинала, потом приглушить (фейд 0,8 с)
    "16": ("v09_krupno_3910.mp4", 0.0, -30.0),
    "35": ("putin_2018_dresden.mp4", 0.0, -20.0),   # врезка Путина: фильм «Путин», А. Кондрашов, 2018 — оригинальный звук
    # пятый кусок: смеси из нескольких слоёв — словарь {"layers": [...]}: file · start (с источника) · at (с от начала
    # вставки) · dur · target (средняя дБ) · fade_in/fade_out · duck=[(t0, t1, дБ)] — плавно приглушить с t0 до t1
    "59": {"layers": [
        {"file": "v02_delo3_1336-1420.mp4", "start": 32.0, "at": 0.0, "dur": 9.3, "target": -19.0, "fade_in": 0.3, "fade_out": 0.8,
         "duck": [(2.0, 2.5, -13.0)]},                                   # Верица: 2 с оригинал, потом приглушить (по тексту)
        {"file": "olga_1.mp3", "start": 0.0, "at": 2.3, "dur": 6.8, "target": -18.0, "fade_in": 0.0, "fade_out": 0.15},   # ОЛЬГА, перевод за кадром
    ]},
    "64": ("v06_krupno_2400.mp4", 0.0, -30.0),      # Верица без слов (v11-v16 без звуковой дорожки — только v03-v10)
    "65": {"layers": [{"file": "olga_2.mp3", "start": 0.0, "at": 0.1, "dur": 2.72, "target": -18.0, "fade_in": 0.0, "fade_out": 0.1}]},
}


def _mean_db(src, start, dur):
    meas = subprocess.run([FF, "-nostdin", "-ss", "%.3f" % start, "-t", "%.3f" % dur, "-i", src,
                           "-vn", "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"mean_volume: ([-\d.]+) dB", meas)
    return float(m.group(1)) if m else None


def insert_mix(sc, spec, out):
    """вставка из нескольких слоёв звука поверх тишины длиной sc["insert"]"""
    L = sc["insert"]
    inputs = ["-f", "lavfi", "-t", "%.3f" % L, "-i", "anullsrc=r=48000:cl=stereo"]
    filters, mixes, n = [], ["[0:a]"], 1
    for ly in spec["layers"]:
        src = C.apath(ly["file"])
        if not os.path.exists(src):
            print("вставка %s: нет файла %s" % (sc["id"], ly["file"]))
            continue
        at = float(ly.get("at", 0.0))
        d = float(ly.get("dur", L - at))
        mean = _mean_db(src, ly["start"], d)
        gain = max(-10.0, min(16.0, ly["target"] - mean)) if mean is not None else 0.0
        af = ["atrim=0:%.3f" % d, "asetpts=PTS-STARTPTS"]
        if ly.get("fade_in", 0) > 0:
            af.append("afade=t=in:d=%.2f" % ly["fade_in"])
        if ly.get("fade_out", 0) > 0:
            af.append("afade=t=out:st=%.2f:d=%.2f" % (d - ly["fade_out"], ly["fade_out"]))
        for t0, t1, db in ly.get("duck", []):
            g = 10 ** (db / 20.0)
            af.append("volume='if(lt(t,%.2f),1,if(lt(t,%.2f),1-(1-%.4f)*(t-%.2f)/%.2f,%.4f))':eval=frame" % (t0, t1, g, t0, t1 - t0, g))
        af.append("volume=%.1fdB" % gain)
        af.append("adelay=%d|%d" % (int(at * 1000), int(at * 1000)))
        af.append("aresample=48000")
        inputs += ["-ss", "%.3f" % ly["start"], "-i", src]
        filters.append("[%d:a]%s[l%d]" % (n, ",".join(af), n))
        mixes.append("[l%d]" % n)
        n += 1
    fc = ";".join(filters + ["%samix=inputs=%d:normalize=0:duration=first[aout]" % ("".join(mixes), len(mixes))])
    run([FF, "-nostdin", "-v", "error", "-y"] + inputs + ["-filter_complex", fc, "-map", "[aout]", "-ac", "2", "-ar", "48000", out])


def run(cmd):
    subprocess.run(cmd, check=True)


def srt_shift(srt_in, scenes, out_ass):
    """субтитры озвучки → .ass со сдвигом на вставки; строка — внизу, спокойная"""
    import razbivka
    cues = razbivka.parse_srt(srt_in)
    # сдвиг для момента t голоса: сумма вставок сцен, начавшихся до t
    def shift(t):
        s = 0.0
        for sc in scenes:
            if sc["voice_start"] <= t + 1e-3:
                s += sc["insert"]
        return s

    def ts(t):
        h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
        return "%d:%02d:%05.2f" % (h, m, s)
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,44,&H00F0EEEA,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,120,120,54,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
"""
    lines = []
    for t0, t1, txt in cues:
        d = shift(t0)
        lines.append("Dialogue: 0,%s,%s,Default,,0,0,0,,%s" % (ts(t0 + d), ts(t1 + d), txt.replace("\n", " ")))
    open(out_ass, "w", encoding="utf-8").write(head + "\n".join(lines) + "\n")


def main():
    clips, mp3, srt, out = sys.argv[1:5]
    tm = json.load(open(os.path.join(HERE, "timing.json"), encoding="utf-8"))
    scenes = tm["scenes"]
    # отрезок фильма: KINO_SCENES="01,02,03,04" — собрать только эти сцены (первая минута на утверждение)
    only = [x.strip() for x in os.environ.get("KINO_SCENES", "").split(",") if x.strip()]
    if only:
        scenes = [sc for sc in scenes if sc["id"] in only]
        print("отрезок:", ", ".join(sc["id"] for sc in scenes))
    tmp = os.path.join(HERE, "sborka_tmp")
    os.makedirs(tmp, exist_ok=True)
    # 1. список клипов по порядку; проверяем, что все есть
    lst = os.path.join(tmp, "list.txt")
    missing = []
    with open(lst, "w", encoding="utf-8") as f:
        for sc in scenes:
            p = os.path.join(clips, "verica_%s.mp4" % sc["id"])
            if not os.path.exists(p):
                p = os.path.join(clips, "%s.mp4" % sc["id"])
            if not os.path.exists(p):
                missing.append(sc["id"])
                continue
            f.write("file '%s'\n" % os.path.abspath(p).replace("'", "'\\''"))
    if missing:
        raise SystemExit("нет клипов сцен: %s" % ", ".join(missing))
    # 2. звуковая дорожка: диктор режется на куски, между ними — оригинал
    parts = []
    cursor = scenes[0]["voice_start"] if only else 0.0   # позиция в голосе диктора
    for sc in scenes:
        if sc["insert"] <= 0:
            continue
        # голос до начала этой сцены
        seg = os.path.join(tmp, "v_%s.wav" % sc["id"])
        if sc["voice_start"] - cursor > 0.02:      # пауза в самом начале отрезка — голоса до неё нет
            run([FF, "-nostdin", "-v", "error", "-y", "-ss", "%.3f" % cursor, "-to", "%.3f" % sc["voice_start"],
                 "-i", mp3, "-ac", "2", "-ar", "48000", seg])
            parts.append(seg)
        cursor = sc["voice_start"]
        # оригинал на длину вставки
        spec = INSERT_AUDIO.get(sc["id"], (None, 0.0, -20.0))
        ins = os.path.join(tmp, "i_%s.wav" % sc["id"])
        if isinstance(spec, dict):
            insert_mix(sc, spec, ins)
            parts.append(ins)
            continue
        name, start, target = spec
        src = C.apath(name) if name else None
        if src and os.path.exists(src):
            # уровень оригинала подтягиваем к голосу диктора (−20 дБ средней)
            meas = subprocess.run([FF, "-nostdin", "-ss", "%.3f" % start, "-t", "%.3f" % sc["insert"], "-i", src,
                                   "-vn", "-af", "volumedetect", "-f", "null", "-"],
                                  capture_output=True, text=True).stderr
            m = re.search(r"mean_volume: ([-\d.]+) dB", meas)
            gain = (target - float(m.group(1))) if m else 0.0
            gain = max(-10.0, min(16.0, gain))
            run([FF, "-nostdin", "-v", "error", "-y", "-ss", "%.3f" % start, "-t", "%.3f" % sc["insert"],
                 "-i", src, "-vn", "-ac", "2", "-ar", "48000",
                 "-af", "afade=t=in:d=0.6,afade=t=out:st=%.2f:d=0.8,volume=%.1fdB" % (sc["insert"] - 0.8, gain), ins])
        else:
            run([FF, "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                 "-t", "%.3f" % sc["insert"], ins])
        parts.append(ins)
    tail = os.path.join(tmp, "v_tail.wav")
    run([FF, "-nostdin", "-v", "error", "-y", "-ss", "%.3f" % cursor, "-i", mp3, "-ac", "2", "-ar", "48000", tail])
    parts.append(tail)
    alist = os.path.join(tmp, "alist.txt")
    open(alist, "w", encoding="utf-8").write("".join("file '%s'\n" % p for p in parts))
    audio = os.path.join(tmp, "audio.wav")
    run([FF, "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", alist, "-c", "copy", audio])
    # 3. субтитры — СНЯТЫ его решением 19.11 (журнал п.43); вернуть: KINO_SUBS=1
    vf = []
    if os.environ.get("KINO_SUBS"):
        ass = os.path.join(tmp, "captions.ass")
        srt_shift(srt, scenes, ass)
        vf = ["-vf", "ass='%s'" % ass.replace("\\", "/").replace(":", "\\:")]
    if os.environ.get("KINO_NO_VIDEO"):
        print("проба: звук собран в", tmp)
        return
    # 4. склейка видео + звук
    run([FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "concat", "-safe", "0", "-i", lst, "-i", audio] + vf + [
         "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-maxrate", "12M", "-bufsize", "24M",
         "-pix_fmt", "yuv420p", "-af", "apad", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out])
    print("готово:", out, os.path.getsize(out) // (1024 * 1024), "МБ")


if __name__ == "__main__":
    main()
