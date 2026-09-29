#!/usr/bin/env python3
import os
os.environ['NUMBA_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
from discover import *
start=time.time();data=np.load(OUT/'pilot1/finite-dual.npz');poses=data['poses'];du=data['coefficients'];budgetold=data['budget']
model,budget,meta=build(12000,seed=913,pool_per_contact=140)
rows=capture(model,poses);excess=du@rows.astype(np.int32)-2*budget
positive=np.flatnonzero(excess>0)
report={'status':'FLOATING_GROUP_PRICING_ONLY','candidate_new_groups':len(meta['new_groups']),'columns':len(budget),'dual_mass':float(sum(du)/2),'positive_excess_columns':positive.tolist(),'maximum_excess':float(max(excess)),'maximum_new_excess':float(max(excess[4731:])),'positive_columns':[{'column':int(j),'excess':float(excess[j]),'budget':float(budget[j]),'group':meta['new_groups'][j-4731] if j>=4731 else None} for j in positive],'elapsed':time.time()-start}
dest=OUT/'pricing1';dest.mkdir(exist_ok=True);(dest/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
np.savez_compressed(dest/'price-rows.npz',rows=rows,poses=poses,dual_numerators=du,budget=budget)
(dest/'model.json').write_text(json.dumps(meta,indent=2)+'\n');np.savez_compressed(dest/'model.npz',budget=budget,**model)
print(json.dumps({k:v for k,v in report.items() if k not in ('positive_columns','positive_excess_columns')},indent=2))
