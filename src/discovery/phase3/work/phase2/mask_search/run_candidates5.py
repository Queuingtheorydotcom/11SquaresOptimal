from pathlib import Path
import json,subprocess,sys,os,time,hashlib
ROOT=Path('/workspace/scratch/6def36ddf53b/current');OUT=ROOT/'research/optimality/deficit_geometry/physical_features';WORK=Path(__file__).parent;TOP=WORK.parents[1];env={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONPATH':str(TOP/'audit/deps')}
extra=[ROOT/p for p in json.loads((OUT/'mask232-p2ms8-result.json').read_text())['additional_exact_capture_files']]
for p in sorted(OUT.glob('*sep27*exact.npz'))+sorted(OUT.glob('*sep27*refuter.npz'))+sorted(OUT.glob('*sep27*jitter.npz'))+sorted(OUT.glob('*p2*exact.npz'))+sorted(OUT.glob('*p2*jitter.npz')):
 try:
  d=json.loads(p.with_suffix('.json').read_text())
  if d['parent_Uplus']=='387708359002281417731/100000000000000000000':extra.append(p)
 except (KeyError,FileNotFoundError):pass
extra=list(dict.fromkeys(extra));groups=json.loads((TOP/'geometry/wall_ownership_groups.json').read_text());history=[];started=time.monotonic();counter=8

def run(script,args,name,timeout=180):
 with (WORK/(name+'.log')).open('w') as f:subprocess.run([sys.executable,str(script),*map(str,args)],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=timeout)
def save():
 (WORK/'progress5.json').write_text(json.dumps({'history':history,'elapsed':time.monotonic()-started},indent=2)+'\n')
for mask in [142,163,167]:
 prev=None
 for iteration in range(1,6):
  if time.monotonic()-started>540:save();sys.exit(0)
  counter+=1;tag=f'p2ms{counter}';stem=f'mask{mask}-{tag}'
  if prev:
   exact=OUT/(stem+'-exact.npz');jitter=OUT/(stem+'-jitter.npz');run(OUT/'add_exact_refuter.py',[prev,'--output',exact],stem+'-add');run(OUT/'jitter_refuter.py',[exact,'--output',jitter,'--count',1024],stem+'-jitter');extra.extend([exact,jitter])
  run(OUT/'solve_sep27_wall.py',['--mask',mask,'--tag',tag,'--dataset',OUT/'owned-tight','--ownership','cell_fivepoints','--seconds',60]+[v for p in extra for v in ['--extra',p]],stem+'-solve');finite=json.loads((OUT/(stem+'-result.json')).read_text());entry={'mask':mask,'iteration':iteration,'tag':tag,'finite_budget':finite.get('best_budget'),'features':finite.get('positive_weight_count')}
  if finite.get('best_budget',12)>=11:
   entry['status']='NO_FINITE_GAP';history.append(entry);save();print(json.dumps(entry),flush=True);break
  if finite['positive_weight_count']>80:
   entry['status']='TOO_MANY_FEATURES';history.append(entry);save();print(json.dumps(entry),flush=True);break
  run(OUT/'freeze.py',['--mask',mask,'--tag',tag],stem+'-freeze');packet=OUT/(stem+'-packet.json');d=json.loads(packet.read_text());d.pop('ownership_offsets_unit',None);d['ownership_points_field']=groups['groups'];d['wall_aware_ownership_extension']=True;packet.write_text(json.dumps(d,indent=2)+'\n')
  ar=OUT/(stem+'-mask-arithmetic.json');ad=json.loads(ar.read_text());ad['pre_ownership_extension_packet_sha256']=ad['packet_sha256'];ad['packet_sha256']=hashlib.sha256(packet.read_bytes()).hexdigest();ar.write_text(json.dumps(ad,indent=2)+'\n')
  gate=OUT/(stem+'-exact-gate.json');run(TOP/'geometry/verify_wall_aware_mask.py',[packet,'--output',gate,'--bins',64,'--max-depth',16,'--max-rows',16000,'--seconds',75],stem+'-gate');g=json.loads(gate.read_text());last=g['records'][-1];entry.update(status=g['status'],last_status=last['status'],cell=last['cell'],rows=g['rows'],seconds=g['seconds'],features=d['positive_physical_features'],budget=d['certificate']['budget_units'],packet=str(packet),gate=str(gate));history.append(entry);save();print(json.dumps(entry),flush=True)
  if g['status'].startswith('PASS_'):sys.exit(0)
  if last['status']!='REFUTED_BY_LEGAL_PARENT':break
  prev=gate
