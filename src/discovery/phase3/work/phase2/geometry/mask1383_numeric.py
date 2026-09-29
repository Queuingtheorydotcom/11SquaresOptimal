"""Nonrigorous fixed-side feasibility diagnostic, never a packing certificate."""
from pathlib import Path
from fractions import Fraction as F
import numpy as np,json,math,time
from scipy.optimize import least_squares
H=Path(__file__).resolve().parent;d=json.load(open(H/'mask1383_dual.json'));U=387708359002281417731/1e20;B=3.82/U;mask=d['mask'];cover=json.load(open(H.parents[2]/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'));P=np.array([r['pose'] for r in d['records']]);P[:,1:]/=B
polys=[np.array([[.5+(U-1)*float(F(x)) for x in v] for v in cover['cells'][j]['vertices']]) for j in mask];constraints=[]
for j,p in enumerate(polys):
 for a,b in zip(p,np.roll(p,-1,axis=0)):
  n=np.array([b[1]-a[1],a[0]-b[0]]);n/=np.linalg.norm(n);constraints.append((j,n,a@n))
pairs=[(i,j) for i in range(11) for j in range(i)]
def residual(z):
 p=z.reshape((-1,3));a=p[:,0];co=np.cos(a);si=np.sin(a);r=(co+si)/2;v=[]
 for i,j in pairs:
  dx,dy=p[i,1:]-p[j,1:];h=(1+abs(math.cos(a[i]-a[j]))+abs(math.sin(a[i]-a[j])))/2;proj=max(abs(dx*co[i]+dy*si[i]),abs(-dx*si[i]+dy*co[i]),abs(dx*co[j]+dy*si[j]),abs(-dx*si[j]+dy*co[j]));v.append(max(0,h-proj))
 v.extend(np.maximum(0,r[:,None]-p[:,1:]).ravel());v.extend(np.maximum(0,p[:,1:]+r[:,None]-U).ravel())
 for j,n,b in constraints:v.append(max(0,p[j,1:]@n-b))
 return np.array(v)
lo=np.tile([0,.5,.5],11);hi=np.tile([math.pi/2,U-.5,U-.5],11);rng=np.random.default_rng(1383);best=None;start=time.time();records=[]
for k in range(10):
 z=P.copy()
 if k:z+=rng.normal(size=z.shape)*np.array([.15,.05,.05])
 z=np.minimum(hi,np.maximum(lo,z.ravel()));rr=least_squares(residual,z,bounds=(lo,hi),max_nfev=600,ftol=1e-11,xtol=1e-11,gtol=1e-11)
 val=max(residual(rr.x));record=dict(trial=k,cost=rr.cost,max_violation=val,nfev=rr.nfev);records.append(record);print(record,flush=True)
 if best is None or rr.cost<best.cost:best=rr
 if time.time()-start>90:break
(H/'mask1383_numeric_result.json').write_text(json.dumps(dict(status='NUMERICAL_INFEASIBILITY_DIAGNOSTIC_ONLY',mask=mask,side=U,best_cost=best.cost,max_violation=float(max(residual(best.x))),poses=best.x.reshape((-1,3)).tolist(),trials=records,global_optimality_proved=False),indent=2))
