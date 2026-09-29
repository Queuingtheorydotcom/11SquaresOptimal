"""Finite pose LP screen only. No result in this file is a continuum proof."""
from pathlib import Path
from fractions import Fraction as F
import os,sys,json,time,argparse,warnings,multiprocessing as mp
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
BASE=Path('/workspace/scratch/6def36ddf53b/current/research/optimality/deficit_geometry/physical_features')
HERE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
def prepare():
 ds=BASE/'owned-tight';P=np.load(ds/'poses.npy');cap=np.load(ds/'fivepoint-captures.npy').copy();c=np.cos(P[:,0]);s=np.sin(P[:,0]);meta=json.loads((ds/'capture-progress.json').read_text());B=float(F(meta['fixed_homothety_B']))
 groups=json.loads((HERE.parents[1]/'geometry/wall_ownership_groups.json').read_text())['groups']
 for j,g in enumerate(groups):
  for p in g:
   dx=float(F(p[0]))-P[:,1];dy=float(F(p[1]))-P[:,2]
   cap[:,j]|=np.maximum(abs(c*dx+s*dy),abs(-s*dx+c*dy))<B/2-2e-12
 bits=(cap.astype(np.uint16)*(1<<np.arange(16,dtype=np.uint16))).sum(axis=1,dtype=np.uint16)
 np.save(HERE/'capture-bits.npy',bits)
 global R,LEGAL,MEM,BITS,COST,BQ,MASKS
 init();np.save(HERE/'baseline-charge.npy',R@np.load(BASE/'model-arrays.npz')['baseline_weights'])
def init():
 global R,LEGAL,MEM,BITS,COST,BQ,MASKS
 threadpool_limits(limits=1)
 ds=BASE/'owned-tight';R=np.load(ds/'rows.npy',mmap_mode='r');LEGAL=np.load(ds/'legal.npy');MEM=np.load(ds/'raw-memberships.npy');BITS=np.load(HERE/'capture-bits.npy');COST=np.load(BASE/'model-arrays.npz')['capacity'];BQ=np.load(HERE/'baseline-charge.npy') if (HERE/'baseline-charge.npy').exists() else None
 MASKS=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text())['canonical_eleven_cell_subsets']
def screen(task):
 idx,iterations=task;start=time.monotonic();mask=MASKS[idx];bits=sum(1<<i for i in mask);n=R.shape[1]
 inds=[np.flatnonzero(LEGAL & MEM[:,i] & ((BITS & (bits^(1<<i)))==0)) for i in mask]
 counts=[len(i) for i in inds]
 if not all(counts):return dict(mask=idx,status='EMPTY_FINITE_DOMAIN_ONLY',counts=counts,geometry_coverage=False)
 row=np.concatenate(inds);cell=np.concatenate([np.full(len(r),i,dtype=int) for i,r in enumerate(inds)])
 active=[];off=0
 for rr in inds:active.extend(off+np.argsort(BQ[rr])[:50]);off+=len(rr)
 active=np.unique(np.r_[active,np.linspace(0,len(row)-1,400,dtype=int)])
 last=sparse.csr_matrix(np.r_[np.zeros(n),-np.ones(11)][None,:]);best=1e99;bestw=None;bestg=None;status='ITERATION_LIMIT';rng=np.random.default_rng(idx)
 for k in range(iterations):
  mat=sparse.hstack([-sparse.csr_matrix(R[row[active]].astype(float)),sparse.csr_matrix((np.ones(len(active)),(np.arange(len(active)),cell[active])),shape=(len(active),11))],format='csr');mat=sparse.vstack([mat,last],format='csr')
  with warnings.catch_warnings():
   warnings.simplefilter('ignore');res=linprog(np.r_[COST,np.zeros(11)],A_ub=mat,b_ub=np.r_[np.zeros(len(active)),-11],bounds=(0,None),method='highs-ds',options={'threads':1,'time_limit':10,'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
  if not res.success:status='SOLVER_'+str(res.status);break
  w=np.maximum(res.x[:n],0);pos=np.flatnonzero(w>1e-10)
  q=R[:,pos].astype(float)@w[pos] if len(pos) else np.zeros(len(R))
  g=np.array([q[rr].min() for rr in inds]);mass=float(COST@w)*11/g.sum() if g.sum()>1e-10 else 1e99
  if mass<best:best=mass;bestw=w*11/g.sum();bestg=g*11/g.sum()
  deficit=res.x[n:][cell]-q[row];bad=np.flatnonzero(deficit>1e-8)
  if not len(bad):status='FINITE_LP_CONVERGED';break
  add=[]
  for j in range(11):
   jj=bad[cell[bad]==j]
   if len(jj):add.extend(jj[np.argsort(deficit[jj])[-35:]]);add.extend(rng.choice(jj,min(10,len(jj)),replace=False))
  active=np.unique(np.r_[active,add])
  if time.monotonic()-start>25:status='TIME_LIMIT';break
  if len(active)>6000:status='ROW_LIMIT';break
 if bestw is not None:
  np.savez_compressed(HERE/f'weights-{idx}.npz',weights=bestw,gamma=bestg,mask=mask)
 return dict(mask=idx,status=status,finite_budget=best,positive_features=int(np.count_nonzero(bestw>1e-10)) if bestw is not None else 0,iterations=k+1,counts=counts,seconds=time.monotonic()-start,geometry_coverage=False,global_optimality_proved=False)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=3);ap.add_argument('--limit',type=int,default=1944);ap.add_argument('--iterations',type=int,default=12);a=ap.parse_args()
 if not (HERE/'baseline-charge.npy').exists():prepare()
 cover=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text());old=json.loads((HERE.parents[1]/'new_mask_audit/two-pattern-union-independent-audit.json').read_text());remaining=[i for i in range(2184) if i not in old['excluded_canonical_mask_indices']]
 # Balanced broad pilot followed by remaining canonical cases; keep candidate controls.
 pilot=list(dict.fromkeys([0,438,999,1462,1659]+[remaining[int(x)] for x in np.linspace(0,len(remaining)-1,64)]));order=pilot+[i for i in remaining if i not in pilot]
 done=set()
 if (HERE/'results.jsonl').exists():
  for line in (HERE/'results.jsonl').read_text().splitlines():done.add(json.loads(line)['mask'])
 todo=[i for i in order if i not in done][:a.limit];start=time.monotonic()
 with mp.get_context('spawn').Pool(a.workers,initializer=init) as pool,(HERE/'results.jsonl').open('a',buffering=1) as f:
  for j,r in enumerate(pool.imap_unordered(screen,[(i,a.iterations) for i in todo])):
   f.write(json.dumps(r)+'\n')
   if j%16==0:print(json.dumps({'done':len(done)+j+1,'elapsed':time.monotonic()-start,'last':r}),flush=True)
if __name__=='__main__':main()
