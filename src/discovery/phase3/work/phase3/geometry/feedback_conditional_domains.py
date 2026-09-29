"""Discovery: exact deficit recapture, numerical neighbors, conditional finite LP."""
from pathlib import Path
from fractions import Fraction as F
import argparse,json,math,os,sys,warnings,time,hashlib
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
from scipy.spatial import ConvexHull
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[1];ROOT=WORK.parent/'current'
sys.path.insert(0,str(WORK/'phase2/screen'));import screen as sc
BASE=ROOT/'research/optimality/deficit_geometry/physical_features';sys.path.insert(0,str(BASE));from model import PhysicalModel
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ownership',type=Path,required=True);ap.add_argument('--gate',type=Path,action='append');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--jitter',type=int,default=2048);a=ap.parse_args();threadpool_limits(limits=1);sc.init();source=json.loads(a.ownership.read_text());mask=source['mask'];generic=source.get('schema')=='exact_generic_owned_hull_v1';U=F(source['U'] if generic else source['parent_Uplus']);L=F(191,50);B=L/U;groups=[source['final_state']['groups'].get(str(j),[]) for j in range(16)] if generic else source['owned_points'];maskbits=sum(1<<j for j in mask)
 cover=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text());sites=[tuple(map(F,c['center'])) for c in cover['cells']]
 for gate in a.gate or []:
  report=json.loads(gate.read_text());rr=report['records'][-1];p=rr['pieces'][-1]['parent_witness'];t=F(p['half_angle']);center=tuple(map(F,p['center']));m=PhysicalModel();exact=m.exact(B-F(1,10**10));poses=[];rows=[];mem=[]
  for swap in (0,1):
   for sx in (-1,1):
    for sy in (-1,1):
     v=center[::-1] if swap else center;cc=tuple(x if sign==1 else L-x for x,sign in zip(v,(sx,sy)));tt=t if sx*sy*(-1 if swap else 1)==1 else (1-t)/(1+t);rows.append(exact.row(tt,cc)[:m.nvar]);poses.append([2*math.atan(float(tt)),*map(float,cc)]);u=tuple((x-B/2)/(L-B) for x in cc);dist=[sum((x-y)**2 for x,y in zip(u,s)) for s in sites];mem.append([v==min(dist) for v in dist])
  rng=np.random.default_rng(int(hashlib.sha256(gate.read_bytes()).hexdigest()[:12],16));P=np.array(poses)[rng.integers(8,size=a.jitter)].copy();P+=rng.normal(size=P.shape)*10**rng.uniform(-7,-1.5,size=(len(P),1));P[:,0]%=np.pi/2;rad=float(B)/2*(np.cos(P[:,0])+np.sin(P[:,0]));P[:,1:]=np.clip(P[:,1:],rad[:,None],float(L)-rad[:,None]);u=(P[:,1:]-float(B)/2)/float(L-B);gen=np.array([[float(x) for x in p] for p in sites]);dist=((u[:,None,:]-gen[None,:,:])**2).sum(axis=2);mm=dist<=dist.min(axis=1)[:,None]+1e-12
  out=HERE/(a.output.stem+'_'+hashlib.sha256(gate.read_bytes()).hexdigest()[:10]+'_extra.npz');np.savez_compressed(out,rows=np.vstack([rows,m.capture(float(B)-1e-10,P)]),poses=np.vstack([poses,P]),memberships=np.vstack([mem,mm]),legal=np.ones(8+len(P),bool));print('recaptured',out,flush=True)
 extras=sorted((WORK/'phase2/geometry').glob('*-exact.npz'))+sorted((WORK/'phase2/geometry').glob('*-jitter.npz'))+sorted(HERE.glob('*_extra.npz'));zs=[np.load(p) for p in extras]
 R=np.vstack([sc.R,*[z['rows'][:,:sc.R.shape[1]] for z in zs]]);P=np.vstack([np.load(sc.BASE/'owned-tight/poses.npy'),*[z['poses'] for z in zs]]);MEM=np.vstack([sc.MEM,*[z['memberships'] for z in zs]]);legal=np.r_[sc.LEGAL,*[z['legal'] for z in zs]];bits=np.zeros(len(P),np.uint16);co=np.cos(P[:,0]);si=np.sin(P[:,0]);b=float(B)-1e-10
 for owner in mask:
  v=np.array([[float(F(x)) for x in p] for p in groups[owner]]);h=v[ConvexHull(v).vertices];gap=np.full(len(P),-1e100)
  for p,q in zip(h,np.roll(h,-1,axis=0)):
   normal=np.array([q[1]-p[1],p[0]-q[0]]);normal/=np.linalg.norm(normal);cen=P[:,1]*normal[0]+P[:,2]*normal[1];ext=b/2*(abs(co*normal[0]+si*normal[1])+abs(-si*normal[0]+co*normal[1]));proj=h@normal;gap=np.maximum(gap,np.maximum(cen-ext-proj.max(),proj.min()-cen-ext))
  for nx,ny in ((co,si),(-si,co)):
   cen=P[:,1]*nx+P[:,2]*ny;proj=h[:,0,None]*nx[None,:]+h[:,1,None]*ny[None,:];gap=np.maximum(gap,np.maximum(cen-b/2-proj.max(axis=0),proj.min(axis=0)-cen-b/2))
  bits[gap<-1e-10]|=1<<owner
 inds=[]
 for owner in mask:
  candidates=np.flatnonzero(legal & MEM[:,owner] & ((bits&(maskbits^(1<<owner)))==0))
  if generic:
   good=np.zeros(len(candidates),bool);angles=np.tan(P[candidates,0]/2);centers=P[candidates,1:]
   for rr in source['final_state']['cells'][str(owner)]:
    angle_lo,angle_hi=map(lambda x:float(F(x)),rr['interval']);which=np.flatnonzero((angles>=angle_lo-1e-13)&(angles<=angle_hi+1e-13))
    if not len(which) or not rr['outer_domain']:continue
    V=np.array([[float(F(x)) for x in p] for p in rr['outer_domain']]);E=np.roll(V,-1,axis=0)-V;N=np.column_stack((E[:,1],-E[:,0]));H=(N*V).sum(1);ok=np.all(centers[which]@N.T<=H+1e-10,axis=1);good[which[ok]]=True
   candidates=candidates[good]
   # The independently proved own hull is contained strictly in the parent.
   V=np.array([[float(F(x)) for x in p] for p in groups[owner]]);e=np.column_stack((co[candidates],si[candidates]));f=np.column_stack((-si[candidates],co[candidates]));z=P[candidates,1:];ok=np.ones(len(candidates),bool)
   for axes in (e,f):
    projection=V@axes.T-(z*axes).sum(1)[None,:];ok&=np.max(abs(projection),axis=0)<=float(B)/2+1e-10
   candidates=candidates[ok]
  assert len(candidates),'No retained finite row for occupied cell'
  inds.append(candidates)
 print('retained pose-domain counts',list(map(len,inds)),flush=True)
 row=np.concatenate(inds);cell=np.concatenate([np.full(len(x),i,int) for i,x in enumerate(inds)]);n=R.shape[1];rng=np.random.default_rng(1383)
 signatures=np.column_stack([cell.astype(np.uint8),R[row]]).astype(np.uint8);raw=np.ascontiguousarray(signatures).view(np.dtype((np.void,signatures.shape[1]))).ravel();_,unique=np.unique(raw,return_index=True);row=row[unique];cell=cell[unique];print('distinct retained cell profiles',len(row),flush=True)
 active=np.arange(len(row));last=sparse.csr_matrix(np.r_[np.zeros(n),-np.ones(11)][None,:])
 for it in range(35):
  A=sparse.hstack([-sparse.csr_matrix(R[row[active]].astype(float)),sparse.csr_matrix((np.ones(len(active)),(np.arange(len(active)),cell[active])),shape=(len(active),11))],format='csr');A=sparse.vstack([A,last],format='csr')
  with warnings.catch_warnings():
   warnings.simplefilter('ignore');res=linprog(np.r_[sc.COST,np.zeros(11)],A_ub=A,b_ub=np.r_[np.zeros(len(active)),-11],bounds=(0,None),method='highs-ds',options={'threads':1,'time_limit':40})
  assert res.success
  w=np.maximum(res.x[:n],0);pos=np.flatnonzero(w>1e-10);q=R[:,pos].astype(float)@w[pos];deficit=res.x[n:][cell]-q[row];bad=np.flatnonzero(deficit>1e-8);print(it,len(active),res.fun,len(bad),flush=True)
  if not len(bad):break
  add=[]
  for j in range(11):
   bbad=bad[cell[bad]==j]
   if len(bbad):add.extend(bbad[np.argsort(deficit[bbad])[-70:]]);add.extend(rng.choice(bbad,min(30,len(bbad)),replace=False))
  active=np.unique(np.r_[active,add])
 gamma=np.array([q[rr].min() for rr in inds]);factor=11/gamma.sum();w*=factor;gamma*=factor;np.savez_compressed(a.output,weights=w,gamma=gamma,mask=mask,capacity=sc.COST);print(json.dumps(dict(status='FINITE_ONLY',budget=float(sc.COST@w),features=int(np.sum(w>1e-10)),counts=list(map(len,inds)),extras=list(map(str,extras)))),flush=True)
if __name__=='__main__':main()
