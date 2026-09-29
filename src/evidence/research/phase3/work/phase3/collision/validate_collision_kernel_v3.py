"""Independent inner-region validation for a universal pair-collision kernel.

The caller supplies proved strict-core polygons and a COMPLETE possible-pose
cover for the partner. This module validates the geometric consequence only.
It explicitly constructs each Qj + (-Qi) from all vertex sums, independently
of a producer that merges facet normals or clips by support-function bounds.
"""
from pathlib import Path
from functools import lru_cache
import sys
if not __debug__:raise RuntimeError('Assertions must be enabled')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hull'))
from rational import F
import arrangement_audit_v2 as geo

def parse(P):return [tuple(x if isinstance(x,F) else F(str(x)) for x in p) for p in P]
def bounded_rows(P):
    H=geo.gift_hull(P);assert H
    xs=[p[0] for p in H];ys=[p[1] for p in H]
    return geo.polygon_rows(H)+[(1,0,max(xs)),(-1,0,-min(xs)),(0,1,max(ys)),(0,-1,-min(ys))]

@lru_cache(maxsize=8192)
def minkowski_facets(Qi,Qj):
    M=geo.gift_hull([(p[0]-q[0],p[1]-q[1]) for p in Qj for q in Qi])
    assert geo.twice_area(M)>0
    out=[]
    for nx,ny,h in geo.polygon_rows(M):
        scale=abs(nx) if nx else abs(ny)
        out.append((nx/scale,ny/scale,h/scale))
    return tuple(out)

@lru_cache(maxsize=8192)
def canonical_core(Q):
    H=tuple(geo.gift_hull(Q));assert geo.twice_area(list(H))>0
    return H

@lru_cache(maxsize=32768)
def minimum_support(D,nx,ny):
    return min(nx*p[0]+ny*p[1] for p in D)

def collision_halfplanes(core_i,partner_rows):
    """Yield all necessary/sufficient facets of the universal collision set.

    Rows are {core, domain, reference}; empty domains carry no possible pose.
    min projection over a polygon union can be supplied by the flattened
    residual vertices: only the convex hull matters for this universal rule.
    """
    Qi=canonical_core(tuple(parse(core_i)))
    live=0
    for index,row in enumerate(partner_rows):
        D=parse(row['domain'])
        if not D:continue
        live+=1;Qj=canonical_core(tuple(parse(row['core'])))
        for nx,ny,h in minkowski_facets(Qi,Qj):
            up=h+minimum_support(tuple(D),nx,ny)
            yield dict(partner_row=index,reference=row.get('reference'),normal=(nx,ny),upper=up)
    if not live:raise ValueError('Partner has no possible pose: use an explicit empty-domain contradiction')

def validate_collision_polygon(core_i,partner_rows,query_domain,polygon):
    """Certify conv(polygon) is inside the collision kernel and query domain.

    Empty, point, segment, and polygon outputs are handled without dropping
    dimensions. An empty result is valid but supplies no exclusion strength.
    """
    P=parse(polygon);D=parse(query_domain);domain_checks=0;facet_checks=0;rows_seen=set();margins=[]
    if not D:
        assert not P
    else:
        for nx,ny,h in bounded_rows(D):
            for p in P:
                domain_checks+=1
                if nx*p[0]+ny*p[1]>h:
                    return dict(passed=False,status='OUTPUT_ESCAPES_QUERY_DOMAIN',point=p,normal=(nx,ny),upper=h)
    supports={}
    for cut in collision_halfplanes(core_i,partner_rows):
        rows_seen.add(cut['partner_row']);nx,ny=cut['normal'];h=cut['upper']
        facet_checks+=len(P)
        if P:
            normal=(nx,ny)
            if normal not in supports:
                supports[normal]=max((nx*p[0]+ny*p[1],p) for p in P)
            support,p=supports[normal];slack=h-support
            if slack<0:return dict(passed=False,status='OUTPUT_ESCAPES_UNIVERSAL_COLLISION_KERNEL',point=p,slack=slack,**cut)
            margins.append(slack)
    return dict(passed=True,status='PASS_INNER_UNIVERSAL_COLLISION_REGION',vertices=len(P),live_partner_rows=len(rows_seen),
                domain_vertex_checks=domain_checks,facet_vertex_checks=facet_checks,minimum_slack=min(margins) if margins else None,
                empty_output=not P,scope='Geometric consequence of supplied strict cores and complete partner pose cover; ownership/pose antecedents must be separately proved.')

def controls():
    sq=[(-F(1,2),-F(1,2)),(F(1,2),-F(1,2)),(F(1,2),F(1,2)),(-F(1,2),F(1,2))]
    rows=[dict(core=sq,domain=[(F(0),F(0))],reference='single-center')]
    query=[(-F(2),-F(2)),(F(2),-F(2)),(F(2),F(2)),(-F(2),F(2))]
    assert validate_collision_polygon(sq,rows,query,[(F(1),F(0))])['passed']
    assert not validate_collision_polygon(sq,rows,query,[(F(1)+F(1,10**50),F(0))])['passed']
    assert validate_collision_polygon(sq,rows,[(F(0),F(0))],[(F(0),F(0))])['passed']
    assert not validate_collision_polygon(sq,rows,[(F(0),F(0))],[(F(1,10**50),F(0))])['passed']
    assert validate_collision_polygon(sq,rows,[(F(0),F(0)),(F(1),F(0))],[(F(1,2),F(0))])['passed']
    shifted=[dict(core=sq,domain=[(F(2),F(0))],reference='shifted')]
    assert not validate_collision_polygon(sq,rows+shifted,query,[(F(0),F(0))])['passed']
    assert validate_collision_polygon(sq,rows+shifted,query,[(F(1),F(0))])['passed']
    assert validate_collision_polygon(sq,rows,query,[])['passed']
    try:list(collision_halfplanes(sq,[dict(core=sq,domain=[])]))
    except ValueError:pass
    else:raise AssertionError('Empty partner pose family was accepted')
    return dict(status='PASS_COLLISION_VALIDATOR_CONTROLS',checks=9)

if __name__=='__main__':
    import json
    print(json.dumps(controls(),default=str,indent=2))
