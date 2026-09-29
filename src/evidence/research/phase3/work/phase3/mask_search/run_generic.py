"""Exact geometric producers over this worker's queue; audit remains separate."""
from pathlib import Path
import os,sys,json,time,hashlib,subprocess,argparse
from warm_tools import TOP,ROOT,WORK,passed_pattern

HERE=WORK/'generic';HERE.mkdir(exist_ok=True)
ENGINE=TOP/'work/phase3/generic/generic_pose_engine_v5.py'
ENV={**os.environ,'PYTHONPATH':str(TOP/'work/phase3/deps')+os.pathsep+os.environ.get('PYTHONPATH','')}
COVER=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text())
MASKS=COVER['canonical_eleven_cell_subsets'];INV=COVER['symmetry_cell_involution'];CACHE={}
def read(p,default=None):
 try:return json.loads(Path(p).read_text())
 except (FileNotFoundError,json.JSONDecodeError):return default
def save(p,d):
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(d,indent=2)+'\n');q.replace(p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def known(mask):
 a=read(TOP/'work/phase3/audit/overall-union-independent-audit.json')
 if a is None:a=read(TOP/'work/phase3/audit/current-union-independent-audit.json',{})
 if mask not in a.get('remaining_canonical_mask_indices',[mask]):return 'INDEPENDENT_AUDITED_UNION'
 J=set(MASKS[mask]);H={INV[i]for i in J}
 for p in (TOP/'work/phase3').glob('*/patterns.json'):
  arr=read(p,[]);arr=arr.get('patterns',[])if isinstance(arr,dict)else arr
  for r in arr:
   try:
    packet=Path(r['packet']);gate=Path(r['gate']);key=(str(packet),str(gate),packet.stat().st_mtime_ns,gate.stat().st_mtime_ns)
    if key not in CACHE:CACHE[key]=passed_pattern(packet,gate)
    T=set(CACHE[key]['required_cells'])
    if T<=J or T<=H:return 'COMPLETE_EXACT_FIELD'
   except (OSError,KeyError,ValueError,AssertionError):pass
 return None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--case-seconds',type=float,default=60);ap.add_argument('--collision-seconds',type=float,default=150);ap.add_argument('--resume-incomplete',action='store_true');a=ap.parse_args()
 subprocess.run([sys.executable,'-c','import gmpy2'],env=ENV,check=True)
 q=read(HERE/'queue.json')
 if q is None:
  assigned=read(WORK/'queue.json')['assigned_masks'];states=read(WORK/'state.json',{}).get('status',{})
  ranks={'CUT_LIMIT':0,'INCOMPLETE_GATE':1,'REFUTED_CANDIDATE':2,'DENSE_DEFERRED':3,'FEATURE_LIMIT':4,'NO_FINITE_GAP':5}
  assigned.sort(key=lambda m:(ranks.get(states.get(str(m),{}).get('status'),6),m))
  q=[dict(mask=m,state='PENDING',outputs=[])for m in assigned if m not in [438,999,1462,1659]]
 candidates=read(HERE/'candidates.json',[]);start=time.monotonic()
 for r in q:
  if r['state']=='RUNNING':
   old=r.get('current_output')
   if old and Path(old).exists()and old not in r['outputs']:r['outputs'].append(old)
   d=read(old,{})if old else {}
   if d.get('terminal')and d.get('contradiction')and not d.get('constraints'):
    r['state']='PRODUCER_EXCLUSION'
    if old not in candidates:candidates.append(old);save(HERE/'candidates.json',candidates)
   else:r['state']='INCOMPLETE'
  if a.resume_incomplete and r['state']=='INCOMPLETE':r['state']='PENDING_RESUME'
 def checkpoint():
  save(HERE/'queue.json',q);save(HERE/'progress.json',dict(elapsed=time.monotonic()-start,counts={s:sum(r['state']==s for r in q)for s in sorted({r['state']for r in q})},producer_candidates=len(candidates),last=next((r for r in reversed(q)if r['state']=='RUNNING'),None)))
 for r in q:
  if r['state']not in ['PENDING','PENDING_RESUME']:continue
  stop=HERE/'STOP'
  if stop.exists()and stop.read_text().strip()!='RESUME':break
  reason=known(r['mask'])
  if reason:r.update(state='COVERED',reason=reason);checkpoint();continue
  mask=r['mask'];J=MASKS[mask];priority=[i for i in [5,6,9,10,1,2]if i in J][:2]
  stages=[3]if r['state']=='PENDING_RESUME'and r['outputs']else[0,3]
  for partners in stages:
   roundno=len(r['outputs']);stem=f'mask{mask}-p3msg-v5-r{roundno}';out=HERE/(stem+'.json');log=HERE/(stem+'.log');seconds=a.case_seconds if partners==0 else a.collision_seconds
   assert not out.exists(),'Never overwrite a frozen or partial geometric trace'
   cmd=[sys.executable,str(ENGINE),'--output',str(out),'--seconds',str(seconds),'--passes','10','--partners',str(partners),'--priority',','.join(map(str,priority))]
   if partners==3 and r['outputs']:cmd+=['--resume-node','--source',r['outputs'][-1]]
   else:cmd+=['--mask',str(mask)]
   r.update(state='RUNNING',current_output=str(out));checkpoint();print(json.dumps(dict(event='GENERIC_START',mask=mask,path=str(out),priority=priority,partners=partners)),flush=True)
   with log.open('w')as f:
    try:proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=seconds+180,env=ENV);returncode=proc.returncode
    except subprocess.TimeoutExpired:returncode='TIMEOUT'
   d=read(out,{})
   complete=(d.get('terminal')is True and bool(d.get('contradiction'))and not d.get('constraints')and d.get('schema')=='exact_generic_owned_hull_v1'and set(d.get('mask',[]))==set(J))
   r['outputs'].append(str(out));r.update(state='PRODUCER_EXCLUSION'if complete else ('ERROR'if returncode!=0 else 'INCOMPLETE'),returncode=returncode,contradiction=d.get('contradiction'),seconds=d.get('seconds'),partners=partners,sha256=sha(out)if out.exists()else None,independently_audited=False)
   if complete and str(out)not in candidates:candidates.append(str(out));save(HERE/'candidates.json',candidates)
   checkpoint();print(json.dumps(dict(event='GENERIC_COMPLETE',**r)),flush=True)
   if complete or not d.get('terminal'):break
 checkpoint();print(json.dumps(dict(event='GENERIC_QUEUE_CHECKPOINT',producer_candidates=len(candidates))),flush=True)
if __name__=='__main__':main()
