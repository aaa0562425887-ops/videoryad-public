#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Клип одной сцены фильма.

    python3 shard.py 12 out/12.mp4            # сцена целиком, все ядра
    python3 shard.py 12 out/12.mp4 --workers 2
    python3 shard.py 12 proba.png --frame 5.0  # один кадр для проверки раскладки
    python3 shard.py --list                    # сцены и длительности (для матрицы)

Кадры считаются кусками по процессам (каждый процесс — свой непрерывный
отрезок, чтобы чтение архивного видео шло последовательно), склеиваются
ffmpeg в H.264 30 к/с.
"""
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import core as C  # noqa: E402


def _load():
    import scenes_a, scenes_b, scenes_c  # noqa: F401
    return scenes_a.SCENES


def _render_chunk(args):
    sid, i0, i1, dur, tmp = args
    S = _load()
    fn = S[sid]
    t0 = time.time()
    for i in range(i0, i1):
        t = i / C.FPS
        im = fn(min(t, dur - 1e-3), dur)
        im.convert("RGB").save(os.path.join(tmp, "f%05d.jpg" % i), quality=93, subsampling=0)
    return (i0, i1, time.time() - t0)


def main():
    if "--list" in sys.argv:
        tm = json.load(open(os.path.join(HERE, "timing.json"), encoding="utf-8"))
        print(json.dumps([s["id"] for s in tm["scenes"]]))
        return
    sid, out = sys.argv[1], sys.argv[2]
    dur = C.dur_of(sid)
    if "--frame" in sys.argv:
        t = float(sys.argv[sys.argv.index("--frame") + 1])
        S = _load()
        S[sid](min(t, dur - 1e-3), dur).convert("RGB").save(out, quality=92)
        print("кадр:", out)
        return
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else (os.cpu_count() or 2)
    n = int(round(dur * C.FPS))
    tmp = os.path.join(HERE, "frames_" + sid)
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    chunks = []
    step = (n + workers - 1) // workers
    for k in range(workers):
        a, b = k * step, min(n, (k + 1) * step)
        if a < b:
            chunks.append((sid, a, b, dur, tmp))
    t0 = time.time()
    if len(chunks) == 1:
        res = [_render_chunk(chunks[0])]
    else:
        with Pool(len(chunks)) as p:
            res = p.map(_render_chunk, chunks)
    dt = time.time() - t0
    print("сцена %s: %d кадров, %d процессов, %.0f с (%.2f с/кадр на процесс)" % (
        sid, n, len(chunks), dt, sum(r[2] for r in res) / max(1, n)))
    subprocess.run([C.ffmpeg(), "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                    "-framerate", str(C.FPS), "-i", os.path.join(tmp, "f%05d.jpg"),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    print("готово:", out, os.path.getsize(out) // 1024, "КБ")


if __name__ == "__main__":
    main()
