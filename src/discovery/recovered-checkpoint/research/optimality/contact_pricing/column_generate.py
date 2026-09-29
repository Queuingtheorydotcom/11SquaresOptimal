#!/usr/bin/env python3
"""Finite column generation, with numerical pose sampling only."""
from discover import *
start=time.time();base=np.load(OUT/'pilot1/state.npz');pool=np.load(OUT/'pricing1/model.npz')
poolmodel={k:pool[k].item() if k=='nvar' else pool[k] for k in pool.files if k!='budget'}
poolbudget=pool['budget'];poolmeta=json.loads((OUT/'pricing1/model.json').read_text())
basecols=base['rows'].shape[1];rows=base['rows'].copy();poses=base['poses'].copy();budgets=base['budget'].copy();chosen=[];history=[]
dest=OUT/'column-generation1';dest.mkdir(exist_ok=True)

def subset(cols):
 cs=np.array(cols,int);lookup=np.full(poolmodel['nvar'],-1,np.int32);lookup[cs]=np.arange(1,len(cs)+1)
 gkeep=lookup[poolmodel['gids']]>=0
 m={}
 for k,v in poolmodel.items():
  if k=='nvar':m[k]=len(cs)+1
  elif k=='points':m[k]=v
  elif k=='pids':m[k]=np.zeros(len(v),np.int32)
  elif k=='gids':m[k]=lookup[v[gkeep]]
  else:m[k]=v[gkeep]
 return m

# The 26 columns already priced against the first dual.
add=json.loads((OUT/'pricing1/RESULT.json').read_text())['positive_excess_columns']
for iteration in range(12):
 if add:
  chosen.extend(add);newrows=capture(subset(add),poses)[:,1:];rows=np.column_stack([rows,newrows]);budgets=np.r_[budgets,poolbudget[add]]
 unique,ui=np.unique(rows,axis=0,return_index=True)
 with threadpool_limits(limits=1):sol=linprog(budgets,A_ub=-csr_matrix(unique,dtype=float),b_ub=-np.ones(len(unique)),bounds=(0,None),method='highs')
 assert sol.success
 du=-sol.ineqlin.marginals;support=np.flatnonzero(du>1e-8);pr=capture(poolmodel,poses[ui[support]])
 reduced=du[support]@pr-poolbudget;reduced[:4731]=-np.inf
 if chosen:reduced[chosen]=-np.inf
 add=[int(j) for j in np.argsort(-reduced)[:80] if reduced[j]>1e-7]
 report={'round':iteration,'rows':len(rows),'columns':rows.shape[1],'new_priced_columns_added':len(chosen),'mass':float(sol.fun),'dual_support':len(support),'best_new_reduced_profit':float(np.max(reduced)),'new_columns_next':len(add),'elapsed':time.time()-start}
 history.append(report);print(json.dumps(report),flush=True)
 np.savez_compressed(dest/'state.npz',rows=rows,poses=poses,budget=budgets,weights=sol.x,dual=du,unique_indices=ui,chosen_pool_columns=chosen)
 (dest/'RESULT.json').write_text(json.dumps({'status':'FINITE_FLOATING_COLUMN_GENERATION_ONLY','global_bound_proved':False,'history':history,'pool_model_sha256':digest(OUT/'pricing1/model.json'),'chosen_pool_columns':chosen},indent=2)+'\n')
 if sol.fun<10.999999 or not add:break
