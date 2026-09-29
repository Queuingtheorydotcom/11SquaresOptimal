"""Exact-center pricing at selected narrow angle rows; discovery only.
Any legal-parent deficit is genuine, but passing sampled angles proves no
continuum statement beyond those explicitly checked tiny intervals.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,time,hashlib
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[1]/'geometry'));from verify_wall_aware_mask import av
if not __debug__:raise SystemExit('Assertions required.')
packet=Path(sys.argv[1]);out=Path(sys.argv[2]);c=json.loads(packet.read_text());av.U=F(c['parent_Uplus']);av.PARENT=av.L/av.U;cover=json.loads(av.typed.COVER.read_text());base=av.expand(c['certificate']);owned=av.validate_owned_sites(cover,c['ownership_points_field']);mask=c['mask'];gamma=c['threshold_units'];support=c.get('conditional_owner_support',mask);epsilon=F(1,2**32)
angles=list(dict.fromkeys([F(0),F(1,2048),F(1,128),F(1,32),F(1,8),F(1,4),F(1,2),F(3,4),F(1)]+[F(i,32) for i in range(33)]));rows=[];refuters=[];start=time.time()
for cell in mask:
 if not gamma[cell]:continue
 data=av.conditioned_data(base,owned,support,cell,gamma[cell]);prepared=av.prepare_majority(data);world=av.field_polygon(cover,cell)
 for t in angles:
  lo=max(F(0),t-epsilon);hi=min(F(1),t+epsilon);r=av.verify_interval(data,prepared,world,lo,hi,gamma[cell],5000);r=dict(cell=cell,depth=0,**r);rows.append(r)
  if r['status']=='REFUTED_BY_LEGAL_PARENT':
   report=dict(status='EXACT_PARENT_REFUTER_AT_SELECTED_ANGLE',parent_Uplus=str(av.U),parent_side=str(av.PARENT),packet_sha256=hashlib.sha256(packet.read_bytes()).hexdigest(),mask_index=c['mask_index'],mask=mask,records=[r],scope='Exact individual counterexample to proposed conditional threshold; no packing or mask exclusion asserted.')
   path=out.parent/f'{out.stem}_cell{cell}_refuter.json';path.write_text(json.dumps(report,indent=2,default=str));refuters.append(str(path));print('REFUTER',cell,str(t),r['parent_witness']['charge_units'],gamma[cell],flush=True);break
  if time.time()-start>120:break
 print('cell',cell,'seconds',time.time()-start,flush=True)
 if time.time()-start>120:break
out.write_text(json.dumps(dict(status='SELECTED_EXACT_ANGLE_PRICING',rows=rows,refuters=refuters,packet_sha256=hashlib.sha256(packet.read_bytes()).hexdigest(),seconds=time.time()-start),indent=2,default=str))
