"""Fast proposals; exact universal moving-SAT validation is authoritative."""
import math
from functools import lru_cache
import moving_sat as exact
F=exact.F;geo=exact.geo

def affine_quadratics(d,I,J,b):
 def one(d,I,J):
  dx,dy=d;lo,hi=I;jlo,jhi=J
  for tj in (jlo,jhi):
   cj,sj=exact.cs(tj)
   for a,z,sgn in ((lo,min(hi,tj),1),(max(lo,tj),hi,-1)):
    if a>z:continue
    fx,fy=cj+sgn*sj,sj-sgn*cj
    A,D=-b*fx/2,-b*fy/2;R=b/2
    const=(R-A,-2*D,R+A)
    for sign in (-1,1):
     for Ad,Dd in ((sign*dx,sign*dy),(sign*dy,-sign*dx)):
      yield const,(-Ad,-2*Dd,Ad),a,z
  a,z=max(lo,jlo),min(hi,jhi)
  if a<=z:
   for sign in (-1,1):
    for Ad,Dd in ((sign*dx,sign*dy),(sign*dy,-sign*dx)):
     yield (b,F(0),b),(-Ad,-2*Dd,Ad),a,z
 yield from one(d,I,J)
 yield from one((-d[0],-d[1]),J,I)

def suggested_scale(d,I,J,b):
 out=1.0
 for n,w,a,z in affine_quadratics(d,I,J,b):
  n=list(map(float,n));v=[-float(x) for x in w];a,z=float(a),float(z)
  pts=[a,z];A=n[2]*v[1]-n[1]*v[2];B=2*(n[2]*v[0]-n[0]*v[2]);C=n[1]*v[0]-n[0]*v[1]
  if abs(A)<1e-25:
   if abs(B)>1e-25:pts.append(-C/B)
  else:
   disc=B*B-4*A*C
   if disc>=0:
    rt=math.sqrt(disc);pts.extend(((-B-rt)/(2*A),(-B+rt)/(2*A)))
  for t in pts:
   if not a<=t<=z:continue
   den=v[0]+t*(v[1]+t*v[2])
   if den>0:out=min(out,(n[0]+t*(n[1]+t*n[2]))/den)
 return max(0,min(1,out))

@lru_cache(maxsize=100000)
def relative_core(I,J,b,bits=18):
 I=tuple(map(F,I));J=tuple(map(F,J));b=F(b)
 result=[(-2*b,-2*b),(2*b,-2*b),(2*b,2*b),(-2*b,2*b)]
 for ti in I:
  for tj in J:
   p=geo.hull([(x-u,y-v) for x,y in exact.square(tj,b) for u,v in exact.square(ti,b)])
   for n,h in geo.rows(p):result=geo.clip_linear(result,n,h)
 certified=[];scales=[];tries=0
 for p in result:
  den=2**bits;num=min(den,max(0,math.floor(suggested_scale(p,I,J,b)*den)))
  decrement=1
  while True:
   scale=F(num,den);q=tuple(x*scale for x in p);tries+=1
   if exact.universal_overlap(q,I,J,b):break
   num=max(0,num-decrement);decrement*=2
  certified.append(q);scales.append(scale)
 return dict(vertices=geo.hull(certified),outer_proposal=result,vertex_scales=scales,
             interval_i=I,interval_j=J,strict_side=b,exact_validation_calls=tries,
             status='CERTIFIED_INNER_MOVING_SAT_CORE')

if __name__=='__main__':
 import json,time,random
 rng=random.Random(2634);start=time.monotonic();tests=0
 for _ in range(100):
  I=sorted((F(rng.randrange(65),64),F(rng.randrange(65),64)));J=sorted((F(rng.randrange(65),64),F(rng.randrange(65),64)))
  result=relative_core(tuple(I),tuple(J),F(1));assert all(exact.universal_overlap(p,I,J,F(1)) for p in result['vertices']);tests+=1
 print(json.dumps(dict(status='PASS',random_interval_pairs=tests,seconds=time.monotonic()-start)))
