from pathlib import Path
import sys,json,time
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/phase3/hull'))
import audit_capture_v6 as A
from coverage_mesh import make_mesh
F=A.F
files=['work/phase3/generic/mask1745-no-collision.json','work/phase3/generic/mask2158-drop1.json']
records=[];examples=[]
for name in files:
 d=json.loads((ROOT/name).read_text());U=F(d['U']);B=F(d['B']);count=0
 for step in d['steps']:
  prior=A.groups(step['prior_owned_hulls']);owner=step['owner']
  for ridx,row in enumerate(step['rows']):
   if ridx%7:continue
   P=A.poly(row['input_domain']);Q=A.poly(row['core_vertices'])
   if not P or not Q:continue
   a,b=map(F,row['interval']);h=B*min(sum(A.geo.cs(t)) for t in (a,b))/2
   P=A.clipped(P,[(1,0,A.geo.L-h),(-1,0,-h),(0,1,A.geo.L-h),(0,-1,-h)])
   if not A.geo.twice_area(P):continue
   negative=[(-x,-y) for x,y in Q]
   regions=[A.geo.gift_hull([(p[0]+q[0],p[1]+q[1]) for p in H for q in negative]) for j,H in prior.items() if j!=owner]
   regions += [A.geo.gift_hull(A.poly(r['vertices'])) for r in row.get('collision_regions',[])]
   regions += [A.geo.gift_hull(A.poly(p)) for p in row['residual_polygons'] if A.geo.twice_area(A.poly(p))]
   t=time.monotonic();mesh=make_mesh(P,regions);mesh_seconds=time.monotonic()-t
   assert mesh['status']=='COMPLETE_TRIANGLE_COVER_PROPOSAL'
   t=time.monotonic();old=A.geo.union_cover(P,regions);old_seconds=time.monotonic()-t
   assert old['passed']
   records.append(dict(source=name,step=step['index'],row=ridx,triangles=len(mesh['triangles']),mesh_seconds=mesh_seconds,
                       arrangement_seconds=old_seconds,arrangement_slabs=old['accepted_slabs']))
   examples.append(dict(domain=P,regions=regions,mesh=mesh))
   print(json.dumps(records[-1]),flush=True);count+=1
   if count==12:break
  if count==12:break
out=Path(__file__).parent
(out/'mesh-benchmark.json').write_text(json.dumps(dict(records=records),indent=2)+'\n')
(out/'mesh-benchmark-inputs.json').write_text(json.dumps(examples,default=str,separators=(',',':'))+'\n')
