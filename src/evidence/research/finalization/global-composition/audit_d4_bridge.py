#!/usr/bin/env python3
"""Standalone exact conditional D4 bridge; no producer receipt is trusted.

Checks the original closed Voronoi cover and half-turn index convention,
reconstructs every four-view closed intersection, checks strict distance bans,
and independently solves three finite CSPs with bitset forward propagation.
The noncandidate exclusion union and candidate438 capture remain premises.
Run only in the root-coordinated CPU slot. This source was prepared without
executing its search during finalization.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import argparse,hashlib,json,sys,time
if sys.flags.optimize:raise SystemExit('This proof replay refuses optimized Python modes.')
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
U=F(387708359002281417731,10**20)
CANDIDATES=(438,999,1462,1659)
EXPECTED={
 'cover':'df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e',
 'overlay':'845b5f748843dd60fa7e290a5ea1a304da4e439ae229bd73a841aec816f4e700',
 'distance':'4f960f4001faa6c9c1e7521f3a2344f71e10b41cd38a6425f6821cc1fd2ccd47'}
EXPECTED_MASKS={438:(0,1,2,3,4,8,9,10,11,13,15),999:(0,1,2,4,6,7,9,10,12,14,15),1462:(0,1,3,5,6,8,9,11,12,13,14),1659:(0,2,3,4,5,6,7,11,12,13,14)}
VIEWS=((0,1,1),(0,-1,1),(1,-1,1),(1,1,1))
def need(test,message):
 if not test:raise ValueError(message)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def hull(points):
 points=sorted(set(points))
 if len(points)<3:return points
 lo=[];hi=[]
 for p in points:
  while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
  lo.append(p)
 for p in reversed(points):
  while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
  hi.append(p)
 return lo[:-1]+hi[:-1]
def dot(a,b):return a[0]*b[0]+a[1]*b[1]
def squared(a,b):return (a[0]-b[0])**2+(a[1]-b[1])**2
def dimension(P):return 0 if len(P)==1 else 1 if len(P)==2 else 2
def clip(P,a,b):
 if not P:return []
 Q=[];edges=[(P[0],P[0])] if len(P)==1 else zip(P,P[1:]+P[:1])
 for p,q in edges:
  hp,hq=cross(a,b,p),cross(a,b,q)
  if hp>=0:Q.append(p)
  if hp*hq<0:
   t=hp/(hp-hq);Q.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
 return hull(Q)
def intersect(P,C):
 for a,b in zip(C,C[1:]+C[:1]):
  P=clip(P,a,b)
  if not P:break
 return P
def inverse_image(p,g):
 swap,sx,sy=g;x=p[0] if sx==1 else 1-p[0];y=p[1] if sy==1 else 1-p[1]
 return (y,x) if swap else (x,y)
def bit_members(m):
 while m:
  b=m&-m;yield b.bit_length()-1;m-=b
def mask(J):return sum(1<<j for j in J)
def half_turn(J):return tuple(sorted(15-j for j in J))

def check_cover(c):
 raw=c['cells'];need(len(raw)==16,'Expected sixteen cells')
 sites=[tuple(map(F,r['center'])) for r in raw];need(len(set(sites))==16,'Sites not distinct')
 cells=[]
 for i,p in enumerate(sites):
  lines=[(-F(1),F(0),F(0)),(F(1),F(0),F(1)),(F(0),-F(1),F(0)),(F(0),F(1),F(1))]
  for j,q in enumerate(sites):
   if i!=j:lines.append((2*(q[0]-p[0]),2*(q[1]-p[1]),dot(q,q)-dot(p,p)))
  vertices=[]
  for (a,b,c0),(d,e,f) in combinations(lines,2):
   determinant=a*e-b*d
   if determinant:
    v=((c0*e-b*f)/determinant,(a*f-c0*d)/determinant)
    if all(x*v[0]+y*v[1]<=z for x,y,z in lines):vertices.append(v)
  P=hull(vertices);need(len(P)>=3,'Empty/degenerate Voronoi cell')
  need(P==hull(tuple(map(F,v)) for v in raw[i]['vertices']),'Incorrect reported cell')
  need(max(squared(a,b)*(U-1)**2 for a in P for b in P)<1,'Closed cell has insufficient strict capacity bound')
  cells.append(P)
 for i,P in enumerate(cells):need(hull((1-x,1-y) for x,y in P)==cells[15-i],'Half-turn cell indexing fails')
 need(c['symmetry_cell_involution']==list(reversed(range(16))),'Wrong reported cell involution')
 allmasks=list(combinations(range(16),11));canonical=sorted({min(J,half_turn(J)) for J in allmasks})
 need(len(allmasks)==4368 and len(canonical)==2184,'Wrong case count')
 need(c['all_eleven_cell_subsets']==[list(J) for J in allmasks],'Raw case enumeration drift')
 need(c['canonical_eleven_cell_subsets']==[list(J) for J in canonical],'Canonical case enumeration drift')
 need(all(canonical[i]==J for i,J in EXPECTED_MASKS.items()),'Candidate index convention drift')
 return cells,canonical

def check_overlay(cells,o):
 need(tuple(map(tuple,o['symmetries']))==VIEWS,'Wrong symmetry representatives')
 regions={(i,):P for i,P in enumerate(cells)};prefix=[16]
 for g in VIEWS[1:]:
  transformed=[hull(inverse_image(p,g) for p in P) for P in cells];new={}
  for labels,P in regions.items():
   for j,C in enumerate(transformed):
    Q=intersect(P,C)
    if Q:new[labels+(j,)]=Q
  regions=new;prefix.append(len(regions))
 need(prefix==[16,56,124,220],'Closed overlay prefix inventory differs')
 reported=o['regions'];need(len(reported)==len(regions),'Missing/extra overlay regions')
 labels=[];vertices=[];seen=set();counts={}
 for index,row in enumerate(reported):
  key=tuple(row['labels']);need(row['index']==index and key in regions and key not in seen,'Duplicate/bad region index')
  seen.add(key);Q=hull(tuple(map(F,v)) for v in row['vertices']);need(Q==regions[key],'Incorrect overlay vertices')
  dim=dimension(Q);need(row['dimension']==dim,'Incorrect closed-region dimension');counts[dim]=counts.get(dim,0)+1
  labels.append(key);vertices.append(Q)
 need(seen==set(regions) and counts=={0:8,2:212},'Boundary region inventory differs')
 return labels,vertices,prefix,counts

def check_bans(vertices,d):
 need(F(d['U'])==U,'Distance side differs from theorem cap')
 banned=set()
 for row in d['pairs']:
  i,j=row['regions'];need(type(i)is int and type(j)is int and 0<=i<j<len(vertices) and (i,j) not in banned,'Bad distance pair inventory')
  maximum=max(squared(p,q)*(U-1)**2 for p in vertices[i] for q in vertices[j])
  need(maximum==F(row['maximum_squared_center_distance']) and maximum<1,'Distance ban is not exact and strict')
  banned.add((i,j))
 need(len(banned)==1572,'Distance ban inventory differs')
 return banned

def solve_other_candidate_cases(labels,banned,canonical):
 # Different finite search from the archived fixed-order, 216-triple checker:
 # simultaneous possible-target bitsets, MRV choice, pairwise forward filtering.
 allowed=sorted({canonical[i] for i in CANDIDATES[1:]}|{half_turn(canonical[i]) for i in CANDIDATES[1:]})
 need(len(allowed)==6,'Unexpected raw non-target candidate masks')
 target_bits=[mask(J) for J in allowed];contains=[sum(1<<k for k,M in enumerate(target_bits) if M&(1<<j)) for j in range(16)]
 initial=[sum(1<<r for r,ls in enumerate(labels) if ls[0]==j) for j in range(16)]
 compatible=[]
 for r,ls in enumerate(labels):
  compatible.append(sum(1<<s for s,ms in enumerate(labels) if all(ls[g]!=ms[g] for g in range(4)) and tuple(sorted((r,s))) not in banned))
 records=[]
 for index in CANDIDATES[1:]:
  nodes=0
  def visit(domains,targets):
   nonlocal nodes;nodes+=1
   if not domains:return []
   filtered={}
   for owner,options in domains.items():
    filtered[owner]=sum(1<<r for r in bit_members(options) if all(targets[g]&contains[labels[r][g+1]] for g in range(3)))
    if not filtered[owner]:return None
   owner=min(filtered,key=lambda j:(filtered[j].bit_count(),j))
   for r in bit_members(filtered[owner]):
    new_domains={j:options&compatible[r] for j,options in filtered.items() if j!=owner}
    if any(not options for options in new_domains.values()):continue
    new_targets=tuple(targets[g]&contains[labels[r][g+1]] for g in range(3))
    found=visit(new_domains,new_targets)
    if found is not None:return [r]+found
   return None
  answer=visit({j:initial[j] for j in canonical[index]},((1<<6)-1,)*3)
  need(answer is None,'All-other-candidate abstract assignment survives: '+str((index,answer)))
  records.append({'source_canonical_index':index,'status':'UNSAT','complete_search_nodes':nodes})
 return records,allowed

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,default=ROOT);ap.add_argument('--output',type=Path,default=HERE/'d4-bridge-independent-replay.json');args=ap.parse_args();start=time.monotonic()
 ph=args.workspace/'research/phase3';paths={'cover':ph/'current/research/optimality/global_capture/center-cover-symmetric-exact.json','overlay':ph/'work/phase2/geometry/cover_overlay_exact.json','distance':ph/'work/phase2/geometry/overlay_distance_pairs.json'}
 data={}
 for key,path in paths.items():need(sha(path)==EXPECTED[key],'Frozen source mismatch: '+key);data[key]=json.loads(path.read_text())
 c,o,d=(data[k] for k in ('cover','overlay','distance'))
 need(o['cover_sha256']==EXPECTED['cover'] and d['overlay_sha256']==EXPECTED['overlay'],'Geometry dependency mismatch')
 cells,canonical=check_cover(c);labels,vertices,prefix,counts=check_overlay(cells,o);banned=check_bans(vertices,d)
 records,allowed=solve_other_candidate_cases(labels,banned,canonical)
 for key,path in paths.items():need(sha(path)==EXPECTED[key],'Input changed during replay')
 out={'review_result':'PASS','status':'PASS_EXACT_CONDITIONAL_D4_BRIDGE','checker_sha256':sha(__file__),'sources':{k:{'path':str(p.resolve()),'sha256':EXPECTED[k]} for k,p in paths.items()},'U':str(U),'canonical_index_base':0,'canonical_count':2184,'raw_count':4368,'candidate_masks':{str(i):list(canonical[i]) for i in CANDIDATES},'symmetry_cell_involution':list(reversed(range(16))),'views':VIEWS,'overlay_prefix_counts':prefix,'overlay_dimensions':counts,'strict_distance_bans':len(banned),'allowed_non_target_raw_masks':allowed,'finite_search':records,'geometry_checked_from_source':True,'producer_receipt_required':False,'premises_not_replayed':['All 2180 canonical cases outside438,999,1462,1659 are impossible at sideU.','Case438 capture holds for the centeredU-cover antecedent at every sideS<=T.'],'conclusion':'Under the noncandidate exclusion premise, every packing at sideS<=U has a D4 image with a valid closed-cell assignment exactly equal to canonical case438. Combining that image with independently established case438 capture atS<=T excludes all packings withS<T.','conditional_d4_bridge_proved':True,'global_optimality_proved':False,'seconds':time.monotonic()-start}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['review_result','status','checker_sha256','finite_search','seconds']},indent=2))
if __name__=='__main__':main()
