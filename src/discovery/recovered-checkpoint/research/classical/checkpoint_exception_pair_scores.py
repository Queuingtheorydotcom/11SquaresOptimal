#!/usr/bin/env python3
"""Compact exact scores for finite discovery rows, not continuum evidence."""
from pathlib import Path
from hashlib import sha256
import argparse,json
import numpy as np
from exception_charge_lp import budgets,filehash,need,dump


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--proposal',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    need(not args.output.exists() and not args.output.with_suffix('.json').exists(),'Use fresh checkpoint paths')
    raw=args.proposal.read_bytes();packet=json.loads(raw);fixed=packet['fixed_A'];b=packet['B'];finite=packet['finite_check']
    need(packet['status']=='EXACT_INTEGER_FINITE_ROW_CONDITIONAL_PROPOSAL_ONLY','Unsupported proposal')
    a_path=Path(fixed['certificate']);need(filehash(a_path)==fixed['certificate_sha256'],'A vector changed')
    a=json.loads(a_path.read_bytes());wA=np.array([p[2] for p in a['point_orbits']]+[p['weight'] for p in a['charge_orbits']],np.int64)
    wB=np.array(b['weight_units'],np.int64);need(len(wA)==len(wB),'Vector lengths differ')
    row_path=Path(finite['rows']);need(filehash(row_path)==finite['rows_sha256'],'Rows changed')
    rows=np.load(row_path,mmap_mode='r');need(rows.shape==(finite['rows_checked'],len(wA)) and rows.dtype==np.uint8,'Bad rows')
    cap=budgets(a);active=np.flatnonzero((wA>0)|(wB>0));qa=np.empty(len(rows),np.int64);qb=np.empty(len(rows),np.int64)
    for start in range(0,len(rows),8192):
        block=np.asarray(rows[start:start+8192][:,active],np.int64)
        need(np.all(block<=cap[active]),'Capture exceeds feature budget')
        qa[start:start+len(block)]=block@wA[active];qb[start:start+len(block)]=block@wB[active]
    mask=qa<fixed['strong_cutoff_units']
    need(np.flatnonzero(mask).tolist()==finite['exception_indices'],'Exception mask differs')
    need(int(qa.min())==finite['minimum_A_units'] and int(qb.min())==b['exact_finite_global_minimum_units']
         and int(qb[mask].min())==b['exact_finite_exception_minimum_units'],'Score extrema differ')
    need(np.all(qa>=fixed['required_global_baseline_units']),'Finite A baseline fails')
    for variant in packet['variants']:
        need(np.all(qb>=variant['global_units']) and np.all(qb[mask]>=variant['exception_units']),'Finite B threshold fails')
    need(filehash(row_path)==finite['rows_sha256'],'Rows changed during replay')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.output,qA_units=qa,qB_units=qb,exception_mask=mask,
                        A_weight_denominator=fixed['weight_denominator'],B_weight_denominator=b['weight_denominator'],
                        exception_cutoff_units=fixed['strong_cutoff_units'],A_baseline_units=fixed['required_global_baseline_units'])
    report=dict(status='PASS_EXACT_FINITE_PAIR_SCORE_CHECKPOINT',proposal=str(args.proposal),
                proposal_sha256=sha256(raw).hexdigest(),scores=str(args.output),scores_sha256=filehash(args.output),
                rows=len(rows),exceptions=int(mask.sum()),A_minimum_units=int(qa.min()),B_minimum_units=int(qb.min()),
                exceptional_B_minimum_units=int(qb[mask].min()),row_matrix_sha256=finite['rows_sha256'],
                generator_sha256=filehash(Path(__file__)),global_bound_proved=False,
                scope='Exact integer scores and threshold checks for the retained finite discovery rows only; no capture matrix copied and no continuum proof.')
    dump(args.output.with_suffix('.json'),report);print(json.dumps(report,indent=2))


if __name__=='__main__':main()
