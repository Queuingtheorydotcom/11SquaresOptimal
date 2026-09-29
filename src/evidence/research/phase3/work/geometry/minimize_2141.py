from pathlib import Path
import json,subprocess,sys,os
H=Path(__file__).resolve().parent
p=json.loads((H/'mask2141_owners9_packet.json').read_text());support=p['conditional_owner_support'][:];history=[]
for j in [2,4,7,9,10]:
 q=dict(p);q['conditional_owner_support']=[i for i in support if i!=j];stem=H/f'mask2141_drop{j}';pin=Path(str(stem)+'_packet.json');out=Path(str(stem)+'_result.json');pin.write_text(json.dumps(q,indent=2))
 with Path(str(stem)+'.log').open('w') as f:subprocess.run([sys.executable,str(H/'verify_wall_aware_mask.py'),str(pin),'--output',str(out),'--seconds','90'],stdout=f,stderr=subprocess.STDOUT,check=True,env={**os.environ,'OPENBLAS_NUM_THREADS':'1'})
 d=json.loads(out.read_text());entry=dict(drop=j,support=q['conditional_owner_support'],status=d['status'],rows=d['rows'],output=str(out));history.append(entry)
 if d['continuum_masks_excluded']:
  support=q['conditional_owner_support'];p=q
 print(entry,flush=True);(H/'mask2141_owner_minimization_history.json').write_text(json.dumps(history,indent=2))
(H/'mask2141_owner_minimization_final.json').write_text(json.dumps(dict(support=support,positive_cells=[i for i,g in enumerate(p['threshold_units']) if g>0],history=history),indent=2))
