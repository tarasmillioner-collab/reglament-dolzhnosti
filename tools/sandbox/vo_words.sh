#!/bin/bash
# One-shot (single sandbox call, <120 s): download VO, whisper (uk) word timestamps, print compact JSON:
# {"dur":..,"lufs":"..","n":N,"w":[[word,start,end],...]}  (~11 KB for 424 words, fits the 20 KB output cap)
# Usage: vo_words.sh <mp3 url> [model=small] [atempo=1.0]
set -e
U="$1"; M=${2:-small}; T=${3:-1.0}
cd /home/user && curl -sf -o vo_src.mp3 "$U"
if [ "$T" != "1.0" ]; then ffmpeg -y -loglevel error -i vo_src.mp3 -filter:a "atempo=$T" -ar 44100 vo.wav; else ffmpeg -y -loglevel error -i vo_src.mp3 -ar 44100 vo.wav; fi
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 vo.wav)
L=$(ffmpeg -nostats -i vo.wav -af ebur128 -f null - 2>&1 | grep -E "^ +I:" | tail -1 | tr -s ' ')
python3 - "$D" "$M" "$L" <<'PY'
import sys,json
from faster_whisper import WhisperModel
m=WhisperModel(sys.argv[2],device='cpu',compute_type='int8',cpu_threads=8)
segs,info=m.transcribe('/home/user/vo.wav',language='uk',word_timestamps=True,beam_size=1,vad_filter=False)
w=[[x.word.strip(),round(x.start,2),round(x.end,2)] for s in segs for x in s.words]
print(json.dumps({'dur':round(float(sys.argv[1]),2),'lufs':sys.argv[3].strip(),'n':len(w),'w':w},ensure_ascii=False,separators=(',',':')))
PY
