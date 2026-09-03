#!/usr/bin/env python3
"""OCR титров / детектор текста в кадре (tesseract ukr+eng).
--image f.png                → {"text":..., "has_text":bool, "boxes":n}
--video f.mp4 [--fps 4] [--band 0.55,0.95] [--tail 5] --out captions.json → по кадрам: t, text; сводка (count, median_hold, style)
Стиль титров: плашка (light_pill) vs без плашки, доля жёлтого (караоке), позиция центра по высоте."""
import json, os, re, sys, tempfile, statistics
sys.path.insert(0, os.path.dirname(__file__)); from common import *

def _ocr(img, lang="ukr+eng"):
    import pytesseract
    from PIL import Image, ImageOps
    im = img if not isinstance(img, str) else Image.open(img)
    g = ImageOps.grayscale(im)
    # два прохода: как есть и инверсия (тёмный текст на светлой плашке / светлый на тёмном)
    best = ""
    for cand in (g, ImageOps.invert(g)):
        t = pytesseract.image_to_string(cand, lang=lang, config="--psm 6")
        t = re.sub(r"[^\w\s'’ʼ-]", " ", t); t = re.sub(r"\s+", " ", t).strip()
        letters = re.findall(r"[A-Za-zА-Яа-яЁёІіЇїЄєҐґ]{3,}", t)
        if len(" ".join(letters)) > len(best): best = " ".join(letters)
    return best

def image_text(path):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    W, H = im.size
    txt = _ocr(im.resize((min(W, 1080), int(H * min(W, 1080) / W))))
    words = [w for w in txt.split() if len(w) >= 3]
    return {"text": " ".join(words), "has_text": len(words) >= 2, "n_words": len(words)}

def frame_style(im, band):
    """Признаки титра в полосе: светлая плашка? жёлтый (караоке)? центр по высоте."""
    import numpy as np
    W, H = im.size; y0, y1 = int(H * band[0]), int(H * band[1])
    a = np.asarray(im.convert("RGB").crop((0, y0, W, y1))).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    white = (r > 225) & (g > 225) & (b > 225)
    yellow = (r > 200) & (g > 170) & (b < 110)
    rows = white.mean(axis=1)
    pill_rows = np.where(rows > 0.45)[0]
    return {"white_frac": round(float(white.mean()), 4), "yellow_frac": round(float(yellow.mean()), 4),
            "light_pill": bool(len(pill_rows) > 8), "center_y_rel": round(float((y0 + (pill_rows.mean() if len(pill_rows) else (y1 - y0) / 2)) / H), 3)}

def video_captions(path, fps=4, band=(0.55, 0.95), tail=None):
    from PIL import Image
    d = duration(path); tmp = tempfile.mkdtemp()
    ss = [] if not tail else ["-ss", f"{max(0, d - tail):.3f}"]
    run(["ffmpeg", "-v", "error", "-y", *ss, "-i", path, "-vf", f"fps={fps}", os.path.join(tmp, "f%05d.png")])
    frames = sorted(os.listdir(tmp)); out = []; t0 = (d - tail) if tail else 0.0
    for k, f in enumerate(frames):
        im = Image.open(os.path.join(tmp, f)); W, H = im.size
        crop = im.crop((0, int(H * band[0]), W, int(H * band[1])))
        txt = _ocr(crop); st = frame_style(im, band)
        out.append({"t": round(t0 + k / fps, 3), "text": txt, **st})
    # сводка: группы одинакового текста
    groups = []; 
    for fr in out:
        if fr["text"] and (not groups or groups[-1]["text"] != fr["text"]): groups.append({"text": fr["text"], "start": fr["t"], "end": fr["t"]})
        elif fr["text"] and groups: groups[-1]["end"] = fr["t"]
    holds = [g["end"] - g["start"] + 1 / fps for g in groups]
    summary = {"count": len(groups), "per_min": round(len(groups) / max(d if not tail else tail, 1) * 60, 1),
               "median_hold": round(statistics.median(holds), 2) if holds else 0,
               "light_pill_frac": round(sum(1 for f in out if f["light_pill"]) / max(len(out), 1), 3),
               "karaoke_yellow_frac": round(sum(1 for f in out if f["yellow_frac"] > 0.002) / max(len(out), 1), 3),
               "center_y_rel_median": round(statistics.median([f["center_y_rel"] for f in out]), 3) if out else None,
               "words_per_card": round(statistics.mean([len(g["text"].split()) for g in groups]), 2) if groups else 0}
    return {"frames": out, "cards": groups, "summary": summary}

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        from PIL import Image, ImageDraw, ImageFont
        im = Image.new("RGB", (480, 854), (30, 30, 30)); dr = ImageDraw.Draw(im)
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
        dr.text((60, 500), "ШИЯ ВИДАЄ ВІК", font=f, fill=(255, 255, 255)); p = tempfile.mktemp(suffix=".png"); im.save(p)
        r = image_text(p); q = p.replace(".png", "_b.png"); Image.new("RGB", (480, 854), (30, 30, 30)).save(q); blank = image_text(q)
        sys.exit(ok(f"ocr='{r['text']}' blank_has_text={blank['has_text']}") if r["has_text"] and not blank["has_text"] else fail(f"{r} {blank}"))
    if "--image" in a: print(json.dumps(image_text(a[a.index("--image") + 1]), ensure_ascii=False)); sys.exit(0)
    if "--video" in a:
        v = a[a.index("--video") + 1]; fps = float(a[a.index("--fps") + 1]) if "--fps" in a else 4
        band = tuple(float(x) for x in a[a.index("--band") + 1].split(",")) if "--band" in a else (0.55, 0.95)
        tail = float(a[a.index("--tail") + 1]) if "--tail" in a else None
        r = video_captions(v, fps, band, tail)
        if "--out" in a: jdump(r, a[a.index("--out") + 1])
        print(json.dumps(r["summary"], ensure_ascii=False)); sys.exit(0)
    print(__doc__)
