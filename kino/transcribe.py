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
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(src, language=lang, vad_filter=True)
    res = [{"t0": round(s.start, 2), "t1": round(s.end, 2), "text": s.text.strip()} for s in segments]
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    for r in res:
        print("%7.1f  %s" % (r["t0"], r["text"]))


if __name__ == "__main__":
    main()
