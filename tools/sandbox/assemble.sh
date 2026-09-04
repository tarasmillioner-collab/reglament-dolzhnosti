#!/bin/bash
# Assemble excerpt/full in the Higgsfield sandbox.
# Usage: assemble.sh <t_from> <t_to> <out.mp4> [upload_url]
# Inputs pulled from the repo branch (raw.githubusercontent): work/stage5/{clips.json,timeline.json,captions.ass}, work/stage5/vo.json (source mp3 url)
# Rules: seedance_2_0_mini 480p clips only (R1); one continuous VO (R7) with atempo from vo_measure.json; picture cut to card timeline.
set -e
T0=${1:-0}; T1=${2:-41.98}; OUT=${3:-/home/user/out.mp4}; UP="$4"
RAW=https://raw.githubusercontent.com/tarasmillioner-collab/reglament-dolzhnosti/claude/vsl-clone-factory-34f2yn
cd /home/user && mkdir -p asm && cd asm
for f in clips.json timeline.json captions.ass vo_measure.json vo.json; do curl -sf -o $f "$RAW/work/stage5/$f"; done
curl -sf -o clips6.json "$RAW/work/stage6/clips.json" || echo '[]' > clips6.json
curl -sf -o endcard.ass "$RAW/work/stage6/endcard.ass" || rm -f endcard.ass
VO_URL=$(python3 -c "import json;print(json.load(open('vo.json'))['url'])")
AT=$(python3 -c "import json;print(json.load(open('vo_measure.json'))['atempo'])")
[ -s vo_src.mp3 ] || curl -sf -o vo_src.mp3 "$VO_URL"
ffmpeg -y -loglevel error -i vo_src.mp3 -filter:a "atempo=$AT,loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 vo.wav
python3 - "$T0" "$T1" <<'PY'
import json,subprocess,sys,os
t0=float(sys.argv[1]); t1=float(sys.argv[2])
clips={c['shot']:c for c in json.load(open('clips.json'))+json.load(open('clips6.json')) if c.get('url') or c.get('image_url')}
tl=json.load(open('timeline.json'))
shots=[]
for c in tl:
    if c['end']<=t0 or c['start']>=t1: continue
    if shots and shots[-1]['shot']==c['shot']: shots[-1]['end']=min(c['end'],t1)
    else: shots.append({'shot':c['shot'],'start':max(c['start'],t0),'end':min(c['end'],t1)})
parts=[]
for i,s in enumerate(shots):
    d=s['end']-s['start']; c=clips.get(s['shot'])
    seg=f'seg{i:03d}.mp4'
    if c and c.get('image_url') and not c.get('url'):
        # static plate (end card): still image held for the shot, slow 3% push-in
        src=f"plate{s['shot']:02d}.png"
        if not os.path.exists(src): subprocess.run(['curl','-sf','-o',src,c['image_url']],check=True)
        n=int(round(d*30))
        subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',src,'-vf',f"scale=960:1708:force_original_aspect_ratio=increase,crop=960:1708,zoompan=z='1+0.03*on/{n}':d={n}:s=480x854:fps=30",'-t',f'{d:.3f}','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',seg],check=True)
    elif c:
        src=f"clip{s['shot']:02d}.mp4"
        if not os.path.exists(src): subprocess.run(['curl','-sf','-o',src,c['url']],check=True)
        # trim to d; if the clip is shorter, freeze the last frame (tpad)
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',src,'-an','-vf',f'scale=480:854:force_original_aspect_ratio=increase,crop=480:854,fps=30,tpad=stop_mode=clone:stop_duration={d+1:.3f}','-t',f'{d:.3f}','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',seg],check=True)
    else:
        subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i',f'color=c=0x1b1b1b:s=480x854:r=30','-t',f'{d:.3f}','-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p',seg],check=True)
    parts.append(seg)
open('list.txt','w').write(''.join(f"file '{p}'\n" for p in parts))
print('segments',len(parts),'span',round(shots[0]['start'],2),round(shots[-1]['end'],2))
PY
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy video.mp4
DUR=$(python3 -c "print(round($T1-$T0,3))")
VF="ass=captions.ass"; [ -s endcard.ass ] && VF="$VF,ass=endcard.ass"
ffmpeg -y -loglevel error -i video.mp4 -ss $T0 -t $DUR -i vo.wav -vf "$VF" -map 0:v -map 1:a -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k -shortest "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,codec_name -of csv=p=0 "$OUT"
sha256sum "$OUT" | cut -c1-16; ls -l "$OUT" | awk '{print $5}'
if [ -n "$UP" ]; then curl -sf -X PUT --upload-file "$OUT" "$UP" -o /dev/null -w "upload_http=%{http_code}\n"; fi
