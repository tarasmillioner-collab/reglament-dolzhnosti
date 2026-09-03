---
name: stage6-assemble
description: Этап 6 — полный рендер оставшихся карточек, сборка deliver/full_rc1.mp4, end card COD, полировка по rc, judge-final, production_kit.
---
# Stage 6 — FULL
1. Те же шаги 5c на оставшиеся карточки, батчами ≤12 клипов (generate_video_batch), стоп при 80% бюджета.
2. End card (последние ~5 с): цена, кнопка «Замовити», гарантия 60 днів, «Оплата при отриманні · Нова Пошта». Только в мире героини/на карточке, не в cutaway.
3. `tools/assemble.py --full` → deliver/full_rc1.mp4 (deliver-first!). `python3 gates/stage6.py` → judge-final → правки = новый rc. ≤2 ч полировки.
4. production_kit/: DNA, TRANSPLANT, SCRIPT_uk, паспорта, все промпты (work/stage4/prompts.json, work/stage5/clip_prompts.json), аудио, тайминги, субтитры .ass. Дашборд, DIGEST, раздел «Rubric additions».

## Gotchas
- Хвост ролика (оффер/CTA) — самое дорогое место для обрыва по бюджету: рендерить оффер-карточки раньше середины (см. pricing.md из vsl-reverse-engineer: срыв на $25.3).
- Длительность = донор ±5%: пересчитывать после каждого трима клипов, не по плану.
- Караоке на 194 с — сотни PNG-состояний; использовать .ass с \k-тегами, а не overlay PNG.
- LUFS мерить на финальном миксе, не на VO.
- F3: любая строка FEEDBACK_LOG в not-done без причины = FAIL.
