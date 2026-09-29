"""Portable exact affine contraction with a rational Farkas fallback.

The geometric Taylor model is supplied by angle_center_screen.py. A common
quarter-turn chart is chosen inside the largest empty angular gap. All accepted
bounds and contradictions use rational dual sums with a box residual correction.
"""
from pathlib import Path
import argparse,json,time
import numpy as np
from scipy.optimize import linprog
import exact_angle_contract as C
E,S,F=C.E,C.S,C.F

def chart(state):
    intervals=sorted((r['interval'] for i in state['mask'] for r in E.partner_rows(state,i) if r['domain']))
    merged=[]
    for a,b in intervals:
        if merged and a<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],b)
        else:merged.append([a,b])
    gaps=[(b,c) for (_,b),(c,_) in zip(merged,merged[1:]) if b<c]
    q=sum(max(gaps,key=lambda p:p[1]-p[0]))/2 if gaps else F(2,3)
    def fold(a,b):
        out=[]
        if a<=q:out.append((a,min(b,q)))
        if b>=q:
            u=max(a,q);out.append(((u-1)/(u+1),(b-1)/(b+1)))
        return out
    S.fold=fold
    return q

def farkas(model):
    rows=model['inequalities'];n=len(model['radii']);m=len(rows)
    A=np.array([[float(v) for v in r['coefficients']] for r in rows]);b=np.array([float(r['upper']) for r in rows])
    trial=linprog(b,A_eq=np.vstack((A.T,np.ones(m))),b_eq=np.r_[np.zeros(n),1.0],bounds=(0,None),method='highs')
    if not trial.success:return dict(proved=False,numerical_status=int(trial.status))
    weights=[(i,F(max(0,round(x*10**15)),10**15)) for i,x in enumerate(trial.x) if x>1e-18]
    residual=[F(0)]*n;value=F(0)
    for i,q in weights:
        assert q>=0
        value+=q*rows[i]['upper']
        for k,a in enumerate(rows[i]['coefficients']):residual[k]+=q*a
    correction=sum(abs(a)*r for a,r in zip(residual,model['radii']))
    upper=value+correction
    return dict(proved=upper<0,weights=weights,residual=residual,weighted_rhs=value,box_correction=correction,contradiction_upper=upper)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--rounds',type=int,default=20)
    args=ap.parse_args();state,parent=E.load_state(args.source);q=chart(state);override=None;rounds=[];start=time.monotonic();infeasible=False
    for k in range(args.rounds):
        model=S.build(state,override);answer=S.solve(model,state);record=dict(index=k,model=model,numerical_status=answer['status'])
        if answer['status']==0:
            updated,certificates=C.contract(model,answer)
            record.update(bound_certificates=certificates,certified_box=updated)
            change=max((float((b-a)-(d-c)) for (a,b),(c,d) in zip(override or model['initial_box'],updated)),default=0)
            width=max(float((updated[3*j+a][1]-updated[3*j+a][0])/state['B']) for j in range(len(state['mask'])) for a in (0,1))
            print(json.dumps(dict(round=k,max_center_width=width,largest_bound_width_improvement=change,seconds=time.monotonic()-start)),flush=True)
        else:
            certificate=farkas(model);record['farkas']=certificate;infeasible=certificate['proved']
            print(json.dumps(dict(round=k,exact_relaxation_infeasible=infeasible,certificate=certificate),default=str),flush=True)
        rounds.append(record)
        E.save(args.output,dict(schema='exact_affine_sat_contraction_v2',source=parent,half_angle_chart_cut=q,rounds=rounds,
                    exact_relaxation_infeasible=infeasible,unconditional_packing_exclusion_proved=False,
                    scope='Rational affine-model inference; geometric model, full root antecedents, and ancestry require separate audit.',
                    global_optimality_proved=False,seconds=time.monotonic()-start,
                    dependencies={str(p):E.sha(p) for p in [Path(__file__),Path(C.__file__),Path(S.__file__),Path(C.R.__file__)]}))
        if answer['status']!=0:break
        if updated==override or change<1e-11:break
        override=updated

if __name__=='__main__':main()
