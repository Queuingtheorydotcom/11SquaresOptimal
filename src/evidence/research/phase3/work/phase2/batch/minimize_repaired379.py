import run_batch as b
import json,time
p=json.loads((b.BASE/'mask379-p2batchrepair3-packet.json').read_text());owners=p['mask'].copy();positive={i for i,g in enumerate(p['threshold_units'])if g};hist=[];last=None
for drop in [13,11,10,9,8,7,4,3]:
 trial=dict(p,conditional_owner_support=[i for i in owners if i!=drop]);e=b.run(trial,f'mask379-p2batchmin-drop{drop}',seconds=90);e['drop']=drop;hist.append(e);print(json.dumps(e),flush=True)
 if e['status'].startswith('PASS_'):p=trial;owners.remove(drop);last=e
 (b.HERE/'mask379-minimized-progress.json').write_text(json.dumps(dict(required_cells=sorted(set(owners)|positive),positive_cells=sorted(positive),last_success=last,history=hist),indent=2)+'\n')
(b.HERE/'mask379-minimized-packet.json').write_text(json.dumps(p,indent=2)+'\n')
