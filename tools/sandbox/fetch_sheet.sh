#!/usr/bin/env bash
# Выполняется в sandbox Higgsfield. Скачивает картинки по URL-ам, кладёт в ./stills/<name>.png,
# делает превью 480x854 JPEG q80 (для чанков) и контакт-лист.
# usage: bash fetch_sheet.sh "<name1>=<url1>" "<name2>=<url2>" ...   → печатает список файлов и размеры
set -e; mkdir -p stills prev
for pair in "$@"; do n="${pair%%=*}"; u="${pair#*=}"; curl -sSL -o "stills/$n.png" "$u"; ffmpeg -v error -y -i "stills/$n.png" -vf "scale=480:854:force_original_aspect_ratio=increase,crop=480:854" -q:v 6 "prev/$n.jpg"; done
ls -la prev | awk '{print $5, $9}'
