"""Parallel exact geometric discovery. No producer result enters the audited count."""
from pathlib import Path
import json,os,sys,subprocess,time,concurrent.futures,threading,argparse,hashlib
HERE=Path(__file__).parent;ROOT=HERE.parents[2];LOCK=threading.Lock();START=time.monotonic()
COVER=json.loads((ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json').read_text())
def read(p,default=None):
 try:return json.loads(p.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return default
def save(p,d):
 t=p.with_suffix('.writing');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(p)
def known(mask):
 a=read(ROOT/'work/phase3/audit/overall-union-independent-audit.json') or read(ROOT/'work/phase3/audit/current-union-independent-audit.json',{})
 if mask not in a.get('remaining_canonical_mask_indices',[mask]):return 'INDEPENDENT_FIELD_UNION'
 J=set(COVER['canonical_eleven_cell_subsets'][mask]);H={15-i for i in J}
 for p in (ROOT/'work/phase3').glob('*/patterns.json'):
  arr=read(p,[])
  if isinstance(arr,dict):arr=arr.get('patterns',[])
  for d in arr:
   required=set(d.get('required_cells',[]))
   if d.get('status','').startswith('PASS_EXACT_') and required and (required<=J or required<=H):return 'COMPLETE_FIELD_PENDING_OR_PASSED_AUDIT'
 for p in HERE.glob(f'mask{mask}-generic-v*.json'):
  d=read(p,{})
  if d.get('contradiction') and len(d.get('mask',[]))==11:return 'COMPLETE_GENERIC_PENDING_OR_PASSED_AUDIT'
 return None
def task(mask,seconds):
 J=COVER['canonical_eleven_cell_subsets'][mask];priority=[i for i in [5,6,9,10,1,2] if i in J][:2]
 out=HERE/f'mask{mask}-hull-first-v5.json';log=HERE/f'mask{mask}-hull-first-v5.log'
 first_seconds=min(60,seconds)
 with log.open('w') as f:
  proc=subprocess.run([sys.executable,str(HERE/'generic_pose_engine_v5.py'),'--mask',str(mask),'--output',str(out),'--seconds',str(first_seconds),'--passes','12','--partners','0','--priority',','.join(map(str,priority))],stdout=f,stderr=subprocess.STDOUT)
 d=read(out,{})
 if not d.get('contradiction') and d.get('terminal') and proc.returncode==0:
  parent=out;out=HERE/f'mask{mask}-collision-followup-v5.json';log=HERE/f'mask{mask}-collision-followup-v5.log'
  with log.open('w') as f:
   proc=subprocess.run([sys.executable,str(HERE/'generic_pose_engine_v5.py'),'--resume-node','--source',str(parent),'--output',str(out),'--seconds',str(max(30,seconds-first_seconds)),'--passes','10','--partners','3','--priority',','.join(map(str,priority))],stdout=f,stderr=subprocess.STDOUT)
  d=read(out,{})
 return dict(state='PRODUCER_EXCLUSION' if d.get('contradiction') else 'INCOMPLETE',returncode=proc.returncode,
             path=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest() if out.exists() else None,
             contradiction=d.get('contradiction'),seconds=d.get('seconds'),independently_audited=False)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);ap.add_argument('--seconds',type=int,default=3600);ap.add_argument('--case-seconds',type=int,default=150);args=ap.parse_args()
 qpath=HERE/'queue.json';q=read(qpath)
 if q is None:
  original=read(ROOT/'work/phase3/root/queue.json');q=[dict(mask=r['mask'],state='PENDING',rank=r['rank']) for r in original if r['mask'] not in [438,999,1462,1659]]
 for r in q:
  if r['state']=='RUNNING':r['state']='PENDING'
 active={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
  while True:
   stop=HERE/'STOP_QUEUE';halt=stop.exists() and stop.read_text().strip()!='RESUME'
   for r in q:
    if r['state']=='PENDING':
     reason=known(r['mask'])
     if reason:r.update(state='COVERED_OR_ALREADY_PRODUCED',reason=reason)
   if not halt and time.monotonic()-START<args.seconds:
    for r in q:
     if len(active)>=args.workers:break
     if r['state']=='PENDING':
      r['state']='RUNNING';active[pool.submit(task,r['mask'],args.case_seconds)]=r
      print(json.dumps(dict(event='START',mask=r['mask'])),flush=True)
   save(qpath,q);save(HERE/'queue-progress.json',dict(elapsed=time.monotonic()-START,counts={s:sum(r['state']==s for r in q) for s in sorted({r['state'] for r in q})},running=[r['mask'] for r in active.values()]))
   if not active:break
   done,_=concurrent.futures.wait(active,timeout=10,return_when=concurrent.futures.FIRST_COMPLETED)
   for f in done:
    r=active.pop(f)
    try:r.update(f.result())
    except Exception as e:r.update(state='ERROR',error=repr(e))
    print(json.dumps(dict(event='COMPLETE',**r)),flush=True)
  save(qpath,q)
if __name__=='__main__':main()
