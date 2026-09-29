"""Rational certification of the archived coupled-center LP relaxation."""
from pathlib import Path
import argparse,json,time
import numpy as np
from scipy.optimize import linprog
from run_capture import E
import coupled_center_screen as Q
import affine_contract_v2 as A
import exact_angle_contract as C

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    state,parent=E.load_state(args.source);start=time.monotonic();d=Q.build(state)
    if 'contradiction_pair' in d:
        E.save(args.output,dict(source=parent,geometry=d,exact_pair_relaxation_empty=True,global_optimality_proved=False));return
    mid=[];rad=[]
    for owner in state['mask']:
        ps=d['domains'][owner]
        for axis in (0,1):
            a=min(p[axis] for p in ps);b=max(p[axis] for p in ps);mid.append((a+b)/2);rad.append((b-a)/2)
    rows=[]
    for row in d['inequalities']:
        row=dict(row);row['upper']-=sum(a*m for a,m in zip(row['coefficients'],mid));rows.append(row)
    model=dict(inequalities=rows,midpoints=mid,radii=rad)
    mat=np.array([[float(v) for v in r['coefficients']] for r in rows]);rhs=np.array([float(r['upper']) for r in rows]);N=len(mid);zero=np.zeros(N)
    trial=linprog(zero,A_ub=mat,b_ub=rhs,bounds=[(None,None)]*N,method='highs');certificates=[];box=[];infeasible=False
    if trial.status==2:
        certificate=A.farkas(model);infeasible=certificate['proved'];certificates=[certificate]
    elif trial.success:
        for k in range(N):
            c=zero.copy();c[k]=1
            lo=linprog(c,A_ub=mat,b_ub=rhs,bounds=[(None,None)]*N,method='highs')
            hi=linprog(-c,A_ub=mat,b_ub=rhs,bounds=[(None,None)]*N,method='highs')
            assert lo.success and hi.success
            lower=C.bound(model,lo.ineqlin.marginals,k,-1);upper=C.bound(model,hi.ineqlin.marginals,k,1)
            certificates.extend([lower,upper]);box.append([max(mid[k]-rad[k],mid[k]-lower['upper']),min(mid[k]+rad[k],mid[k]+upper['upper'])])
    output=dict(source=parent,geometry=d,model=model,exact_certificates=certificates,center_box=box,
                numerical_status=int(trial.status),exact_relaxation_infeasible=infeasible,
                geometric_model_independently_audited=False,unconditional_packing_exclusion_proved=False,global_optimality_proved=False,seconds=time.monotonic()-start)
    E.save(args.output,output)
    print(json.dumps(dict(status=int(trial.status),exact_relaxation_infeasible=infeasible,
           old_max_width=max(float(2*r/state['B']) for r in rad),
           new_max_width=max((float((b-a)/state['B']) for a,b in box),default=None),seconds=output['seconds'])),flush=True)

if __name__=='__main__':main()
