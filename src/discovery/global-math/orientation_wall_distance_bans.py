#!/usr/bin/env python3
"""Exact stronger region-pair bans from wall-imposed edge-angle restrictions."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,math,time
D=Path(__file__).resolve().parent;R=D.parent/'phase3';O=R/'work/phase2/geometry/cover_overlay_exact.json';B=R/'work/phase2/geometry/overlay_distance_pairs.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
o=json.load(open(O));b=json.load(open(B));U=F(b['U']);scale=U-1
points=[[(F(x)*scale+F(1,2),F(y)*scale+F(1,2)) for x,y in r['vertices']] for r in o['regions']]
caps=[2*min(max(x for x,y in pp),max(y for x,y in pp),U-min(x for x,y in pp),U-min(y for x,y in pp)) for pp in points]
known={tuple(sorted(r['regions'])) for r in b['pairs']}

def below_one(dx,dy,w):
 x,y=sorted((abs(dx),abs(dy)),reverse=True);norm=x*x+y*y
 if norm<1:return True
 # The angularly constrained maximum is attained at c+s=w only if the
 # unconstrained optimizing direction is outside the allowable end sectors.
 if w*w>=2 or w*w*norm >= (x+y)**2:return False
 a=2-(x+y)*w
 return a>0 and (x-y)**2*(2-w*w)<a*a

def screen(dx,dy,w):
 x,y=sorted((abs(float(dx)),abs(float(dy))),reverse=True);w=float(w);n=x*x+y*y
 if n<1-1e-10:return True
 if w*w>=2 or w*w*n >= (x+y)**2:return False
 return ((x+y)*w+(x-y)*math.sqrt(2-w*w))/2<1-1e-10
start=time.time();out=[]
for i in range(len(points)):
 for j in range(i):
  if (j,i) in known or any(x==y for x,y in zip(o['regions'][i]['labels'],o['regions'][j]['labels'])):continue
  w=max(caps[i],caps[j])
  if w*w>=2:continue
  diffs=[(p[0]-q[0],p[1]-q[1]) for p in points[i] for q in points[j]]
  if not all(screen(dx,dy,w) for dx,dy in diffs):continue
  if not all(below_one(dx,dy,w) for dx,dy in diffs):raise ValueError('Numeric proposal failed exact check')
  out.append({'regions':[j,i],'half_width_sum_cap':str(w)})
record={'status':'EXACT_BANS_WITH_ANALYTIC_LEMMA_REQUIRING_INDEPENDENT_REVIEW','new_pairs':out,'new_pair_count':len(out),'angle_restricted_region_count':sum(w*w<2 for w in caps),'wall_caps':list(map(str,caps)),'overlay_sha256':sha(O),'distance_sha256':sha(B),'checker_sha256':sha(Path(__file__)),'seconds':time.time()-start}
(D/'orientation-wall-distance-bans.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ['new_pairs','wall_caps']},indent=2))
