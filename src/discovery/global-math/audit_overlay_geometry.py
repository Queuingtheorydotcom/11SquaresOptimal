#!/usr/bin/env python3
"""Read-only exact reconstruction of all closed D4 regions and retained bans."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,time
D=Path(__file__).resolve().parent;R=D.parent/'phase3'
P={'cover':R/'current/research/optimality/global_capture/center-cover-symmetric-exact.json','overlay':R/'work/phase2/geometry/cover_overlay_exact.json','distance':R/'work/phase2/geometry/overlay_distance_pairs.json'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c,o,d=[json.load(open(P[k])) for k in ['cover','overlay','distance']]
if sha(P['cover'])!=o['cover_sha256'] or sha(P['overlay'])!=d['overlay_sha256']:raise ValueError('Hash mismatch')

def cross(p,q,r):return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
def hull(points):
 pts=sorted(set(points))
 if len(pts)<3:return pts
 lo=[]
 for p in pts:
  while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
  lo.append(p)
 hi=[]
 for p in reversed(pts):
  while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
  hi.append(p)
 return lo[:-1]+hi[:-1]

def clip(poly,a,b):
 if not poly:return []
 out=[]
 edges=[(poly[0],poly[0])] if len(poly)==1 else list(zip(poly,poly[1:]+poly[:1]))
 for p,q in edges:
  hp,hq=cross(a,b,p),cross(a,b,q)
  if hp>=0:out.append(p)
  if hp*hq<0:
   r=hp/(hp-hq);out.append((p[0]+r*(q[0]-p[0]),p[1]+r*(q[1]-p[1])))
 return hull(out)

def intersect(poly,cell):
 for a,b in zip(cell,cell[1:]+cell[:1]):
  poly=clip(poly,a,b)
  if not poly:return []
 return poly

def preimage(v,config):
 swap,sx,sy=config
 x=v[0] if sx==1 else 1-v[0];y=v[1] if sy==1 else 1-v[1]
 return (y,x) if swap else (x,y)

start=time.time();cells=[hull([tuple(map(F,v)) for v in r['vertices']]) for r in c['cells']]
if len(cells)!=16 or any(len(p)<3 for p in cells):raise ValueError('Bad source cells')
if o['symmetries']!=[[0,1,1],[0,-1,1],[1,-1,1],[1,1,1]]:raise ValueError('Unexpected views')
regions={(i,):p for i,p in enumerate(cells)}
for g in o['symmetries'][1:]:
 cc=[hull([preimage(v,g) for v in p]) for p in cells]; nxt={}
 for ls,p in regions.items():
  for j,q in enumerate(cc):
   h=intersect(p,q)
   if h:nxt[ls+(j,)]=h
 regions=nxt
 print('Reconstructed views',len(next(iter(regions))),'regions',len(regions),flush=True)
expected={tuple(r['labels']):hull([tuple(map(F,v)) for v in r['vertices']]) for r in o['regions']}
if set(regions)!=set(expected):raise ValueError('Incomplete label tuple list')
for k,v in regions.items():
 if set(v)!=set(expected[k]):raise ValueError(f'Wrong exact region {k}')
U=F(d['U']);scale=(U-1)**2
for row in d['pairs']:
 a,b=row['regions'];p=expected[tuple(o['regions'][a]['labels'])];q=expected[tuple(o['regions'][b]['labels'])]
 m=max((x[0]-y[0])**2+(x[1]-y[1])**2 for x in p for y in q)*scale
 if not m<1 or m!=F(row['maximum_squared_center_distance']):raise ValueError('Wrong distance exclusion')
record={'status':'PASS_INDEPENDENT_EXACT_OVERLAY_GEOMETRY','sources':{k:{'path':str(p),'sha256':sha(p)} for k,p in P.items()},'checker_sha256':sha(Path(__file__)),'regions':len(regions),'degenerate_regions':sum(len(p)<3 for p in regions.values()),'exact_distance_bans':len(d['pairs']),'seconds':time.time()-start,'scope':'Independently reconstructs every closed label tuple, including points/segments, from the retained16cell cover. The capacity-one proof of that input cover remains a separate premise.'}
(D/'overlay-geometry-independent-replay.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='sources'},indent=2))
