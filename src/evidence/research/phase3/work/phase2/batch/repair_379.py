from pathlib import Path
import json,subprocess,sys,os,time,hashlib,concurrent.futures,numpy as np
HERE=Path(__file__).parent;TOP=HERE.parents[1];ROOT=TOP.parent/'current';BASE=ROOT/'research/optimality/deficit_geometry/physical_features';ENV={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONPATH':str(TOP/'audit/deps')};U='387708359002281417731/100000000000000000000';GROUPS=json.loads((TOP/'geometry/wall_ownership_groups.json').read_text())['groups'];START=time.monotonic();HISTORY=[]
def run(script,args,label,timeout=200):
 with(HERE/(label+'.log')).open('w')as f:subprocess.run([sys.executable,str(script),*map(str,args)],env=ENV,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=timeout)
def save():
 (HERE/'repair379-progress.json').write_text(json.dumps(dict(history=HISTORY,elapsed=time.monotonic()-START),indent=2)+'\n')
def pool_one(entry):
 mask=entry['mask'];gate=Path(entry['receipt']);prefix=f'mask{mask}-p2batchpool';source=BASE/(prefix+'-source.json');source.write_bytes(gate.read_bytes());exact=BASE/(prefix+'-exact.npz');jitter=BASE/(prefix+'-jitter.npz')
 if not exact.exists():run(BASE/'add_exact_refuter.py',[source,'--output',exact],prefix+'-capture',200)
 if not jitter.exists():run(BASE/'jitter_refuter.py',[exact,'--output',jitter,'--count','1024'],prefix+'-jitter',200)
 print(json.dumps(dict(status='EXACT_REFUTER_POOL_ADDED',mask=mask,exact=str(exact),jitter=str(jitter))),flush=True)
 return [exact,jitter]
def extras():
 e=[ROOT/p for p in json.loads((BASE/'mask2147-sep27wallr6-result.json').read_text())['additional_exact_capture_files']]
 for pattern in ['*exact.npz','*refuter.npz','*jitter.npz']:
  for p in sorted(BASE.glob(pattern)):
   try:
    d=json.loads(p.with_suffix('.json').read_text())
    if d['parent_Uplus']==U:e.append(p)
   except(FileNotFoundError,KeyError,json.JSONDecodeError):pass
 return [p for p in dict.fromkeys(e) if {'rows','memberships','legal','fivepoint_captures','generator_captures','poses'}<=set(np.load(p).files)]
def main():
 entries=json.loads((HERE/'multi-history.json').read_text())
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:
  for _ in ex.map(pool_one,entries):pass
 for mask in [379,391]:
  prev=None
  for iteration in range(1,6):
   tag=f'p2batchrepair{iteration}';stem=f'mask{mask}-{tag}'
   if prev:
    exact=BASE/(stem+'-exact.npz');jitter=BASE/(stem+'-jitter.npz');run(BASE/'add_exact_refuter.py',[prev,'--output',exact],stem+'-capture');run(BASE/'jitter_refuter.py',[exact,'--output',jitter,'--count','1024'],stem+'-jitter')
   extra=extras();run(BASE/'solve_sep27_wall.py',['--mask',mask,'--tag',tag,'--dataset',BASE/'owned-tight','--ownership','cell_fivepoints','--seconds',75]+[v for p in extra for v in ['--extra',p]],stem+'-solve',180)
   finite=json.loads((BASE/(stem+'-result.json')).read_text());e=dict(mask=mask,iteration=iteration,extra_files=len(extra),finite_budget=finite.get('best_budget'),features=finite.get('positive_weight_count'))
   if finite.get('best_budget',12)>=11 or finite.get('positive_weight_count',100)>80:
    e['status']='NO_USEFUL_FINITE_CANDIDATE';HISTORY.append(e);save();print(json.dumps(e),flush=True);break
   run(BASE/'freeze.py',['--mask',mask,'--tag',tag],stem+'-freeze');packet=BASE/(stem+'-packet.json');d=json.loads(packet.read_text());d.pop('ownership_offsets_unit',None);d.update(ownership_points_field=GROUPS,wall_aware_ownership_extension=True);packet.write_text(json.dumps(d,indent=2)+'\n');arith=BASE/(stem+'-mask-arithmetic.json');a=json.loads(arith.read_text());a['pre_ownership_extension_packet_sha256']=a['packet_sha256'];a['packet_sha256']=hashlib.sha256(packet.read_bytes()).hexdigest();arith.write_text(json.dumps(a,indent=2)+'\n')
   gate=BASE/(stem+'-exact-gate.json');run(TOP/'geometry/verify_wall_aware_mask.py',[packet,'--output',gate,'--bins',64,'--max-depth',16,'--max-rows',16000,'--seconds',120],stem+'-gate',180);g=json.loads(gate.read_text());e.update(status=g['status'],last=g['records'][-1]['status'],cell=g['records'][-1]['cell'],packet=str(packet),gate=str(gate),rows=g['rows'],budget=d['certificate']['budget_units'],seconds=g['seconds']);HISTORY.append(e);save();print(json.dumps(e),flush=True)
   if g['status'].startswith('PASS_'):return
   if e['last']!='REFUTED_BY_LEGAL_PARENT':break
   prev=gate
if __name__=='__main__':main()
