#!/usr/bin/env python3
"""Идентичность стилла с референсом (паспортом): лицо — YuNet-кроп + сравнение (гистограмма HSV + ORB-совпадения + пропорции ландмарок);
продукт/мир — гистограмма цвета всего кадра. Порог грубый, финальное слово за judge-identity (глазами).
--still s.png --ref hero.png [--mode face|product|world] → {"score":0..1,"pass":bool}"""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__)); from common import *
import glitch_detect as G

def face_crop(path):
    import cv2
    img = cv2.imread(path); f = G.faces(img)
    if not f: return None, img
    a = max(f, key=lambda r: r["w"] * r["h"]); pad = int(0.25 * a["w"])
    x0, y0 = max(a["x"] - pad, 0), max(a["y"] - pad, 0); x1, y1 = min(a["x"] + a["w"] + pad, img.shape[1]), min(a["y"] + a["h"] + pad, img.shape[0])
    return cv2.resize(img[y0:y1, x0:x1], (160, 160)), img

def hist_sim(a, b):
    import cv2
    ha = cv2.calcHist([cv2.cvtColor(a, cv2.COLOR_BGR2HSV)], [0, 1], None, [24, 8], [0, 180, 0, 256]); hb = cv2.calcHist([cv2.cvtColor(b, cv2.COLOR_BGR2HSV)], [0, 1], None, [24, 8], [0, 180, 0, 256])
    cv2.normalize(ha, ha); cv2.normalize(hb, hb); return max(0.0, float(cv2.compareHist(ha, hb, cv2.HISTCMP_CORREL)))

def orb_sim(a, b):
    import cv2
    orb = cv2.ORB_create(500); ka, da = orb.detectAndCompute(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), None); kb, db = orb.detectAndCompute(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), None)
    if da is None or db is None: return 0.0
    m = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db); good = [x for x in m if x.distance < 48]
    return min(1.0, len(good) / 60.0)

def compare(still, ref, mode="face"):
    import cv2
    if mode == "face":
        fa, ia = face_crop(still); fb, ib = face_crop(ref)
        if fa is None or fb is None: return {"score": 0.0, "pass": False, "reason": "face not found in still or ref"}
        s = 0.5 * hist_sim(fa, fb) + 0.5 * orb_sim(fa, fb)
    else:
        ia = cv2.resize(cv2.imread(still), (240, 426)); ib = cv2.resize(cv2.imread(ref), (240, 426))
        s = 0.6 * hist_sim(ia, ib) + 0.4 * orb_sim(ia, ib)
    return {"score": round(s, 3), "pass": s >= (0.45 if mode == "face" else 0.4), "mode": mode}

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        import cv2, numpy as np
        p = tempfile.mktemp(suffix=".png"); img = np.zeros((426, 240, 3), np.uint8); img[:, :, 0] = 200; cv2.circle(img, (120, 200), 60, (30, 80, 220), -1); cv2.imwrite(p, img)
        q = tempfile.mktemp(suffix=".png"); img2 = np.zeros((426, 240, 3), np.uint8); img2[:, :, 1] = 200; cv2.imwrite(q, img2)
        r1 = compare(p, p, "world"); r2 = compare(p, q, "world")
        sys.exit(ok(f"same={r1['score']} diff={r2['score']}") if r1["pass"] and r1["score"] > r2["score"] else fail(f"{r1} {r2}"))
    g = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    print(json.dumps(compare(g("--still"), g("--ref"), g("--mode", "face"))))
