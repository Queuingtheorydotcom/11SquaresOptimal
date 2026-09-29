#!/usr/bin/env python3
"""Freeze a separate primitive-integer conditional r4 proposal, finite only."""
from pathlib import Path
from fractions import Fraction as F
import json,time
import numpy as np
from exception_charge_lp import budgets,filehash,need,dump
ROOT=Path('research/classical');oldpath=ROOT/'cutround8-four-exception-repair1-pair-D1e9.json'
reconpath=ROOT/'cutround8-four-exception-repair1-small-integer.json'
outpath=ROOT/'cutround8-four-exception-repair1-pair-primitive.json'
need(not outpath.exists(),'Use a new immutable packet output')
start=time.monotonic();old=json.loads(oldpath.read_bytes());rec=json.loads(reconpath.read_bytes())
need(rec['original_pair_sha256']==filehash(oldpath),'Original proposal changed')
need(rec['status']=='PASS_EXACT_FINITE_SMALL_INTEGER_RECONSTRUCTION','Missing exact reconstruction')
result=json.loads(json.dumps(old));D_A=result['fixed_A']['weight_denominator'];a_path=Path(result['fixed_A']['certificate'])
need(filehash(a_path)==result['fixed_A']['certificate_sha256'],'A changed');a=json.loads(a_path.read_bytes())
wa=np.array([p[2] for p in a['point_orbits']]+[p['weight'] for p in a['charge_orbits']],np.int64)
wb=np.zeros(len(wa),np.int64)
for i,w in rec['sparse_B_weights']:
    need(type(i) is int and type(w) is int and 0<=i<len(wb) and 0<w<=8 and wb[i]==0,'Invalid sparse reconstruction')
    wb[i]=w
cap=budgets(a);MA=int(cap@wa);MB=int(cap@wb)
need(MA==result['fixed_A']['budget_units'] and MB==160,'Budget changed')
rows_path=Path(result['finite_check']['rows']);rows_hash=result['finite_check']['rows_sha256']
need(filehash(rows_path)==rows_hash,'Rows changed');rows=np.load(rows_path,mmap_mode='r')
qa=np.empty(len(rows),np.int64);qb=qa.copy();active=np.flatnonzero((wa>0)|(wb>0))
for startrow in range(0,len(rows),8192):
    block=np.asarray(rows[startrow:startrow+8192][:,active],np.int64)
    need(np.all(block<=cap[active]),'Capture exceeds budget')
    qa[startrow:startrow+len(block)]=block@wa[active];qb[startrow:startrow+len(block)]=block@wb[active]
mask=qa<result['fixed_A']['strong_cutoff_units'];need(np.flatnonzero(mask).tolist()==result['finite_check']['exception_indices'],'Exception set changed')
minimum=int(qb.min());emin=int(qb[mask].min());need((minimum,emin)==(8,30),'Primitive minima changed')
need(np.all(qa>=result['fixed_A']['required_global_baseline_units']),'Finite A baseline failed')
variants=[]
for label,beta,delta in [('primitive_global7_exception28',7,28),('primitive_global8_exception27',8,27)]:
    gap=7*beta+4*delta-MB
    need(0<=beta<=delta and gap>0 and np.all(qb>=beta) and np.all(qb[mask]>=delta),'Finite variant failed')
    variants.append(dict(label=label,global_units=beta,exception_units=delta,
        global_threshold=str(beta),exception_threshold=str(delta),counting_surplus_units=gap,
        global_relaxation_units=minimum-beta,exception_relaxation_units=emin-delta,
        finite_global_margin_units=minimum-beta,finite_exception_margin_units=emin-delta,
        proof_gates=old['variants'][0]['proof_gates']))
result['B']=dict(weight_denominator=1,weight_units=wb.tolist(),budget_units=MB,
    positive_columns=int(np.count_nonzero(wb)),maximum_weight=int(wb.max()),
    floating_vector=old['B']['floating_vector'],floating_vector_sha256=old['B']['floating_vector_sha256'],
    rounding='Separate primitive integer reconstruction; every integer finite row is rechecked. This is not a ceiling of the numerical vector.',
    original_numerical_scale='1/16',reconstruction_receipt=str(reconpath),reconstruction_sha256=filehash(reconpath),
    exact_finite_global_minimum_units=minimum,exact_finite_exception_minimum_units=emin,
    unrelaxed_counting_surplus_units=7*minimum+4*emin-MB)
result['variants']=variants
result['finite_check']['primitive_reconstruction_rechecked_on_every_row']=True
result['prior_proposal']=dict(path=str(oldpath),sha256=filehash(oldpath),relation='A remains fixed; this is a separate B vector and threshold allocation, not an amendment to the prior packet.')
result['generator_sha256']=filehash(Path(__file__))
result['seconds']=time.monotonic()-start
result['scope']='New conditional r4 pair proposal with primitive integer B weights. Exact integer finite-row checks do not prove the A baseline, B baseline, or disjunction over the continuum. No angle catalogue or unconditional certificate is emitted.'
for p,h in result['input_hashes'].items():need(filehash(p)==h,'Input changed during freeze')
need(filehash(rows_path)==rows_hash and filehash(oldpath)==rec['original_pair_sha256'],'Input changed during freeze')
result['input_hashes_rechecked']=True;dump(outpath,result)
print(json.dumps(dict(output=str(outpath),sha256=filehash(outpath),B_budget=MB,
    finite_global_minimum=minimum,finite_exception_minimum=emin,variants=variants),indent=2))
