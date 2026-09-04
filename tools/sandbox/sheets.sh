#!/bin/bash
# Deterministic contact sheets for judges (no whisper): 1 tile per shot at shot midpoint + end-card crop.
# The sandbox forgets files between calls, so this regenerates byte-identical sheets on demand (sha printed).
# Usage: sheets.sh <excerpt_url> <full_url>   -> /home/user/v/{excerpt_sheet.jpg, full_sheet.jpg, full_endcard.jpg}
set -e
EU="$1"; FU="$2"
RAW=https://raw.githubusercontent.com/tarasmillioner-collab/reglament-dolzhnosti/claude/vsl-clone-factory-34f2yn
mkdir -p /home/user/v && cd /home/user/v
[ -s excerpt.mp4 ] || curl -sf -o excerpt.mp4 "$EU"
[ -s full.mp4 ] || curl -sf -o full.mp4 "$FU"
curl -sf -o timeline.json "$RAW/work/stage5/timeline.json?nc=$RANDOM$RANDOM"
python3 - <<'PY'
import json,subprocess
from PIL import Image, ImageDraw
tl=json.load(open('timeline.json'))
def sheet(name,t0,t1,cols):
    shots={}
    for c in tl:
        if c['end']<=t0 or c['start']>=t1: continue
        s=shots.setdefault(c['shot'],[c['start'],c['end']]); s[0]=min(s[0],c['start']); s[1]=max(s[1],c['end'])
    tiles=[]
    for sh in sorted(shots):
        a,b=shots[sh]; mid=(max(a,t0)+min(b,t1))/2-t0
        subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',f'{mid:.2f}','-i',name+'.mp4','-frames:v','1','-vf','scale=120:213',f'{name}_f{sh:02d}.jpg'],check=True)
        im=Image.open(f'{name}_f{sh:02d}.jpg'); ImageDraw.Draw(im).text((2,2),f'{sh}',fill=(255,255,0)); tiles.append(im)
    rows=(len(tiles)+cols-1)//cols; S=Image.new('RGB',(cols*120,rows*213))
    for i,im in enumerate(tiles): S.paste(im,((i%cols)*120,(i//cols)*213))
    S.save(name+'_sheet.jpg',quality=42,optimize=True)
sheet('excerpt',0,41.98,6); sheet('full',0,200.87,7)
subprocess.run(['ffmpeg','-y','-loglevel','error','-ss','199.00','-i','full.mp4','-frames:v','1','-vf','scale=240:427','-q:v','5','full_endcard.jpg'],check=True)
PY
for f in excerpt_sheet.jpg full_sheet.jpg full_endcard.jpg; do echo "$f $(stat -c%s $f) $(sha256sum $f | cut -c1-16)"; done
