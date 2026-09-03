#!/usr/bin/env python3
"""Per-shot video clip specs for seedance_2_0_mini (R1: only this model, only 480p).
Reads work/stage5/timeline.json + work/stage4/prompts.json (latest completed still per card).
Usage: python3 tools/clip_prompts.py [shot ...] -> JSON list [{shot, cards, dur_shot, clip_dur, start_image(job_id), prompt, world}]"""
import json, sys
MOTION = ("Subtle realistic motion, handheld 35mm documentary feel, slow push-in, natural micro-movements, "
          "the person breathes and blinks, no camera shake, no text, no captions, no logos. Keep the exact face, hair, clothes, "
          "lighting and colour grade of the start image.")
def specs(shots=None):
    tl = json.load(open("work/stage5/timeline.json"))
    pr = json.load(open("work/stage4/prompts.json"))
    latest = {}
    for s in pr["stills"]:
        if s["status"] == "completed": latest[s["id"]] = s["job_id"]
    out = []
    for sh in sorted({c["shot"] for c in tl}):
        if shots and sh not in shots: continue
        cs = [c for c in tl if c["shot"] == sh]
        d = cs[-1]["end"] - cs[0]["start"]
        clip = 5 if d <= 4.6 else (8 if d <= 7.6 else (10 if d <= 9.6 else 12))
        # start image: first card of the shot that has a still; else any card of the shot
        img = next((latest[c["id"]] for c in cs if c["id"] in latest), None)
        desc = " ".join(dict.fromkeys(c["shot_desc"] for c in cs))
        out.append({"shot": sh, "cards": [c["id"] for c in cs], "t_start": cs[0]["start"], "t_end": cs[-1]["end"],
                    "dur_shot": round(d, 2), "clip_dur": clip, "start_image": img, "world": cs[0]["world"],
                    "prompt": MOTION + " Scene: " + desc,
                    "params": {"model": "seedance_2_0_mini", "resolution": "480p", "aspect_ratio": "9:16", "generate_audio": False}})
    return out
if __name__ == "__main__":
    sh = [int(x) for x in sys.argv[1:]] or None
    print(json.dumps(specs(sh), ensure_ascii=False, indent=1))
