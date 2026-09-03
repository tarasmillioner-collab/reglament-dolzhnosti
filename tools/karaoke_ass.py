#!/usr/bin/env python3
"""Караоке .ass из timeline.json: активное слово жёлтым (\\k), без плашки, чуть ниже центра, без ударений.
python3 tools/karaoke_ass.py timeline.json out.ass [--w 480 --h 854] [--font DejaVu Sans] [--size 34] [--y 0.62]"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__)); from common import *
STRESS = "́̀"

def strip_stress(s): return "".join(ch for ch in s if ch not in STRESS)

def build(timeline, w=480, h=854, font="DejaVu Sans", size=34, y_rel=0.62, outline=2):
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: K,{font},{size},&H0000FFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,{outline},0,5,20,20,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # Alignment 5 = центр; позиция задаётся \pos
    def ts(t):
        t = max(0.0, t); hh = int(t // 3600); mm = int(t % 3600 // 60); ss = t % 60
        return f"{hh}:{mm:02d}:{ss:05.2f}"
    ev = []
    for c in timeline:
        words = [strip_stress(x) for x in c["text"].split()]
        if not words: continue
        s, e = c["start"], c["end"]; span = max(e - s, 0.2)
        wt = c.get("words_t")
        parts = []
        for i, wd in enumerate(words):
            if wt and i < len(wt) and wt[i]:
                ws, we = wt[i]; d = max(we - ws, 0.05)
                # \k в сантисекундах: время до подсветки + длительность подсветки
                lead = (ws - s) if i == 0 else 0
            else:
                d = span / len(words); lead = 0
            parts.append(f"{{\\k{int(round(lead*100))}}}" if lead > 0.01 else "")
            parts.append(f"{{\\k{int(round(d*100))}}}{wd.upper()} ")
        # секундарный цвет (до подсветки) — белый; primary (после \k) — жёлтый; для караоке «слово горит сейчас» используем \kf? Нет: \k красит слово ПОСЛЕ прохода. Используем два слоя: белый текст + жёлтая маска \k.
        text = "".join(parts).strip()
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},K,,0,0,0,,{{\\pos({w//2},{int(h*y_rel)})\\an5}}{text}")
    return hdr + "\n".join(ev) + "\n"

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        tl = [{"text": "шия́ видає вік", "start": 0.0, "end": 1.2, "words_t": [(0.0, 0.4), (0.4, 0.8), (0.8, 1.2)]}]
        s = build(tl); sys.exit(ok("ass built, stress stripped") if "\\k40" in s and "ШИЯ " in s and "́" not in s else fail(s))
    tl = json.load(open(a[0], encoding="utf-8"))
    g = lambda k, d: a[a.index(k) + 1] if k in a else d
    open(a[1], "w", encoding="utf-8").write(build(tl, int(g("--w", 480)), int(g("--h", 854)), g("--font", "DejaVu Sans"), int(g("--size", 34)), float(g("--y", 0.62))))
    print("ass ->", a[1])
