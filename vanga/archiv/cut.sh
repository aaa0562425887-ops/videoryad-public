#!/usr/bin/env bash
# cut.sh <src> <start_s> <dur_s> <out.mp4> — копия без перекодирования; в CUTS.tsv пишется
# реальное начало куска в секундах источника (ближайший ключевой кадр до start).
set -e
src="$1"; st="$2"; du="$3"; out="$4"; here="$(dirname "$0")"
a=$(python3 -c "print(max(0,$st-12))")
kf=$(ffprobe -v error -select_streams v:0 -skip_frame nokey -show_entries frame=pts_time -of csv=p=0 -read_intervals "${a}%${st}" "$src" | grep -v '^$' | tail -1)
[ -n "$kf" ] || kf=$st
ffmpeg -nostdin -v error -y -ss "$kf" -i "$src" -t "$du" -c copy -avoid_negative_ts make_zero -movflags +faststart "$out"
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")
printf '%s\t%s\t%s\t%s\t%s\n' "$(basename "$out")" "$(basename "$src")" "$st" "$kf" "$d" >> "$here/CUTS.tsv"
echo "$(basename "$out"): запрошено $st, начало с ключевого $kf, длина $d"
