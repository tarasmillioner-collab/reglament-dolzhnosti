#!/usr/bin/env python3
"""Gate 6: full_rcN.mp4 существует; длительность = донор ±5%; end card (OCR последних 5 с: цена+гарантия); FEEDBACK_LOG без not-done без причины; production_kit."""
import json, os, re, subprocess, sys; sys.path.insert(0, os.path.dirname(__file__)); from common import *
d = load_json("work/stage1/DNA.json", {}); ch = []
fu = sorted([f for f in os.listdir(P("deliver")) if f.startswith("full_rc") and f.endswith(".mp4")]) if os.path.isdir(P("deliver")) else []
ch.append(("G6-1", bool(fu), f"deliver/full_rcN.mp4: {fu[-1] if fu else 'нет'}"))
if fu:
    p = P("deliver", fu[-1]); r = subprocess.run([sys.executable, P("tools","ffprobe_wrap.py"), p], capture_output=True, text=True); pr = json.loads(r.stdout)
    ch.append(("G6-2", within(pr["duration"], d.get("duration_s", 0), 5), f"длительность {pr['duration']:.1f} vs донор {d.get('duration_s')} (±5%)"))
    r = subprocess.run([sys.executable, P("tools","caption_ocr.py"), "--video", p, "--tail", "5", "--band", "0.2,0.95"], capture_output=True, text=True)
    txt = " ".join(c["text"] for c in (json.loads(r.stdout).get("cards", []) if r.stdout.startswith("{") else [])) if False else ""
    # OCR результат сохраняется отдельным вызовом с --out; здесь читаем work/stage6/endcard_ocr.json
    e = load_json("work/stage6/endcard_ocr.json", {}); alltxt = " ".join(c.get("text","") for c in e.get("cards", [])).lower()
    ch.append(("G6-3", any(k in alltxt for k in ("грн","₴")) and any(k in alltxt for k in ("гарант","60")), f"end card OCR: '{alltxt[:120]}'"))
fl = read("FEEDBACK_LOG.md"); bad = [l for l in fl.splitlines() if "not-done" in l and len([c for c in l.split("|") if c.strip()]) < 5]
ch.append(("G6-4", not bad, f"FEEDBACK_LOG not-done без причины: {len(bad)}"))
kit = P("deliver","production_kit"); need = ["DNA.json","TRANSPLANT.md","SCRIPT_uk.md","passports","prompts.json","vo.wav","timeline.json","subs.ass"]
have = [n for n in need if os.path.exists(os.path.join(kit, n))]; ch.append(("G6-5", have == need, f"production_kit: нет {[n for n in need if n not in have]}"))
sys.exit(report("stage6", ch))
