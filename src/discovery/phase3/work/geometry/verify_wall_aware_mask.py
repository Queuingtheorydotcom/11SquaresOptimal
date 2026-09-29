"""Adapter adding independently certified wall-aware strict ownership.
All charge geometry is delegated unchanged to the hash-pinned upstream checker.
This adapter supplies a new ownership premise; it does not claim the upstream
inscribed-disk validator accepts wall-aware sites.
"""
from pathlib import Path
from fractions import Fraction as F
import importlib.util,argparse,json,hashlib,sys,os
if not __debug__:
    raise SystemExit('Exact verifier requires assertions; do not use python -O.')
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('ELEVEN_PACKING_ROOT', str(HERE.parents[1]/'current')))
UPSTREAM=ROOT/'research/optimality/asymmetric_coverage/verify.py'
UPSTREAM_SHA='3bce6069052493d6fe910a7d83cbf2108a4fe7d80eef4f48663e06a3286b7d2b'
assert hashlib.sha256(UPSTREAM.read_bytes()).hexdigest()==UPSTREAM_SHA
spec=importlib.util.spec_from_file_location('upstream_asymmetric_wall_adapter',UPSTREAM)
av=importlib.util.module_from_spec(spec);spec.loader.exec_module(av)
sys.path.insert(0,str(HERE));import validate_wall_sites as wall
WALL_SHA='e4ab3ce5c479d7a1be20528d1517ea50cedb3133e2d86e3748158386cde44fc1'
assert hashlib.sha256(Path(wall.__file__).read_bytes()).hexdigest()==WALL_SHA
OWNERSHIP_RECEIPTS=[]
def validate_owned_sites(cover,groups):
 assert av.U==wall.U and av.PARENT==wall.B,'Wall proof coordinates mismatch'
 assert type(groups) is list and len(groups)==16
 result=[]
 for j,group in enumerate(groups):
  assert type(group) is list and 1<=len(group)<=65
  assert all(type(p) is list and len(p)==2 for p in group)
  points=[tuple(map(F,p)) for p in group];assert len(set(points))==len(points)
  poly=[tuple(F(1,2)+(wall.U-1)*F(x) for x in p) for p in cover['cells'][j]['vertices']]
  for point in points:
   assert all(0<=v<=av.L for v in point)
   unit=tuple(x/wall.B for x in point)
   diskmax=max(sum((x-y)**2 for x,y in zip(unit,v)) for v in poly)
   if diskmax<F(1,4):receipt=dict(status='PASS_EXACT_DISK_OWNERSHIP',maximum_vertex_distance_squared=diskmax)
   else:
    receipt=wall.validate(unit,poly)
    assert receipt['status']=='PASS_EXACT_WALL_OWNERSHIP','Unproved point ownership'
   OWNERSHIP_RECEIPTS.append(dict(owner=j,field_point=point,unit_point=unit,**receipt))
  result.append(points)
 return result
av.validate_owned_sites=validate_owned_sites
ORIGINAL_SAVE=av.typed.save
def decorated_save(path,out):
 out=dict(out)
 out['ownership_proof']='Strict wall-aware ownership by complete rational half-angle interval envelopes and exact trigonometric support extrema; disk bounds used when sufficient.'
 out['ownership_receipts']=OWNERSHIP_RECEIPTS
 out['adapter_dependencies']={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [UPSTREAM,Path(__file__),Path(wall.__file__)]}
 out['scope']='This adapter supplies a new wall-aware ownership validator. The upstream geometric verifier is unchanged. Every ownership point has an exact continuum certificate. Only complete eleven-cell coverage plus the counting gap excludes the stated mask; no global optimality claim.'
 if out['status']=='PASS_EXACT_ASYMMETRIC_MASK_EXCLUSION':out['status']='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION'
 ORIGINAL_SAVE(path,out)
av.typed.save=decorated_save
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('packet',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--cells');p.add_argument('--bins',type=int,default=64);p.add_argument('--max-depth',type=int,default=14);p.add_argument('--max-rows',type=int,default=15000);p.add_argument('--seconds',type=float,default=300);p.add_argument('--patch-nodes',type=int,default=5000);a=p.parse_args()
 av.run(a)
