#!/usr/bin/env bash
# R1: только seedance-2-mini, только 480p — для ЛЮБОГО провайдера.
# Читает JSON вызова инструмента из stdin. exit 2 = блок с причиной.
INPUT=$(cat)
python3 - "$INPUT" <<'PY'
import json, re, sys
raw = sys.argv[1]
try:
    d = json.loads(raw)
except Exception:
    sys.exit(0)
tool = d.get("tool_name", "")
ti = d.get("tool_input", {}) or {}
blob = json.dumps(ti, ensure_ascii=False)
low = blob.lower()

def block(msg):
    print(f"[R1 gate_model] BLOCK: {msg}", file=sys.stderr)
    sys.exit(2)

# Область проверки: реальные вызовы генерации видео, а не тексты/тесты.
#  - MCP generate_video / generate_video_batch (Higgsfield и любой другой сервер)
#  - Bash, который вызывает провайдера: tools/kie_client.py video, curl api.kie.ai createTask, sandbox generate
# Write/Edit не проверяются: запись файла — не вызов провайдера.
if tool in ("Write", "Edit", "MultiEdit", "Read"):
    sys.exit(0)
is_video = tool.endswith("generate_video") or tool.endswith("generate_video_batch")
if tool == "Bash":
    cmd = (ti.get("command") or "").lower()
    is_video = any(k in cmd for k in ("kie_client.py video", "kie_client.py --video", "api.kie.ai/api/v1/jobs", "createtask", "generate_video"))
if not is_video:
    sys.exit(0)

# Разрешённые идентификаторы модели
ALLOWED = ("bytedance/seedance-2-mini", "seedance_2_0_mini", "seedance-2-mini", "seedance-2.0-mini")
models = re.findall(r'"model"\s*:\s*"([^"]+)"', blob)
for m in models:
    if m.lower() not in ALLOWED:
        block(f"model='{m}' — разрешён только seedance-2-mini ({', '.join(ALLOWED)})")
if not models and any(k in low for k in ("seedance_2_0\"", "seedance_2_5", "seedance1_5", "seedance-1", "kling", "veo", "sora", "runway", "hailuo", "luma")):
    block("упомянута не-seedance-2-mini видео-модель")

# Разрешённое разрешение
res = re.findall(r'"resolution"\s*:\s*"([^"]+)"', blob)
for r in res:
    if r.lower() != "480p":
        block(f"resolution='{r}' — разрешено только 480p")
if any(k in low for k in ("720p", "1080p", "\"4k\"", "2k")):
    block("в вызове встречается 720p/1080p/4k — разрешено только 480p")
if models and not res:
    block("видео-вызов без явного resolution=480p")
sys.exit(0)
PY
