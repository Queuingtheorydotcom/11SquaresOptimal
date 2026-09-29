import run_batch as b
import json,time
started=time.monotonic();rs=[json.loads(x) for x in (b.SCREEN/'results.jsonl').read_text().splitlines()];seen=set();todo=[]
for x in sorted([x for x in rs if 350<=x['mask']<=700 and x['positive_features']==1 and x['finite_budget']<10.99],key=lambda q:(q['finite_budget'],q['mask'])):
 p=b.packet(x['mask']);key=(tuple(p['source_physical_feature_indices']),tuple(i for i,g in enumerate(p['threshold_units']) if g))
 if key in seen:continue
 seen.add(key);todo.append((x,p))
history=[]
for count,(x,p) in enumerate(todo):
 if time.monotonic()-started>420:break
 mask=x['mask'];label=f'mask{mask}-p2batchfast{count+1}';entry=dict(mask=mask,features=p['source_physical_feature_indices'],**b.run(p,label));history.append(entry);(b.HERE/'gates-first-history.json').write_text(json.dumps(history,indent=2)+'\n');print(json.dumps(entry),flush=True)
