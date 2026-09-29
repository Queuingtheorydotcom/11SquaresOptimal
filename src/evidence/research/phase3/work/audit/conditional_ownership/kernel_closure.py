"""Exact acyclic conditional ownership kernels. Discovery rays never imply proof.
Each round uses an immutable snapshot of previously proved owner sites.
"""
from pathlib import Path
from fractions import Fraction as F
import importlib.util,json,time,math,argparse,hashlib,sys
ROOT=Path('/workspace/scratch/6def36ddf53b/current');HERE=Path(__file__).parent
SRC=ROOT/'research/optimality/asymmetric_coverage/verify.py'
spec=importlib.util.spec_from_file_location('closure_asymmetric_kernel',SRC);av=importlib.util.module_from_spec(spec);spec.loader.exec_module(av)
sys.path.insert(0,str(HERE.parents[1]/'geometry'))
import validate_wall_sites as wall

def hull(points):
 p=sorted(set(points))
 if len(p)<=1:return p
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 def chain(p):
  out=[]
  for x in p:
   while len(out)>1 and cross(out[-2],out[-1],x)<=0:out.pop()
   out.append(x)
  return out
 return chain(p)[:-1]+chain(p[::-1])[:-1]

def overlap(a,b):
 # For positive-area convex polygons, edge-normal projection separation is exact.
 av.need(len(a)>=3 and len(b)>=3,'Owned hull lacks dimension')
 for poly in (a,b):
  for p,q in zip(poly,poly[1:]+poly[:1]):
   nx,ny=q[1]-p[1],p[0]-q[0]
   aa=[nx*x+ny*y for x,y in a];bb=[nx*x+ny*y for x,y in b]
   if max(aa)<min(bb) or max(bb)<min(aa):return False
 return True

def prove(point,owner,prior,deadline):
 D=math.lcm(50,*(x.denominator for x in point));data=([(int(point[0]*D),int(point[1]*D))],[1],[],[],D,[])
 data=av.conditioned_data(data,prior,mask,owner,1);prepared=av.prepare_majority(data);world=av.field_polygon(cover,owner)
 pending=[(F(i,32),F(i+1,32),0) for i in reversed(range(32))];accepted=[];records=[];failed=[]
 while pending and time.monotonic()<deadline:
  lo,hi,depth=pending.pop();ans=av.verify_interval(data,prepared,world,lo,hi,1,1000);records.append(dict(depth=depth,**ans))
  if ans['status'].startswith('PASS'):accepted.append((lo,hi))
  elif ans['status']=='REFUTED_BY_LEGAL_PARENT':failed.append((lo,hi));break
  elif depth<10:
   mid=(lo+hi)/2;pending.extend([(mid,hi,depth+1),(lo,mid,depth+1)])
  else:failed.append((lo,hi));break
 cursor=F(0)
 for lo,hi in sorted(accepted):
  if lo!=cursor:break
  cursor=hi
 complete=not pending and not failed and cursor==1
 return dict(status='PASS_EXACT_CONDITIONAL_POINT_OWNERSHIP' if complete else 'INCOMPLETE',point=point,owner=owner,accepted=sorted(accepted),pending=pending,failed=failed,records=records)

p=argparse.ArgumentParser();p.add_argument('--packet',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=float,default=280);p.add_argument('--rounds',type=int,default=2);p.add_argument('--owners',default='6,1,2,4,5,9');a=p.parse_args()
packet=json.loads(a.packet.read_text());cover=json.loads(av.typed.COVER.read_text());av.need(packet['cover_sha256']==av.typed.sha(av.typed.COVER)==av.typed.COVER_SHA256,'Cover mismatch')
av.U=F(packet['parent_Uplus']);av.PARENT=av.L/av.U;av.need(av.U==wall.U and av.PARENT==wall.B,'Wall premise target mismatch')
mask=packet['mask'];av.need(mask==cover['canonical_eleven_cell_subsets'][packet['mask_index']],'Mask mismatch');owners=list(map(int,a.owners.split(',')));av.need(set(owners)<=set(mask),'Unoccupied owner')
generators=av.owned_generators(cover);groups=[[tuple(map(F,p)) for p in group] for group in packet['ownership_points_field']]
wall_records=[]
for owner,group in enumerate(groups):
 poly=[tuple(F(1,2)+(av.U-1)*F(x) for x in v) for v in cover['cells'][owner]['vertices']]
 for point in group:
  result=wall.validate(tuple(x/av.PARENT for x in point),poly)
  av.need(result['status']=='PASS_EXACT_WALL_OWNERSHIP','Initial wall-owned point failed fresh exact replay')
  wall_records.append(dict(owner=owner,point=point,**result))
start=time.monotonic();deadline=start+a.seconds;rounds=[];proofs=[];attempts=[];contradiction=None
rays=[(1,0),(1,F(1,2)),(1,1),(F(1,2),1),(0,1),(-F(1,2),1),(-1,1),(-1,F(1,2)),(-1,0),(-1,-F(1,2)),(-1,-1),(-F(1,2),-1),(0,-1),(F(1,2),-1),(1,-1),(1,-F(1,2))]
def write():
 out=dict(status='PASS_EXACT_CONDITIONAL_HULL_MASK_EXCLUSION' if contradiction else 'PARTIAL_EXACT_CONDITIONAL_OWNERSHIP_KERNELS',global_optimality_proved=False,mask_exclusion_proved=bool(contradiction),mask_index=packet['mask_index'],mask=mask,parent_Uplus=av.U,parent_side=av.PARENT,packet_sha256=av.typed.sha(a.packet),cover_sha256=av.typed.COVER_SHA256,seed_wall_replay=wall_records,rounds=rounds,proofs=proofs,attempts=attempts,owned_points=groups,contradiction=contradiction,seconds=time.monotonic()-start,dependencies={str(path):av.typed.sha(path) for path in [Path(__file__),SRC,av.BASE,Path(wall.__file__),*sorted((ROOT/'research/exact_checker').glob('*.py'))]})
 av.typed.save(a.output,out)
for round_index in range(a.rounds):
 prior=[[p for p in group] for group in groups];prior_digest=hashlib.sha256(json.dumps(prior,default=str,separators=(',',':')).encode()).hexdigest();rounds.append(dict(index=round_index+1,prior_owned_points=prior,prior_snapshot_sha256=prior_digest));added=0
 for owner in owners:
  for direction in rays:
   if time.monotonic()>deadline:break
   lo,hi=F(0),F(1,4);best=None
   for depth in range(4):
    if time.monotonic()>deadline:break
    radius=(lo+hi)/2;point=tuple(g+av.PARENT*radius*v for g,v in zip(generators[owner],direction))
    t=time.monotonic();ans=prove(point,owner,prior,min(deadline,time.monotonic()+3));passed=ans['status'].startswith('PASS')
    attempts.append(dict(round=round_index+1,owner=owner,direction=direction,radius=radius,passed=passed,rows=len(ans['records']),last=ans['records'][-1]['status'] if ans['records'] else None,seconds=time.monotonic()-t))
    if passed:lo=radius;best=ans
    else:hi=radius
   if best is not None and tuple(best['point']) not in groups[owner]:
    best.update(round=round_index+1,prior_snapshot_sha256=prior_digest,direction=direction,radius=lo);proofs.append(best);groups[owner].append(tuple(best['point']));added+=1
   hh={j:hull(groups[j]) for j in mask}
   for i,j in [(i,j) for i in mask for j in mask if i<j]:
    if overlap(hh[i],hh[j]):contradiction=dict(owners=[i,j],owned_hulls=[hh[i],hh[j]],round=round_index+1);break
   write()
   if contradiction:break
  print(json.dumps(dict(round=round_index+1,owner=owner,proofs=len(proofs),attempts=len(attempts),seconds=time.monotonic()-start)),flush=True)
  if contradiction or time.monotonic()>deadline:break
 rounds[-1]['new_owned_points']=added
 if contradiction or time.monotonic()>deadline or not added:break
write();print(json.dumps(dict(proofs=len(proofs),attempts=len(attempts),contradiction=bool(contradiction),seconds=time.monotonic()-start)),flush=True)
