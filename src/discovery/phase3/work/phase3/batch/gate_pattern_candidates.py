"""Proper-pattern CEGAR. All outputs remain proposals until a complete exact gate."""
from pathlib import Path
import json,sys,time,hashlib,subprocess,os
import pattern_solver as ps
HERE=Path(__file__).resolve().parent;TOP=HERE.parents[1];ROOT=TOP.parent/'current';BASE=ps.OUT;OUT=HERE.parent/'batch_subset';OUT.mkdir(exist_ok=True);ENV={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONPATH':str(TOP/'audit/deps')};GROUPS=json.loads((TOP/'geometry/wall_ownership_groups.json').read_text())['groups'];history=[]
def read(p):return json.loads(p.read_text())
def run(script,args,label,timeout=180):
 with(OUT/(label+'.log')).open('w')as f:subprocess.run([sys.executable,str(script),*map(str,args)],cwd=ROOT,env=ENV,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=timeout)
def emit(e):
 history.append(e);(OUT/'history.json').write_text(json.dumps(history,indent=2)+'\n');print(json.dumps(e),flush=True)
rs=[r for r in read(HERE/'pattern-screen.json')if r.get('finite_budget',99)<10.95 and r.get('features',999)<=16];rs.sort(key=lambda r:(len(r['required_cells']),r['finite_budget'],r['features']))
for candidate in rs:
 mask=candidate['mask'];drop=candidate['drop'];J=candidate['required_cells'];previous=None
 for iteration in range(1,4):
  if iteration==1:tag=candidate['tag'];finite=read(BASE/f'mask{mask}-{tag}-result.json')
  else:
   tag=f'p3batchpat{mask}d{drop}r{iteration}';stem=f'mask{mask}-{tag}';ex=BASE/(stem+'-exact.npz');ji=BASE/(stem+'-jitter.npz');run(BASE/'add_exact_refuter.py',[previous,'--output',ex],stem+'-capture');run(BASE/'jitter_refuter.py',[ex,'--output',ji,'--count',512],stem+'-jitter');finite=ps.solve(mask,tag,J,extra=[p for p,n,e in ps.compatible()],seconds=30)
  stem=f'mask{mask}-{tag}';entry=dict(mask=mask,pattern_id=f'mask{mask}-without{drop}',iteration=iteration,required_cells=J,finite_budget=finite.get('best_budget'),features=finite.get('positive_weight_count'))
  if finite.get('best_budget',99)>=10.999 or finite.get('positive_weight_count',999)>16:emit(dict(entry,status='NO_SPARSE_FINITE_GAP'));break
  run(BASE/'freeze.py',['--mask',mask,'--tag',tag],stem+'-freeze');packet=BASE/(stem+'-packet.json');p=read(packet);p.pop('ownership_offsets_unit',None);p.update(ownership_points_field=GROUPS,conditional_owner_support=J,wall_aware_ownership_extension=True);assert not any(g for i,g in enumerate(p['threshold_units'])if i not in J);p['positive_cells']=[i for i,g in enumerate(p['threshold_units'])if g];p['conditional_counting_surplus_units']=sum(p['threshold_units'][i]for i in p['mask'])-p['certificate']['budget_units'];packet.write_text(json.dumps(p,indent=2)+'\n');a=BASE/(stem+'-mask-arithmetic.json');d=read(a);d['pre_ownership_extension_packet_sha256']=d['packet_sha256'];d['packet_sha256']=hashlib.sha256(packet.read_bytes()).hexdigest();a.write_text(json.dumps(d,indent=2)+'\n');gate=BASE/(stem+'-exact-gate.json');run(TOP/'geometry/verify_wall_aware_mask.py',[packet,'--output',gate,'--bins',32,'--max-depth',16,'--max-rows',20000,'--seconds',90],stem+'-gate',180);g=read(gate);entry.update(status=g['status'],last=g['records'][-1]['status'],packet=str(packet),gate=str(gate),rows=g['rows'],bins=32);emit(entry)
  if g['status'].startswith('PASS_EXACT_'):
   values=read(OUT/'patterns.json')if(OUT/'patterns.json').exists()else[];values.append(dict(entry,final=True,global_optimality_proved=False));(OUT/'patterns.json').write_text(json.dumps(values,indent=2)+'\n');break
  if entry['last']!='REFUTED_BY_LEGAL_PARENT':break
  previous=gate
