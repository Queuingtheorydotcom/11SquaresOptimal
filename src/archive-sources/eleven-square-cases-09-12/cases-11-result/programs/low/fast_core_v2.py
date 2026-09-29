"""Rational polygon strict cores, with exact full-interval vertex certificates.

All proposal vertices are checked by four rational quadratic minima. The
endpoint shrink formula is merely a proposal; no acceptance relies on it.
"""
from gmpy2 import mpq as F
from functools import lru_cache
from pathlib import Path
import sys
if not __debug__:raise RuntimeError('Assertions must be enabled')
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'phase2/hull'))
import fast_convex_v2 as base
L=base.L
EPS=F(1,10**12)

def quadratic_minimum(A,B,C,lo,hi):
    """Minimum of A*t^2+B*t+C on a closed rational interval."""
    lo,hi=F(lo),F(hi)
    candidates=[(lo,A*lo*lo+B*lo+C),(hi,A*hi*hi+B*hi+C)]
    if A>0:
        t=-B/(2*A)
        if lo<t<hi:candidates.append((t,A*t*t+B*t+C))
    return min(candidates,key=lambda x:x[1])

def validate_vertex(point,lo,hi,parent_side):
    x,y=map(F,point);lo,hi,B=F(lo),F(hi),F(parent_side)
    assert 0<=lo<hi<=1 and B>0
    records=[]
    for axis,(a,b) in enumerate(((x,y),(y,-x))):
        for sign in (-1,1):
            A=B/2-sign*a;C=B/2+sign*a;linear=2*sign*b
            t,margin=quadratic_minimum(A,linear,C,lo,hi)
            records.append(dict(axis=axis,sign=sign,coefficients=[A,linear,C],minimum_at=t,minimum=margin))
    return dict(passed=all(r['minimum']>0 for r in records),point=(x,y),quadratics=records)

def validate_core(vertices,lo,hi,U):
    vertices=[tuple(map(F,p)) for p in vertices]
    assert len(vertices)>=3 and base.twice_area(vertices)>0
    records=[validate_vertex(p,lo,hi,L/F(U)) for p in vertices]
    return dict(passed=all(r['passed'] for r in records),vertices=records)

@lru_cache(maxsize=16384)
def polygon_core(lo,hi,U):
    lo,hi,U=F(lo),F(hi),F(U);B=L/U
    assert 0<=lo<hi<=1 and U>1
    # Keep the old core so the proposed polygon never regresses in strength.
    t=(lo+hi)/2;c,s=base.cs(t);factors=[];narrow=True
    for end in (lo,hi):
        ce,se=base.cs(end);dot=c*ce+s*se;cr=abs(c*se-s*ce)
        narrow &= dot>0 and dot>=cr;factors.append(dot+cr)
    # For very wide rows the old endpoint-factor formula is unavailable.
    # The rational factor 2 safely bounds every projection support instead.
    oldside=(B-EPS)/(max(factors) if narrow else F(2))
    old=[(oldside*(a*c-b*s)/2,oldside*(a*s+b*c)/2) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
    endpoint_side=B*(1-(hi-lo)**2/2)-EPS
    p=[(-B,-B),(B,-B),(B,B),(-B,B)]
    for end in (lo,hi):
        c,s=base.cs(end)
        for n in ((c,s),(-c,-s),(-s,c),(s,-c)):
            p=base.clip_linear(p,n,endpoint_side/2)
    # Only universally certified proposal vertices may enlarge the old core.
    accepted=[v for v in p if validate_vertex(v,lo,hi,B)['passed']]
    result=base.hull(old+accepted)
    certificate=validate_core(result,lo,hi,U);assert certificate['passed']
    return dict(vertices=tuple(result),endpoint_side=endpoint_side,reference_half_angle=t,
                old_core_side=oldside,old_core_vertices=tuple(old),certificate=certificate)

def ownership_halfplanes(residual_vertices,core_vertices):
    """All p satisfying the returned facets lie in z+Q for every residual z."""
    residual_vertices=[tuple(map(F,p)) for p in residual_vertices]
    assert residual_vertices
    return [(n,b+min(n[0]*p[0]+n[1]*p[1] for p in residual_vertices))
            for n,b in base.rows(core_vertices)]

def row_geometry(world,lo,hi,U):
    core=polygon_core(F(lo),F(hi),F(U))
    B=L/F(U);h=B*min(sum(base.cs(F(t))) for t in (lo,hi))/2
    domain=base.hull(world)
    for n,b in (((1,0),L-h),((-1,0),-h),((0,1),L-h),((0,-1),-h)):
        domain=base.clip_linear(domain,n,b)
    return domain,list(core['vertices']),core

def interval_cover(world,other_hulls,target,lo,hi,U,max_pieces=10000):
    domain,Q,core=row_geometry(world,lo,hi,U)
    metadata=dict(core_vertices=Q,reference_half_angle=core['reference_half_angle'],
                  core_side=core['old_core_side'],core_kind='certified_endpoint_polygon',outer_domain=domain)
    if not domain:return dict(passed=True,status='PASS_EMPTY_OUTER_DOMAIN',remaining=[],peak_pieces=0,regions_used=0,**metadata)
    groups=list(other_hulls.values()) if isinstance(other_hulls,dict) else list(other_hulls)
    minusQ=[(-x,-y) for x,y in Q]
    regions=[]
    if target is not None:
        p=tuple(map(F,target));regions.append(base.hull([(p[0]+q[0],p[1]+q[1]) for q in minusQ]))
    forbidden=[base.hull([(p[0]+q[0],p[1]+q[1]) for p in base.hull(K) for q in minusQ]) for K in groups if K]
    forbidden.sort(key=base.twice_area,reverse=True);regions.extend(forbidden)
    return dict(**metadata,**base.union_cover(domain,regions,max_pieces))

# The driver may use these exact generic polygon operations through one module.
hull=base.hull
rows=base.rows
clip_linear=base.clip_linear
cs=base.cs
twice_area=base.twice_area

def controls():
    U=F(387708359002281417731,10**20);B=L/U;records=[]
    for a,b in ((F(0),F(1)),(F(0),F(1,64)),(F(15,64),F(16,64)),(F(63,64),F(1))):
        r=polygon_core(a,b,U)
        assert r['certificate']['passed']
        assert all(all(n[0]*p[0]+n[1]*p[1]<=v for n,v in rows(r['vertices'])) for p in r['old_core_vertices'])
        assert not validate_vertex((B,B),a,b,B)['passed']
        records.append(dict(interval=[a,b],vertices=len(r['vertices']),area_ratio=twice_area(r['vertices'])/twice_area(list(r['old_core_vertices']))))
    assert quadratic_minimum(F(1),F(-1),F(1),F(0),F(1))==(F(1,2),F(3,4))
    assert quadratic_minimum(F(-1),F(0),F(1),F(0),F(1))==(F(1),F(0))
    return dict(status='PASS',checks=14,intervals=records)

if __name__=='__main__':
    import json
    print(json.dumps(controls(),default=str,indent=2))
