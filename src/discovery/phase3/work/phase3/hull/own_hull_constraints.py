"""Independent necessary center cuts from a square's proved owned hull.

A unit-axis normal n has full-square support (B/2)(|n.u|+|n.v|).
We certify a rational upper bound over the whole angle interval by four
quadratic inequalities, independently of the producer's monotonicity proof.
Every p in the already proved owned hull must belong to the actual parent.
Consequently max_K n.p-E <= n.center <= min_K n.p+E.
"""
from rational import F
if not __debug__:raise RuntimeError('Assertions must be enabled')

def cs(t):return (1-t*t)/(1+t*t),2*t/(1+t*t)
def nonnegative_quadratic(c0,c1,c2,a,b):
    if min(c0+c1*a+c2*a*a,c0+c1*b+c2*b*b)<0:return False
    if c2>0 and c1+2*c2*a<0<c1+2*c2*b:return 4*c0*c2-c1*c1>=0
    return True

def support_bound_valid(n,E,a,b,B):
    x,y=n
    for sign1 in (-1,1):
        for sign2 in (-1,1):
            A=sign1*x+sign2*y;D=sign1*y-sign2*x
            if not nonnegative_quadratic(E-B*A/2,-B*D,E+B*A/2,a,b):return False
    return True

def necessary_cuts(owned,lo,hi,B):
    """Return four rational midpoint-axis cuts with a checked support bound."""
    a,b,B=F(lo),F(hi),F(B);assert 0<=a<=b<=1 and B>0
    K=[tuple(map(F,p)) for p in owned];assert K
    c,s=cs((a+b)/2);factors=[];narrow=True
    for t in (a,b):
        u,v=cs(t);dot=c*u+s*v;cross=c*v-s*u
        if not (dot>0 and dot>=abs(cross)):narrow=False
        factors.append(dot+abs(cross))
    E=B*(max(factors) if narrow else F(3,2))/2;result=[]
    for n in ((c,s),(-s,c)):
        assert support_bound_valid(n,E,a,b,B),'Endpoint proposal is not a universal full-square support bound'
        projections=[n[0]*x+n[1]*y for x,y in K]
        result.append(dict(normal=n,upper=min(projections)+E))
        result.append(dict(normal=(-n[0],-n[1]),upper=E-max(projections)))
    return result

def normalize(n,h):
    x,y=map(F,n);h=F(h);scale=abs(x) if x else abs(y);assert scale
    return x/scale,y/scale,h/scale

def validate_cuts(owned,lo,hi,B,supplied):
    expected=necessary_cuts(owned,lo,hi,B)
    got=[normalize(r['normal'],r['upper']) for r in supplied]
    want=[normalize(r['normal'],r['upper']) for r in expected]
    assert len(got)==len(want) and set(got)==set(want),'Recorded own-hull cuts differ from independently derived necessary cuts'
    return [(F(r['normal'][0]),F(r['normal'][1]),F(r['upper'])) for r in supplied]
