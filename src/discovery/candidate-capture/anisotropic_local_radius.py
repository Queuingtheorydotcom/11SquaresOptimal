"""Rigorous rectangular local-isolation radii from audited coordinate duals.

For centers bounded by r and angular perturbations by a*r, a pair elementary
gap has directional second derivative bounded by
 (D*a*a + 4*sqrt(2)*a + 4/sqrt(2)*a*a)*r*r,
where D bounds the distance between the two centers on the declared box.
This follows directly from g'' = -axis.d*wo^2 + 2*Jaxis.v*wo
                              -axis.corner*(wo-wp)^2.
The coordinate-dual and unavailable-feature checks use exact rationals only.
"""
from pathlib import Path
import sys,json,hashlib,time
from fractions import Fraction as F

HERE=Path(__file__).resolve().parent
CLASSICAL=HERE.parent/'recovered-checkpoint/research/classical'
sys.path.insert(0,str(CLASSICAL))
from replay_trump_local import enclose
from cases.trump11 import isolation_radius as ir
from cases.trump11 import tangent_cones as tc

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    start=time.monotonic();p=CLASSICAL/'trump-local-weighted-coordinate-radius.json';old=json.loads(p.read_text())
    assert old['status']=='PASS_FULL_EXACT_WEIGHTED_COORDINATE_RADIUS'
    baseline=json.loads((CLASSICAL/'trump-local-conservative-radius.json').read_text());lo,hi=map(F,baseline['root_interval'])
    witness=ir.load_witness();functions=ir.elementary_functions(witness,F(old['box_radius']))
    kind={};functions_by_subject={}
    for fn in functions:
        functions_by_subject[fn.subject]=fn
        if fn.value.is_zero():kind[ir.gradient_key(fn.gradient)]=fn.kind
    root2=F(old['sqrt2_upper']);invroot2=F(old['inverse_sqrt2_upper']);oldbox=F(old['box_radius'])
    cached={}
    def magnitude(x):
        key=tuple(x.coeffs)
        if key not in cached:
            a,b=enclose(key,lo,hi);cached[key]=max(abs(a),abs(b))
        return cached[key]
    results=[]
    for angle_ratio in [F(1),F(1,2),F(1,4),F(1,8),F(1,16),F(1,32)]:
        def curvature(K,iswall):
            if iswall:return invroot2*angle_ratio**2
            D=K-6*root2
            assert D>0
            return D*angle_ratio**2+4*root2*angle_ratio+4*invroot2*angle_ratio**2
        caps=[];branch_records=[]
        for branch in old['branches']:
            rows=witness.branches[branch['branch']]['rows'];krows=[curvature(F(K),kind[tc.row_key(row)]=='wall') for K,row in zip(branch['row_curvature_upper'],rows)]
            records=[]
            for certificate in branch['certificates']:
                j=certificate['coordinate'];shape=angle_ratio if j%3==2 else F(1)
                error=F(certificate['residual_upper'])
                mass=sum(F(v,old['coefficient_denominator'])*K for v,K in zip(certificate['coefficients'],krows))
                cap=2*(shape-error)/mass
                assert cap>0
                caps.append(cap);records.append(dict(coordinate=j,sign=certificate['sign'],curvature_mass=mass,radius_cap=cap))
            branch_records.append(dict(branch=branch['branch'],certificates=records))
        gaps=[]
        for record in old['unavailable_feature_proofs']:
            subject=tuple(record['feature'])+(record['negative_corner'],);fn=functions_by_subject[subject]
            assert fn.kind=='pair'
            # Derive a reach bound for this elementary function's pair from
            # its original uniform-curvature bound on the same declared box.
            K=curvature(fn.curvature,False)
            G=sum(magnitude(v)*(angle_ratio if j%3==2 else 1) for j,v in enumerate(fn.gradient))
            gap=F(record['negative_gap_lower']);assert gap>0
            gaps.append(dict(subject=subject,negative_gap_lower=gap,weighted_gradient_upper=G,directional_curvature_upper=K))
        # Search a rational grid downward; no floating root is accepted.
        radius=min(oldbox,*caps)
        D=10**9;radius=F((radius*D).numerator//(radius*D).denominator,D)
        while not all(g['weighted_gradient_upper']*radius+g['directional_curvature_upper']*radius*radius/2<g['negative_gap_lower'] for g in gaps):
            radius*=F(999,1000)
            radius=F((radius*D).numerator//(radius*D).denominator,D)
        # Strict inequality is required for each signed-coordinate maximum.
        while not all(radius<cap for cap in caps):radius-=F(1,D)
        assert radius>0
        result=dict(angle_to_center_radius_ratio=angle_ratio,center_radius=radius,angle_radius=angle_ratio*radius,
                    coordinate_dual_radius_cap=min(caps),branch_certificates=branch_records,unavailable_feature_checks=gaps)
        results.append(result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('branch_certificates','unavailable_feature_checks')},default=str),flush=True)
    out=dict(status='PASS_EXACT_RECTANGULAR_LOCAL_RADIUS_FROM_AUDITED_DUALS',scope='Local labelled fixed-side isolation only; no global capture or optimality.',
             input_sha256=sha(p),baseline_sha256=sha(CLASSICAL/'trump-local-conservative-radius.json'),checker_sha256=sha(__file__),
             declared_center_box=oldbox,root_interval=[lo,hi],results=results,independent_replay_complete=False,global_optimality_proved=False,seconds=time.monotonic()-start)
    (HERE/'anisotropic-local-radii.json').write_text(json.dumps(out,default=str,separators=(',',':'))+'\n')

if __name__=='__main__':main()
