#!/usr/bin/env bash
# Выполняется в sandbox Higgsfield (sandbox_exec): whisper word-timestamps для файла по URL.
# usage: bash decode_remote.sh <media_url> <lang uk|en> <out.json>
set -e; URL="$1"; LANG="$2"; OUT="$3"
curl -sSL -o in.media "$URL"; ffmpeg -v error -y -i in.media -vn -ac 1 -ar 16000 in.wav
python3 - "$LANG" "$OUT" <<'PY'
import json, sys
from faster_whisper import WhisperModel
lang, out = sys.argv[1], sys.argv[2]
m = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = m.transcribe("in.wav", language=None if lang == "auto" else lang, word_timestamps=True, vad_filter=False)
words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)} for s in segs for w in (s.words or [])]
json.dump({"language": info.language, "words": words}, open(out, "w"), ensure_ascii=False)
print("WORDS", len(words), "LANG", info.language)
PY
