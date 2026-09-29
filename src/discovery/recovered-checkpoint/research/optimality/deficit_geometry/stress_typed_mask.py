"""Fresh full-quarter-turn, cell-clipped finite stress of a typed proposal."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,time,resource,argparse,math,hashlib
import numpy as np
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/stromquist'))
sys.path.insert(0,str(ROOT/'research/reweight'))
from true_majority_model import TrueMajorityModel
from trump_anchor_screen import Restricted
BASE=Path(__file__).parent/'typed_masks'
SOURCE=ROOT/'research/true_catalogue/round6-cutround12-surplus-3.8754-full/proposal.json'
COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'

def clip(poly,axis,value,sign):
    if len(poly)==0:return []
    result=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        fp=sign*(p[axis]-value);fq=sign*(q[axis]-value)
        if fp<=0:result.append(p)
        if fp*fq<0:
            t=fp/(fp-fq);result.append(p+t*(q-p))
    return result

def random_point(poly,rng,index):
    V=np.array(poly);center=V.mean(axis=0)
    if index%3==0:
        # Almost-boundary vertices detect narrow charge changes missed by area sampling.
        z=V[rng.integers(len(V))];e=10**rng.uniform(-9,-2)
        return (1-e)*z+e*center
    if index%3==1:
        k=rng.integers(len(V));t=rng.random();z=t*V[k]+(1-t)*V[(k+1)%len(V)]
        e=10**rng.uniform(-9,-2);return (1-e)*z+e*center
    triangles=[(V[0],V[i],V[i+1]) for i in range(1,len(V)-1)]
    areas=np.array([abs(np.linalg.det(np.array([b-a,c-a])))/2 for a,b,c in triangles])
    if areas.sum()<=0:return center
    a,b,c=triangles[rng.choice(len(triangles),p=areas/areas.sum())]
    u,v=rng.random(2);u=np.sqrt(u);return (1-u)*a+u*(1-v)*b+u*v*c

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mask',type=int,default=2045);ap.add_argument('--batch',type=int,default=1);ap.add_argument('--count',type=int,default=5000);ap.add_argument('--weights',type=Path);ap.add_argument('--external',type=Path);a=ap.parse_args();assert 0<a.count<=5000
    start=time.time();d=json.loads((BASE/'screen.json').read_text());record=next(r for r in d['results'] if r['mask_index']==a.mask)
    z=np.load(a.weights or BASE/'solutions.npz');w=z['weights'] if a.weights else z['weights'][record['weight_solution_index']];gamma=z['gamma'] if a.weights else z['gamma'][record['weight_solution_index']];selected=z['selected_columns']
    c=json.loads(SOURCE.read_text());cover=json.loads(COVER.read_text());U=F(cover['side_upper']);L=F(c['L']);B=L/U;core=B-F(1,10**10)
    polys=[[np.array([.5+(float(U)-1)*float(F(x)) for x in p]) for p in cell['vertices']] for cell in cover['cells']]
    rng=np.random.default_rng(110000+a.mask*17+a.batch);mask=record['mask'];poses=[];cells=[];external_count=0
    if a.external:
        sites=np.array([[float(F(x)) for x in cell['center']] for cell in cover['cells']])
        for p in np.load(a.external)['poses']:
            u=(p[1:]/float(B)-.5)/(float(U)-1);cell=int(np.argmin(((sites-u)**2).sum(axis=1)))
            radius=float(B)*(abs(np.cos(p[0]))+abs(np.sin(p[0])))/2
            if cell in mask and np.all(p[1:]>=radius-1e-13) and np.all(p[1:]<=float(L)-radius+1e-13):
                poses.append(p.tolist());cells.append(cell);external_count+=1
            if len(poses)==a.count:break
    anchor=.7013071055461422
    for i in range(a.count-len(poses)):
        cell=mask[i%len(mask)]
        for retry in range(100):
            mode=(i//len(mask))%10
            theta=(0 if mode==0 else np.pi/2 if mode==1 else np.pi/4 if mode==2 else anchor+rng.normal()*1e-3 if mode==3 else np.pi/2-anchor+rng.normal()*1e-3 if mode==4 else rng.random()*np.pi/2)
            theta=float(np.clip(theta,0,np.pi/2));extent=(np.cos(theta)+np.sin(theta))/2;poly=polys[cell]
            for axis in (0,1):poly=clip(poly,axis,extent,-1);poly=clip(poly,axis,float(U)-extent,1)
            if len(poly)>=3:break
        else:raise RuntimeError(('No clipped polygon',cell))
        center=random_point(poly,rng,i);poses.append([theta,*(float(B)*center)]);cells.append(cell)
    P=np.array(poses);cells=np.array(cells,np.int64);model=TrueMajorityModel(SOURCE);restricted=Restricted(model,selected)
    rows=restricted.capture(float(core),P);values=rows@w;slack=values-gamma[cells];bad=np.flatnonzero(slack<-1e-8)
    out=BASE/f'mask{a.mask}-stress{a.batch}';np.savez_compressed(out.with_suffix('.npz'),poses=P,cells=cells,rows=rows,charges=values,slack=slack,weights=w,gamma=gamma,selected_columns=selected)
    result=dict(status='FRESH_FINITE_TYPED_STRESS_ONLY',mask_index=a.mask,mask=mask,batch=a.batch,pose_count=len(P),angle_domain='[0,pi/2]',center_domain='Each occupied closed Voronoi cell intersected with actual unit-parent wall containment in Uplus.',fixed_homothety_B=str(B),strict_core_side=str(core),strict_core_epsilon='1/10000000000',weights_source='solutions.npz',weight_solution_index=record['weight_solution_index'],original_finite_budget=record['budget'],deficient_count=len(bad),minimum_slack=float(slack.min()),minimum_charge=float(values.min()),per_cell=[dict(cell=k,count=int((cells==k).sum()),minimum_charge=float(values[cells==k].min()),threshold=float(gamma[k]),minimum_slack=float(slack[cells==k].min())) for k in mask],worst_indices=np.argsort(slack)[:30].tolist(),global_geometry_coverage=False,global_optimality=False,maximum_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,elapsed=time.time()-start,scope='Fresh numerical stress only. The original finite proposal is refuted if any legal sampled charge falls below its assigned cell threshold; passing is not continuum certification.')
    if a.weights:
        result['weights_source']=str(a.weights);result['weight_solution_index']=None
        result['original_finite_budget']=json.loads(a.weights.with_suffix('.json').read_text())['budget']
    result['external_pose_source']=str(a.external) if a.external else None
    result['external_pose_count']=external_count
    relaxation=(11-result['original_finite_budget'])/22
    result['half_aggregate_margin_per_cell_relaxation']=relaxation
    result['deficient_after_half_margin_relaxation']=int((slack+relaxation<-1e-8).sum())
    result['minimum_slack_after_half_margin_relaxation']=float(slack.min()+relaxation)
    sites=np.array([[float(F(x)) for x in cell['center']] for cell in cover['cells']]);image_bad=0;worst_image=0.;image_tests=0
    for swap in (0,1):
        for sx in (-1,1):
            for sy in (-1,1):
                centered=P[:,1:]-float(L)/2
                if swap:centered=centered[:,::-1]
                u=(centered*[sx,sy]/float(B))/(float(U)-1)+.5
                dd=((u[:,None,:]-sites[None,:,:])**2).sum(axis=2);included=dd<=dd.min(axis=1)[:,None]+2e-12
                for k in mask:
                    ii=np.flatnonzero(included[:,k]);ss=values[ii]-gamma[k]+relaxation
                    image_tests+=len(ii);image_bad+=int((ss<-1e-8).sum())
                    if len(ss):worst_image=min(worst_image,float(ss.min()))
    result['D4_image_tests_within_occupied_mask']=image_tests
    result['D4_deficient_after_half_margin_relaxation']=image_bad
    result['D4_minimum_relaxed_slack']=worst_image
    out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':
    with threadpool_limits(limits=1):main()
