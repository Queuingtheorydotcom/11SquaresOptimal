"""Checkpointed exact CEGAR over this worker's assigned occupancy masks.
Discovery computations never count as proofs. Dynamic skips bind complete
exact gate receipts to packets and validate their positive/owner cell support.
"""
from pathlib import Path
import os,sys,json,time,hashlib,traceback,contextlib,importlib.util,gc
os.environ['OPENBLAS_NUM_THREADS']='1'
from warm_tools import TOP,ROOT,OUT,WORK,module,entry,gate,passed_pattern
import numpy as np
START=time.monotonic();QUEUE=json.loads((WORK/'queue.json').read_text())['assigned_masks'];COVER=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text());MASKS=COVER['canonical_eleven_cell_subsets'];INV=COVER['symmetry_cell_involution'];U='387708359002281417731/100000000000000000000';GROUPS=json.loads((TOP/'work/geometry/wall_ownership_groups.json').read_text());SEEN_EXTRA=set();EXTRA=[];counter=0;history=[];own_patterns=[];checked_patterns={};status={};stop=False
if (WORK/'state.json').exists():
 state=json.loads((WORK/'state.json').read_text());counter=state['counter'];history=state['history'];status={int(k):v for k,v in state['status'].items()}
if (WORK/'patterns.json').exists():own_patterns=json.loads((WORK/'patterns.json').read_text())
def stop_requested():
 p=WORK/'STOP'
 return p.exists() and p.read_text().strip()!='RESUME'
def save_json(path,value):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)
def snapshot():
 save_json(WORK/'state.json',dict(counter=counter,history=history,status=status,elapsed_this_run=time.monotonic()-START))
 save_json(WORK/'progress.json',dict(assigned=len(QUEUE),attempted=len(status),passed_fields=len(own_patterns),status_counts={s:sum(v.get('status')==s for v in status.values()) for s in sorted({v.get('status','?') for v in status.values()})},extra_archives=len(EXTRA),elapsed_this_run=time.monotonic()-START,last=history[-1] if history else None))
def log(e):
 history.append(e)
 with (WORK/'results.jsonl').open('a') as f:f.write(json.dumps(e)+'\n')
 snapshot();print(json.dumps(e),flush=True)
def extras():
 for p in sorted(OUT.glob('*.npz')):
  if p in SEEN_EXTRA or not(p.stem.endswith('-exact') or p.stem.endswith('-refuter') or p.stem.endswith('-jitter')):continue
  try:
   d=json.loads(p.with_suffix('.json').read_text())
   if d.get('parent_Uplus')!=U:continue
   with np.load(p) as z:
    if not all(k in z.files for k in ['rows','poses','memberships','legal','fivepoint_captures','generator_captures']):continue
    if z['rows'].shape[1]!=1232:continue
   SEEN_EXTRA.add(p);EXTRA.append(p)
  except (KeyError,FileNotFoundError,ValueError,json.JSONDecodeError):continue
 return EXTRA

def all_patterns():
 result=[]
 audit_path=TOP/'work/phase3/audit/current-union-independent-audit.json'
 if not audit_path.exists():audit_path=TOP/'work/phase2/audit/current-union-independent-audit.json'
 baseline=json.loads(audit_path.read_text())
 for e in baseline['entries']:result.append((set(e['required_owner_cells'])|set(map(int,e['positive_cell_thresholds'])),e['packet_path']))
 for folder in (TOP/'work/phase3').iterdir():
  path=folder/'patterns.json'
  if not path.exists():continue
  try:items=json.loads(path.read_text());items=items.get('patterns',[]) if isinstance(items,dict) else items
  except (ValueError,OSError):continue
  for e in items:
   try:
    p=Path(e['packet']);g=Path(e['gate']);key=(str(p),str(g),p.stat().st_mtime_ns,g.stat().st_mtime_ns)
    if key not in checked_patterns:checked_patterns[key]=passed_pattern(p,g)
    good=checked_patterns[key];result.append((set(good['required_cells']),str(p)))
   except (KeyError,AssertionError,ValueError,OSError):continue
 return result

def covered(mask):
 m=set(MASKS[mask]);hm={INV[i] for i in m}
 for p,source in all_patterns():
  if p<=m:return source
  if p<=hm:return source+' [half_turn]'
 return None

def solve(mask,tag,paths):
 hook=WORK/'solve_hook.py'
 if hook.exists():
  key='hook_'+hashlib.sha256(hook.read_bytes()).hexdigest();name='p3ms_'+key
  if name not in sys.modules:
   spec=importlib.util.spec_from_file_location(name,hook);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
  with (WORK/f'mask{mask}-{tag}-solve.log').open('w') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):return sys.modules[name].solve(mask,tag,paths,90)
 entry(OUT/'solve_sep27_wall.py',['--mask',mask,'--tag',tag,'--dataset',OUT/'owned-tight','--ownership','cell_fivepoints','--seconds',90,*[v for p in paths for v in ['--extra',p]]],WORK/f'mask{mask}-{tag}-solve.log')
 return json.loads((OUT/f'mask{mask}-{tag}-result.json').read_text())

def freeze(mask,tag):
 stem=f'mask{mask}-{tag}';entry(OUT/'freeze.py',['--mask',mask,'--tag',tag],WORK/f'{stem}-freeze.log');p=OUT/f'{stem}-packet.json';d=json.loads(p.read_text());d.pop('ownership_offsets_unit',None);assert d['parent_Uplus']==GROUPS['parent_Uplus'];d['ownership_points_field']=GROUPS['groups'];d['wall_aware_ownership_extension']=True;save_json(p,d)
 ar=OUT/f'{stem}-mask-arithmetic.json';ad=json.loads(ar.read_text());ad['pre_ownership_extension_packet_sha256']=ad['packet_sha256'];ad['packet_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();save_json(ar,ad);return p,d

def add_refuter(report,stem):
 p=OUT/f'{stem}-exact.npz';j=OUT/f'{stem}-jitter.npz'
 if not p.exists():entry(OUT/'add_exact_refuter.py',[report,'--output',p],WORK/f'{stem}-capture.log')
 if not j.exists():entry(OUT/'jitter_refuter.py',[p,'--output',j,'--count',512],WORK/f'{stem}-jitter.log')
 extras();return str(p)

def publish(pattern_id,p,g):
 r=passed_pattern(p,g);r['pattern_id']=pattern_id
 for i,old in enumerate(own_patterns):
  if old.get('pattern_id')==pattern_id:own_patterns[i]=r;break
 else:own_patterns.append(r)
 save_json(WORK/'patterns.json',own_patterns);return r

def minimize(mask,tag,p,g):
 d=json.loads(p.read_text());owners=list(d.get('conditional_owner_support',d['mask']));P={i for i,x in enumerate(d['threshold_units']) if x};lastp,lastg=p,g;pattern_id=f'{mask}:{tag}';tested=set()
 initial_sig=tuple(d['threshold_units'])
 for e in history:
  if e.get('mask')==mask and e.get('tag')==tag and e.get('event') in ['OWNER_TRIAL','POSITIVE_TRIAL'] and not e.get('passed'):
   tested.add((e['event'],e['drop'],tuple(e.get('threshold_signature',initial_sig))))
 publish(pattern_id,lastp,lastg)
 while not stop_requested():
  sig=tuple(d['threshold_units']);forced=sum(sig[i] for i in d['mask']);budget=d['certificate']['budget_units']
  opts=[i for i in owners if i not in P and ('OWNER_TRIAL',i,sig) not in tested];event='OWNER_TRIAL'
  if not opts:
   opts=[i for i in P if forced-sig[i]>budget and ('POSITIVE_TRIAL',i,sig) not in tested];event='POSITIVE_TRIAL'
  if not opts:break
  remaining=[set(MASKS[i]) for i in QUEUE if status.get(i,{}).get('status')!='COVERED']
  def benefit(i):
   T=(set(owners)|P)-{i};H={INV[j] for j in T}
   return sum(T<=m or H<=m for m in remaining)
  drop=max(opts,key=lambda i:(benefit(i),i));tested.add((event,drop,sig));trial=dict(d);trial['conditional_owner_support']=[i for i in owners if i!=drop]
  if event=='POSITIVE_TRIAL':
   gamma=list(d['threshold_units']);gamma[drop]=0;trial['threshold_units']=gamma;trial['positive_cells']=[i for i,v in enumerate(gamma) if v];trial['conditional_counting_surplus_units']=sum(gamma[i] for i in d['mask'])-budget;trial['positive_cell_pruning_steps']=d.get('positive_cell_pruning_steps',[])+[drop]
  signature=hashlib.sha256(json.dumps(list(sig)).encode()).hexdigest()[:8];stem=f'mask{mask}-{tag}-g{signature}-'+('zero' if event=='POSITIVE_TRIAL' else 'drop')+str(drop);tp=OUT/f'{stem}-packet.json';tg=OUT/f'{stem}-gate.json';save_json(tp,trial)
  rr=gate(tp,tg,WORK/f'{stem}-gate.log',seconds=120);good=rr['status']=='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION';log({'event':event,'mask':mask,'tag':tag,'drop':drop,'passed':good,'threshold_signature':list(sig),'last_status':rr['records'][-1]['status'],'rows':rr['rows'],'gate':str(tg),'seconds':rr['seconds']})
  if good:
   owners=[i for i in owners if i!=drop];d=trial;P={i for i,v in enumerate(d['threshold_units']) if v};lastp,lastg=tp,tg;publish(pattern_id,lastp,lastg)
  elif rr['records'][-1]['status']=='REFUTED_BY_LEGAL_PARENT':add_refuter(tg,stem)
 # Older warm receipts retained their provenance inline. Freshly replay them
 # into canonical adapter format; originals and source-capture hashes survive.
 saved=json.loads(Path(lastg).read_text())
 if 'orchestration_dependencies' in saved or saved.get('scope','').startswith('Warm-process'):
  normalized=OUT/f'mask{mask}-{tag}-canonical-gate.json';rr=gate(lastp,normalized,WORK/f'mask{mask}-{tag}-canonical-gate.log',seconds=120);assert rr['status']=='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION';lastg=normalized
 r=publish(pattern_id,lastp,lastg);r['minimization_complete']=not stop_requested();save_json(WORK/'patterns.json',own_patterns);log(dict(event='MINIMIZED_PATTERN' if r['minimization_complete'] else 'PRUNING_PAUSED',**r));return r

try:
 extras();log({'event':'START','assigned_masks':len(QUEUE),'extra_archives':len(EXTRA)})
 for record in own_patterns.copy():
  if not record.get('minimization_complete',False) and not stop_requested():
   minimize(record['mask_index'],record['pattern_id'].split(':',1)[1],Path(record['packet']),Path(record['gate']))
 screen={d['mask']:d for d in [json.loads(s) for s in (TOP/'work/phase2/screen/results.jsonl').read_text().splitlines()]}
 order=sorted(QUEUE,key=lambda m:(screen.get(m,{}).get('positive_features',999),screen.get(m,{}).get('finite_budget',99),m))
 # Finite screening is now informed by the enlarged shared refuter pool.
 # The first sweep gates sparse fields promptly; dense discoveries remain
 # explicitly unresolved and are revisited in a complete second sweep.
 for sweep,mask in [(s,m) for s in (0,1) for m in order]:
  if stop_requested():break
  cover=covered(mask)
  if cover:
   status[mask]={'status':'COVERED','source':cover};snapshot();continue
  previous=status.get(mask,{}).get('status')
  if previous in ['PASS','NO_FINITE_GAP','FEATURE_LIMIT','CUT_LIMIT','INCOMPLETE_GATE']:continue
  if sweep==1 and previous!='DENSE_DEFERRED':continue
  for cut in range(1,9):
   if stop_requested():break
   cover=covered(mask)
   if cover:status[mask]={'status':'COVERED','source':cover};snapshot();break
   counter+=1;tag=f'p3ms{counter:04d}';stem=f'mask{mask}-{tag}';finite=solve(mask,tag,extras());status[mask]={'status':'ACTIVE','tag':tag,'cut':cut,'finite_budget':finite.get('best_budget')};snapshot()
   if finite.get('best_budget',99)>=11-1e-9:
    status[mask]['status']='NO_FINITE_GAP';log({'event':'NO_FINITE_GAP','mask':mask,'tag':tag,'finite_budget':finite.get('best_budget')});break
   if finite.get('positive_weight_count',999)>100:
    status[mask]['status']='FEATURE_LIMIT';log({'event':'FEATURE_LIMIT','mask':mask,'tag':tag,'features':finite.get('positive_weight_count'),'finite_budget':finite.get('best_budget')});break
   if sweep==0 and finite.get('positive_weight_count',999)>12:
    status[mask]['status']='DENSE_DEFERRED';log({'event':'DENSE_DEFERRED','mask':mask,'tag':tag,'features':finite.get('positive_weight_count'),'finite_budget':finite.get('best_budget'),'scope':'Finite discovery only; exact gate is deferred to the second sweep.'});break
   p,d=freeze(mask,tag);g=OUT/f'{stem}-gate.json';r=gate(p,g,WORK/f'{stem}-gate.log',seconds=120);last=r['records'][-1];log({'event':'GATE','mask':mask,'tag':tag,'cut':cut,'status':r['status'],'last_status':last['status'],'cell':last['cell'],'features':d['positive_physical_features'],'finite_budget':finite['best_budget'],'budget':d['certificate']['budget_units'],'forced':sum(d['threshold_units'][i] for i in d['mask']),'rows':r['rows'],'seconds':r['seconds'],'packet':str(p),'gate':str(g)})
   if r['status']=='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION':
    status[mask]={'status':'PASS','tag':tag,'packet':str(p),'gate':str(g)};publish(f'{mask}:{tag}',p,g);snapshot();minimize(mask,tag,p,g);break
   if last['status']=='REFUTED_BY_LEGAL_PARENT':
    add_refuter(g,stem+'-refuter');status[mask]={'status':'REFUTED_CANDIDATE','tag':tag,'cut':cut};snapshot()
   else:
    status[mask]={'status':'INCOMPLETE_GATE','tag':tag,'last_status':last['status'],'gate':str(g)};snapshot();break
  else:status[mask]={'status':'CUT_LIMIT','tag':tag,'cut':8};snapshot()
  gc.collect()
 # Final frontier is recomputed from every currently verified shared pattern.
 unresolved=[]
 for mask in QUEUE:
  source=covered(mask)
  if source:status[mask]={'status':'COVERED','source':source}
  else:unresolved.append(mask)
 save_json(WORK/'unresolved.json',{'assigned':len(QUEUE),'unresolved_masks':unresolved,'count':len(unresolved),'scope':'Unresolved means no complete certificate found by this worker or a validated shared pattern; it is not a feasible packing claim.'});snapshot();log({'event':'QUEUE_CHECKPOINT','unresolved':len(unresolved),'assigned':len(QUEUE)})
except BaseException as exc:
 log({'event':'WORKER_ERROR','error':repr(exc),'traceback':traceback.format_exc()});raise
