#!/usr/bin/env python3
"""Gate 1: DNA.json валиден, покрывает 100% таймлайна, каждый бит имеет роль. Если есть targ.mp4 — сверка с live-замером."""
import os, sys; sys.path.insert(0, os.path.dirname(__file__)); from common import *
ROLES = {"hook","problem","agitate","mechanism","proof","transformation","offer","price","urgency","callback","cta","cutaway","backstory","mentor","diagnosis","handover","resolution","brand"}
d = load_json("work/stage1/DNA.json"); ch = []
if not d: sys.exit(report("stage1", [("G1-1", False, "work/stage1/DNA.json отсутствует/невалиден")]))
req = ["duration_s","width","height","fps","source","scenes","cuts","speech","audio","captions","beats","sale_starts_s","enemy","audio_route"]
miss = [k for k in req if k not in d]; ch.append(("G1-1", not miss, f"обязательные поля: missing={miss}"))
sc = d.get("scenes", []); dur = float(d.get("duration_s", 0))
cov = ok_cov = False
if sc:
    gaps = [round(sc[i+1]["start"] - sc[i]["end"], 3) for i in range(len(sc)-1)]
    ok_cov = abs(sc[0]["start"]) < 0.05 and abs(sc[-1]["end"] - dur) < 0.5 and all(abs(g) < 0.05 for g in gaps)
ch.append(("G1-2", ok_cov, f"сцены покрывают таймлайн: n={len(sc)}, first={sc[0]['start'] if sc else None}, last={sc[-1]['end'] if sc else None}, dur={dur}"))
b = d.get("beats", []); badroles = [x.get("id") for x in b if x.get("role") not in ROLES]; nofields = [x.get("id") for x in b if not all(k in x for k in ("start","end","in_frame","belief"))]
ch.append(("G1-3", bool(b) and not badroles and not nofields, f"битов={len(b)}, без роли={badroles}, без полей={nofields}"))
bc = b and abs(b[0]["start"]) < 0.5 and abs(b[-1]["end"] - dur) < 1.0 and all(b[i+1]["start"] - b[i]["end"] < 0.6 for i in range(len(b)-1))
ch.append(("G1-4", bool(bc), "биты покрывают таймлайн без дыр"))
ch.append(("G1-5", d.get("audio_route") in ("suno-first","vo+bed"), f"audio_route={d.get('audio_route')} при speech.mode={d.get('speech',{}).get('mode')}"))
ch.append(("G1-6", isinstance(d.get("sale_starts_s"), (int,float)) and 0 < d["sale_starts_s"] < dur, f"sale_starts_s={d.get('sale_starts_s')}"))
live = os.path.exists(P("targ.mp4"))
ch.append(("G1-7", True if not live else bool(d.get("source",{}).get("live_measurement")), f"targ.mp4 {'есть' if live else 'НЕТ'} → source.live_measurement={d.get('source',{}).get('live_measurement')}"))
if live and d.get("source",{}).get("live_measurement"):
    import subprocess, json
    r = subprocess.run([sys.executable, P("tools","ffprobe_wrap.py"), P("targ.mp4")], capture_output=True, text=True); pr = json.loads(r.stdout)
    ch.append(("G1-8", within(pr["duration"], dur, 1), f"ffprobe dur {pr['duration']} vs DNA {dur}"))
sys.exit(report("stage1", ch))
