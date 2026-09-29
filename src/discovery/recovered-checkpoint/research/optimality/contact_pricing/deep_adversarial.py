#!/usr/bin/env python3
from discover import *
start=time.time();st=np.load(OUT/'hard-poses1/state.npz');z=np.load(OUT/'hard-poses1/model.npz');model={k:z[k].item() if k=='nvar' else z[k] for k in z.files if k!='budget'}
rows=np.vstack([st['rows'],st['adversarial_rows']]);poses=np.vstack([st['poses'],st['adversarial_poses']]);budget=st['budget'];history=[];dest=OUT/'deep-adversarial1';dest.mkdir(exist_ok=True)
def compact(model,w):
 active=thin(model,w);ids=np.flatnonzero(w>1e-10);lookup=np.zeros(len(w),np.int32);lookup[ids]=np.arange(1,len(ids)+1)
 active['pids']=lookup[active['pids']];active['gids']=lookup[active['gids']];active['nvar']=len(ids)+1
 return active,np.r_[0.,w[ids]]
for iteration in range(4):
 unique,ui=np.unique(rows,axis=0,return_index=True)
 with threadpool_limits(limits=1):sol=linprog(budget,A_ub=-csr_matrix(unique,dtype=float),b_ub=-np.ones(len(unique)),bounds=(0,None),method='highs')
 assert sol.success;active,aw=compact(model,sol.x)
 ap=legal_poses(qmc.Sobol(3,scramble=True,seed=7300+iteration).random_base2(16));all_ac=[]
 for i in range(0,len(ap),1024):all_ac.append(capture(active,ap[i:i+1024]))
 ac=np.vstack(all_ac);scores=ac@aw;failposes=list(ap[scores<1-1e-8]);failedscores=list(scores[scores<1-1e-8]);mins=[float(min(scores))]
 def objective(z):
  z=np.asarray(z);p=legal_poses(z.T if z.ndim==2 else z);q=capture(active,p)@aw
  if len(failposes)<10000:
   for pp,v in zip(p,q):
    if v<1-1e-8:failposes.append(pp.copy());failedscores.append(float(v))
  mins.append(float(min(q)));return q
 for seed in range(5):
  differential_evolution(objective,[(0,1)]*3,seed=8811+seed+10*iteration,popsize=20,maxiter=100,tol=1e-8,atol=0,polish=False,vectorized=True,updating='deferred')
 fp=np.array(failposes);fs=np.array(failedscores)
 if len(fp):
  # Distinct active profiles selected from both independent and adaptive search.
  ca=np.vstack([capture(active,fp[i:i+512]) for i in range(0,len(fp),512)]);_,ix=np.unique(ca,axis=0,return_index=True);ix=ix[np.argsort(fs[ix])[:min(100,5000-len(rows))]];newposes=fp[ix];newrows=capture(model,newposes)
 else:newposes=np.empty((0,3));newrows=np.empty((0,len(budget)),np.uint8)
 report={'round':iteration,'training_rows':len(rows),'distinct_rows':len(unique),'mass':float(sol.fun),'positive_columns':int(sum(sol.x>1e-9)),'sobol_poses':len(ap),'sobol_minimum':float(min(scores)),'all_adversary_minimum':float(min(mins)),'new_distinct_profiles':len(newrows),'elapsed':time.time()-start}
 history.append(report);print(json.dumps(report),flush=True)
 np.savez_compressed(dest/'state.npz',rows=rows,poses=poses,budget=budget,weights=sol.x,dual=-sol.ineqlin.marginals,unique_indices=ui,adversarial_rows=newrows,adversarial_poses=newposes,floor_columns=st['floor_columns'],chosen_pool_columns=st['chosen_pool_columns'])
 (dest/'RESULT.json').write_text(json.dumps({'status':'FLOATING_ADAPTIVE_ENDPOINT_DISCOVERY_ONLY','global_bound_proved':False,'history':history},indent=2)+'\n')
 if sol.fun>=11-1e-8 or len(rows)>=5000 or not len(newrows):break
 rows=np.vstack([rows,newrows]);poses=np.vstack([poses,newposes])
