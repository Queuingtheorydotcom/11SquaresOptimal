#!/usr/bin/env python3
"""Independently recheck a small-integer reconstruction on finite capture rows.

The output is evidence for a new finite proposal, never continuum coverage.
The existing denominator-1e9 pair remains unchanged.
"""
from pathlib import Path
from fractions import Fraction as F
import json, math
import numpy as np
from exception_charge_lp import budgets,filehash,need,dump
ROOT=Path('research/classical')
pair_path=ROOT/'cutround8-four-exception-pair-D1e9.json'
pair=json.loads(pair_path.read_bytes())
output=ROOT/'cutround8-four-exception-small-integer.json'
need(not output.exists(),'Use a fresh immutable output')
a_path=Path(pair['fixed_A']['certificate']);a=json.loads(a_path.read_bytes())
need(filehash(a_path)==pair['fixed_A']['certificate_sha256'],'A vector changed')
vector_path=Path(pair['B']['floating_vector']);need(filehash(vector_path)==pair['B']['floating_vector_sha256'],'Float vector changed')
with np.load(vector_path) as f:w=f['weights'].copy()
# Reconstruction is only a suggestion until the exact rows below pass.
scale=F(11,1944)
integer=[round(float(x)/float(scale)) for x in w]
need(min(integer)>=0 and max(integer)<=36,'Unexpected integer reconstruction')
max_error=max(abs(float(F(n)*scale)-float(x)) for n,x in zip(integer,w))
need(max_error<1e-12,'Small-denominator reconstruction is not close')
wa=np.array([p[2] for p in a['point_orbits']]+[p['weight'] for p in a['charge_orbits']],np.int64)
wb=np.array(integer,np.int64);cap=budgets(a);mb=int(cap@wb)
path=Path(pair['finite_check']['rows']);need(filehash(path)==pair['finite_check']['rows_sha256'],'Rows changed')
rows=np.load(path,mmap_mode='r');active=np.flatnonzero((wa>0)|(wb>0));qa=np.empty(len(rows),np.int64);qb=qa.copy()
for start in range(0,len(rows),8192):
    block=np.asarray(rows[start:start+8192][:,active],np.int64)
    need(np.all(block<=cap[active]),'Coefficient exceeds budget')
    qa[start:start+len(block)]=block@wa[active];qb[start:start+len(block)]=block@wb[active]
mask=qa<pair['fixed_A']['strong_cutoff_units']
need(np.flatnonzero(mask).tolist()==pair['finite_check']['exception_indices'],'Exception mask changed')
minimum=int(qb.min());emin=int(qb[mask].min())
need(mb==1672 and minimum==136 and emin==248,'Unexpected reconstructed exact extrema')
variants=[]
for label,beta,delta in [('integer_equal_margin',112,224),('integer_global_margin_one',135,182)]:
    gap=7*beta+4*delta-mb
    need(0<=beta<=delta and gap>0 and np.all(qb>=beta) and np.all(qb[mask]>=delta),'Reconstructed proposal fails')
    variants.append(dict(label=label,global_units=beta,exception_units=delta,counting_surplus_units=gap,
                         finite_global_margin_units=minimum-beta,finite_exception_margin_units=emin-delta))
need(filehash(path)==pair['finite_check']['rows_sha256'],'Rows changed during replay')
result=dict(status='PASS_EXACT_FINITE_SMALL_INTEGER_RECONSTRUCTION',global_bound_proved=False,
    original_immutable_pair=str(pair_path),original_pair_sha256=filehash(pair_path),
    source_certificate=pair['source_certificate'],source_sha256=pair['source_sha256'],
    fixed_A=pair['fixed_A'],reconstructed_B_weight_denominator=1,
    sparse_B_weights=[[i,n] for i,n in enumerate(integer) if n],B_budget_units=mb,
    original_scale=str(scale),maximum_float_reconstruction_error=max_error,
    finite_rows=len(rows),exception_rows=int(mask.sum()),finite_A_minimum_units=int(qa.min()),
    finite_B_global_minimum_units=minimum,finite_B_exception_minimum_units=emin,
    variants=variants,
    original_scale_rationals=dict(budget=str(mb*scale),global_minimum=str(minimum*scale),exception_minimum=str(emin*scale)),
    root_suggested_variant=dict(global_threshold='154/243',exception_threshold='307/243',counting_surplus='7/243',
                                all_finite_rows_pass=True),
    rows=str(path),rows_sha256=filehash(path),generator_sha256=filehash(Path(__file__)),
    scope='Exact finite reconstruction only. No A baseline, global B floor, or A/B disjunction has been established over all placements. This separate receipt does not replace or alter the approved D1e9 packet.')
need(7*F(154,243)+4*F(307,243)-mb*scale==F(7,243),'Suggested gate mismatch')
need(minimum*scale>=F(154,243) and emin*scale>=F(307,243),'Suggested finite gates fail')
dump(output,result)
print(json.dumps({k:v for k,v in result.items() if k not in ('fixed_A','sparse_B_weights')},indent=2))
