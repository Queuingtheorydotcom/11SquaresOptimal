"""Exact orientation-polygon test for fitting finite sites in a rotated square.

Research helper only: no production checker imports this module.
"""
from fractions import Fraction as F
from itertools import combinations


def need(ok,message):
    if not ok:raise ValueError(message)


def clip(poly,a,b,c):
    """Intersect a rational convex polygon with ax+by<=c."""
    out=[]
    for first,second in zip(poly,poly[1:]+poly[:1]):
        f=a*first[0]+b*first[1]-c;g=a*second[0]+b*second[1]-c
        if f<=0:out.append(first)
        if (f<0<g) or (g<0<f):
            t=f/(f-g)
            out.append(tuple(first[j]+t*(second[j]-first[j]) for j in range(2)))
    compact=[]
    for p in out:
        if not compact or p!=compact[-1]:compact.append(p)
    if len(compact)>1 and compact[0]==compact[-1]:compact.pop()
    return compact


def fit_certificate(points,A):
    A=F(A);need(A>0,'side must be positive')
    points=sorted(set(tuple(map(F,p)) for p in points));need(points,'empty support')
    normals=set()
    for p,q in combinations(points,2):
        x,y=p[0]-q[0],p[1]-q[1]
        normals.update(((x,y),(-x,-y),(-y,x),(y,-x)))
    if not normals:
        return dict(kind='singleton_or_identical',A=A,fits=True,unit_direction=(F(1),F(0)))
    x,y=next(iter(sorted(normals)));norm=x*x+y*y
    # Invert the first pair's orthogonal projection map; no artificial box.
    poly=[((x*s-y*t)/norm,(y*s+x*t)/norm)
          for s,t in ((-A,-A),(A,-A),(A,A),(-A,A))]
    for a,b in sorted(normals):poly=clip(poly,a,b,A)
    need(len(poly)>=3,'positive-side orientation body must have interior')
    for p in poly:
        need(all(a*p[0]+b*p[1]<=A for a,b in normals),'vertex violates strip')
    maximum=max(x*x+y*y for x,y in poly)
    return dict(kind='bounded_orientation_polygon',A=A,fits=maximum>=1,
                normal_count=len(normals),vertices=poly,maximum_squared_radius=maximum,
                maximizing_vertex=next(p for p in poly if p[0]*p[0]+p[1]*p[1]==maximum))


def fits_square(points,A):
    return fit_certificate(points,A)['fits']
