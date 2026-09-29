"""Exact integer inner staircases for the direct majority-hull charge.

Coordinates are in the core's edge axes on the existing integer lattice.
Every returned rectangle is inside the true median-halfspace polygon. The
rectangles have pairwise disjoint interiors; shared boundaries are intentional.
"""
from itertools import combinations
from math import gcd
from fractions import Fraction as F


def require(value,message):
    if not value:raise ValueError(message)


def median_strips(points,half):
    """Return strips (a,b,lo,hi) for lo<=a*x+b*y<=hi, without normalization."""
    m=len(points);require(m in (1,3,5,7),'Odd majority group of at most seven sites required')
    require(type(half) is int and half>0,'Positive integer half-side required')
    normals={(1,0),(0,1)}
    for p,q in combinations(points,2):
        a,b=q[1]-p[1],p[0]-q[0]
        if not a and not b:continue
        divisor=gcd(abs(a),abs(b));a//=divisor;b//=divisor
        if a<0 or (a==0 and b<0):a,b=-a,-b
        normals.add((a,b))
    strips=[]
    for a,b in sorted(normals):
        median=sorted(a*x+b*y for x,y in points)[m//2]
        radius=half*(abs(a)+abs(b))
        strips.append((a,b,median-radius,median+radius))
    return strips


def direct_majority_charge(points,half,center):
    return int(all(lo<=a*center[0]+b*center[1]<=hi
                   for a,b,lo,hi in median_strips(points,half)))


def majority_rectangles(points,half,subdivisions=4,verify_corners=False,strips=None):
    """A conservative union of integer rectangles for one majority polygon.

    Site-capture x events ensure every capture rectangle of a valid support is
    retained generically. Integer rounding moves only inward. Extra subdivision
    improves the approximation; correctness does not depend on its density.
    """
    require(type(subdivisions) is int and subdivisions>=1,'Positive subdivision count required')
    if strips is None:strips=median_strips(points,half)
    middle=len(points)//2
    umed=sorted(p[0] for p in points)[middle]
    vmed=sorted(p[1] for p in points)[middle]
    left,right=umed-half,umed+half
    bottom,top=vmed-half,vmed+half
    events=sorted({left,right}|{u+sign*half for u,v in points for sign in (-1,1)
                              if left<u+sign*half<right})
    refined=set(events)
    for a,b in zip(events,events[1:]):
        refined.update(a+(b-a)*j//subdivisions for j in range(1,subdivisions))
    events=sorted(refined)
    oblique=[]
    for a,b,lo,hi in strips:
        if a==0 or b==0:continue  # The two axis strips are the bounding box.
        if b<0:a,b,lo,hi=-a,-b,-hi,-lo
        oblique.append((a,b,lo,hi))
    sections=[]
    for x in events:
        lower,upper=bottom,top
        for a,b,lo,hi in oblique:
            ax=a*x
            lower=max(lower,-((ax-lo)//b))  # ceil((lo-a*x)/b)
            upper=min(upper,(hi-ax)//b)
            if lower>upper:break
        sections.append(None if lower>upper else (lower,upper))
    rectangles=[]
    for index,(a,b) in enumerate(zip(events,events[1:])):
        first,second=sections[index:index+2]
        if first is None or second is None:continue
        lower=max(first[0],second[0]);upper=min(first[1],second[1])
        if a>=b or lower>=upper:continue
        rectangle=(a,b,lower,upper)
        if verify_corners:
            require(all(lo<=nx*x+ny*y<=hi
                        for nx,ny,lo,hi in strips for x in (a,b) for y in (lower,upper)),
                    'A staircase corner is outside the majority polygon')
        if rectangles and rectangles[-1][1]==a and rectangles[-1][2:]==rectangle[2:]:
            rectangles[-1]=(rectangles[-1][0],b,lower,upper)
        else:rectangles.append(rectangle)
    return rectangles


def clip_axis(polygon,axis,bound,keep_high):
    """Exact closed clipping by one axis halfplane."""
    if not polygon:return []
    result=[]
    for p,q in zip(polygon,polygon[1:]+polygon[:1]):
        inside_p=p[axis]>=bound if keep_high else p[axis]<=bound
        inside_q=q[axis]>=bound if keep_high else q[axis]<=bound
        if inside_p:result.append(p)
        if inside_p!=inside_q:
            ratio=F(bound-p[axis])/F(q[axis]-p[axis])
            result.append(tuple(p[j]+ratio*(q[j]-p[j]) for j in range(2)))
    clean=[]
    for p in result:
        if not clean or clean[-1]!=p:clean.append(p)
    if len(clean)>1 and clean[0]==clean[-1]:clean.pop()
    return clean


def majority_rectangles_in_domain(points,half,domain,subdivisions=4,verify_corners=False,strips=None):
    """Rectangles which imply the majority charge ONLY inside the legal domain.

    The caller must supply a convex polygon in cyclic vertex order, as the
    current rotated-square caller does. Each slab drops exactly those feature halfplanes implied by the legal
    domain restricted to the slab and the feature's axis bounding box. Facet
    intersections with domain edges are x events, eliminating false wedges
    where a feature facet becomes redundant on the legal boundary. Coordinates
    remain exact rationals; there is no inward rounding gap.
    """
    require(type(subdivisions) is int and subdivisions>=1,'Positive subdivisions required')
    if strips is None:strips=median_strips(points,half)
    middle=len(points)//2
    umed=sorted(p[0] for p in points)[middle];vmed=sorted(p[1] for p in points)[middle]
    left,right=umed-half,umed+half;bottom,top=vmed-half,vmed+half
    restricted=[tuple(map(F,p)) for p in domain]
    for axis,bound,high in [(0,left,True),(0,right,False),(1,bottom,True),(1,top,False)]:
        restricted=clip_axis(restricted,axis,F(bound),high)
    if len(restricted)<3:return []
    area=sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(restricted,restricted[1:]+restricted[:1]))
    if not area:return []
    xmin=min(p[0] for p in restricted);xmax=max(p[0] for p in restricted)
    site_events=sorted({F(left),F(right)}|{F(u+sign*half) for u,v in points for sign in (-1,1)
                                        if left<u+sign*half<right})
    events={p[0] for p in restricted}
    for a,b in zip(site_events,site_events[1:]):
        for j in range(subdivisions+1):
            x=a+(b-a)*j/subdivisions
            if xmin<=x<=xmax:events.add(x)
    oblique=[]
    for a,b,lo,hi in strips:
        if not a or not b:continue
        if b<0:a,b,lo,hi=-a,-b,-hi,-lo
        oblique.append((a,b,lo,hi))
        for p,q in zip(restricted,restricted[1:]+restricted[:1]):
            vp=a*p[0]+b*p[1];vq=a*q[0]+b*q[1]
            for bound in (lo,hi):
                if (vp<bound<vq) or (vq<bound<vp):
                    ratio=F(bound-vp)/F(vq-vp)
                    events.add(p[0]+ratio*(q[0]-p[0]))
    events=sorted(events)
    sections=[]
    for x in events:
        ys=[]
        for p,q in zip(restricted,restricted[1:]+restricted[:1]):
            if p[0]==x:ys.append(p[1])
            if p[0]!=q[0] and min(p[0],q[0])<=x<=max(p[0],q[0]):
                ys.append(p[1]+F(x-p[0])/F(q[0]-p[0])*(q[1]-p[1]))
        require(ys,'Missing restricted-domain cross section')
        sections.append((min(ys),max(ys)))
    rectangles=[]
    for index,(left_x,right_x) in enumerate(zip(events,events[1:])):
        low_left,high_left=sections[index];low_right,high_right=sections[index+1]
        lower,upper=F(bottom),F(top)
        retained=[]
        for a,b,lo,hi in oblique:
            minimum=min(a*left_x+b*low_left,a*right_x+b*low_right)
            maximum=max(a*left_x+b*high_left,a*right_x+b*high_right)
            if minimum<lo:
                extreme=left_x if a>0 else right_x
                lower=max(lower,F(lo-a*extreme)/b)
                retained.append((-a,-b,-lo))
            if maximum>hi:
                extreme=right_x if a>0 else left_x
                upper=min(upper,F(hi-a*extreme)/b)
                retained.append((a,b,hi))
            if lower>=upper:break
        if left_x>=right_x or lower>=upper:continue
        rectangle=(left_x,right_x,lower,upper)
        if verify_corners:
            require(all(a*x+b*y<=rhs for a,b,rhs in retained
                        for x in (left_x,right_x) for y in (lower,upper)),
                    'Conditional staircase violates a retained halfplane')
            clipped=restricted
            for axis,bound,high in [(0,left_x,True),(0,right_x,False),(1,lower,True),(1,upper,False)]:
                clipped=clip_axis(clipped,axis,bound,high)
            require(all(lo<=a*x+b*y<=hi for a,b,lo,hi in strips for x,y in clipped),
                    'Conditional rectangle captures an invalid legal center')
        if rectangles and rectangles[-1][1]==left_x and rectangles[-1][2:]==rectangle[2:]:
            rectangles[-1]=(rectangles[-1][0],right_x,lower,upper)
        else:rectangles.append(rectangle)
    return rectangles
