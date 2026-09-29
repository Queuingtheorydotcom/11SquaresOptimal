#!/usr/bin/env python3
"""Exact physical charge atoms for any independently proved convex strict core.

Coordinates are global field coordinates; Q is the core relative to the parent
center. This module builds charge regions only. The caller must separately
prove strict containment of Q for every parent orientation in the row, field
capacities, all-angle domain coverage, and any conditional ownership premise.
"""
from fractions import Fraction as F
from itertools import combinations
import hashlib,json
from pathlib import Path
import independent_weighted_cover as weighted
from independent_patch_cover import primitive
if not __debug__:raise RuntimeError('Assertions must remain enabled')
def exact(x):
 if isinstance(x,float):raise TypeError('Approximate coordinates are forbidden')
 if hasattr(x,'numerator') and hasattr(x,'denominator'):return F(int(x.numerator),int(x.denominator))
 return F(x)
def points(P):return [tuple(exact(x) for x in p) for p in P]
def rows_of_polygon(P):
 P=weighted.convex_hull(points(P));assert weighted.area2(P)>0
 return [(q[1]-p[1],p[0]-q[0],(q[1]-p[1])*p[0]+(p[0]-q[0])*p[1]) for p,q in zip(P,P[1:]+P[:1])]
def negative_core_rows(Q):return rows_of_polygon([(-x,-y) for x,y in points(Q)])
def subset_capture_rows(P,Q):
 P=points(P);assert P
 return [(a,b,h+min(a*x+b*y for x,y in P)) for a,b,h in negative_core_rows(Q)]
def true_capture_rows(P,Q):
 P=points(P);Q=weighted.convex_hull(points(Q));assert len(P)%2 and weighted.area2(Q)>0
 normals=set()
 for a,b,h in negative_core_rows(Q):
  n=primitive(a,b);normals.add(n);normals.add((-n[0],-n[1]))
 for p,q in combinations(P,2):
  a,b=q[1]-p[1],p[0]-q[0]
  if a or b:
   n=primitive(a,b);normals.add(n);normals.add((-n[0],-n[1]))
 middle=len(P)//2
 return [(a,b,sorted(a*x+b*y for x,y in P)[middle]-min(a*x+b*y for x,y in Q)) for a,b in sorted(normals)]
def row_atoms(packet,Q,cell=None,extra_forbidden_polygons=()):
 Q=points(Q);assert weighted.area2(weighted.convex_hull(Q))>0
 cert=packet['certificate'];D=cert['coordinate_denominator'];P=[tuple(F(v,D) for v in p) for p in cert['sites']];atoms=[]
 for p,w in zip(P,cert['point_weights']):
  if w:atoms.append(('point',[subset_capture_rows([p],Q)],w))
 for feature in cert['features']:
  G=[P[i] for i in feature['indices']];k=feature['threshold'];w=feature['weight'];kind=feature['kind']
  if not w:continue
  if kind=='majority_hull':
   assert len(G)==2*k-1;atoms.append(('TRUE',[true_capture_rows(G,Q)],w))
  elif kind in ('threshold','floor'):
   levels=[k] if kind=='threshold' else range(k,len(G)+1,k)
   for level in levels:atoms.append((kind,[subset_capture_rows(S,Q) for S in combinations(G,level)],w))
  else:raise ValueError('Unknown physical feature')
 if cell is not None:
  gamma=packet['threshold_units'][cell]
  for owner in packet.get('conditional_owner_support',[]):
   if owner!=cell:
    for p in packet['ownership_points_field'][owner]:atoms.append(('owned_point',[subset_capture_rows([p],Q)],gamma))
  for P in extra_forbidden_polygons:atoms.append(('conditional_owned_hull',[rows_of_polygon(P)],gamma))
 elif extra_forbidden_polygons:raise ValueError('A cell threshold is required for forbidden-region atoms')
 return atoms

def normalized(rows):
 out=set()
 for a,b,c in rows:
  a,b,c=exact(a),exact(b),exact(c);scale=abs(a) if a else abs(b);out.add((a/scale,b/scale,c/scale))
 return out
def contains(rows,p):return all(a*p[0]+b*p[1]<=h for a,b,h in rows)
def controls():
 Q=[(F(1),-F(1,2)),(F(2),-F(1,2)),(F(2),F(1,2)),(F(1),F(1,2))]
 R=subset_capture_rows([(0,0)],Q)
 assert contains(R,(-F(3,2),0)) and not contains(R,(F(3,2),0))
 assert contains(R,(-1,F(1,2))) and not contains(R,(-1+F(1,10**50),0))
 assert normalized(R)==normalized(true_capture_rows([(0,0)],Q))
 collinear=[(0,0),(1,0),(2,0)]
 assert normalized(true_capture_rows(collinear,Q))==normalized(subset_capture_rows([(1,0)],Q))
 for P in [[(F(0),F(0)),(F(1),F(0)),(F(0),F(1))],[(F(i,7),F((i*i+2)%11,9)) for i in range(5)]]:
  for half in (F(1,5),F(3,2)):
   square=[(-half,-half),(half,-half),(half,half),(-half,half)]
   assert normalized(true_capture_rows(P,square))==normalized(weighted.true_rows(P,half))
 # Translation of the query core translates every admissible center oppositely.
 shift=(F(7,13),-F(5,17));P=[(F(0),F(0)),(F(1),F(0)),(F(0),F(1))]
 base=true_capture_rows(P,Q);moved=true_capture_rows(P,[(x+shift[0],y+shift[1]) for x,y in Q])
 assert normalized(moved)==normalized([(a,b,h-a*shift[0]-b*shift[1]) for a,b,h in base])
 return dict(status='PASS_INDEPENDENT_GENERAL_CORE_ATOM_CONTROLS',checks=9)
if __name__=='__main__':
 result=controls();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 result.update(checker_sha256=sha(__file__),weighted_cover_sha256=sha(weighted.__file__),scope='Exact atom geometry and sign controls only; no standalone mask exclusion.')
 Path(__file__).with_name('polygon-core-atom-controls.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
