#!/usr/bin/env python3
"""kie.ai клиент: image (nano-banana-2) / video (bytedance/seedance-2-mini, ТОЛЬКО 480p, R1 зашит) / suno (V5_5).
Ключ: $KIE_API_KEY. Все вызовы пишут в COSTS.csv через cost_logger. `--selftest` работает без ключа (проверка сборки payload и R1)."""
import json, os, re, subprocess, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(__file__)); from common import *; import cost_logger as CL
BASE = "https://api.kie.ai"; JOBS = BASE + "/api/v1/jobs/createTask"; INFO = BASE + "/api/v1/jobs/recordInfo"
SUNO = BASE + "/api/v1/generate"; SUNO_INFO = BASE + "/api/v1/generate/record-info"; CALLBACK = "https://example.com/kie-callback"
VIDEO_MODEL = "bytedance/seedance-2-mini"; IMAGE_MODEL = "nano-banana-2"; USD_PER_CREDIT = 0.005

def key():
    v = os.environ.get("KIE_API_KEY", "").strip()
    if not v: raise RuntimeError("KIE_API_KEY не задан")
    return v

def _http(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r: return json.loads(r.read().decode())

def video_payload(prompt, seconds, refs=None, ref_videos=None, first_frame=None):
    if first_frame and refs: raise ValueError("first_frame_url и reference_image_urls взаимоисключающие (422)")
    inp = {"prompt": prompt, "resolution": "480p", "aspect_ratio": "9:16", "duration": int(seconds), "generate_audio": False}
    if refs: inp["reference_image_urls"] = list(refs)
    if ref_videos: inp["reference_video_urls"] = list(ref_videos)
    if first_frame: inp["first_frame_url"] = first_frame
    return {"model": VIDEO_MODEL, "input": inp, "callBackUrl": CALLBACK}

def _wait(tid, label):
    t0 = time.time()
    while time.time() - t0 < 1500:
        time.sleep(10); d = (_http("GET", f"{INFO}?taskId={tid}").get("data")) or {}
        st = (d.get("state") or "").lower()
        if st in ("success", "completed"):
            res = d.get("resultJson") or {}; res = json.loads(res) if isinstance(res, str) else res
            urls = res.get("resultUrls") or []; return urls[0], float(d.get("creditsConsumed") or 0)
        if st in ("fail", "failed"): raise RuntimeError(f"{label}: {d.get('failMsg')}")
    raise RuntimeError(f"{label}: timeout")

def video(prompt, seconds, label, **kw):
    p = video_payload(prompt, seconds, **kw)
    assert p["input"]["resolution"] == "480p" and p["model"] == VIDEO_MODEL  # R1
    if not CL.can_spend(seconds * CL.RATES[("kie", "video_sec_480p")]): raise RuntimeError("STOP: 80% бюджета")
    r = _http("POST", JOBS, p); tid = r["data"]["taskId"]; url, cr = _wait(tid, label)
    CL.add("kie", "video_sec_480p", VIDEO_MODEL, seconds, label, note=tid, unit_cost=(cr * USD_PER_CREDIT / seconds) if cr else None); return url

def image(prompt, label, refs=None):
    inp = {"prompt": prompt, "aspect_ratio": "9:16", "resolution": "1K", "output_format": "png"}
    if refs: inp["image_input"] = list(refs)
    if not CL.can_spend(CL.RATES[("kie", "image")]): raise RuntimeError("STOP: 80% бюджета")
    r = _http("POST", JOBS, {"model": IMAGE_MODEL, "input": inp, "callBackUrl": CALLBACK}); url, cr = _wait(r["data"]["taskId"], label)
    CL.add("kie", "image", IMAGE_MODEL, 1, label, unit_cost=(cr * USD_PER_CREDIT) if cr else None); return url

def suno(lyrics, style, title, duration, label, instrumental=False):
    body = {"customMode": True, "instrumental": instrumental, "model": "V5_5", "style": style[:1000], "title": title[:80], "prompt": lyrics[:3000], "duration": int(duration), "callBackUrl": CALLBACK}
    if not CL.can_spend(CL.RATES[("kie", "suno")]): raise RuntimeError("STOP: 80% бюджета")
    r = _http("POST", SUNO, body); tid = r["data"]["taskId"]; t0 = time.time()
    while time.time() - t0 < 1500:
        time.sleep(8); d = (_http("GET", f"{SUNO_INFO}?taskId={tid}").get("data")) or {}
        if d.get("status") == "SUCCESS":
            takes = [(t.get("audioUrl"), t.get("duration")) for t in ((d.get("response") or {}).get("sunoData") or [])]
            CL.add("kie", "suno", "V5_5", 1, label, note=tid); return takes
        if str(d.get("status", "")).endswith("FAILED") or d.get("status") == "SENSITIVE_WORD_ERROR": raise RuntimeError(str(d))
    raise RuntimeError("suno timeout")

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        p = video_payload("test", 5, first_frame="https://x/y.png")
        try: video_payload("t", 5, refs=["a"], first_frame="b"); sys.exit(fail("должен был отвергнуть first_frame+refs"))
        except ValueError: pass
        sys.exit(ok("payload 480p/seedance-2-mini, R1 ok, key=" + ("set" if os.environ.get("KIE_API_KEY") else "absent")) if p["input"]["resolution"] == "480p" else fail(str(p)))
    print(__doc__)
