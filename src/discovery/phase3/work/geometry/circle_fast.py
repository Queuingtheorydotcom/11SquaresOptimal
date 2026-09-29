import numpy as np
from scipy.optimize import differential_evolution, minimize
W=.7195;H=.5756
for tiles in [[1,4,5,9],[1,5,8,9]]:
 b=[]
 for t in tiles:
  r,c=divmod(t,4);b.extend([(.5+c*W,.5+(c+1)*W),(.5+r*H,.5+(r+1)*H)])
 def paird(z):
  p=z.reshape((-1,2));return np.array([np.linalg.norm(p[i]-p[j]) for i in range(4) for j in range(i)])
 best=None
 for seed in range(2):
  rr=differential_evolution(lambda z:-min(paird(z)), b, maxiter=800,popsize=15,tol=1e-8,seed=seed)
  if best is None or rr.fun<best.fun:best=rr
 print(tiles,-best.fun,best.x.reshape((-1,2)),flush=True); np.savez("work/geometry/circles_"+str(tiles[1])+".npz", x=best.x, value=-best.fun)
