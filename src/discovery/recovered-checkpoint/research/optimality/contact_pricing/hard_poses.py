#!/usr/bin/env python3
from discover import *
start=time.time();state=np.load(OUT/'adversarial1/state.npz');z=np.load(OUT/'adversarial1/model.npz');model={k:z[k].item() if k=='nvar' else z[k] for k in z.files if k!='budget'}
rows=state['rows'];poses=state['poses'];budget=state['budget'];active=thin(model,state['weights'])
h=np.load(ROOT/'research/optimality/deficit_geometry/endpoint-sample.npz');hp=h['poses'][:2576].copy();r=B/2*(abs(np.cos(hp[:,0]))+abs(np.sin(hp[:,0])));old=hp.copy();hp[:,1]=np.clip(hp[:,1],r,L-r);hp[:,2]=np.clip(hp[:,2],r,L-r)
ac=capture(active,hp);scores=ac@state['weights'];_,unique=np.unique(ac,axis=0,return_index=True);selected=unique[np.argsort(scores[unique])[:500]];selected=selected[scores[selected]<1-1e-8]
newposes=np.vstack([state['adversarial_poses'],hp[selected]]);newrows=capture(model,newposes);rows=np.vstack([rows,newrows]);poses=np.vstack([poses,newposes]);assert len(poses)<=5000
# Add positively priced contact floor groups.
f=np.load(OUT/'floor-pricing1/model.npz');fm={k:f[k].item() if k=='nvar' else f[k] for k in f.files if k!='budget'};result=json.loads((OUT/'floor-pricing1/RESULT.json').read_text());chosen=[r['column'] for r in result['positive_columns']];mapping={int(col):model['nvar']+i for i,col in enumerate(chosen)};keep=np.array([int(g) in mapping for g in fm['gids']]);only={}
for k,v in fm.items():
 if k=='points':only[k]=v
 elif k=='pids':only[k]=np.zeros(len(v),np.int32)
 elif k=='nvar':only[k]=len(chosen)+1
 elif k=='gids':only[k]=np.array([chosen.index(int(g))+1 for g in v[keep]],np.int32)
 else:only[k]=v[keep]
if chosen:
 rows=np.column_stack([rows,capture(only,poses)[:,1:]]);budget=np.r_[budget,f['budget'][chosen]]
 for k in model:
  if k in ('points','pids'):continue
  if k=='nvar':model[k]+=len(chosen)
  elif k=='gids':model[k]=np.r_[model[k],[mapping[int(v)] for v in fm[k][keep]]].astype(np.int32)
  else:model[k]=np.concatenate([model[k],fm[k][keep]])
unique,ui=np.unique(rows,axis=0,return_index=True)
with threadpool_limits(limits=1):sol=linprog(budget,A_ub=-csr_matrix(unique,dtype=float),b_ub=-np.ones(len(unique)),bounds=(0,None),method='highs')
assert sol.success
active=thin(model,sol.x);ap=legal_poses(qmc.Sobol(3,scramble=True,seed=4141).random_base2(14));scores=np.concatenate([capture(active,ap[i:i+1024])@sol.x for i in range(0,len(ap),1024)]);bad=np.argsort(scores)[:200];bad=bad[scores[bad]<1-1e-8]
out={'status':'FLOATING_HARD_POSE_AND_CONTACT_FLOOR_DISCOVERY_ONLY','global_bound_proved':False,'historical_pool_poses':2576,'historical_poses_clamped':int(np.any(old!=hp,axis=1).sum()),'historical_unique_active_profiles_added':len(selected),'previous_adversarial_profiles_added':len(state['adversarial_poses']),'floor_columns_added':chosen,'training_rows':len(poses),'distinct_rows':len(unique),'columns':model['nvar'],'mass':float(sol.fun),'positive_columns':int(sum(sol.x>1e-9)),'adversarial_minimum':float(min(scores)),'adversarial_failures':int(sum(scores<1-1e-9)),'elapsed':time.time()-start}
dest=OUT/'hard-poses1';dest.mkdir(exist_ok=True);(dest/'RESULT.json').write_text(json.dumps(out,indent=2)+'\n');np.savez_compressed(dest/'state.npz',rows=rows,poses=poses,budget=budget,weights=sol.x,dual=-sol.ineqlin.marginals,unique_indices=ui,historical_selected=selected,adversarial_poses=ap[bad],adversarial_rows=capture(model,ap[bad]),floor_columns=chosen,chosen_pool_columns=state['chosen_pool_columns']);np.savez_compressed(dest/'model.npz',budget=budget,**model)
print(json.dumps(out,indent=2))
