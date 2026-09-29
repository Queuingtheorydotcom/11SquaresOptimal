"""Diagnostic exact coordinate-dual isolation test on a focused capture box.

This reports no capture theorem: ancestry, chart correspondence, and inactive
feature stability require independent replay even if every dual ratio passes.
"""
from pathlib import Path
from fractions import Fraction as F
from math import isqrt
import argparse,json,time
import anisotropic_local_radius as R

def sqrt_upper(x,D=10**15):
    n=(x.numerator*D*D+x.denominator-1)//x.denominator;k=isqrt(n)
    if k*k<n:k+=1
    return F(k,D)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();start=time.monotonic()
    d=json.loads(a.source.read_text());s=d['final_state'];B=F(s['B']);U=F(s['U']);old=json.loads((R.CLASSICAL/'trump-local-weighted-coordinate-radius.json').read_text())
    witness=R.ir.load_witness();base=json.loads((R.CLASSICAL/'trump-local-conservative-radius.json').read_text());lo,hi=map(F,base['root_interval'])
    gsrc=R.HERE.parent/'phase3/current/research/optimality/global_capture/local-capture-guards.json';gd=json.loads(gsrc.read_text());guard=next(g for g in gd['guards'] if g['mask']==s['mask'])
    # Independently obtain target intervals from the exact algebraic witness.
    cached={}
    def interval(v):
        key=tuple(v.coeffs)
        if key not in cached:cached[key]=R.enclose(key,lo,hi)
        return cached[key]
    target_t=list(map(F,gd['root_interval']));radii=[F(0)]*33;details=[]
    for role in guard['roles']:
        i=role['label'];owner=role['cell'];live=[r for r in s['cells'][str(owner)] if r['residual_polygons']]
        pts=[[F(v)/B-U/2 for v in p] for r in live for P in r['residual_polygons'] for p in P]
        target=[witness.centres[i][k]-witness.side/2 for k in (0,1)]
        if guard['symmetry']['swap']:target=target[::-1]
        if guard['symmetry']['reflect_x']:target[0]=-target[0]
        if guard['symmetry']['reflect_y']:target[1]=-target[1]
        cr=[]
        for axis in (0,1):
            tl,th=interval(target[axis]);pl=min(p[axis] for p in pts);ph=max(p[axis] for p in pts)
            cr.append(max(abs(pl-th),abs(ph-tl)))
        if guard['symmetry']['swap']:cr=cr[::-1]
        radii[3*i],radii[3*i+1]=cr
        axis_role=any(F(x)==0 for x,y in role['half_angle_intervals'])
        ar=F(0)
        for row in live:
            x,y=map(F,row['interval'])
            if axis_role:
                assert y<=F(1,2) or x>=F(1,2)
                ts=[x,y] if y<=F(1,2) else [(x-1)/(x+1),(y-1)/(y+1)]
                bound=2*max(map(abs,ts))
            else:
                assert y<F(2,3)
                m=min(x,target_t[0]);bound=2*max(abs(x-target_t[1]),abs(y-target_t[0]))/(1+m*m)
            ar=max(ar,bound)
        radii[3*i+2]=ar
        details.append(dict(label=i,cell=owner,center_radii=cr,angle_radius=ar))
    functions=R.ir.elementary_functions(witness,F(old['box_radius']));inv=F(old['inverse_sqrt2_upper']);root2=F(old['sqrt2_upper']);K_by_key={}
    for fn in functions:
        if not fn.value.is_zero():continue
        if fn.kind=='wall':K=inv*radii[3*fn.subject[0]+2]**2
        else:
            i,j,owner=fn.subject[:3];other=j if owner==i else i
            dx=radii[3*i]+radii[3*j];dy=radii[3*i+1]+radii[3*j+1]
            wo=radii[3*owner+2];wp=radii[3*other+2];reach=fn.curvature-6*root2
            K=reach*wo*wo+2*sqrt_upper(dx*dx+dy*dy)*wo+inv*(wo+wp)**2
        key=R.ir.gradient_key(fn.gradient);K_by_key[key]=max(K_by_key.get(key,F(0)),K)
    assert max(radii)<F(old['box_radius'])
    worst=(F(0),None);ratios=[];dual_records=[]
    for branch in old['branches']:
        rows=witness.branches[branch['branch']]['rows'];K=[K_by_key[R.tc.row_key(row)] for row in rows]
        for cert in branch['certificates']:
            j=cert['coordinate'];M=sum(F(v,old['coefficient_denominator'])*k for v,k in zip(cert['coefficients'],K))
            margin=radii[j]-F(cert['residual_upper'])*max(radii);ratio=M/(2*margin) if margin>0 else F(10**50)
            if ratio>worst[0]:worst=(ratio,dict(branch=branch['branch'],coordinate=j,sign=cert['sign']))
            ratios.append(ratio)
            dual_records.append(dict(branch=branch['branch'],coordinate=j,sign=cert['sign'],curvature_mass=M,linear_margin=margin,ratio=ratio))
    by_subject={fn.subject:fn for fn in functions};gap_records=[]
    contact_pairs={c.pair for c in witness.contacts};groups={}
    for fn in functions:
        if fn.kind=='pair' and fn.subject[:2] in contact_pairs:groups.setdefault(fn.subject[:5],[]).append(fn)
    excluded_features={key for key,group in groups.items() if any(interval(fn.value)[1]<0 for fn in group)}
    assert excluded_features=={tuple(g['feature']) for g in old['unavailable_feature_proofs']} and len(excluded_features)==88
    for g in old['unavailable_feature_proofs']:
        subject=tuple(g['feature'])+(g['negative_corner'],);fn=by_subject[subject]
        value_upper=interval(fn.value)[1];assert value_upper<0
        i,j,owner=fn.subject[:3];other=j if owner==i else i
        dx=radii[3*i]+radii[3*j];dy=radii[3*i+1]+radii[3*j+1]
        wo=radii[3*owner+2];wp=radii[3*other+2];reach=fn.curvature-6*root2
        K=reach*wo*wo+2*sqrt_upper(dx*dx+dy*dy)*wo+inv*(wo+wp)**2
        G=sum(max(map(abs,interval(v)))*r for v,r in zip(fn.gradient,radii))
        upper=value_upper+G+K/2
        gap_records.append(dict(subject=subject,value_upper=value_upper,weighted_gradient_upper=G,directional_curvature_upper=K,whole_box_upper=upper))
    stable=all(g['whole_box_upper']<0 for g in gap_records)
    files=[Path(__file__),Path(R.__file__),R.CLASSICAL/'trump-local-weighted-coordinate-radius.json',R.CLASSICAL/'trump-local-conservative-radius.json',gsrc,
           R.HERE.parent/'local-radius/fresh-local-algebra.json',R.HERE.parent/'local-radius/fresh-baseline-radius.json',R.HERE.parent/'local-radius/fresh-weighted-coordinate-radius.json']
    out=dict(status='PASS_PRODUCER_FOCUSED_LOCAL_ISOLATION_BOX' if stable and max(ratios)<1 else 'FOCUSED_LOCAL_BOX_NOT_CERTIFIED',
             source_sha256=R.sha(a.source),source=str(a.source.resolve()),radius_by_coordinate=radii,details=details,worst_dual_ratio=worst[0],worst_coordinate=worst[1],
             coordinate_dual_tests=dual_records,unavailable_feature_checks=gap_records,
             all_coordinate_dual_tests_pass=max(ratios)<1,unavailable_feature_stability_checked=stable,
             dependencies={str(p.resolve()):R.sha(p) for p in files},
             local_capture_proved=False,independent_replay_complete=False,global_optimality_proved=False,
             scope='Conditional focused-box isolation at exact candidate side; full pose induction and chart bridge require independent replay.',seconds=time.monotonic()-start)
    a.output.write_text(json.dumps(out,default=str,indent=2)+'\n');print(json.dumps(dict(worst_ratio=float(worst[0]),worst_coordinate=worst[1],all_pass=out['all_coordinate_dual_tests_pass'],seconds=out['seconds'])),flush=True)

if __name__=='__main__':main()
