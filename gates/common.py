"""Общее для gates/: чтение STATE, FACTS, DNA; exit 2 = блок с причиной."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a): return os.path.join(ROOT, *a)
def load_json(p, default=None):
    try: return json.load(open(P(p), encoding="utf-8"))
    except Exception: return default
def read(p):
    try: return open(P(p), encoding="utf-8").read()
    except Exception: return ""
def facts_ids():
    return set(re.findall(r"^\|\s*(F-\d+)\s*\|", read("FACTS.md"), re.M))
def report(name, checks):
    """checks: list of (id, ok, evidence). Печатает и возвращает exit-код (0 или 2)."""
    bad = [c for c in checks if not c[1]]
    for cid, okk, ev in checks: print(f"{'PASS' if okk else 'FAIL'} {cid}: {ev}")
    print(f"== {name}: {'GREEN' if not bad else 'RED'} ({len(checks)-len(bad)}/{len(checks)})")
    out = {"gate": name, "verdict": "PASS" if not bad else "FAIL", "items": [{"id": c, "pass": o, "evidence": e} for c, o, e in checks]}
    os.makedirs(P("logs"), exist_ok=True); json.dump(out, open(P("logs", f"gate_{name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0 if not bad else 2
def within(a, b, pct): 
    try: return abs(float(a) - float(b)) <= pct / 100.0 * abs(float(b))
    except Exception: return False
