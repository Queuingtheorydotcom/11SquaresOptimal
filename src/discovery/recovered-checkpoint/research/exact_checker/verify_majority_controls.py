#!/usr/bin/env python3
"""Independent finite controls of the median fan and staircase safety."""
import argparse
from fractions import Fraction as F
from itertools import combinations,product
import json
from pathlib import Path

from charge_geometry import convex_hull,point_in_hull,segments_intersect
from majority_geometry import (direct_majority_charge,majority_rectangles,
                               majority_rectangles_in_domain)


def require(value,message):
    if not value:raise ValueError(message)


def square_meets_hull(center,half,hull):
    x,y=center;left,right=x-half,x+half;bottom,top=y-half,y+half
    if any(left<=u<=right and bottom<=v<=top for u,v in hull):return True
    square=[(left,bottom),(right,bottom),(right,top),(left,top)]
    if any(point_in_hull(p,hull) for p in square):return True
    if len(hull)<2:return False
    return any(segments_intersect(a,b,c,d)
               for a,b in zip(square,square[1:]+square[:1])
               for c,d in zip(hull,hull[1:]+hull[:1]))


def verify():
    families=[[(0,0)],[(0,0),(4,0),(0,4)],[(0,0),(2,0),(5,0)],
              [(-2,1),(1,-2),(3,3)],
              [(-3,0),(-1,-3),(3,-2),(4,2),(0,4)],
              [(-4,0),(-2,0),(0,0),(2,0),(4,0)],
              [(0,0),(4,0),(0,4),(1,1),(2,1)],
              [(-3,0),(-2,-3),(1,-4),(4,-1),(4,2),(0,4),(-2,3)],
              [(0,0),(5,0),(0,5),(1,1),(2,1),(1,2),(2,2)]]
    domains=[convex_hull([(-6,-6),(6,-6),(6,6),(-6,6)]),
             convex_hull([(-4,-2),(2,-4),(4,2),(-2,4)])]
    values=[F(i) for i in range(-5,6)]+[F(-1,2),F(1,2)]
    centers=list(product(values,repeat=2))
    fan_checks=0;proxy_checks=0;rectangles_checked=0;budget_pairs=0
    for points in families:
        k=(len(points)+1)//2
        hulls=[convex_hull(subset) for subset in combinations(points,k)]
        qualifying=[]
        for half in (2,3):
            for center in centers:
                expected=int(all(square_meets_hull(center,half,hull) for hull in hulls))
                require(direct_majority_charge(points,half,center)==expected,
                        'Finite median fan disagrees with direct hull intersections')
                fan_checks+=1
                if expected:qualifying.append((center,half))
            for subdivisions in (1,2,4):
                plain=majority_rectangles(points,half,subdivisions,verify_corners=True)
                rectangles_checked+=len(plain)
                for center in centers:
                    covered=any(a<=center[0]<=b and lo<=center[1]<=hi for a,b,lo,hi in plain)
                    require(not covered or direct_majority_charge(points,half,center),
                            'Unconditional staircase captures an invalid center')
                    proxy_checks+=1
                for domain in domains:
                    conditional=majority_rectangles_in_domain(points,half,domain,subdivisions,
                                                              verify_corners=True)
                    rectangles_checked+=len(conditional)
                    for center in centers:
                        if not point_in_hull(center,domain):continue
                        covered=any(a<=center[0]<=b and lo<=center[1]<=hi
                                    for a,b,lo,hi in conditional)
                        require(not covered or direct_majority_charge(points,half,center),
                                'Conditional staircase captures an invalid legal center')
                        interiors=sum(a<center[0]<b and lo<center[1]<hi
                                      for a,b,lo,hi in conditional)
                        require(interiors<=1,'Staircase rectangle interiors overlap')
                        proxy_checks+=1
        for (first,h1),(second,h2) in combinations(qualifying,2):
            require(abs(first[0]-second[0])<=h1+h2 and abs(first[1]-second[1])<=h1+h2,
                    'Disjoint closed squares both trigger the majority charge')
            budget_pairs+=1
    return {'status':'PASS_EXACT_MAJORITY_FAN_AND_STAIRCASE_CONTROLS',
            'scope':'Finite exact controls plus separately stated universal proofs; '
                    'not a full numerical packing certificate.',
            'site_families':len(families),'site_sizes':[1,3,5,7],
            'median_vs_direct_hull_checks':fan_checks,
            'proxy_membership_checks':proxy_checks,
            'rectangles_with_exact_corner_or_domain_clip_checks':rectangles_checked,
            'qualifying_square_pair_budget_checks':budget_pairs,
            'tested_subdivision_counts':[1,2,4],
            'collinear_and_boundary_cases_included':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=verify()
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
