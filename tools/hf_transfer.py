#!/usr/bin/env python3
"""Перенос файлов sandbox Higgsfield ↔ локально.
sandbox→local: в sandbox: `python3 - <<EOF ... base64 chunk N` (см. chunk_cmd); чанки складываются в logs/chunks/<name>/NNN.b64,
затем `assemble logs/chunks/<name> out.mp4` (проверка sha256).
local→sandbox: файлы пушатся в GitHub, sandbox тянет raw.githubusercontent.com (см. raw_url).
fetch <url> <out> — прямая закачка, если egress откроют."""
import base64, hashlib, os, sys, json
sys.path.insert(0, os.path.dirname(__file__)); from common import *
CHUNK = 140_000  # байт бинарных на чанк (~187 КБ base64 < 200 КБ лимита stdout)

def chunk_cmd(remote_path, idx):
    """Команда для sandbox_exec, печатающая чанк idx файла remote_path (base64) и, для idx==0, метаданные."""
    return (f"python3 -c \"import base64,hashlib,sys,os;p='{remote_path}';b=open(p,'rb').read();n=(len(b)+{CHUNK}-1)//{CHUNK};"
            f"i={idx};print('META',len(b),n,hashlib.sha256(b).hexdigest()) if i==0 else None;"
            f"sys.stdout.write('CHUNK '+str(i)+' '+base64.b64encode(b[i*{CHUNK}:(i+1)*{CHUNK}]).decode())\"")

def save_chunk(name, idx, text):
    d = os.path.join(ROOT, "logs", "chunks", name); os.makedirs(d, exist_ok=True)
    meta = None; payload = None
    for line in text.splitlines():
        if line.startswith("META "): meta = line.split()[1:]
        if line.startswith("CHUNK "): payload = line.split(" ", 2)[2].strip()
    if meta: json.dump({"size": int(meta[0]), "n": int(meta[1]), "sha256": meta[2]}, open(os.path.join(d, "meta.json"), "w"))
    if payload is None: raise RuntimeError("нет CHUNK в тексте")
    open(os.path.join(d, f"{idx:03d}.b64"), "w").write(payload); return d

def assemble(dirpath, out):
    meta = json.load(open(os.path.join(dirpath, "meta.json")))
    b = b"".join(base64.b64decode(open(os.path.join(dirpath, f"{i:03d}.b64")).read()) for i in range(meta["n"]))
    if len(b) != meta["size"] or hashlib.sha256(b).hexdigest() != meta["sha256"]: raise RuntimeError("sha256/size mismatch")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True); open(out, "wb").write(b); return out

def raw_url(repo_rel_path, branch="claude/vsl-clone-factory-34f2yn"):
    return f"https://raw.githubusercontent.com/tarasmillioner-collab/reglament-dolzhnosti/{branch}/{repo_rel_path}"

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        import tempfile
        data = os.urandom(300_000); p = tempfile.mktemp(); open(p, "wb").write(data)
        n = (len(data) + CHUNK - 1) // CHUNK; name = "selftest"
        for i in range(n):
            txt = (f"META {len(data)} {n} {hashlib.sha256(data).hexdigest()}\n" if i == 0 else "") + "CHUNK %d %s" % (i, base64.b64encode(data[i*CHUNK:(i+1)*CHUNK]).decode())
            save_chunk(name, i, txt)
        out = assemble(os.path.join(ROOT, "logs", "chunks", name), tempfile.mktemp())
        sys.exit(ok(f"{n} chunks roundtrip") if open(out, "rb").read() == data else fail("mismatch"))
    if a[0] == "assemble": print(assemble(a[1], a[2]))
    elif a[0] == "chunk_cmd": print(chunk_cmd(a[1], int(a[2])))
    elif a[0] == "save": save_chunk(a[1], int(a[2]), open(a[3]).read())
    elif a[0] == "fetch": run(["curl", "-sSL", "-o", a[2], a[1]]); print(a[2])
    else: print(__doc__)
