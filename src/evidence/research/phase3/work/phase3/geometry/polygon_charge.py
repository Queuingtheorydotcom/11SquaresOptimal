"""Exact nonnegative physical charge arrangements for arbitrary convex cores.

TRUE capture uses the median support inequalities for all support-pair and
core facet normals. Threshold unions are counted once per logical atom.
"""
from pathlib import Path
import sys,math
from itertools import combinations
if not __debug__:raise RuntimeError('Assertions must be enabled')
WORK=Path(__file__).resolve().parents[2];sys.path.insert(0,str(WORK/'phase3/deps'));sys.path.insert(0,str(WORK/'phase3/capture/gmp'))
from gmpy2 import mpq as F
import fast_convex_v2 as geo
def dot(n,p):return n[0]*p[0]+n[1]*p[1]
def primitive(n):
 a,b=map(F,n);x=int(a.numerator)*int(b.denominator);y=int(b.numerator)*int(a.denominator);d=math.gcd(abs(x),abs(y));return (x//d,y//d) if d else None
def intersect(P,Q):
 for n,h in geo.rows(Q):
  P=geo.clip_linear(P,n,h)
  if not P:return []
 return P
def atom_regions(cert,Q,domain):
 D=cert['coordinate_denominator'];sites=[tuple(F(x,D) for x in p) for p in cert['sites']];minus=[(-x,-y) for x,y in Q];pointregions=[[(p[0]+q[0],p[1]+q[1]) for q in minus] for p in sites];atoms=[]
 for p,w in zip(pointregions,cert['point_weights']):
  if w:atoms.append(('point',[p],w))
 core_normals={primitive(n) for n,h in geo.rows(minus)}
 for f in cert['features']:
  w=f['weight'];ids=f['indices'];k=f['threshold'];kind=f['kind']
  if not w:continue
  if kind=='majority_hull':
   assert len(ids)==2*k-1
   points=[sites[j] for j in ids];normals=set(core_normals)
   for a,b in combinations(points,2):
    n=primitive((b[1]-a[1],a[0]-b[0]))
    if n:normals.add(n);normals.add((-n[0],-n[1]))
   P=list(domain)
   for n in normals:
    h=sorted(dot(n,p) for p in points)[k-1]-min(dot(n,q) for q in Q);P=geo.clip_linear(P,n,h)
    if not P:break
   if geo.twice_area(P)>0:atoms.append(('TRUE',[P],w))
  elif kind in ('threshold','floor'):
   for level in ([k] if kind=='threshold' else range(k,len(ids)+1,k)):
    regions=[]
    for group in combinations(ids,level):
     P=list(domain)
     for j in group:
      P=intersect(P,pointregions[j])
      if not P:break
     if geo.twice_area(P)>0:regions.append(P)
    if regions:atoms.append((kind,regions,w))
  else:raise ValueError('Unsupported physical feature')
 return atoms
def cover(domain,atoms,threshold,max_pieces=20000):
 assert isinstance(threshold,int) and threshold>=0
 if not domain:return dict(status='PASS_EMPTY',passed=True,remaining_pieces=0)
 if geo.twice_area(domain)==0:return dict(status='UNRESOLVED_DEGENERATE',passed=False)
 if not threshold:return dict(status='PASS_NONNEGATIVE',passed=True,remaining_pieces=0)
 prepared=[]
 for kind,regions,w in atoms:
  assert isinstance(w,int) and w>=0
  clipped=[intersect(domain,R) for R in regions];clipped=[P for P in clipped if geo.twice_area(P)>0]
  if clipped:prepared.append((min(w,threshold)*sum(geo.twice_area(P) for P in clipped),kind,clipped,w))
 prepared.sort(key=lambda x:x[0],reverse=True);pieces=[(domain,0)];peak=1;used=0
 for _,kind,regions,w in prepared:
  nextpieces=[]
  for P,charge in pieces:
   outside=[P]
   for R in regions:
    nextoutside=[]
    for S in outside:
     inside=intersect(S,R)
     if geo.twice_area(inside)>0:
      if charge+w<threshold:nextpieces.append((inside,charge+w))
      nextoutside.extend(geo.convex_difference(S,R))
     else:nextoutside.append(S)
    outside=nextoutside
    if not outside:break
   nextpieces.extend((P,charge) for P in outside)
  pieces=nextpieces;used+=1;peak=max(peak,len(pieces))
  if not pieces:break
  if len(pieces)>max_pieces:return dict(passed=False,status='UNRESOLVED_WEIGHTED_PIECE_BUDGET',maximum_pieces=peak,atoms_used=used)
 answer=dict(passed=not pieces,status='PASS_POLYGON_PHYSICAL_CHARGE' if not pieces else 'UNRESOLVED_POLYGON_LOW_CHARGE',maximum_pieces=peak,atoms_used=used,remaining_pieces=len(pieces))
 if pieces:
  P,q=min(pieces,key=lambda x:x[1]);answer.update(low_charge_units=q,low_charge_center=[sum(p[k] for p in P)/len(P) for k in (0,1)])
 return answer
def verify(cert,Q,domain,threshold,max_pieces=20000):
 Q=geo.hull(Q);domain=geo.hull(domain);return cover(domain,atom_regions(cert,Q,domain),threshold,max_pieces)
def controls():
 Q=[(F(-1,2),F(-1,2)),(F(1,2),F(-1,2)),(F(1,2),F(1,2)),(F(-1,2),F(1,2))];domain=[(F(-1,4),F(-1,4)),(F(1,4),F(-1,4)),(F(1,4),F(1,4)),(F(-1,4),F(1,4))]
 assert cover(domain,[('union',[Q,Q],1)],1)['passed']
 assert not cover(domain,[('union',[Q,Q],1)],2)['passed']
 cert=dict(coordinate_denominator=10,sites=[[-1,0],[0,0],[1,0]],point_weights=[0,0,0],features=[dict(kind='majority_hull',indices=[0,1,2],threshold=2,weight=1)])
 assert verify(cert,Q,domain,1)['passed'] and not verify(cert,Q,domain,2)['passed']
 cert['features']=[dict(kind='floor',indices=[0,1,2],threshold=1,weight=1)]
 assert verify(cert,Q,domain,3)['passed'];return dict(status='PASS_POLYGON_CHARGE_CONTROLS',checks=5)
if __name__=='__main__':print(controls())
