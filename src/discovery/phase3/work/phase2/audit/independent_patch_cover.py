#!/usr/bin/env python3
"""Independent threshold-one row coverage by exact polygon subtraction.

Build TRUE regions directly from median halfplanes and point-capture boxes in
rational unit edge axes. Cover the entire legal cell envelope, without calling
the producer staircase, low-cell extractor, patcher, or feature precomputation.
"""
from fractions import Fraction as F
from itertools import combinations
from math import gcd,lcm

def need(v,s):
 if not v:raise ValueError(s)
def area2(P):return abs(sum(x*v-y*u for (x,y),(u,v) in zip(P,P[1:]+P[:1]))) if len(P)>=3 else F(0)
def clean(P):
 out=[]
 for p in P:
  if not out or out[-1]!=p:out.append(p)
 if len(out)>1 and out[-1]==out[0]:out.pop()
 return out
def convex_hull(P):
 points=sorted(set(P))
 def half(seq):
  out=[]
  for p in seq:
   while len(out)>1:
    a,b=out[-2:]
    cross=(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    if cross>0:break
    out.pop()
   out.append(p)
  return out
 return half(points)[:-1]+half(points[::-1])[:-1]

def clip(P,line):
 if not P:return []
 a,b,c=line;out=[]
 for p,q in zip(P,P[1:]+P[:1]):
  dp=a*p[0]+b*p[1]-c;dq=a*q[0]+b*q[1]-c
  if dp<=0:out.append(p)
  if (dp<=0)!=(dq<=0):
   z=dp/(dp-dq);out.append(tuple(p[k]+z*(q[k]-p[k]) for k in range(2)))
 return clean(out)
def intersection(P,rows):
 for line in rows:
  P=clip(P,line)
  if not area2(P):return []
 return P
def subtract(P,rows):
 """Return convex pieces whose interiors partition P minus the closed region."""
 inside=P;outside=[]
 for a,b,c in rows:
  out=clip(inside,(-a,-b,-c))
  if area2(out):outside.append(out)
  inside=clip(inside,(a,b,c))
  if not area2(inside):break
 return outside

def primitive(a,b):
 D=lcm(a.denominator,b.denominator);A=int(a*D);B=int(b*D);g=gcd(abs(A),abs(B))
 need(g>0,'zero normal');A//=g;B//=g
 if A<0 or (A==0 and B<0):A=-A;B=-B
 return F(A),F(B)
def true_rows(points,half):
 normals={(F(1),F(0)),(F(0),F(1))}
 for p,q in combinations(points,2):
  a=q[1]-p[1];b=p[0]-q[0]
  if a or b:normals.add(primitive(a,b))
 rows=[];m=len(points)//2
 for a,b in sorted(normals):
  median=sorted(a*x+b*y for x,y in points)[m];h=half*(abs(a)+abs(b))
  rows.extend([(a,b,median+h),(-a,-b,-median+h)])
 return rows

def controls():
 P=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
 rect=lambda a,b:[(F(1),F(0),b),(F(-1),F(0),-a),(F(0),F(1),F(1)),(F(0),F(-1),F(0))]
 left=subtract(P,rect(F(0),F(1,2)))
 need(sum(map(area2,left))==1,'half-square subtraction failed')
 need(not [Q for R in left for Q in subtract(R,rect(F(1,2),F(1)))],'closed shared boundary not covered')
 eps=F(1,10**50)
 gap=[Q for R in left for Q in subtract(R,rect(F(1,2)+eps,F(1)))]
 need(sum(map(area2,gap))==2*eps,'tiny positive gap silently lost')
 need(subtract(P,rect(F(2),F(3)))==[P],'disjoint region changed domain')
 need(not subtract(P,rect(F(-1),F(2))),'containing region failed')
 # A collinear odd support has its median point as the intersection of all
 # majority subset hulls, so TRUE is exactly the median capture rectangle.
 points=[(F(0),F(0)),(F(1),F(0)),(F(2),F(0))]
 rows=true_rows(points,F(1,2))
 need(area2(intersection(P,rows))==F(1,2),'collinear median feature differs from exact capture box')
 return ['exact half-square area','closed shared boundary','10^-50 positive gap retained',
         'disjoint and containing regions','collinear majority median capture']

def verify_row(packet,cover,row):
 i=row['cell'];gamma=packet['threshold_units'][i];need(gamma==1,'independent patch union supports only threshold one')
 U=F(packet['parent_Uplus']);L=F(191,50);B=L/U;core=F(row['core_side']);H=F(row['parent_center_halfwidth']);t=F(row['reference_half_angle'])
 c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);half=core/2
 rotate=lambda p:(c*(p[0]-L/2)+s*(p[1]-L/2),-s*(p[0]-L/2)+c*(p[1]-L/2))
 world=convex_hull([tuple(L/2+B*(U-1)*(F(v)-F(1,2)) for v in p) for p in cover['cells'][i]['vertices']])
 for a,b in ((F(1),F(0)),(F(0),F(1))):
  world=clip(world,(a,b,L/2+H));world=clip(world,(-a,-b,-L/2+H))
 need(area2(world)>0,'degenerate original cell domain')
 domain=[rotate(p) for p in world];cert=packet['certificate'];D=cert['coordinate_denominator']
 sites=[rotate(tuple(F(v,D) for v in p)) for p in cert['sites']]
 regions=[]
 for f in cert['features']:
  need(f['kind']=='majority_hull' and len(f['indices'])==2*f['threshold']-1,'unsupported feature')
  if f['weight']>0:regions.append(('TRUE',true_rows([sites[j] for j in f['indices']],half)))
 points=[sites[j] for j,w in enumerate(cert['point_weights']) if w>0]
 for owner in packet.get('conditional_owner_support',packet['mask']):
  if owner!=i:points.extend(rotate(tuple(map(F,p))) for p in packet['ownership_points_field'][owner])
 for x,y in points:regions.append(('point',[(F(1),F(0),x+half),(F(-1),F(0),-x+half),(F(0),F(1),y+half),(F(0),F(-1),-y+half)]))
 # Regions missing the domain can be removed without changing its coverage.
 eligible=[(kind,rows,area2(intersection(domain,rows))) for kind,rows in regions]
 eligible=[x for x in eligible if x[2]>0];eligible.sort(key=lambda x:x[2],reverse=True)
 pieces=[domain];maxpieces=1;used=0;counts={'TRUE':0,'point':0}
 for kind,rows,ar in eligible:
  pieces=[Q for P in pieces for Q in subtract(P,rows)]
  used+=1;counts[kind]+=1;maxpieces=max(maxpieces,len(pieces))
  if not pieces:break
 need(not pieces,'positive-area uncovered center region remains')
 return dict(status='PASS_INDEPENDENT_EXACT_POLYGON_UNION_COVER',cell=i,interval=row['interval'],threshold_units=1,
  initial_domain_area_twice=str(area2(domain)),eligible_regions=len(eligible),used_regions=used,used_region_types=counts,
  maximum_residual_pieces=maxpieces,remaining_positive_area_pieces=0,
  boundary_argument='Finite union of closed charge regions contains the dense full-dimensional domain; hence it contains its closure, including every boundary center.')

if __name__=='__main__':
 from pathlib import Path
 import argparse,json,hashlib
 ap=argparse.ArgumentParser();ap.add_argument('packet',type=Path);ap.add_argument('replay',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 root=Path(__file__).resolve().parents[3]/'current';coverpath=root/'research/optimality/global_capture/center-cover-symmetric-exact.json'
 packet=json.loads(args.packet.read_text());replay=json.loads(args.replay.read_text());cover=json.loads(coverpath.read_text())
 results=[verify_row(packet,cover,row) for row in replay['records'] if row['status']=='PASS_TRUE_PATCH']
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 out=dict(status='PASS_INDEPENDENT_PATCH_ROW_UNIONS',checker_sha256=sha(Path(__file__)),packet_sha256=sha(args.packet),replay_sha256=sha(args.replay),cover_sha256=sha(coverpath),rows=results,scope='Independent entire-domain charge-one coverage for the accepted patch leaves; no complete mask claim in isolation.')
 args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
