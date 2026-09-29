"""Exact rational common-interior points from numerical ray seeds.
Every output point is checked using rational squared distances to all vertices.
"""
from pathlib import Path
from fractions import Fraction as F
import json, math, argparse
ROOT=Path('/workspace/scratch/6def36ddf53b/current')
p=argparse.ArgumentParser();p.add_argument('packet',type=Path);p.add_argument('output',type=Path);p.add_argument('--directions',type=int,default=16);a=p.parse_args()
d=json.loads(a.packet.read_text());cover=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text());L=F(191,50);U=F(d['parent_Uplus']);B=L/U
fields=[];margins=[]
for cell in cover['cells']:
 g=tuple(map(F,cell['center']));vects=[tuple((U-1)*(F(x)-y) for x,y in zip(v,g)) for v in cell['vertices']];gen=tuple(B/2+(L-B)*x for x in g)
 offsets=[(F(0),F(0)),(F(1,200),F(0)),(-F(1,200),F(0)),(F(0),F(1,200)),(F(0),-F(1,200))]
 for i in range(a.directions):
  angle=2*math.pi*i/a.directions;ux,uy=math.cos(angle),math.sin(angle)
  rr=min(float(v[0])*ux+float(v[1])*uy+math.sqrt((float(v[0])*ux+float(v[1])*uy)**2+.25-sum(float(x)**2 for x in v)) for v in vects)
  off=(F(round(rr*ux*.999*10**7),10**7),F(round(rr*uy*.999*10**7),10**7))
  assert all(sum((x-y)**2 for x,y in zip(v,off))<F(1,4) for v in vects)
  offsets.append(off)
 offsets=list(dict.fromkeys(offsets));fields.append([[str(z+B*x) for z,x in zip(gen,off)] for off in offsets]);margins.append(str(min(F(1,4)-sum((x-y)**2 for x,y in zip(v,off)) for v in vects for off in offsets)))
d.pop('ownership_offsets_unit',None);d['ownership_points_field']=fields;d['ownership_enlargement_method']='Numerically proposed ray points; every rational point exactly checked in strict radius-one-half disks of all cell vertices.';d['ownership_minimum_squared_slack_by_cell']=margins;d['geometry_coverage']=False;d['continuum_masks_excluded']=0;d['status']='FINITE_NONSYMMETRIC_PHYSICAL_PROPOSAL';a.output.write_text(json.dumps(d,indent=2)+'\n')
print(a.output)
