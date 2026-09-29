"""Exact one-parent diagnostics; no packing feasibility/exclusion claim."""
from pathlib import Path
from fractions import Fraction as F
import json,math,sys,hashlib
import verify_coupled_polygon_charge as v

def main():
 H=Path(__file__).resolve().parent
 gate=json.loads((H/'mask1383_coupled_polygon_gate.json').read_text());packet=json.loads((H/'mask1383_generic2_packet.json').read_text());source=json.loads((H/'mask1383_collision_propagation_r2.json').read_text());state=source['final_state'];B=F(source['B']);U=F(source['U']);L=F(191,50)
 r=next(r for r in reversed(gate['records']) if r.get('pieces') and r['pieces'][-1].get('low_charge_center'));cell=r['cell'];t=sum(map(F,r['interval']))/2;c,s=v.cv.cs(t);radius=B*(c+s)/2
 # Round only the proposed witness; every conclusion below is checked exactly.
 cen=tuple(max(radius,min(L-radius,F(round(float(F(x))*10**12),10**12))) for x in r['pieces'][-1]['low_charge_center'])
 world=v.parse(r['prior_residual_outer_hull']);hulls={int(j):v.cv.hull(v.parse(P)) for j,P in state['groups'].items()}
 P=v.parent_hull(dict(center=cen,half_angle=t,side=B));wall=all(0<=x<=L and 0<=y<=L for x,y in P);indomain=all(n[0]*cen[0]+n[1]*cen[1]<=b for n,b in v.cv.rows(world));owns=all(all(n[0]*p[0]+n[1]*p[1]<b for n,b in v.cv.rows(P)) for p in hulls[cell]);intersections=[j for j,H in hulls.items() if j!=cell and v.intersects(P,H)]
 data=v.av.expand(packet['certificate']);uv=[((c*x+s*y)/data[4],(-s*x+c*y)/data[4]) for x,y in data[0]];center=(c*cen[0]+s*cen[1],-s*cen[0]+c*cen[1]);half=B/2;scale=math.lcm(half.denominator,*(x.denominator for p in uv+[center] for x in p));charge=v.av.true_charge(data,[tuple(int(x*scale) for x in p) for p in uv],int(half*scale),tuple(int(x*scale) for x in center))
 Qi=[tuple(v.pc.F((B-F(1,10**12))*(a*c-b*s)/2) for a,b in [])]
 Qi=[(v.pc.F((B-F(1,10**12))*(a*c-b*s)/2),v.pc.F((B-F(1,10**12))*(a*s+b*c)/2)) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
 domain=v.pc.geo.hull([p for poly in state['cells'][str(cell)][r['prior_row']]['residual_polygons'] for p in poly]);blocked=[]
 for owner,oldrows in state['cells'].items():
  owner=int(owner)
  if owner==cell:continue
  rows=[]
  for old in oldrows:
   lo,hi=map(v.pc.F,old['interval']);D=v.pc.geo.hull([p for poly in old['residual_polygons'] for p in poly]);Q=v.polycore.polygon_core(lo,hi,v.pc.F(U))['vertices'] if D else []
   rows.append(dict(core=Q,domain=D,reference=old['reference']))
  K=v.kernels.col.PartnerCover(rows).kernel(Qi,domain)['vertices'];C=tuple(map(v.pc.F,cen))
  if K and all(n[0]*C[0]+n[1]*C[1]<=h for n,h in v.pc.geo.rows(K)):blocked.append(owner)
 out=dict(status='EXACT_ONE_PARENT_DIAGNOSTIC',source_sha256=v.sha(H/'mask1383_collision_propagation_r2.json'),packet_sha256=v.sha(H/'mask1383_generic2_packet.json'),cell=cell,wall_legal=wall,inside_prior_domain=indomain,contains_own_hull=owns,intersected_other_hulls=intersections,universal_collision_blockers=blocked,parent_witness=dict(center=cen,half_angle=t,side=B,charge_units=charge,required_units=packet['threshold_units'][cell]),mask_exclusion_proved=False)
 (H/'mask1383_coupled_refuter.json').write_text(json.dumps(out,default=str,indent=2)+'\n');print(json.dumps(out,default=str,indent=2))
if __name__=='__main__':main()
