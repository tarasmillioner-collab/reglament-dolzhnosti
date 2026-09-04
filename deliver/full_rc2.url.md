# full_rc2.mp4 (полный ролик, 0–199.79 с)
- Круг 2 (после judge-final rc1: E3/E6/E8/T10): ребаланс сценария (454 слова, c75 перед брендом, `work/stage3/rebalance_r2.json`), VO перезаписан одним куском (job `61353ea8…`, atempo 1.15 → 199.79 с = 194.49 +2.7%), новые words/timeline/captions, end card ретаймлен; перерендер шотов 5, 13, 14, 36, 40 (новые стиллы c08/c16/c17/c62 round 3).
- Собран в sandbox Higgsfield: `tools/sandbox/assemble.sh 0 199.79` — 43 сегмента / 42 шота (41 клип seedance_2_0_mini 480p + статичная end-card плита c77 с медленным наездом), VO loudnorm −16 LUFS, караоке-титры `work/stage5/captions.ass` + end card `work/stage6/endcard.ass` (цены/гарантия/COD из FACTS).
- ffprobe: h264 480×854, aac, 199.68 с; sha256[:16] = `e366f29fb8a75b3e`; 28 483 057 байт.
- Higgsfield media_id: `351e86d9-6cea-4524-930f-3522d81ed221`
- URL: https://d2ol7oe51mr4n9.cloudfront.net/user_39X4DueuoaObGccsCPKMarFan0M/351e86d9-6cea-4524-930f-3522d81ed221.mp4
- Чтобы положить файл в репо: GitHub → Actions → `fetch-assets` → Run workflow (ветка `claude/vsl-clone-factory-34f2yn`, urls = ссылка выше, dest = `deliver`), затем переименовать в `full_rc2.mp4`. Из сессии запуск невозможен (D-16).
