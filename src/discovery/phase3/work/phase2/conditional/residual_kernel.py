"""Exact owned-hull pose outer covers and common-strict-core ownership kernels.
An empty common kernel is not an infeasibility proof. Candidate masks are kept.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,time,hashlib,argparse
if not __debug__:raise SystemExit('Assertions must remain enabled.')
ROOT=Path('/workspace/scratch/6def36ddf53b');HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/phase2/hull'));import convex_cover as geo
sys.path.insert(0,str(ROOT/'work/geometry'));import validate_wall_sites as wall
COVER=ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json';EXPECTED_COVER='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(x):return json.dumps(x,default=str,sort_keys=True,separators=(',',':')).encode()
def save(p,d):
 tmp=p.with_suffix('.writing');tmp.write_text(json.dumps(d,default=str,indent=2)+'\n');tmp.replace(p)
def intersects(a,b):
 for poly in (a,b):
  for n,z in geo.rows(poly):
   aa=[n[0]*x+n[1]*y for x,y in a];bb=[n[0]*x+n[1]*y for x,y in b]
   if max(aa)<min(bb) or max(bb)<min(aa):return False
 return True

def inside_intervals(lo,hi,allowed):return any(F(a)<=lo and hi<=F(b) for a,b in allowed)

ap=argparse.ArgumentParser();ap.add_argument('--seed',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--bins',type=int,default=64);ap.add_argument('--rounds',type=int,default=3);ap.add_argument('--seconds',type=float,default=180);args=ap.parse_args()
seed=json.loads(args.seed.read_text());assert sha(COVER)==seed['cover_sha256']==EXPECTED_COVER;cover=json.loads(COVER.read_text());mask=seed['mask'];assert mask==cover['canonical_eleven_cell_subsets'][seed['mask_index']]
U=F(seed['parent_Uplus']);PARENT=geo.L/U;assert U==wall.U and PARENT==wall.B
world=[[tuple(PARENT/2+(geo.L-PARENT)*F(x) for x in p) for p in cell['vertices']] for cell in cover['cells']]
groups=[[tuple(map(F,p)) for p in group] for group in seed['owned_points']]
guardpath=ROOT/'current/research/optimality/global_capture/local-capture-guards.json';guards=json.loads(guardpath.read_text());guard=next((g for g in guards['guards'] if g['mask']==mask),None);roles={r['cell']:r for r in guard['roles']} if guard else {}
wall_records=[]
for owner in mask:
 poly=[tuple(x/PARENT for x in p) for p in world[owner]]
 for point in groups[owner]:
  r=wall.validate(tuple(x/PARENT for x in point),poly);assert r['status']=='PASS_EXACT_WALL_OWNERSHIP';wall_records.append(dict(owner=owner,point=point,**r))
start=time.monotonic();deadline=start+args.seconds;rounds=[];contradiction=None;guard_capture=False

def write():
 d=dict(status='PASS_EXACT_OWNED_HULL_MASK_EXCLUSION' if contradiction else ('POSE_COVER_INSIDE_LOCAL_GUARD' if guard_capture else 'PARTIAL_EXACT_POSE_LOCALIZATION'),mask_index=seed['mask_index'],mask=mask,parent_Uplus=U,parent_side=PARENT,cover_sha256=EXPECTED_COVER,seed_sha256=sha(args.seed),seed_wall_replay=wall_records,rounds=rounds,owned_points=groups,contradiction=contradiction,local_guard_geometry_captured=guard_capture,local_guard_source_sha256=sha(guardpath),mask_exclusion_proved=bool(contradiction),global_optimality_proved=False,seconds=time.monotonic()-start,dependencies={str(p):sha(p) for p in [Path(__file__),Path(geo.__file__),Path(wall.__file__)]});save(args.output,d)
for ri in range(args.rounds):
 prior=[[p for p in group] for group in groups];prior_hulls={j:geo.hull(prior[j]) for j in mask};digest=hashlib.sha256(canon(prior)).hexdigest();round=dict(index=ri+1,prior_owned_points=prior,prior_snapshot_sha256=digest,cells=[]);rounds.append(round);added=0
 for owner in mask:
  if time.monotonic()>deadline:break
  other={j:prior_hulls[j] for j in mask if j!=owner};kernel=geo.hull([(0,0),(geo.L,0),(geo.L,geo.L),(0,geo.L)]);rows=[];remaining_vertices=[];remaining_angles=[];cell_guard=bool(guard)
  for i in range(args.bins):
   if time.monotonic()>deadline:break
   lo,hi=F(i,args.bins),F(i+1,args.bins);ans=geo.interval_cover(world[owner],other,None,lo,hi,U,max_pieces=3000);remaining=ans['remaining'];t=ans['reference_half_angle'];core=ans['core_side'];c,s=geo.cs(t)
   if remaining:
    vertices=[p for poly in remaining for p in poly];remaining_vertices.extend(vertices);remaining_angles.append((lo,hi));strips=[]
    for n in ((c,s),(-s,c)):
     values=[n[0]*x+n[1]*y for x,y in vertices];lower=max(values)-core/2;upper=min(values)+core/2;strips.append(dict(normal=n,lower=lower,upper=upper))
     kernel=geo.clip_linear(kernel,n,upper,True);kernel=geo.clip_linear(kernel,(-n[0],-n[1]),-lower,True)
    if guard:
     role=roles[owner]
     if not inside_intervals(lo,hi,role['half_angle_intervals']):cell_guard=False
     for x,y in vertices:
      for z,bounds in zip((x/PARENT-U/2,y/PARENT-U/2),role['centered_box']):
       if not F(bounds[0])<=z<=F(bounds[1]):cell_guard=False
   else:strips=[]
   rows.append(dict(interval=[lo,hi],core_side=core,reference_half_angle=t,status=ans['status'],residual_polygons=remaining,common_core_strips=strips,peak_pieces=ans.get('peak_pieces',0)))
  complete=len(rows)==args.bins
  cell=dict(owner=owner,complete=complete,rows=rows,common_core_kernel=kernel if complete else [],retained_angle_intervals=remaining_angles,inside_local_guard=complete and cell_guard)
  if complete:
   if not remaining_vertices:contradiction=dict(kind='all_parent_poses_forbidden',owner=owner,round=ri+1)
   else:
    cell['center_bounds_field']=[[min(p[k] for p in remaining_vertices),max(p[k] for p in remaining_vertices)] for k in (0,1)]
    cell['center_bounds_centered_unit']=[[x/PARENT-U/2 for x in b] for b in cell['center_bounds_field']]
    for p in kernel:
     if p not in groups[owner]:groups[owner].append(p);added+=1
  round['cells'].append(cell);write()
  print(json.dumps(dict(round=ri+1,owner=owner,complete=complete,residual_rows=len(remaining_angles),kernel_vertices=len(kernel),center_widths=[float(b[1]-b[0]) for b in cell.get('center_bounds_centered_unit',[])],inside_guard=cell['inside_local_guard'],seconds=time.monotonic()-start)),flush=True)
  if contradiction:break
  hs={j:geo.hull(groups[j]) for j in mask}
  for i,j in [(i,j) for i in mask for j in mask if i<j]:
   if intersects(hs[i],hs[j]):contradiction=dict(kind='owned_hulls_intersect',owners=[i,j],round=ri+1,hulls=[hs[i],hs[j]]);break
  if contradiction:break
 round.update(complete=len(round['cells'])==len(mask) and all(c['complete'] for c in round['cells']),added_owned_vertices=added)
 guard_capture=round['complete'] and all(c['inside_local_guard'] for c in round['cells'])
 write()
 if contradiction or guard_capture or time.monotonic()>deadline or not added:break
print(json.dumps(dict(rounds=len(rounds),contradiction=bool(contradiction),inside_guard=guard_capture,seconds=time.monotonic()-start)),flush=True)
