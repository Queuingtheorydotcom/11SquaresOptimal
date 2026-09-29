"""Optimize and exactly accept coordinate duals for one rectangular shape."""
from pathlib import Path
from fractions import Fraction as F
import json,time,math
import numpy as np
from scipy.optimize import linprog
import anisotropic_local_radius as R

def main():
    start=time.monotonic();a=F(1,4);D=10**12
    old=json.loads((R.CLASSICAL/'trump-local-weighted-coordinate-radius.json').read_text())
    root=json.loads((R.CLASSICAL/'trump-local-conservative-radius.json').read_text());lo,hi=map(F,root['root_interval'])
    witness=R.ir.load_witness();functions=R.ir.elementary_functions(witness,F(old['box_radius']));kind={}
    for fn in functions:
        if fn.value.is_zero():kind[R.ir.gradient_key(fn.gradient)]=fn.kind
    root2=F(old['sqrt2_upper']);inv=F(old['inverse_sqrt2_upper']);cached={}
    def entry(v):
        key=tuple(v.coeffs)
        if key not in cached:
            low,high=R.enclose(key,lo,hi);q=round((low+high)*D/2)
            assert F(q-1,D)<=low<=high<=F(q+1,D)
            cached[key]=q
        return cached[key]
    result=[];caps=[]
    for original in old['branches']:
        bi=original['branch'];rows=witness.branches[bi]['rows']
        K=[]
        for row,k in zip(rows,original['row_curvature_upper']):
            if kind[R.tc.row_key(row)]=='wall':K.append(inv*a*a)
            else:K.append((F(k)-6*root2)*a*a+4*root2*a+4*inv*a*a)
        matrix=np.array([[entry(v) for v in row.coefficients] for row in rows],dtype=object)
        numeric=np.array(matrix,dtype=float)/D;certs=[]
        for j in range(33):
            for sign in (-1,1):
                target=np.zeros(33);target[j]=sign
                trial=linprog(np.array(list(map(float,K))),A_eq=numeric.T,b_eq=target,bounds=(0,None),method='highs-ds')
                assert trial.success
                coefficients=np.array([math.ceil(max(0,float(v))*D) for v in trial.x],dtype=object)
                residual=coefficients@matrix;residual[j]-=sign*D*D
                mass=F(int(sum(coefficients)),D)
                error=F(int(sum(abs(v) for v in residual)),D*D)+mass*F(33,D)
                shape=a if j%3==2 else F(1)
                weighted=sum(F(int(v),D)*k for v,k in zip(coefficients,K))
                cap=2*(shape-error)/weighted;assert cap>0
                caps.append(cap);certs.append(dict(coordinate=j,sign=sign,coefficients=coefficients.tolist(),mass=mass,residual_upper=error,curvature_mass=weighted,radius_cap=cap))
        result.append(dict(branch=bi,matrix_integer_approximations=matrix.tolist(),directional_curvature=K,certificates=certs))
        if bi%16==15:print(json.dumps(dict(branches=bi+1,radius_cap=float(min(caps)),seconds=time.monotonic()-start)),flush=True)
    prior=json.loads((R.HERE/'anisotropic-local-radii.json').read_text())
    gaps=next(x['unavailable_feature_checks'] for x in prior['results'] if F(x['angle_to_center_radius_ratio'])==a)
    radius=min(F(old['box_radius']),*caps);grid=10**9;radius=F(math.floor(radius*grid),grid)
    def stable(r):return all(F(g['weighted_gradient_upper'])*r+F(g['directional_curvature_upper'])*r*r/2<F(g['negative_gap_lower']) for g in gaps)
    while not stable(radius):radius=F(math.floor(radius*F(999,1000)*grid),grid)
    while not all(radius<x for x in caps):radius-=F(1,grid)
    assert radius>0 and stable(radius)
    out=dict(status='PASS_EXACT_OPTIMIZED_RECTANGULAR_LOCAL_COORDINATE_DUALS',angle_to_center_radius_ratio=a,center_radius=radius,angle_radius=a*radius,
             coordinate_dual_radius_cap=min(caps),branches=result,coefficient_denominator=D,matrix_approximation_denominator=D,
             feature_stability_source_sha256=R.sha(R.HERE/'anisotropic-local-radii.json'),unavailable_feature_checks=gaps,
             old_weighted_radius_sha256=R.sha(R.CLASSICAL/'trump-local-weighted-coordinate-radius.json'),checker_sha256=R.sha(__file__),
             scope='Local labelled fixed-side rectangular isolation only.',independent_replay_complete=False,global_optimality_proved=False,seconds=time.monotonic()-start)
    (R.HERE/'optimized-anisotropic-local-radius.json').write_text(json.dumps(out,default=str,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('branches','unavailable_feature_checks')},default=str),flush=True)

if __name__=='__main__':main()
