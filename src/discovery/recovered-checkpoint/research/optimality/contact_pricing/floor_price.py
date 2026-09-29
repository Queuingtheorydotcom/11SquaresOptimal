#!/usr/bin/env python3
from discover import *
start=time.time();state=np.load(OUT/'adversarial1/state.npz');du=state['dual'];supp=np.flatnonzero(du>1e-8);poses=state['poses'][state['unique_indices'][supp]]
model,budget,meta=build(6000,seed=1401,pool_per_contact=75,cardinalities=(5,7))
mask=model['gids']>=4731;model['kinds'][mask]=1;model['thresholds'][mask]=(model['length'][mask]-1)//2;budget[4731:]*=2
for g in meta['new_groups']:
 g['kind']='floor';g['threshold']=(g['cardinality']-1)//2;g['budget']*=2
rows=capture(model,poses);profit=du[supp]@rows-budget;positive=np.flatnonzero((profit>1e-7)&(np.arange(len(budget))>=4731))
report={'status':'FLOATING_FLOOR_FEATURE_PRICING_ONLY','global_bound_proved':False,'dual_mass':float(sum(du)),'dual_support':len(supp),'groups_priced':len(meta['new_groups']),'positive_columns':[{'column':int(j),'profit':float(profit[j]),'group':meta['new_groups'][j-4731]} for j in positive],'maximum_profit':float(max(profit[4731:])),'elapsed':time.time()-start}
dest=OUT/'floor-pricing1';dest.mkdir(exist_ok=True);(dest/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n');(dest/'model.json').write_text(json.dumps(meta,indent=2)+'\n');np.savez_compressed(dest/'model.npz',budget=budget,**model);np.savez_compressed(dest/'price-rows.npz',rows=rows,poses=poses,dual=du[supp],budget=budget)
print(json.dumps({k:v for k,v in report.items() if k!='positive_columns'}));print('positive_count',len(positive))
