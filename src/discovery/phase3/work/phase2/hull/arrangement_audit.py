"""Independent exact convex-union cover check by adaptive vertical arrangements.

Hull construction uses gift wrapping; domain intersection enumerates exact line
intersections. Coverage uses affine vertical intervals, splitting only at exact
boundary crossing abscissae when a midpoint covering chain changes validity.
No producer clipping, convex-difference, or hull code is imported.
"""
from fractions import Fraction as F
from itertools import combinations
if not __debug__:raise RuntimeError('Assertions must be enabled')
L=F(191,50)
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def gift_hull(points):
    pts=sorted(set(tuple(map(F,p)) for p in points))
    if len(pts)<3:return pts
    result=[];p=pts[0]
    while True:
        result.append(p);q=next(v for v in pts if v!=p)
        for r in pts:
            orient=cross(p,q,r)
            if orient<0 or (orient==0 and sum((r[k]-p[k])**2 for k in (0,1))>sum((q[k]-p[k])**2 for k in (0,1))):q=r
        p=q
        if p==pts[0]:break
        assert len(result)<=len(pts)
    return result
def polygon_rows(poly):
    out=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        a,b=q[1]-p[1],p[0]-q[0];out.append((a,b,a*p[0]+b*p[1]))
    return out
def intersection_polygon(rows):
    pts=[]
    for (a,b,c),(d,e,f) in combinations(rows,2):
        det=a*e-b*d
        if not det:continue
        x,y=(c*e-b*f)/det,(a*f-c*d)/det
        if all(v*x+w*y<=z for v,w,z in rows):pts.append((x,y))
    return gift_hull(pts)
def twice_area(poly):return abs(sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(poly,poly[1:]+poly[:1]))) if poly else F(0)
def value(line,x):return line[0]*x+line[1]
def vertical_lines(poly,x):
    lines=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        if min(p[0],q[0])<x<max(p[0],q[0]):
            slope=(q[1]-p[1])/(q[0]-p[0]);lines.append((slope,p[1]-slope*p[0]))
    if not lines:return None
    return min(lines,key=lambda z:value(z,x)),max(lines,key=lambda z:value(z,x))
def failure_root(nonnegative_line,a,b):
    fa,fb=value(nonnegative_line,a),value(nonnegative_line,b)
    if fa>=0 and fb>=0:return None
    m,c=nonnegative_line;assert m
    r=-c/m;assert a<r<b
    return r
def minus(a,b):return a[0]-b[0],a[1]-b[1]
def union_cover(domain,regions,max_slabs=100000):
    assert domain and twice_area(domain)>0
    left=min(x for x,y in domain);right=max(x for x,y in domain)
    events=sorted({left,right}|{x for poly in [domain,*regions] for x,y in poly if left<x<right})
    pending=list(reversed(list(zip(events,events[1:]))));accepted=0;splits=0
    while pending:
        a,b=pending.pop();mid=(a+b)/2
        dl=vertical_lines(domain,mid)
        if dl is None:continue
        low,high=dl;current=low
        intervals=[v for p in regions if (v:=vertical_lines(p,mid)) is not None]
        root=None;used=set()
        while value(current,mid)<value(high,mid):
            candidates=[(i,lo,hi) for i,(lo,hi) in enumerate(intervals)
                        if value(lo,mid)<=value(current,mid)<value(hi,mid)]
            if not candidates:
                nextlow=min([value(lo,mid) for lo,hi in intervals if value(lo,mid)>value(current,mid)]+[value(high,mid)])
                return dict(passed=False,status='EXACT_UNCOVERED_POINT',point=(mid,(value(current,mid)+nextlow)/2),accepted_slabs=accepted,splits=splits)
            idx,lo,hi=max(candidates,key=lambda row:value(row[2],mid))
            assert idx not in used;used.add(idx)
            for inequality in (minus(current,lo),minus(hi,current)):
                root=failure_root(inequality,a,b)
                if root is not None:break
            if root is not None:break
            current=hi
        if root is None:root=failure_root(minus(current,high),a,b)
        if root is not None:
            pending.extend([(root,b),(a,root)]);splits+=1
        else:accepted+=1
        if accepted+splits>max_slabs:return dict(passed=False,status='ARRANGEMENT_BUDGET',accepted_slabs=accepted,splits=splits)
    return dict(passed=True,status='PASS_VERTICAL_ARRANGEMENT',accepted_slabs=accepted,splits=splits)
def cs(t):return (1-t*t)/(1+t*t),2*t/(1+t*t)
def interval_geometry(world,hulls,target,lo,hi,U):
    lo,hi,U=F(lo),F(hi),F(U);assert 0<=lo<hi<=1
    B=L/U;t=(lo+hi)/2;c,s=cs(t);f=[];w=[]
    for q in (lo,hi):
        cq,sq=cs(q);d=c*cq+s*sq;v=abs(c*sq-s*cq);assert d>=v and d>0
        f.append(d+v);w.append(cq+sq)
    side=(B-F(1,10**12))/max(f);assert side*max(f)<B
    h=B*min(w)/2
    dom=intersection_polygon(polygon_rows(gift_hull(world))+[(1,0,L-h),(-1,0,-h),(0,1,L-h),(0,-1,-h)])
    corner=[(side*(a*c-b*s)/2,side*(a*s+b*c)/2) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
    groups=list(hulls.values()) if isinstance(hulls,dict) else list(hulls)
    if target is not None:groups=[[*[tuple(map(F,target))]],*groups]
    regions=[gift_hull([(p[0]+q[0],p[1]+q[1]) for p in group for q in corner]) for group in groups if group]
    return dom,regions,side,t
def interval_cover(world,hulls,target,lo,hi,U):
    dom,regions,side,t=interval_geometry(world,hulls,target,lo,hi,U)
    if not dom:return dict(passed=True,status='EMPTY_DOMAIN',accepted_slabs=0,splits=0)
    if twice_area(dom)==0:return dict(passed=False,status='DEGENERATE_DOMAIN')
    return dict(core_side=side,reference_half_angle=t,**union_cover(dom,regions))
def audit_residual_cover(world,hulls,lo,hi,U,residual):
    """Prove that every feasible parent center is in a supplied residual union.

    Feasible centers cannot belong to any forbidden mandatory-hull Minkowski
    polygon. Thus covering the domain by forbidden regions and residual pieces
    proves localization in those pieces, without asserting infeasibility.
    """
    dom,regions,side,t=interval_geometry(world,hulls,None,lo,hi,U)
    if not dom:return dict(passed=True,status='EMPTY_DOMAIN',accepted_slabs=0,splits=0)
    if twice_area(dom)==0:return dict(passed=False,status='DEGENERATE_DOMAIN')
    residual=[gift_hull(p) for p in residual if p]
    # Zero-area pieces are unnecessary for the closed-cover argument.
    residual=[p for p in residual if twice_area(p)>0]
    ans=union_cover(dom,regions+residual)
    return dict(core_side=side,reference_half_angle=t,localization_only=True,**ans)
def controls():
    square=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
    a=[(F(0),F(0)),(F(1),F(0)),(F(0),F(1))]
    b=[(F(1),F(1)),(F(0),F(1)),(F(1),F(0))]
    assert union_cover(square,[a,b])['passed']
    assert not union_cover(square,[a])['passed']
    assert gift_hull(square)==square
    assert intersection_polygon(polygon_rows(square))==square
    return {'status':'PASS','checks':4}
if __name__=='__main__':print(controls())
