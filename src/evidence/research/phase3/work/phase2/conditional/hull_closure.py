"""Acyclic conditional ownership using exact forbidden owned-hull intersections.
All geometry accepted only through complete rational angular covers.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,time,hashlib,argparse
if not __debug__:raise SystemExit('Assertions must remain enabled.')
ROOT=Path('/workspace/scratch/6def36ddf53b');HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/phase2/hull'));import convex_cover as geo
sys.path.insert(0,str(ROOT/'work/geometry'));import validate_wall_sites as wall
COVER=ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
EXPECTED_COVER='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(d,default=str,indent=2)+'\n');q.replace(p)
def canonical(x):return json.dumps(x,default=str,sort_keys=True,separators=(',',':')).encode()
def intersects(a,b):
 for poly in (a,b):
  for n,z in geo.rows(poly):
   aa=[n[0]*x+n[1]*y for x,y in a];bb=[n[0]*x+n[1]*y for x,y in b]
   if max(aa)<min(bb) or max(bb)<min(aa):return False
 return True

def witness_from(answer,other,target):
 t=answer['reference_half_angle'];c,s=geo.cs(t);radius=PARENT*(c+s)/2
 for poly in answer['remaining']:
  if not poly or not geo.twice_area(poly):continue
  q=tuple(sum(p[k] for p in poly)/len(poly) for k in (0,1))
  if not all(radius<=x<=geo.L-radius for x in q):continue
  corners=[(q[0]+PARENT*(a*c-b*s)/2,q[1]+PARENT*(a*s+b*c)/2) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
  if any(intersects(corners,h) for h in other.values()):continue
  if target is not None:
   dx,dy=target[0]-q[0],target[1]-q[1]
   if max(abs(c*dx+s*dy),abs(-s*dx+c*dy))<PARENT/2:continue
  return dict(center=q,half_angle=t,parent_side=PARENT,avoids_every_prior_other_owned_hull=True,target_not_strictly_captured=target is not None)
 return None

def prove(owner,target,prior,deadline,max_nodes=1000):
 other={j:geo.hull(prior[j]) for j in mask if j!=owner};pending=[(F(i,32),F(i+1,32),0) for i in reversed(range(32))];records=[];accepted=[];refuter=None;fail=[]
 while pending and time.monotonic()<deadline and len(records)<max_nodes:
  lo,hi,depth=pending.pop();ans=geo.interval_cover(world[owner],other,target,lo,hi,U,max_pieces=3000)
  if ans['passed']:
   records.append(dict(interval=[lo,hi],depth=depth,core_side=ans['core_side'],reference_half_angle=ans['reference_half_angle'],status=ans['status'],peak_pieces=ans.get('peak_pieces',0)));accepted.append((lo,hi))
  else:
   refuter=witness_from(ans,other,target)
   records.append(dict(interval=[lo,hi],depth=depth,core_side=ans['core_side'],reference_half_angle=ans['reference_half_angle'],status=ans['status'],remaining_count=len(ans['remaining']),parent_refuter=refuter))
   if refuter:fail.append((lo,hi));break
   if depth<12:
    mid=(lo+hi)/2;pending.extend([(mid,hi,depth+1),(lo,mid,depth+1)])
   else:fail.append((lo,hi));break
 cursor=F(0)
 for lo,hi in sorted(accepted):
  assert lo==cursor;cursor=hi
 complete=not pending and not fail and cursor==1
 return dict(status=('PASS_EXACT_OWNED_HULL_CELL_INFEASIBILITY' if target is None else 'PASS_EXACT_HULL_CONDITIONAL_POINT_OWNERSHIP') if complete else 'INCOMPLETE',owner=owner,target=target,accepted=sorted(accepted),records=records,pending=pending,failed=fail,parent_refuter=refuter)

ap=argparse.ArgumentParser();ap.add_argument('--seed',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--seconds',type=float,default=180);ap.add_argument('--rounds',type=int,default=3);ap.add_argument('--owners');ap.add_argument('--probe-only',action='store_true');ap.add_argument('--rays',type=int,default=8);ap.add_argument('--radius-upper',default='1/2');args=ap.parse_args()
seed=json.loads(args.seed.read_text());assert sha(COVER)==EXPECTED_COVER==seed['cover_sha256'];cover=json.loads(COVER.read_text());mask=seed['mask'];assert mask==cover['canonical_eleven_cell_subsets'][seed['mask_index']]
U=F(seed['parent_Uplus']);PARENT=geo.L/U;assert U==wall.U and PARENT==wall.B
world=[[tuple(PARENT/2+(geo.L-PARENT)*F(x) for x in p) for p in cell['vertices']] for cell in cover['cells']]
generators=[tuple(PARENT/2+(geo.L-PARENT)*F(x) for x in cell['center']) for cell in cover['cells']]
groups=[[tuple(map(F,p)) for p in group] for group in seed['owned_points']];wall_records=[]
for j in mask:
 poly=[tuple(x/PARENT for x in v) for v in world[j]]
 for point in groups[j]:
  r=wall.validate(tuple(x/PARENT for x in point),poly);assert r['status']=='PASS_EXACT_WALL_OWNERSHIP';wall_records.append(dict(owner=j,point=point,**r))
start=time.monotonic();deadline=start+args.seconds;proofs=[];rounds=[];attempts=[];contradiction=None;owners=list(map(int,args.owners.split(','))) if args.owners else sorted(mask,key=lambda j:sum((float(generators[j][0]-generators[k][0])**2+float(generators[j][1]-generators[k][1])**2)**-.5 for k in mask if k!=j),reverse=True);assert set(owners)<=set(mask)
rays=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
if args.rays==16:rays=[(1,0),(1,F(1,2)),(1,1),(F(1,2),1),(0,1),(-F(1,2),1),(-1,1),(-1,F(1,2)),(-1,0),(-1,-F(1,2)),(-1,-1),(-F(1,2),-1),(0,-1),(F(1,2),-1),(1,-1),(1,-F(1,2))]
def write():
 d=dict(status='PASS_EXACT_HULL_MASK_EXCLUSION' if contradiction else 'PARTIAL_EXACT_HULL_OWNERSHIP_CLOSURE',mask_index=seed['mask_index'],mask=mask,parent_Uplus=U,parent_side=PARENT,cover_sha256=EXPECTED_COVER,seed_sha256=sha(args.seed),seed_wall_replay=wall_records,rounds=rounds,proofs=proofs,attempts=attempts,owned_points=groups,contradiction=contradiction,seconds=time.monotonic()-start,mask_exclusion_proved=bool(contradiction),global_optimality_proved=False,dependencies={str(p):sha(p) for p in [Path(__file__),Path(geo.__file__),Path(wall.__file__)]});save(args.output,d)
for round_index in range(args.rounds):
 prior=[[p for p in group] for group in groups];digest=hashlib.sha256(canonical(prior)).hexdigest();rounds.append(dict(index=round_index+1,prior_owned_points=prior,prior_snapshot_sha256=digest));added=0
 for owner in owners:
  if time.monotonic()>deadline:break
  r=prove(owner,None,prior,min(deadline,time.monotonic()+10));attempts.append(dict(round=round_index+1,kind='infeasibility',owner=owner,proof=r));write()
  if r['status'].startswith('PASS'):
   contradiction=dict(kind='owner_pose_infeasible',owner=owner,round=round_index+1,prior_snapshot_sha256=digest,proof=r);write();break
  print(json.dumps(dict(round=round_index+1,owner=owner,probe_rows=len(r['records']),has_refuter=bool(r['parent_refuter']),seconds=time.monotonic()-start)),flush=True)
 if contradiction or args.probe_only or time.monotonic()>deadline:break
 for owner in owners:
  for direction in rays:
   if time.monotonic()>deadline:break
   lo,hi=F(0),F(args.radius_upper);best=None
   for _ in range(4):
    if time.monotonic()>deadline:break
    radius=(lo+hi)/2;target=tuple(g+PARENT*radius*v for g,v in zip(generators[owner],direction));r=prove(owner,target,prior,min(deadline,time.monotonic()+3));passed=r['status'].startswith('PASS');attempts.append(dict(round=round_index+1,kind='point',owner=owner,direction=direction,radius=radius,passed=passed,rows=len(r['records']),parent_refuter=r['parent_refuter']))
    if passed:lo=radius;best=r
    else:hi=radius
   if best is not None and tuple(best['target']) not in groups[owner]:
    best.update(round=round_index+1,prior_snapshot_sha256=digest,direction=direction,radius=lo);proofs.append(best);groups[owner].append(tuple(best['target']));added+=1
   hs={j:geo.hull(groups[j]) for j in mask}
   for i,j in [(i,j) for i in mask for j in mask if i<j]:
    if intersects(hs[i],hs[j]):contradiction=dict(kind='owned_hulls_intersect',owners=[i,j],owned_hulls=[hs[i],hs[j]],round=round_index+1);break
   write()
   if contradiction:break
  print(json.dumps(dict(round=round_index+1,owner=owner,proofs=len(proofs),attempts=len(attempts),seconds=time.monotonic()-start)),flush=True)
  if contradiction or time.monotonic()>deadline:break
 rounds[-1]['new_owned_points']=added
 if contradiction or time.monotonic()>deadline or not added:break
write();print(json.dumps(dict(proofs=len(proofs),attempts=len(attempts),contradiction=bool(contradiction),seconds=time.monotonic()-start)),flush=True)
