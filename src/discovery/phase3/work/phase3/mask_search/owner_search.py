"""Recursive support retraining. Finite LP outputs are never proof claims."""
from pathlib import Path
import os,json,time,hashlib,contextlib,gc,re
os.environ['OPENBLAS_NUM_THREADS']='1'
from warm_tools import TOP,ROOT,OUT,WORK,module,entry,gate,passed_pattern
import numpy as np

PS=module(TOP/'work/phase3/batch/pattern_solver.py')
GROUPS=json.loads((TOP/'work/geometry/wall_ownership_groups.json').read_text())
COVER=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text())
MASKS=COVER['canonical_eleven_cell_subsets'];INV=COVER['symmetry_cell_involution']
START=time.monotonic();COUNTER=0;QUEUE={};SEEN=set();HISTORY=[]
STATE=WORK/'owner-state.json'
if STATE.exists():
 d=json.loads(STATE.read_text());COUNTER=d['counter'];QUEUE={tuple(e['owners']):e for e in d['queue']};SEEN={tuple(x) for x in d['seen']};HISTORY=d['history']
# A process can stop after creating a discovery file but before committing its
# event. Reserve every existing tag on restart so frozen output is not reused.
COUNTER=max([COUNTER]+[int(re.search(r'p3msown(\d+)',p.name)[1])for p in OUT.glob('*-p3msown*-result.json')])

def read(p):return json.loads(Path(p).read_text())
def save(p,d):
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(d,indent=2)+'\n');q.replace(p)
def emit(e):
 HISTORY.append(e);save(STATE,dict(counter=COUNTER,queue=list(QUEUE.values()),seen=[list(x)for x in sorted(SEEN)],history=HISTORY));save(WORK/'owner-progress.json',dict(queued=len(QUEUE),processed=len(SEEN),complete_patterns=sum(x.get('event')=='EXACT_PATTERN'for x in HISTORY),elapsed=time.monotonic()-START,last=e));print(json.dumps(e),flush=True)
def enqueue(record):
 T=set(record['required_cells'])
 for i in sorted(T):
  J=tuple(sorted(T-{i}))
  if J not in SEEN and J not in QUEUE:QUEUE[J]=dict(mask=record['mask_index'],owners=list(J),drop=i,parent_packet=record['packet'])
def known():
 a=read(TOP/'work/phase3/audit/current-union-independent-audit.json')
 patterns=[set(e['required_owner_cells'])|set(map(int,e['positive_cell_thresholds']))for e in a['entries']]
 for folder in (TOP/'work/phase3').iterdir():
  p=folder/'patterns.json'
  if not p.exists():continue
  try:
   rows=read(p);rows=rows.get('patterns',[])if isinstance(rows,dict)else rows
   for r in rows:
    try:patterns.append(set(passed_pattern(Path(r['packet']),Path(r['gate']))['required_cells']))
    except (KeyError,OSError,ValueError,AssertionError):pass
  except (ValueError,OSError):pass
 return patterns,a['remaining_canonical_mask_indices']
def covered(T,patterns):return any(P<=T or {INV[i]for i in P}<=T for P in patterns)
def extras():
 result=[]
 for p,n,e in PS.compatible():
  with np.load(p)as z:
   if z['rows'].shape[1]==1232:result.append(p)
 return result
def freeze(mask,tag,J):
 stem=f'mask{mask}-{tag}';entry(OUT/'freeze.py',['--mask',mask,'--tag',tag],WORK/f'{stem}-freeze.log');p=OUT/f'{stem}-packet.json';d=read(p);d.pop('ownership_offsets_unit',None);assert d['parent_Uplus']==GROUPS['parent_Uplus'];d.update(ownership_points_field=GROUPS['groups'],conditional_owner_support=J,wall_aware_ownership_extension=True);assert all(not v for i,v in enumerate(d['threshold_units'])if i not in J);d['positive_cells']=[i for i,v in enumerate(d['threshold_units'])if v];d['conditional_counting_surplus_units']=sum(d['threshold_units'])-d['certificate']['budget_units'];save(p,d)
 ar=OUT/f'{stem}-mask-arithmetic.json';ad=read(ar);ad['pre_ownership_extension_packet_sha256']=ad['packet_sha256'];ad['packet_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();save(ar,ad);return p,d
def capture(report,stem):
 ex=OUT/f'{stem}-exact.npz';ji=OUT/f'{stem}-jitter.npz'
 entry(OUT/'add_exact_refuter.py',[report,'--output',ex],WORK/f'{stem}-capture.log');entry(OUT/'jitter_refuter.py',[ex,'--output',ji,'--count',512],WORK/f'{stem}-jitter.log')

for r in read(WORK/'patterns.json'):enqueue(r)
emit(dict(event='OWNER_SEARCH_START',queued=len(QUEUE)))
PS.init()
while QUEUE:
 stop=WORK/'OWNER_STOP'
 if stop.exists() and stop.read_text().strip()!='RESUME':break
 patterns,frontier=known()
 def gain(J):
  T=set(J);H={INV[i]for i in T}
  return sum(T<=set(MASKS[m])or H<=set(MASKS[m])for m in frontier)
 J=max(QUEUE,key=lambda x:(gain(x),-len(x),tuple(-i for i in x)));candidate=QUEUE.pop(J);SEEN.add(J);potential=gain(J)
 if covered(set(J),patterns):emit(dict(event='OWNER_SUBSET_ALREADY_CERTIFIED',**candidate));continue
 if not potential:emit(dict(event='OWNER_SUBSET_NO_NEW_FRONTIER',**candidate));continue
 for cut in range(1,5):
  COUNTER+=1;tag=f'p3msown{COUNTER:04d}';mask=candidate['mask'];stem=f'mask{mask}-{tag}'
  with (WORK/f'{stem}-solve.log').open('w')as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):finite=PS.solve(mask,tag,list(J),seconds=45,extra=extras())
  info=dict(mask=mask,owners=list(J),tag=tag,cut=cut,potential_frontier_gain=potential,finite_budget=finite.get('best_budget'),features=finite.get('positive_weight_count'))
  if finite.get('best_budget',99)>=10.999999:emit(dict(event='OWNER_NO_FINITE_GAP',**info));break
  if finite.get('positive_weight_count',999)>24:emit(dict(event='OWNER_DENSE_DEFERRED',**info));break
  p,d=freeze(mask,tag,list(J));g=OUT/f'{stem}-gate.json';r=gate(p,g,WORK/f'{stem}-gate.log',seconds=120);last=r['records'][-1]['status'];emit(dict(event='OWNER_GATE',**info,status=r['status'],last_status=last,rows=r['rows'],seconds=r['seconds'],packet=str(p),gate=str(g)))
  if r['status']=='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION':
   record=passed_pattern(p,g);record.update(pattern_id=f'{mask}:{tag}',final=True,minimization_complete=False,source_method='proper_support_retraining');rows=read(WORK/'patterns.json');rows.append(record);save(WORK/'patterns.json',rows);enqueue(record);emit(dict(event='EXACT_PATTERN',**record));break
  if last!='REFUTED_BY_LEGAL_PARENT':break
  capture(g,stem+'-refuter')
 gc.collect()
emit(dict(event='OWNER_SEARCH_CHECKPOINT',remaining_queue=len(QUEUE),processed=len(SEEN)))
