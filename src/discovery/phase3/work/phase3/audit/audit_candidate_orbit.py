#!/usr/bin/env python3
"""Independent conditional D4 capture lemma: four candidate cases reduce to438.

Reconstructs the complete closed overlay by exact half-plane intersections,
checks every used distance incompatibility, and exhausts each of 6^3 physical
view-mask triples with a separate finite matching search. No producer clipping
or CSP routine is imported. This is conditional and excludes no current case.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations,product
import hashlib,json,sys,time
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[1];ROOT=HERE.parents[2]/'current'
sys.path.insert(0,str(ROOT/'research/optimality/audit'))
from audit_center_cover import audit as audit_cover,hull as original_hull
H=WORK/'phase2/geometry';COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def hull(P):
 P=sorted(set(P));return P if len(P)<3 else original_hull(P)
def rows(P):
 out=[]
 for p,q in zip(P,P[1:]+P[:1]):
  a=q[1]-p[1];b=p[0]-q[0];out.append((a,b,a*p[0]+b*p[1]))
 return out
def preimage_rows(R,g):
 sw,sx,sy=g;offx=F(sx==-1);offy=F(sy==-1);out=[]
 for a,b,c in R:
  n=(a*sx,b*sy) if not sw else (b*sy,a*sx)
  out.append((*n,c-a*offx-b*offy))
 return out
def feasible_vertices(R):
 pts=[]
 for (a,b,c),(d,e,f) in combinations(R,2):
  det=a*e-b*d
  if not det:continue
  x=(c*e-b*f)/det;y=(a*f-c*d)/det
  if all(v*x+w*y<=z for v,w,z in R):pts.append((x,y))
 return hull(pts)
def bbox(P):return [(min(p[k] for p in P),max(p[k] for p in P)) for k in (0,1)]
def disjoint_box(A,B):return any(a[1]<b[0] or b[1]<a[0] for a,b in zip(A,B))
def area(P):return abs(sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(P,P[1:]+P[:1]))) if len(P)>2 else 0

def main():
 begin=time.monotonic();cover=read(COVER);overlaypath=H/'cover_overlay_exact.json';distpath=H/'overlay_distance_pairs.json';overlay=read(overlaypath);distance=read(distpath)
 coveraudit=audit_cover(COVER);need(overlay['cover_sha256']==sha(COVER) and distance['overlay_sha256']==sha(overlaypath),'unbound geometric inputs')
 U=F(distance['U']);need(U==F(387708359002281417731,10**20),'wrong side domain')
 cells=[hull([tuple(map(F,p)) for p in c['vertices']]) for c in cover['cells']]
 expected_views=[(0,1,1),(0,-1,1),(1,-1,1),(1,1,1)]
 need([tuple(g) for g in overlay['symmetries']]==expected_views,'unexpected fourD4representatives')
 # Source-independent affine substitution into target-cell inequalities.
 views=[[preimage_rows(rows(P),g) for P in cells] for g in expected_views]
 viewverts=[[feasible_vertices(R) for R in view] for view in views]
 states=[((i,),views[0][i],viewverts[0][i]) for i in range(16)];stage_counts=[16]
 for view in range(1,4):
  new=[]
  for lab,R,P in states:
   BP=bbox(P)
   for j in range(16):
    if disjoint_box(BP,bbox(viewverts[view][j])):continue
    RR=R+views[view][j];Q=feasible_vertices(RR)
    if Q:new.append((lab+(j,),RR,Q))
  states=new;stage_counts.append(len(states));print('independent overlay prefix',view+1,len(states),flush=True)
 mapping={lab:P for lab,R,P in states};need(len(mapping)==len(states),'duplicate independently enumerated tuple')
 reported=overlay['regions'];need(len(reported)==len(mapping),'missing/extra overlay label tuples')
 vertices=[];labels=[];dimensions=[]
 for i,r in enumerate(reported):
  lab=tuple(r['labels']);need(r['index']==i and lab in mapping,'wrong region index or omitted tuple')
  P=mapping[lab];Q=hull([tuple(map(F,p)) for p in r['vertices']]);need(P==Q,'overlay extreme vertices differ')
  dim=2 if area(P)>0 else 1 if len(P)>1 else 0;need(r['dimension']==dim,'overlay dimension differs')
  vertices.append(P);labels.append(lab);dimensions.append(dim)
 need({tuple(r['labels']) for r in reported}==set(mapping),'overlay tuple completeness fails')
 ban=[0]*len(reported);usedpairs=set()
 for r in distance['pairs']:
  i,j=r['regions'];need(type(i)is int and type(j)is int and 0<=i<j<len(vertices) and (i,j) not in usedpairs,'bad duplicate distance pair')
  md=max((U-1)**2*sum((p[k]-q[k])**2 for k in (0,1)) for p in vertices[i] for q in vertices[j])
  need(md==F(r['maximum_squared_center_distance']) and md<1,'distance exclusion not strict or not correct')
  usedpairs.add((i,j));ban[i]|=1<<j;ban[j]|=1<<i
 # Distinct labels within each view follow from strict unit-center diameter.
 need(max((U-1)**2*sum((p[k]-q[k])**2 for k in (0,1)) for C in cells for p in C for q in C)<1,'view-cell injectivity fails')
 turn=lambda J:tuple(sorted(15-i for i in J));canonical=[tuple(J) for J in cover['canonical_eleven_cell_subsets']]
 allowed=sorted({canonical[i] for i in (999,1462,1659)}|{turn(canonical[i]) for i in (999,1462,1659)})
 need(len(allowed)==6,'unexpected physical target cases')
 domains={i:[r for r,lab in enumerate(labels) if lab[0]==i] for i in range(16)};proofs=[]
 for sourceindex in (999,1462,1659):
  source=canonical[sourceindex];nodes=0;triples=0;empty_domains=0
  for target in product(allowed,repeat=3):
   triples+=1;targets=[set(J) for J in target]
   options={i:[r for r in domains[i] if all(labels[r][g+1] in targets[g] for g in range(3))] for i in source}
   if any(not a for a in options.values()):empty_domains+=1;continue
   order=sorted(source,key=lambda i:(len(options[i]),i))
   def visit(k,used,chosen,assignment):
    nonlocal nodes
    nodes+=1
    if k==11:return assignment
    i=order[k]
    for r in options[i]:
     if ban[r]&chosen:continue
     bits=[1<<labels[r][g+1] for g in range(3)]
     if any(used[g]&bits[g] for g in range(3)):continue
     found=visit(k+1,tuple(used[g]|bits[g] for g in range(3)),chosen|(1<<r),assignment+[r])
     if found is not None:return found
    return None
   witness=visit(0,(0,0,0),0,[])
   need(witness is None,'abstract all-other-candidate assignment survives')
  proofs.append(dict(source_canonical_mask=sourceindex,physical_view_mask_triples=triples,empty_domain_triples=empty_domains,exhaustive_search_nodes=nodes,status='UNSAT'))
 proposalpath=WORK/'phase3/reductions/candidate-orbit-result.json';proposal=read(proposalpath)
 need(proposal['target_mask']==438 and {r['mask_index'] for r in proposal['records']}=={999,1462,1659} and all(r['status']=='CONDITIONAL_ORBIT_CAPTURE_PROVED' for r in proposal['records']),'producer conditional conclusion differs')
 out=dict(status='PASS_INDEPENDENT_CONDITIONAL_CANDIDATE_ORBIT_CAPTURE',checker_sha256=sha(Path(__file__)),cover_sha256=sha(COVER),overlay_sha256=sha(overlaypath),distance_receipt_sha256=sha(distpath),producer_result_sha256=sha(proposalpath),U=str(U),
  independently_enumerated_overlay_prefix_counts=stage_counts,overlay_regions=len(vertices),overlay_dimensions={str(d):dimensions.count(d) for d in set(dimensions)},exact_distance_pairs_checked=len(usedpairs),
  tested_source_masks=[999,1462,1659],proofs=proofs,target_mask=438,
  assumption='Every feasible packing belongs only to canonical occupied cases438,999,1462,1659; equivalently all other closed-cell canonical cases have already been excluded.',
  conclusion='Every feasible packing has a D4 image belonging to canonical case438.',
  current_masks_excluded=0,global_optimality_proved=False,seconds=time.monotonic()-begin,
  scope='Conditional global-symmetry reduction only. The assumption is not currently established; this receipt adds no case to the unconditional exclusion registry.')
 (HERE/'candidate-orbit-independent-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
