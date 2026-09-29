#!/usr/bin/env python3
"""Two bounded finite-row exception-charge LPs; no geometric proof or pricing.

Every supplied row appears in the global constraints. qA classification uses
only exact integer arithmetic on the retained integer capture coefficients.
The permitted B columns are exactly the immutable pool's selected columns.
"""
from fractions import Fraction as F
from pathlib import Path
from hashlib import sha256
import argparse,json,time
import numpy as np
from scipy.sparse import csr_matrix,hstack,vstack
from scipy.optimize import linprog


def need(ok,message):
    if not ok:raise ValueError(message)


def filehash(path):
    h=sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()


def budgets(c):
    D=c['coordinate_denominator'];LD=int(F(c['L'])*D);out=[]
    for x,y,w in c['point_orbits']:
        out.append(len({(a,b) for u,v in ((x,y),(y,x)) for a in (u,LD-u) for b in (v,LD-v)}))
    for atom in c['charge_orbits']:
        kind=atom.get('kind','threshold');n=len(atom['sets'][0]);k=atom['threshold']
        need(kind in ('majority_hull','floor','threshold','convex_clique','edge_or'),'Unsupported feature')
        factor=1 if kind in ('majority_hull','convex_clique','edge_or') else n//k
        out.append(len(atom['sets'])*factor)
    return np.array(out,dtype=np.int64)


def dump(path,result):
    path=Path(path);temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(result,indent=2)+'\n');temporary.replace(path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--qA',type=Path,required=True);p.add_argument('--pool',type=Path,required=True)
    p.add_argument('--rows',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--time-limit',type=float,default=75);args=p.parse_args();started=time.monotonic()
    need(not args.output.exists(),'Use a fresh output result')
    raw=args.qA.read_bytes();c=json.loads(raw);den=c['weight_denominator'];alpha=c['minimum_units'];M=c['budget_units']
    weightsA=np.array([q[2] for q in c['point_orbits']]+[q['weight'] for q in c['charge_orbits']],dtype=np.int64)
    budget=budgets(c);need(int(budget@weightsA)==M and 11*alpha>M,'qA exact budget/count gate failed')
    need(np.all(weightsA>=0) and M<2**60,'Unsafe qA integer arithmetic')
    pool=np.load(args.pool);rows=np.load(args.rows,mmap_mode='r');selected=np.asarray(pool['selected_columns'],dtype=np.int64)
    need(rows.ndim==2 and rows.shape[1]==len(weightsA) and rows.dtype==np.uint8,'Row matrix does not match qA features')
    need(len(selected)==len(set(selected)) and 0<len(selected)<=400,'Allowed column cap violated')
    need(np.all((selected>=0)&(selected<len(weightsA))),'Invalid permitted columns')
    source=c['frozen_weight_provenance'];need(filehash(source['source'])==source['source_sha256'],'qA feature source changed')
    positive=np.flatnonzero(weightsA);qA=np.empty(len(rows),dtype=np.int64)
    for start in range(0,len(rows),8192):
        block=np.array(rows[start:start+8192][:,positive],dtype=np.int64)
        need(np.all(block<=budget[positive]),'Capture exceeds a feature global budget')
        qA[start:start+len(block)]=block@weightsA[positive]
    a0_two=F(M,den)-10+F(1,10000);a0_three=F(9951,10000)
    need(F(int(qA.min()),den)>=a0_two,'Finite pool fails the proposed two-exception baseline')
    hashes={str(path):filehash(path) for path in (args.qA,args.pool,args.rows)}
    matrix=csr_matrix(np.asarray(rows[:,selected]),dtype=np.float64);n=len(rows);k=len(selected)
    global_constraints=hstack([-matrix,csr_matrix(np.ones((n,1))),csr_matrix((n,1))],format='csr')
    result=dict(status='BOUNDED_FINITE_EXCEPTION_CHARGE_EXPERIMENT',inputs=hashes,
                source_certificate=source['source'],source_sha256=source['source_sha256'],
                discovery_target=float(pool['target']),discovery_parent_side=float(pool['A']),
                qA_proposal_target=c['bound'],qA_weight_denominator=den,qA_budget_units=M,
                qA_alpha_units=alpha,qA_counting_surplus_units=11*alpha-M,
                qA_minimum_stored_row_units=int(qA.min()),rows_retained=n,available_columns=rows.shape[1],
                permitted_columns=len(selected),selected_column_indices=selected.tolist(),
                baseline_two_exceptions=str(a0_two),baseline_three_exceptions=str(a0_three),
                finite_rows_meet_two_baseline=True,finite_rows_meet_three_baseline=F(int(qA.min()),den)>=a0_three,
                one_baseline_count_surplus=str(10+a0_two-F(M,den)),
                two_baseline_count_surplus=str(9+2*a0_three-F(M,den)),solves=[],
                global_bound_proved=False,
                scope='Exact classification relative to stored integer capture rows; two numerical B LPs retain every global row, with at most400 existing columns. No continuum lower bound, exact B certificate, new geometric pricing, or packing bound.')
    for label,threshold,exceptions_required in (('one-exception',alpha,1),('two-exceptions',den,2)):
        exceptional=np.flatnonzero(qA<threshold);m=len(exceptional)
        extra=hstack([-matrix[exceptional],csr_matrix((m,1)),csr_matrix(np.ones((m,1)))],format='csr')
        # beta-delta<=0 and -(11-r)beta-r*delta<=-11.
        tail=csr_matrix(([1.,-1.,-float(11-exceptions_required),-float(exceptions_required)],
                         ([0,0,1,1],[k,k+1,k,k+1])),shape=(2,k+2))
        constraints=vstack([global_constraints,extra,tail],format='csr')
        rhs=np.r_[np.zeros(n+m+1),-11.]
        print('SOLVE',label,'rows',n,'exceptional',m,'columns',k,'nonzeros',constraints.nnz,flush=True)
        tick=time.monotonic()
        lp=linprog(np.r_[budget[selected].astype(float),0.,0.],A_ub=constraints,b_ub=rhs,bounds=(0,None),
                   method='highs-ds',options={'threads':1,'time_limit':args.time_limit,
                                             'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
        record=dict(label=label,exceptions_required=exceptions_required,exception_threshold_units=int(threshold),
                    exceptional_rows=m,exceptional_indices=exceptional.tolist(),all_global_rows_retained=n,
                    constraint_rows=constraints.shape[0],solver_status=int(lp.status),solver_message=lp.message,
                    seconds=time.monotonic()-tick,success=bool(lp.success))
        if lp.success:
            values=matrix@lp.x[:k];beta,delta=map(float,lp.x[k:]);MB=float(budget[selected]@lp.x[:k])
            global_min=float(values.min());exception_min=float(values[exceptional].min()) if m else None
            count=(11-exceptions_required)*beta+exceptions_required*delta
            violations=max(beta-global_min,delta-exception_min if m else 0,beta-delta,11-count,0)
            need(violations<1e-7,'Numerical full-row check failed')
            full=np.zeros(len(weightsA));full[selected]=lp.x[:k]
            output=args.output.with_name(args.output.stem+'-'+label+'.npz')
            np.savez_compressed(output,weights=full,beta=beta,delta=delta,budget=MB,selected_columns=selected,
                                exception_indices=exceptional,qA_units=qA,alpha_units=threshold)
            record.update(budget=MB,beta=beta,delta=delta,count_lower_bound=count,
                          strict_finite_surplus=count-MB,budget_below_11=MB<11-1e-8,
                          global_row_minimum=global_min,exception_row_minimum=exception_min,
                          maximum_numerical_violation=violations,positive_columns=int(np.count_nonzero(lp.x[:k]>1e-10)),
                          vector_path=str(output),vector_sha256=filehash(output))
            if exceptions_required==2:
                count3=8*beta+3*delta
                record['derived_three_exception_case']=dict(required_global_qA_baseline=str(a0_three),
                    baseline_is_globally_proved=False,count_lower_bound=count3,strict_finite_surplus=count3-MB,
                    budget_to_count_ratio=MB/count3,normalized_budget_at_count11=11*MB/count3)
        result['solves'].append(record);result['elapsed_seconds']=time.monotonic()-started;dump(args.output,result)
        print(json.dumps(record,indent=2),flush=True)
        del constraints,extra
    for name,value in hashes.items():need(filehash(name)==value,'Frozen experiment input changed during the run')
    result['input_hashes_rechecked']=True;result['elapsed_seconds']=time.monotonic()-started;dump(args.output,result)


if __name__=='__main__':main()
