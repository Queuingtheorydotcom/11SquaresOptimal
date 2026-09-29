"""Numerical finite-LP screen for prefixes of a frozen exact ownership trace."""
from pathlib import Path
from fractions import Fraction as F
import os,sys,json,time,warnings,hashlib
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
from scipy.spatial import ConvexHull
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
H=Path(__file__).resolve().parent;WORK=H.parents[1];sys.path.insert(0,str(WORK/'phase2/screen'));import screen as sc
threadpool_limits(limits=1);sc.init();source=WORK/'phase2/geometry/mask1383_conditional_filter_checkpoint.json';full=json.loads(source.read_text());P=np.load(sc.BASE/'owned-tight/poses.npy');B=float(F(full['parent_side']))-1e-10;co=np.cos(P[:,0]);si=np.sin(P[:,0]);mask=full['mask'];maskbits=sum(1<<j for j in mask);n=sc.R.shape[1];summary=[]
for rnd in map(int,sys.argv[1:] or [1,2,3,4]):
 groups=full['rounds'][rnd]['prior_owned_points'];bits=sc.BITS.copy();start=time.time()
 for owner in mask:
  v=np.array([[float(F(x)) for x in p] for p in groups[owner]]);h=v[ConvexHull(v).vertices];gap=np.full(len(P),-1e100)
  for a,b in zip(h,np.roll(h,-1,axis=0)):
   nrm=np.array([b[1]-a[1],a[0]-b[0]]);nrm/=np.linalg.norm(nrm);q=P[:,1]*nrm[0]+P[:,2]*nrm[1];ext=B/2*(abs(co*nrm[0]+si*nrm[1])+abs(-si*nrm[0]+co*nrm[1]));proj=h@nrm;gap=np.maximum(gap,np.maximum(q-ext-proj.max(),proj.min()-q-ext))
  for nx,ny in [(co,si),(-si,co)]:
   q=P[:,1]*nx+P[:,2]*ny;proj=h[:,0,None]*nx[None,:]+h[:,1,None]*ny[None,:];gap=np.maximum(gap,np.maximum(q-B/2-proj.max(axis=0),proj.min(axis=0)-q-B/2))
  bits[gap<-1e-10]|=1<<owner
 inds=[np.flatnonzero(sc.LEGAL & sc.MEM[:,j] & ((bits & (maskbits^(1<<j)))==0)) for j in mask]
 if not all(map(len,inds)):print('FINITE_EMPTY',rnd,flush=True);continue
 row=np.concatenate(inds);cell=np.concatenate([np.full(len(r),i,dtype=int) for i,r in enumerate(inds)]);active=[];off=0
 for rr in inds:active.extend(off+np.argsort(sc.BQ[rr])[:100]);off+=len(rr)
 active=np.unique(np.r_[active,np.linspace(0,len(row)-1,600,dtype=int)]);last=sparse.csr_matrix(np.r_[np.zeros(n),-np.ones(11)][None,:]);rng=np.random.default_rng(1383)
 for it in range(25):
  mat=sparse.hstack([-sparse.csr_matrix(sc.R[row[active]].astype(float)),sparse.csr_matrix((np.ones(len(active)),(np.arange(len(active)),cell[active])),shape=(len(active),11))],format='csr');mat=sparse.vstack([mat,last],format='csr')
  with warnings.catch_warnings():
   warnings.simplefilter('ignore');res=linprog(np.r_[sc.COST,np.zeros(11)],A_ub=mat,b_ub=np.r_[np.zeros(len(active)),-11],bounds=(0,None),method='highs-ds',options={'threads':1,'time_limit':20,'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
  assert res.success
  w=np.maximum(res.x[:n],0);pos=np.flatnonzero(w>1e-10);q=sc.R[:,pos].astype(float)@w[pos];deficit=res.x[n:][cell]-q[row];bad=np.flatnonzero(deficit>1e-8)
  if not len(bad):break
  add=[]
  for j in range(11):
   jj=bad[cell[bad]==j]
   if len(jj):add.extend(jj[np.argsort(deficit[jj])[-50:]]);add.extend(rng.choice(jj,min(20,len(jj)),replace=False))
  active=np.unique(np.r_[active,add])
 g=np.array([q[rr].min() for rr in inds]);mass=float(sc.COST@w)*11/g.sum();w*=11/g.sum();g*=11/g.sum();np.savez_compressed(H/f'mask1383_round{rnd}_weights.npz',weights=w,gamma=g,mask=mask,capacity=sc.COST)
 record=dict(round=rnd,finite_budget=mass,positive_features=int(np.sum(w>1e-10)),iterations=it+1,violations=len(bad),counts=list(map(len,inds)),seconds=time.time()-start);print(record,flush=True);summary.append(record)
 trunc=dict(full);trunc['rounds']=full['rounds'][:rnd];trunc['owned_points']=groups;trunc['seconds']=None;trunc['truncated_from_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();trunc['truncation_rounds']=rnd
 (H/f'mask1383_round{rnd}_ownership.json').write_text(json.dumps(trunc,indent=2))
(H/'early_round_screen.json').write_text(json.dumps(summary,indent=2))
