"""Single fresh-process typed-mask LP repair, reusing saved numerical captures."""
from pathlib import Path
from fractions import Fraction as F
import argparse,json,time,resource,warnings
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).parent/'typed_masks'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mask',type=int,default=2045);ap.add_argument('--round',type=int,default=1);ap.add_argument('--exact',type=Path);a=ap.parse_args();start=time.time()
    cover=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text());U=float(F(cover['side_upper']));L=3.82;B=L/U
    mask=cover['canonical_eleven_cell_subsets'][a.mask];sites=np.array([[float(F(x)) for x in c['center']] for c in cover['cells']]);pool=np.load(BASE/'finite-typed-pool.npz');selected=pool['selected_columns'];budget=pool['budget'];n=len(selected)
    typed=[np.column_stack([pool['typed_cells'],pool['typed_rows']]).astype(np.uint8)];source_files=[]
    for batch in range(1,a.round+1):
        file=BASE/f'mask{a.mask}-stress{batch}.npz';z=np.load(file);assert np.array_equal(z['selected_columns'],selected);P=z['poses'];R=z['rows'];source_files.append(file.name)
        for swap in (0,1):
            for sx in (-1,1):
                for sy in (-1,1):
                    centered=P[:,1:]-L/2
                    if swap:centered=centered[:,::-1]
                    u=(centered*[sx,sy]/B)/(U-1)+.5
                    d=((u[:,None,:]-sites[None,:,:])**2).sum(axis=2);included=d<=d.min(axis=1)[:,None]+2e-12
                    for cell in range(16):
                        ii=np.flatnonzero(included[:,cell]);typed.append(np.column_stack([np.full(len(ii),cell,np.uint8),R[ii]]))
    exact_count=0
    if a.exact:
        zz=np.load(a.exact);assert np.array_equal(zz['selected_columns'],selected)
        typed.append(np.column_stack([zz['typed_cells'],zz['typed_rows']]).astype(np.uint8));exact_count=len(zz['typed_cells'])
    allrows=np.unique(np.vstack(typed),axis=0);del typed
    cell=allrows[:,0].astype(int);R=allrows[:,1:];inmask=np.isin(cell,mask);eligible=np.flatnonzero(inmask)
    if a.round>1:previous=np.load(BASE/f'mask{a.mask}-repair{a.round-1}.npz')['weights']
    else:previous=np.load(BASE/'solutions.npz')['weights'][next(r for r in json.loads((BASE/'screen.json').read_text())['results'] if r['mask_index']==a.mask)['weight_solution_index']]
    scores=R@previous;active=[]
    for k in mask:
        ii=np.flatnonzero(cell==k);active.extend(ii[np.argsort(scores[ii])[:80]])
    active=np.unique(np.r_[active,eligible[np.linspace(0,len(eligible)-1,500,dtype=int)]]).astype(int)
    last=np.zeros(n+16);last[n+np.array(mask)]=-1;history=[]
    import ctypes,gc
    for iteration in range(25):
        rr=R[active];cc=cell[active]
        bounds=sparse.hstack([-sparse.csr_matrix(rr.astype(float)),sparse.csr_matrix((np.ones(len(rr)),(np.arange(len(rr)),cc)),shape=(len(rr),16))],format='csr')
        matrix=sparse.vstack([bounds,sparse.csr_matrix(last[None,:])],format='csr');rhs=np.r_[np.zeros(len(rr)),-11]
        del bounds;gc.collect();ctypes.CDLL(None).malloc_trim(0)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='Unrecognized options detected')
            res=linprog(np.r_[budget,np.zeros(16)],A_ub=matrix,b_ub=rhs,bounds=(0,None),method='highs-ds',options={'threads':1,'time_limit':60,'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
        assert res.success,res.message
        deficits=res.x[n:][cell]-R@res.x[:n];bad=np.flatnonzero(inmask&(deficits>1e-8))
        history.append(dict(iteration=iteration,active_rows=len(active),violated_rows=len(bad),relaxed_budget=float(res.fun)));print(json.dumps(history[-1]),flush=True)
        if not len(bad):break
        extra=bad[np.argsort(deficits[bad])[-256:]];active=np.unique(np.r_[active,extra])
        assert len(active)<=7800
    assert res.success,res.message;w=np.maximum(res.x[:n],0);v=R@w;gamma=np.array([v[cell==k].min() for k in range(16)]);scale=11/gamma[mask].sum();w*=scale;gamma*=scale;M=float(budget@w)
    output=BASE/f'mask{a.mask}-repair{a.round}';np.savez_compressed(output.with_suffix('.npz'),weights=w,gamma=gamma,selected_columns=selected,budget=budget,typed_rows=R,typed_cells=cell)
    report=dict(status='FINITE_TYPED_MASK_REPAIR_ONLY',mask_index=a.mask,mask=mask,round=a.round,source_stress_files=source_files,unique_typed_profiles=len(R),mask_profiles=len(eligible),active_lp_rows=len(active),active_constraint_history=history,budget=M,finite_pruning_margin=11-M,positive_finite_margin=bool(M<11-1e-6),positive_weight_count=int((w>1e-10).sum()),cell_lower_bounds=gamma.tolist(),minimum_finite_slack=float((R@w-gamma[cell]).min()),homothety_B=str(F('3.82')/F(cover['side_upper'])),core_side=str(F('3.82')/F(cover['side_upper'])-F(1,10**10)),global_geometry_coverage=False,global_optimality=False,maximum_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,elapsed=time.time()-start)
    report['exact_additional_capture_source']=str(a.exact) if a.exact else None
    report['exact_additional_typed_rows']=exact_count
    output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':
    with threadpool_limits(limits=1):main()
