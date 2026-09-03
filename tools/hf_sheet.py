#!/usr/bin/env python3
"""Печатает команду для sandbox: собрать контакт-лист из prev/*.jpg (N в ряд) в sheet_<tag>.jpg 240x427 на плитку и выдать base64-чанки.
python3 tools/hf_sheet.py cmd <tag> <name1> <name2> ...  → команда ffmpeg tile
Также: python3 tools/hf_sheet.py chunkcmd <remote_path> <idx> (обёртка hf_transfer.chunk_cmd)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); import hf_transfer as T
if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "cmd":
        tag, names = a[1], a[2:]; cols = min(4, len(names)); rows = (len(names) + cols - 1) // cols
        inputs = " ".join(f"-i prev/{n}.jpg" for n in names)
        fc = "".join(f"[{i}:v]scale=240:427[s{i}];" for i in range(len(names))) + "".join(f"[s{i}]" for i in range(len(names))) + f"xstack=inputs={len(names)}:layout=" + "|".join(f"{(i%cols)*240}_{(i//cols)*427}" for i in range(len(names))) + ":fill=black[o]"
        print(f"ffmpeg -v error -y {inputs} -filter_complex \"{fc}\" -map \"[o]\" -q:v 5 sheet_{tag}.jpg && ls -la sheet_{tag}.jpg")
    elif a[0] == "chunkcmd":
        print(T.chunk_cmd(a[1], int(a[2])))
