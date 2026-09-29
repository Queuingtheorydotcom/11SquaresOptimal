"""Derive a smaller forbidden cell pattern, preserving every exact failed trial."""
from pathlib import Path
import json,subprocess,sys,os,time,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]/'current';BASE=ROOT/'research/optimality/deficit_geometry/physical_features';ADAPTER=HERE.parent/'geometry/verify_wall_aware_mask.py'
packet=json.loads((BASE/'mask2147-sep27wallr6-packet.json').read_text());owners=list(packet['mask']);positive={i for i,x in enumerate(packet['threshold_units']) if x};history=[];start=time.monotonic()
env={**os.environ,'PYTHONPATH':str(HERE.parent/'audit/deps'),'OPENBLAS_NUM_THREADS':'1'}
for drop in [13,14,8,7,11,9,4,2]:
 trial=dict(packet);trial['conditional_owner_support']=[j for j in owners if j!=drop]
 p=HERE/f'mask2147-omit{drop}-packet.json';o=HERE/f'mask2147-omit{drop}-gate.json';p.write_text(json.dumps(trial,indent=2)+'\n')
 with (HERE/f'mask2147-omit{drop}.log').open('w') as f:
  subprocess.run([sys.executable,str(ADAPTER),str(p),'--output',str(o),'--seconds','90','--max-rows','16000'],stdout=f,stderr=subprocess.STDOUT,env=env,check=True,timeout=150)
 d=json.loads(o.read_text());passed=d['status']=='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION'
 history.append({'dropped_owner':drop,'pass':passed,'status':d['status'],'last':d['records'][-1]['status'],'cell':d['records'][-1]['cell'],'rows':d['rows'],'packet':str(p),'receipt':str(o)})
 if passed:owners.remove(drop);packet=trial
 print(json.dumps(history[-1]),flush=True)
 required=sorted(positive|set(owners));(HERE/'mask2147-minimized-owners-progress.json').write_text(json.dumps({'required_cells':required,'conditional_owner_support':owners,'positive_cells':sorted(positive),'history':history,'elapsed':time.monotonic()-start},indent=2)+'\n')
 if time.monotonic()-start>600:break
(HERE/'mask2147-minimized-packet.json').write_text(json.dumps(packet,indent=2)+'\n')
print('DONE',owners,flush=True)
