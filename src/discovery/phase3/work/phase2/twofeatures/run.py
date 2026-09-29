from pathlib import Path
import sys,json,time,concurrent.futures
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'batch'));import run_batch as gate
gate.HERE=HERE
histpath=HERE/'history.json';history=json.loads(histpath.read_text()) if histpath.exists() else []
done={h['mask'] for h in history};todo=json.loads((HERE/'todo.json').read_text());seen={};selected=[]
for x in todo:
 if x['mask'] in {232,235,1902} or x['mask'] in done:continue
 p=json.loads((HERE/f"proposal-{x['mask']}.json").read_text())
 if max(p['threshold_units'])>1:continue
 k=tuple(x['positive']);seen[k]=seen.get(k,0)+1
 if seen[k]>2:continue
 selected.append(x)
print('SELECTED',len(selected),[x['mask'] for x in selected],flush=True)
def run(x):
 p=json.loads((HERE/f"proposal-{x['mask']}.json").read_text());return dict(**x,**gate.run(p,f"mask{x['mask']}-root2",seconds=45))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for result in pool.map(run,selected):
  history.append(result);histpath.write_text(json.dumps(history,indent=2)+'\n');print(json.dumps(result),flush=True)
