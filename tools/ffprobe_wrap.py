#!/usr/bin/env python3
"""ffprobe-обёртка: длительность, WxH, fps, аудио, вертикаль/горизонталь. `--selftest`."""
import json, sys, os, tempfile
sys.path.insert(0, os.path.dirname(__file__)); from common import *

def probe(path):
    if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        from PIL import Image
        im = Image.open(path); return {"path": path, "w": im.width, "h": im.height, "kind": "image"}
    j = ffprobe_json(path)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    fps = 0.0
    if v and v.get("r_frame_rate"):
        n, d = v["r_frame_rate"].split("/"); fps = float(n) / float(d) if float(d) else 0
    out = {"path": path, "duration": float(j["format"]["duration"]), "w": v["width"] if v else 0,
           "h": v["height"] if v else 0, "fps": round(fps, 3), "has_audio": bool(a),
           "orientation": ("vertical" if v and v["height"] > v["width"] else "horizontal"), "kind": "video"}
    if a: out.update({"sample_rate": int(a.get("sample_rate", 0)), "channels": a.get("channels")})
    return out

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        p = synth_video(tempfile.mktemp(suffix=".mp4"), seconds=3)
        r = probe(p)
        sys.exit(ok(f"probe {r['w']}x{r['h']} {r['duration']:.2f}s") if r["w"] == 480 and abs(r["duration"] - 3) < 0.3 else fail(str(r)))
    print(json.dumps(probe(sys.argv[1]), ensure_ascii=False, indent=2))
