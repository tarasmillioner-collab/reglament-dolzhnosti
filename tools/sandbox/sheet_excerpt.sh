#!/bin/bash
# Rebuild the Stage-4 excerpt contact sheet in the Higgsfield sandbox and print base64 chunk $1 (1-based, 13500 chars).
# Deterministic: same inputs -> same JPEG bytes, so chunks fetched across sandbox restarts are consistent (sha printed).
set -e
N=${1:-1}; CH=13500
mkdir -p /home/user/w/st && cd /home/user/w/st
B=https://d8j0ntlcm91z4.cloudfront.net/user_39X4DueuoaObGccsCPKMarFan0M
while read -r id f; do [ -s $id.png ] || curl -sf -o $id.png "$B/hf_20260903_$f.png" & done <<'LIST'
c01 161915_e6c6d38e-c4ea-407d-8661-caa6d9a840b5
c02 161916_94f97182-7441-483c-aaef-da95d8e7f115
c03 161915_7faa87dd-db1b-46ea-9b57-a70b1c0bd94e
c04 161915_c20399f7-b9ae-4235-b529-963fa926cfa1
c05 161916_f10d1330-d005-4025-9de8-816a2c8e0911
c06 161915_ec317834-681f-43a2-9cbf-a6b52b4af6d5
c07 161915_166f67ef-cd5d-4444-91c5-c509311e389e
c08 161915_35440aa9-dc77-4c7a-bc7e-1499bb0d3d1a
c09 160926_248dadfb-134b-469b-afea-585e915367ec
c10 160925_9353c8fc-0929-44b8-8764-f407326f3ac1
c11 160924_3e5bcfb0-f6a3-4d4f-9dfb-f1bde711348e
c12 160925_671c785c-1e30-4683-80d7-2ecd28abc6b6
c13 160938_7ac0704b-38cc-49bc-b402-4f14dc3283ca
c14 160938_df73bfff-4c1f-413a-b4b0-2a874ec75f8c
c15 160938_1485505e-ba11-4838-b9dc-f4b0732a59fd
c16 160938_b9e51572-575e-4378-9855-bd645d8548b4
c17 160938_f5489430-0222-4941-8bba-eac68a2c468e
c18 160938_e74d2d3f-ea1f-4ff2-ba61-91f87e1fd4ae
c19 160938_d2403b78-d26e-4c84-9892-0f3a73b4c7e2
LIST
wait
python3 - <<'PY'
from PIL import Image, ImageDraw
import glob,os
fs=sorted(glob.glob('/home/user/w/st/c*.png'))
W,H=126,224; cols=5; rows=(len(fs)+cols-1)//cols
sheet=Image.new('RGB',(cols*W,rows*H),'black'); d=ImageDraw.Draw(sheet)
for i,f in enumerate(fs):
    im=Image.open(f).convert('RGB'); im.thumbnail((W,H)); x,y=(i%cols)*W,(i//cols)*H
    sheet.paste(im,(x,y)); d.rectangle([x,y,x+26,y+12],fill='black'); d.text((x+2,y+1),os.path.basename(f)[:3],fill='yellow')
sheet.save('/home/user/w/sheet_s.jpg',quality=42,optimize=True)
PY
cd /home/user/w && base64 -w0 sheet_s.jpg > sheet_s.b64
echo "META $(wc -c < sheet_s.b64) $(sha256sum sheet_s.jpg | cut -c1-16) chunk=$N"
cut -c$(( (N-1)*CH+1 ))-$(( N*CH )) sheet_s.b64
