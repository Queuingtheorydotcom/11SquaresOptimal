"""Square-specific captured-support conflicts from exact centroid variance.

No production checker is modified. These predicates certify new finite
captured-support rules; they do not assert that TRUE-majority OR support has
budget one.
"""
from fractions import Fraction as F
from itertools import combinations
from math import isqrt


def require(ok,message):
    if not ok:raise ValueError(message)


def sqrt_upper(value,denominator=10**15):
    value=F(value);require(value>=0,'Negative square root')
    n=value.numerator*denominator*denominator;d=value.denominator
    root=isqrt(n//d)
    if root*root*d<n:root+=1
    answer=F(root,denominator)
    require(answer*answer>=value,'Invalid square-root upper bound')
    return answer


def moment(points,weights=None):
    points=[tuple(map(F,p)) for p in points];require(points,'Empty support')
    if weights is None:weights=[F(1,len(points))]*len(points)
    weights=list(map(F,weights));require(len(weights)==len(points),'Weight count differs')
    require(all(w>=0 for w in weights) and sum(weights)==1,'Invalid convex weights')
    center=tuple(sum(w*p[j] for w,p in zip(weights,points)) for j in range(2))
    variance=sum(w*sum((p[j]-center[j])**2 for j in range(2)) for w,p in zip(weights,points))
    return center,variance


def disk_witness(first,second,A,first_weights=None,second_weights=None):
    """Return an exact sufficient conflict certificate, or None if inconclusive."""
    A=F(A);require(A>0,'Nonpositive maximum square side')
    m,v=moment(first,first_weights);n,w=moment(second,second_weights)
    if v>A*A/2:return {'kind':'impossible_first','variance':v,'A':A}
    if w>A*A/2:return {'kind':'impossible_second','variance':w,'A':A}
    distance2=sum((x-y)**2 for x,y in zip(m,n))
    bound=sqrt_upper(distance2)+sqrt_upper(A*A/2-v)+sqrt_upper(A*A/2-w)
    if bound<A:
        return {'kind':'variance_disks','A':A,'first_mean':m,'second_mean':n,
                'first_variance':v,'second_variance':w,'distance_squared':distance2,
                'first_radius_squared':A*A/2-v,'second_radius_squared':A*A/2-w,
                'sum_upper':bound,'strict_margin':A-bound}
    return None


def subset_disk_witness(first,second,A,max_arity=None):
    """Search unweighted subsets; every returned witness is checked rationally."""
    first,second=list(first),list(second)
    a=len(first) if max_arity is None else min(max_arity,len(first))
    b=len(second) if max_arity is None else min(max_arity,len(second))
    for n in range(a,0,-1):
        for ii in combinations(range(len(first)),n):
            for m in range(b,0,-1):
                for jj in combinations(range(len(second)),m):
                    result=disk_witness([first[i] for i in ii],[second[j] for j in jj],A)
                    if result is not None:
                        return dict(result,first_subset=list(ii),second_subset=list(jj))
    return None
