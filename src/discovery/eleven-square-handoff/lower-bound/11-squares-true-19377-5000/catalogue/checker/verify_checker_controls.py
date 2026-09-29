#!/usr/bin/env python3
"""Original-kernel regression and independent exact controls for new charges.

This runs selected original rows, never relabels that sample as a full replay.
The complete adapted replay is provided by replay_parallel.py.
"""
import argparse
from fractions import Fraction as F
from hashlib import sha256
import importlib.util
import inspect
from itertools import combinations,product
import json
from pathlib import Path
import time

import exact_mixed as adapted
from integer_sweep import accumulate
from charge_geometry import (clique_coefficients,segments_intersect,convex_hull,
                             segment_hits_hull,validate_support_clique)


def require(value,message):
    if not value:raise ValueError(message)


def reject(function,*args):
    try:function(*args)
    except (ValueError,TypeError,KeyError):return
    raise ValueError('Invalid premise was accepted')


def parametric_intersection(a,b,c,d):
    """Independent rational parameter solution of two closed segments."""
    x=(b[0]-a[0],b[1]-a[1]);y=(d[0]-c[0],d[1]-c[1]);z=(c[0]-a[0],c[1]-a[1])
    determinant=x[0]*y[1]-x[1]*y[0]
    if determinant:
        t=F(z[0]*y[1]-z[1]*y[0],determinant)
        u=F(z[0]*x[1]-z[1]*x[0],determinant)
        return 0<=t<=1 and 0<=u<=1
    if x==(0,0):
        if y==(0,0):return a==c
        coordinate=0 if y[0] else 1
        u=F(a[coordinate]-c[coordinate],y[coordinate])
        return 0<=u<=1 and all(c[i]+u*y[i]==a[i] for i in range(2))
    coordinate=0 if x[0] else 1
    t=F(c[coordinate]-a[coordinate],x[coordinate])
    v=F(d[coordinate]-a[coordinate],x[coordinate])
    return (all(a[i]+t*x[i]==c[i] and a[i]+v*x[i]==d[i] for i in range(2))
            and max(min(t,v),F(0))<=min(max(t,v),F(1)))


def geometric_controls():
    grid=list(product(range(3),repeat=2));segments=list(product(grid,repeat=2));checks=0
    for a,b in segments:
        for c,d in segments:
            require(segments_intersect(a,b,c,d)==parametric_intersection(a,b,c,d),
                    'Segment predicates disagree')
            checks+=1
    triangle=convex_hull([(0,0),(4,0),(0,4)])
    hull_cases=[((1,1),(2,1),triangle,True),
                ((-1,1),(4,1),triangle,True),
                ((-1,-1),(0,0),triangle,True),
                ((-1,5),(5,5),triangle,False),
                ((1,0),(3,0),convex_hull([(0,0),(2,0),(4,0)]),True),
                ((1,1),(3,1),convex_hull([(0,0),(2,0),(4,0)]),False),
                ((0,0),(2,2),[(1,1)],True),
                ((0,0),(2,2),[(1,2)],False)]
    for a,b,hull,expected in hull_cases:
        require(segment_hits_hull(a,b,hull)==expected,'Hull intersection fixture failed')
    reject(validate_support_clique,[0,1,2,3],[(0,1),(2,3)],None,
           [(0,0),(2,0),(0,1),(2,1)])
    reject(validate_support_clique,list(range(5)),[(0,1)],3,
           [(0,0),(1,0),(0,2),(1,2),(0,3)])
    return {'parametric_segment_comparisons':checks,'hull_fixtures':len(hull_cases),
            'invalid_geometry_rejected':2}


def boolean_graph_controls():
    models=0;patterns=0
    for n in range(2,8):
        edges=list(combinations(range(n),2))
        if n<=5:
            families=[[edge for i,edge in enumerate(edges) if mask&(1<<i)]
                      for mask in range(1<<len(edges))]
        else:
            families=[[],edges,[(0,j) for j in range(1,n)],
                      [tuple(sorted((i,(i+1)%n))) for i in range(n)],
                      [tuple(sorted((i,(i+3)%n))) for i in range(n)]]
        for family in families:
            for threshold in [None,*range(n//2+1,n+1)]:
                basis=clique_coefficients(n,family,threshold)
                for mask in range(1<<n):
                    direct=int((threshold is not None and mask.bit_count()>=threshold)
                               or any(mask&(1<<i) and mask&(1<<j) for i,j in family))
                    expansion=sum(value for subset,value in enumerate(basis)
                                  if subset&mask==subset)
                    require(expansion==direct,'Graph Boolean Mobius identity failed')
                models+=1;patterns+=1<<n
    return {'graph_models_checked':models,'boolean_patterns_checked':patterns,
            'all_graphs_enumerated_through_size':5,'selected_graphs_through_size':7}


def candidate_boolean_controls(path):
    certificate=json.loads(path.read_text());models=0;patterns=0
    adapted.expand(certificate)  # Includes every exact geometric and D4 premise.
    for atom in certificate['charge_orbits']:
        if atom.get('kind') not in ('edge_or','convex_clique'):continue
        support_sets=atom.get('support_sets',[[] for _ in atom['sets']])
        edge_sets=atom.get('edge_sets',[[] for _ in atom['sets']])
        for group,edges,supports in zip(atom['sets'],edge_sets,support_sets):
            n=len(group);local={site:i for i,site in enumerate(group)}
            local_edges=[(local[i],local[j]) for i,j in edges]
            threshold=atom.get('threshold') if atom['kind']=='convex_clique' else None
            local_supports=[tuple(local[i] for i in support) for support in supports]
            coefficients=clique_coefficients(n,local_edges,threshold,local_supports)
            for mask in range(1<<n):
                captured={group[i] for i in range(n) if mask&(1<<i)}
                direct=int((threshold is not None and len(captured)>=threshold)
                           or any(i in captured and j in captured for i,j in edges)
                           or any(set(support)<=captured for support in supports))
                expanded=sum(value for subset,value in enumerate(coefficients)
                             if subset&mask==subset)
                require(direct==expanded,'Candidate logical identity failed')
            models+=1;patterns+=1<<n
    return {'certificate_sha256':sha256(path.read_bytes()).hexdigest(),
            'geometric_feature_models':models,'boolean_patterns':patterns,
            'all_geometry_and_D4_premises_checked':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-root',type=Path,required=True)
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();start=time.monotonic()
    original_root=args.original_root.resolve()
    spec=importlib.util.spec_from_file_location('original_exact_mixed',original_root/'exact_mixed.py')
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    require(inspect.getsource(adapted.geometry)==inspect.getsource(original.geometry),
            'Geometry kernel changed')
    original_sweep=(original_root/'integer_sweep.py').read_bytes()
    require(original_sweep==(Path(__file__).parent/'integer_sweep.py').read_bytes(),
            'Integer sweep kernel changed')
    certificate=json.loads((original_root/'global-certificate.json').read_text())
    data,jobs,margin=adapted.validate(certificate)
    old_data,old_jobs,old_margin=original.validate(certificate)
    require(data==old_data and jobs==old_jobs and margin==old_margin,
            'Original expansion or job geometry changed')
    recorded=json.loads((original_root/'evidence/portable/python.json').read_text())['rows']
    selected=sorted(set([0,1,2,100,1000,3000,6000,9000,len(jobs)-2,len(jobs)-1]+
                        [row['row'] for row in sorted(recorded,key=lambda r:r['minimum_units'])[:12]]))
    rows=[]
    for i in selected:
        arrays=adapted.geometry(*data,*jobs[i])
        value,cells,winner=accumulate(*arrays)
        require(value==recorded[i]['minimum_units'],'Original row minimum mismatch')
        if i in (selected[0],selected[len(selected)//2],selected[-1]):
            direct,_,_=accumulate(*arrays,direct=True)
            require(value==direct,'Range tree and direct sweep disagree')
        rows.append({'row':i,'minimum_units':int(value),'cells':int(cells)})
    result={'status':'PASS_ADAPTED_EXACT_CHECKER_CONTROLS',
            'scope':'Kernel identity, original expansion identity, selected original rows, '
                    'and new algebra/geometry controls; not a full new-certificate replay.',
            'integer_sweep_sha256':sha256(original_sweep).hexdigest(),
            'geometry_kernel_unchanged':True,'original_expansion_unchanged':True,
            'selected_original_rows':rows,
            'geometry_controls':geometric_controls(),
            'graph_boolean_controls':boolean_graph_controls()}
    if args.candidate:result['candidate_controls']=candidate_boolean_controls(args.candidate)
    result['seconds']=time.monotonic()-start
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='selected_original_rows'},indent=2))


if __name__=='__main__':main()
