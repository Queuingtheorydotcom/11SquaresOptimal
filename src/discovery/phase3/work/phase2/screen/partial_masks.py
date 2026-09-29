"""Finite proposal search for small forbidden occupied patterns; no geometric proof."""
from pathlib import Path
import numpy as np,json,time,warnings
from scipy import sparse
from scipy.optimize import linprog
import screen as s
s.init();OUT=Path(__file__).parent/'partial';OUT.mkdir(exist_ok=True)
def solve(mask,tag):
 n=s.R.shape[1];m=len(mask);bits=sum(1<<i for i in mask);inds=[np.flatnonzero(s.LEGAL&s.MEM[:,i]&((s.BITS&(bits^(1<<i)))==0)) for i in mask];row=np.concatenate(inds);cell=np.concatenate([np.full(len(r),i,dtype=int) for i,r in enumerate(inds)]);active=[];off=0
 for rr in inds:active.extend(off+np.argsort(s.BQ[rr])[:150]);off+=len(rr)
 active=np.unique(np.r_[active,np.linspace(0,len(row)-1,600,dtype=int)]);last=sparse.csr_matrix(np.r_[np.zeros(n),-np.ones(m)][None,:]);best=1e99
 for iteration in range(30):
  mat=sparse.hstack([-sparse.csr_matrix(s.R[row[active]].astype(float)),sparse.csr_matrix((np.ones(len(active)),(np.arange(len(active)),cell[active])),shape=(len(active),m))],format='csr');mat=sparse.vstack([mat,last],format='csr')
  with warnings.catch_warnings():
   warnings.simplefilter('ignore');res=linprog(np.r_[s.COST,np.zeros(m)],A_ub=mat,b_ub=np.r_[np.zeros(len(active)),-m],bounds=(0,None),method='highs-ds',options={'threads':1,'time_limit':15})
  if not res.success:break
  w=np.maximum(res.x[:n],0);pos=np.flatnonzero(w>1e-10);q=s.R[:,pos].astype(float)@w[pos];g=np.array([q[rr].min() for rr in inds]);mass=float(s.COST@w)*m/g.sum() if g.sum()>1e-10 else 1e99
  if mass<best:best=mass;np.savez_compressed(OUT/(tag+'.npz'),weights=w*m/g.sum(),gamma=g*m/g.sum(),mask=mask)
  deficit=res.x[n:][cell]-q[row];bad=np.flatnonzero(deficit>1e-8)
  if not len(bad):break
  add=[]
  for j in range(m):
   jj=bad[cell[bad]==j]
   if len(jj):add.extend(jj[np.argsort(deficit[jj])[-50:]])
  active=np.unique(np.r_[active,add])
 result=dict(pattern=mask,tag=tag,finite_budget=best,required_gamma_sum=m,converged=not len(bad),iterations=iteration+1,global_optimality_proved=False);(OUT/(tag+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
for mask,tag in [([0,1,2,3],'toprow'),([1,5,9,13],'innercolumn'),([4,5,6,7],'innerrow')]:solve(mask,tag)
