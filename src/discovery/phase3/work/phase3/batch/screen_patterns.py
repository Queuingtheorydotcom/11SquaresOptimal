from pathlib import Path
import json,sys,time
import pattern_solver as ps
HERE=Path(__file__).resolve().parent;PHASE=HERE.parent;ps.init();extra=[p for p,n,e in ps.compatible()];rows=[];count=0
known=[]
for f in PHASE.glob('*/patterns.json'):
 d=json.loads(f.read_text());d=d.get('patterns',[])if isinstance(d,dict)else d
 for q in d:
  if str(q.get('status','')).startswith('PASS_EXACT_'):known.append(set(q['required_cells']))
for v in json.loads((HERE/'patterns.json').read_text()):
 if not v.get('final')or len(v['required_cells'])<7:continue
 required=set(v['required_cells'])
 for drop in sorted(required):
  J=required-{drop};T={15-i for i in J}
  if any(K<=J or K<=T for K in known):continue
  count+=1;tag=f'p3batchpattern{v["mask"]}omit{drop}';r=ps.solve(v['mask'],tag,sorted(J),seconds=20,extra=extra);e=dict(mask=v['mask'],drop=drop,required_cells=sorted(J),tag=tag,status=r['status'],finite_budget=r.get('best_budget'),features=r.get('positive_weight_count'),geometry_coverage=False);rows.append(e);(HERE/'pattern-screen.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(e),flush=True)
