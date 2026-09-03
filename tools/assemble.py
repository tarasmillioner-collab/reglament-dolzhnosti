#!/usr/bin/env python3
"""Сборка: timeline.json (карточки с clip-путями) + VO + .ass → mp4. Каждый клип режется под длину карточки, scale 480x854, fps 30.
python3 tools/assemble.py timeline.json vo.wav subs.ass out.mp4 [--from 0 --to 40] [--music bed.wav --music-db -18]
Также умеет --script: печатает bash-скрипт для выполнения в sandbox (те же операции)."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__)); from common import *

def plan(timeline, t_from=0.0, t_to=None):
    items = []
    for c in timeline:
        s, e = c["start"], c["end"]
        if t_to is not None and s >= t_to: break
        if e <= t_from: continue
        clip = c.get("clip")
        if not clip: continue
        items.append({"clip": clip, "start": max(s, t_from), "end": min(e, t_to) if t_to else e, "in": c.get("clip_in", 0.0)})
    return items

def build(timeline, vo, ass, out, t_from=0.0, t_to=None, music=None, music_db=-18, w=480, h=854, fps=30):
    items = plan(timeline, t_from, t_to); tmp = tempfile.mkdtemp(); parts = []
    for i, it in enumerate(items):
        d = it["end"] - it["start"]; p = os.path.join(tmp, f"p{i:03d}.mp4")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{it['in']:.3f}", "-i", it["clip"], "-t", f"{d:.3f}", "-an",
             "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},setsar=1", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", p])
        parts.append(p)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    vid = os.path.join(tmp, "video.mp4"); run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid])
    total = sum(it["end"] - it["start"] for it in items)
    a_in = ["-ss", f"{t_from:.3f}", "-t", f"{total:.3f}", "-i", vo]
    if music:
        a_in += ["-stream_loop", "-1", "-i", music]
        af = f"[1:a]aformat=channel_layouts=mono,volume=1.0[v];[2:a]volume={music_db}dB,aformat=channel_layouts=mono[m];[v][m]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[mc];[v][mc]amix=inputs=2:duration=first:normalize=0[a]"
        maps = ["-filter_complex", af, "-map", "0:v", "-map", "[a]"]
    else:
        maps = ["-map", "0:v", "-map", "1:a"]
    vf = f"subtitles={ass}" if ass else "null"
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, *a_in, *maps, "-vf", vf, "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out])
    return out, total

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        c1 = synth_video(tempfile.mktemp(suffix=".mp4"), seconds=3, scenes=1); c2 = synth_video(tempfile.mktemp(suffix=".mp4"), seconds=3, scenes=1)
        vo = tempfile.mktemp(suffix=".wav"); run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=300:duration=4", vo])
        tl = [{"text": "раз два", "start": 0, "end": 1.5, "clip": c1, "words_t": [(0, 0.7), (0.7, 1.5)]}, {"text": "три", "start": 1.5, "end": 3.0, "clip": c2, "words_t": [(1.5, 3.0)]}]
        import karaoke_ass; ass = tempfile.mktemp(suffix=".ass"); open(ass, "w").write(karaoke_ass.build(tl))
        out, total = build(tl, vo, ass, tempfile.mktemp(suffix=".mp4"))
        d = duration(out); sys.exit(ok(f"assembled {d:.2f}s") if abs(d - 3.0) < 0.3 else fail(f"dur={d}"))
    tl = json.load(open(a[0], encoding="utf-8")); g = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    out, total = build(tl, a[1], a[2] if a[2] != "-" else None, a[3], float(g("--from", 0)), float(g("--to")) if g("--to") else None, g("--music"), float(g("--music-db", -18)))
    print(f"{out} {total:.2f}s")
