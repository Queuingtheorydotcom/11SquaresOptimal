#!/usr/bin/env python3
"""A conservative exact local radius from rational inverse residuals and stresses.

Uses the already replayed jlevy tangent matrices. Floating inverse matrices
only propose rational witnesses; every acceptance inequality is rational.
No face LP or retained quantitative modulus is trusted.
"""
if not __debug__:
    raise SystemExit('Assertions must remain enabled; remove -O/-OO.')

from fractions import Fraction as F
from pathlib import Path
from hashlib import sha256
import json
import sys
import time
import numpy as np

from replay_trump_local import ROOT,SOURCE,need,enclose,evaluate
from cases.trump11 import isolation_radius as ir
from cases.trump11 import tangent_cones as tc
from cases.trump11 import packing


def encode(value):
    if isinstance(value,F):return str(value)
    raise TypeError(type(value).__name__)


def main():
    started=time.monotonic();witness=ir.load_witness();field=witness.field
    record=ir.load_record();modulus=list(map(F,reversed(packing.U_MIN_POLY)))
    lo,hi=map(F,packing.U_INTERVAL)
    while hi-lo>F(1,10**45):
        mid=(lo+hi)/2
        if evaluate(modulus,lo)*evaluate(modulus,mid)<0:hi=mid
        else:lo=mid
    # All nonlinear estimates below use only U<4 and the exact declared box.
    need(enclose(witness.side.coeffs,lo,hi)[1]<4,'Side bound U<4 failed')
    box=F(1,64);K=F(16);Lipschitz=F(12)
    reach=F(3,2)*(4+2*box)
    need(reach+6*F(3,2)<K and reach+3*F(3,2)<Lipschitz,'Universal derivative bounds fail')
    functions=ir.elementary_functions(witness,box)
    identified=ir.identify_rows(witness,functions)
    gap=None
    for function in functions:
        if function.value.is_zero():continue
        a,b=enclose(function.value.coeffs,lo,hi)
        need(a>0 or b<0,'Nonzero elementary gap is not sign-separated')
        lower=min(abs(a),abs(b));gap=lower if gap is None else min(gap,lower)
    need(gap is not None and gap>0,'No strict gap lower bound')
    gap_radius=gap/Lipschitz
    DB=10**12;DJ=10**9;receipts=[];modulus_min=None
    cached={}
    def bounds(value):
        key=tuple(value.coeffs)
        if key not in cached:cached[key]=enclose(key,lo,hi)
        return cached[key]
    for branch in witness.branches:
        index=branch['branch'];rows=branch['rows'];cert=record['branches']['records'][index]['certificate']
        pivots=cert['pivot_rows'];B=[list(rows[i].coefficients) for i in pivots]
        BN=[]
        for row in B:
            values=[]
            for value in row:
                a,b=bounds(value);q=round((a+b)*DB/2)
                need(F(q-1,DB)<=a<=b<=F(q+1,DB),'Rounded matrix entry not enclosed')
                values.append(q)
            BN.append(values)
        Bnum=np.array(BN,dtype=object)
        proposal=np.linalg.inv(np.array(BN,dtype=float)/DB)
        need(np.isfinite(proposal).all(),'Nonfinite inverse proposal')
        Jnum=np.array([[int(round(x*DJ)) for x in row] for row in proposal],dtype=object)
        residual=DJ*DB*np.eye(33,dtype=object)-Jnum@Bnum
        residual_integer=max(sum(abs(x) for x in row) for row in residual)
        Jnorm=F(int(max(sum(abs(x) for x in row) for row in Jnum)),DJ)
        error=F(int(residual_integer),DJ*DB)+Jnorm*F(33,DB)
        need(error<1,'Rational inverse residual did not prove invertibility')
        inverse_norm=Jnorm/(1-error)
        stress=ir.reconstruct_stress(rows,cert,field)
        stress_bounds=[bounds(value) for value in stress]
        minimum=min(a for a,b in stress_bounds);total=sum(b for a,b in stress_bounds)
        need(minimum>0,'Stress positivity failed independent interval check')
        ratio=total/minimum
        kappa=1/(inverse_norm*ratio)
        modulus_min=kappa if modulus_min is None else min(modulus_min,kappa)
        receipts.append(dict(branch=index,rounded_inverse=Jnum.tolist(),inverse_denominator=DJ,
                             matrix_approximation_denominator=DB,residual_upper=error,
                             inverse_norm_upper=inverse_norm,stress_min_lower=minimum,
                             stress_total_upper=total,cone_modulus_lower=kappa))
        if index%32==31:print(f'Certified inverse/stress bounds: {index+1}/128',flush=True)
    radius=min(box,gap_radius,2*modulus_min/K)
    simple_radius=F(1,120000)
    need(all(F(b['inverse_norm_upper'])<89 for b in receipts),'Uniform inverse bound89 failed')
    need(all(F(b['stress_total_upper'])/F(b['stress_min_lower'])<158 for b in receipts),
         'Uniform stress-ratio bound158 failed')
    need(gap>F(1,250),'Uniform gap bound1/250 failed')
    need(simple_radius<min(box,F(1,3000),F(1,8*89*158)),'Simple radius check failed')
    decimal=10**15;short=F(radius.numerator*decimal//radius.denominator,decimal)
    if short<=0:
        decimal=10**30;short=F(radius.numerator*decimal//radius.denominator,decimal)
    need(0<short<=radius,'Short rational radius is invalid')
    result=dict(status='PASS_EXACT_CONSERVATIVE_LOCAL_RADIUS',radius_lower=short,
                radius_decimal=float(short),unrounded_radius_lower=radius,
                simple_closed_radius=simple_radius,uniform_inverse_norm_upper=89,
                uniform_stress_ratio_upper=158,uniform_nonzero_gap_lower=F(1,250),
                box_radius=box,curvature_upper=K,lipschitz_upper=Lipschitz,
                all_nonzero_gap_lower=gap,branch_stability_radius_lower=gap_radius,
                cone_modulus_lower=modulus_min,root_interval=[lo,hi],branches=receipts,
                identified_distinct_rows=identified['distinct_branch_rows'],
                source_hashes={p:sha256((SOURCE/p).read_bytes()).hexdigest() for p in
                               ('cases/trump11/packing.py','cases/trump11/tangent_cones.py',
                                'cases/trump11/isolation_radius.py','src/sqpack/field.py')},
                tangent_record_sha256=sha256(ir.RECORD.read_bytes()).hexdigest(),
                checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                rational_helper_sha256=sha256(Path(__file__).with_name('replay_trump_local.py').read_bytes()).hexdigest(),
                scope='Full33-variable labelled anchored local fixed-side isolation; no global optimality, no claimed retained .004 radius, no relabelling quotient.',
                seconds=time.monotonic()-started)
    path=Path(__file__).with_name('trump-local-conservative-radius.json')
    path.write_text(json.dumps(result,default=encode,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='branches'},default=encode,indent=2))


if __name__=='__main__':main()
