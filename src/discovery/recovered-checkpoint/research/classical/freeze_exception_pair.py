#!/usr/bin/env python3
"""Freeze an exploratory conditional pair and check its finite rows exactly.

This creates no unconditional certificate and proves no continuum coverage.
"""
from fractions import Fraction as F
from pathlib import Path
from hashlib import sha256
import argparse,json,math,time
import numpy as np
from exception_charge_lp import budgets,filehash,need,dump


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--experiment',type=Path,required=True);p.add_argument('--denominator',type=int,default=10**9)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args();started=time.monotonic()
    need(not args.output.exists(),'Use a fresh immutable proposal output')
    experiment=json.loads(args.experiment.read_bytes());need(experiment['input_hashes_rechecked'] is True,'Incomplete finite experiment')
    for name,h in experiment['inputs'].items():need(filehash(name)==h,'Experiment input changed: '+name)
    record=next(q for q in experiment['solves'] if q['label']=='two-exceptions')
    need(record['success'] is True and record['exceptions_required']==2,'Missing successful r2 discovery vector')
    vector_path=Path(record['vector_path']);need(filehash(vector_path)==record['vector_sha256'],'Numerical B vector changed')
    source_path=Path(experiment['source_certificate']);need(filehash(source_path)==experiment['source_sha256'],'Feature source changed')
    source=json.loads(source_path.read_bytes())
    a_path=next(Path(name) for name in experiment['inputs'] if name.endswith('rational-proposal.json'))
    rows_path=next(Path(name) for name in experiment['inputs'] if name.endswith('.rows.npy'))
    a=json.loads(a_path.read_bytes());D_A=a['weight_denominator'];D=args.denominator
    need(type(D) is int and D>0 and D%1000==0,'B denominator must be a positive multiple of1000')
    need([q[:2] for q in source['point_orbits']]==[q[:2] for q in a['point_orbits']],'A point ordering differs from source')
    normalize=lambda g:{k:v for k,v in g.items() if k!='weight'}
    need([normalize(g) for g in source['charge_orbits']]==[normalize(g) for g in a['charge_orbits']],
         'A features differ from source')
    weightsA=np.array([q[2] for q in a['point_orbits']]+[q['weight'] for q in a['charge_orbits']],dtype=np.int64)
    coefficient_budgets=budgets(a);M_A=int(coefficient_budgets@weightsA)
    need(M_A==a['budget_units'],'A budget mismatch')
    with np.load(vector_path) as saved:binary=saved['weights'].copy()
    need(len(binary)==len(weightsA) and np.isfinite(binary).all(),'Invalid B numerical weights')
    integers=[]
    for value in binary:
        exact=F.from_float(float(value))*D
        integers.append(-((-exact.numerator)//exact.denominator))
    need(min(integers)>=0,'Ceiling does not remove a materially negative numerical weight')
    weightsB=np.array(integers,dtype=np.int64);M_B=int(coefficient_budgets@weightsB)
    need(M_A<2**60 and M_B<2**60,'Unsafe integer charge range')
    rows=np.load(rows_path,mmap_mode='r');need(rows.dtype==np.uint8 and rows.shape[1]==len(weightsA),'Capture row shape differs')
    active=np.flatnonzero((weightsA>0)|(weightsB>0));qA=np.empty(len(rows),np.int64);qB=np.empty(len(rows),np.int64)
    for start in range(0,len(rows),8192):
        block=np.asarray(rows[start:start+8192][:,active],dtype=np.int64)
        need(np.all(block<=coefficient_budgets[active]),'Capture coefficient exceeds its feature budget')
        qA[start:start+len(block)]=block@weightsA[active];qB[start:start+len(block)]=block@weightsB[active]
    N=np.flatnonzero(qA<D_A);need(N.tolist()==record['exceptional_indices'],'Exact exception classification changed')
    beta0=int(qB.min());delta0=int(qB[N].min());surplus=9*beta0+2*delta0-M_B
    need(surplus>0 and delta0>=beta0>=0,'Exact finite B minima do not satisfy the r2 gate')
    a0=F(M_A,D_A)-10+F(1,10000);a0_units=a0*D_A
    need(a0_units.denominator==1 and 0<=a0<=1,'A baseline is not an admissible integer threshold')
    need(np.all(qA>=int(a0_units)),'Finite row violates required A baseline')
    a3=F(9951,10000);a3_surplus=9+2*a3-F(M_A,D_A)
    need(a3_surplus>0,'Derived r3 baseline does not force three exceptions')
    common=(surplus-1)//11
    variants=[dict(label='equal_per_parent_relaxation',global_units=beta0-common,exception_units=delta0-common,
                   global_relaxation_units=common,exception_relaxation_units=common)]
    shift=3*(D//1000);beta1=beta0-shift;remaining=9*beta1+2*delta0-M_B
    need(beta1>=0 and remaining>0,'Requested .003 baseline relaxation exhausts the budget')
    extra=(remaining-1)//2
    variants.append(dict(label='global_relaxation_0.003_then_exception',global_units=beta1,exception_units=delta0-extra,
                         global_relaxation_units=shift,exception_relaxation_units=extra))
    for v in variants:
        beta,delta=v['global_units'],v['exception_units'];gap=9*beta+2*delta-M_B
        need(0<=beta<=delta and gap>0,'Variant lacks a strict counting contradiction')
        need(np.all(qB>=beta) and np.all(qB[N]>=delta),'Variant fails a stored row exactly')
        count3=8*beta+3*delta
        v.update(global_threshold=str(F(beta,D)),exception_threshold=str(F(delta,D)),
                 counting_surplus_units=gap,finite_global_margin_units=beta0-beta,
                 finite_exception_margin_units=delta0-delta,
                 proof_gates=dict(A_global='q_A(Q_A)>=a0',B_global='q_B(Q_B)>=global_threshold',
                                  conditional='q_A(Q_A)>=1 OR q_B(Q_B)>=exception_threshold',
                                  core_pairing='The A and B charges refer to the same parent; their core maps may differ only with an explicit matching-domain proof.'),
                 derived_r3_metadata=dict(required_A_baseline=str(a3),A_forcing_surplus=str(a3_surplus),
                     global_baseline_proved=False,counting_surplus_units=count3-M_B,
                     budget_to_count_ratio=str(F(M_B,count3)),normalized_budget_at_count11=str(F(11*M_B,count3))))
    result=dict(schema='conditional-exception-charge-pair-proposal-v1',
                status='EXACT_INTEGER_FINITE_ROW_CONDITIONAL_PROPOSAL_ONLY',global_bound_proved=False,
                source_certificate=str(source_path),source_sha256=filehash(source_path),
                proposed_side=a['bound'],proposed_parent_side=a['A'],L=a['L'],
                fixed_A=dict(certificate=str(a_path),certificate_sha256=filehash(a_path),
                    weight_denominator=D_A,budget_units=M_A,strong_cutoff_units=D_A,
                    required_global_baseline=str(a0),required_global_baseline_units=int(a0_units),
                    forced_exceptions=2,forcing_surplus=str(10+a0-F(M_A,D_A)),
                    globally_verified_baseline=False,
                    original_alpha_units=a['minimum_units'],original_alpha_is_not_the_exception_cutoff=True),
                B=dict(weight_denominator=D,weight_units=integers,budget_units=M_B,
                    positive_columns=int(np.count_nonzero(weightsB)),floating_vector=str(vector_path),
                    floating_vector_sha256=filehash(vector_path),
                    rounding='exact rational ceiling of every stored binary64 weight; tiny negative solver residues round upward to zero',
                    negative_float_residues=int(np.count_nonzero(binary<0)),minimum_stored_float=float(binary.min()),
                    exact_finite_global_minimum_units=beta0,exact_finite_exception_minimum_units=delta0,
                    unrelaxed_counting_surplus_units=surplus),variants=variants,
                finite_check=dict(experiment=str(args.experiment),experiment_sha256=filehash(args.experiment),
                    rows=str(rows_path),rows_sha256=filehash(rows_path),rows_checked=len(rows),
                    source_columns=rows.shape[1],exception_rows=len(N),exception_indices=N.tolist(),
                    classification='stored integer capture dot fixed integer A weights < A weight denominator',
                    minimum_A_units=int(qA.min()),all_rows_meet_A_baseline=True,
                    both_B_variants_checked_on_every_global_and_exception_row=True,
                    all_rows_meet_optional_r3_A_baseline=F(int(qA.min()),D_A)>=a3),
                input_hashes=dict(experiment['inputs']),generator_sha256=filehash(Path(__file__)),
                seconds=time.monotonic()-started,
                scope='Conditional pair proposal only. Exact integer finite-row checks do not prove the A baseline, B baseline, or disjunction over the continuum. The original995/1024 A interval passes are partial and do not complete any of these proof gates. No angle catalogue or unconditional certificate is emitted.')
    for name,h in result['input_hashes'].items():need(filehash(name)==h,'An input changed during freezing')
    need(filehash(vector_path)==record['vector_sha256'],'B vector changed during freezing')
    result['input_hashes_rechecked']=True;dump(args.output,result)
    brief={k:v for k,v in result.items() if k not in ('B','input_hashes')}
    brief['B']={k:v for k,v in result['B'].items() if k!='weight_units'}
    print(json.dumps(brief,indent=2))


if __name__=='__main__':main()
