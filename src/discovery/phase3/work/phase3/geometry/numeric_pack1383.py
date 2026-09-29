"""Numerical diagnostic only: seek residual-mask packing, no proof claims."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import json,math,time
import numpy as np
from scipy.optimize import least_squares
from threadpoolctl import threadpool_limits
threadpool_limits(limits=1)
H=Path(__file__).resolve().parent

def main():
 start=time.monotonic();d=json.loads((H/'mask1383_collision_propagation_r3.json').read_text());s=d['final_state'];B=float(__import__('fractions').Fraction(s['B']));U=float(__import__('fractions').Fraction(s['U']));mask=d['mask'];rng=np.random.default_rng(1383);i,j=np.triu_indices(11,1);world=[];live=[];bounds=[]
 for owner in mask:
  P=np.array([[float(__import__('fractions').Fraction(x))/B for x in p] for p in s['world'][owner]]);D=np.roll(P,-1,axis=0)-P;n=np.column_stack((D[:,1],-D[:,0]));n/=np.linalg.norm(n,axis=1)[:,None];world.append((n,(n*P).sum(1)))
  rows=[r for r in s['cells'][str(owner)] if r['residual_polygons']];live.append(rows);vv=np.array([[float(__import__('fractions').Fraction(x))/B for x in p] for r in rows for q in r['residual_polygons'] for p in q]);bounds.append((vv.min(0),vv.max(0)))
 lower=np.concatenate([[0,b[0][0],b[0][1]] for b in bounds]);upper=np.concatenate([[math.pi/2,b[1][0],b[1][1]] for b in bounds]);tiny=1e-12;lower=np.minimum(lower,upper-tiny)
 def residual(flat,report=False):
  P=flat.reshape(11,3);theta=P[:,0];z=P[:,1:];co=np.cos(theta);si=np.sin(theta);e=np.column_stack((co,si));f=np.column_stack((-si,co));delta=z[j]-z[i];axes=np.stack((e[i],f[i],e[j],f[j]),axis=1);dist=np.abs((axes*delta[:,None,:]).sum(2));rad=.5*(np.abs((axes*e[i,None,:]).sum(2))+np.abs((axes*f[i,None,:]).sum(2))+np.abs((axes*e[j,None,:]).sum(2))+np.abs((axes*f[j,None,:]).sum(2)));gaps=(dist-rad).max(1);ext=(co+si)/2;walls=np.column_stack((ext-z[:,0],ext-z[:,1],z[:,0]+ext-U,z[:,1]+ext-U));cell=np.concatenate([np.maximum(0,n@z[k]-h) for k,(n,h) in enumerate(world)]);ans=np.r_[np.maximum(0,-gaps),np.maximum(0,walls).ravel(),cell]
  if report:return ans,gaps
  return ans
 records=[];best=None
 for trial in range(24):
  P=[]
  for rows in live:
   r=rows[rng.integers(len(rows))];a,b=map(lambda x:float(__import__('fractions').Fraction(x)),r['interval']);t=rng.uniform(a,b);v=np.array([[float(__import__('fractions').Fraction(x))/B for x in p] for q in r['residual_polygons'] for p in q]);P.append([2*math.atan(t),*v.mean(0)])
  x=np.clip(np.array(P).ravel(),lower+tiny,upper-tiny);opt=least_squares(residual,x,bounds=(lower,upper),max_nfev=600,ftol=1e-11,xtol=1e-11,gtol=1e-11);res,gaps=residual(opt.x,True);record=dict(trial=trial,squared_error=float(res@res),maximum_violation=float(res.max()),evaluations=opt.nfev,poses=opt.x.reshape(11,3).tolist(),negative_pairs=[dict(owners=[mask[a],mask[b]],gap=float(g)) for a,b,g in zip(i,j,gaps) if g< -1e-7]);records.append(record)
  if best is None or record['squared_error']<best['squared_error']:best=record
  print(json.dumps(dict(trial=trial,objective=record['squared_error'],maximum=record['maximum_violation'],best=best['squared_error'],seconds=time.monotonic()-start)),flush=True)
  if time.monotonic()-start>90:break
 out=dict(status='NUMERICAL_DIAGNOSTIC_ONLY',mask=mask,best=best,trials=records,source='mask1383_collision_propagation_r3.json',source_sha256=__import__('hashlib').sha256((H/'mask1383_collision_propagation_r3.json').read_bytes()).hexdigest(),mask_exclusion_proved=False,seconds=time.monotonic()-start);(H/'mask1383_numeric_packing_diagnostic.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
