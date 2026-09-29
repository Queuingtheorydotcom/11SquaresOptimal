"""Exact continuum row coverage by convex mandatory-hull penalties.

For a rational fixed core Q and an owned convex hull K, centers whose core
intersects K are precisely K+(-Q). Here Q is centrally symmetric. Coverage is
proved by subtracting closed convex polygons from the complete legal-center
outer domain, retaining every positive-area convex remainder. Boundaries follow
from closedness of the finite covering union and density of domain interior.
"""
from gmpy2 import mpq as F
from itertools import combinations
from functools import lru_cache
if not __debug__:raise RuntimeError('Exact verifier requires assertions enabled')
L=F(191,50)

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def twice_area(p):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1]))) if p else F(0)
def hull(points):
    p=sorted(set(tuple(map(F,x)) for x in points))
    if len(p)<3:return p
    def half(p):
        q=[]
        for x in p:
            while len(q)>1 and cross(q[-2],q[-1],x)<=0:q.pop()
            q.append(x)
        return q
    return half(p)[:-1]+half(p[::-1])[:-1]
def clean(p):
    result=[]
    for q in p:
        if not result or q!=result[-1]:result.append(q)
    if len(result)>1 and result[0]==result[-1]:result.pop()
    return result
def clip_linear(poly,n,b,inside=True):
    """Keep n dot x <= b, or its opposite closed halfplane."""
    if not poly:return []
    out=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        a=n[0]*p[0]+n[1]*p[1]-b;z=n[0]*q[0]+n[1]*q[1]-b
        ip=a<=0 if inside else a>=0; iq=z<=0 if inside else z>=0
        if ip:out.append(p)
        if ip!=iq:
            t=a/(a-z);out.append(tuple(p[k]+t*(q[k]-p[k]) for k in (0,1)))
    return clean(out)
def rows(poly):
    for p,q in zip(poly,poly[1:]+poly[:1]):
        n=(q[1]-p[1],p[0]-q[0]);yield n,n[0]*p[0]+n[1]*p[1]
def bbox(poly):return min(x for x,y in poly),max(x for x,y in poly),min(y for x,y in poly),max(y for x,y in poly)
def box_disjoint(a,b):return a[1]<b[0] or b[1]<a[0] or a[3]<b[2] or b[3]<a[2]
@lru_cache(maxsize=20000)
def _minkowski(a,b):
    if len(a)<3 or len(b)<3:return tuple(hull([(x+u,y+v) for x,y in a for u,v in b]))
    ka=min(range(len(a)),key=lambda i:(a[i][1],a[i][0]));kb=min(range(len(b)),key=lambda i:(b[i][1],b[i][0]))
    a=a[ka:]+a[:ka];b=b[kb:]+b[:kb];i=j=0;n=len(a);m=len(b);out=[]
    while i<n or j<m:
        out.append((a[i%n][0]+b[j%m][0],a[i%n][1]+b[j%m][1]))
        if i==n:j+=1;continue
        if j==m:i+=1;continue
        av=(a[(i+1)%n][0]-a[i][0],a[(i+1)%n][1]-a[i][1])
        bv=(b[(j+1)%m][0]-b[j][0],b[(j+1)%m][1]-b[j][1]);z=av[0]*bv[1]-av[1]*bv[0]
        if z>=0:i+=1
        if z<=0:j+=1
    # Canonicalize to exactly match the existing Cartesian-hull representation.
    k=min(range(len(out)),key=lambda i:out[i]);return tuple(out[k:]+out[:k])
def minkowski(a,b):return list(_minkowski(tuple(hull(a)),tuple(hull(b))))
def convex_difference(poly,cut):
    """Return closed convex pieces covering closure(poly minus cut)."""
    a,b,c,d=bbox(poly);e,f,g,h=bbox(cut)
    if b<e or f<a or d<g or h<c:return [poly]
    inside=poly;pieces=[]
    for n,offset in rows(cut):
        outside=clip_linear(inside,n,offset,False)
        if twice_area(outside)>0:pieces.append(outside)
        inside=clip_linear(inside,n,offset,True)
        if twice_area(inside)==0:break
    return pieces
def union_cover(domain,regions,max_pieces=10000):
    if twice_area(domain)==0:
        return dict(passed=False,status='DEGENERATE_OUTER_DOMAIN',remaining=[domain])
    pieces=[domain];peak=1;cut_count=0
    for region in regions:
        assert len(region)>=3 and twice_area(region)>0
        updated=[]
        for p in pieces:updated.extend(convex_difference(p,region))
        pieces=updated;peak=max(peak,len(pieces));cut_count+=1
        if not pieces:return dict(passed=True,status='PASS_CONVEX_UNION_COVER',remaining=[],peak_pieces=peak,regions_used=cut_count)
        if len(pieces)>max_pieces:return dict(passed=False,status='PIECE_BUDGET',remaining=pieces,peak_pieces=peak,regions_used=cut_count)
    return dict(passed=False,status='UNCOVERED_OUTER_REGION',remaining=pieces,peak_pieces=peak,regions_used=cut_count)
def cs(t):return (1-t*t)/(1+t*t),2*t/(1+t*t)
def row_geometry(world,lo,hi,U):
    lo,hi,U=F(lo),F(hi),F(U)
    assert 0<=lo<hi<=1 and U>1
    B=L/U;t=(lo+hi)/2;c,s=cs(t);factors=[];widths=[]
    for end in (lo,hi):
        ce,se=cs(end);dot=c*ce+s*se;cr=abs(c*se-s*ce)
        assert dot>0 and dot>=cr
        factors.append(dot+cr);widths.append(ce+se)
    core=(B-F(1,10**12))/max(factors);assert 0<core<B and core*max(factors)<B
    h=B*min(widths)/2;domain=hull(world)
    for n,b in (((1,0),L-h),((-1,0),-h),((0,1),L-h),((0,-1),-h)):
        domain=clip_linear(domain,n,b)
    corners=[(core*(a*c-b*s)/2,core*(a*s+b*c)/2) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
    return domain,corners,t,core
def interval_cover(world,other_hulls,target,lo,hi,U,max_pieces=10000):
    """Arguments/outputs are rational FIELD coordinates in side L=191/50.

    other_hulls may be a list or owner->points mapping; owner exclusion is the
    caller's obligation. target=None requests infeasibility of the whole row.
    No ownership premise is assumed proved by this pure geometric function.
    """
    domain,corners,t,core=row_geometry(world,lo,hi,U)
    if not domain:return dict(passed=True,status='PASS_EMPTY_OUTER_DOMAIN',remaining=[],core_side=core,reference_half_angle=t,peak_pieces=0,regions_used=0)
    groups=list(other_hulls.values()) if isinstance(other_hulls,dict) else list(other_hulls)
    regions=[]
    if target is not None:
        target=tuple(map(F,target));regions.append(hull([(target[0]+x,target[1]+y) for x,y in corners]))
    # Larger regions first is only a performance heuristic; union is unchanged.
    forbidden=[hull([(p[0]+q[0],p[1]+q[1]) for p in hull(k) for q in corners]) for k in groups if k]
    forbidden.sort(key=twice_area,reverse=True);regions.extend(forbidden)
    answer=union_cover(domain,regions,max_pieces)
    return dict(core_side=core,reference_half_angle=t,outer_domain=domain,**answer)

def controls():
    sq=hull([(0,0),(1,0),(1,1),(0,1)])
    left=hull([(0,0),(F(1,2),0),(F(1,2),1),(0,1)])
    right=hull([(F(1,2),0),(1,0),(1,1),(F(1,2),1)])
    assert union_cover(sq,[left,right])['passed']
    assert not union_cover(sq,[left])['passed']
    # Boundary-only join is covered; a genuine rational sliver is retained.
    right_gap=hull([(F(500001,1000000),0),(1,0),(1,1),(F(500001,1000000),1)])
    assert not union_cover(sq,[left,right_gap])['passed']
    assert union_cover(sq,[sq])['passed']
    # Triangle decomposition covers a square along a shared diagonal.
    assert union_cover(sq,[hull([(0,0),(1,0),(0,1)]),hull([(1,1),(1,0),(0,1)])])['passed']
    # A hull penalty may reject an intersecting core although no owned vertex
    # is captured: long segment through a small centered square.
    K=[(F(-2),F(0)),(F(2),F(0))];small=[(F(-1,4),F(-1,4)),(F(1,4),F(-1,4)),(F(1,4),F(1,4)),(F(-1,4),F(1,4))]
    region=hull([(p[0]+q[0],p[1]+q[1]) for p in K for q in small])
    assert all(n[0]*0+n[1]*0<=b for n,b in rows(region))
    assert all(abs(p[0])>F(1,4) for p in K)
    return dict(status='PASS',checks=6)
if __name__=='__main__':print(controls())
