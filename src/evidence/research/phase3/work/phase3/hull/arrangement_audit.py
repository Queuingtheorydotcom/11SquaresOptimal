"""Independent exact convex-union cover check by adaptive vertical arrangements.

Hull construction uses gift wrapping; domain intersection enumerates exact line
intersections. Coverage uses affine vertical intervals, splitting only at exact
boundary crossing abscissae when a midpoint covering chain changes validity.
No producer clipping, convex-difference, or hull code is imported.
"""
from rational import F
from itertools import combinations
from functools import cmp_to_key
if not __debug__:raise RuntimeError('Assertions must be enabled')
L=F(191,50)
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def gift_hull(points):
    pts=sorted(set(tuple(map(F,p)) for p in points))
    if len(pts)<3:return pts
    # Independent Graham scan, rather than the producer's monotone chains.
    pivot=min(pts,key=lambda p:(p[1],p[0]))
    def compare(p,q):
        turn=cross(pivot,p,q)
        if turn:return -1 if turn>0 else 1
        dp=(p[0]-pivot[0])**2+(p[1]-pivot[1])**2
        dq=(q[0]-pivot[0])**2+(q[1]-pivot[1])**2
        return (dp>dq)-(dp<dq)
    result=[pivot]
    for p in sorted((p for p in pts if p!=pivot),key=cmp_to_key(compare)):
        while len(result)>1 and cross(result[-2],result[-1],p)<=0:result.pop()
        result.append(p)
    first=min(range(len(result)),key=lambda i:result[i])
    return result[first:]+result[:first]
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
def prepare_polygon(poly):
    edges=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        if p[0]==q[0]:continue
        slope=(q[1]-p[1])/(q[0]-p[0]);edges.append((min(p[0],q[0]),max(p[0],q[0]),(slope,p[1]-slope*p[0])))
    return min(x for x,y in poly),max(x for x,y in poly),edges
def prepared_vertical(poly,x):
    left,right,edges=poly
    if not left<x<right:return None
    lines=[(line,value(line,x)) for a,b,line in edges if a<x<b]
    if not lines:return None
    low=min(lines,key=lambda z:z[1]);high=max(lines,key=lambda z:z[1])
    return low[0],high[0],low[1],high[1]
def union_cover(domain,regions,max_slabs=100000):
    assert domain and twice_area(domain)>0
    left=min(x for x,y in domain);right=max(x for x,y in domain)
    events=sorted({left,right}|{x for poly in [domain,*regions] for x,y in poly if left<x<right})
    pending=list(reversed(list(zip(events,events[1:]))));accepted=0;splits=0
    pdomain=prepare_polygon(domain);pregions=[prepare_polygon(poly) for poly in regions]
    while pending:
        a,b=pending.pop();mid=(a+b)/2
        dl=prepared_vertical(pdomain,mid)
        if dl is None:continue
        low,high,lowvalue,highvalue=dl;current=low;currentvalue=lowvalue
        intervals=[v for p in pregions if (v:=prepared_vertical(p,mid)) is not None]
        root=None;used=set()
        while currentvalue<highvalue:
            candidates=[(i,lo,hi,hv) for i,(lo,hi,lv,hv) in enumerate(intervals)
                        if lv<=currentvalue<hv]
            if not candidates:
                nextlow=min([lv for lo,hi,lv,hv in intervals if lv>currentvalue]+[highvalue])
                return dict(passed=False,status='EXACT_UNCOVERED_POINT',point=(mid,(currentvalue+nextlow)/2),accepted_slabs=accepted,splits=splits)
            idx,lo,hi,hivalue=max(candidates,key=lambda row:row[3])
            assert idx not in used;used.add(idx)
            for inequality in (minus(current,lo),minus(hi,current)):
                root=failure_root(inequality,a,b)
                if root is not None:break
            if root is not None:break
            current=hi;currentvalue=hivalue
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
