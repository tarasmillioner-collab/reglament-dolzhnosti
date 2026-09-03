"""Общие помощники для tools/. Никакой бизнес-логики."""
import json, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(cmd, check=True, capture=True, timeout=600):
    r = subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"cmd failed ({r.returncode}): {' '.join(cmd)}\n{r.stderr[-800:]}")
    return r

def ffprobe_json(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path])
    return json.loads(r.stdout)

def duration(path):
    return float(ffprobe_json(path)["format"]["duration"])

def synth_video(path, seconds=6, w=480, h=854, fps=30, scenes=3, with_audio=True):
    """Синтетический вертикальный ролик с N сценами разного цвета + тон, для --selftest."""
    seg = seconds / scenes
    colors = ["0x2244aa", "0xaa3322", "0x22aa44", "0xaaaa22", "0x8822aa"]
    parts = []
    for i in range(scenes):
        f = tempfile.mktemp(suffix=f"_s{i}.mp4")
        vf = f"color=c={colors[i % len(colors)]}:s={w}x{h}:r={fps}:d={seg:.3f}"
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", vf]
        if with_audio:
            cmd += ["-f", "lavfi", "-i", f"sine=frequency={220*(i+1)}:duration={seg:.3f}", "-shortest"]
        cmd += ["-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast"]
        if with_audio: cmd += ["-c:a", "aac"]
        cmd += [f]
        run(cmd); parts.append(f)
    lst = tempfile.mktemp(suffix=".txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", path])
    return path

def jdump(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def ok(msg): print(f"SELFTEST OK: {msg}"); return 0
def fail(msg): print(f"SELFTEST FAIL: {msg}"); return 1
