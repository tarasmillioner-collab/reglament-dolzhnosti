# VSL_CLONE_FACTORY — CLAUDE.md

Конвейер: ДОНОР (чужой winner-ролик) → КЛОН на МОЙ продукт. Тот же ритм/структура/грамматика, мой продукт/аватар/рынок/язык.
Читай при старте: STATE.md (машинное состояние) → DIGEST.md (что сделано) → DECISIONS.md.

## Железные правила (R1–R9) — коротко
- R1 Видео-модель ТОЛЬКО seedance-2-mini (kie: `bytedance/seedance-2-mini`, higgsfield: `seedance_2_0_mini`), ТОЛЬКО 480p. Хук `.claude/hooks/gate_model.sh` блокирует всё остальное.
- R2 Gate 0: ничего не генерировать, пока 4 документа + сайт не прочитаны ПОЛНОСТЬЮ и не собран FACTS.md.
- R3 ROLES.md: DONOR = структура/ритм/грамматика; PRODUCT = факты/аватар/оффер. Хук `gate_roles.sh` блокирует донорский бренд/продукт/ингредиент в сценарии/промптах.
- R4 Ни одного факта без источника: claim → строка FACTS.md → документ/URL. Нет источника — claim удаляется.
- R5 Excerpt-first: ~40 с первого акта рендерится и судится ДО полного рендера.
- R6 Deliver-first: любой mp4 сначала в deliver/ как rcN. Красный gate после 2 попыток → запись в DIGEST, не третья попытка.
- R7 Аудио первым, целиком, одним куском; картинка режется под word-timestamps. Голос нарратора = пол аватара (женский).
- R8 Паспорта до картинок: ни одного стилла без паспорта персонажа/продукта/мира.
- R9 Дашборд `dashboard/index.html` (+ .md) обновляется после каждого этапа: `python3 dashboard/build_dashboard.py`.

## Этапы и петля
stage1 decode → stage2 facts → stage3 transplant → stage4 passports/stills → stage5 audio+excerpt → stage6 full.
Петля: generate → `python3 gates/<stage>.py` → судья (субагент из `.claude/agents/`, чистый контекст, видит только артефакт+паспорт+рубрику+отрезок донора) → чинить только items с pass=false → максимум 3 круга → красный = «red carried» в DIGEST.

## Где что лежит
- Входы: `targ.mp4` (донор, в корне), `gopure_docs/` (4 документа), PRODUCT_URL — см. ROLES.md.
- `work/stage1/DNA.md|DNA.json` · `work/stage2/FACTS` (корневой FACTS.md) + `work/stage2/product_photos/` · `work/stage3/TRANSPLANT.md, SCRIPT_uk.md, cards.json` · `work/stage4/passports/, stills/` · `work/stage5/vo.wav, words.json, timeline.json, excerpt/` · `work/stage6/`
- `deliver/` — excerpt_rcN.mp4, full_rcN.mp4, production_kit/
- `rubrics/` — бинарные чеклисты. `gates/` — детерминированные проверки. `tools/` — измерители/клиенты (каждый: `--selftest`).
- `COSTS.csv` — каждый вызов провайдера. Cap $30, стоп генерации на 80% ($24).
- `logs/` — джобы провайдера, чанки трансфера.

## Команды
```
python3 tools/selftest_all.py                 # все tools --selftest
python3 gates/stage1.py .. gates/stage6.py    # gate текущего этапа (exit 2 = блок)
python3 tools/cost_logger.py add --provider higgsfield --op video --units 5 --note "clip_03"
python3 tools/cost_logger.py status
python3 dashboard/build_dashboard.py
python3 tools/hf_transfer.py assemble logs/chunks/<name> deliver/<name>.mp4   # сборка base64-чанков из sandbox
```

## Провайдеры (см. DECISIONS.md D-03)
kie.ai ($KIE_API_KEY) и ElevenLabs ($ELEVENLABS_API_KEY) — клиенты в tools/, но в этой среде ключей нет и хосты закрыты egress-политикой.
Рабочий маршрут: Higgsfield MCP (seedance_2_0_mini 480p, nano_banana_pro, text2speech_v2/elevenlabs, sandbox_exec с ffmpeg+faster-whisper).
Локальная машина не может скачать ничего с CDN Higgsfield; файлы возвращаются base64-чанками через stdout sandbox (≤200 КБ/вызов) и собираются `tools/hf_transfer.py`.
Локальная машина → sandbox: push в этот публичный GitHub-репозиторий, sandbox тянет по raw.githubusercontent.com.
