#!/usr/bin/env python3
"""Independent exact feasibility and one-parameter-family minimum for Trump 11.

Requires SymPy. No upstream implementation is imported. All decisive tests use
rational arithmetic, polynomial remainders and certified isolating intervals.
Formula provenance: David Ellsworth's Squares in Squares catalogue; also
https://github.com/jlevy/squares/blob/main/packing/cases/trump11/packing.py

This is NOT a global optimality proof, nor a full 33-dimensional local proof.
"""
from __future__ import annotations
import json
import argparse
from functools import lru_cache
from itertools import combinations
from pathlib import Path
import sympy as sp

if not __debug__:
    raise SystemExit('Run without -O: exact verification assertions must remain enabled.')

u, s = sp.symbols('u s')
M = sp.Poly(5*u**8-10*u**7-2*u**6+14*u**5+12*u**4-6*u**3+2*u**2+2*u-1,u,domain=sp.QQ)
P = sp.Poly(s**8-20*s**7+178*s**6-842*s**5+1923*s**4-496*s**3-6754*s**2+12420*s-6865,s)
I = (sp.Rational(36,100),sp.Rational(37,100))


def interval_product(a,b):
    vals=[x*y for x in a for y in b]
    return min(vals),max(vals)


def polynomial_interval(poly, ab):
    z=(sp.S.Zero,sp.S.Zero)
    for a in sp.Poly(poly,u).all_coeffs():
        z=interval_product(z,ab); z=(z[0]+a,z[1]+a)
    return z


def rational_interval(expr,ab):
    num,den=sp.fraction(sp.cancel(expr))
    n=polynomial_interval(num,ab); d=polynomial_interval(den,ab)
    if d[0]<=0<=d[1]: return None
    return interval_product(n,(1/d[1],1/d[0]))


def strictly_positive_on(expr,ab=I,depth=0):
    """Rational interval subdivision; all accepted conclusions are exact."""
    expr=sp.cancel(expr)
    bounds=rational_interval(expr,ab)
    if bounds is not None and bounds[0]>0: return
    if depth>=18: raise AssertionError(('could not establish positive',expr,ab,bounds))
    mid=sum(ab)/2
    strictly_positive_on(expr,(ab[0],mid),depth+1)
    strictly_positive_on(expr,(mid,ab[1]),depth+1)


def nonnegative_on(expr):
    expr=sp.cancel(expr)
    if expr!=0: strictly_positive_on(expr)


class E:
    """An element of Q[u]/(M), with exact sign at the isolated real root."""
    root_interval=I
    refinements=0
    def __init__(self, x=0):
        self.p=x.p if isinstance(x,E) else sp.Poly(x,u,domain=sp.QQ).rem(M)
    def __add__(self,b): return E(self.p+E(b).p)
    __radd__=__add__
    def __neg__(self): return E(-self.p)
    def __sub__(self,b): return self+-E(b)
    def __rsub__(self,b): return E(b)+-self
    def __mul__(self,b): return E(self.p*E(b).p)
    __rmul__=__mul__
    def __truediv__(self,b): return E(self.p*sp.invert(E(b).p,M))
    def __rtruediv__(self,b): return E(b)/self
    def __pow__(self,k):
        assert k>=0
        a=E(1)
        for _ in range(k): a=a*self
        return a
    def iszero(self): return self.p.is_zero
    def sign(self):
        if self.iszero(): return 0
        while True:
            lo,hi=polynomial_interval(self.p,E.root_interval)
            if lo>0: return 1
            if hi<0: return -1
            a,b=E.root_interval; mid=(a+b)/2
            if M.eval(a)*M.eval(mid)<0: E.root_interval=(a,mid)
            else: E.root_interval=(mid,b)
            E.refinements+=1
    def __lt__(self,b): return (self-E(b)).sign()<0
    def __le__(self,b): return (self-E(b)).sign()<=0
    def decimal(self): return str(sp.N(self.p.as_expr().subs(u,sp.CRootOf(M,1)),45))


def configuration(t):
    """Works for either rational functions or the exact number-field class."""
    c=(1-t*t)/(1+t*t); d=2*t/(1+t*t)
    L=(6*t+4)/(1+2*t-t*t)
    r=1-(L-3)*c; b=((1+r)*c-1)/d
    v=c-d; w=(L-1)/d-r-(3+b)*c/d
    x=1+2/c-(L-2)*d/c
    axis_origins=[(0,0),(L-1,0),(x,L-1),(0,L-1),(1,L-1),(0,L-2)]
    tilt_origins=[(0,0),(b,-1),(1,v),(b+1,v-1),(b+2,-w)]
    offsets=[(0,0),(1,0),(1,1),(0,1)]
    squares=[[(t*0+x+dx,t*0+y+dy) for dx,dy in offsets] for x,y in axis_origins]
    squares.extend([[(1+c*(x+dx)-d*(y+dy-r),1+d*(x+dx)+c*(y+dy-r)) for dx,dy in offsets] for x,y in tilt_origins])
    return squares,L,[(t*0+1,t*0),(t*0,t*0+1),(c,d),(-d,c)]


def dot(a,b): return a[0]*b[0]+a[1]*b[1]


def verify_exact():
    assert M.is_irreducible
    assert M.count_roots(*I)==1
    assert M.count_roots(0,sp.oo)==1
    assert M.count_roots(-sp.oo,0)==1
    assert M.eval(I[0])<0<M.eval(I[1])
    squares,L,axes=configuration(E(u))
    walls=0
    for square in squares:
        edges=[(square[(k+1)%4][0]-square[k][0],square[(k+1)%4][1]-square[k][1]) for k in range(4)]
        for k in range(4):
            assert (dot(edges[k],edges[k])-1).iszero()
            assert dot(edges[k],edges[(k+1)%4]).iszero()
        for x,y in square:
            for v in [x,y,L-x,L-y]:
                assert v.sign()>=0
                walls+=v.iszero()
    witnesses=[]; touching=0
    for i,j in combinations(range(11),2):
        possible=[]
        for k,axis in enumerate(axes):
            a=[dot(p,axis) for p in squares[i]]; b=[dot(p,axis) for p in squares[j]]
            for direction,gap in [(1,min(b)-max(a)),(-1,min(a)-max(b))]:
                if gap.sign()>=0: possible.append((gap.sign(),k,direction,gap))
        assert possible,('overlap',i,j)
        sign,k,direction,gap=max(possible,key=lambda x:x[0])
        touching+=sign==0
        witnesses.append({'pair':[i,j],'axis_index':k,'direction':direction,'gap_sign':sign,'gap_coefficients':[str(x) for x in gap.p.all_coeffs()]})
    side_identity=E(0)
    for a in P.all_coeffs(): side_identity=side_identity*L+int(a)
    assert side_identity.iszero()
    assert P.is_irreducible and P.count_roots(0,sp.oo)==1
    lower=sp.Rational(387708359002281417730789706010096270637645566846,10**47)
    upper=lower+sp.Rational(1,10**47)
    assert (L-lower).sign()>0 and (upper-L).sign()>0
    return {'valid':True,'square_count':11,'pairs_checked':55,'contact_pairs':touching,'strictly_separated_pairs':55-touching,'boundary_corner_coordinates':walls,'side_lower':str(lower),'side_upper':str(upper),'side_decimal':L.decimal(),'algebraic_degree':8,'sign_interval_refinements':E.refinements,'separation_witnesses':witnesses}


def verify_family_minimum():
    """Certify minimum in this explicitly parametrized family, t in [0.36,0.37]."""
    squares,L,axes=configuration(u)
    a,b=squares[2],squares[10]
    candidate=None; excluded=0
    mid=sum(I)/2
    for axis_index,axis in enumerate(axes):
        A=[sp.cancel(dot(p,axis)) for p in a]; B=[sp.cancel(dot(p,axis)) for p in b]
        index=lambda vals,fn: fn(range(4),key=lambda j: vals[j].subs(u,mid))
        amin,amax=index(A,min),index(A,max); bmin,bmax=index(B,min),index(B,max)
        for vals,low,high in [(A,amin,amax),(B,bmin,bmax)]:
            for val in vals:
                nonnegative_on(val-vals[low]); nonnegative_on(vals[high]-val)
        for direction,gap in [(1,B[bmin]-A[amax]),(-1,A[amin]-B[bmax])]:
            gap=sp.cancel(gap)
            if sp.rem(sp.Poly(sp.fraction(gap)[0],u),M)==0 and gap!=0:
                assert candidate is None
                candidate=(axis_index,direction,gap)
                strictly_positive_on(gap/M.as_expr())
            else:
                strictly_positive_on(-gap); excluded+=1
    assert excluded==7 and candidate is not None
    strictly_positive_on(sp.diff(M.as_expr(),u))
    strictly_positive_on(sp.diff(L,u))
    # M increases through its sole root u*. SAT for squares 2 and 10 forces
    # candidate gap >= 0, hence u >= u*. Since L increases, L(u) >= L(u*).
    return {'proved':True,'scope':'Only configuration(t) for 36/100 <= t <= 37/100','necessary_gap_axis_index':candidate[0],'necessary_gap_direction':candidate[1],'necessary_gap':str(sp.factor(candidate[2])),'alternative_directed_separators_excluded':excluded,'M_strictly_increasing':True,'side_strictly_increasing':True,'global_optimality_proved':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('trump-verification.json'))
    args=parser.parse_args()
    report={'construction':verify_exact(),'family_minimum':verify_family_minimum()}
    destination=args.output
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:{a:b for a,b in v.items() if a!='separation_witnesses'} for k,v in report.items()},indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
