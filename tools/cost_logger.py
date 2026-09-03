#!/usr/bin/env python3
"""COSTS.csv: каждый вызов провайдера. Cap $30, стоп генерации на 80%.
add --provider higgsfield --op video|image|tts|suno --model X --units N --label L [--note ...]
status | can_spend <usd> (exit 2 если превысит 80%) | --rate <usd_per_credit>"""
import csv, json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__)); from common import *
CSV = os.path.join(ROOT, "COSTS.csv"); STATE = os.path.join(ROOT, "STATE.md")
RATES = {  # usd за единицу
    ("higgsfield", "video"): 0.01, ("higgsfield", "image"): 0.01, ("higgsfield", "tts"): 0.01, ("higgsfield", "credit"): 0.01,
    ("kie", "video_sec_480p"): 0.0258, ("kie", "image"): 0.04, ("kie", "suno"): 0.06, ("elevenlabs", "chars_1k"): 0.09}
CAP = 30.0; STOP_AT = 0.8

def rows():
    if not os.path.exists(CSV): return []
    return list(csv.DictReader(open(CSV, encoding="utf-8")))

def total(): return round(sum(float(r["cost_usd"]) for r in rows()), 4)

def add(provider, op, model, units, label, note="", unit_cost=None):
    uc = unit_cost if unit_cost is not None else RATES.get((provider, op), RATES.get((provider, "credit"), 0.01))
    cost = round(float(units) * uc, 4); cum = round(total() + cost, 4)
    new = not os.path.exists(CSV) or os.path.getsize(CSV) == 0
    with open(CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new: w.writerow(["ts", "provider", "op", "model", "units", "unit_cost_usd", "cost_usd", "cumulative_usd", "label", "note"])
        w.writerow([time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), provider, op, model, units, uc, cost, cum, label, note])
    _sync_state(cum); return cum

def _sync_state(cum):
    if not os.path.exists(STATE): return
    lines = open(STATE, encoding="utf-8").read().splitlines()
    lines = [f"spent_usd: {cum:.2f}" if l.startswith("spent_usd:") else l for l in lines]
    open(STATE, "w", encoding="utf-8").write("\n".join(lines) + "\n")

def can_spend(usd):
    return total() + usd <= CAP * STOP_AT

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        import tempfile; CSV = tempfile.mktemp(suffix=".csv"); STATE = "/nonexistent"
        add("higgsfield", "video", "seedance_2_0_mini", 5, "t1"); add("higgsfield", "image", "nano_banana_pro", 2, "t2")
        sys.exit(ok(f"total={total()} can_spend(23)={can_spend(23)}") if abs(total() - 0.07) < 1e-6 and not can_spend(24) else fail(str(total())))
    if not a or a[0] == "status":
        t = total(); print(json.dumps({"spent_usd": t, "cap": CAP, "stop_at_usd": CAP * STOP_AT, "remaining_to_stop": round(CAP * STOP_AT - t, 4), "n_calls": len(rows())})); sys.exit(0)
    if a[0] == "can_spend":
        okk = can_spend(float(a[1])); print("OK" if okk else "STOP: 80% budget"); sys.exit(0 if okk else 2)
    if a[0] == "add":
        g = lambda k, d=None: a[a.index(k) + 1] if k in a else d
        cum = add(g("--provider"), g("--op"), g("--model", ""), float(g("--units", 1)), g("--label", ""), g("--note", ""), float(g("--unit-cost")) if g("--unit-cost") else None)
        print(f"cumulative_usd={cum}"); sys.exit(0 if cum <= CAP * STOP_AT else 2)
