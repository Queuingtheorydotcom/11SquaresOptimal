#!/usr/bin/env python3
"""Exact half-turn variant: 16 capacity-one cells, 2,184 selection orbits.

Use concentric containers when applying the mask symmetry at varying side S.
"""
from fractions import Fraction as F
from pathlib import Path
from itertools import combinations
import json,hashlib
from verify_center_cover import CENTERS,DEN,SIDE_UPPER,verify,require

def symmetric_sites():
    return [tuple((F(CENTERS[i][k],DEN)+1-F(CENTERS[15-i][k],DEN))/2 for k in range(2)) for i in range(16)]

def run():
    sites=symmetric_sites()
    out=verify(sites,radius=F(171,1000))
    for i,p in enumerate(sites):
        require(all(p[k]+sites[15-i][k]==1 for k in range(2)),'site half-turn equality')
    for i,cell in enumerate(out['cells']):
        a={tuple(F(x) for x in p) for p in cell['vertices']}
        b={tuple(1-F(x) for x in p) for p in out['cells'][15-i]['vertices']}
        require(a==b,'polygon half-turn equality')
    selections=[tuple(j) for j in out['all_eleven_cell_subsets']]
    turn=lambda j:tuple(sorted(15-i for i in j))
    require(all(j!=turn(j) for j in selections),'odd selection invariant under fixed-point-free involution')
    representatives=sorted({min(j,turn(j)) for j in selections})
    require(len(representatives)==2184,'incorrect canonical mask count')
    out.update({'status':'PASS_EXACT_HALF_TURN_16_CELL_COVER','center_domain_coordinate_convention':'Centered container [-S/2,S/2]^2; map normalized u to (U_plus-1)*(u-1/2). Equivalently translate by U_plus/2 and use concentric containment [(U_plus-S)/2,(U_plus+S)/2]^2.','symmetry_cell_involution':[15-i for i in range(16)],'canonical_eleven_cell_selections':len(representatives),'canonical_eleven_cell_subsets':[list(j) for j in representatives],'covering_radius_optimality_claimed':False,'source_checker_sha256':hashlib.sha256(Path(__file__).with_name('verify_center_cover.py').read_bytes()).hexdigest(),'symmetric_checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    return out

if __name__=='__main__':
    out=run();Path(__file__).with_name('center-cover-symmetric-exact.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('cells','all_eleven_cell_subsets','canonical_eleven_cell_subsets')},indent=2))
