#!/usr/bin/env python3
"""Bounded17-site D4 cover proposal, including the fixed center site."""
from pathlib import Path
import numpy as np,json,time,sys
from scipy.optimize import differential_evolution,minimize
import propose_cover as cover
from propose_d4_cover import sites
OUT=Path(__file__).resolve().parent
KIND='axes_diags' if '--axes-diags' in sys.argv else ('axis_diagonal' if '--axis' in sys.argv else 'two_diagonal')
cover.PAIR=np.asarray([(i,j) for i in range(17) for j in range(i)],dtype=int)

def points(params):
    if KIND!='axes_diags':return np.vstack((sites(params,KIND),[[.5,.5]]))
    a,b,c,d=params;out=[]
    for x in (a,b):out.extend([(.5,x),(x,.5),(.5,1-x),(1-x,.5)])
    for x in (c,d):out.extend([(x,x),(1-x,x),(x,1-x),(1-x,1-x)])
    return np.asarray(out+[(.5,.5)])
def objective(params):
    p=points(params)
    if len(np.unique(p.round(10),axis=0))<17:return 1.
    try:v,_=cover.vertices(p)
    except Exception:return 1.
    ds=np.sum((v[:,None,:]-p[None,:,:])**2,axis=2);nearest=ds.min(axis=1);diameter=0.
    for i in range(17):
        vv=v[ds[:,i]<nearest+1e-9]
        if len(vv)<3:return 1.
        diameter=max(diameter,float(np.sum((vv[:,None,:]-vv[None,:,:])**2,axis=2).max()))
    return diameter
if __name__=='__main__':
    started=time.time()
    sol=differential_evolution(objective,[(.025,.32),(.16,.485),(.025,.27),(.025,.485)],maxiter=180,popsize=16,tol=1e-9,seed=894,polish=False,workers=1,updating='immediate',x0=[.11,.39,.12,.34])
    local=minimize(objective,sol.x,method='Nelder-Mead',options={'maxiter':1500,'xatol':1e-11,'fatol':1e-12})
    if local.fun<sol.fun:sol=local
    out={'family':KIND+'+center','parameters':sol.x.tolist(),'max_diameter_squared':float(sol.fun),'physical_diameter':float(np.sqrt(sol.fun)*2.877084),'centers':points(sol.x).tolist(),'seconds':time.time()-started,'status':'NUMERICAL_PROPOSAL_ONLY'}
    (OUT/('d4-17-'+KIND+'-cover-proposal.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='centers'}),flush=True)
