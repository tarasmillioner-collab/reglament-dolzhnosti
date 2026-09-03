#!/usr/bin/env bash
# Stop-хук: читает STATE.md, запускает gates/<stage>.py. exit 2 = блок с причиной.
# Не блокирует, если этап уже помечен как done/red_carried в STATE.md, или если stop_hook_active (защита от цикла).
INPUT=$(cat)
ROOT="${CLAUDE_PROJECT_DIR:-.}"
cd "$ROOT" || exit 0
echo "$INPUT" | grep -q '"stop_hook_active": *true' && exit 0
[ -f STATE.md ] || exit 0
STAGE=$(grep -E '^stage:' STATE.md | head -1 | sed 's/stage:[[:space:]]*//')
STATUS=$(grep -E '^status:' STATE.md | head -1 | sed 's/status:[[:space:]]*//')
case "$STATUS" in done|red_carried|delivered|building_pipeline|blocked_*) exit 0;; esac
case "$STAGE" in 1|2|3|4|5|6) ;; *) exit 0;; esac
if [ -f "gates/stage${STAGE}.py" ]; then
  OUT=$(python3 "gates/stage${STAGE}.py" 2>&1); RC=$?
  if [ $RC -eq 2 ]; then
    echo "[gate_stage] stage${STAGE} RED — нельзя останавливаться. Причина:" >&2
    echo "$OUT" | tail -20 >&2
    exit 2
  fi
fi
exit 0
