#!/usr/bin/env python3
"""Bounded numerical10-circle cover proposal for noncorner center cells.

Only discovery; a successful sampled objective still needs exact continuum replay.
"""
from pathlib import Path
import numpy as np,json,time
from scipy.optimize import minimize
from scipy.cluster.vq import kmeans2
HERE=Path(__file__).resolve().parent

def main():
    start=time.time();p=json.loads((HERE/'center-cover-symmetric-exact.json').read_text())
    sites=np.array([[float(__import__('fractions').Fraction(x)) for x in r['center']] for r in p['cells']])
    grid=np.array([(i/55,j/55) for i in range(56) for j in range(56)])
    nearest=np.sum((grid[:,None,:]-sites[None,:,:])**2,axis=2).argmin(axis=1)
    data=grid[~np.isin(nearest,[0,3,12,15])]
    verts=np.array([[float(__import__('fractions').Fraction(x)) for x in v] for c in p['cells'] if c['index'] not in [0,3,12,15] for v in c['vertices']])
    data=np.vstack((data,verts));rng=np.random.default_rng(384)
    def objective(x,beta):
        centers=x.reshape(-1,2);delta=centers[None,:,:]-data[:,None,:];dist=np.sum(delta*delta,axis=2)
        labels=dist.argmin(axis=1);minimum=dist[np.arange(len(data)),labels];m=minimum.max();exp=np.exp(beta*(minimum-m));weights=exp/exp.sum()
        grad=np.zeros_like(centers);np.add.at(grad,labels,2*weights[:,None]*delta[np.arange(len(data)),labels])
        return m+np.log(exp.sum())/beta,grad.ravel()
    records=[];best=1.
    for run in range(8):
        if time.time()-start>95:break
        centers,_=kmeans2(data,10,minit='++',iter=30,rng=rng);x=centers.ravel()
        for beta in (300,1000,5000,30000,100000):
            sol=minimize(objective,x,args=(beta,),jac=True,method='L-BFGS-B',bounds=[(0,1)]*20,options={'maxiter':220,'ftol':1e-12,'gtol':1e-8});x=sol.x
        diameter=2*np.sqrt(np.sum((data[:,None,:]-x.reshape(1,10,2))**2,axis=2).min(axis=1).max())*2.877084
        row={'run':run,'sampled_physical_diameter':float(diameter),'centers':x.reshape(10,2).tolist(),'seconds':time.time()-start,'status':'SAMPLED_NUMERICAL_PROPOSAL_ONLY'}
        print(json.dumps({k:v for k,v in row.items() if k!='centers'}),flush=True);records.append(row)
        if diameter<best:best=diameter;(HERE/'corner-free-cover-proposal.json').write_text(json.dumps(row,indent=2)+'\n')
        if diameter<.997:break
    (HERE/'corner-free-cover-discovery.json').write_text(json.dumps({'status':'BOUNDED_DISCOVERY_ONLY','sample_count':len(data),'runs':records,'seconds':time.time()-start},indent=2)+'\n')
if __name__=='__main__':main()
