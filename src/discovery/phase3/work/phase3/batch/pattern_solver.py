"""Warm sparse-scored finite LP discovery. NEVER a continuum proof."""
from pathlib import Path
from fractions import Fraction as F
import json,time,hashlib,warnings,sys,argparse,os
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[3]/'current';OUT=ROOT/'research/optimality/deficit_geometry/physical_features';POOL=OUT/'p3-shared-pool';SOURCE=OUT/'owned-tight';U='387708359002281417731/100000000000000000000';WALL=ROOT.parent/'work/geometry/wall_ownership_groups.json';READY=False
REQ={'rows','memberships','legal','fivepoint_captures','generator_captures','poses'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(d,indent=2)+'\n');q.replace(p)
def compatible():
 answer=[]
 for p in sorted(OUT.glob('*.npz')):
  if not any(s in p.name for s in ['exact','refuter','jitter']):continue
  try:
   d=json.loads(p.with_suffix('.json').read_text())
   if d.get('parent_Uplus')!=U:continue
   with np.load(p) as z:
    if REQ<=set(z.files):answer.append((p,len(z['rows']),d.get('exact_rows',0)))
  except (OSError,KeyError,ValueError):pass
 return answer

def capture_bits(poses,captured):
 captured=captured.copy();B=float(F(json.loads((SOURCE/'capture-progress.json').read_text())['fixed_homothety_B']));c=np.cos(poses[:,0]);s=np.sin(poses[:,0]);groups=json.loads(WALL.read_text())['groups']
 for owner,group in enumerate(groups):
  for p in group:
   dx=float(F(p[0]))-poses[:,1];dy=float(F(p[1]))-poses[:,2]
   captured[:,owner]|=np.maximum(abs(c*dx+s*dy),abs(-s*dx+c*dy))<B/2-2e-12
 return (captured.astype(np.uint16)*(1<<np.arange(16,dtype=np.uint16))).sum(axis=1,dtype=np.uint16)

def prepare():
 POOL.mkdir(exist_ok=True);source=np.load(SOURCE/'rows.npy',mmap_mode='r');extras=compatible();N=len(source)+sum(n for _,n,_ in extras)
 dst=np.lib.format.open_memmap(POOL/'rows.npy',mode='w+',dtype=np.uint8,shape=(N,source.shape[1]));dst[:len(source)]=source
 P=[np.load(SOURCE/'poses.npy')];M=[np.load(SOURCE/'raw-memberships.npy')];L=[np.load(SOURCE/'legal.npy')];C=[np.load(SOURCE/'fivepoint-captures.npy')];off=len(source)
 for p,n,_ in extras:
  with np.load(p) as z:
   dst[off:off+n]=z['rows'];P.append(z['poses']);M.append(z['memberships']);L.append(z['legal']);C.append(z['fivepoint_captures']);off+=n
 dst.flush();poses=np.vstack(P);np.save(POOL/'poses.npy',poses);np.save(POOL/'raw-memberships.npy',np.vstack(M));np.save(POOL/'legal.npy',np.concatenate(L));np.save(POOL/'capture-bits.npy',capture_bits(poses,np.vstack(C)))
 baseline=np.load(OUT/'model-arrays.npz')['baseline_weights'];bq=np.empty(N)
 with threadpool_limits(limits=1):
  for start in range(0,N,4096):bq[start:start+4096]=np.asarray(dst[start:start+4096],float)@baseline
 np.save(POOL/'baseline-charge.npy',bq);meta=json.loads((SOURCE/'capture-progress.json').read_text());meta.update(pose_count=N,exact_override_rows=40+sum(n for _,_,n in extras),geometry_coverage=False,scope='Merged finite discovery pool; numerical rows and exact controls only, no continuum proof.');save(POOL/'capture-progress.json',meta)
 manifest=dict(status='FINITE_DISCOVERY_POOL',source_rows_sha256=sha(SOURCE/'rows.npy'),sources=[dict(path=str(p.relative_to(ROOT)),rows=n,exact_rows=e,sha256=sha(p)) for p,n,e in extras],wall_groups_sha256=sha(WALL),rows=N,features=source.shape[1],parent_Uplus=U,geometry_coverage=False,global_optimality_proved=False)
 save(POOL/'pool-manifest.json',manifest);print(json.dumps(dict(pool=str(POOL),rows=N,extra_files=len(extras))),flush=True)

def init():
 global READY,R0,M0,L0,BITS0,BQ0,CAP,BASELINE,ORBITS,MASKS,META,POOLED
 if READY:return
 threadpool_limits(limits=1);R0=np.load(POOL/'rows.npy',mmap_mode='r');M0=np.load(POOL/'raw-memberships.npy');L0=np.load(POOL/'legal.npy');BITS0=np.load(POOL/'capture-bits.npy');BQ0=np.load(POOL/'baseline-charge.npy');a=np.load(OUT/'model-arrays.npz');CAP=a['capacity'];BASELINE=a['baseline_weights'];ORBITS=a['source_orbits'];META=json.loads((POOL/'capture-progress.json').read_text());MASKS=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text())['canonical_eleven_cell_subsets'];POOLED={str((ROOT/p['path']).resolve()) for p in json.loads((POOL/'pool-manifest.json').read_text())['sources']};READY=True

def solve(mask,tag,pattern,seconds=60,iterations=30,extra=None):
 init();start=time.monotonic();idx=int(mask);original_mask=MASKS[idx];mask=sorted(pattern);assert mask and set(mask)<=set(original_mask);nslots=len(mask);stem=f'mask{idx}-{tag}';paths=[Path(p).resolve() for p in (extra or []) if str(Path(p).resolve()) not in POOLED];zs=[]
 for p in dict.fromkeys(paths):
  d=json.loads(p.with_suffix('.json').read_text());assert d['parent_Uplus']==U;z=np.load(p);assert REQ<=set(z.files);zs.append((p,{k:z[k] for k in REQ}));z.close()
 extra_R=np.vstack([z['rows'] for _,z in zs]) if zs else np.empty((0,R0.shape[1]),np.uint8)
 if zs:
  mem=np.vstack([M0,*[z['memberships'] for _,z in zs]]);legal=np.r_[L0,*[z['legal'] for _,z in zs]];bits=np.r_[BITS0,capture_bits(np.vstack([z['poses'] for _,z in zs]),np.vstack([z['fivepoint_captures'] for _,z in zs]))];bq=np.r_[BQ0,extra_R.astype(float)@BASELINE]
 else:mem=M0;legal=L0;bits=BITS0;bq=BQ0
 n=R0.shape[1];owned=sum(1<<i for i in mask);membership=np.zeros(mem.shape,bool)
 for k in mask:membership[:,k]=mem[:,k]&legal&((bits&(owned^(1<<k)))==0)
 inds=[np.flatnonzero(membership[:,k]) for k in mask];counts=membership.sum(axis=0)
 if not all(len(i) for i in inds):return dict(status='EMPTY_FINITE_DOMAIN_ONLY',mask_index=idx,mask=mask,geometry_coverage=False,global_optimality=False)
 row=np.concatenate(inds);cell=np.concatenate([np.full(len(r),i,dtype=int) for i,r in enumerate(inds)]);active=[];off=0
 for rr in inds:active.extend(off+np.argsort(bq[rr])[:100]);off+=len(rr)
 active=np.unique(np.r_[active,np.linspace(0,len(row)-1,600,dtype=int)]);last=sparse.csr_matrix(np.r_[np.zeros(n),-np.ones(nslots)][None,:]);rng=np.random.default_rng(idx+303)
 def rows(ii):
  a=np.empty((len(ii),n),np.uint8);base=ii<len(R0);a[base]=R0[ii[base]];a[~base]=extra_R[ii[~base]-len(R0)];return a
 def score(w):
  pos=np.flatnonzero(w>0);q=np.empty(len(mem));q[:len(R0)]=R0[:,pos].astype(float)@w[pos]
  if len(extra_R):q[len(R0):]=extra_R[:,pos].astype(float)@w[pos]
  return q
 bg=np.array([bq[rr].min() for rr in inds]);scale=11/bg.sum();bestw=BASELINE*scale;bestg=np.zeros(16);bestg[mask]=bg*scale;bestmass=float(CAP@bestw);history=[];status='ITERATION_LIMIT';baseline_mass=bestmass
 for iteration in range(iterations):
  if time.monotonic()-start>seconds:status='TIME_LIMIT';break
  mat=sparse.hstack([-sparse.csr_matrix(rows(row[active]).astype(float)),sparse.csr_matrix((np.ones(len(active)),(np.arange(len(active)),cell[active])),shape=(len(active),nslots))],format='csr');mat=sparse.vstack([mat,last],format='csr')
  with warnings.catch_warnings():
   warnings.simplefilter('ignore');res=linprog(np.r_[CAP,np.zeros(nslots)],A_ub=mat,b_ub=np.r_[np.zeros(len(active)),-11],bounds=(0,None),method='highs-ds',options={'threads':1,'time_limit':min(20,max(1,seconds-(time.monotonic()-start))),'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
  if not res.success:status='SOLVER_'+str(res.status);break
  w=np.maximum(res.x[:n],0);q=score(w);g=np.array([q[rr].min() for rr in inds]);gsum=g.sum();mass=float(CAP@w)*11/gsum if gsum>1e-10 else 1e99
  if mass<bestmass:bestmass=mass;bestw=w*11/gsum;bestg=np.zeros(16);bestg[mask]=g*11/gsum
  deficits=res.x[n:][cell]-q[row];bad=np.flatnonzero(deficits>1e-8);history.append(dict(iteration=iteration,active_constraints=len(active),violated_constraints=len(bad),best_full_pool_budget=bestmass,seconds=time.monotonic()-start))
  if not len(bad):status='FINITE_FULL_POOL_LP_CONVERGED';break
  add=[]
  for j in range(nslots):
   bb=bad[cell[bad]==j]
   if len(bb):add.extend(bb[np.argsort(deficits[bb])[-40:]]);add.extend(rng.choice(bb,min(20,len(bb)),replace=False))
  active=np.unique(np.r_[active,add])
  if len(active)>10000:status='ACTIVE_ROW_LIMIT';break
 memberfile=OUT/(stem+'-memberships.npy');np.save(memberfile,membership);np.savez_compressed(OUT/(stem+'-best.npz'),weights=bestw,gamma=bestg,capacity=CAP,mask=np.array(original_mask),source_orbits=ORBITS)
 report=dict(status=status,mask_index=idx,mask=original_mask,conditional_owner_support=mask,best_budget=bestmass,positive_weight_count=int(np.count_nonzero(bestw>1e-10)),cell_lower_bounds=bestg.tolist(),history=history,source_pose_count=len(mem),individual_feature_count=n,baseline_symmetric_budget_on_same_pool=baseline_mass,geometry_coverage=False,global_optimality=False,conditional_ownership='cell_fivepoints',parent_Uplus=U,dataset=str(POOL.relative_to(ROOT)),membership_file=str(memberfile.relative_to(ROOT)),additional_exact_capture_files=[str(p.relative_to(ROOT)) for p,_ in zs],additional_exact_capture_rows=sum(json.loads(p.with_suffix('.json').read_text()).get('exact_rows',0) for p,_ in zs),family_sha256=META['family_sha256'],cover_sha256=META['cover_sha256'],retained_poses_by_cell=counts.tolist(),elapsed=time.monotonic()-start,solver_source_sha256=sha(Path(__file__)),merged_pool_manifest_sha256=sha(POOL/'pool-manifest.json'))
 save(OUT/(stem+'-result.json'),report);return report
