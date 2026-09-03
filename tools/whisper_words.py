#!/usr/bin/env python3
"""Word-timestamps через faster-whisper. Выход words.json: [{"w":..,"s":..,"e":..,"p":..}], wps, gaps.
python3 tools/whisper_words.py audio_or_video --out words.json [--lang uk|en] [--model small]
Если весов нет локально (HF закрыт) — печатает {"unavailable": true} и exit 3; тот же скрипт запускается в sandbox Higgsfield."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__)); from common import *

def to_wav(path):
    w = tempfile.mktemp(suffix=".wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", w]); return w

def transcribe(path, lang=None, model="small"):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, info = m.transcribe(to_wav(path), language=lang, word_timestamps=True, vad_filter=False)
    words = []
    for s in segs:
        for w in (s.words or []):
            words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)})
    return words, info.language

def stats(words, dur=None):
    if not words: return {"n_words": 0}
    span = (dur or words[-1]["e"]) - words[0]["s"]
    gaps = [round(words[i+1]["s"] - words[i]["e"], 3) for i in range(len(words) - 1)]
    return {"n_words": len(words), "first": words[0]["s"], "last": words[-1]["e"], "wps": round(len(words) / max(span, 0.1), 3),
            "wpm": round(len(words) / max(span, 0.1) * 60, 1), "max_gap": max(gaps) if gaps else 0, "gaps_over_1_2": sum(1 for g in gaps if g > 1.2)}

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        try:
            import faster_whisper  # noqa
        except Exception as e:
            sys.exit(fail(f"faster_whisper import: {e}"))
        s = stats([{"w": "a", "s": 0, "e": 0.3}, {"w": "b", "s": 0.5, "e": 0.9}, {"w": "c", "s": 2.5, "e": 2.9}])
        sys.exit(ok(f"import ok; stats {s}") if s["gaps_over_1_2"] == 1 and s["n_words"] == 3 else fail(str(s)))
    path = a[0]; lang = a[a.index("--lang") + 1] if "--lang" in a else None
    model = a[a.index("--model") + 1] if "--model" in a else "small"
    try:
        words, lng = transcribe(path, lang, model)
    except Exception as e:
        print(json.dumps({"unavailable": True, "error": str(e)[:200]})); sys.exit(3)
    out = {"language": lng, "words": words, "stats": stats(words, duration(path))}
    if "--out" in a: jdump(out, a[a.index("--out") + 1])
    print(json.dumps(out["stats"], ensure_ascii=False))
