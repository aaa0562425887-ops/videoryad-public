#!/usr/bin/env bash
# Забрать клипы сцен из облака в папку фильма и поднять страницу показа.
#   bash zabrat.sh <run_id>
set -e
RUN="$1"
REPO=aaa0562425887-ops/videoryad-public
VA=~/.claude/skills/news-video/cloud/va.sh
D="/mnt/d/YouTube/ФИЛЬМЫ/КИССИНДЖЕР-ЛИНИЯ/klipy"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$D"
TMP=$(mktemp -d)
bash "$VA" shest gh run download "$RUN" -R "$REPO" -D "$TMP" 2>&1 | tail -1 || true
n=0
while read -r f; do
  cp "$f" "$D/$(basename "$f")"; n=$((n+1))
done < <(find "$TMP" -name 'kino_*.mp4')
while read -r f; do
  mkdir -p "$D/../scenes/rasshifrovka"; cp "$f" "$D/../scenes/rasshifrovka/"
done < <(find "$TMP" -name '*.json')
rm -rf "$TMP"
echo "клипов забрано: $n → $D"
python3 "$HERE/pokaz.py" "$D" 8840
