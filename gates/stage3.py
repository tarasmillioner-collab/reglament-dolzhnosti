#!/usr/bin/env python3
"""Gate 3: TRANSPLANT.md таблица; SCRIPT_uk слов = донор ±10%; cards.json: hot-слово, claims F-NN существуют, блок-лист, продукт только в мире героя, враг ≤12 кадров, доля актов ±5%."""
import json, os, re, sys; sys.path.insert(0, os.path.dirname(__file__)); from common import *
d = load_json("work/stage1/DNA.json", {}); tr = read("work/stage3/TRANSPLANT.md"); sc = read("work/stage3/SCRIPT_uk.md"); cards = load_json("work/stage3/cards.json", [])
ch = []
ch.append(("G3-1", tr.count("|") > 40 and "таймкод" in tr.lower(), f"TRANSPLANT.md таблица: {tr.count(chr(10))} строк"))
words = len(re.findall(r"[\w'’ʼ-]+", re.sub(r"\[[^\]]*\]|#.*|\*\*|F-\d+", " ", sc)))
dw = d.get("speech", {}).get("words", 0); ch.append(("G3-2", within(words, dw, 10) if dw else words > 0, f"слов в SCRIPT_uk={words}, донор={dw} (±10%)"))
ch.append(("G3-3", bool(cards) and all(c.get("hot") and c.get("hot").lower() in c.get("text","").lower() for c in cards), f"карточек={len(cards)}, все с hot-словом в тексте"))
fids = facts_ids(); used = set(re.findall(r"F-\d+", sc + tr + json.dumps(cards, ensure_ascii=False))); missing = sorted(used - fids)
ch.append(("G3-4", not missing and bool(used), f"claims: использовано {len(used)} F-NN, нет в FACTS: {missing}"))
bl = [t.strip().lower() for t in read("gates/donor_blocklist.txt").splitlines() if t.strip() and not t.startswith("#")]; fl = read("FACTS.md").lower()
hits = [t for t in bl if t not in fl and re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", (sc + tr + json.dumps(cards, ensure_ascii=False)).lower())]
ch.append(("G3-5", not hits, f"донорские токены: {hits}"))
bad_pv = [c.get("id") for c in cards if c.get("product_visible") and c.get("world") != "hero"]
ch.append(("G3-6", not bad_pv, f"продукт/оффер вне мира героини: {bad_pv}"))
enemy = sum(1 for c in cards if c.get("enemy_in_frame")); ch.append(("G3-7", enemy <= 12, f"кадров с врагом: {enemy} (≤12)"))
ss = d.get("sale_starts_s"); cs = next((c.get("t_start") for c in cards if c.get("role") in ("offer","brand","price") and c.get("t_start") is not None), None)
ch.append(("G3-8", cs is not None and ss and within(cs, ss, 5), f"начало продажи: клон {cs} vs ДНК {ss} (±5%)"))
roles = {c.get("role") for c in cards}; need = {"hook","proof","transformation","price","urgency","callback","cta"}
ch.append(("G3-9", need <= roles, f"роли в карточках: нет {sorted(need - roles)}"))
sys.exit(report("stage3", ch))
