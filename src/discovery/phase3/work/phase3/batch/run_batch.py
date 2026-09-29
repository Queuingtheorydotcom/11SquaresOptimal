"""Phase3 counterexample-guided exact gates; finite proposals are never proofs."""
from pathlib import Path
import json,subprocess,sys,os,time,hashlib,threading,concurrent.futures,argparse
import numpy as np
HERE=Path(__file__).resolve().parent;TOP=HERE.parents[1];ROOT=TOP.parent/'current';BASE=ROOT/'research/optimality/deficit_geometry/physical_features';PHASE=HERE.parent;U='387708359002281417731/100000000000000000000';ENV={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONPATH':str(TOP/'audit/deps')};LOCK=threading.RLock();START=time.monotonic();GROUPS=json.loads((TOP/'geometry/wall_ownership_groups.json').read_text())['groups'];COVER=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text());CONTROLS={438,999,1462,1659};QUEUE=HERE/'queue.json';HISTORY=HERE/'history.jsonl';PATTERNS=HERE/'patterns.json';PROGRESS=HERE/'progress.json'
def read(p,default=None):
 try:return json.loads(p.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return default

def atomic(p,d):
 temp=p.with_suffix('.tmp');temp.write_text(json.dumps(d,indent=2)+'\n');temp.replace(p)
def record(e):
 with LOCK:
  e=dict(unix_time=time.time(),elapsed=time.monotonic()-START,**e)
  with HISTORY.open('a')as f:f.write(json.dumps(e)+'\n')
  print(json.dumps(e),flush=True)

def script(name,args,label,timeout):
 if Path(name).name=='solve_sep27_wall.py':name=HERE/'fast_solve_cli.py'
 with(HERE/(label+'.log')).open('w')as f:
  subprocess.run([sys.executable,str(name),*map(str,args)],cwd=ROOT,env=ENV,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=timeout)

def extras():
 paths=[ROOT/p for p in read(BASE/'mask2147-sep27wallr6-result.json')['additional_exact_capture_files']]
 for pattern in ['*exact.npz','*refuter.npz','*jitter.npz']:
  for p in sorted(BASE.glob(pattern)):
   d=read(p.with_suffix('.json'),{})
   if d.get('parent_Uplus')==U:paths.append(p)
 out=[]
 for p in dict.fromkeys(paths):
  try:
   with np.load(p)as z:
    if {'rows','memberships','legal','fivepoint_captures','generator_captures','poses'}<=set(z.files) and z['rows'].shape[1]==1232:out.append(p)
  except (OSError,ValueError):pass
 return out

def known_exclusion(mask):
 J=set(COVER['canonical_eleven_cell_subsets'][mask]);T={15-i for i in J}
 audit=read(PHASE/'audit/current-union-independent-audit.json',{})
 for key in ['excluded_canonical_mask_indices','excluded_mask_indices','excluded']:
  if mask in audit.get(key,[]):return dict(kind='INDEPENDENT_AUDIT',source=str(PHASE/'audit/current-union-independent-audit.json'))
 for p in PHASE.glob('*/patterns.json'):
  values=read(p,[])
  if isinstance(values,dict):values=values.get('patterns',[])
  for v in values:
   if not str(v.get('status','')).startswith('PASS_EXACT_'):continue
   required=set(v.get('required_cells',[]))
   if required and (required<=J or required<=T):return dict(kind='COMPLETE_EXACT_PRODUCER_PATTERN',source=str(p),required_cells=sorted(required),packet=v.get('packet'),gate=v.get('gate'))
 return None

def publish(mask,packet,gate,final):
 p=read(packet);g=read(gate);assert g['status']=='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION' and g['continuum_masks_excluded']==1;assert g['packet_sha256']==hashlib.sha256(packet.read_bytes()).hexdigest();positive={i for i,x in enumerate(p['threshold_units'])if x};support=set(p.get('conditional_owner_support',p['mask']));v=dict(mask=mask,status=g['status'],required_cells=sorted(positive|support),positive_cells=sorted(positive),conditional_owner_support=sorted(support),packet=str(packet),gate=str(gate),bins=32,rows=g['rows'],final=final,global_optimality_proved=False)
 with LOCK:
  arr=read(PATTERNS,[]);arr=[x for x in arr if x['mask']!=mask];arr.append(v);atomic(PATTERNS,arr)
 record(dict(event='EXACT_PATTERN',**v));return v

def gate(packet,label,seconds=90):
 out=BASE/(label+'-exact-gate.json');script(TOP/'geometry/verify_wall_aware_mask.py',[packet,'--output',out,'--bins',32,'--max-depth',16,'--max-rows',20000,'--seconds',seconds],label+'-gate',seconds+90);g=read(out);return out,g

def minimize(mask,packet,out,label):
 p=read(packet);owners=p['mask'].copy();positive={i for i,g in enumerate(p['threshold_units'])if g};centers=[np.array([float(__import__('fractions').Fraction(z))for z in c['center']])for c in COVER['cells']];order=sorted(set(owners)-positive,key=lambda i:min(np.linalg.norm(centers[i]-centers[j])for j in positive),reverse=True);bestp=packet;bestg=out
 for drop in order:
  trial=dict(p,conditional_owner_support=[j for j in owners if j!=drop]);pp=BASE/(label+f'-omit{drop}-packet.json');pp.write_text(json.dumps(trial,indent=2)+'\n');gg,g=gate(pp,label+f'-omit{drop}',75);success=g['status'].startswith('PASS_EXACT_');record(dict(event='OWNER_MINIMIZATION',mask=mask,drop=drop,status=g['status'],last=g['records'][-1]['status'],packet=str(pp),gate=str(gg)))
  if success:p=trial;owners.remove(drop);bestp=pp;bestg=gg;publish(mask,bestp,bestg,False)
 for drop in sorted(positive,key=lambda i:p['threshold_units'][i]):
  if sum(p['threshold_units'][i]for i in p['mask'])-p['threshold_units'][drop]<=p['certificate']['budget_units']:continue
  gamma=p['threshold_units'].copy();gamma[drop]=0;trial=dict(p,threshold_units=gamma,positive_cells=[i for i,g in enumerate(gamma)if g],conditional_counting_surplus_units=sum(gamma[i]for i in p['mask'])-p['certificate']['budget_units'],conditional_owner_support=[j for j in owners if j!=drop]);pp=BASE/(label+f'-dropcharged{drop}-packet.json');pp.write_text(json.dumps(trial,indent=2)+'\n');gg,g=gate(pp,label+f'-dropcharged{drop}',75);success=g['status'].startswith('PASS_EXACT_');record(dict(event='CHARGED_CELL_MINIMIZATION',mask=mask,drop=drop,status=g['status'],last=g['records'][-1]['status'],packet=str(pp),gate=str(gg)))
  if success:p=trial;owners.remove(drop);bestp=pp;bestg=gg;publish(mask,bestp,bestg,False)
 return publish(mask,bestp,bestg,True)

def task(row,args):
 mask=row['mask'];attempt=row.get('attempts',0)+1;prefix=f'mask{mask}-p3batcha{attempt}';previous=None
 try:
  for iteration in range(1,args.repairs+1):
   if known_exclusion(mask):return dict(state='COVERED_BY_NEW_PATTERN',exclusion=known_exclusion(mask))
   stem=prefix+f'r{iteration}';tag=stem.split('-',1)[1]
   if previous:
    exact=BASE/(stem+'-exact.npz');jitter=BASE/(stem+'-jitter.npz');script(BASE/'add_exact_refuter.py',[previous,'--output',exact],stem+'-capture',180);script(BASE/'jitter_refuter.py',[exact,'--output',jitter,'--count',512],stem+'-jitter',180)
   pool=extras();script(BASE/'solve_sep27_wall.py',['--mask',mask,'--tag',tag,'--dataset',BASE/'owned-tight','--ownership','cell_fivepoints','--seconds',60]+[v for p in pool for v in ['--extra',p]],stem+'-solve',180);finite=read(BASE/(stem+'-result.json'));entry=dict(event='FINITE_TRAINING',mask=mask,attempt=attempt,iteration=iteration,archive_count=len(pool),finite_budget=finite.get('best_budget'),features=finite.get('positive_weight_count'),geometry_coverage=False);record(entry)
   if finite.get('best_budget',12)>=11-1e-9:return dict(state='NO_FINITE_GAP',last=entry)
   if finite.get('positive_weight_count',999)>args.max_features:return dict(state='DENSE_FINITE_PROPOSAL_DEFERRED',last=entry)
   script(BASE/'freeze.py',['--mask',mask,'--tag',tag],stem+'-freeze',180);pp=BASE/(stem+'-packet.json');p=read(pp);p.pop('ownership_offsets_unit',None);p.update(ownership_points_field=GROUPS,wall_aware_ownership_extension=True);pp.write_text(json.dumps(p,indent=2)+'\n');ar=BASE/(stem+'-mask-arithmetic.json');a=read(ar);a['pre_ownership_extension_packet_sha256']=a['packet_sha256'];a['packet_sha256']=hashlib.sha256(pp.read_bytes()).hexdigest();atomic(ar,a)
   gg,g=gate(pp,stem,args.gate_seconds);entry=dict(event='EXACT_GATE',mask=mask,attempt=attempt,iteration=iteration,status=g['status'],last=g['records'][-1]['status'],cell=g['records'][-1]['cell'],rows=g['rows'],seconds=g['seconds'],packet=str(pp),gate=str(gg));record(entry)
   if g['status'].startswith('PASS_EXACT_'):
    publish(mask,pp,gg,False);v=minimize(mask,pp,gg,stem);return dict(state='EXACT_PATTERN_PROVED',pattern=v)
   if entry['last']!='REFUTED_BY_LEGAL_PARENT':return dict(state='UNRESOLVED_EXACT_GATE',last=entry)
   previous=gg
  terminal=BASE/(prefix+'-terminal-exact.npz');jitter=BASE/(prefix+'-terminal-jitter.npz');script(BASE/'add_exact_refuter.py',[previous,'--output',terminal],prefix+'-terminal-capture',180);script(BASE/'jitter_refuter.py',[terminal,'--output',jitter,'--count',256],prefix+'-terminal-jitter',180)
  return dict(state='REPAIR_LIMIT',last=entry,terminal_exact=str(terminal),terminal_jitter=str(jitter))
 except Exception as e:
  record(dict(event='TASK_ERROR',mask=mask,error=repr(e)));return dict(state='ERROR',error=repr(e))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);ap.add_argument('--seconds',type=int,default=2400);ap.add_argument('--repairs',type=int,default=5);ap.add_argument('--max-features',type=int,default=24);ap.add_argument('--gate-seconds',type=int,default=90);args=ap.parse_args()
 q=read(QUEUE)
 if q is None:
  ids=read(TOP/'phase2/audit/remaining-mask-indices.json')[220:440];screen={x['mask']:x for x in map(json.loads,(TOP/'phase2/screen/results.jsonl').read_text().splitlines())};seen={};rows=[]
  for m in sorted(ids,key=lambda m:(screen[m].get('positive_features',999)>12,screen[m].get('positive_features',999)>4,screen[m].get('finite_budget',99),screen[m].get('positive_features',999),m)):
   s=screen[m];z=np.load(TOP/f'phase2/screen/weights-{m}.npz');key=str((np.flatnonzero(z['weights']>1e-10).tolist(),np.flatnonzero(z['gamma']>1e-10).tolist()));repeat=seen.get(key,0);seen[key]=repeat+1;rows.append(dict(mask=m,state='CONTROL_RESERVED'if m in CONTROLS else'PENDING',rank=[repeat,s.get('positive_features',999)>12,s.get('positive_features',999)>4,s.get('finite_budget',99),s.get('positive_features',999),m],screen_budget=s.get('finite_budget'),screen_features=s.get('positive_features'),attempts=0))
  q=sorted(rows,key=lambda r:r['rank']);atomic(QUEUE,q)
 for r in q:
  if r['state']=='RUNNING':r['state']='PENDING'
 running={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers)as pool:
  while True:
   with LOCK:
    for r in q:
     if r['state']=='PENDING' and known_exclusion(r['mask']):r.update(state='COVERED_BY_NEW_PATTERN',exclusion=known_exclusion(r['mask']))
    if time.monotonic()-START<args.seconds and (not (HERE/'STOP').exists() or (HERE/'STOP').read_text().strip()=='RESUME'):
     for r in q:
      if len(running)>=args.workers:break
      if r['state']!='PENDING':continue
      r['state']='RUNNING';r['attempts']+=1;running[pool.submit(task,dict(r,attempts=r['attempts']-1),args)]=r;record(dict(event='TASK_START',mask=r['mask'],attempt=r['attempts']))
    atomic(QUEUE,q);atomic(PROGRESS,dict(elapsed=time.monotonic()-START,counts={s:sum(r['state']==s for r in q)for s in sorted({r['state']for r in q})},running=[r['mask']for r in running.values()],global_optimality_proved=False))
   if not running:break
   done,_=concurrent.futures.wait(running,timeout=10,return_when=concurrent.futures.FIRST_COMPLETED)
   for future in done:
    row=running.pop(future);row.update(future.result());record(dict(event='TASK_COMPLETE',mask=row['mask'],state=row['state']))
  atomic(QUEUE,q)
if __name__=='__main__':main()
