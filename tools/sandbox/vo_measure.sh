#!/bin/bash
# Measure a one-piece VO in the Higgsfield sandbox: whisper word timestamps (uk), duration, LUFS (ebur128), pauses.
# Usage: vo_measure.sh <mp3 url> [whisper model] [part]   part=meta|words1|words2 (words printed in halves to fit the 20 KB output cap)
set -e
U="$1"; M=${2:-small}; PART=${3:-meta}
cd /home/user
[ -s vo.mp3 ] || curl -sf -o vo.mp3 "$U"
if [ ! -s words.json ]; then
python3 - "$M" <<'PY'
import sys,json
from faster_whisper import WhisperModel
m=WhisperModel(sys.argv[1],device='cpu',compute_type='int8')
segs,info=m.transcribe('/home/user/vo.mp3',language='uk',word_timestamps=True,beam_size=1,vad_filter=False)
words=[{'w':w.word.strip(),'s':round(w.start,2),'e':round(w.end,2)} for s in segs for w in s.words]
json.dump(words,open('/home/user/words.json','w'),ensure_ascii=False,separators=(',',':'))
PY
fi
if [ "$PART" = meta ]; then
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 vo.mp3)
L=$(ffmpeg -nostats -i vo.mp3 -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|LRA:|Peak:" | tail -3 | tr -s ' ' | tr '\n' ' ')
G=$(ffmpeg -nostats -i vo.mp3 -af silencedetect=noise=-35dB:d=0.6 -f null - 2>&1 | grep -o "silence_duration: [0-9.]*" | awk '{print $2}' | sort -n | tail -5 | tr '\n' ' ')
N=$(python3 -c "import json;print(len(json.load(open('/home/user/words.json'))))")
echo "{\"dur\":$D,\"n_words\":$N,\"loud\":\"$L\",\"top_gaps\":\"$G\"}"
elif [ "$PART" = words1 ]; then
python3 -c "import json;w=json.load(open('/home/user/words.json'));print(json.dumps(w[:len(w)//2],ensure_ascii=False,separators=(',',':')))"
else
python3 -c "import json;w=json.load(open('/home/user/words.json'));print(json.dumps(w[len(w)//2:],ensure_ascii=False,separators=(',',':')))"
fi
