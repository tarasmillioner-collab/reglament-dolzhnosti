#!/usr/bin/env python3
"""Gate 4: каждый стилл в stills.json привязан к паспорту; OCR — нет текста в кадре; glitch_detect — нет флагов; паспорта существуют."""
import json, os, subprocess, sys; sys.path.insert(0, os.path.dirname(__file__)); from common import *
ch = []; pp = P("work","stage4","passports")
need = ["heroine.md","product.md","world.md","extras.md"]; have = [f for f in need if os.path.exists(os.path.join(pp, f))]
ch.append(("G4-1", have == need, f"паспорта: {have}"))
st = load_json("work/stage4/stills.json", []); ch.append(("G4-2", bool(st), f"stills.json: {len(st)} стиллов"))
nop = [s.get("card") for s in st if not s.get("passports") or not s.get("path")]; ch.append(("G4-3", not nop, f"стиллы без паспорта/пути: {nop}"))
txt = []; gl = []
for s in st:
    p = P(s["path"]) if not os.path.isabs(s.get("path","")) else s["path"]
    if not os.path.exists(p): txt.append(f"{s.get('card')}:missing"); continue
    if s.get("ocr_checked") and s.get("glitch_checked"):  # результаты уже записаны
        if s.get("ocr_has_text"): txt.append(s.get("card"))
        if s.get("glitch_flags"): gl.append(s.get("card"))
        continue
    r = subprocess.run([sys.executable, P("tools","caption_ocr.py"), "--image", p], capture_output=True, text=True); o = json.loads(r.stdout or "{}")
    if o.get("has_text") and not s.get("text_allowed"): txt.append(s.get("card"))
    r = subprocess.run([sys.executable, P("tools","glitch_detect.py"), "--image", p], capture_output=True, text=True); g = json.loads(r.stdout or "{}")
    if g.get("flags"): gl.append(f"{s.get('card')}:{g['flags']}")
ch.append(("G4-4", not txt, f"текст в кадре (OCR): {txt}")); ch.append(("G4-5", not gl, f"глитчи: {gl}"))
cards = load_json("work/stage3/cards.json", []); key = [c["id"] for c in cards if c.get("key_frame")]; done = {s.get("card") for s in st}
ch.append(("G4-6", all(k in done for k in key), f"key frames без стилла: {[k for k in key if k not in done]}"))
sys.exit(report("stage4", ch))
