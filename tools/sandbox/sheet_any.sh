#!/bin/bash
# Generic contact sheet in the Higgsfield sandbox. stdin: lines "<id> <https url>"; args: <chunk N> [cols=5] [name=sheet]
# Prints META line (b64 length, sha16) and base64 chunk N (13500 chars). Deterministic for identical inputs.
set -e
N=${1:-1}; COLS=${2:-5}; NAME=${3:-sheet}; CH=13500
D=/home/user/w/$NAME; mkdir -p $D && cd $D
while read -r id url; do [ -z "$id" ] && continue; [ -s $id.png ] || curl -sf -o $id.png "$url" & done
wait
python3 - "$COLS" "$D" <<'PY'
from PIL import Image, ImageDraw
import glob,os,sys
cols=int(sys.argv[1]); D=sys.argv[2]
fs=sorted(glob.glob(D+'/*.png'))
W,H=126,224; rows=(len(fs)+cols-1)//cols
sheet=Image.new('RGB',(cols*W,rows*H),'black'); d=ImageDraw.Draw(sheet)
for i,f in enumerate(fs):
    im=Image.open(f).convert('RGB'); im.thumbnail((W,H)); x,y=(i%cols)*W,(i//cols)*H
    sheet.paste(im,(x,y)); d.rectangle([x,y,x+26,y+12],fill='black'); d.text((x+2,y+1),os.path.basename(f)[:3],fill='yellow')
sheet.save(D+'.jpg',quality=42,optimize=True)
PY
base64 -w0 $D.jpg > $D.b64
echo "META $(wc -c < $D.b64) $(sha256sum $D.jpg | cut -c1-16) chunk=$N"
cut -c$(( (N-1)*CH+1 ))-$(( N*CH )) $D.b64
