"""One asymmetric typed-mask LP with chunked full-pool scoring and checkpoints."""
from pathlib import Path
from fractions import Fraction as F
import argparse,json,time,resource,warnings,gc,ctypes,mmap,hashlib
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
from data import Rows
OUT=Path(__file__).parent;ROOT=OUT.parents[3]
def save(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)
def score(R,w):
    result=np.empty(len(R))
    for lo in range(0,len(R),2048):result[lo:lo+2048]=np.asarray(R[lo:lo+2048],float)@w
    R._mmap.madvise(mmap.MADV_DONTNEED)
    return result
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mask',type=int,default=2140);ap.add_argument('--seconds',type=float,default=180);ap.add_argument('--iterations',type=int,default=30);ap.add_argument('--extra',type=Path,action='append',default=[]);ap.add_argument('--tag',default='');ap.add_argument('--dataset',type=Path,default=OUT);ap.add_argument('--ownership',choices=['none','cell_generators','cell_fivepoints'],default='none');a=ap.parse_args();start=time.time();stem=f'mask{a.mask}'+('-'+a.tag if a.tag else '');a.dataset=a.dataset.resolve();a.extra=[p.resolve() for p in a.extra]
    coverfile=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json';cover=json.loads(coverfile.read_text());mask=cover['canonical_eleven_cell_subsets'][a.mask]
    capture=json.loads((a.dataset/'capture-progress.json').read_text());assert capture['status']=='COMPLETE_PHYSICAL_CAPTURE_WITH_EXACT_OVERRIDES'
    extras=[np.load(p) for p in a.extra];extra_rows=np.vstack([z['rows'] for z in extras]) if extras else None
    R=Rows(a.dataset/'rows.npy',extra_rows)
    if a.ownership=='none':membership=np.vstack([np.load(a.dataset/'memberships.npy'),*[z['memberships'] for z in extras]])
    else:
        membership=np.vstack([np.load(a.dataset/'raw-memberships.npy'),*[z['memberships'] for z in extras]]);legal=np.concatenate([np.load(a.dataset/'legal.npy'),*[z['legal'] for z in extras]]);capturekey='fivepoint' if a.ownership=='cell_fivepoints' else 'generator';captured=np.vstack([np.load(a.dataset/(capturekey+'-captures.npy')),*[z[capturekey+'_captures'] for z in extras]])
        for path in a.extra:assert json.loads(path.with_suffix('.json').read_text())['parent_Uplus']==capture['parent_Uplus']
        # Discovery-only strengthening by independently certified wall-owned points.
        wall_groups=json.loads(Path('/workspace/scratch/6def36ddf53b/work/geometry/wall_ownership_groups.json').read_text())['groups']
        poses=np.vstack([np.load(a.dataset/'poses.npy'),*[z['poses'] for z in extras]])
        B=float(F(capture['fixed_homothety_B']));cc=np.cos(poses[:,0]);ss=np.sin(poses[:,0])
        for owner,group in enumerate(wall_groups):
            for point in group:
                dx=float(F(point[0]))-poses[:,1];dy=float(F(point[1]))-poses[:,2]
                captured[:,owner]|=np.maximum(abs(cc*dx+ss*dy),abs(-ss*dx+cc*dy))<B/2-2e-12
        del poses,cc,ss
        for k in range(16):membership[:,k]&=legal & ~np.any(captured[:,[j for j in mask if j!=k]],axis=1)
    typedrow,typedcell=np.where(membership);eligible=np.flatnonzero(np.isin(typedcell,mask));n=R.shape[1]
    counts=membership.sum(axis=0);assert np.all(counts[mask]>0),f'Empty finite owned cells: {counts}'
    memberfile=OUT/f'{stem}-memberships.npy';np.save(memberfile,membership)
    arrays=np.load(OUT/'model-arrays.npz');capacity=arrays['capacity'];baseline=arrays['baseline_weights'];baselineq=score(R,baseline)
    bg=np.array([baselineq[membership[:,k]].min() if counts[k] else 0 for k in range(16)]);bscale=11/bg[mask].sum();bestw=baseline*bscale;bestg=bg*bscale;bestmass=float(capacity@bestw);baseline_mass=bestmass
    active=[]
    for k in mask:
        ii=np.flatnonzero(typedcell==k);active.extend(ii[np.argsort(baselineq[typedrow[ii]])[:100]])
    active=np.unique(np.r_[active,eligible[np.linspace(0,len(eligible)-1,600,dtype=int)]]).astype(int)
    history=[];report=dict(status='NO_SUCCESSFUL_LP',mask_index=a.mask,mask=mask);status='ITERATION_LIMIT';rng=np.random.default_rng(1232+a.mask);last=np.zeros(n+16);last[n+np.array(mask)]=-1
    for iteration in range(a.iterations):
        if time.time()-start>a.seconds:status='TIME_LIMIT';break
        ar=typedrow[active];ac=typedcell[active];rr=np.array(R[ar],float)
        matrix=sparse.hstack([-sparse.csr_matrix(rr),sparse.csr_matrix((np.ones(len(ar)),(np.arange(len(ar)),ac)),shape=(len(ar),16))],format='csr');matrix=sparse.vstack([matrix,sparse.csr_matrix(last[None,:])],format='csr');rhs=np.r_[np.zeros(len(ar)),-11]
        del rr;R._mmap.madvise(mmap.MADV_DONTNEED);gc.collect();ctypes.CDLL(None).malloc_trim(0)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='Unrecognized options detected')
            res=linprog(np.r_[capacity,np.zeros(16)],A_ub=matrix,b_ub=rhs,bounds=(0,None),method='highs-ds',options={'threads':1,'time_limit':min(30,max(1,a.seconds-(time.time()-start))),'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
        del matrix;gc.collect();ctypes.CDLL(None).malloc_trim(0)
        if not res.success:status='SOLVER_'+str(res.status);break
        w=np.maximum(res.x[:n],0);q=score(R,w);gamma=np.array([q[membership[:,k]].min() if counts[k] else 0 for k in range(16)]);gsum=gamma[mask].sum()
        mass=float(capacity@w)*11/gsum if gsum>1e-10 else 1e100
        if mass<bestmass:
            bestmass=mass;bestw=w*(11/gsum);bestg=gamma*(11/gsum)
        deficit=res.x[n:][typedcell]-q[typedrow];bad=eligible[deficit[eligible]>1e-8]
        record=dict(iteration=iteration,active_constraints=len(active),relaxed_budget=float(res.fun),violated_constraints=len(bad),full_pool_feasible_budget=mass,best_full_pool_budget=bestmass,seconds=time.time()-start,maximum_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024);history.append(record);print(json.dumps(record),flush=True)
        np.savez_compressed(OUT/f'{stem}-best.npz',weights=bestw,gamma=bestg,capacity=capacity,mask=np.array(mask),source_orbits=arrays['source_orbits'])
        report=dict(status='FINITE_PHYSICAL_MASK_LP_CHECKPOINT',mask_index=a.mask,mask=mask,individual_feature_count=n,source_pose_count=len(R),typed_constraints=len(eligible),symmetry_weight_equalities=False,baseline_symmetric_budget_on_same_pool=baseline_mass,best_budget=bestmass,finite_pruning_margin=11-bestmass,positive_weight_count=int((bestw>1e-10).sum()),cell_lower_bounds=bestg.tolist(),history=history,family_sha256=capture['family_sha256'],cover_sha256=capture['cover_sha256'],geometry_coverage=False,global_optimality=False,elapsed=time.time()-start,maximum_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
        report['discovery_wall_ownership_groups']='/workspace/scratch/6def36ddf53b/work/geometry/wall_ownership_groups.json'
        report['additional_exact_capture_files']=[str(p.relative_to(ROOT)) for p in a.extra]
        report['additional_exact_capture_rows']=sum(json.loads(p.with_suffix('.json').read_text()).get('exact_rows',len(z['rows'])) for p,z in zip(a.extra,extras))
        report['additional_numerical_capture_rows']=(0 if extra_rows is None else len(extra_rows))-report['additional_exact_capture_rows']
        report.update(dataset=str(a.dataset.relative_to(ROOT)),membership_file=str(memberfile.relative_to(ROOT)),conditional_ownership=a.ownership,retained_poses_by_cell=counts.tolist(),parent_Uplus=capture.get('parent_Uplus',cover['side_upper']))
        save(OUT/f'{stem}-result.json',report)
        if not len(bad):status='FINITE_FULL_POOL_LP_CONVERGED';break
        extra=[]
        for k in mask:
            bb=bad[typedcell[bad]==k]
            if len(bb):extra.extend(bb[np.argsort(deficit[bb])[-40:]]);extra.extend(rng.choice(bb,min(20,len(bb)),replace=False))
        active=np.unique(np.r_[active,extra]);
        if len(active)>8000:status='ACTIVE_ROW_LIMIT';break
    report.update(status=status,elapsed=time.time()-start,maximum_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024);save(OUT/f'{stem}-result.json',report)
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='history'}),flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=1):main()
