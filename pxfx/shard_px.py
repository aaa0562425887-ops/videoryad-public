#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Клип одной сцены:  python3 shard_px.py <сцена> <куда.mp4>"""
import os
import subprocess
import sys

import pxscenes as SC


HERE = os.path.dirname(os.path.abspath(__file__))


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def main():
    name = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "px_%s.mp4" % name)
    fn, secs = SC.SCENES[name]
    tmp = os.path.join(HERE, "frames_" + name)
    os.makedirs(tmp, exist_ok=True)
    n = int(SC.FPS * secs)
    for i in range(n):
        fn(i / (n - 1)).save(os.path.join(tmp, "f%04d.jpg" % i), quality=93)
    subprocess.run([ffmpeg(), "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                    "-framerate", str(SC.FPS), "-i", os.path.join(tmp, "f%04d.jpg"),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
    print("готово:", out, os.path.getsize(out) // 1024, "КБ")


if __name__ == "__main__":
    main()
