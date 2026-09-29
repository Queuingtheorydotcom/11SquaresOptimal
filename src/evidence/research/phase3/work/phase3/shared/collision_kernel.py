"""Exact universal collision regions for complete, certified partner pose covers.

For every partner row (strict common core Q and an OUTER center polygon D),
intersect all translates c + Q - query_core, c in D.  Their intersection over
every partner row is forbidden to the query center.  Closed intersection is
safe because both cores must lie strictly inside their parent squares.

This module does not certify input pose covers or strict cores.  The caller
must bind those antecedents to already proved rows.  A returned region is an
additional exclusion, never a replacement for older owned-hull exclusions.
"""
from gmpy2 import mpq as F
from math import gcd
from functools import lru_cache

if not __debug__:
    raise RuntimeError('Assertions must remain enabled')

def dot(n,p):
    return n[0]*p[0]+n[1]*p[1]

def primitive(n):
    a,b=map(F,n)
    x=int(a.numerator)*int(b.denominator)
    y=int(b.numerator)*int(a.denominator)
    d=gcd(abs(x),abs(y))
    assert d
    return x//d,y//d

def polygon(p):
    return tuple(tuple(map(F,q)) for q in p)

def twice_signed_area(p):
    return sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1]))

@lru_cache(maxsize=40000)
def normals(p):
    assert len(p)>=3 and twice_signed_area(p)>0
    return tuple(dict.fromkeys(primitive((q[1]-r[1],r[0]-q[0]))
                              for r,q in zip(p,p[1:]+p[:1]) if r!=q))

@lru_cache(maxsize=300000)
def support(p,n):
    return max(dot(n,x) for x in p)

def clip(p,n,b):
    """Exact clipping, preserving points and line segments."""
    if not p:return []
    values=[dot(n,x)-b for x in p]
    if max(values)<=0:return p
    if min(values)>0:return []
    result=[]
    for k,(x,y) in enumerate(zip(p,p[1:]+p[:1])):
        a,z=values[k],values[(k+1)%len(p)]
        if a<=0:result.append(x)
        if (a<=0)!=(z<=0):
            t=a/(a-z)
            result.append((x[0]+t*(y[0]-x[0]),x[1]+t*(y[1]-x[1])))
    clean=[]
    for x in result:
        if not clean or x!=clean[-1]:clean.append(x)
    if len(clean)>1 and clean[-1]==clean[0]:clean.pop()
    return clean

class PartnerCover:
    """Reusable halfplanes for one complete partner pose cover.

    Each input row has keys core, domain and optionally reference.  Empty
    domains are impossible poses and may be omitted.  An entirely empty cover
    means the antecedents themselves are inconsistent, recorded explicitly.
    """
    def __init__(self,rows):
        self.rows=[]
        self.facet_bounds={}
        self.query_bounds={}
        self.input_row_count=len(rows)
        self.facet_instances=0
        for row in rows:
            d=polygon(row['domain'])
            if not d:continue
            q=polygon(row['core'])
            ns=normals(q)
            self.rows.append((q,d,row.get('reference')))
            for n in ns:
                b=support(q,n)+min(dot(n,c) for c in d)
                self.facet_bounds[n]=min(self.facet_bounds.get(n,b),b)
                self.facet_instances+=1

    def free_bound(self,n):
        if n not in self.query_bounds:
            assert self.rows
            self.query_bounds[n]=min(support(q,n)+min(dot(n,c) for c in d)
                                     for q,d,_ in self.rows)
        return self.query_bounds[n]

    def kernel(self,query_core,query_domain):
        """Return exact intersection restricted to the supplied query domain."""
        p=list(polygon(query_domain));q=polygon(query_core)
        # Require a genuine positively oriented core even for empty domains.
        qnormals=normals(q)
        if not self.rows:
            return dict(vertices=p,status='EMPTY_PARTNER_COVER',
                        input_rows=self.input_row_count,live_rows=0,
                        checked_constraints=0)
        minus=tuple((-x,-y) for x,y in q)
        checked=0
        # These four universally valid support constraints reject distant
        # partners before constructing query-dependent facet bounds.
        for n in ((1,0),(-1,0),(0,1),(0,-1)):
            p=clip(p,n,self.free_bound(n)+support(minus,n));checked+=1
            if not p:break
        total=len(self.facet_bounds)+len(qnormals)+4
        if not p:
            return dict(vertices=[],status='EXACT_UNIVERSAL_COLLISION_KERNEL',
                        input_rows=self.input_row_count,live_rows=len(self.rows),
                        total_constraints=total,checked_constraints=checked)
        # Lazy support evaluation makes an early empty intersection cheap.
        for n,b in self.facet_bounds.items():
            p=clip(p,n,b+support(minus,n));checked+=1
            if not p:break
        for n0 in qnormals:
            if not p:break
            n=(-n0[0],-n0[1])
            b=self.free_bound(n)+support(minus,n)
            p=clip(p,n,b);checked+=1
        return dict(vertices=p,status='EXACT_UNIVERSAL_COLLISION_KERNEL',
                    input_rows=self.input_row_count,live_rows=len(self.rows),
                    total_constraints=total,
                    checked_constraints=checked)

def controls():
    q=polygon([(-1,-1),(1,-1),(1,1),(-1,1)])
    domain=polygon([(-5,-5),(5,-5),(5,5),(-5,5)])
    fixed=PartnerCover([dict(core=q,domain=[(0,0)])])
    k=fixed.kernel(q,domain)['vertices']
    assert set(k)==set(polygon([(-2,-2),(2,-2),(2,2),(-2,2)]))
    moving=PartnerCover([dict(core=q,domain=[(-1,0),(1,0)])])
    k=moving.kernel(q,domain)['vertices']
    assert set(k)==set(polygon([(-1,-2),(1,-2),(1,2),(-1,2)]))
    two=PartnerCover([dict(core=q,domain=[(-2,0)]),dict(core=q,domain=[(2,0)])])
    k=two.kernel(q,domain)['vertices']
    assert set(k)==set(polygon([(0,-2),(0,2)]))
    assert clip([(F(0),F(0))],(1,0),0)==[(F(0),F(0))]
    assert clip([(F(0),F(0))],(1,0),-1)==[]
    return dict(status='PASS',checks=5)

if __name__=='__main__':
    print(controls())
