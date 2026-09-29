"""Search proper owner subsets; only full continuum gates publish patterns.

This search ranks candidates by their current independently unresolved cases.
The original canonical eleven-cell mask is always retained in every packet.
"""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys, time
import pattern_solver as ps

HERE=Path(__file__).resolve().parent
PHASE=HERE.parent
TOP=HERE.parents[1]
ROOT=TOP.parent/'current'
BASE=ps.OUT
OUT=PHASE/'batch_recursive'
OUT.mkdir(exist_ok=True)
ENV={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONPATH':str(TOP/'audit/deps')}
GROUPS=json.loads((TOP/'geometry/wall_ownership_groups.json').read_text())['groups']
COVER=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text())['canonical_eleven_cell_subsets']

def read(p,default=None):
 try:return json.loads(p.read_text())
 except (OSError,json.JSONDecodeError):return default

def save(p,x):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)

def key(J):return ','.join(map(str,sorted(J)))

def emit(e):
 e=dict(unix_time=time.time(),**e)
 with (OUT/'history.jsonl').open('a') as f:f.write(json.dumps(e)+'\n')
 print(json.dumps(e),flush=True)

def run(script,args,label,timeout=180):
 with (OUT/(label+'.log')).open('w') as f:
  subprocess.run([sys.executable,str(script),*map(str,args)],cwd=ROOT,env=ENV,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=timeout)

def all_patterns():
 ans=[]
 for f in PHASE.glob('*/patterns.json'):
  d=read(f,[]);d=d.get('patterns',[]) if isinstance(d,dict) else d
  for p in d:
   if str(p.get('status','')).startswith('PASS_EXACT_'):
    ans.append(dict(p,producer=str(f.parent.name)))
 return ans

def candidates(done,producers):
 pats=all_patterns();known=[set(p['required_cells']) for p in pats]
 # Separate recursive workers share attempted owner sets, including in-flight work.
 # This is only scheduling: no finite failure is promoted to an exclusion.
 shared_attempts=set()
 for f in PHASE.glob('batch*recursive/history.jsonl'):
  if f.parent==OUT:continue
  for line in f.read_text().splitlines():
   try:r=json.loads(line)
   except json.JSONDecodeError:continue
   if r.get('event')=='TASK_START':shared_attempts.add(key(r['required_cells']))
 frontier=PHASE/'audit/overall-remaining-mask-indices.json'
 if not frontier.exists():frontier=PHASE/'audit/remaining-mask-indices.json'
 remain=read(frontier,[])
 masks=[set(COVER[i]) for i in remain];twists=[{15-j for j in J} for J in masks]
 ans={}
 for p in pats:
  if p['producer'] not in producers or not p.get('final'):continue
  owners=set(p['required_cells'])
  if len(owners)<5:continue
  for drop in sorted(owners):
   J=owners-{drop};T={15-j for j in J};k=key(J)
   if k in done or k in shared_attempts or any(K<=J or K<=T for K in known):continue
   gain=sum(J<=M or J<=N for M,N in zip(masks,twists))
   if gain==0:continue
   e=dict(mask=p['mask'],parent_packet=p['packet'],parent_required_cells=sorted(owners),drop=drop,required_cells=sorted(J),prospective_gain=gain)
   if k not in ans or p['mask']<ans[k]['mask']:ans[k]=e
 return sorted(ans.values(),key=lambda r:(-r['prospective_gain'],len(r['required_cells']),r['mask'],r['drop']))

def attempt(c,args):
 J=c['required_cells'];mask=c['mask'];kid=hashlib.sha256(key(J).encode()).hexdigest()[:10];previous=None
 for iteration in range(1,args.repairs+1):
  tag=f'{args.tag_prefix}{kid}r{iteration}';stem=f'mask{mask}-{tag}'
  if previous:
   ex=BASE/(stem+'-exact.npz');ji=BASE/(stem+'-jitter.npz')
   run(BASE/'add_exact_refuter.py',[previous,'--output',ex],stem+'-capture')
   run(BASE/'jitter_refuter.py',[ex,'--output',ji,'--count',512],stem+'-jitter')
  finite=ps.solve(mask,tag,J,seconds=30,extra=[p for p,n,e in ps.compatible()])
  e=dict(c,pattern_id=f'pattern-{kid}',iteration=iteration,tag=tag,finite_budget=finite.get('best_budget'),features=finite.get('positive_weight_count'))
  if finite.get('best_budget',99)>=10.999:emit(dict(e,status='NO_FINITE_GAP',geometry_coverage=False));return dict(e,status='NO_FINITE_GAP')
  if finite.get('positive_weight_count',999)>args.max_features:emit(dict(e,status='DENSE_FINITE_PROPOSAL_DEFERRED',geometry_coverage=False));return dict(e,status='DENSE_FINITE_PROPOSAL_DEFERRED')
  run(BASE/'freeze.py',['--mask',mask,'--tag',tag],stem+'-freeze')
  packet=BASE/(stem+'-packet.json');p=read(packet)
  assert p['mask']==COVER[mask]
  assert not any(g for i,g in enumerate(p['threshold_units']) if i not in J)
  p.pop('ownership_offsets_unit',None)
  p.update(ownership_points_field=GROUPS,conditional_owner_support=J,wall_aware_ownership_extension=True)
  p['positive_cells']=[i for i,g in enumerate(p['threshold_units']) if g]
  p['conditional_counting_surplus_units']=sum(p['threshold_units'][i] for i in p['mask'])-p['certificate']['budget_units']
  save(packet,p)
  ap=BASE/(stem+'-mask-arithmetic.json');a=read(ap)
  a['pre_ownership_extension_packet_sha256']=a['packet_sha256'];a['packet_sha256']=hashlib.sha256(packet.read_bytes()).hexdigest();save(ap,a)
  gate=BASE/(stem+'-exact-gate.json')
  run(TOP/'geometry/verify_wall_aware_mask.py',[packet,'--output',gate,'--bins',32,'--max-depth',16,'--max-rows',20000,'--seconds',90],stem+'-gate')
  g=read(gate);e.update(status=g['status'],last=g['records'][-1]['status'],packet=str(packet),gate=str(gate),rows=g['rows'],bins=32);emit(e)
  if e['status'].startswith('PASS_EXACT_'):
   assert g['packet_sha256']==hashlib.sha256(packet.read_bytes()).hexdigest()
   values=read(OUT/'patterns.json',[]);values.append(dict(e,final=True,global_optimality_proved=False));save(OUT/'patterns.json',values)
   return e
  if e['last']!='REFUTED_BY_LEGAL_PARENT':return e
  previous=gate
 # Preserve the last exact refuter even when the local repair budget is spent.
 ex=BASE/(stem+'-terminal-exact.npz');ji=BASE/(stem+'-terminal-jitter.npz')
 run(BASE/'add_exact_refuter.py',[previous,'--output',ex],stem+'-terminal-capture')
 run(BASE/'jitter_refuter.py',[ex,'--output',ji,'--count',256],stem+'-terminal-jitter')
 return dict(e,status='REPAIR_LIMIT',terminal_exact=str(ex))

def main():
 global OUT
 ap=argparse.ArgumentParser();ap.add_argument('--seconds',type=int,default=3600);ap.add_argument('--repairs',type=int,default=4);ap.add_argument('--max-features',type=int,default=16);ap.add_argument('--producers',nargs='+',default=['batch','batch_subset','batch_recursive']);ap.add_argument('--output',default='batch_recursive');ap.add_argument('--tag-prefix',default='p3batchrecursive');args=ap.parse_args()
 OUT=PHASE/args.output;OUT.mkdir(exist_ok=True)
 state=read(OUT/'queue-state.json',{})
 # Earlier screen jobs are source-distinct, complete finite attempts; do not redo them.
 for f in [HERE/'pattern-screen.json',PHASE/'batch_subset/five-cell-screen.json']:
  for r in read(f,[]):
   if 'required_cells' in r:state.setdefault(key(r['required_cells']),dict(r,status='ALREADY_SCREENED',source=str(f)))
 ps.init();started=time.monotonic();count=0
 while time.monotonic()-started<args.seconds:
  todo=candidates(state,set(args.producers));save(OUT/'pending-candidates.json',todo)
  if not todo:break
  c=todo[0];k=key(c['required_cells']);emit(dict(c,event='TASK_START',remaining_candidates=len(todo)))
  try:r=attempt(c,args)
  except Exception as e:r=dict(c,status='ERROR',error=repr(e));emit(r)
  state[k]=r;save(OUT/'queue-state.json',state);count+=1
 emit(dict(event='SEARCH_PAUSED',new_attempts=count,elapsed=time.monotonic()-started))

if __name__=='__main__':main()
