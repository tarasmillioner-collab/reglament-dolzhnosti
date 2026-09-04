# Stage 5 — аудио + отрывок (excerpt_rc1)
- VO одним куском (R7): ElevenLabs через Higgsfield text2speech_v2, голос Elena (женский), job `432a6987…` → 224.96 с → `atempo=1.12` → 200.87 с (D-15); при сборке `loudnorm I=-16`.
- Слова: faster-whisper small (uk) на ускоренном файле → `words.json` (438 слов, числительные развёрнуты); раскладка карточек → `timeline.json` (80 карточек, 42 шота); караоке → `captions.ass`.
- Клипы отрывка: 16 шотов, seedance_2_0_mini 480p 9:16, start_image = стилл шота (`clips.json`); sh10 rc2 после ложного nsfw-флага провайдера.
- Сборка: `tools/sandbox/assemble.sh 0 41.98` в sandbox → `excerpt_rc1.mp4` (42.00 с, 5.7 МБ, sha 2da8bd0a5273c6ca) → загружен на CDN (`deliver/excerpt_rc1.url.md`).
- Проверка на том же файле в sandbox (`tools/sandbox/verify.sh`): `excerpt_metrics.json` — 480×854, −15.9 LUFS, пауз ≥0.6 с нет, дрейф титров медиана 20 мс; контакт-лист `excerpt_sheet.jpg` (1 кадр на шот) перенесён base64-чанками с проверкой sha.
- Файл в `deliver/` отсутствует: доставка с CDN в репо возможна только через workflow `fetch-assets` (D-16, QUESTIONS §8).
