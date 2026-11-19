#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Расшифровка архивного звука В ОБЛАКЕ (не на его машине): где в записи
нужная фраза. faster-whisper, модель small, CPU.

    python3 transcribe.py archiv/zelensky_2022_05_25.mp3 uk out/zelensky.json
"""
import json
import sys


def main():
    src, lang, out = sys.argv[1], sys.argv[2], sys.argv[3]
    import subprocess
    import numpy as np
    from faster_whisper import WhisperModel
    # звук декодируем сами через ffmpeg (PyAV на раннере несовместим с faster-whisper)
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ff = "ffmpeg"
    raw = subprocess.run([ff, "-nostdin", "-loglevel", "error", "-i", src, "-f", "f32le", "-ac", "1",
                          "-ar", "16000", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32)
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio, language=lang, vad_filter=True)
    res = [{"t0": round(s.start, 2), "t1": round(s.end, 2), "text": s.text.strip()} for s in segments]
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    for r in res:
        print("%7.1f  %s" % (r["t0"], r["text"]))


if __name__ == "__main__":
    main()
