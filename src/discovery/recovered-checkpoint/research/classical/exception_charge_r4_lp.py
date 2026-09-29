#!/usr/bin/env python3
"""One bounded r=4 finite exception-charge LP after the cutround8 parents.

Every stored global row is retained; no column-generation or geometry checker
is changed. The optional A baseline is a finite premise, not a global proof.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse,json,time
import numpy as np
from scipy.sparse import csr_matrix,hstack,vstack
from scipy.optimize import linprog
from exception_charge_lp import budgets,filehash,need,dump


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--qA',type=Path,required=True)
    p.add_argument('--columns-snapshot',type=Path,required=True);p.add_argument('--rows',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--time-limit',type=float,default=75)
    args=p.parse_args();need(not args.output.exists(),'Use a fresh output');started=time.monotonic()
    paths=(args.qA,args.columns_snapshot,args.rows);hashes={str(x):filehash(x) for x in paths}
    c=json.loads(args.qA.read_bytes());wA=np.array([r[2] for r in c['point_orbits']]+[r['weight'] for r in c['charge_orbits']],np.int64)
    D=c['weight_denominator'];M=c['budget_units'];cost=budgets(c)
    need(int(cost@wA)==M and np.all(wA>=0) and M<2**60,'Invalid A budget/weights')
    provenance=c['frozen_weight_provenance'];need(filehash(provenance['source'])==provenance['source_sha256'],'Source changed')
    pool=np.load(args.columns_snapshot);columns=pool['selected_columns'];need(len(columns)==len(set(columns))<=400,'Bad column cap')
    rows=np.load(args.rows,mmap_mode='r');need(rows.dtype==np.uint8 and rows.shape[1]==len(wA),'Bad coefficient rows')
    positive=np.flatnonzero(wA);qa=np.empty(len(rows),np.int64)
    for start in range(0,len(rows),8192):
        block=np.asarray(rows[start:start+8192][:,positive],np.int64)
        need(np.all(block<=cost[positive]),'Capture exceeds feature budget');qa[start:start+len(block)]=block@wA[positive]
    a0=F(9967,10000);forcing=8+3*a0-F(M,D)
    need(forcing>0 and F(int(qa.min()),D)>=a0,'Finite A rows do not support the r4 baseline')
    exceptions=np.flatnonzero(qa<D);n=len(rows);k=len(columns);m=len(exceptions)
    matrix=csr_matrix(np.asarray(rows[:,columns]),dtype=float)
    global_rows=hstack([-matrix,csr_matrix(np.ones((n,1))),csr_matrix((n,1))],format='csr')
    extra=hstack([-matrix[exceptions],csr_matrix((m,1)),csr_matrix(np.ones((m,1)))],format='csr')
    tail=csr_matrix(([1.,-1.,-7.,-4.],([0,0,1,1],[k,k+1,k,k+1])),shape=(2,k+2))
    constraints=vstack([global_rows,extra,tail],format='csr');rhs=np.r_[np.zeros(n+m+1),-11.]
    print('SOLVE r4','rows',n,'exceptions',m,'columns',k,'nonzeros',constraints.nnz,flush=True);tick=time.monotonic()
    lp=linprog(np.r_[cost[columns].astype(float),0.,0.],A_ub=constraints,b_ub=rhs,bounds=(0,None),method='highs-ds',
               options={'threads':1,'time_limit':args.time_limit,'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
    result=dict(status='BOUNDED_FINITE_FOUR_EXCEPTION_CHARGE_EXPERIMENT',inputs=hashes,
                source_certificate=provenance['source'],source_sha256=provenance['source_sha256'],
                qA_weight_denominator=D,qA_budget_units=M,strong_cutoff_units=D,
                required_global_A_baseline=str(a0),A_forcing_surplus=str(forcing),A_baseline_globally_proved=False,
                minimum_stored_A_units=int(qa.min()),rows_retained=n,exception_rows=m,exception_indices=exceptions.tolist(),
                allowed_columns=columns.tolist(),permitted_column_count=k,exceptions_required=4,
                discovery_target=float(pool['target']),qA_proposal_target=c['bound'],
                constraint_rows=constraints.shape[0],solver_success=bool(lp.success),solver_status=int(lp.status),
                solver_message=lp.message,solver_seconds=time.monotonic()-tick,
                global_bound_proved=False,
                scope='One numerical finite-row B LP on fixed existing columns, with exact classification of stored integer A scores. All rows retained. No global A baseline, B floor, conditional floor, or packing theorem is proved.')
    if lp.success:
        values=matrix@lp.x[:k];beta,delta=map(float,lp.x[k:]);MB=float(cost[columns]@lp.x[:k]);count=7*beta+4*delta
        lower=float(values.min());conditional=float(values[exceptions].min());error=max(0,beta-lower,delta-conditional,beta-delta,11-count)
        need(error<1e-7,'Full stored-row numerical check failed')
        weights=np.zeros(len(wA));weights[columns]=lp.x[:k];vector=args.output.with_suffix('.npz')
        np.savez_compressed(vector,weights=weights,beta=beta,delta=delta,budget=MB,selected_columns=columns,
                            exception_indices=exceptions,qA_units=qa,A=float(pool['A']),target=float(pool['target']))
        result.update(B_budget=MB,beta=beta,delta=delta,count_lower_bound=count,finite_surplus=count-MB,
                      global_row_minimum=lower,exception_row_minimum=conditional,maximum_numerical_violation=error,
                      positive_columns=int(np.count_nonzero(lp.x[:k]>1e-10)),minimum_float_weight=float(lp.x[:k].min()),
                      vector=str(vector),vector_sha256=filehash(vector))
    for path,h in hashes.items():need(filehash(path)==h,'Input changed during bounded solve')
    result['input_hashes_rechecked']=True;result['elapsed_seconds']=time.monotonic()-started;dump(args.output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('allowed_columns','exception_indices')},indent=2))


if __name__=='__main__':main()
