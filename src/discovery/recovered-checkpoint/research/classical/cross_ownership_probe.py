"""Numerical test of saturated-corner e=5 ownership branches; no proof."""
exec(open(str(__import__('pathlib').Path(__file__).with_name('cross_probe.py'))).read().split('rng=np.random')[0])
from itertools import product
q=a/(2+np.sqrt(2)/2);v=np.array([q,a-q,S-a+q,S-q]);sites=np.array([(x,y) for y in v for x in v]);rng=np.random.default_rng(617)
# index (x,y)->x+4y; masks bottom,bottom,top,left,right.
choices=[(0,0),(0,1),(1,1)] # side captures outer(0)/inner(1) lower-TL; top captures low(0)/high(1)
results=[]
for (lc,tl),(rc,tr) in product(choices,repeat=2):
 owned=[[1,2],[5,6],[1+4*(2+tl),2+4*(2+tr)], [4, (lc)+8], [7,(3-rc)+8]]
 # here left BLowner is(0,1)=4; rightBRowner(3,1)=7
 # ifleft lc=1owns(1,2), topmusthigh; analogousright
 def cost(z):
  p,c,s=poses(z);g=np.minimum(gaps(z),0);err=g@g
  for i in range(5):
   delta=sites-p[i];proj=np.maximum(np.abs(delta[:,0]*c[i]+delta[:,1]*s[i]),np.abs(delta[:,1]*c[i]-delta[:,0]*s[i]));req=np.zeros(16,dtype=bool);req[owned[i]]=True
   loss=np.where(req,np.maximum(proj-.5,0),np.maximum(.5-proj,0));err+=loss@loss
  return err
 best=1e9;bestz=None;start=time.monotonic()
 for k in range(80):
  r=minimize(cost,rng.random(15),method='L-BFGS-B',bounds=[(0,1)]*15,options={'ftol':1e-15,'gtol':1e-8,'maxiter':700})
  if r.fun<best:best=r.fun;bestz=r.x
  if best<1e-18:break
 p,c,s=poses(bestz);result={'choices':[lc,tl,rc,tr],'objective':best,'owned_sites':owned,'centers':p.tolist(),'angles':np.arctan2(s,c).tolist(),'parameters':bestz.tolist(),'starts':k+1,'seconds':time.monotonic()-start};results.append(result);print(result['choices'],best,k+1,round(result['seconds'],3),flush=True);Path(__file__).with_name('cross-ownership-probe.json').write_text(json.dumps({'status':'NUMERICAL_ONLY','branches':results},indent=2)+'\n')
