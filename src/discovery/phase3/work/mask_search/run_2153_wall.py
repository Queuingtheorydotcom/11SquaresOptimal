from pathlib import Path
import json,subprocess,sys,os,time
ROOT=Path('/workspace/scratch/6def36ddf53b/current');OUT=ROOT/'research/optimality/deficit_geometry/physical_features';WORK=Path(__file__).parent;env={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONPATH':'/workspace/scratch/6def36ddf53b/work/audit/deps'}
extra=[ROOT/p for p in json.loads((OUT/'mask2147-sep27wallr6-result.json').read_text())['additional_exact_capture_files']];groups=json.loads((WORK.parent/'geometry/wall_ownership_groups.json').read_text());history=[]
def run(script,args,name):
 with (WORK/(name+'.log')).open('w') as f:subprocess.run([sys.executable,str(script),*map(str,args)],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
for i in range(1,7):
 tag=f'sep27wallr{i}';stem=f'mask2153-{tag}'
 if i>1:
  prev=OUT/f'mask2153-sep27wallr{i-1}-exact-gate.json';pd=json.loads(prev.read_text())
  if pd['records'][-1]['status']!='REFUTED_BY_LEGAL_PARENT':break
  exact=OUT/(stem+'-exact.npz');jitter=OUT/(stem+'-jitter.npz');run(OUT/'add_exact_refuter.py',[prev,'--output',exact],stem+'-add');run(OUT/'jitter_refuter.py',[exact,'--output',jitter,'--count',1024],stem+'-jitter');extra.extend([exact,jitter])
 run(OUT/'solve_sep27_wall.py',['--mask',2153,'--tag',tag,'--dataset',OUT/'owned-tight','--ownership','cell_fivepoints','--seconds',100]+[v for p in extra for v in ['--extra',p]],stem+'-solve');finite=json.loads((OUT/(stem+'-result.json')).read_text())
 if finite.get('best_budget',12)>=11:print('NO_FINITE_GAP');break
 run(OUT/'freeze.py',['--mask',2153,'--tag',tag],stem+'-freeze');packet=OUT/(stem+'-packet.json');d=json.loads(packet.read_text());d.pop('ownership_offsets_unit',None);d['ownership_points_field']=groups['groups'];d['wall_aware_ownership_extension']=True;packet.write_text(json.dumps(d,indent=2)+'\n')
 if d['positive_physical_features']>100:print('TOO_MANY_FEATURES',d['positive_physical_features']);break
 gate=OUT/(stem+'-exact-gate.json');run(WORK.parent/'geometry/verify_wall_aware_mask.py',[packet,'--output',gate,'--bins',64,'--max-depth',16,'--max-rows',16000,'--seconds',100],stem+'-gate');g=json.loads(gate.read_text());last=g['records'][-1];entry={'iteration':i,'status':g['status'],'last_status':last['status'],'cell':last['cell'],'rows':g['rows'],'seconds':g['seconds'],'features':d['positive_physical_features'],'budget':d['certificate']['budget_units'],'finite_budget':finite['best_budget']};history.append(entry);(WORK/'2153_wall_progress.json').write_text(json.dumps(history,indent=2)+'\n');print(json.dumps(entry),flush=True)
 if last['status']!='REFUTED_BY_LEGAL_PARENT':break
