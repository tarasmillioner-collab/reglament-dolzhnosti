#!/bin/bash
# Measure a delivered mp4 inside the Higgsfield sandbox (local machine cannot reach the CDN):
#   ffprobe, integrated LUFS, longest silence, caption drift (faster-whisper words vs captions.ass karaoke),
#   contact sheets for judges (1 tile per shot at shot midpoint), end-card crop.
# Usage: verify.sh <mp4 url> <t0> <t1> <name>      -> /home/user/v/<name>_metrics.json, <name>_sheet.jpg, <name>_endcard.jpg
set -e
U="$1"; T0=${2:-0}; T1=${3:-41.98}; N=${4:-excerpt}
RAW=https://raw.githubusercontent.com/tarasmillioner-collab/reglament-dolzhnosti/claude/vsl-clone-factory-34f2yn
mkdir -p /home/user/v && cd /home/user/v
[ -s $N.mp4 ] || curl -sf -o $N.mp4 "$U"
curl -sf -o timeline.json "$RAW/work/stage5/timeline.json"; curl -sf -o captions.ass "$RAW/work/stage5/captions.ass"
ffprobe -v error -show_entries format=duration:stream=width,height,codec_name -of json $N.mp4 > probe.json
ffmpeg -nostats -i $N.mp4 -vn -af ebur128 -f null - 2>&1 | grep -E "^ +I:" | tail -1 | tr -s ' ' > lufs.txt
ffmpeg -nostats -i $N.mp4 -vn -af silencedetect=n=-35dB:d=0.6 -f null - 2>&1 | grep -o "silence_duration: [0-9.]*" | awk '{print $2}' | sort -n | tail -1 > gap.txt
ffmpeg -y -loglevel error -i $N.mp4 -vn -ar 16000 -ac 1 a.wav
python3 - "$T0" "$T1" "$N" <<'PY'
import json,re,sys,subprocess,statistics
t0=float(sys.argv[1]); t1=float(sys.argv[2]); N=sys.argv[3]
from faster_whisper import WhisperModel
m=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=8)
segs,info=m.transcribe('a.wav',language='uk',word_timestamps=True,beam_size=1,vad_filter=False)
ww=[(x.word.strip().lower(),x.start) for s in segs for x in s.words]
# ASS karaoke -> (word, abs start)
def ts(s):
    h,mm,ss=s.split(':'); return int(h)*3600+int(mm)*60+float(ss)
aw=[]
for line in open('captions.ass',encoding='utf-8'):
    if not line.startswith('Dialogue:'): continue
    p=line.split(',',9); st=ts(p[1]); txt=p[9].strip()
    if st<t0 or st>=t1: continue
    t=st-t0
    for k,w in re.findall(r'\{\\k(\d+)\}([^{]*)',txt):
        w=w.strip().lower()
        if w: aw.append((w,round(t,2))); t+=int(k)/100
norm=lambda s: re.sub(r'[^\w]','',s)
# align by normalized-text matches in order (greedy)
d=[]; j=0
for w,t in aw:
    for k in range(j,min(j+6,len(ww))):
        if norm(ww[k][0])==norm(w) and norm(w):
            d.append((ww[k][1]-t)*1000); j=k+1; break
med=statistics.median([abs(x) for x in d]) if d else None
pr=json.load(open('probe.json')); v=[s for s in pr['streams'] if s['codec_name']!='aac'][0]
out={'name':N,'duration':round(float(pr['format']['duration']),2),'w':v['width'],'h':v['height'],
     'lufs':open('lufs.txt').read().strip(),'max_gap_s':float(open('gap.txt').read().strip() or 0),
     'asr_words':len(ww),'ass_words':len(aw),'matched':len(d),'median_abs_drift_ms':round(med,1) if med is not None else None,
     'p90_abs_drift_ms':round(sorted(abs(x) for x in d)[int(len(d)*0.9)],1) if d else None}
json.dump(out,open(N+'_metrics.json','w'),ensure_ascii=False); print(json.dumps(out,ensure_ascii=False))
# contact sheet: one tile per shot at its midpoint (within [t0,t1])
tl=json.load(open('timeline.json')); shots={}
for c in tl:
    if c['end']<=t0 or c['start']>=t1: continue
    s=shots.setdefault(c['shot'],[c['start'],c['end']]); s[0]=min(s[0],c['start']); s[1]=max(s[1],c['end'])
from PIL import Image, ImageDraw
tiles=[]
for sh in sorted(shots):
    a,b=shots[sh]; mid=(max(a,t0)+min(b,t1))/2-t0
    subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',f'{mid:.2f}','-i',N+'.mp4','-frames:v','1','-vf','scale=120:213',f'f{sh:02d}.jpg'],check=True)
    im=Image.open(f'f{sh:02d}.jpg'); ImageDraw.Draw(im).text((2,2),f'{sh}',fill=(255,255,0)); tiles.append(im)
cols=7 if len(tiles)>20 else 6; rows=(len(tiles)+cols-1)//cols
sheet=Image.new('RGB',(cols*120,rows*213))
for i,im in enumerate(tiles): sheet.paste(im,((i%cols)*120,(i//cols)*213))
sheet.save(N+'_sheet.jpg',quality=42,optimize=True)
if t1>195:
    subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',f'{199.0-t0:.2f}','-i',N+'.mp4','-frames:v','1','-vf','scale=240:427','-q:v','5',N+'_endcard.jpg'],check=True)
import os; print({f:os.path.getsize(f) for f in os.listdir('.') if f.endswith('.jpg') and '_' in f})
PY
