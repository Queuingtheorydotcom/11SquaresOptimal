#!/usr/bin/env python3
"""Source-distinct strict polygon-core audit via exact quadratic positivity.

The positivity checker uses endpoint derivatives and the completed-square
numerator, without importing the producer stationary-point evaluator.
"""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[1]
sys.path.insert(0,str(WORK/'phase2/audit'))
from independent_patch_cover import convex_hull,area2

def need(v,s):
 if not v:raise ValueError(s)
def positive_quadratic(c0,c1,c2,a,b):
 a,b=F(a),F(b)
 qa=c0+c1*a+c2*a*a;qb=c0+c1*b+c2*b*b
 if min(qa,qb)<=0:return False
 if c2>0 and c1+2*c2*a<0<c1+2*c2*b:
  return 4*c0*c2-c1*c1>0
 return True

def vertex_inside(point,a,b,B):
 x,y=map(F,point);B=F(B);a,b=F(a),F(b)
 need(0<=a<b<=1 and B>0,'invalid interval/side')
 polynomials=[]
 for sign in (-1,1):
  polynomials.extend([(B/2-sign*x,-2*sign*y,B/2+sign*x),
                      (B/2-sign*y,2*sign*x,B/2+sign*y)])
 return all(positive_quadratic(*q,a,b) for q in polynomials)

def audit_vertices(vertices,a,b,U):
 V=[tuple(map(F,p)) for p in vertices];H=convex_hull(V);B=F(191,50)/F(U)
 need(area2(H)>0,'degenerate core')
 need(set(V)==set(H) and len(V)==len(H),'reported core contains nonvertex or duplicate points')
 need(all(vertex_inside(v,a,b,B) for v in V),'a core vertex escapes an actual parent')
 return H

def facet_ownership(core,residual,halfplanes):
 H=convex_hull([tuple(map(F,p)) for p in core]);R=[tuple(map(F,p)) for p in residual]
 need(R and area2(H)>0,'missing residual or core geometry')
 expected=[]
 for p,q in zip(H,H[1:]+H[:1]):
  n=(q[1]-p[1],p[0]-q[0]);h=n[0]*p[0]+n[1]*p[1]
  expected.append((n,h+min(n[0]*v[0]+n[1]*v[1] for v in R)))
 def normalized(n,b):
  scale=next(abs(x) for x in n if x);return tuple(x/scale for x in n)+(b/scale,)
 need({normalized(n,b) for n,b in expected}=={normalized(tuple(map(F,n)),F(b)) for n,b in halfplanes},'common-core facets differ')
 return True

def controls():
 need(positive_quadratic(F(1),F(-1),F(1),0,1),'positive interior minimum rejected')
 need(not positive_quadratic(F(1,4),F(-1),F(1),0,1),'interior tangent incorrectly strict')
 need(not positive_quadratic(F(1,4)-F(1,10**50),F(-1),F(1),0,1),'tiny negative interior minimum missed')
 need(positive_quadratic(F(1,4)+F(1,10**50),F(-1),F(1),0,1),'tiny positive interior minimum rejected')
 need(not positive_quadratic(F(1),F(0),F(-1),0,1),'endpoint zero incorrectly strict')
 need(vertex_inside((0,0),0,1,1),'center rejected')
 need(not vertex_inside((F(1,2),0),0,F(1,4),1),'parent edge contact incorrectly strict')
 return 7

def main():
 sys.path.insert(0,str(WORK/'phase3/core'));import polygon_core as producer
 U=F(387708359002281417731,10**20);rows=[]
 intervals=[(F(0),F(1)),(F(0),F(1,2)),(F(1,2),F(1))]+[(F(i,64),F(i+1,64)) for i in range(64)]
 for a,b in intervals:
  r=producer.polygon_core(a,b,U);H=audit_vertices(r['vertices'],a,b,U)
  need(all(producer.validate_vertex(p,a,b,F(191,50)/U)['passed']==vertex_inside(p,a,b,F(191,50)/U) for p in H),'producer vertex result differs')
  R=[(F(1),F(1)),(F(5,4),F(1)),(F(5,4),F(6,5))]
  facet_ownership(H,R,producer.ownership_halfplanes(R,r['vertices']))
  rows.append(dict(interval=[str(a),str(b)],vertices=len(H),strict_vertex_checks=len(H)))
 out=dict(status='PASS_INDEPENDENT_STRICT_POLYGON_CORE_AUDIT',checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  producer_sha256=hashlib.sha256(Path(producer.__file__).read_bytes()).hexdigest(),controls=controls(),intervals=rows,
  statement='Every tested produced core vertex lies strictly inside every side-B parent square over its complete angle interval. Independent facet reconstruction agrees with the common-core ownership halfplanes.',
  global_optimality_proved=False,scope='Exact polygon-core/control validation only; no mask exclusion or ownership antecedent is established here.')
 (HERE/'polygon-core-independent-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='intervals'},indent=2))
if __name__=='__main__':main()
