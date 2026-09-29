import run_batch as b
import json
p=json.loads((b.HERE/'mask202-p2batch2-drop5-packet.json').read_text());owners=p['conditional_owner_support'];hist=[]
for drop in [3,2,1,0,12]:
 trial=dict(p,conditional_owner_support=[i for i in owners if i!=drop]);e=b.run(trial,f'mask202-p2batchstrong-drop{drop}');e['drop']=drop;hist.append(e);print(json.dumps(e),flush=True)
 if e['status'].startswith('PASS_'):p=trial;owners.remove(drop)
 (b.HERE/'mask202-strong-progress.json').write_text(json.dumps(dict(required_cells=sorted(set(owners)|{4,8}),history=hist),indent=2)+'\n')
