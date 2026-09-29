"""Bounded numerical endpoint-deficit discovery; never a coverage proof."""
from pathlib import Path
from fractions import Fraction as F
import sys, json, math, hashlib, time, resource
import numpy as np
from scipy.stats import qmc
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/stromquist'))
sys.path.insert(0,str(ROOT/'research/reweight'))
from true_majority_model import TrueMajorityModel
from trump_anchor_screen import Restricted
OUT=Path(__file__).parent
SOURCE=ROOT/'research/true_catalogue/round6-cutround12-surplus-3.8754-full/proposal.json'
TARGET=F('3.877084')

def pose_orbits(target,L):
    data=json.loads((ROOT/'work/construction/trump-pose-intervals.json').read_text())
    A=L/target; result=[]; seen=set()
    for p in data['poses']:
        xy=np.array([float(sum(map(F,z))/2) for z in p['centered_center']])
        theta=float(sum(map(F,p['angle_radians']))/2)
        for swap in (0,1):
            for sx in (-1,1):
                for sy in (-1,1):
                    v=(xy[::-1] if swap else xy)*[sx,sy]
                    th=(theta*sx*sy*(-1 if swap else 1))%(math.pi/2)
                    key=tuple(np.round([th,*v],12))
                    if key in seen: continue
                    seen.add(key); result.append(dict(template=p['index'],pose=[th,*(L/2+A*v)],unit_pose=[th,*(target/2+v)]))
    return result

def distances(poses,A,L,orbits):
    unit=(poses[:,1:]-L/2)/A+float(TARGET)/2
    best=np.full(len(poses),np.inf); nearest=np.zeros(len(poses),int)
    for j,r in enumerate(orbits):
        th,x,y=r['unit_pose']; da=np.abs(poses[:,0]-th); da=np.minimum(da,np.pi/2-da)
        d=np.maximum(np.max(np.abs(unit-[x,y]),axis=1),da)
        hit=d<best; best[hit]=d[hit]; nearest[hit]=j
    return best,nearest

def main():
    start=time.time(); rng=np.random.default_rng(1103877)
    model=TrueMajorityModel(SOURCE); L=model.L; A=float(F(model.c['L'])/TARGET)
    w=np.array([p[2] for p in model.c['point_orbits']]+[g['weight'] for g in model.c['charge_orbits']],np.int64)
    selected=np.flatnonzero(w); restricted=Restricted(model,selected); gamma=model.c['minimum_units']
    z=np.load(ROOT/'research/checkpoints/true-round6-cutround12-surplus-pool-resume.npz')
    pool=z['placements']; oldA=float(z['A']); override=np.load(ROOT/'research/checkpoints/true-round6-cutround12-surplus-pool-row-overrides.npz')['indices']
    indices=np.unique(np.r_[override,rng.choice(len(pool),1600,replace=False)])
    P=pool[indices].copy(); cs=np.cos(P[:,0])+np.sin(P[:,0])
    P[:,1:]=L/2+(P[:,1:]-L/2)*((L-A*cs)/(L-oldA*cs))[:,None]
    labels=['transported_pool']*len(P)
    u=qmc.Sobol(3,scramble=True,seed=1103877).random_base2(9)
    theta=u[:,0]*np.pi/4; rad=A*(np.cos(theta)+np.sin(theta))/2
    random=np.c_[theta,rad[:,None]+u[:,1:]*(L-2*rad)[:,None]]
    P=np.vstack([P,random]); labels+=['sobol']*len(random)
    orbits=pose_orbits(float(TARGET),L)
    anchors=np.array([r['pose'] for r in orbits if r['pose'][0]<=np.pi/4+1e-14])
    P=np.vstack([P,anchors]); labels+=['trump_orbit']*len(anchors)
    # Boundary-biased orientation grid, with a full legal center square.
    extras=[]
    for th in np.linspace(0,np.pi/4,41):
        r=A*(np.cos(th)+np.sin(th))/2
        for x,y in [(0,0),(0,.5),(0,1),(.5,0),(.5,1),(1,0),(1,.5),(1,1)]:
            extras.append([th,r+x*(L-2*r),r+y*(L-2*r)])
    P=np.vstack([P,extras]); labels+=['boundary_grid']*len(extras)
    assert len(P)<4000
    rows=restricted.capture(A,P); charges=rows.astype(np.int64)@w[selected]
    stage1=len(P); print('stage1',stage1,'deficient',int((charges<gamma).sum()),'min',int(charges.min()),flush=True)
    # At most 5000 total poses, concentrate the remainder near sampled minima.
    seeds=np.argsort(charges)[:min(40,len(P))]; count=5000-len(P)
    extra=P[rng.choice(seeds,count)].copy()
    scales=rng.choice(np.array([1e-5,5e-5,2e-4,1e-3,5e-3]),count)
    extra+=rng.normal(size=(count,3))*scales[:,None]
    extra[:,0]=np.clip(extra[:,0],0,np.pi/4)
    rad=A*(np.cos(extra[:,0])+np.sin(extra[:,0]))/2
    extra[:,1:]=np.maximum(rad[:,None],np.minimum(L-rad[:,None],extra[:,1:]))
    rows2=restricted.capture(A,extra); charges2=rows2.astype(np.int64)@w[selected]
    P=np.vstack([P,extra]); rows=np.vstack([rows,rows2]); charges=np.r_[charges,charges2]; labels+=['local_refinement']*count
    d,nearest=distances(P,A,L,orbits); bad=np.flatnonzero(charges<gamma)
    np.savez_compressed(OUT/'endpoint-sample.npz',poses=P,charges=charges,rows=rows,selected=selected,distances=d,nearest=nearest,labels=np.array(labels),A=A,target=float(TARGET))
    controls=np.unique(np.r_[np.argsort(charges)[:4],rng.choice(len(P),4,replace=False)])
    assert np.array_equal(model.capture(A,P[controls])[:,selected],rows[controls])
    records=[dict(index=int(i),source=labels[i],charge_units=int(charges[i]),deficit_units=gamma-int(charges[i]),pose=P[i].tolist(),distance_to_trump_orbits=float(d[i]),nearest_template=int(orbits[nearest[i]]['template'])) for i in bad]
    report=dict(status='BOUNDED_NUMERICAL_DISCOVERY_ONLY',source=str(SOURCE.relative_to(ROOT)),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),target=str(TARGET),A=str(F(model.c['L'])/TARGET),budget_units=model.c['budget_units'],threshold_units=gamma,stage1_count=stage1,pose_count=len(P),positive_columns=len(selected),deficient_count=len(bad),minimum_charge_units=int(charges.min()),minimum_deficient_distance_to_trump_orbits=float(d[bad].min()) if len(bad) else None,maximum_deficient_distance_to_trump_orbits=float(d[bad].max()) if len(bad) else None,deficient_within_radius_1_over_248=int((d[bad]<=1/248).sum()),full_model_controls=controls.tolist(),deficient_records=records,trump_orbits=orbits,global_coverage=False,global_optimality=False,maximum_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,elapsed=time.time()-start,scope='Numerical charges of fixed B=L/3.877084 cores. Since3.877084>alpha, these cores strictly fit every parent in a hypothetical packing of sideS<=alpha, after normalization to L. The sampled legal-core center domain is a conservative superset of parent centers. No exhaustive deficit-domain or pairwise compatibility coverage is asserted.')
    (OUT/'endpoint-sample.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('deficient_records','trump_orbits')}),flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=1): main()
