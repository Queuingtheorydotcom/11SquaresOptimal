from pathlib import Path
import json,sys,concurrent.futures,time
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'batch'));import run_batch as gate
gate.HERE=HERE
front=json.loads((HERE.parent/'provisional-frontier.json').read_text());patterns=[set(p) for p in front['patterns']];history=json.loads((HERE/'history.json').read_text());todo=[x for x in history if x['status'].startswith('PASS_') and not (HERE/f"mask{x['mask']}-minimal-result.json").exists()]
def minimize(entry):
 idx=entry['mask'];p=json.loads(Path(entry['packet']).read_text());owners=list(p['mask']);positive={i for i,g in enumerate(p['threshold_units']) if g};last=entry;records=[]
 for drop in reversed(owners.copy()):
  if drop in positive:continue
  trial=dict(p,conditional_owner_support=[j for j in owners if j!=drop]);r=gate.run(trial,f'mask{idx}-min-drop{drop}',seconds=45);r['dropped']=drop;records.append(r)
  if r['status'].startswith('PASS_'):owners.remove(drop);p=trial;last=r
  (HERE/f'mask{idx}-min-progress.json').write_text(json.dumps(dict(owners=owners,records=records),indent=2)+'\n')
 required=sorted(set(owners)|positive);result=dict(mask=idx,required_cells=required,packet=last['packet'],receipt=last['receipt'],rows=last['rows'],features=entry['features'],subsumed=any(x<=set(required) or {15-i for i in x}<=set(required) for x in patterns))
 (HERE/f'mask{idx}-minimal-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(minimize,todo))
(HERE/'minimal-results.json').write_text(json.dumps(result,indent=2)+'\n')
