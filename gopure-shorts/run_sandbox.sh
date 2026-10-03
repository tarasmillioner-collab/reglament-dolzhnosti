#!/usr/bin/env bash
# End-to-end OpenShorts demo run for goPure, made for the Higgsfield sandbox
# (Debian, python3 + faster-whisper, node + Playwright, ffmpeg, internet).
#
#   bash run_sandbox.sh [workdir]
#
# 1. upstream OpenShorts at a pinned commit + openshorts-higgsfield.patch
# 2. backend deps (heavy CV models stubbed: AI Shorts never touches them) and a dashboard build
# 3. prepare_assets.py: Higgsfield generations -> OpenShorts asset sets
# 4. backend + built dashboard on :8000, Playwright drives the AI Shorts wizard per script
# 5. collects the finished shorts, screenshots and the screen recording in $WORK/out/publish
#    and, if $WORK/uploads.tsv appears (name<TAB>content-type<TAB>presigned PUT url), uploads them.
#
# MODE=live stops after step 3 and serves the dashboard on :8000 for a person to use.
set -euo pipefail
WORK=${1:-$HOME/gopure-run}
OPENSHORTS_REV=06a119c280e545bc3f55f2b7b036d4c187630d50
KIT_REPO=https://github.com/tarasmillioner-collab/reglament-dolzhnosti.git
KIT_BRANCH=claude/gopure-demo-videos-bq8io5
mkdir -p "$WORK" && cd "$WORK"
log() { echo "[$(date +%T)] $*"; }

log "1/5 code"
if [ ! -d openshorts/.git ]; then
  git init -q openshorts
  git -C openshorts remote add origin https://github.com/mutonby/openshorts.git
  git -C openshorts fetch -q --depth 1 origin "$OPENSHORTS_REV"
  git -C openshorts checkout -q FETCH_HEAD
fi
[ -d kit/.git ] || git clone -q --depth 1 -b "$KIT_BRANCH" "$KIT_REPO" kit
KIT=$WORK/kit/gopure-shorts
git -C openshorts diff --quiet && git -C openshorts apply "$KIT/openshorts-higgsfield.patch"

log "2/5 dependencies"
pip install -q --user --disable-pip-version-check fastapi==0.136.1 uvicorn==0.46.0 \
  python-multipart==0.0.27 httpx==0.28.1 beautifulsoup4==4.14.3 python-dotenv==1.2.2 \
  google-genai==1.75.0 boto3==1.43.4 py3langid==0.3.0 tqdm opencv-python-headless \
  scenedetect==0.7 yt-dlp
if [ ! -f openshorts/dashboard/dist/index.html ]; then
  (cd openshorts/dashboard && npm ci --no-audit --no-fund --loglevel=error && npm run build >/dev/null)
fi
# Captions use "Arial Black": map it to the bundled Montserrat ExtraBold (Cyrillic).
mkdir -p ~/.fonts ~/.config/fontconfig
cp openshorts/fonts/*.ttf ~/.fonts/
cat > ~/.config/fontconfig/fonts.conf <<'EOF'
<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <alias binding="strong"><family>Arial Black</family><prefer><family>Montserrat ExtraBold</family></prefer></alias>
</fontconfig>
EOF
fc-cache -f >/dev/null

export PYTHONPATH=$KIT/stubs OPENSHORTS_DIR=$WORK/openshorts
export HIGGSFIELD_ASSETS_DIR=$WORK/openshorts/output/higgsfield_assets
export HF_HUB_CACHE=/opt/whisper-models WHISPER_MODEL=small WHISPER_LANGUAGE=uk
export AI_SHORTS_CAPTION_MARGIN_V=560

log "3/5 Higgsfield assets -> OpenShorts asset sets"
python3 "$KIT/prepare_assets.py"

if [ "${MODE:-record}" = live ]; then
  # Live mode: serve the dashboard for a person instead of recording it.
  # /gopure.html seeds the browser with the goPure analysis and scripts.
  cp "$KIT/demo.html" openshorts/dashboard/dist/gopure.html
  cp "$KIT/scripts_aligned.json" openshorts/dashboard/dist/demo-data.json
  log "LIVE https://8000-${E2B_SANDBOX_ID:-sandbox}.e2b.app/gopure.html"
  cd openshorts && exec python3 serve_dashboard.py
fi

log "4/5 backend + dashboard"
(cd openshorts && nohup python3 serve_dashboard.py > "$WORK/backend.log" 2>&1 &)
for _ in $(seq 60); do curl -sf localhost:8000/api/config >/dev/null && break; sleep 1; done
rm -rf "$WORK/out" && mkdir -p "$WORK/out"
NODE_PATH=$(npm root -g) OPENSHORTS_OUTPUT=$WORK/openshorts/output \
  node "$KIT/drive_dashboard.cjs" "$KIT/scripts_aligned.json" "$HIGGSFIELD_ASSETS_DIR" "$WORK/out"

log "5/5 collect"
PUB=$WORK/out/publish && mkdir -p "$PUB"
python3 - "$WORK" <<'EOF'
import json, os, shutil, subprocess, sys
work = sys.argv[1]
out = os.path.join(work, "out")
for r in json.load(open(os.path.join(out, "results.json"))):
    src = os.path.join(work, "openshorts", "output", r["video_url"].split("/videos/", 1)[1])
    dst = os.path.join(out, "publish", r["asset_id"] + ".mp4")
    shutil.copy2(src, dst)
    ass = [f for f in os.listdir(os.path.dirname(src)) if f.endswith(".ass")]
    caps = []
    if ass:
        for line in open(os.path.join(os.path.dirname(src), ass[0]), encoding="utf-8"):
            if line.startswith("Dialogue:"):
                caps.append(line.rsplit(",", 1)[-1].strip())
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
                            "-of", "csv=p=0", dst], capture_output=True, text=True).stdout.split()
    print(f"{r['asset_id']}: {probe} {os.path.getsize(dst)//1024} KB | captions: {' / '.join(caps)}")
EOF
ffmpeg -y -loglevel error -i "$WORK/out/recording/dashboard.webm" -vf "setpts=PTS/1.5,scale=1440:900" \
  -c:v libx264 -preset veryfast -crf 26 -pix_fmt yuv420p -an "$PUB/dashboard_walkthrough.mp4"
for f in "$WORK"/out/screens/*.png; do
  ffmpeg -y -loglevel error -i "$f" -q:v 3 "$PUB/$(basename "${f%.png}").jpg"
done
(cd "$WORK/out" && zip -qr "$PUB/screens.zip" screens results.json)
ls -la "$PUB"

if [ -n "${WAIT_FOR_UPLOADS:-}" ]; then
  log "waiting for uploads.tsv"
  for _ in $(seq 300); do [ -f "$WORK/uploads.tsv" ] && break; sleep 2; done
fi
if [ -f "$WORK/uploads.tsv" ]; then
  while IFS=$'\t' read -r name ctype url; do
    [ -z "$name" ] && continue
    code=$(curl -s -o /dev/null -w '%{http_code}' -X PUT -H "Content-Type: $ctype" --data-binary @"$PUB/$name" "$url")
    echo "upload $name -> $code"
  done < "$WORK/uploads.tsv"
fi
log "DONE"
