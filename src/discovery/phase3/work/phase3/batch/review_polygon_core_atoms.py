"""Source review controls using literal Minkowski polygons, retaining points."""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import hashlib,json,random,sys,time
HERE=Path(__file__).resolve().parent;AUDIT=HERE.parent/'audit';sys.path.insert(0,str(AUDIT))
import independent_polygon_core_atoms as a
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_sha=sha(a.__file__)
def cross(p,q,r):return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
def hull(P):
 P=sorted(set(P))
 if len(P)<=1:return P
 def half(P):
  ans=[]
  for p in P:
   while len(ans)>1 and cross(ans[-2],ans[-1],p)<=0:ans.pop()
   ans.append(p)
  return ans
 return half(P)[:-1]+half(P[::-1])[:-1]
def normalize(rows):
 d={}
 for x,y,z in rows:
  scale=abs(x) if x else abs(y);n=(x/scale,y/scale);z/=scale
  d[n]=min(z,d.get(n,z))
 return [(x,y,z) for (x,y),z in d.items()]
def literal(P,Q):
 rows=[];k=(len(P)+1)//2
 for S in combinations(P,k):
  V=hull([(px-qx,py-qy) for px,py in S for qx,qy in Q])
  assert len(V)>=3
  for p,q in zip(V,V[1:]+V[:1]):
   x,y=q[1]-p[1],p[0]-q[0];rows.append((x,y,x*p[0]+y*p[1]))
 return normalize(rows)
def vertices(rows):
 out=set()
 for (a,b,c),(d,e,f) in combinations(rows,2):
  det=a*e-b*d
  if not det:continue
  x,y=(c*e-b*f)/det,(a*f-c*d)/det
  if all(u*x+v*y<=w for u,v,w in rows):out.add((x,y))
 return out
def dimension(V):
 if not V:return -1
 if len(V)==1:return 0
 P=list(V)
 return 2 if any(cross(P[0],P[1],p) for p in P[2:]) else 1
start=time.monotonic();records=[]
def check(P,Q,label):
 direct=vertices(normalize(a.true_capture_rows(P,Q)));oracle=vertices(literal(P,Q))
 assert direct==oracle,(label,direct,oracle)
 records.append(dict(label=label,sites=len(P),core_vertices=len(Q),dimension=dimension(direct),vertices=len(direct)))
shift=(F(7,13),-F(5,17));triangle=[(F(0),F(0)),(F(1),F(0)),(F(0),F(1))]
for delta in [-F(1,10**10),F(0),F(1,10**10)]:
 h=F(1,4)+delta;Q=[(x+shift[0],y+shift[1]) for x,y in [(-h,-h),(h,-h),(h,h),(-h,h)]]
 check(triangle,Q,'translated_square_critical_'+str(delta))
assert [r['dimension'] for r in records]==[-1,0,2]
rng=random.Random(270926)
for case in range(24):
 m=[1,3,5,7][case%4];P=[]
 while len(P)<m:
  p=(F(rng.randrange(-8,9),5),F(rng.randrange(-8,9),7))
  if p not in P:P.append(p)
 Q=[]
 while len(Q)<3:
  Q=hull([(F(rng.randrange(-12,13),[3,5,9][case%3])+shift[0],F(rng.randrange(-10,11),[4,7,11][case%3])+shift[1]) for _ in range(7)])
 check(P,Q,'random_asymmetric_'+str(case))
assert source_sha==sha(a.__file__),'source changed during review'
out=dict(status='PASS_LITERAL_POLYGON_CORE_SOURCE_REVIEW',atom_builder_sha256=source_sha,reviewer_sha256=sha(__file__),controls_file_sha256=sha(AUDIT/'audit_polygon_core_true_controls.py'),cases=records,seconds=time.monotonic()-start,mathematical_review=dict(TRUE='For every k-subset S, z lies in conv(S)+(-Q). Its support inequality is n.z <= max(n.p for p in S)-min(n.q for q in Q). The minimum of the maxima over all k-subsets is the kth order statistic, the median for 2k-1 sites. Each Minkowski polygon facet comes from a subset-hull edge or a -Q edge; site-pair normals and -Q facet normals therefore form a complete finite set.',subset_capture='Capturing every site in S is z in intersection_{p in S}(p-Q), giving n.z <= min(n.p for p in S)-min(n.q for q in Q).',boundary='The literal vertex oracle retains zero-dimensional intersections. A translated critical square yields empty, singleton, and positive-area regions on three consecutive exact side lengths.',union_and_floor='One threshold union is one weighted atom; floor(count/k) decomposes into indicators count>=k,2k,... . The existing weighted atom evaluator counts overlap once within each union.',caller_contract='Q must already be proved a convex strict core in global coordinates relative to the parent center. extra_forbidden_polygons are already forbidden CENTER regions; this builder does not derive those regions from spatial owned hulls. Capacity, domain and conditional premises remain caller obligations.'),global_optimality_proved=False)
(HERE/'polygon-core-source-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(status=out['status'],cases=len(records),dimensions={str(d):sum(r['dimension']==d for r in records) for d in [-1,0,1,2]},seconds=out['seconds'],atom_builder_sha256=source_sha)))
