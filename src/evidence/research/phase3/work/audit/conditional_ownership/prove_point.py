"""Exact one-cell ownership extension using only independently validated prior sites.
Imports the unchanged audited geometric kernel. No mask exclusion is asserted.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,importlib.util,json,time,hashlib,math,argparse
ROOT=Path('/workspace/scratch/6def36ddf53b/current')
SRC=ROOT/'research/optimality/asymmetric_coverage/verify.py'
spec=importlib.util.spec_from_file_location('ownership_asymmetric_kernel',SRC)
av=importlib.util.module_from_spec(spec);spec.loader.exec_module(av)
p=argparse.ArgumentParser();p.add_argument('--packet',type=Path,required=True);p.add_argument('--owner',type=int,required=True);p.add_argument('--offset',nargs=2,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=float,default=120);p.add_argument('--bins',type=int,default=32);p.add_argument('--max-depth',type=int,default=15);p.add_argument('--unconditioned',action='store_true');a=p.parse_args()
packet=json.loads(a.packet.read_text());cover=json.loads(av.typed.COVER.read_text());av.need(packet['cover_sha256']==av.typed.sha(av.typed.COVER)==av.typed.COVER_SHA256,'Cover hash mismatch')
av.U=F(packet['parent_Uplus']);av.PARENT=av.L/av.U
av.need(F(19377,5000)<=av.U<=av.typed.U,'Outside audited contraction range')
mask=packet['mask'];av.need(mask==cover['canonical_eleven_cell_subsets'][packet['mask_index']] and a.owner in mask,'Invalid mask/owner')
generators=av.owned_generators(cover)
if 'ownership_points_field' in packet:owned=av.validate_owned_sites(cover,packet['ownership_points_field'])
else:owned=av.owned_points(cover,generators,packet['ownership_offsets_unit'])
point=tuple(g+av.PARENT*F(x) for g,x in zip(generators[a.owner],a.offset));av.need(all(0<x<av.L for x in point),'New point outside field')
D=math.lcm(50,*(x.denominator for x in point))
certificate=dict(L=str(av.L),coordinate_denominator=D,weight_denominator=1,sites=[[int(x*D) for x in point]],point_weights=[1],features=[],budget_units=1)
data=av.expand(certificate)
if not a.unconditioned:data=av.conditioned_data(data,owned,mask,a.owner,1)
prepared=av.prepare_majority(data);world=av.field_polygon(cover,a.owner)
start=time.monotonic();pending=[(F(i,a.bins),F(i+1,a.bins),0) for i in reversed(range(a.bins))];accepted=[];records=[];failed=[]
while pending and time.monotonic()-start<a.seconds:
 lo,hi,depth=pending.pop();ans=av.verify_interval(data,prepared,world,lo,hi,1,5000);records.append(dict(depth=depth,**ans))
 if ans['status'].startswith('PASS'):accepted.append((lo,hi))
 elif ans['status']=='REFUTED_BY_LEGAL_PARENT':failed.append((lo,hi));break
 elif depth<a.max_depth:
  mid=(lo+hi)/2;pending.extend([(mid,hi,depth+1),(lo,mid,depth+1)])
 else:failed.append((lo,hi))
 if len(records)%100==0:print(json.dumps(dict(rows=len(records),accepted=len(accepted),pending=len(pending),seconds=time.monotonic()-start)),flush=True)
cursor=F(0)
for lo,hi in sorted(accepted):
 if lo!=cursor:break
 cursor=hi
complete=not pending and not failed and cursor==1
out=dict(status='PASS_EXACT_CONDITIONAL_POINT_OWNERSHIP' if complete else 'INCOMPLETE_CONDITIONAL_POINT_OWNERSHIP',global_optimality_proved=False,mask_exclusion_claimed=False,mask_index=packet['mask_index'],mask=mask,owner=a.owner,point=point,offset=a.offset,conditioned=not a.unconditioned,parent_Uplus=av.U,parent_side=av.PARENT,packet_sha256=av.typed.sha(a.packet),cover_sha256=av.typed.COVER_SHA256,prior_owned_points=owned,prior_owner_support=[] if a.unconditioned else [j for j in mask if j!=a.owner],induction_round=1,uses_learned_points=False,rows=len(records),accepted=sorted(accepted),failed=failed,pending=pending,records=records,seconds=time.monotonic()-start,dependencies={str(path):av.typed.sha(path) for path in [Path(__file__),SRC,av.BASE,*sorted((ROOT/'research/exact_checker').glob('*.py'))]},theorem='Conditional on a feasible packing with this occupied-cell mask, the parent assigned to owner contains point in its interior. Every row proves 1[point in strict core]+sum[prior other-owner points in strict core]>=1. All prior other-owner captures vanish in a feasible packing. Only a complete quarter-turn coverage gives this conclusion.')
av.typed.save(a.output,out);print(json.dumps({k:v for k,v in out.items() if k not in ('prior_owned_points','accepted','failed','pending','records','dependencies')},default=str,indent=2))
