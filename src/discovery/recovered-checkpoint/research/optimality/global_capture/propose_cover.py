#!/usr/bin/env python3
"""Numerical proposal only: minimum enclosing nearest-center radius on unit square."""
import json, time
from pathlib import Path
import numpy as np
from scipy.spatial import Delaunay
from scipy.optimize import minimize

DEST=Path(__file__).resolve().parent
PAIR=np.asarray([(i,j) for i in range(16) for j in range(i)],dtype=int)

def vertices(x):
    p=np.asarray(x).reshape(-1,2)
    tri=Delaunay(p).simplices
    a=p[tri[:,0]]; b=p[tri[:,1]]; c=p[tri[:,2]]
    mat=2*np.stack((b-a,c-a),axis=1)
    rhs=np.stack((np.sum(b*b-a*a,axis=1),np.sum(c*c-a*a,axis=1)),axis=1)
    det=mat[:,0,0]*mat[:,1,1]-mat[:,0,1]*mat[:,1,0]
    q=np.column_stack(((rhs[:,0]*mat[:,1,1]-rhs[:,1]*mat[:,0,1])/det,(mat[:,0,0]*rhs[:,1]-mat[:,1,0]*rhs[:,0])/det))
    q=q[np.all((q>=0)&(q<=1),axis=1)]
    aa=p[PAIR[:,0]]; bb=p[PAIR[:,1]]; d=2*(bb-aa); rhs=np.sum(bb*bb-aa*aa,axis=1)
    out=[q,np.asarray([[0.,0.],[0.,1.],[1.,0.],[1.,1.]])]
    for axis in (0,1):
        for v in (0.,1.):
            good=np.abs(d[:,1-axis])>1e-12
            value=(rhs[good]-d[good,axis]*v)/d[good,1-axis]
            active=(value>=0)&(value<=1)
            qq=np.zeros((active.sum(),2)); qq[:,axis]=v; qq[:,1-axis]=value[active]
            da=np.sum((qq-aa[good][active])**2,axis=1)
            dd=np.sum((qq[:,None,:]-p[None,:,:])**2,axis=2).min(axis=1)
            out.append(qq[da<=dd+1e-10])
    pts=np.vstack(out)
    d2=np.sum((pts[:,None,:]-p[None,:,:])**2,axis=2).min(axis=1)
    return pts,d2

def objective(x,beta):
    _,v=vertices(x)
    a=v.max()
    return a+np.log(np.exp(beta*(v-a)).sum())/beta

def main():
    rng=np.random.default_rng(737)
    base=np.array([[(i+.5)/4,(j+.5)/4] for j in range(4) for i in range(4)])
    best=1.
    start=time.time()
    for run in range(16):
        x=np.clip(base+rng.normal(0,.025,size=base.shape),.025,.975).ravel()
        for beta in (300,1000,3000,10000,50000):
            sol=minimize(objective,x,args=(beta,),method='L-BFGS-B',bounds=[(.0,1.)]*32,options={'maxiter':180,'ftol':1e-12,'maxls':30,'gtol':1e-7})
            x=sol.x
        v,d2=vertices(x); radius=float(np.sqrt(d2.max()))
        print(json.dumps({'run':run,'radius':radius,'seconds':time.time()-start}),flush=True)
        if radius<best:
            best=radius
            (DEST/'cover-proposal.json').write_text(json.dumps({'status':'NUMERICAL_PROPOSAL_ONLY','radius':best,'centers':x.reshape(16,2).tolist(),'worst_vertex':v[d2.argmax()].tolist(),'run':run},indent=2)+'\n')
        if radius<.1737: break
if __name__=='__main__':main()
