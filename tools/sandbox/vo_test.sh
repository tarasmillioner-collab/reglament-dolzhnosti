#!/bin/bash
# Transcribe a Higgsfield TTS result with faster-whisper (uk) and print word timestamps as JSON. Usage: vo_test.sh <mp3 url> [model]
set -e
U="$1"; M=${2:-small}
cd /home/user && curl -sf -o vo.mp3 "$U"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 vo.mp3)
python3 - "$D" "$M" <<'PY'
import sys,json
from faster_whisper import WhisperModel
m=WhisperModel(sys.argv[2],device='cpu',compute_type='int8')
segs,info=m.transcribe('/home/user/vo.mp3',language='uk',word_timestamps=True,beam_size=1)
words=[{'w':w.word.strip(),'s':round(w.start,2),'e':round(w.end,2)} for s in segs for w in s.words]
print(json.dumps({'dur':float(sys.argv[1]),'lang':info.language,'prob':round(info.language_probability,3),'n':len(words),'words':words},ensure_ascii=False))
PY
