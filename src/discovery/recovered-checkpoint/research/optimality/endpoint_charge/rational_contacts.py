"""Exact rational lines/points incident to algebraic Trump endpoint poses.

Diagnostic source geometry only. Does not certify endpoint coverage.
"""
import sys,json,time
from pathlib import Path
import sympy as sp
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/construction'))
from verify_trump import E,u,configuration,M,I

def coeffs(z):return [z.p.nth(k) for k in range(8)]
def relation(*zs):
    a=sp.Matrix.hstack(*(sp.Matrix(coeffs(z)) for z in zs))
    out=[]
    for v in a.nullspace():
        d=sp.ilcm(*[x.q for x in v]);v=[int(x*d) for x in v];g=sp.igcd(*v);v=[x//g for x in v]
        if next(x for x in v if x)<0:v=[-x for x in v]
        out.append(v)
    return {'rank':a.rank(),'nullspace':out}

def main():
    start=time.time();assert M.is_irreducible and M.count_roots(*I)==1
    squares,alpha,axes=configuration(E(u));A=E(sp.Rational(191,50))/alpha
    out=[]
    for i,sq in enumerate(squares):
        vs=[(A*x,A*y) for x,y in sq]
        edge=[]
        for j in range(4):
            p,q=vs[j],vs[(j+1)%4];nx,ny=-(q[1]-p[1]),q[0]-p[0]
            intercept=-(nx*p[0]+ny*p[1])
            edge.append({'edge':j,'rational_point_equation':relation(nx,ny,intercept)})
        corners=[{'vertex':j,'rational_line_equation':relation(p[0],p[1],E(1))} for j,p in enumerate(vs)]
        out.append({'square':i,'edges':edge,'vertices':corners})
    result={'status':'EXACT_RATIONAL_INCIDENCE_CLASSIFICATION','scope':'Rational points on each support edge and rational lines through each vertex, for scaled exact Trump construction. Nullspace gives all rational incidence triples, not edge segment membership.','L':'191/50','minimal_polynomial':str(M.as_expr()),'squares':out,'elapsed_seconds':time.time()-start}
    dest=Path(__file__).with_name('rational-contact-classification.json');dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
