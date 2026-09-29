from pathlib import Path
import json,shutil,subprocess,sys,os
H=Path(__file__).resolve().parent;B=H.parents[2]/'current/research/optimality/deficit_geometry/physical_features';d=json.loads((H/'angleprice_feedback2.json').read_text());env={**os.environ,'OPENBLAS_NUM_THREADS':'1'}
for q in d['refuters']:
 p=Path(q);cell=json.loads(p.read_text())['records'][-1]['cell'];gate=B/f'mask1383-p2angle2-cell{cell}-gate.json';exact=B/f'mask1383-p2angle2-cell{cell}-exact.npz';shutil.copy2(p,gate)
 with (H/f'anglefeedback_cell{cell}.log').open('w') as f:
  subprocess.run([sys.executable,str(B/'add_exact_refuter.py'),str(gate),'--output',str(exact)],stdout=f,stderr=subprocess.STDOUT,check=True,env=env)
  dest=H/f'mask1383_feedback_angle2cell{cell}-exact.npz';shutil.copy2(exact,dest);shutil.copy2(exact.with_suffix('.json'),dest.with_suffix('.json'))
  subprocess.run([sys.executable,str(B/'jitter_refuter.py'),str(exact),'--output',str(H/f'mask1383_feedback_angle2cell{cell}-jitter.npz'),'--count','256'],stdout=f,stderr=subprocess.STDOUT,check=True,env=env)
 print('captured',cell,flush=True)
