# goPure × OpenShorts: AI Shorts на Higgsfield

Демо-прогон [OpenShorts](https://github.com/mutonby/openshorts) (вкладка **AI Shorts**) для крема goPure Tighten & Lift. Генерация медиа идёт на Higgsfield, сборка роликов делается штатным пайплайном OpenShorts.

| Что | Модель |
|---|---|
| Фото героини, пэкшоты | Nano Banana Pro |
| Видео с украинской речью и b-roll | Gemini Omni Flash 1.1, 360p, 9:16 |
| Закадровый голос (ролик 2) | ElevenLabs v4, голос Elena |
| Сценарии и анализ | написаны вручную по брифам goPure (VSL v2, ресёрч рынка): ключа Gemini в среде нет |
| Субтитры, вставки b-roll, финальная сборка 1080×1920 | OpenShorts: faster-whisper + FFmpeg |

## Ролики

1. **Гравитаційна пастка** (UGC): героиня говорит в камеру, речь сгенерирована самим Omni Flash.
2. **Амазонський водяний магніт** (shock/discovery): озвучка ElevenLabs поверх сцен Omni Flash.
3. **Три роки під шарфом** (story): та же героиня, другая локация.

Сценарии, подписи и хэштеги лежат в `scripts.json`. Какие задания Higgsfield пошли в какой ролик, указано в `assets.json`.

## Что поменялось в OpenShorts (`openshorts-higgsfield.patch`)

- Новый режим видео **`higgsfield`** (бэкенд и дашборд). Ассеты, сгенерированные на Higgsfield, раскладываются в кэш пайплайна (`higgsfield_assets.py`). Ключи fal.ai и ElevenLabs в этом режиме не нужны. Стоимость показывается в кредитах.
- **Субтитры по сценарию.** Тайминг берётся у Whisper, а написание слов из сценария, поэтому бренд и украинские слова не искажаются.
- `WHISPER_LANGUAGE`: язык распознавания можно зафиксировать (`uk`).
- `AI_SHORTS_CAPTION_MARGIN_V`: субтитры можно поднять над нижней зоной, которую закрывает интерфейс TikTok и Reels.
- `serve_dashboard.py`: API и собранный дашборд на одном порту, когда Docker недоступен.

## Как запустить

```bash
bash run_sandbox.sh ~/gopure-run
```

Нужны python3 с faster-whisper, node с Playwright, ffmpeg и интернет. Скрипт:

1. ставит OpenShorts на зафиксированном коммите и накладывает патч;
2. собирает ассеты (`prepare_assets.py`), подгоняя тайминги вставок под реальную речь;
3. поднимает бэкенд и дашборд;
4. проходит мастер AI Shorts через Playwright по каждому сценарию (`drive_dashboard.cjs`), записывает экран и делает скриншоты.

Тяжёлые CV-зависимости (torch, YOLO, mediapipe) заменены заглушками в `stubs/`: AI Shorts их не использует.

> Все ролики сгенерированы ИИ. При публикации ставьте отметку «AI-generated» (TikTok, Instagram и YouTube этого требуют для реалистичных ИИ-людей). В подписи уже есть дисклеймер «Результати можуть відрізнятися».
