---
name: stage1-decode
description: Этап 1 — DECODE донора в ДНК измерением (ffprobe, scene cuts, whisper word-timestamps, BPM/pitch, OCR титров, бит-лист с ролями). Выход work/stage1/DNA.md + DNA.json.
---
# Stage 1 — DECODE
1. `python3 tools/ffprobe_wrap.py targ.mp4` → длительность, WxH, fps.
2. `python3 tools/scene_cuts.py targ.mp4 --out work/stage1/cuts.json` → сцены, средняя/медианная длина, распределение по актам.
3. `python3 tools/whisper_words.py targ.mp4 --out work/stage1/words.json` (локально весов нет → запусти тот же скрипт в sandbox Higgsfield: см. tools/sandbox/decode_remote.sh).
4. `python3 tools/audio_measure.py targ.mp4 --out work/stage1/audio.json` → спето/сказано (pitch variance), BPM, LUFS, паузы.
5. `python3 tools/caption_ocr.py --video targ.mp4 --out work/stage1/captions.json` → стиль, тайминг, караоке или нет.
6. Собери бит-лист руками из транскрипта + кадров: каждый бит = таймкод, роль (hook/problem/agitate/mechanism/proof/transformation/offer/price/urgency/callback/CTA), что в кадре, какое убеждение ставит. Зафиксируй секунду начала продажи, объект-«враг» и сколько кадров он занимает.
7. Запиши DNA.json по схеме `gates/schemas/dna.schema.json`, DNA.md — человеческая версия. `python3 gates/stage1.py`.
8. Дефолт аудио-маршрута: спето → Suno-first; сказано → сплошной VO + бед под BPM.

## Gotchas: как этот этап обычно ломается
- Scene detect на 0.3 режет фейды дважды и пропускает мягкие переходы — сверяй число сцен с глазами по контакт-листу (`tools/scene_cuts.py --sheet`).
- Whisper на песне даёт слова с дрейфом до 0.5 с; для песни используй `--vad off` и сверяй с энергией.
- BPM на VO-миксе врёт вдвое (половинный темп) — считать по HPSS-перкуссии, не по автокорреляции.
- OCR титров: белая плашка + тёмный текст требует инверсии; без неё «нет титров».
- Бит-лист без ролей = красный gate: каждой сцене нужна роль, даже если «cutaway».
- Если файла донора нет — НЕ выдумывать цифры; использовать только архивные замеры с пометкой источника и статусом red_carried.
