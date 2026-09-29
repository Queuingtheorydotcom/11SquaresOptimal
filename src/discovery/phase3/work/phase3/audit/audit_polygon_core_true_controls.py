#!/usr/bin/env python3
"""Compare polygon TRUE atoms with their literal majority-subset definition."""
from pathlib import Path
from itertools import combinations
from fractions import Fraction as F
import json,hashlib
import independent_polygon_core_atoms as a
w=a.weighted
D=[(-F(10),-F(10)),(F(10),-F(10)),(F(10),F(10)),(-F(10),F(10))]
P=[(F(0),F(0)),(F(1),F(0)),(F(0),F(1)),(F(2,3),F(5,7)),(F(1,5),F(3,4))]
cores=[[(F(0),F(0)),(F(3),F(0)),(F(0),F(2))],[(F(1,9),F(1,7)),(F(2,9),F(1,7)),(F(1,9),F(2,7))]]
results=[]
for Q in cores:
 literal=D[:]
 for S in combinations(P,3):
  M=w.convex_hull([(p[0]-q[0],p[1]-q[1]) for p in S for q in Q])
  literal=w.intersection(literal,a.rows_of_polygon(M))
  if not literal:break
 direct=w.intersection(D,a.true_capture_rows(P,Q))
 assert set(w.convex_hull(literal))==set(w.convex_hull(direct))
 results.append(dict(core_vertices=[[str(x) for x in p] for p in Q],literal_area_twice=str(w.area2(literal)),direct_area_twice=str(w.area2(direct))))
assert w.area2(w.intersection(D,a.true_capture_rows(P,cores[0])))>0
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=dict(status='PASS_LITERAL_POLYGON_TRUE_SUBSET_EQUIVALENCE',checker_sha256=sha(__file__),atom_builder_sha256=sha(a.__file__),weighted_geometry_sha256=sha(w.__file__),cases=results,scope='Two nonrectangular asymmetric query-core controls compare the median-support formula to all ten explicit majority-subset Minkowski polygons, including a positive-area region and an empty region.')
Path(__file__).with_name('polygon-core-literal-TRUE-controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
