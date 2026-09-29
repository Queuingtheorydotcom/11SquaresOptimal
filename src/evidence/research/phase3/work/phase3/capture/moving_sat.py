"""Exact inner collision cores for two independently rotating STRICT squares.

The caller binds I,J to complete angle half-tangent intervals and b strictly
below actual parent side B.  A d in this region implies the two strict squares
intersect for EVERY angle pair, hence the actual parent interiors overlap.
No owned-point or pose-cover antecedent is established by this module.
"""
from gmpy2 import mpq as F
from functools import lru_cache
from pathlib import Path
import sys
if not __debug__:raise RuntimeError('Assertions must be enabled')
sys.path.insert(0,str(Path(__file__).parent/'gmp'))
import fast_convex_v2 as geo

def cs(t):
 t=F(t);return (1-t*t)/(1+t*t),2*t/(1+t*t)
def qmin(a,b,c,lo,hi):
 vals=[a+b*lo+c*lo*lo,a+b*hi+c*hi*hi]
 if c>0 and lo < -b/(2*c) < hi:vals.append(a-b*b/(4*c))
 return min(vals)
def trig_nonnegative(R,A,D,lo,hi):
 return qmin(R-A,-2*D,R+A,lo,hi)>=0

def moving_axis_checks(d,I,J,b):
 """All separating axes attached to I, with every partner angle in J."""
 dx,dy=d;lo,hi=I;jlo,jhi=J
 for tj in (jlo,jhi):
  cj,sj=cs(tj)
  for a,z,sgn in ((lo,min(hi,tj),1),(max(lo,tj),hi,-1)):
   if a>z:continue
   fx,fy=cj+sgn*sj,sj-sgn*cj
   for sign in (-1,1):
    yield trig_nonnegative(b/2,sign*dx-b*fx/2,sign*dy-b*fy/2,a,z)
    yield trig_nonnegative(b/2,sign*dy-b*fx/2,-sign*dx-b*fy/2,a,z)
 a,z=max(lo,jlo),min(hi,jhi)
 if a<=z:
  for sign in (-1,1):
   yield trig_nonnegative(b,sign*dx,sign*dy,a,z)
   yield trig_nonnegative(b,sign*dy,-sign*dx,a,z)

def universal_overlap(d,I,J,b):
 I=tuple(map(F,I));J=tuple(map(F,J));b=F(b);d=tuple(map(F,d))
 assert b>0 and 0<=I[0]<=I[1]<=1 and 0<=J[0]<=J[1]<=1
 return all(moving_axis_checks(d,I,J,b)) and all(moving_axis_checks((-d[0],-d[1]),J,I,b))

def square(t,b):
 c,s=cs(t);h=b/2
 return [(h*(c*x-s*y),h*(s*x+c*y)) for x,y in ((-1,-1),(1,-1),(1,1),(-1,1))]

@lru_cache(maxsize=100000)
def relative_core(I,J,b,bits=18):
 I=tuple(map(F,I));J=tuple(map(F,J));b=F(b)
 result=[(-2*b,-2*b),(2*b,-2*b),(2*b,2*b),(-2*b,2*b)]
 for ti in I:
  for tj in J:
   p=geo.hull([(x-u,y-v) for x,y in square(tj,b) for u,v in square(ti,b)])
   for n,h in geo.rows(p):result=geo.clip_linear(result,n,h)
 certified=[];scales=[]
 for p in result:
  if universal_overlap(p,I,J,b):scale=F(1)
  else:
   lo,hi=0,2**bits
   while hi-lo>1:
    mid=(lo+hi)//2;q=tuple(x*F(mid,2**bits) for x in p)
    if universal_overlap(q,I,J,b):lo=mid
    else:hi=mid
   scale=F(lo,2**bits)
  q=tuple(x*scale for x in p);assert universal_overlap(q,I,J,b)
  certified.append(q);scales.append(scale)
 return dict(vertices=geo.hull(certified),outer_proposal=result,vertex_scales=scales,
             interval_i=I,interval_j=J,strict_side=b,status='CERTIFIED_INNER_MOVING_SAT_CORE')

def fixed_sat(d,ti,tj,b):
 ci,si=cs(ti);cj,sj=cs(tj);dot=ci*cj+si*sj;cross=ci*sj-si*cj
 support=b*(1+dot+abs(cross))/2
 return all(abs(n[0]*d[0]+n[1]*d[1])<=support for n in ((ci,si),(-si,ci),(cj,sj),(-sj,cj)))

def controls():
 import random,time
 rng=random.Random(7361);start=time.monotonic();count=0
 for ti in (F(0),F(1,7),F(2,5),F(1)):
  for tj in (F(0),F(1,4),F(3,5),F(1)):
   for _ in range(50):
    d=tuple(F(rng.randrange(-200,201),100) for _ in range(2))
    assert universal_overlap(d,(ti,ti),(tj,tj),F(1))==fixed_sat(d,ti,tj,F(1));count+=1
 for I,J in (((F(0),F(1)),(F(0),F(1))),((F(23,64),F(24,64)),(F(0),F(1,64))),((F(0),F(1,496)),(F(363,1000),F(368,1000)))):
  ans=relative_core(I,J,F(1));assert ans['vertices']
  for p in ans['vertices']:
   assert universal_overlap(p,I,J,F(1))
   for i in range(17):
    for j in range(17):
     assert fixed_sat(p,I[0]+(I[1]-I[0])*F(i,16),J[0]+(J[1]-J[0])*F(j,16),F(1));count+=1
 # Exact touching is allowed for strict squares, but arbitrarily outside is not.
 assert universal_overlap((F(1),F(0)),(F(0),F(0)),(F(0),F(0)),F(1))
 assert not universal_overlap((F(1)+F(1,10**50),F(0)),(F(0),F(0)),(F(0),F(0)),F(1))
 return dict(status='PASS',checks=count+2,seconds=time.monotonic()-start)
if __name__=='__main__':
 import json
 print(json.dumps(controls(),indent=2))
