#!/usr/bin/env bash
# R3: донорский бренд/продукт/ингредиент не должен попасть в сценарии/промпты/deliver.
# Проверяет Write/Edit в work/stage3..6, deliver/ и промпты generate_*.
INPUT=$(cat)
python3 - "$INPUT" <<'PY'
import json, os, re, sys
try:
    d = json.loads(sys.argv[1])
except Exception:
    sys.exit(0)
tool = d.get("tool_name", ""); ti = d.get("tool_input", {}) or {}
root = os.environ.get("CLAUDE_PROJECT_DIR", ".")
bl_path = os.path.join(root, "gates", "donor_blocklist.txt")
facts_path = os.path.join(root, "FACTS.md")
if not os.path.exists(bl_path):
    sys.exit(0)
tokens = [t.strip() for t in open(bl_path, encoding="utf-8") if t.strip() and not t.startswith("#")]
facts = open(facts_path, encoding="utf-8").read().lower() if os.path.exists(facts_path) else ""
tokens = [t for t in tokens if t.lower() not in facts]

text = ""
path = ti.get("file_path") or ti.get("path") or ""
if tool in ("Write", "Edit"):
    scoped = any(s in path for s in ("work/stage3", "work/stage4", "work/stage5", "work/stage6", "deliver/"))
    if not scoped:
        sys.exit(0)
    text = (ti.get("content") or "") + " " + (ti.get("new_string") or "")
elif "generate_" in tool:
    text = json.dumps(ti, ensure_ascii=False)
elif tool == "Bash":
    cmd = ti.get("command", "")
    if not any(s in cmd for s in ("work/stage3", "work/stage4", "work/stage5", "work/stage6", "deliver/")):
        sys.exit(0)
    text = cmd
else:
    sys.exit(0)
low = text.lower()
hits = [t for t in tokens if re.search(r'(?<![\w])' + re.escape(t.lower()) + r'(?![\w])', low)]
if hits:
    print(f"[R3 gate_roles] BLOCK: донорские токены {hits} в {path or tool}. Клон использует только FACTS.md.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
PY
