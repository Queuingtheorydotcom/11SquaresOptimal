"""Exact closed-cell compatibility under all eight square symmetries."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib
if not __debug__:raise SystemExit('Exact checker requires assertions.')
ROOT=Path(__file__).resolve().parents[3]/'current'
COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
EXPECTED='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
assert hashlib.sha256(COVER.read_bytes()).hexdigest()==EXPECTED
C=json.loads(COVER.read_text());P=[[tuple(map(F,p)) for p in c['vertices']] for c in C['cells']]
def dot(p,n):return sum(x*y for x,y in zip(p,n))
def intersection(p,q):
 for a,b in list(zip(p,p[1:]+p[:1]))+list(zip(q,q[1:]+q[:1])):
  n=(b[1]-a[1],a[0]-b[0]);pp=[dot(v,n) for v in p];qq=[dot(v,n) for v in q]
  if max(pp)<min(qq) or max(qq)<min(pp):return False
 return True
out=[]
for swap in (0,1):
 for sx in (-1,1):
  for sy in (-1,1):
   def transform(p):
    v=p[::-1] if swap else p
    return tuple(x if sg==1 else 1-x for x,sg in zip(v,(sx,sy)))
   TP=[[transform(v) for v in p] for p in P]
   edges=[[j for j,q in enumerate(P) if intersection(p,q)] for p in TP]
   out.append(dict(swap=swap,sx=sx,sy=sy,edges=edges,edge_masks=[sum(1<<j for j in e) for e in edges],edge_count=sum(map(len,edges))))
   print(swap,sx,sy,'edges',out[-1]['edge_count'], 'degrees',[len(e) for e in edges])
HERE=Path(__file__).resolve().parent
(HERE/'cover_d4_intersections.json').write_text(json.dumps(dict(status='PASS_EXACT_CLOSED_POLYGON_INTERSECTION_RELATION',cover_sha256=EXPECTED,checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),symmetries=out),indent=2))
patterns=[[1,2,4,5,6,7,11],[1,2,4,5,8,9,13]];patterns +=[[15-i for i in p] for p in patterns[:]]
with (HERE/'matching_input.txt').open('w') as f:
 f.write(f'{len(out)} {len(C["canonical_eleven_cell_subsets"])} {len(patterns)}\n')
 for p in patterns:f.write(str(sum(1<<j for j in p))+'\n')
 for r in out:f.write(' '.join(map(str,r['edge_masks']))+'\n')
 for m in C['canonical_eleven_cell_subsets']:f.write(str(sum(1<<j for j in m))+'\n')
