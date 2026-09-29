"""Discover wall-aware mandatory sites; exact validation is separate."""
from fractions import Fraction as F
from pathlib import Path
import numpy as np,json,math
ROOT=Path('/workspace/scratch/6def36ddf53b/current')
COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
U=F(387708359002281417731,10**20);B=F(191,50)/U
cover=json.loads(COVER.read_text())
polys=[np.array([[.5+(float(U)-1)*float(F(x)) for x in p] for p in c['vertices']]) for c in cover['cells']]
gens=[np.array([.5+(float(U)-1)*float(F(x)) for x in c['center']]) for c in cover['cells']]
def clip(poly,n,b):
 if not len(poly):return poly
 out=[]
 for p,q in zip(poly,np.roll(poly,-1,axis=0)):
  a=p@n-b;z=q@n-b;ina=a<=0;inz=z<=0
  if ina:out.append(p)
  if ina!=inz:out.append(p+a/(a-z)*(q-p))
 return np.array(out).reshape((-1,2))
def kernel(poly,n=1000):
 k=np.array([[0,0],[float(U),0],[float(U),float(U)],[0,float(U)]])
 for t in np.linspace(0,1,n+1):
  c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);r=(c+s)/2; p=poly.copy()
  for nn,b in [(np.array([1,0]),float(U)-r),(np.array([-1,0]),-r),(np.array([0,1]),float(U)-r),(np.array([0,-1]),-r)]:p=clip(p,nn,b)
  if not len(p):continue
  for nn in [np.array([c,s]),np.array([-c,-s]),np.array([-s,c]),np.array([s,-c])]:k=clip(k,nn,.5+min(p@nn))
 return k
def witness():
 path=ROOT/'research/optimality/deficit_geometry/physical_features/mask2141-owned1-exact-gate.json'
 d=json.loads(path.read_text());r=[r for r in d['records'] if 'parent_witness' in r][-1];w=r['parent_witness'];q=np.array([float(F(x)/B) for x in w['center']]);t=float(F(w['half_angle']));c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
 return d,r,q,[np.array([c,s]),np.array([-s,c])]
if __name__=='__main__':
 d,r,q,ns=witness();out=[]
 for i,p in enumerate(polys):
  k=kernel(p);kw=k.copy()
  for n in ns:
   for sign in [-1,1]:kw=clip(kw,sign*n,.5+q@(sign*n))
  print(i,'kernelvertices',len(k),'hit',bool(len(kw)), 'bounds',np.min(k,axis=0),np.max(k,axis=0),flush=True)
  out.append(dict(cell=i,polygon=k.tolist(),witness_intersection=kw.tolist(),occupied_other=i in d['mask'] and i!=r['cell']))
 Path('work/geometry/wall_kernel_discovery.json').write_text(json.dumps(out,indent=2))
