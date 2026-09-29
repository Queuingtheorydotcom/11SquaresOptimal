#!/usr/bin/env python3
from discover import *
start=time.time();cg=np.load(OUT/'column-generation1/state.npz');base=np.load(OUT/'pilot1/model.npz');pool=np.load(OUT/'pricing1/model.npz')
model={k:base[k].item() if k=='nvar' else base[k] for k in base.files if k!='budget'};chosen=cg['chosen_pool_columns'];mapping={int(col):model['nvar']+i for i,col in enumerate(chosen)};keep=np.array([int(g) in mapping for g in pool['gids']])
for k in model:
 if k in ('points','pids'):continue
 if k=='nvar':model[k]+=len(chosen)
 elif k=='gids':model[k]=np.r_[model[k],[mapping[int(v)] for v in pool[k][keep]]].astype(np.int32)
 else:model[k]=np.concatenate([model[k],pool[k][keep]])
rows=cg['rows'];poses=cg['poses'];budget=cg['budget'];history=[];dest=OUT/'adversarial1';dest.mkdir(exist_ok=True)
np.savez_compressed(dest/'model.npz',budget=budget,**model)
for iteration in range(6):
 unique,ui=np.unique(rows,axis=0,return_index=True)
 with threadpool_limits(limits=1):sol=linprog(budget,A_ub=-csr_matrix(unique,dtype=float),b_ub=-np.ones(len(unique)),bounds=(0,None),method='highs')
 assert sol.success;active=thin(model,sol.x)
 z=qmc.Sobol(3,scramble=True,seed=900+iteration).random_base2(13);adversary=legal_poses(z)
 ac=np.vstack([capture(active,adversary[i:i+1024]) for i in range(0,len(adversary),1024)]);scores=ac@sol.x
 order=np.argsort(scores);local=[]
 for theta,x,y in adversary[order[:30]]:
  for da,dx,dy in itertools.product([-1,0,1],repeat=3):
   aa=theta+da*.0005;r=B/2*(abs(np.cos(aa))+abs(np.sin(aa)));local.append([aa,np.clip(x+dx*.0005,r,L-r),np.clip(y+dy*.0005,r,L-r)])
 local=np.array(local);lc=capture(active,local);ls=lc@sol.x
 allposes=np.vstack([adversary,local]);allscores=np.r_[scores,ls];active_rows=np.vstack([ac,lc]);_,keep=np.unique(active_rows,axis=0,return_index=True);bad=keep[np.argsort(allscores[keep])[:200]]
 bad=bad[allscores[bad]<1-1e-9];newposes=allposes[bad];newrows=capture(model,newposes)
 report={'round':iteration,'poses':len(poses),'distinct_rows':len(unique),'mass':float(sol.fun),'positive_columns':int(sum(sol.x>1e-9)),'adversarial_minimum':float(min(allscores)),'new_rows':len(newrows),'elapsed':time.time()-start}
 history.append(report);print(json.dumps(report),flush=True)
 np.savez_compressed(dest/'state.npz',rows=rows,poses=poses,budget=budget,weights=sol.x,dual=-sol.ineqlin.marginals,unique_indices=ui,adversarial_rows=newrows,adversarial_poses=newposes,chosen_pool_columns=chosen)
 (dest/'RESULT.json').write_text(json.dumps({'status':'FLOATING_FINITE_LP_AND_ADVERSARIAL_SEARCH_ONLY','global_bound_proved':False,'history':history},indent=2)+'\n')
 if sol.fun>=11-1e-8 or len(bad)==0 or len(poses)+len(bad)>5000:break
 rows=np.vstack([rows,newrows]);poses=np.vstack([poses,newposes])
