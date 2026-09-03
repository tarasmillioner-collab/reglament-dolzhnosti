#!/usr/bin/env python3
"""Gate 5: 5a VO длительность = донор ±5%, слов/сек ±10%, max gap ≤1.2, LUFS −16±1; 5b timeline; 5c excerpt существует, титры синхронны (дрейф ≤100 мс по OCR-выборке)."""
import json, os, subprocess, sys; sys.path.insert(0, os.path.dirname(__file__)); from common import *
d = load_json("work/stage1/DNA.json", {}); a = load_json("work/stage5/audio.json", {}); w = load_json("work/stage5/words.json", {}); ch = []
dur = d.get("duration_s", 0); ch.append(("G5-1", bool(a) and within(a.get("duration", 0), dur, 5), f"VO {a.get('duration')}s vs донор {dur}s (±5%)"))
wps = (w.get("stats") or {}).get("wps"); dwps = (d.get("speech") or {}).get("wps"); ch.append(("G5-2", wps and dwps and within(wps, dwps, 10), f"слов/сек {wps} vs ДНК {dwps} (±10%)"))
ch.append(("G5-3", bool(a) and a.get("max_gap", 9) <= 1.2, f"max gap {a.get('max_gap')} (≤1.2)"))
ch.append(("G5-4", bool(a) and abs(a.get("lufs", 0) + 16) <= 1.0, f"LUFS {a.get('lufs')} (−16±1)"))
tl = load_json("work/stage5/timeline.json", []); ch.append(("G5-5", bool(tl) and all(c.get("matched") for c in tl[:20]), f"timeline: {len(tl)} карточек, unmatched первых 20 = {sum(1 for c in tl[:20] if not c.get('matched'))}"))
ex = sorted([f for f in os.listdir(P("deliver")) if f.startswith("excerpt_rc") and f.endswith(".mp4")]) if os.path.isdir(P("deliver")) else []
ch.append(("G5-6", bool(ex), f"deliver/excerpt_rcN.mp4: {ex[-1] if ex else 'нет'}"))
if ex:
    p = P("deliver", ex[-1]); r = subprocess.run([sys.executable, P("tools","ffprobe_wrap.py"), p], capture_output=True, text=True); pr = json.loads(r.stdout)
    ch.append(("G5-7", pr["w"] == 480 or pr["h"] == 854 or pr["w"] <= 486, f"excerpt {pr['w']}x{pr['h']} {pr['duration']:.1f}s"))
    sync = load_json("work/stage5/caption_sync.json", {}); ch.append(("G5-8", sync.get("median_drift_ms", 999) <= 100, f"дрейф титров медиана {sync.get('median_drift_ms')} мс (≤100)"))
sys.exit(report("stage5", ch))
