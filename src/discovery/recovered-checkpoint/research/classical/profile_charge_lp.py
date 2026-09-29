#!/usr/bin/env python3
"""Finite LP bridge from corner occupancy classes to scalar certificate weights.

Separate nonnegative guaranteed charges gamma_single, gamma_double, gamma_all
are allowed. Every known occupancy profile must have total guaranteed charge
at least eleven. No continuum coverage or new packing bound is asserted.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse
import hashlib
import json
import time
import warnings
import numpy as np
from scipy import sparse
from scipy.optimize import linprog, OptimizeWarning

ROOT=Path(__file__).resolve().parents[2]


def budget_coefficients(c):
    LD=int(F(c['L'])*c['coordinate_denominator'])
    budget=[]
    for x,y,w in c['point_orbits']:
        budget.append(len({(a,b) for u,v in ((x,y),(y,x))
                           for a in (u,LD-u) for b in (v,LD-v)}))
    for g in c['charge_orbits']:
        kind=g.get('kind','threshold')
        b=1 if kind in ('majority_hull','edge_or','convex_clique') else len(g['sets'][0])//g['threshold']
        budget.append(len(g['sets'])*b)
    return np.array(budget,float)


def classify(poses,A,L,a=2.707106):
    extent=A*(np.abs(np.cos(poses[:,0]))+np.abs(np.sin(poses[:,0])))/2
    window=A*a;x,y=poses[:,1],poses[:,2]
    flags=np.c_[x+extent<=window,x-extent>=L-window,
                y+extent<=window,y-extent>=L-window]
    counts=(flags[:,0].astype(int)+flags[:,1])*(flags[:,2].astype(int)+flags[:,3])
    if not np.isin(counts,[1,2,4]).all():raise ValueError('A sample belongs to no corner window')
    residuals=np.c_[x+extent-window,x-extent-(L-window),y+extent-window,y-extent-(L-window)]
    if np.any(np.min(np.abs(residuals),axis=1)<1e-9):
        raise ValueError('Numerically ambiguous window membership requires extra class constraints')
    if np.any((x<extent-1e-8)|(x>L-extent+1e-8)|(y<extent-1e-8)|(y>L-extent+1e-8)):
        raise ValueError('Numerical pool contains invalid full-parent centers')
    return np.array([{1:0,2:1,4:2}[int(n)] for n in counts],np.int32)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pool',type=Path,required=True)
    parser.add_argument('--certificate',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--iterations',type=int,default=30)
    parser.add_argument('--profile',help='Optional single aggregate count s,d,c; a conditional case only')
    parser.add_argument('--restrict-columns',action='store_true',help='After one exploratory solve, keep its positive columns plus baseline columns and solve the full pool once; candidate only')
    args=parser.parse_args();start=time.monotonic()
    d=np.load(args.pool);rows=d['rows'];poses=d['placements'];oldweights=d['weights'];oldbudget=float(d['budget'])
    c=json.loads(args.certificate.read_text());B=budget_coefficients(c)
    if rows.shape[1]!=len(B):raise ValueError('Column mismatch')
    types=classify(poses,float(d['A']),float(F(c['L'])))
    profiles=json.loads((ROOT/'research/structure/corner-profiles.json').read_text())['all_profiles']
    aggregated=np.array(sorted({(sum(p[:4]),sum(p[4:8]),p[8]) for p in profiles}),float)
    if args.profile:
        selected=tuple(map(int,args.profile.split(',')))
        if selected not in set(map(tuple,aggregated.astype(int))):raise ValueError('Unknown aggregate profile')
        aggregated=np.array([selected],float)
    profile_matrix=sparse.hstack([sparse.csr_matrix((len(aggregated),len(B))),-sparse.csr_matrix(aggregated)],format='csr')
    active=set(np.flatnonzero(np.abs(d['duals'])>1e-10).tolist()) if args.profile else set(map(int,d['active']))
    if not active:active.update(range(min(3000,len(rows))))
    history=[];weights=None;gammas=None;complete=False
    restricted_columns=None
    for iteration in range(args.iterations):
        if args.restrict_columns and iteration==1:
            restricted_columns=np.flatnonzero((weights>1e-11)|(oldweights>1e-11))
            active=set(range(len(rows)))
        ii=np.array(sorted(active),int)
        columns=np.arange(len(B)) if restricted_columns is None else restricted_columns
        matrix=sparse.csr_matrix(rows[np.ix_(ii,columns)],dtype=float)
        gamma_columns=sparse.coo_matrix((np.ones(len(ii)),(np.arange(len(ii)),types[ii])),shape=(len(ii),3)).tocsr()
        current_profiles=sparse.hstack([sparse.csr_matrix((len(aggregated),len(columns))),-sparse.csr_matrix(aggregated)],format='csr')
        constraints=sparse.vstack([sparse.hstack([-matrix,gamma_columns],format='csr'),current_profiles],format='csr')
        rhs=np.r_[np.zeros(len(ii)),-np.full(len(aggregated),11.)]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',OptimizeWarning)
            res=linprog(np.r_[B[columns],np.zeros(3)],A_ub=constraints,b_ub=rhs,bounds=(0,None),
                        method='highs-ds',options={'threads':1,'dual_feasibility_tolerance':1e-8,
                                                 'primal_feasibility_tolerance':1e-8})
        if not res.success:raise RuntimeError(res.message)
        weights=np.zeros(len(B));weights[columns]=res.x[:-3];gammas=res.x[-3:]
        values=rows@weights-gammas[types];bad=np.flatnonzero(values < -1e-8)
        event={'iteration':iteration,'constraints':len(ii),'bad_pool_rows':len(bad),
               'budget':float(B@weights),'gammas':gammas.tolist(),'worst_residual':float(min(values)),
               'elapsed':time.monotonic()-start}
        history.append(event);print(json.dumps(event),flush=True)
        if not len(bad):complete=True;break
        if iteration==0:
            active=set(ii[np.abs(res.ineqlin.marginals[:len(ii)])>1e-10].tolist())
        active.update(bad[np.argsort(values[bad])[:2500]].tolist())
    result={'status':'FINITE_POOL_CLASS_CHARGE_LP_COMPLETE' if complete else 'INCOMPLETE_FINITE_POOL_LP',
            'pool_path':str(args.pool),'certificate_path':str(args.certificate),
            'pool_sha256':hashlib.sha256(args.pool.read_bytes()).hexdigest(),
            'pool_rows':len(rows),'variables':len(B),'class_counts':np.bincount(types,minlength=3).tolist(),
            'aggregate_profiles':aggregated.astype(int).tolist(),
            'all_single_profile_present':(11,0,0) in set(map(tuple,aggregated.astype(int))),
            'baseline_budget_recorded':oldbudget,'baseline_budget_recomputed':float(B@oldweights),
            'class_charge_budget':float(B@weights),'numerical_budget_gain':oldbudget-float(B@weights),
            'restricted_column_count':None if restricted_columns is None else len(restricted_columns),
            'gammas_single_double_all':gammas.tolist(),
            'minimum_profile_total':float(min(aggregated@gammas)),
            'history':history,'seconds':time.monotonic()-start,
            'scope':'Numerical finite-pool optimization with verified occupancy-count premises; optional individual profile restricts the conclusion to that count case. No continuum class pricing, exact coverage, or new packing bound.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    np.savez_compressed(args.output.with_suffix('.npz'),weights=weights,gammas=gammas,
                        types=types,aggregate_profiles=aggregated,active=np.array(sorted(active)),
                        budget=B@weights)
    print(json.dumps({k:v for k,v in result.items() if k!='history'},indent=2),flush=True)


if __name__=='__main__':main()
