#!/usr/bin/env python3
"""Exact toy showing a square-specific budget-one rule beyond TRUE majority."""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import json
import sys
from square_variance_support import moment,disk_witness,subset_disk_witness,require

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/exact_checker'))
from charge_geometry import convex_hull,hulls_intersect,clique_coefficients


def main():
    A=F(1);B=F(99,100)
    points=[(-F(49,100),-F(49,100)),(F(49,100),F(49,100)),
            (F(3,5),-F(7,10)),(F(3,5),F(7,10)),(F(3,5),F(0))]
    T=(0,1);U=(2,3,4);threshold=list(combinations(range(5),3));family=threshold+[T]
    proof=subset_disk_witness([points[i] for i in T],[points[i] for i in U],A)
    require(proof is not None and proof['kind']=='variance_disks','Toy disk proof failed')
    direct=disk_witness([points[i] for i in T],[points[i] for i in (2,3)],A)
    require(direct is not None and direct['sum_upper']<F(841,1000),'Expected strict disk margin failed')
    require(moment([points[i] for i in T])[1]==F(2401,5000),'T variance differs')
    require(moment([points[i] for i in (2,3)])[1]==F(49,100),'Extreme-pair variance differs')
    shared=0;metric=0
    for first,second in combinations(family,2):
        if set(first)&set(second):shared+=1;continue
        require(subset_disk_witness([points[i] for i in first],[points[i] for i in second],A)
                is not None,'Support-family conflict failed')
        metric+=1
    require(shared==54 and metric==1,'Unexpected support-family inventory')
    core=[(-B/2,-B/2),(B/2,-B/2),(B/2,B/2),(-B/2,B/2)]
    captured=[i for i,(x,y) in enumerate(points) if abs(x)<=B/2 and abs(y)<=B/2]
    require(captured==[0,1],'Toy core captures wrong sites')
    require(not hulls_intersect(convex_hull([points[i] for i in T]),convex_hull([points[i] for i in U])),
            'Toy support hulls must be disjoint')
    require(not hulls_intersect(core,convex_hull([points[i] for i in U])),
            'Toy core must miss a3-site hull, making TRUE majority zero')
    # U is not an impossible threshold: a side.99 square at45degrees can capture it.
    # Projection magnitudes of its extreme sites equal.7/sqrt2 < .99/2.
    require(2*F(7,10)**2<B*B,'Complementary threshold is not capturable at side.99')
    coefficients=clique_coefficients(5,[T],3)
    for mask in range(32):
        logical=int(mask.bit_count()>=3 or mask&3==3)
        expanded=sum(c for part,c in enumerate(coefficients) if part&mask==part)
        require(logical==expanded,'Boolean expansion does not match rule')
    # Boundary-rich algebraic monotonicity checks, using squared equivalents:
    # eta(A)-eta(B) >= (A-B)/2 follows from eta(A)+eta(B)<=A+B.
    controls=0
    for variance in (F(0),F(1,10),F(49,100),F(2401,5000)):
        for side in (F(7,10),F(9,10),F(99,100),F(1)):
            if side*side/2<variance:continue
            require(A*A/2-variance<=A*A and side*side/2-variance<=side*side,
                    'Monotonicity premise failed')
            controls+=1
    result=dict(status='PASS_EXACT_SQUARE_SPECIFIC_MAJORITY_TOY',A=str(A),core_side=str(B),
                sites=[[str(x),str(y)] for x,y in points],captured=captured,
                threshold_charge=0,true_majority_charge=0,new_square_specific_charge=1,
                support_pair_checks=55,shared_site_checks=shared,variance_disk_checks=metric,
                boolean_masks_checked=32,monotonicity_controls=controls,
                complementary_threshold_capturable=True,
                core_strictly_inside_unit_parent=True,strict_core_margin=str((A-B)/2),
                exact_disk_witness=direct,
                scope='Budget1 for this finite captured-support rule on pairwise disjoint closed squares of arbitrary sides≤1. No proof that TRUE-majority OR the new support has budget1; no packing bound.')
    out=Path(__file__).with_name('square-variance-toy-controls.json')
    out.write_text(json.dumps(result,default=lambda x:str(x) if isinstance(x,F) else x,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='exact_disk_witness'},indent=2))


if __name__=='__main__':main()
