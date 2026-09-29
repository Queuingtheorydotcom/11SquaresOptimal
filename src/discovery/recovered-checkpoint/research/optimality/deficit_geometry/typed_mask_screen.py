"""Bounded finite typed-mask LP discovery. No continuum exclusion is claimed."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,hashlib,time,resource,warnings
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/stromquist'))
sys.path.insert(0,str(ROOT/'research/reweight'))
from true_majority_model import TrueMajorityModel
from trump_anchor_screen import Restricted
OUT=Path(__file__).parent/'typed_masks'
SOURCE=ROOT/'research/true_catalogue/round6-cutround12-surplus-3.8754-full/proposal.json'
COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
CAPTURE=ROOT/'research/optimality/global_capture/trump-cell-symmetric-assignments.json'
POSES=Path(__file__).parent/'endpoint-sample.npz'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def symmetries(c,selected):
    """Prove closure of every selected physical feature orbit under D4."""
    LD=int(F(c['L'])*c['coordinate_denominator']);orbits=[];points=[]
    for x,y,w in c['point_orbits']:
        orb=sorted({(a,b) for u,v in ((x,y),(y,x)) for a in (u,LD-u) for b in (v,LD-v)})
        ids={p:len(points)+i for i,p in enumerate(orb)};orbits.append(ids);points.extend(orb)
    images=[];npids=len(orbits)
    for swap in (False,True):
        for sx in (-1,1):
            for sy in (-1,1):
                mapping=[]
                for ids in orbits:
                    for x,y in ids:
                        a,b=(y,x) if swap else (x,y);q=(a if sx==1 else LD-a,b if sy==1 else LD-b)
                        mapping.append(ids[q])
                for k in selected:
                    if k<npids:continue
                    sets=c['charge_orbits'][k-npids]['sets'];source={tuple(sorted(s)) for s in sets}
                    assert {tuple(sorted(mapping[i] for i in s)) for s in sets}==source
                images.append((swap,sx,sy))
    return images

def diverse_masks(cover,capture,limit=32):
    masks=cover['canonical_eleven_cell_subsets'];local={tuple(z) for z in capture['canonical_capture_masks']}
    ids=[i for i,m in enumerate(masks) if tuple(m) not in local]
    bits={i:sum(1<<k for k in masks[i]) for i in ids}; localbits=[sum(1<<k for k in m) for m in local]
    near={i:min((bits[i]^b).bit_count() for b in localbits) for i in ids}
    first=max(ids,key=lambda i:(near[i],-i));chosen=[first]
    while len(chosen)<limit:
        remaining=[i for i in ids if i not in chosen]
        chosen.append(max(remaining,key=lambda i:(min((bits[i]^bits[j]).bit_count() for j in chosen),near[i],-i)))
    return chosen,near

def main():
    start=time.time();OUT.mkdir(exist_ok=True);c=json.loads(SOURCE.read_text());cover=json.loads(COVER.read_text());capture=json.loads(CAPTURE.read_text())
    U=F(cover['side_upper']);L=F(c['L']);B=L/U;eps=F(1,10**10);core=B-eps
    model=TrueMajorityModel(SOURCE);selected=np.flatnonzero(np.array([p[2] for p in c['point_orbits']]+[g['weight'] for g in c['charge_orbits']],np.int64));assert len(selected)==158
    images=symmetries(c,selected);restricted=Restricted(model,selected);P=np.load(POSES)['poses'];assert len(P)<=5000
    rows=restricted.capture(float(core),P);sites=np.array([[float(F(x)) for x in cell['center']] for cell in cover['cells']]);nf=len(selected)
    alltyped=[];provenance=[];counts=np.zeros(16,int);ties=0
    for im,(swap,sx,sy) in enumerate(images):
        centered=P[:,1:]-float(L)/2
        if swap:centered=centered[:,::-1]
        centers=float(L)/2+centered*[sx,sy]
        # q is the actual centered unit-parent center. This uses B, not core.
        q=centers/float(B)-float(U)/2
        normalized=q/(float(U)-1)+.5
        dist=((normalized[:,None,:]-sites[None,:,:])**2).sum(axis=2)
        included=dist<=dist.min(axis=1)[:,None]+2e-12
        ties+=int((included.sum(axis=1)>1).sum())
        for cell in range(16):
            ii=np.flatnonzero(included[:,cell]);counts[cell]+=len(ii)
            alltyped.append(np.column_stack([np.full(len(ii),cell,np.uint8),rows[ii]]))
            provenance.extend((int(i),im,cell) for i in ii)
    typed=np.vstack(alltyped);unique,first=np.unique(typed,axis=0,return_index=True);provenance=np.array(provenance,np.int64)[first]
    cells=unique[:,0].astype(int);R=unique[:,1:];unique_counts=np.bincount(cells,minlength=16);assert np.all(unique_counts>0)
    masks,distances=diverse_masks(cover,capture);budget=model.budget[selected]
    # Every sampled typed row says gamma_cell <= row dot weights.
    upper=sparse.hstack([-sparse.csr_matrix(R.astype(float)),sparse.csr_matrix((np.ones(len(R)),(np.arange(len(R)),cells)),shape=(len(R),16))],format='csr')
    objective=np.r_[budget,np.zeros(16)];results=[];solutions=[];gammas=[]
    print('CAPTURE',len(P),'source poses;',len(typed),'D4 typed rows;',len(R),'unique; cells',unique_counts.tolist(),flush=True)
    np.savez_compressed(OUT/'finite-typed-pool.npz',source_poses=P,source_rows=rows,selected_columns=selected,typed_rows=R,typed_cells=cells,provenance=provenance,budget=budget,core=float(core),homothety_B=float(B))
    for index in masks:
        mask=cover['canonical_eleven_cell_subsets'][index];last=np.zeros(nf+16);last[nf+np.array(mask)]=-1
        A=sparse.vstack([upper,sparse.csr_matrix(last[None,:])],format='csr');rhs=np.r_[np.zeros(len(R)),-11]
        begin=time.time()
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='Unrecognized options detected')
            res=linprog(objective,A_ub=A,b_ub=rhs,bounds=(0,None),method='highs-ds',options={'threads':1,'time_limit':60,'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
        record=dict(mask_index=index,mask=mask,minimum_hamming_distance_from_capture_masks=distances[index],solver_success=bool(res.success),solver_message=res.message,seconds=time.time()-begin)
        if res.success:
            w=np.maximum(res.x[:nf],0);v=R@w;gamma=np.array([v[cells==k].min() for k in range(16)])
            scale=11/gamma[mask].sum();w*=scale;gamma*=scale;M=float(budget@w);margin=11-M
            record.update(budget=M,finite_pruning_margin=margin,positive_finite_pruning_margin=bool(margin>1e-6),positive_weight_count=int((w>1e-10).sum()),cell_lower_bounds=gamma.tolist(),selected_lower_bound_sum=float(gamma[mask].sum()),minimum_finite_slack=float((R@w-gamma[cells]).min()),weight_solution_index=len(solutions))
            solutions.append(w);gammas.append(gamma)
        results.append(record);print(json.dumps(record),flush=True)
        snapshot=dict(status='FINITE_TYPED_MASK_LP_DISCOVERY_ONLY',global_optimality=False,continuum_masks_excluded=0,source_sha256=sha(SOURCE),cover_sha256=sha(COVER),capture_masks_sha256=sha(CAPTURE),source_pose_sha256=sha(POSES),ambient_L=str(L),parent_Uplus=str(U),fixed_homothety_B=str(B),strict_core_epsilon=str(eps),strict_core_side=str(core),coordinate_convention='Actual centered unit-parent center q=(fieldcenter-L/2)/B; cover normalized u=q/(Uplus-1)+1/2. The homothety B is fixed independently of the strict core side.',source_pose_count=len(P),source_pose_domain='The existing fundamental-angle sample plus exact D4 profile invariance; no newly sampled poses.',D4_images=len(images),selected_feature_D4_closure_exact=True,typed_rows_before_dedup=len(typed),unique_typed_rows=len(R),source_image_memberships_per_cell=counts.tolist(),unique_profiles_per_cell=unique_counts.tolist(),numerical_near_ties_included_in_all_closed_cells=ties,positive_columns=nf,selected_mask_indices=masks,finished_masks=len(results),finite_positive_masks=sum(r.get('positive_finite_pruning_margin',False) for r in results),results=results,maximum_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,elapsed=time.time()-start,scope='Sample inequalities only. A positive finite margin is a candidate for exact continuum typed verification, not a mask exclusion. D4 feature closure is exact; captures, membership, and LP weights are numerical. Pairwise compatibility constraints are not added to the LP.')
        (OUT/'screen.json').write_text(json.dumps(snapshot,indent=2)+'\n');np.savez_compressed(OUT/'solutions.npz',weights=np.array(solutions),gamma=np.array(gammas),selected_columns=selected)
    print('SUMMARY',json.dumps({k:v for k,v in snapshot.items() if k!='results'}),flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=1):main()
