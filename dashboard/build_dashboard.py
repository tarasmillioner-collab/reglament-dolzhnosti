#!/usr/bin/env python3
"""Собирает dashboard/index.html + dashboard/index.md из STATE.md, DIGEST.md, DECISIONS.md, COSTS.csv, logs/gate_*.json, logs/judge_*.json,
work/*/ (DNA, TRANSPLANT, SCRIPT, паспорта, prompts.json, стиллы), deliver/."""
import csv, glob, html, json, os, re, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def R(p):
    try: return open(os.path.join(ROOT, p), encoding="utf-8").read()
    except Exception: return ""
def J(p):
    try: return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))
    except Exception: return None
def esc(s): return html.escape(str(s))
def md_block(title, body): return f"\n## {title}\n\n{body}\n"
def pre(s): return f"<pre>{esc(s)}</pre>"

sections = []; md = [f"# VSL Clone Factory — dashboard ({time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())})\n"]
state = R("STATE.md"); sections.append(("STATE", pre(state))); md.append(md_block("STATE", f"```\n{state}```"))
costs = list(csv.DictReader(open(os.path.join(ROOT, "COSTS.csv"), encoding="utf-8"))) if os.path.exists(os.path.join(ROOT, "COSTS.csv")) else []
tot = sum(float(r["cost_usd"]) for r in costs)
ct = "<table><tr><th>ts</th><th>provider</th><th>op</th><th>model</th><th>units</th><th>usd</th><th>label</th></tr>" + "".join(f"<tr><td>{esc(r['ts'])}</td><td>{esc(r['provider'])}</td><td>{esc(r['op'])}</td><td>{esc(r['model'])}</td><td>{esc(r['units'])}</td><td>{esc(r['cost_usd'])}</td><td>{esc(r['label'])}</td></tr>" for r in costs) + "</table>"
sections.append((f"COSTS — ${tot:.2f} / $30 (стоп на $24)", ct)); md.append(md_block(f"COSTS — ${tot:.2f} / $30", "\n".join(f"- {r['ts']} {r['provider']} {r['op']} {r['model']} ×{r['units']} = ${r['cost_usd']} {r['label']}" for r in costs) or "—"))
for stage in range(1, 7):
    parts = []; mdp = []
    g = J(f"logs/gate_stage{stage}.json")
    if g:
        parts.append(f"<h4>Gate: {esc(g['verdict'])}</h4><ul>" + "".join(f"<li>{'✅' if i['pass'] else '❌'} <b>{esc(i['id'])}</b> {esc(i['evidence'])}</li>" for i in g["items"]) + "</ul>")
        mdp.append(f"Gate: **{g['verdict']}**\n" + "\n".join(f"- {'PASS' if i['pass'] else 'FAIL'} {i['id']}: {i['evidence']}" for i in g["items"]))
    for jf in sorted(glob.glob(os.path.join(ROOT, "logs", f"judge_stage{stage}_*.json"))):
        jj = J(os.path.relpath(jf, ROOT)) or {}
        parts.append(f"<h4>Судья {esc(os.path.basename(jf))}: {esc(jj.get('verdict'))}</h4><ul>" + "".join(f"<li>{'✅' if i.get('pass') else '❌'} <b>{esc(i.get('id'))}</b> {esc(i.get('evidence'))} <i>{esc(i.get('fix',''))}</i></li>" for i in jj.get("items", [])) + "</ul>" + (f"<p>top3: {esc(jj.get('top3_fixes'))}</p>" if jj.get("top3_fixes") else ""))
        mdp.append(f"Судья {os.path.basename(jf)}: **{jj.get('verdict')}**\n" + "\n".join(f"- {'PASS' if i.get('pass') else 'FAIL'} {i.get('id')}: {i.get('evidence')} → {i.get('fix','')}" for i in jj.get("items", [])))
    files = {1: ["work/stage1/DNA.md"], 2: ["FACTS.md"], 3: ["work/stage3/TRANSPLANT.md", "work/stage3/SCRIPT_uk.md"], 4: ["work/stage4/passports/heroine.md", "work/stage4/passports/product.md", "work/stage4/passports/world.md", "work/stage4/passports/extras.md"], 5: ["work/stage5/README.md"], 6: ["work/stage6/README.md"]}[stage]
    for f in files:
        t = R(f)
        if t: parts.append(f"<details><summary>{esc(f)}</summary>{pre(t)}</details>"); mdp.append(f"### {f}\n\n{t}")
    pj = J(f"work/stage{stage}/prompts.json")
    if pj:
        parts.append("<details><summary>Промпты (полные)</summary>" + "".join(f"<div class='p'><b>{esc(k)}</b>{pre(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, indent=1))}</div>" for k, v in (pj.items() if isinstance(pj, dict) else enumerate(pj))) + "</details>")
        mdp.append("### Промпты\n" + "\n".join(f"**{k}**\n```\n{v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, indent=1)}\n```" for k, v in (pj.items() if isinstance(pj, dict) else enumerate(pj))))
    imgs = sorted(glob.glob(os.path.join(ROOT, f"work/stage{stage}", "**", "*.png"), recursive=True) + glob.glob(os.path.join(ROOT, f"work/stage{stage}", "**", "*.jpg"), recursive=True))[:80]
    if imgs: parts.append("<div class='grid'>" + "".join(f"<figure><img src='../{esc(os.path.relpath(i, ROOT))}'><figcaption>{esc(os.path.basename(i))}</figcaption></figure>" for i in imgs) + "</div>"); mdp.append("Референсы/стиллы: " + ", ".join(os.path.relpath(i, ROOT) for i in imgs))
    if parts: sections.append((f"Stage {stage}", "".join(parts))); md.append(md_block(f"Stage {stage}", "\n\n".join(mdp)))
dl = sorted(os.listdir(os.path.join(ROOT, "deliver"))) if os.path.isdir(os.path.join(ROOT, "deliver")) else []
sections.append(("deliver/", "<ul>" + "".join(f"<li><a href='../deliver/{esc(f)}'>{esc(f)}</a></li>" for f in dl) + "</ul>")); md.append(md_block("deliver/", "\n".join(f"- {f}" for f in dl) or "—"))
for name in ("DIGEST.md", "DECISIONS.md", "QUESTIONS.md", "FEEDBACK_LOG.md"):
    sections.append((name, pre(R(name)))); md.append(md_block(name, R(name)))
page = "<!doctype html><meta charset='utf-8'><title>VSL Clone Factory</title><style>body{font:14px/1.45 system-ui;margin:24px;max-width:1200px;background:#fafafa}pre{white-space:pre-wrap;background:#fff;border:1px solid #ddd;padding:10px;font-size:12px}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:3px 6px;font-size:12px}.grid{display:flex;flex-wrap:wrap;gap:8px}figure{margin:0;width:140px}figure img{width:140px;border:1px solid #ccc}figcaption{font-size:10px}details{margin:6px 0}.p{margin:6px 0}h2{border-bottom:2px solid #333;margin-top:28px}</style>"
page += f"<h1>VSL Clone Factory — {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}</h1>" + "".join(f"<h2>{esc(t)}</h2>{b}" for t, b in sections)
os.makedirs(os.path.join(ROOT, "dashboard"), exist_ok=True)
open(os.path.join(ROOT, "dashboard", "index.html"), "w", encoding="utf-8").write(page); open(os.path.join(ROOT, "dashboard", "index.md"), "w", encoding="utf-8").write("\n".join(md))
print("dashboard ok:", len(page), "bytes")
