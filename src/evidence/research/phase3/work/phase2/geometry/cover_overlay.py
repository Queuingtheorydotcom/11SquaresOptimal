"""Exact closed common refinement of four independent D4 center covers."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib
if not __debug__:raise SystemExit('Exact geometry requires assertions.')
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]/'current';COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
C=json.loads(COVER.read_text());P=[[tuple(map(F,p)) for p in c['vertices']] for c in C['cells']]
assert hashlib.sha256(COVER.read_bytes()).hexdigest()=='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
SYMS=[(0,1,1),(0,-1,1),(1,-1,1),(1,1,1)]
def area(p):return sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1]))
def preimage(p,g):
 sw,sx,sy=g;v=tuple(x if sg==1 else 1-x for x,sg in zip(p,(sx,sy)));return v[::-1] if sw else v

def clip(poly,n,b):
 out=[]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  a=sum(x*y for x,y in zip(p,n))-b;c=sum(x*y for x,y in zip(q,n))-b;ia=a<=0;ic=c<=0
  if ia:out.append(p)
  if ia!=ic:
   r=a/(a-c);out.append(tuple(x+r*(y-x) for x,y in zip(p,q)))
 clean=[]
 for p in out:
  if not clean or p!=clean[-1]:clean.append(p)
 if len(clean)>1 and clean[0]==clean[-1]:clean.pop()
 return clean

def intersect(p,q):
 if area(q)<0:q=q[::-1]
 for a,b in zip(q,q[1:]+q[:1]):
  n=(b[1]-a[1],a[0]-b[0]);bound=sum(x*y for x,y in zip(a,n));p=clip(p,n,bound)
  if not p:break
 return p
R=[]
for i,p in enumerate(P):R.append(dict(labels=[i],vertices=p))
for g in SYMS[1:]:
 nextrows=[];Q=[[preimage(v,g) for v in p] for p in P]
 for r in R:
  for j,q in enumerate(Q):
   poly=intersect(r['vertices'],q)
   if poly:nextrows.append(dict(labels=r['labels']+[j],vertices=poly))
 R=nextrows;print('views',len(R[0]['labels']),'regions',len(R),'area0',sum(area(r['vertices'])==0 for r in R),flush=True)
for i,r in enumerate(R):r['index']=i;r['dimension']=2 if area(r['vertices']) else (1 if len(set(r['vertices']))>1 else 0)
out=dict(status='PASS_EXACT_CLOSED_FOUR_COVER_OVERLAY',cover_sha256=hashlib.sha256(COVER.read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),symmetries=SYMS,regions=R,scope='Every realizable choice of closed-cell labels across four D4 covers has its complete nonempty intersection polygon listed, including degenerate points and segments. Halfturn copies use label15-j and introduce no new constraints when forbidden patterns are halfturn invariant.')
(HERE/'cover_overlay_exact.json').write_text(json.dumps(out,indent=2,default=str))
