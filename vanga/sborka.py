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
    # «Ванга 2027», блок 0. Кортеж (файл, старт в куске, дБ) или словарь слоёв (см. insert_mix).
    "04": ("b_g1_2438.mp4", 1484.0 - 1473.08, -30.0),       # Ванга без слов, чб 1974 — оригинальный звук тихо
    # В0: Горещо 2, 11:43–11:52 — оригинал 2 с −19 дБ, под Ольгу −13 дБ, после Ольги оригинал обратно, потом тишина (пауза 1,5 с)
    "09": {"layers": [
        {"file": "v0_g2_1103.mp4", "start": 703.0 - 660.16, "at": 0.0, "dur": 9.0, "target": -19.0, "fade_in": 0.25, "fade_out": 0.6,
         "duck": [(2.0, 2.5, -13.0), (7.7, 8.2, 7.0)]},
        {"file": "olga_v0.mp3", "start": 0.0, "at": 2.3, "dur": 5.3, "target": -18.0, "fade_in": 0.0, "fade_out": 0.1},
    ]},
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


def voice_piece(mp3, a, b, out, cuts):
    """кусок голоса a→b (b=None — до конца) без вырезанных отрезков cuts; пишет out, возвращает True если что-то есть"""
    spans, cur = [], a
    for c0, c1 in sorted(cuts):
        if b is not None and c0 >= b:
            break
        if c1 <= cur:
            continue
        if c0 > cur:
            spans.append((cur, c0))
        cur = max(cur, c1)
    if b is None or b - cur > 0.02:
        spans.append((cur, b))
    spans = [(x, y) for x, y in spans if y is None or y - x > 0.02]
    if not spans:
        return False
    parts = []
    for i, (x, y) in enumerate(spans):
        seg = out[:-4] + "_%d.wav" % i
        cmd = [FF, "-nostdin", "-v", "error", "-y", "-ss", "%.3f" % x]
        if y is not None:
            cmd += ["-to", "%.3f" % y]
        run(cmd + ["-i", mp3, "-ac", "2", "-ar", "48000", seg])
        parts.append(seg)
    if len(parts) == 1:
        os.replace(parts[0], out)
    else:
        lst = out[:-4] + "_list.txt"
        open(lst, "w", encoding="utf-8").write("".join("file '%s'\n" % p for p in parts))
        run([FF, "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    return True


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


AIR_AT = 80.6   # «воздух» комнаты для пауз внутри сцены: естественная тишина озвучки 80,27-82,55 с (после «…военными.»)
FADE = 0.06     # сглаживание реза голоса на паузе, с


def mid_pauses(sc, mp3, cursor, parts, tmp, cuts):
    """паузы внутри сцены (финал п.1-2): голос до точки с фейдом, вместо нулевой тишины — воздух комнаты, следующий голос с фейдом.
    Его слово 25.11 ~20:50: «паузы видны, как будто их обрезали» — поэтому не цифровой ноль и не рез впритык."""
    for k, (v, m) in enumerate(sc.get("mid", [])):
        seg = os.path.join(tmp, "v_%s_m%d.wav" % (sc["id"], k))
        if v - cursor > 0.02 and voice_piece(mp3, cursor, v, seg, cuts):
            seg2 = seg[:-4] + "_f.wav"   # фейд хвоста без ffprobe (на раннере его нет): переворот → фейд входа → переворот
            run([FF, "-nostdin", "-v", "error", "-y", "-i", seg, "-af", "areverse,afade=t=in:d=%.3f,areverse" % FADE, seg2])
            parts.append(seg2)
        air = os.path.join(tmp, "s_%s_m%d.wav" % (sc["id"], k))
        run([FF, "-nostdin", "-v", "error", "-y", "-ss", "%.3f" % AIR_AT, "-t", "%.3f" % m, "-i", mp3, "-ac", "2", "-ar", "48000",
             "-af", "afade=t=in:d=0.08,afade=t=out:st=%.3f:d=0.08" % (m - 0.08), air])
        parts.append(air)
        head = os.path.join(tmp, "h_%s_m%d.wav" % (sc["id"], k))
        run([FF, "-nostdin", "-v", "error", "-y", "-ss", "%.3f" % v, "-t", "%.3f" % FADE, "-i", mp3, "-ac", "2", "-ar", "48000",
             "-af", "afade=t=in:d=%.3f" % FADE, head])
        parts.append(head)
        cursor = v + FADE
    return cursor


def main():
    clips, mp3, srt, out = sys.argv[1:5]
    tm = json.load(open(os.path.join(HERE, "timing.json"), encoding="utf-8"))
    scenes = tm["scenes"]
    cuts = [tuple(c) for c in tm.get("cuts", [])]   # вырезанные отрезки озвучки (оговорка блока 4)
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
            p = os.path.join(clips, "vanga_%s.mp4" % sc["id"])
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
        mid = sc.get("mid", [])
        if sc["insert"] <= 0 and not mid:
            continue
        if sc["insert"] <= 0:
            cursor = mid_pauses(sc, mp3, cursor, parts, tmp, cuts)   # только паузы внутри сцены (сцена 14)
            continue
        # голос до начала этой сцены
        seg = os.path.join(tmp, "v_%s.wav" % sc["id"])
        if sc["voice_start"] - cursor > 0.02:      # пауза в самом начале отрезка — голоса до неё нет
            if voice_piece(mp3, cursor, sc["voice_start"], seg, cuts):
                parts.append(seg)
        cursor = sc["voice_start"]
        # оригинал на длину вставки
        spec = INSERT_AUDIO.get(sc["id"], (None, 0.0, -20.0))
        ins = os.path.join(tmp, "i_%s.wav" % sc["id"])
        if isinstance(spec, dict):
            insert_mix(sc, spec, ins)
            parts.append(ins)
            cursor = mid_pauses(sc, mp3, cursor, parts, tmp, cuts)
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
        cursor = mid_pauses(sc, mp3, cursor, parts, tmp, cuts)   # паузы внутри сцены со вставкой в начале (сцена 12)
    tail = os.path.join(tmp, "v_tail.wav")
    if voice_piece(mp3, cursor, None, tail, cuts):
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
