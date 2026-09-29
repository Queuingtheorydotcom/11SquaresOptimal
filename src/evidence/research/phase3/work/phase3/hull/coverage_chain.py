"""Independent convex-union coverage by positive triangle boundary chains.

Input polygons denote their convex hulls.  A positive-area domain is covered
when every supplied positive CCW triangle is contained in both the domain and
its assigned region, and their oriented boundary chain equals the domain's.
Exact support-line endpoint events handle overlapping edge pieces and
T-junctions.  No producer clipping/partition routine is imported.

Proof: the difference of triangle indicators and the domain indicator is a
compactly supported integer-valued function off finitely many edges.  Its
oriented distributional boundary is zero, so its winding number is constant
(and zero outside).  Thus triangles cover every off-edge domain point.
Because their finite union is closed, they cover the whole closed domain.
Positive triangle orientation prevents cancellation by negative triangles.
"""
from collections import defaultdict
from math import gcd
from rational import F
import arrangement_audit_v2 as geo
if not __debug__:raise RuntimeError('Assertions must be enabled')

def polygon(P):
    return geo.gift_hull([tuple(map(F,p)) for p in P])

def rows(P):
    if not P:return []
    xs=[p[0] for p in P];ys=[p[1] for p in P]
    return geo.polygon_rows(P)+[(F(1),F(0),max(xs)),(-F(1),F(0),-min(xs)),
                               (F(0),F(1),max(ys)),(F(0),-F(1),-min(ys))]

def contains(halfplanes,p):
    return all(a*p[0]+b*p[1]<=c for a,b,c in halfplanes)

def lower_dimensional_cover(domain,regions):
    """Exact affine parameter interval union, including singleton domains."""
    assert domain and len(domain)<=2
    p,q=domain[0],domain[-1];d=(q[0]-p[0],q[1]-p[1]);intervals=[]
    for R in regions:
        if not R:continue
        lo,hi=F(0),F(1);possible=True
        for a,b,c in rows(R):
            slope=a*d[0]+b*d[1];slack=c-a*p[0]-b*p[1]
            if slope>0:hi=min(hi,slack/slope)
            elif slope<0:lo=max(lo,slack/slope)
            elif slack<0:possible=False;break
        if possible and lo<=hi:intervals.append((lo,hi))
    cursor=F(0)
    for lo,hi in sorted(intervals):
        if hi<cursor:continue
        if lo>cursor:return dict(passed=False,status='UNCOVERED_PARAMETER_INTERVAL',gap=(cursor,lo))
        cursor=max(cursor,hi)
        if cursor>=1:return dict(passed=True,status='PASS_EXACT_LOWER_DIMENSIONAL_COVER',triangles=0,support_lines=0)
    return dict(passed=False,status='UNCOVERED_PARAMETER_INTERVAL',gap=(cursor,F(1)))

def edge_key(p,q):
    """Primitive canonical integer normal and rational line offset."""
    dx,dy=q[0]-p[0],q[1]-p[1];assert dx or dy
    a,b=dy,-dx
    denominator=a.denominator//gcd(a.denominator,b.denominator)*b.denominator
    ai,bi=int(a.numerator*(denominator//a.denominator)),int(b.numerator*(denominator//b.denominator))
    divisor=gcd(abs(ai),abs(bi));ai//=divisor;bi//=divisor
    if ai<0 or (ai==0 and bi<0):ai=-ai;bi=-bi
    offset=ai*p[0]+bi*p[1]
    # Along a nonvertical line, x parametrizes it; otherwise y does.
    t0,t1=(p[0],q[0]) if bi else (p[1],q[1])
    assert t0!=t1
    return (ai,bi,offset),min(t0,t1),max(t0,t1),(1 if t1>t0 else -1)

def validate_mesh(domain,regions,mesh):
    """Prove coverage, ignoring any producer status or remaining-list claim."""
    D=polygon(domain);R=[polygon(P) for P in regions]
    if not D:return dict(passed=True,status='PASS_EMPTY_DOMAIN',triangles=0,support_lines=0)
    if len(D)<=2:return lower_dimensional_cover(D,R)
    assert geo.twice_area(D)>0
    triangles=mesh['triangles'] if isinstance(mesh,dict) else mesh
    domain_rows=rows(D);region_rows={};events=defaultdict(lambda:defaultdict(int));membership=0
    def add_edge(p,q,multiplicity):
        key,lo,hi,direction=edge_key(p,q)
        events[key][lo]+=multiplicity*direction;events[key][hi]-=multiplicity*direction
    for p,q in zip(D,D[1:]+D[:1]):add_edge(p,q,-1)
    for index,record in enumerate(triangles):
        T=[tuple(map(F,p)) for p in record['vertices']]
        if len(T)!=3 or geo.cross(*T)<=0:
            return dict(passed=False,status='TRIANGLE_NOT_POSITIVE_CCW',triangle=index)
        k=record['region_index']
        if type(k) is not int or not 0<=k<len(R) or not R[k]:
            return dict(passed=False,status='INVALID_ASSIGNED_REGION',triangle=index)
        if k not in region_rows:region_rows[k]=rows(R[k])
        for p in T:
            if not contains(domain_rows,p) or not contains(region_rows[k],p):
                return dict(passed=False,status='TRIANGLE_VERTEX_OUTSIDE_ASSIGNED_DOMAIN_OR_REGION',triangle=index,point=p)
            membership+=len(domain_rows)+len(region_rows[k])
        for p,q in zip(T,T[1:]+T[:1]):add_edge(p,q,1)
    segments=0
    for line,ev in events.items():
        cursor=0;points=sorted(ev)
        for i,t in enumerate(points):
            cursor+=ev[t]
            if i+1<len(points):
                segments+=1
                if cursor:
                    return dict(passed=False,status='ORIENTED_BOUNDARY_CHAIN_MISMATCH',line=line,interval=(t,points[i+1]),multiplicity=cursor)
        assert cursor==0
    return dict(passed=True,status='PASS_POSITIVE_TRIANGLE_BOUNDARY_CHAIN',triangles=len(triangles),
                support_lines=len(events),edge_intervals=segments,vertex_halfplane_checks=membership)
