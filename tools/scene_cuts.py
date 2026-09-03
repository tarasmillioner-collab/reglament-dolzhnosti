#!/usr/bin/env python3
"""Scene cut detector: ffmpeg scene-score + гистограммный детектор (cv2) как второй голос.
Выход: cuts (сек), scenes [{i,start,end,len}], avg/median len, распределение по актам.
python3 tools/scene_cuts.py video.mp4 --out cuts.json [--thr 0.3] [--sheet sheet.jpg] [--acts 0,40,120,194]"""
import json, os, re, sys, tempfile, statistics
sys.path.insert(0, os.path.dirname(__file__)); from common import *

def ffmpeg_cuts(path, thr=0.3):
    r = run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"], check=False)
    ts = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    return sorted(set(round(t, 3) for t in ts))

def hist_cuts(path, thr=0.45, step=2):
    try:
        import cv2, numpy as np
    except Exception:
        return None
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS) or 30
    prev = None; cuts = []; i = 0
    while True:
        okf, fr = cap.read()
        if not okf: break
        if i % step == 0:
            small = cv2.resize(fr, (96, 160)); hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
            h = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256]); cv2.normalize(h, h)
            if prev is not None:
                d = 1 - cv2.compareHist(prev, h, cv2.HISTCMP_CORREL)
                if d > thr: cuts.append(round(i / fps, 3))
            prev = h
        i += 1
    cap.release()
    # схлопнуть соседние (<0.4 с)
    out = []
    for c in cuts:
        if not out or c - out[-1] > 0.4: out.append(c)
    return out

def scenes_from_cuts(cuts, dur):
    b = [0.0] + [c for c in cuts if 0.2 < c < dur - 0.2] + [dur]
    sc = [{"i": i, "start": round(b[i], 3), "end": round(b[i+1], 3), "len": round(b[i+1] - b[i], 3)} for i in range(len(b) - 1)]
    return sc

def analyze(path, thr=0.3, acts=None):
    dur = duration(path)
    c1 = ffmpeg_cuts(path, thr); c2 = hist_cuts(path)
    cuts = c1
    if c2 is not None:
        # объединение: берём ffmpeg, добавляем hist-cuts, которых нет в ±0.5 с
        for c in c2:
            if all(abs(c - x) > 0.5 for x in cuts): cuts.append(c)
        cuts = sorted(cuts)
    sc = scenes_from_cuts(cuts, dur)
    lens = [s["len"] for s in sc]
    out = {"duration": round(dur, 3), "n_scenes": len(sc), "cuts": cuts, "scenes": sc,
           "avg_len": round(sum(lens) / len(lens), 3), "median_len": round(statistics.median(lens), 3),
           "cuts_per_min": round(len(cuts) / dur * 60, 2), "under3s": sum(1 for l in lens if l < 3),
           "sigma": round(statistics.pstdev(lens), 3) if len(lens) > 1 else 0.0}
    if acts:
        out["acts"] = []
        for i in range(len(acts) - 1):
            a, b = acts[i], acts[i+1]
            ls = [s["len"] for s in sc if s["start"] >= a and s["start"] < b]
            out["acts"].append({"from": a, "to": b, "n": len(ls), "avg_len": round(sum(ls)/len(ls), 3) if ls else None})
    return out

def sheet(path, scenes, out, cols=6):
    from PIL import Image
    tiles = []
    for s in scenes:
        f = tempfile.mktemp(suffix=".jpg")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s['start'] + min(0.3, s['len']/2):.3f}", "-i", path, "-frames:v", "1", "-vf", "scale=180:-1", f])
        tiles.append((s, Image.open(f)))
    if not tiles: return
    w, h = tiles[0][1].size; rows = (len(tiles) + cols - 1) // cols
    im = Image.new("RGB", (cols * w, rows * h), "black")
    for k, (s, t) in enumerate(tiles): im.paste(t, ((k % cols) * w, (k // cols) * h))
    im.save(out)

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        p = synth_video(tempfile.mktemp(suffix=".mp4"), seconds=6, scenes=3)
        r = analyze(p)
        sys.exit(ok(f"{r['n_scenes']} scenes, cuts={r['cuts']}") if r["n_scenes"] == 3 else fail(json.dumps(r)))
    a = sys.argv[1:]; path = a[0]
    thr = float(a[a.index("--thr") + 1]) if "--thr" in a else 0.3
    acts = [float(x) for x in a[a.index("--acts") + 1].split(",")] if "--acts" in a else None
    r = analyze(path, thr, acts)
    if "--out" in a: jdump(r, a[a.index("--out") + 1])
    if "--sheet" in a: sheet(path, r["scenes"], a[a.index("--sheet") + 1])
    print(json.dumps({k: v for k, v in r.items() if k != "scenes"}, ensure_ascii=False))
