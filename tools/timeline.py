#!/usr/bin/env python3
"""cards.json + words.json → timeline.json: каждой карточке — start/end по word-timestamps.
Сопоставление: последовательное fuzzy (difflib) по нормализованным словам; пропущенные слова интерполируются."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__)); from common import *
from difflib import SequenceMatcher

def norm(w): return re.sub(r"[^\w]", "", w.lower().replace("ʼ", "").replace("’", "").replace("'", ""))

def lay(cards, words, total_dur=None):
    tw = [norm(w["w"]) for w in words]; pos = 0; out = []
    for c in cards:
        cw = [norm(x) for x in c["text"].split() if norm(x)]
        best = None
        for k in range(pos, min(pos + 12, len(tw))):
            seg = tw[k:k + len(cw)]
            if not seg: break
            r = SequenceMatcher(None, " ".join(cw), " ".join(seg)).ratio()
            if best is None or r > best[0]: best = (r, k)
        if best and best[0] >= 0.5:
            k = best[1]; k2 = min(k + len(cw), len(words)) - 1
            s, e = words[k]["s"], words[k2]["e"]; pos = k2 + 1
            per_word = [(words[min(k + i, len(words) - 1)]["s"], words[min(k + i, len(words) - 1)]["e"]) for i in range(len(cw))]
        else:
            s = out[-1]["end"] if out else (words[0]["s"] if words else 0.0); e = s + 0.35 * len(cw); per_word = None
        out.append({**c, "start": round(s, 3), "end": round(e, 3), "words_t": per_word, "matched": bool(best and best[0] >= 0.5)})
    # монотонность + без дыр: конец = начало следующего
    for i in range(len(out) - 1):
        if out[i + 1]["start"] < out[i]["end"]: out[i + 1]["start"] = out[i]["end"]
        out[i]["end"] = out[i + 1]["start"]
    if total_dur and out: out[-1]["end"] = round(max(out[-1]["end"], total_dur), 3)
    return out

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        cards = [{"id": 1, "text": "шия видає вік"}, {"id": 2, "text": "а обличчя ні"}]
        words = [{"w": "Шия", "s": 0.1, "e": 0.4}, {"w": "видає", "s": 0.45, "e": 0.8}, {"w": "вік.", "s": 0.85, "e": 1.1}, {"w": "А", "s": 1.4, "e": 1.5}, {"w": "обличчя", "s": 1.55, "e": 2.0}, {"w": "ні", "s": 2.05, "e": 2.3}]
        t = lay(cards, words, 3.0)
        sys.exit(ok(f"{[(x['start'], x['end']) for x in t]}") if t[0]["start"] == 0.1 and t[1]["start"] == 1.4 and all(x["matched"] for x in t) else fail(str(t)))
    cards = json.load(open(a[0], encoding="utf-8")); words = json.load(open(a[1], encoding="utf-8"))["words"]
    dur = float(a[a.index("--dur") + 1]) if "--dur" in a else None
    t = lay(cards, words, dur); jdump(t, a[a.index("--out") + 1]); print(f"{len(t)} cards laid, unmatched={sum(1 for x in t if not x['matched'])}")
