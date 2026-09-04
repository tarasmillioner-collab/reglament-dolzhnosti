#!/usr/bin/env python3
"""Детектор глитчей рук/лица (эвристики, без тяжёлых моделей): YuNet-лица (tools/models/yunet.onnx) — размер/уверенность/лишние лица;
руки — кожные блобы с аномальным числом «пальцев» (выпуклые дефекты). --image f.png | --video f.mp4 [--fps 2] → {"flags":[...], "faces":n}"""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__)); from common import *
MODEL = os.path.join(ROOT, "tools", "models", "yunet.onnx")

def faces(img):
    import cv2
    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(MODEL, "", (w, h), 0.6, 0.3, 500)
    det.setInputSize((w, h)); _, f = det.detect(img)
    out = []
    for r in (f if f is not None else []):
        x, y, bw, bh, *lm, sc = r.tolist(); out.append({"x": int(x), "y": int(y), "w": int(bw), "h": int(bh), "score": round(sc, 3), "lm": [round(v, 1) for v in lm]})
    return out

def hand_flags(img):
    import cv2, numpy as np
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    skin = cv2.inRange(hsv, (0, 30, 60), (25, 170, 255)); skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(skin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); flags = []
    for c in cnts:
        if cv2.contourArea(c) < 0.004 * img.shape[0] * img.shape[1]: continue
        hull = cv2.convexHull(c, returnPoints=False)
        if len(hull) < 4: continue
        try: d = cv2.convexityDefects(c, hull)
        except Exception: continue
        if d is None: continue
        d = d.reshape(-1, 4); deep = sum(1 for k in range(d.shape[0]) if d[k, 3] / 256.0 > 0.03 * img.shape[0])
        if deep >= 6: flags.append(f"hand_like_blob_with_{deep+1}_fingers")
    return flags

def analyze_image(path):
    import cv2
    img = cv2.imread(path); f = faces(img); flags = []
    for a in f:
        if a["score"] < 0.75: flags.append("low_confidence_face")
        lm = a["lm"]  # re, le, nose, rm, lm
        if len(lm) >= 10:
            eye_d = abs(lm[0] - lm[2]); 
            if eye_d < 0.25 * a["w"] or eye_d > 0.7 * a["w"]: flags.append("face_landmarks_off")
    if len(f) > 3: flags.append(f"too_many_faces_{len(f)}")
    flags += hand_flags(img)
    return {"faces": len(f), "face_boxes": f, "flags": flags, "ok": not flags}

def analyze_video(path, fps=2):
    tmp = tempfile.mkdtemp(); run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", f"fps={fps}", os.path.join(tmp, "f%05d.png")])
    frames = sorted(os.listdir(tmp)); per = []
    for k, fr in enumerate(frames):
        r = analyze_image(os.path.join(tmp, fr)); per.append({"t": round(k / fps, 2), "faces": r["faces"], "flags": r["flags"]})
    bad = [p for p in per if p["flags"]]
    return {"n_frames": len(per), "flagged_frames": len(bad), "flag_rate": round(len(bad) / max(len(per), 1), 3), "frames": per}

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        import cv2, numpy as np
        img = np.full((854, 480, 3), 40, np.uint8); p = tempfile.mktemp(suffix=".png"); cv2.imwrite(p, img)
        r = analyze_image(p); sys.exit(ok(f"model loads, blank frame faces={r['faces']} flags={r['flags']}") if r["faces"] == 0 else fail(str(r)))
    if "--image" in a: print(json.dumps(analyze_image(a[a.index("--image") + 1]), ensure_ascii=False))
    elif "--video" in a:
        r = analyze_video(a[a.index("--video") + 1], float(a[a.index("--fps") + 1]) if "--fps" in a else 2)
        if "--out" in a: jdump(r, a[a.index("--out") + 1])
        print(json.dumps({k: v for k, v in r.items() if k != "frames"}))
