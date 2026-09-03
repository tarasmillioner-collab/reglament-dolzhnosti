#!/usr/bin/env python3
"""Аудио-замеры: LUFS, паузы (gaps по RMS), BPM (HPSS-перкуссия), спето/сказано (pitch variance + периодичность).
python3 tools/audio_measure.py media --out audio.json [--vo] [--normalize out.wav]"""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__)); from common import *

def load(path, sr=22050):
    import librosa
    w = tempfile.mktemp(suffix=".wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), w])
    y, _ = librosa.load(w, sr=sr, mono=True); return y, sr

def lufs(y, sr):
    import pyloudnorm as pyln
    m = pyln.Meter(sr); return round(float(m.integrated_loudness(y)), 2)

def gaps(y, sr, thr_db=-38, min_gap=0.25):
    import librosa, numpy as np
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    db = librosa.amplitude_to_db(rms + 1e-9, ref=np.max(np.abs(rms)) + 1e-9)
    t = librosa.frames_to_time(np.arange(len(db)), sr=sr, hop_length=512)
    quiet = db < thr_db; out = []; start = None
    for i, q in enumerate(quiet):
        if q and start is None: start = t[i]
        if not q and start is not None:
            if t[i] - start >= min_gap: out.append((round(float(start), 3), round(float(t[i]), 3)))
            start = None
    voiced = [(a, b) for a, b in out]
    return {"n_gaps": len(out), "max_gap": round(max((b - a for a, b in out), default=0), 3), "gaps_over_1_2": sum(1 for a, b in out if b - a > 1.2), "gaps": out[:200]}

def tempo(y, sr):
    import librosa, numpy as np
    yh, yp = librosa.effects.hpss(y)
    t, beats = librosa.beat.beat_track(y=yp, sr=sr)
    t = float(np.atleast_1d(t)[0])
    on = librosa.onset.onset_strength(y=yp, sr=sr)
    return {"bpm": round(t, 1), "n_beats": int(len(beats)), "onset_strength_mean": round(float(on.mean()), 3)}

def sung_or_spoken(y, sr):
    """Пение: устойчивая высота тона (низкая дисперсия f0 внутри нот, много вокализованных кадров) + гармоничность.
    Речь: f0 дрейфует непрерывно, короткие вокализованные сегменты."""
    import librosa, numpy as np
    f0, vflag, vprob = librosa.pyin(y[: sr * 60], fmin=80, fmax=600, sr=sr)
    f0v = f0[~np.isnan(f0)]
    if len(f0v) < 50: return {"mode": "unknown", "voiced_frac": 0.0}
    semis = 12 * np.log2(f0v / 55.0)
    # доля кадров, где тон держится в пределах ±0.5 полутона к соседу (ноты)
    stable = np.mean(np.abs(np.diff(semis)) < 0.5)
    voiced_frac = float(np.mean(~np.isnan(f0)))
    harm = librosa.effects.harmonic(y[: sr * 60]); hr = float(np.mean(np.abs(harm)) / (np.mean(np.abs(y[: sr * 60])) + 1e-9))
    score = 0.6 * stable + 0.4 * min(hr, 1.0)
    return {"mode": "sung" if (stable > 0.72 and voiced_frac > 0.45) else "spoken", "pitch_stability": round(float(stable), 3),
            "voiced_frac": round(voiced_frac, 3), "harmonic_ratio": round(hr, 3), "f0_range_semitones": round(float(np.ptp(semis)), 1)}

def analyze(path, vo=False):
    y, sr = load(path)
    out = {"duration": round(len(y) / sr, 3), "lufs": lufs(y, sr), **gaps(y, sr)}
    if not vo: out.update(tempo(y, sr))
    out["speech"] = sung_or_spoken(y, sr)
    return out

def normalize(path, out, target=-16.0):
    run(["ffmpeg", "-v", "error", "-y", "-i", path, "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11", "-ar", "44100", out]); return out

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        p = synth_video(tempfile.mktemp(suffix=".mp4"), seconds=4, scenes=2)
        r = analyze(p)
        sys.exit(ok(f"lufs={r['lufs']} bpm={r.get('bpm')} mode={r['speech']['mode']}") if "lufs" in r and "bpm" in r else fail(str(r)))
    path = a[0]; r = analyze(path, vo="--vo" in a)
    if "--normalize" in a: normalize(path, a[a.index("--normalize") + 1]); r["normalized_to"] = a[a.index("--normalize") + 1]
    if "--out" in a: jdump(r, a[a.index("--out") + 1])
    print(json.dumps({k: v for k, v in r.items() if k != "gaps"}, ensure_ascii=False))
