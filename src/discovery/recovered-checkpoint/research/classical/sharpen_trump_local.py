#!/usr/bin/env python3
"""Sharpen the local cone bound by shifting rational inverse rows by stress.

Reads the banked rational J matrices; performs no numerical inversion or LP.
Every one of the66 signed coordinate functionals receives a nonnegative
row-combination certificate with an exact residual bound.
"""
if not __debug__:
    raise SystemExit('Assertions must remain enabled; remove -O/-OO.')

from fractions import Fraction as F
from pathlib import Path
from hashlib import sha256
import json
import time
import numpy as np

from replay_trump_local import SOURCE,need,enclose
from cases.trump11 import isolation_radius as ir


def encode(value):
    if isinstance(value,F):return str(value)
    raise TypeError(type(value).__name__)


def main():
    started=time.monotonic();here=Path(__file__).parent
    input_path=here/'trump-local-conservative-radius.json';old=json.loads(input_path.read_text())
    need(old['status']=='PASS_EXACT_CONSERVATIVE_LOCAL_RADIUS','Unverified input status')
    for path,fingerprint in old['source_hashes'].items():
        need(sha256((SOURCE/path).read_bytes()).hexdigest()==fingerprint,'Changed source '+path)
    witness=ir.load_witness();record=ir.load_record();lo,hi=map(F,old['root_interval'])
    need(sha256(ir.RECORD.read_bytes()).hexdigest()==old['tangent_record_sha256'],'Changed tangent packet')
    branches=[];global_kappa=None;cached={}
    def bounds(value):
        key=tuple(value.coeffs)
        if key not in cached:cached[key]=enclose(key,lo,hi)
        return cached[key]
    for branch,previous in zip(witness.branches,old['branches'],strict=True):
        index=branch['branch'];need(index==previous['branch'],'Branch order drift')
        rows=branch['rows'];cert=record['branches']['records'][index]['certificate'];pivots=cert['pivot_rows']
        Jnum=np.array(previous['rounded_inverse'],dtype=object);DJ=previous['inverse_denominator']
        DB=previous['matrix_approximation_denominator'];Bnum=[]
        need(Jnum.shape==(33,33) and DJ>0 and DB>0,'Malformed rational inverse')
        for i in pivots:
            approx=[]
            for coefficient in rows[i].coefficients:
                a,b=bounds(coefficient);q=round((a+b)*DB/2)
                need(F(q-1,DB)<=a<=b<=F(q+1,DB),'Entry enclosure failed')
                approx.append(q)
            Bnum.append(approx)
        residual=DJ*DB*np.eye(33,dtype=object)-Jnum@np.array(Bnum,dtype=object)
        errors=[F(int(sum(abs(x) for x in r)),DJ*DB)+
                F(int(sum(abs(x) for x in j)),DJ)*F(33,DB)
                for r,j in zip(residual,Jnum)]
        need(max(errors)<1,'Inverse row residual is too large')
        stress=ir.reconstruct_stress(rows,cert,witness.field)
        intervals=[bounds(y) for y in stress];need(min(a for a,b in intervals)>0,'Nonpositive stress')
        total=sum(b for a,b in intervals);coordinates=[];kappa=None
        for j in range(33):
            for sign in (-1,1):
                initial=[F(sign*int(x),DJ) for x in Jnum[j]]
                shift=max([F(0)]+[-q/intervals[p][0] for p,q in zip(pivots,initial) if q<0])
                # These interval bounds prove every actual coefficient nonnegative.
                need(all(q+shift*intervals[p][0]>=0 for p,q in zip(pivots,initial)),
                     'Stress-shift combination has a negative coefficient')
                mass=sum(initial)+shift*total
                need(mass>0,'Nonpositive combination mass upper bound')
                lower=(1-errors[j])/mass
                kappa=lower if kappa is None else min(kappa,lower)
                coordinates.append(dict(coordinate=j,sign=sign,shift=shift,
                                        coefficient_mass_upper=mass,residual_upper=errors[j],
                                        modulus_lower=lower))
        global_kappa=kappa if global_kappa is None else min(global_kappa,kappa)
        branches.append(dict(branch=index,cone_modulus_lower=kappa,coordinates=coordinates))
        if index%32==31:print(f'Exact stress-shift combinations: {index+1}/128 branches',flush=True)
    radius=min(F(old['box_radius']),F(old['branch_stability_radius_lower']),
               2*global_kappa/F(old['curvature_upper']))
    den=10**15;short=F(radius.numerator*den//radius.denominator,den)
    need(short>0,'Positive rounded radius required')
    result=dict(status='PASS_EXACT_STRESS_SHIFT_LOCAL_RADIUS',radius_open=short,
                radius_decimal=float(short),cone_modulus_lower=global_kappa,
                branches=branches,signed_coordinate_certificates=128*66,
                curvature_upper=old['curvature_upper'],lipschitz_upper=old['lipschitz_upper'],
                branch_stability_radius_lower=old['branch_stability_radius_lower'],
                inherited_input_sha256=sha256(input_path.read_bytes()).hexdigest(),
                inherited_input=str(input_path),checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='Sharper explicit local radius using banked exact gap/curvature premises and all128 retained tangent branches. No global claim or retained .004-radius claim.',
                seconds=time.monotonic()-started)
    (here/'trump-local-stress-shift-radius.json').write_text(json.dumps(result,default=encode,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='branches'},default=encode,indent=2))


if __name__=='__main__':main()
