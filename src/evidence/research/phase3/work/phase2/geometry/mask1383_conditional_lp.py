"""Numerical dual-profile diagnosis, explicitly not a geometric certificate."""
from pathlib import Path
import sys,os,json,time,warnings
os.environ['OPENBLAS_NUM_THREADS']='1'
H=Path(__file__).resolve().parent;SCREEN=H.parent/'screen';sys.path.insert(0,str(SCREEN));import screen as sc
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
threadpool_limits(limits=1);sc.init();sc.BITS=sc.BITS|np.load(H/'mask1383_conditional_hull_capture_bits.npy');idx=1383;mask=sc.MASKS[idx];bits=sum(1<<i for i in mask);n=sc.R.shape[1]
inds=[np.flatnonzero(sc.LEGAL & sc.MEM[:,i] & ((sc.BITS & (bits^(1<<i)))==0)) for i in mask]
row=np.concatenate(inds);cell=np.concatenate([np.full(len(r),i,dtype=int) for i,r in enumerate(inds)])
active=[];off=0
for rr in inds:active.extend(off+np.argsort(sc.BQ[rr])[:100]);off+=len(rr)
active=np.unique(np.r_[active,np.linspace(0,len(row)-1,600,dtype=int)]);last=sparse.csr_matrix(np.r_[np.zeros(n),-np.ones(11)][None,:]);rng=np.random.default_rng(idx)
for it in range(35):
 mat=sparse.hstack([-sparse.csr_matrix(sc.R[row[active]].astype(float)),sparse.csr_matrix((np.ones(len(active)),(np.arange(len(active)),cell[active])),shape=(len(active),11))],format='csr');mat=sparse.vstack([mat,last],format='csr')
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');res=linprog(np.r_[sc.COST,np.zeros(11)],A_ub=mat,b_ub=np.r_[np.zeros(len(active)),-11],bounds=(0,None),method='highs-ds',options={'threads':1,'time_limit':30,'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
 assert res.success
 w=np.maximum(res.x[:n],0);pos=np.flatnonzero(w>1e-10);q=sc.R[:,pos].astype(float)@w[pos];deficit=res.x[n:][cell]-q[row];bad=np.flatnonzero(deficit>1e-8);print(it,len(active),res.fun,len(bad),flush=True)
 if not len(bad):break
 add=[]
 for j in range(11):
  jj=bad[cell[bad]==j]
  if len(jj):add.extend(jj[np.argsort(deficit[jj])[-50:]]);add.extend(rng.choice(jj,min(20,len(jj)),replace=False))
 active=np.unique(np.r_[active,add])
lamb=np.maximum(0,-res.ineqlin.marginals[:-1]);mu=-res.ineqlin.marginals[-1];selected=np.flatnonzero(lamb>1e-8);P=np.load(sc.BASE/'owned-tight/poses.npy');records=[]
for i in selected:
 ar=active[i];r=row[ar];c=cell[ar];records.append(dict(row=int(r),cell=int(mask[c]),mass=float(lamb[i]/mu),pose=P[r].tolist()))
from fractions import Fraction as F
out=dict(status='NUMERICAL_CONDITIONAL_HULL_FINITE_LP_DIAGNOSIS',mask_index=idx,mask=mask,budget=res.fun,mu=mu,records=records,global_optimality_proved=False,scope='Finite legal-pose profile mixture only; poses need not coexist. Geometric continuum or exact rational feasibility is not asserted.')
(H/'mask1383_conditional_dual.json').write_text(json.dumps(out,indent=2));np.savez_compressed(H/'mask1383_conditional_dual.npz',row=np.array([r['row'] for r in records]),cell=np.array([r['cell'] for r in records]),mass=np.array([r['mass'] for r in records]),profiles=sc.R[[r['row'] for r in records]],poses=P[[r['row'] for r in records]])
print('dual rows',len(records),'cells',[(c,sum(r['mass'] for r in records if r['cell']==c)) for c in mask])

np.savez_compressed(H/'mask1383_conditional_weights.npz',weights=np.maximum(res.x[:n],0),gamma=np.array([q[rr].min() for rr in inds]),mask=np.array(mask),capacity=sc.COST)
print('positive_features',int(np.count_nonzero(res.x[:n]>1e-10)),flush=True)
