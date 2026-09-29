#!/usr/bin/env python3
"""Bounded numerical discovery only for fullyD4 sixteen-cell covers."""
from pathlib import Path
import numpy as np,json,time
from scipy.optimize import differential_evolution,minimize
from propose_cover import vertices
OUT=Path(__file__).resolve().parent

def sites(params,kind):
    a,b,c,d=params
    points=[]
    for x,y in ((a,b),(b,a)):
        points.extend([(x,y),(1-x,y),(x,1-y),(1-x,1-y)])
    points.extend([(c,c),(1-c,c),(c,1-c),(1-c,1-c)])
    if kind=='two_diagonal':points.extend([(d,d),(1-d,d),(d,1-d),(1-d,1-d)])
    else:points.extend([(.5,d),(d,.5),(.5,1-d),(1-d,.5)])
    return np.asarray(points)

def objective(params,kind):
    p=sites(params,kind)
    if len(np.unique(p.round(10),axis=0))<16:return 1.
    try:v,_=vertices(p)
    except Exception:return 1.
    ds=np.sum((v[:,None,:]-p[None,:,:])**2,axis=2); nearest=ds.min(axis=1)
    diameter=0.
    for i in range(16):
        vv=v[ds[:,i]<nearest+1e-9]
        if len(vv)<3:return 1.
        dd=np.sum((vv[:,None,:]-vv[None,:,:])**2,axis=2)
        diameter=max(diameter,float(dd.max()))
    return diameter

def main():
    started=time.time();best=1.;record=[]
    for kind in ('two_diagonal','axis_diagonal'):
        if time.time()-started>108:break
        bounds=[(.025,.32),(.16,.485),(.025,.27),(.26,.485)] if kind=='two_diagonal' else [(.025,.35),(.14,.485),(.03,.45),(.025,.485)]
        callback=lambda x,convergence:time.time()-started>108
        result=differential_evolution(objective,bounds,args=(kind,),maxiter=95,popsize=12,tol=1e-8,polish=False,seed=893,callback=callback,workers=1,updating='immediate')
        if time.time()-started<108:
            local=minimize(objective,result.x,args=(kind,),method='Nelder-Mead',options={'maxiter':800,'xatol':1e-10,'fatol':1e-10})
            if local.fun<result.fun:result=local
        row={'family':kind,'parameters':result.x.tolist(),'max_diameter_squared':float(result.fun),'max_diameter':float(np.sqrt(result.fun)),'physical_diameter':float(np.sqrt(result.fun)*2.877084),'centers':sites(result.x,kind).tolist(),'seconds':time.time()-started,'status':'NUMERICAL_PROPOSAL_ONLY'}
        record.append(row);print(json.dumps({k:v for k,v in row.items() if k!='centers'}),flush=True)
        if result.fun<best:
            best=result.fun;(OUT/'d4-cover-proposal.json').write_text(json.dumps(row,indent=2)+'\n')
    (OUT/'d4-cover-discovery.json').write_text(json.dumps({'status':'BOUNDED_DISCOVERY_ONLY','runs':record,'seconds':time.time()-started},indent=2)+'\n')
if __name__=='__main__':main()
