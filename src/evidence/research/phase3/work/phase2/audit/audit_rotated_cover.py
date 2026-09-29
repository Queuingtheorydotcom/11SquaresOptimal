#!/usr/bin/env python3
"""Independent exact closed-cell D4 relation audit by half-plane vertices.

No producer separating-axis code is imported. A bounded nonempty intersection
of closed polygons has a feasible vertex: enumerate all pairs of boundary
lines, retaining exact feasible intersections. Point/segment contacts remain.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations,product
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]/'current'
sys.path.insert(0,str(ROOT/'research/optimality/audit'))
from audit_center_cover import audit as audit_cover,hull
COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def transform(p,g):
 x,y=p
 if g[0]:x,y=y,x
 return (x if g[1]==1 else 1-x,y if g[2]==1 else 1-y)
def halfplanes(poly):
 out=[]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  a=q[1]-p[1];b=p[0]-q[0];c=a*p[0]+b*p[1]
  need(a or b,'repeated polygon vertex')
  out.append((a,b,c))
 return out
def intersection_vertex(P,Q):
 # Strict inequality excludes; equality must retain closed contacts.
 if any(max(p[k] for p in P)<min(q[k] for q in Q) or max(q[k] for q in Q)<min(p[k] for p in P) for k in (0,1)):return None
 rows=halfplanes(P)+halfplanes(Q)
 for x,y in P+Q:
  if all(a*x+b*y<=c for a,b,c in rows):return (x,y)
 for (a,b,c),(d,e,f) in combinations(rows,2):
  det=a*e-b*d
  if not det:continue
  x=(c*e-b*f)/det;y=(a*f-c*d)/det
  if all(u*x+v*y<=w for u,v,w in rows):return (x,y)
 return None

def controls():
 square=lambda x0,y0,x1,y1:[(F(x0),F(y0)),(F(x1),F(y0)),(F(x1),F(y1)),(F(x0),F(y1))]
 P=square(0,0,1,1);eps=F(1,10**50)
 tests=[('point contact',square(1,1,2,2),True),('segment contact',square(1,0,2,1),True),
 ('strict tiny gap',square(1+eps,0,2,1),False),('strict tiny overlap',square(1-eps,0,2,1),True),
 ('containment',square(F(1,4),F(1,4),F(3,4),F(3,4)),True),
 ('crossing without contained vertices',[(F(-1),F(2,5)),(F(2,5),F(-1)),(F(2),F(3,5)),(F(3,5),F(2))],True)]
 for name,Q,expected in tests:need((intersection_vertex(P,hull(Q)) is not None)==expected,'failed '+name)
 return [name for name,Q,expected in tests]

def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('producer',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 producer=json.loads(args.producer.read_text());cover=json.loads(COVER.read_text());geometry=audit_cover(COVER)
 need(producer['cover_sha256']==sha(COVER),'producer cover hash mismatch')
 cells=[hull([tuple(map(F,p)) for p in c['vertices']]) for c in cover['cells']]
 syms={(r['swap'],r['sx'],r['sy']):r for r in producer['symmetries']}
 expected=set(product((0,1),(-1,1),(-1,1)));need(set(syms)==expected and len(producer['symmetries'])==8,'wrong D4 maps')
 rows=[];edgecount=0;point_contacts=0
 for g in sorted(expected):
  src=syms[g];edges=[];witnesses=[]
  for i,P in enumerate(cells):
   GP=hull([transform(p,g) for p in P]);row=[]
   for j,Q in enumerate(cells):
    w=intersection_vertex(GP,Q)
    if w is not None:
     row.append(j);witnesses.append(dict(source=i,target=j,point=list(map(str,w))))
   edges.append(row)
  need(edges==src['edges'],'closed graph differs at symmetry '+str(g))
  masks=[sum(1<<j for j in row) for row in edges]
  need(masks==src['edge_masks'],'edge mask encoding differs')
  n=sum(map(len,edges));need(n==src['edge_count'],'edge count differs');edgecount+=n
  rows.append(dict(swap=g[0],sx=g[1],sy=g[2],edges=edges,edge_masks=masks,edge_count=n,feasible_intersection_vertices=witnesses))
 out=dict(status='PASS_INDEPENDENT_EXACT_D4_CLOSED_INTERSECTION_AUDIT',checker_sha256=sha(Path(__file__)),
  producer_sha256=sha(args.producer),producer_checker_sha256=producer['checker_sha256'],cover_sha256=sha(COVER),
  method='Exhaustive feasible intersections of polygon boundary-line pairs; strict bounding-box rejection; no separating-axis producer imported.',
  controls=controls(),symmetries=rows,cell_pairs_checked=8*16*16,total_directed_edges=edgecount,
  masks_excluded_by_this_audit=0,global_optimality_proved=False,
  scope='Certifies only the necessary closed-cell source-to-transformed-target relation. Every packing induces an injective matching; graph edges alone exclude no packing.')
 args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='symmetries'},indent=2))
if __name__=='__main__':main()
