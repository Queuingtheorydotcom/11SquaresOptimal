#!/usr/bin/env python3
"""Mine separate square-specific captured-rule columns; immutable source input.

Numerical filters only propose conflicts; every accepted conflict is rationally
checked. No claim of completeness is made for near-zero filtered margins.
TRUE-majority is not retained in these alternative finite captured rules.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
from hashlib import sha256
from collections import Counter
import argparse,json,math,sys,time
import numpy as np
from square_variance_support import moment,disk_witness,require

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/exact_checker'))
from charge_geometry import convex_hull,hulls_intersect


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--A',type=F,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--orientation-polygon',action='store_true',help='Use the stronger exact arbitrary-rotation square-fit test')
    args=parser.parse_args();started=time.monotonic();raw=args.source.read_bytes();c=json.loads(raw)
    D=c['coordinate_denominator'];LD=int(F(c['L'])*D);A=args.A;points=[]
    for x,y,w in c['point_orbits']:
        points.extend(sorted({(a,b) for u,v in ((x,y),(y,x)) for a in (u,LD-u) for b in (v,LD-v)}))
    require(len(points)==len(set(points)),'Duplicate physical sites')
    found=[];counts=Counter();groups_scanned=0
    for orbit,atom in enumerate(c['charge_orbits']):
        inds=atom['sets'][0];n=len(inds);k=atom['threshold']
        if n not in (5,7) or n!=2*k-1:continue
        groups_scanned+=1;ps=[points[i] for i in inds]
        rational=[tuple(F(x,D) for x in p) for p in ps];numeric=np.array(ps,float)/D
        thresholds=list(combinations(range(n),k));cache={};ball_cache={};hull_cache={};impossible_cache={};variance_cache={}
        def balls(subset):
            if subset in ball_cache:return ball_cache[subset]
            out=[]
            for size in range(2,len(subset)+1):
                for sub in combinations(subset,size):
                    q=numeric[list(sub)];mean=q.mean(axis=0)
                    rad2=float(A*A/2)-np.mean(np.sum((q-mean)**2,axis=1))
                    if rad2>=0:out.append((mean,math.sqrt(rad2),sub))
            ball_cache[subset]=out;return out
        def impossible(subset):
            if subset in impossible_cache:return impossible_cache[subset]
            for size in range(2,len(subset)+1):
                for sub in combinations(subset,size):
                    if sub not in variance_cache:variance_cache[sub]=moment([rational[i] for i in sub])[1]
                    if variance_cache[sub]>A*A/2:
                        impossible_cache[subset]={'kind':'impossible_threshold','subset':list(sub)}
                        return impossible_cache[subset]
            if args.orientation_polygon:
                from square_fit_polygon import fit_certificate
                certificate=fit_certificate([rational[i] for i in subset],A)
                if not certificate['fits']:
                    impossible_cache[subset]={'kind':'orientation_polygon','subset':list(subset),'certificate':certificate}
                    return impossible_cache[subset]
            impossible_cache[subset]=None
            return None
        def hull(subset):
            if subset not in hull_cache:hull_cache[subset]=convex_hull([ps[i] for i in subset])
            return hull_cache[subset]
        def conflict(first,second):
            if set(first)&set(second):return {'kind':'shared_site'}
            key=(first,second)
            if key in cache:return cache[key]
            if hulls_intersect(hull(first),hull(second)):
                cache[key]={'kind':'hull_intersection'};return cache[key]
            bad=impossible(second)
            if bad is not None:
                cache[key]=bad;return cache[key]
            proposals=[]
            for x,r,ii in balls(first):
                for y,s,jj in balls(second):
                    margin=float(A)-float(np.linalg.norm(x-y))-r-s
                    if margin>1e-12:proposals.append((margin,ii,jj))
            for margin,ii,jj in sorted(proposals,reverse=True):
                proof=disk_witness([rational[i] for i in ii],[rational[i] for i in jj],A)
                if proof is not None:
                    cache[key]=dict(proof,first_local_subset=list(ii),second_local_subset=list(jj))
                    return cache[key]
            cache[key]=None;return None
        for size in range(2,k):
            for pattern in combinations(range(n),size):
                if impossible(pattern) is not None:continue
                extra=[];valid=True;novel=False
                for threshold in thresholds:
                    proof=conflict(pattern,threshold)
                    if proof is None:valid=False;break
                    if proof['kind'] not in ('shared_site','hull_intersection'):
                        novel=True;extra.append(dict(threshold_local=list(threshold),proof=proof))
                if valid and novel:
                    found.append(dict(orbit=orbit,sites=list(inds),pattern_local=list(pattern),
                                      pattern_global=[inds[i] for i in pattern],proofs=extra,
                                      rule='captured_count>=threshold OR capture_this_pattern'))
                    counts[n,size]+=1
        if groups_scanned%500==0:print('Scanned',groups_scanned,'groups; candidates',len(found),flush=True)
    result=dict(status='EXACT_ACCEPTED_SQUARE_SPECIFIC_CAPTURED_RULE_CANDIDATES',
                source=str(args.source),source_sha256=sha256(raw).hexdigest(),maximum_core_side=str(A),
                groups_scanned=groups_scanned,candidate_rules=len(found),
                orientation_polygon_test=args.orientation_polygon,
                candidate_counts={str(k):v for k,v in counts.items()},rules=found,
                seconds=time.monotonic()-started,
                scope='Each accepted rule has a separate budget1 on disjoint closed square cores with arbitrary sides≤A. No TRUE-majority OR upgrade, no mutual compatibility claim across new patterns, no LP benefit or packing bound; numerical filters may miss near-zero-margin candidates.')
    args.output.write_text(json.dumps(result,default=lambda x:str(x) if isinstance(x,F) else x,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rules'},indent=2))


if __name__=='__main__':main()
