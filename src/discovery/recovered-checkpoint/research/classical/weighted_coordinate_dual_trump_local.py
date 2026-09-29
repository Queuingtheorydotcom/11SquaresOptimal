#!/usr/bin/env python3
"""Exact curvature-weighted acceptance of proposed nonnegative coordinate duals.

The LP only proposes42 rational coefficients. Exact entry enclosures certify
every signed coordinate functional and its residual. No LP optimum is used.
"""
if not __debug__:
    raise SystemExit('Assertions must remain enabled; remove -O/-OO.')

from fractions import Fraction as F
from pathlib import Path
from hashlib import sha256
from math import ceil, isqrt
import argparse
import json
import time
import warnings
import numpy as np
from scipy.optimize import linprog,OptimizeWarning
from replay_trump_local import SOURCE,need,enclose
from cases.trump11 import isolation_radius as ir
from cases.trump11 import tangent_cones as tc


def encode(value):
    if isinstance(value,F):return str(value)
    raise TypeError(type(value).__name__)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--branches',type=int,nargs='+')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();started=time.monotonic();here=Path(__file__).parent
    source_path=here/'trump-local-conservative-radius.json';old=json.loads(source_path.read_text())
    need(old['status']=='PASS_EXACT_CONSERVATIVE_LOCAL_RADIUS','Bad source receipt')
    for path,fingerprint in old['source_hashes'].items():
        need(sha256((SOURCE/path).read_bytes()).hexdigest()==fingerprint,'Changed source '+path)
    witness=ir.load_witness();lo,hi=map(F,old['root_interval']);cached={}
    def bounds(value):
        key=tuple(value.coeffs)
        if key not in cached:cached[key]=enclose(key,lo,hi)
        return cached[key]
    # Each unavailable separating feature needs only one strictly negative corner.
    root2=F(14143,10000);inverse_root2=F(7072,10000);box=F(old['box_radius'])
    need(root2*root2>2 and 2*inverse_root2*inverse_root2>1,'Invalid square-root upper bounds')
    pair_curvatures={}
    for first in range(11):
        for second in range(first+1,11):
            dx=witness.centres[second][0]-witness.centres[first][0]
            dy=witness.centres[second][1]-witness.centres[first][1]
            squared=bounds(dx*dx+dy*dy)[1];den=10**9
            integer=(squared.numerator*den*den+squared.denominator-1)//squared.denominator
            root=isqrt(integer)
            if root*root<integer:root+=1
            distance=F(root,den);need(distance*distance>=squared,'Invalid center distance upper bound')
            pair_curvatures[first,second]=distance+2*root2*box+6*root2
    functions=ir.elementary_functions(witness,box);curvatures={};lipschitz={};row_curvatures={}
    for function in functions:
        K=inverse_root2 if function.kind=='wall' else pair_curvatures[function.subject[:2]]
        gradient_upper=sum(max(abs(a),abs(b)) for a,b in map(bounds,function.gradient))
        curvatures[function.label]=K;lipschitz[function.label]=gradient_upper+K*box
        if function.value.is_zero():
            key=ir.gradient_key(function.gradient)
            row_curvatures[key]=max(row_curvatures.get(key,F(0)),K)
    groups={};contact_pairs={c.pair for c in witness.contacts}
    for function in functions:
        if function.kind=='pair' and function.subject[:2] in contact_pairs:
            groups.setdefault(function.subject[:5],[]).append(function)
    gap_proofs=[];active=0
    for key,functions in sorted(groups.items()):
        negative=[]
        for function in functions:
            if function.value.is_zero():continue
            a,b=bounds(function.value);need(a>0 or b<0,'Unseparated elementary value')
            if b<0:negative.append((-b/lipschitz[function.label],-b,function.subject[-1],lipschitz[function.label]))
        if not negative:
            need(any(f.value.is_zero() for f in functions),'Contact has strictly positive gap')
            active+=1;continue
        cap,lower,corner,L=max(negative)
        gap_proofs.append(dict(feature=list(key),negative_corner=corner,negative_gap_lower=lower,
                               lipschitz_upper=L,radius_lower=cap))
    need(active==24 and len(gap_proofs)==88,'Incomplete separating-feature inventory')
    gap_radius=min(g['radius_lower'] for g in gap_proofs)
    selected=list(range(128)) if args.branches is None else sorted(set(args.branches))
    need(selected and all(0<=i<128 for i in selected),'Invalid selected branches')
    D=10**12;DB=10**12;output=[];kappa=None
    for index in selected:
        branch=witness.branches[index];rows=branch['rows'];AN=[]
        for row in rows:
            approximate=[]
            for value in row.coefficients:
                a,b=bounds(value);q=round((a+b)*DB/2)
                need(F(q-1,DB)<=a<=b<=F(q+1,DB),'Entry enclosure failed')
                approximate.append(q)
            AN.append(approximate)
        Krows=[row_curvatures[tc.row_key(row)] for row in rows]
        exact=np.array(AN,dtype=object);numeric=np.array(AN,dtype=float)/DB;certificates=[];local=None
        for j in range(33):
            for sign in (-1,1):
                target=np.zeros(33);target[j]=sign
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore',OptimizeWarning)
                    result=linprog(np.array(list(map(float,Krows))),A_eq=numeric.T,b_eq=target,bounds=(0,None),
                                   method='highs-ds',options={'threads':1})
                need(result.success and np.isfinite(result.x).all(),'LP proposal failed')
                coefficients=np.array([int(ceil(max(float(v),0)*D)) for v in result.x],dtype=object)
                need(all(v>=0 for v in coefficients),'Negative rounded dual')
                residual=coefficients@exact;residual[j]-=sign*D*DB
                mass=F(int(sum(coefficients)),D);need(mass>0,'Zero combination')
                error=F(int(sum(abs(v) for v in residual)),D*DB)+mass*F(33,DB)
                need(error<1,'Coordinate residual is too large')
                curvature_mass=sum(K*int(v) for K,v in zip(Krows,coefficients))/D
                need(curvature_mass>0,'Nonpositive curvature-weighted mass')
                bound=2*(1-error)/curvature_mass
                local=bound if local is None else min(local,bound)
                certificates.append(dict(coordinate=j,sign=sign,coefficients=coefficients.tolist(),
                                         mass=mass,curvature_mass=curvature_mass,residual_upper=error,radius_lower=bound))
        kappa=local if kappa is None else min(kappa,local)
        output.append(dict(branch=index,weighted_radius_lower=local,row_curvature_upper=Krows,certificates=certificates))
        print(f'Coordinate duals: branch{index}, weighted_radius≥{float(local):.12g}, seconds{time.monotonic()-started:.2f}',flush=True)
    radius=min(F(old['box_radius']),gap_radius,kappa)
    short=F((radius*10**15).__floor__(),10**15)
    closed=F(1,radius.denominator//radius.numerator+1)
    need(0<closed<radius,'Closed radius is not strictly conservative')
    full=selected==list(range(128))
    result=dict(status='PASS_FULL_EXACT_WEIGHTED_COORDINATE_RADIUS' if full else 'PASS_SELECTED_WEIGHTED_COORDINATE_DUALS_ONLY',
                radius_open=short if full else None,radius_closed=closed if full else None,
                proposed_radius_if_remaining_branches_pass=short,radius_decimal=float(short),
                weighted_radius_lower=kappa,branches=output,coefficient_denominator=D,
                matrix_approximation_denominator=DB,signed_coordinate_certificates=len(output)*66,
                unavailable_feature_proofs=gap_proofs,active_features=active,
                branch_stability_radius_lower=gap_radius,sqrt2_upper=root2,inverse_sqrt2_upper=inverse_root2,
                box_radius=box,
                input_sha256=sha256(source_path.read_bytes()).hexdigest(),input_path=str(source_path),
                checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                rational_helper_sha256=sha256(Path(__file__).with_name('replay_trump_local.py').read_bytes()).hexdigest(),
                scope='Exact curvature-weighted nonnegative coordinate combinations and per-feature gradient stability bounds; local labelled fixed-side claim only.',
                seconds=time.monotonic()-started)
    destination=args.output or here/'trump-local-weighted-coordinate-radius.json'
    destination.write_text(json.dumps(result,default=encode,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('branches','unavailable_feature_proofs')},default=encode,indent=2))


if __name__=='__main__':main()
