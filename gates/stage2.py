#!/usr/bin/env python3
"""Gate 2 (Gate 0): FACTS.md ≥25 строк с источниками, скидка ≠ старая цена и арифметика, фото ≥3, ROLES.md заполнен."""
import os, re, sys; sys.path.insert(0, os.path.dirname(__file__)); from common import *
f = read("FACTS.md"); rows = [l for l in f.splitlines() if re.match(r"^\|\s*F-\d+\s*\|", l)]
with_src = [l for l in rows if len([c for c in l.split("|") if c.strip()]) >= 3 and re.search(r"(\bS\d+\b|drive|gopure|\.md|\.html|\.docx|\.pdf|http|Drive|landing|advertorial|MSDS|Stylebook|Карта|Аналіз|Исследование|VSL|статья|article)", l, re.I)]
ch = [("G2-1", len(rows) >= 25, f"строк FACTS: {len(rows)} (≥25)"), ("G2-2", len(with_src) == len(rows) and rows, f"строк с источником: {len(with_src)}/{len(rows)}")]
prices = {k: None for k in ("price_1","old_price_1","discount_1_pct")}
m = re.search(r"price_1\s*=\s*(\d+)", f); o = re.search(r"old_price_1\s*=\s*(\d+)", f); dsc = re.search(r"discount_1_pct\s*=\s*(\d+)", f)
if m and o and dsc:
    p, op, dp = int(m.group(1)), int(o.group(1)), int(dsc.group(1)); calc = round((op - p) / op * 100)
    ch.append(("G2-3", op > p and dp != op and abs(calc - dp) <= 1, f"цена {p}, старая {op}, скидка {dp}% (расчёт {calc}%)"))
else: ch.append(("G2-3", False, "в FACTS.md нет машинных полей price_1/old_price_1/discount_1_pct"))
ph = [x for x in os.listdir(P("work","stage2","product_photos")) if x.lower().endswith((".jpg",".png",".jpeg",".webp"))] if os.path.isdir(P("work","stage2","product_photos")) else []
ch.append(("G2-4", len(ph) >= 3, f"фото продукта: {len(ph)}"))
r = read("ROLES.md"); ch.append(("G2-5", all(k in r for k in ("DONOR","PRODUCT","MARKET")) and "Запрещённые" in r, "ROLES.md: DONOR/PRODUCT/MARKET + блок-лист"))
ch.append(("G2-6", all(k in f for k in ("Аватар","Avatar")) or "аватар" in f.lower(), "раздел аватара (пол/возраст/боли/слова) в FACTS"))
sys.exit(report("stage2", ch))
