#!/usr/bin/env python3
"""Build OpenShorts "higgsfield" asset sets from Higgsfield generations.

Reads assets.json (which Higgsfield job produced which file) and scripts.json
(the OpenShorts scripts), and for every set writes
$HIGGSFIELD_ASSETS_DIR/<asset_id>/{actor.png, head.mp4, voice.mp3?, broll_N.mp4, manifest.json}.

  talking   - Omni Flash clips with native speech: each clip is trimmed to its
              speech (+ a short tail) and the clips are joined into head.mp4.
  voiceover - an ElevenLabs track over muted Omni Flash scenes: the scene shown
              under each script segment is cut to that segment's length.

Segment start/end times in the scripts are then re-measured on the real audio
(whisper word timings aligned to the script text) so OpenShorts inserts the
b-roll exactly where its line is spoken. Output: scripts_aligned.json.
"""
import json
import os
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
OPENSHORTS = os.environ.get("OPENSHORTS_DIR", os.path.join(HERE, "..", "openshorts"))
sys.path.insert(0, OPENSHORTS)
from saasshorts import align_words_to_script, _norm_token  # noqa: E402

OUT = os.environ.get("HIGGSFIELD_ASSETS_DIR", os.path.join(OPENSHORTS, "output", "higgsfield_assets"))
CACHE = os.path.join(OUT, "_downloads")
VF = "scale=720:1280:flags=lanczos,fps=30,setsar=1,format=yuv420p"
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
       "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "160k"]
# Which scene sits under each segment type in a voiceover set (index into "clips").
VOICEOVER_SCENES = {"hook": 0, "problem": 0, "solution": 1, "demo": 2, "cta": 3}

_model = None


def run(cmd):
    subprocess.run(cmd, check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    for attempt in range(4):
        try:
            urllib.request.urlretrieve(url, dest + ".part")
            os.replace(dest + ".part", dest)
            return dest
        except Exception:
            if attempt == 3:
                raise
    return dest


def transcribe(path, hint):
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
    segments, _ = _model.transcribe(path, language=os.environ.get("WHISPER_LANGUAGE", "uk"),
                                    word_timestamps=True, vad_filter=True, beam_size=5,
                                    condition_on_previous_text=False, initial_prompt=hint)
    return [{"word": w.word.strip(), "start": float(w.start), "end": float(w.end)}
            for s in segments for w in (s.words or [])]


def normalize(src, dst, start=0.0, length=None, mute=False, loop=False):
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if loop:
        cmd += ["-stream_loop", "-1"]
    cmd += ["-ss", f"{start:.3f}", "-i", src]
    if mute:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a"]
    if length is not None:
        cmd += ["-t", f"{length:.3f}"]
    cmd += ["-vf", VF, *ENC, "-shortest", dst]
    run(cmd)


def concat(parts, dst):
    inputs = []
    for p in parts:
        inputs += ["-i", p]
    streams = "".join(f"[{i}:v][{i}:a]" for i in range(len(parts)))
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex",
         f"{streams}concat=n={len(parts)}:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]", *ENC, dst])


def segment_times(script, words, total):
    """Start of every segment = when its first word is spoken."""
    aligned = align_words_to_script(words, script["full_narration"], keep_heard_digits=False)
    seg_tokens = [[t for t in seg["narration"].split() if _norm_token(t)] for seg in script["segments"]]
    if sum(len(t) for t in seg_tokens) != len(aligned):
        print(f"  ! segment narrations do not add up to full_narration, keeping script timings")
        return [(s["start"], s["end"]) for s in script["segments"]]
    starts, idx = [], 0
    for tokens in seg_tokens:
        starts.append(aligned[idx]["start"] if tokens else (starts[-1] if starts else 0.0))
        idx += len(tokens)
    starts[0] = 0.0
    ends = starts[1:] + [total]
    return list(zip(starts, ends))


def build_set(asset_id, spec, script, cdn):
    out_dir = os.path.join(OUT, asset_id)
    os.makedirs(out_dir, exist_ok=True)
    work = os.path.join(out_dir, "_work")
    os.makedirs(work, exist_ok=True)
    get = lambda item: fetch(cdn + item["file"], os.path.join(CACHE, item["file"]))  # noqa: E731

    fetch(cdn + spec["actor"]["file"], os.path.join(out_dir, "actor.png"))
    head = os.path.join(out_dir, "head.mp4")

    if spec["kind"] == "talking":
        parts = []
        for i, clip in enumerate(spec["clips"]):
            src = get(clip)
            words = transcribe(src, clip["say"])
            clip_len = duration(src)
            start = max(0.0, words[0]["start"] - 0.12) if words else 0.0
            end = min(clip_len, words[-1]["end"] + 0.30) if words else clip_len
            print(f"  clip {i}: speech {start:.2f}-{end:.2f}s of {clip_len:.1f}s :: "
                  + " ".join(w["word"] for w in words))
            part = os.path.join(work, f"clip_{i}.mp4")
            normalize(src, part, start=start, length=end - start)
            parts.append(part)
        concat(parts, head)
        total = duration(head)
        words = transcribe(head, script["full_narration"])
    else:
        voice = os.path.join(out_dir, "voice.mp3")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", get(spec["voice"]), "-c:a", "libmp3lame",
             "-b:a", "192k", voice])
        total = duration(voice) + 0.3
        words = transcribe(voice, script["full_narration"])

    times = segment_times(script, words, total)
    for seg, (start, end) in zip(script["segments"], times):
        seg["start"], seg["end"] = round(start, 2), round(end, 2)
    script["duration_seconds"] = round(total)

    if spec["kind"] == "voiceover":
        parts = []
        for i, seg in enumerate(script["segments"]):
            scene = get(spec["clips"][VOICEOVER_SCENES.get(seg["type"], 0)])
            part = os.path.join(work, f"scene_{i}.mp4")
            normalize(scene, part, length=max(0.1, seg["end"] - seg["start"]), mute=True, loop=True)
            parts.append(part)
        visual = os.path.join(work, "visual.mp4")
        concat(parts, visual)
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", visual, "-i", voice, "-map", "0:v",
             "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "160k",
             "-shortest", head])

    for i, item in enumerate(spec["broll"]):
        normalize(get(item), os.path.join(out_dir, f"broll_{i}.mp4"), mute=True)

    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"models": spec["models"], "credits": spec["credits"],
                   "higgsfield_jobs": {"actor": spec["actor"]["job"],
                                       "clips": [c["job"] for c in spec["clips"]],
                                       "broll": [b["job"] for b in spec["broll"]],
                                       **({"voice": spec["voice"]["job"]} if "voice" in spec else {})}},
                  f, ensure_ascii=False, indent=2)
    print(f"  {asset_id}: head {duration(head):.1f}s, segments "
          + ", ".join(f"{s['type']} {s['start']}-{s['end']}" for s in script["segments"]))


def main():
    os.makedirs(CACHE, exist_ok=True)
    assets = json.load(open(os.path.join(HERE, "assets.json"), encoding="utf-8"))
    data = json.load(open(os.path.join(HERE, "scripts.json"), encoding="utf-8"))
    cdn = assets["cdn"]

    # Download everything up front, in parallel.
    files = set()
    for spec in assets["sets"].values():
        for item in [spec["actor"], *spec["clips"], *spec["broll"], *([spec["voice"]] if "voice" in spec else [])]:
            files.add(item["file"])
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda f: fetch(cdn + f, os.path.join(CACHE, f)), sorted(files)))
    print(f"downloaded {len(files)} Higgsfield files")

    for script in data["scripts"]:
        print(f"[{script['asset_id']}] {script['title']}")
        build_set(script["asset_id"], assets["sets"][script["asset_id"]], script, cdn)

    with open(os.path.join(HERE, "scripts_aligned.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("wrote scripts_aligned.json")


if __name__ == "__main__":
    main()
