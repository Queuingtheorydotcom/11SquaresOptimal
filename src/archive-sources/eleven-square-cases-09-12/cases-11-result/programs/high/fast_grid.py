"""Certified bounded-size rational inner approximations of owned convex hulls.

Every retained grid point carries an exact convex-combination witness in three
original vertices. Replay needs neither a hull algorithm nor rounding logic.
"""
from gmpy2 import mpq as F
from types import SimpleNamespace
import fast_convex_v2 as base
geom = SimpleNamespace(__file__=base.__file__, gift_hull=base.hull, twice_area=base.twice_area, cross=base.cross, polygon_rows=lambda p: [(n[0],n[1],b) for n,b in base.rows(p)])
if not __debug__:raise RuntimeError('Assertions must be enabled')

BASE=[(1,0),(4,1),(2,1),(4,3),(1,1),(3,4),(1,2),(1,4)]
DIRECTIONS=[]
for turn in range(4):
    for a,b in BASE:
        for _ in range(turn):a,b=-b,a
        DIRECTIONS.append((a,b))

def round_grid(x,D):return F((x*D+F(1,2)).numerator//(x*D+F(1,2)).denominator,D)
def barycentric_witness(point,polygon,original):
    lookup={p:i for i,p in enumerate(original)}
    if len(polygon)==1:
        assert point==polygon[0]
        return dict(indices=[lookup[point]],weights=[F(1)])
    if len(polygon)==2:
        a,b=polygon
        axis=0 if a[0]!=b[0] else 1
        t=(point[axis]-a[axis])/(b[axis]-a[axis])
        assert 0<=t<=1 and point==tuple((1-t)*a[k]+t*b[k] for k in (0,1))
        return dict(indices=[lookup[a],lookup[b]],weights=[1-t,t])
    a=polygon[0]
    for b,c in zip(polygon[1:-1],polygon[2:]):
        den=geom.cross(a,b,c)
        if not den:continue
        wb=geom.cross(a,point,c)/den;wc=geom.cross(a,b,point)/den;wa=1-wb-wc
        if min(wa,wb,wc)>=0:
            return dict(indices=[lookup[a],lookup[b],lookup[c]],weights=[wa,wb,wc])
    raise AssertionError('Point has no exact convex-combination witness')

def inner_grid(points,denominator=65536,directions=16):
    original=[tuple(map(F,p)) for p in points];D=int(denominator)
    assert D>0 and directions in (4,8,16,32)
    poly=geom.gift_hull(original)
    if not poly:return dict(status='EMPTY_INPUT',vertices=[],witnesses=[],denominator=D,directions=directions)
    if geom.twice_area(poly)==0:
        candidates=[p for p in poly if all((x*D).denominator==1 for x in p)]
    else:
        constraints=geom.polygon_rows(poly)
        def inside(p):return all(a*p[0]+b*p[1]<=c for a,b,c in constraints)
        # A noncollinear three-vertex centroid is strictly interior. Using
        # three vertices avoids the huge denominator of a full centroid.
        a=poly[0];b=max(poly,key=lambda p:sum((p[k]-a[k])**2 for k in (0,1)))
        c=max(poly,key=lambda p:abs(geom.cross(a,b,p)))
        center=tuple((a[k]+b[k]+c[k])/3 for k in (0,1))
        rounded=tuple(round_grid(x,D) for x in center)
        if inside(rounded):center=rounded
        candidates=[]
        for vertex in poly:
            numerator=0
            while True:
                lam=F(min(numerator,D),D)
                point=tuple(round_grid((1-lam)*vertex[k]+lam*center[k],D) for k in (0,1))
                if inside(point):candidates.append(point);break
                if numerator>=D:break
                numerator=1 if numerator==0 else 2*numerator
    candidates=sorted(set(candidates))
    if candidates:
        selected={max(candidates,key=lambda p:(n[0]*p[0]+n[1]*p[1],p))
                  for n in DIRECTIONS[::32//directions]}
        vertices=geom.gift_hull(selected)
    else:vertices=[]
    witnesses=[dict(point=p,**barycentric_witness(p,poly,original)) for p in vertices]
    result=dict(status='PASS_CERTIFIED_INNER_GRID',vertices=vertices,witnesses=witnesses,
                denominator=D,directions=directions,original_vertices=len(poly),
                rounded_candidates=len(candidates),retained_vertices=len(vertices))
    verify_inner(original,result)
    return result

def verify_inner(original,result):
    """Replay only rational equalities, nonnegativity, and grid membership."""
    original=[tuple(map(F,p)) for p in original];D=int(result['denominator'])
    vertices=[tuple(map(F,p)) for p in result['vertices']]
    assert len(vertices)==len(result['witnesses']) and len(vertices)<=result['directions']
    for p,w in zip(vertices,result['witnesses']):
        assert p==tuple(map(F,w['point'])) and all((x*D).denominator==1 for x in p)
        indices=w['indices'];weights=list(map(F,w['weights']))
        assert 1<=len(indices)==len(weights)<=3 and all(type(i) is int and 0<=i<len(original) for i in indices)
        assert all(x>=0 for x in weights) and sum(weights)==1
        assert p==tuple(sum(a*original[i][k] for i,a in zip(indices,weights)) for k in (0,1))
    return True

def controls():
    polygons=[[(F(1,7),F(1,11)),(F(9,7),F(1,11)),(F(9,7),F(12,11)),(F(1,7),F(12,11))],
              [(F(0),F(0)),(F(1),F(0)),(F(1,100000),F(1,1000000))],
              [(F(0),F(0)),(F(1),F(1))]]
    results=[inner_grid(p,4096,16) for p in polygons]
    assert all(verify_inner(p,r) for p,r in zip(polygons,results))
    bad=dict(results[0]);bad['vertices']=list(bad['vertices']);bad['vertices'][0]=(F(-10),F(-10))
    try:verify_inner(polygons[0],bad)
    except AssertionError:pass
    else:raise AssertionError('Mutated point accepted')
    return dict(status='PASS',cases=3,mutated_point_rejected=True)
if __name__=='__main__':print(controls())
