#!/usr/bin/env python3
"""Запускает --selftest для всех tools/*.py (кроме себя и common)."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__)); bad = 0
for f in sorted(os.listdir(here)):
    if not f.endswith(".py") or f in ("common.py", "selftest_all.py"): continue
    r = subprocess.run([sys.executable, os.path.join(here, f), "--selftest"], capture_output=True, text=True, timeout=600)
    line = (r.stdout.strip().splitlines() or [r.stderr.strip()[-200:]])[-1]
    print(f"{'OK ' if r.returncode == 0 else 'BAD'} {f:22s} {line}")
    bad += r.returncode != 0
sys.exit(1 if bad else 0)
