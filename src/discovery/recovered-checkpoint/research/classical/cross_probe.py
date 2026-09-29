"""Numerical falsification search for a five-arm capacity conjecture. Not a proof."""
import numpy as np
from scipy.optimize import minimize
from pathlib import Path
import json,time
S=3.877084;a=2.707106;d=S-a
masks=[0,0,1,2,3] # bottom,bottom,top,left,right
pairs=[(i,j) for i in range(5) for j in range(i)]

def poses(z):
 th=z[:5]*np.pi/2;c=np.cos(th);s=np.sin(th);w=c+s
 arr=[]
 for i,m in enumerate(masks):
  low=np.array([d+w[i]/2,w[i]/2]);hi=np.array([a-w[i]/2,min(a-w[i]/2,d+w[i]/2)])
  p=low+(hi-low)*z[5+2*i:7+2*i]
  if m==1:p[1]=S-p[1]
  if m==2:p=p[::-1]
  if m==3:p=np.array([S-p[1],p[0]])
  arr.append(p)
 return np.array(arr),c,s

def gaps(z):
 p,c,s=poses(z);gg=[]
 for i,j in pairs:
  dx,dy=p[i]-p[j];dot=abs(c[i]*c[j]+s[i]*s[j]);cross=abs(c[i]*s[j]-s[i]*c[j]);h=(1+dot+cross)/2
  gg.append(max(abs(dx*c[i]+dy*s[i]),abs(-dx*s[i]+dy*c[i]),abs(dx*c[j]+dy*s[j]),abs(-dx*s[j]+dy*c[j]))-h)
 return np.array(gg)
def fun(z):
 g=np.minimum(gaps(z),0);return g@g
rng=np.random.default_rng(174);best=1e9;start=time.monotonic()
for k in range(200):
 r=minimize(fun,rng.random(15),method='L-BFGS-B',bounds=[(0,1)]*15,options={'ftol':1e-15,'gtol':1e-9,'maxiter':500})
 if r.fun<best:
  best=r.fun;p,c,s=poses(r.x);out={'status':'NUMERICAL_PROBE_ONLY','objective':best,'minimum_gap':float(gaps(r.x).min()),'centers':p.tolist(),'angles':np.arctan2(s,c).tolist(),'parameters':r.x.tolist(),'iteration':k,'seconds':time.monotonic()-start};Path(__file__).with_name('cross-probe.json').write_text(json.dumps(out,indent=2)+'\n');print(k,best,gaps(r.x).min(),flush=True)
 if best<1e-18:break
