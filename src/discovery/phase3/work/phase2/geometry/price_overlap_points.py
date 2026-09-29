"""Numerical discovery of NEW point resources from a finite typed-LP dual.
Final output is a proposal only; an exact continuum gate remains mandatory.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,os,json,time,warnings,math
os.environ['OPENBLAS_NUM_THREADS']='1'
H=Path(__file__).resolve().parent;SCREEN=H.parent/'screen';sys.path.insert(0,str(SCREEN));import screen as sc
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
threadpool_limits(limits=1);sc.init();idx=int(sys.argv[1]) if len(sys.argv)>1 else 1383
mask=sc.MASKS[idx];bits=sum(1<<i for i in mask);nbase=sc.R.shape[1];P=np.load(sc.BASE/'owned-tight/poses.npy');meta=json.loads((sc.BASE/'owned-tight/capture-progress.json').read_text());B=float(F(meta['fixed_homothety_B']));core=B-1e-10
extras=[np.load(p) for p in sorted(H.glob(f'mask{idx}_feedback*.npz'))]
if extras:
 sc.R=np.vstack([sc.R,*[e['rows'] for e in extras]])
 extraP=np.vstack([e['poses'] for e in extras]);P=np.vstack([P,extraP]);sc.LEGAL=np.r_[sc.LEGAL,np.concatenate([e['legal'] for e in extras])];sc.MEM=np.vstack([sc.MEM,*[e['memberships'] for e in extras]])
 groups=json.loads((H.parents[1]/'geometry/wall_ownership_groups.json').read_text())['groups'];eb=np.zeros(len(extraP),np.uint16);ec=np.cos(extraP[:,0]);es=np.sin(extraP[:,0])
 for j,group in enumerate(groups):
  for pp in group:
   dx=float(F(pp[0]))-extraP[:,1];dy=float(F(pp[1]))-extraP[:,2];hit=np.maximum(abs(dx*ec+dy*es),abs(-dx*es+dy*ec))<B/2-2e-12;eb[hit]|=1<<j
 sc.BITS=np.r_[sc.BITS,eb];bw=np.load(sc.BASE/'model-arrays.npz')['baseline_weights'];sc.BQ=np.r_[sc.BQ,np.vstack([e['rows'] for e in extras])@bw]
co=np.cos(P[:,0]);si=np.sin(P[:,0])
inds=[np.flatnonzero(sc.LEGAL & sc.MEM[:,i] & ((sc.BITS & (bits^(1<<i)))==0)) for i in mask]
row=np.concatenate(inds);cell=np.concatenate([np.full(len(r),i,dtype=int) for i,r in enumerate(inds)])
active=[];off=0
for rr in inds:active.extend(off+np.argsort(sc.BQ[rr])[:100]);off+=len(rr)
active=np.unique(np.r_[active,np.linspace(0,len(row)-1,600,dtype=int)]);rng=np.random.default_rng(idx);sites=[];columns=np.empty((len(P),0),np.uint8);history=[];start=time.time()
seed=H/f'mask{idx}_newpoints_history.json'
if seed.exists():
 sites=json.loads(seed.read_text())['sites']
 for point in sites:
  x,y=np.array(point)/1e10;dx=x-P[:,1];dy=y-P[:,2];cap=np.maximum(abs(dx*co+dy*si),abs(-dx*si+dy*co))<core/2-1e-12;columns=np.column_stack((columns,cap.astype(np.uint8)))
def clip(poly,n,b):
 if not len(poly):return poly
 out=[]
 for p,q in zip(poly,np.roll(poly,-1,axis=0)):
  a=p@n-b;z=q@n-b;ia=a<=0;iz=z<=0
  if ia:out.append(p)
  if ia!=iz:out.append(p+a/(a-z)*(q-p))
 return np.array(out).reshape((-1,2))
def square(p):
 t,x,y=p;c=math.cos(t);s=math.sin(t)
 return np.array([[x+core*(a*c-b*s)/2,y+core*(a*s+b*c)/2] for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]])
def intersection(a,b):
 p=square(a);c=math.cos(b[0]);s=math.sin(b[0])
 for n in [np.array([c,s]),np.array([-c,-s]),np.array([-s,c]),np.array([s,-c])]:p=clip(p,n,core/2+b[1:]@n)
 return p
for pricing in range(30):
 n=nbase+len(sites);cost=np.r_[sc.COST,np.ones(len(sites))];last=sparse.csr_matrix(np.r_[np.zeros(n),-np.ones(11)][None,:])
 for it in range(40):
  ar=row[active];base=sparse.csr_matrix(sc.R[ar].astype(float));new=sparse.csr_matrix(columns[ar].astype(float));mat=sparse.hstack([-base,-new,sparse.csr_matrix((np.ones(len(active)),(np.arange(len(active)),cell[active])),shape=(len(active),11))],format='csr');mat=sparse.vstack([mat,last],format='csr')
  with warnings.catch_warnings():
   warnings.simplefilter('ignore');res=linprog(np.r_[cost,np.zeros(11)],A_ub=mat,b_ub=np.r_[np.zeros(len(active)),-11],bounds=(0,None),method='highs-ds',options={'threads':1,'time_limit':20,'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
  assert res.success
  w=np.maximum(res.x[:n],0);pos=np.flatnonzero(w[:nbase]>1e-10);q=sc.R[:,pos].astype(float)@w[pos]+columns.astype(float)@w[nbase:];deficit=res.x[n:][cell]-q[row];bad=np.flatnonzero(deficit>1e-8)
  if not len(bad):break
  add=[]
  for j in range(11):
   jj=bad[cell[bad]==j]
   if len(jj):add.extend(jj[np.argsort(deficit[jj])[-50:]]);add.extend(rng.choice(jj,min(15,len(jj)),replace=False))
  active=np.unique(np.r_[active,add])
 assert not len(bad),'Finite rows not fully priced'
 g=np.array([q[rr].min() for rr in inds]);mass=float(cost@w)*11/g.sum();w*=11/g.sum();g*=11/g.sum()
 entry=dict(pricing=pricing,sites=len(sites),budget=mass,active=len(active),seconds=time.time()-start);history.append(entry);print(entry,flush=True)
 np.savez_compressed(H/f'mask{idx}_newpoints_weights.npz',weights=w,gamma=g,mask=mask,sites=np.array(sites,dtype=np.int64).reshape((-1,2)),capacity=cost)
 (H/f'mask{idx}_newpoints_history.json').write_text(json.dumps(dict(status='FINITE_NEWPOINT_PRICING',mask=mask,history=history,sites=sites,coordinate_denominator=10**10,global_optimality_proved=False),indent=2))
 if mass<10.99999:print('STRICT_FINITE_GAP',mass,flush=True);break
 lamb=np.maximum(0,-res.ineqlin.marginals[:-1]);mu=-res.ineqlin.marginals[-1];selected=np.flatnonzero(lamb>1e-8);ar=active[selected];rr=row[ar];cc=cell[ar];la=lamb[selected]/mu
 for j in range(11):
  ii=cc==j;la[ii]/=la[ii].sum()
 poses=P[rr];candidates=[]
 for i in range(len(rr)):
  for j in range(i):
   if cc[i]==cc[j]:continue
   poly=intersection(poses[i],poses[j])
   if len(poly)<3:continue
   center=poly.mean(axis=0);candidates.append(center)
   candidates.extend(.999*v+.001*center for v in poly)
 if not candidates:print('NO_INTERSECTION_CANDIDATES',flush=True);break
 candidates=np.unique(np.round(np.array(candidates)*10**10).astype(np.int64),axis=0);px=candidates[:,0]/1e10;py=candidates[:,1]/1e10
 dx=px[:,None]-poses[:,1];dy=py[:,None]-poses[:,2];ct=np.cos(poses[:,0]);st=np.sin(poses[:,0]);caps=np.maximum(abs(dx*ct+dy*st),abs(-dx*st+dy*ct))<core/2-1e-11;charges=caps@la;order=np.argsort(charges)[::-1];added=[]
 for k in order:
  if charges[k]<=1+1e-7:break
  point=candidates[k].tolist()
  if point in sites:continue
  if any(np.linalg.norm((candidates[k]-np.array(p))/1e10)<.005 for p in added):continue
  added.append(point)
  if len(added)>=5:break
 print('dual rows',len(rr),'maxnewpointcharge',max(charges),'adding',len(added),flush=True)
 if not added:break
 for point in added:
  sites.append(point);x,y=np.array(point)/1e10;dx=x-P[:,1];dy=y-P[:,2];cap=np.maximum(abs(dx*co+dy*si),abs(-dx*si+dy*co))<core/2-1e-12;columns=np.column_stack((columns,cap.astype(np.uint8)))
