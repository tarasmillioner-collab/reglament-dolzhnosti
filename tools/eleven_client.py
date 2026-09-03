#!/usr/bin/env python3
"""ElevenLabs: сплошной VO одним куском с посимвольным alignment (/with-timestamps) → wav + words.json.
Ключ $ELEVENLABS_API_KEY (sk_...). `--selftest` без ключа проверяет разбор alignment→слова."""
import base64, json, os, re, sys, subprocess, urllib.request
sys.path.insert(0, os.path.dirname(__file__)); from common import *; import cost_logger as CL
API = "https://api.elevenlabs.io/v1/text-to-speech"; MODEL = os.environ.get("EL_MODEL", "eleven_multilingual_v2")
VOICE = os.environ.get("EL_VOICE", "")  # женский украинский голос задаётся окружением

def key():
    v = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not v.startswith("sk_"): raise RuntimeError("ELEVENLABS_API_KEY отсутствует или это ID ключа, а не ключ (нужен sk_...)")
    return v

def align_to_words(text, chars, st, en):
    words = []; cur = ""; s0 = None
    for i, ch in enumerate(chars):
        if ch.isspace():
            if cur: words.append({"w": cur, "s": round(s0, 3), "e": round(en[i-1], 3)}); cur = ""; s0 = None
        else:
            if s0 is None: s0 = st[i]
            cur += ch
    if cur: words.append({"w": cur, "s": round(s0, 3), "e": round(en[-1], 3)})
    return words

def say_timed(text, out_wav, voice=None, stability=0.35, similarity=0.75, style=0.3, speed=1.0, label="vo"):
    body = {"text": text, "model_id": MODEL, "voice_settings": {"stability": stability, "similarity_boost": similarity, "style": style, "use_speaker_boost": True, "speed": speed}}
    req = urllib.request.Request(f"{API}/{voice or VOICE}/with-timestamps", data=json.dumps(body, ensure_ascii=False).encode(), headers={"xi-api-key": key(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r: d = json.loads(r.read())
    mp3 = out_wav + ".mp3"; open(mp3, "wb").write(base64.b64decode(d["audio_base64"]))
    run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ar", "44100", "-ac", "1", out_wav]); os.remove(mp3)
    al = d.get("alignment") or d["normalized_alignment"]
    words = align_to_words(text, al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"])
    CL.add("elevenlabs", "chars_1k", MODEL, len(text) / 1000, label)
    jdump({"words": words}, out_wav + ".words.json"); return out_wav, words

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ch = list("шия видає"); st = [i * 0.1 for i in range(len(ch))]; en = [i * 0.1 + 0.09 for i in range(len(ch))]
        w = align_to_words("шия видає", ch, st, en)
        sys.exit(ok(f"{w} key=" + ("set" if os.environ.get("ELEVENLABS_API_KEY") else "absent")) if len(w) == 2 and w[1]["w"] == "видає" else fail(str(w)))
    print(__doc__)
