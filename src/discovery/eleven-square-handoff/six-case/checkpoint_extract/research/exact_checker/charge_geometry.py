"""Exact support-intersection predicates and Boolean Mobius coefficients."""
from itertools import combinations


def require(value,message):
    if not value:raise ValueError(message)


def orient(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def on_segment(p,a,b):
    return (orient(a,b,p)==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0])
            and min(a[1],b[1])<=p[1]<=max(a[1],b[1]))


def segments_intersect(a,b,c,d):
    ab_c,ab_d,cd_a,cd_b=orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)
    if ab_c*ab_d<0 and cd_a*cd_b<0:return True
    return ((ab_c==0 and on_segment(c,a,b)) or
            (ab_d==0 and on_segment(d,a,b)) or
            (cd_a==0 and on_segment(a,c,d)) or
            (cd_b==0 and on_segment(b,c,d)))


def convex_hull(points):
    points=sorted(set(points))
    if len(points)<=1:return points
    lower=[]
    for p in points:
        while len(lower)>=2 and orient(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    upper=[]
    for p in reversed(points):
        while len(upper)>=2 and orient(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def point_in_hull(point,hull):
    if len(hull)==1:return point==hull[0]
    if len(hull)==2:return on_segment(point,*hull)
    return all(orient(hull[i],hull[(i+1)%len(hull)],point)>=0
               for i in range(len(hull)))


def segment_hits_hull(a,b,hull):
    if len(hull)==1:return on_segment(hull[0],a,b)
    if len(hull)==2:return segments_intersect(a,b,*hull)
    if point_in_hull(a,hull) or point_in_hull(b,hull):return True
    return any(segments_intersect(a,b,hull[i],hull[(i+1)%len(hull)])
               for i in range(len(hull)))


def hulls_intersect(first,second):
    """Closed convex hull intersection, including points and collinear hulls."""
    require(bool(first) and bool(second),'Empty support hull')
    if len(first)==1:return point_in_hull(first[0],second)
    if len(second)==1:return point_in_hull(second[0],first)
    if len(first)==2:return segment_hits_hull(first[0],first[1],second)
    if len(second)==2:return segment_hits_hull(second[0],second[1],first)
    if point_in_hull(first[0],second) or point_in_hull(second[0],first):return True
    return any(segments_intersect(first[i],first[(i+1)%len(first)],
                                  second[j],second[(j+1)%len(second)])
               for i in range(len(first)) for j in range(len(second)))


def validate_support_clique(group,edges,threshold,points,supports=()):
    """Every support's convex hull meets every other support's convex hull.

    Supports comprise edges, optional pairs/triples, and every threshold subset.
    Threshold supports intersect combinatorially because 2*k>m. Explicit
    pairwise hull tests also cover the broader existing strict-majority schema.
    """
    if threshold is not None:
        require(2*threshold>len(group),'Threshold supports need strict majority')
    edge_pair_checks=0;edge_hull_checks=0
    for first,second in combinations(edges,2):
        require(segments_intersect(points[first[0]],points[first[1]],
                                   points[second[0]],points[second[1]]),
                'Disjoint feature segments invalidate unit budget')
        edge_pair_checks+=1
    if threshold is not None:
        for edge in edges:
            complement=[i for i in group if i not in edge]
            for subset in combinations(complement,threshold):
                hull=convex_hull([points[i] for i in subset])
                require(segment_hits_hull(points[edge[0]],points[edge[1]],hull),
                        'Segment misses a disjoint threshold-support hull')
                edge_hull_checks+=1
    all_supports=[tuple(edge) for edge in edges]+[tuple(support) for support in supports]
    hull_cache={}
    def hull(indices):
        key=tuple(sorted(indices))
        if key not in hull_cache:hull_cache[key]=convex_hull([points[i] for i in key])
        return hull_cache[key]
    for i,first in enumerate(all_supports):
        for j in range(max(i+1,len(edges)),len(all_supports)):
            second=all_supports[j]
            if set(first).intersection(second):continue
            require(hulls_intersect(hull(first),hull(second)),
                    'Disjoint support hulls invalidate unit budget')
            edge_pair_checks+=1
    if threshold is not None:
        for support in supports:
            complement=[i for i in group if i not in support]
            for subset in combinations(complement,threshold):
                require(hulls_intersect(hull(support),hull(subset)),
                        'Support hull misses a disjoint threshold-support hull')
                edge_hull_checks+=1
    return edge_pair_checks,edge_hull_checks


def clique_coefficients(n,local_edges,threshold=None,local_supports=()):
    """Mobius coefficients indexed by capture-subset bitmask, not its size."""
    require(1<=n<=7,'Support size must be at most seven')
    edge_masks=[(1<<i)|(1<<j) for i,j in local_edges]
    edge_masks.extend(sum(1<<i for i in support) for support in local_supports)
    values=[int((threshold is not None and mask.bit_count()>=threshold)
                or any(mask & edge == edge for edge in edge_masks))
            for mask in range(1<<n)]
    coefficients=values.copy()
    for i in range(n):
        bit=1<<i
        for mask in range(1<<n):
            if mask & bit:coefficients[mask]-=coefficients[mask^bit]
    return tuple(coefficients)
