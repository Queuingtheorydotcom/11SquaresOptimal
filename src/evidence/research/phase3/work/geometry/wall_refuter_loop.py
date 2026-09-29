"""Bounded point pricing for a frozen physical charge field.
Every proposed point is independently exact checked by validate_wall_sites
and rechecked by the mask adapter; numerical polygon proposals are not premises.
"""
from wall_kernel import *
import validate_wall_sites as exact
import subprocess,os,sys,time,hashlib
HERE=Path(__file__).resolve().parent
startpacket=Path(sys.argv[1]);startresult=Path(sys.argv[2]);rounds=int(sys.argv[3]) if len(sys.argv)>3 else 8
packet=json.loads(startpacket.read_text());result=json.loads(startresult.read_text());D=json.loads((HERE/'wall_kernel_discovery.json').read_text());history=[]
for it in range(1,rounds+1):
 witnesses=[r for r in result['records'] if 'parent_witness' in r]
 if not witnesses:print('NO_NEW_WITNESS',result['status'],flush=True);break
 r=witnesses[-1];w=r['parent_witness'];q=np.array([float(F(x)/B) for x in w['center']]);t=float(F(w['half_angle']));c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);ns=[np.array([c,s]),np.array([-s,c])];accepted=[]
 for row in D:
  j=row['cell']
  if j not in result['mask'] or j==r['cell']:continue
  kw=np.array(row['polygon'])
  for n in ns:
   for sign in [-1,1]:kw=clip(kw,sign*n,.5+q@(sign*n))
  if not len(kw):continue
  point=tuple(F(round(sum(v[k] for v in kw)/len(kw)*10**12),10**12) for k in range(2))
  poly=[tuple(F(1,2)+(exact.U-1)*F(x) for x in p) for p in cover['cells'][j]['vertices']]
  receipt=exact.validate(point,poly)
  if not receipt['status'].startswith('PASS'):continue
  field=[str(exact.B*x) for x in point]
  if field in packet['ownership_points_field'][j]:continue
  packet['ownership_points_field'][j].append(field)
  accepted.append(dict(owner=j,point=point,**receipt))
 entry=dict(iteration=it,witness_cell=r['cell'],witness_halfangle=w['half_angle'],added_points=accepted)
 if not accepted:
  print('NO_NEW_WALL_POINT',entry,flush=True);history.append(entry);break
 path=HERE/f'mask2141_wall_round{it}_packet.json';out=HERE/f'mask2141_wall_round{it}_result.json';log=HERE/f'mask2141_wall_round{it}.log';path.write_text(json.dumps(packet,indent=2))
 with log.open('w') as f:subprocess.run([sys.executable,str(HERE/'verify_wall_aware_mask.py'),str(path),'--output',str(out),'--seconds','90'],stdout=f,stderr=subprocess.STDOUT,check=True,env={**os.environ,'OPENBLAS_NUM_THREADS':'1'})
 result=json.loads(out.read_text());last=result['records'][-1];entry.update(status=result['status'],rows=result['rows'],cell=last['cell'],last_status=last['status']);history.append(entry)
 (HERE/'wall_refuter_loop_history.json').write_text(json.dumps(history,indent=2,default=str));print({k:v for k,v in entry.items() if k!='added_points'},'newpoints',len(accepted),flush=True)
 if result['continuum_masks_excluded']:break
(HERE/'wall_refuter_loop_history.json').write_text(json.dumps(history,indent=2,default=str))
