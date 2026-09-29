"""Exact dual replay for the supplied affine SAT contraction model.

The floating LP proposes nonnegative multipliers only. For A*d<=b and
|d[k]|<=r[k], lambda>=0 proves
 c*d <= lambda*b + sum(abs(c-lambda*A)*r).
Every promoted bound is computed with GMP rationals. The model's geometric
soundness and root antecedents are separate proof obligations.
"""
from pathlib import Path
import argparse, json, time, math
import run_capture as R
import angle_center_screen as S
E=R.E
F=E.F

def fold_at_empty_gap(a,b):
    # Quarter-turn equivalence sends t to (t-1)/(t+1). A common cut
    # preserves one pi/2-wide angular chart and hence cos(theta_i-theta_j)>=0.
    # The archived cut at 1/2 unnecessarily split the candidate's rotated
    # squares; 2/3 lies inside the root's common gap in all live pose covers.
    q=F(2,3);out=[]
    if a<=q:out.append((a,min(b,q)))
    if b>=q:
        u=max(a,q);out.append(((u-1)/(u+1),(b-1)/(b+1)))
    return out

S.fold=fold_at_empty_gap

def bound(model, numerical, coordinate, sign, grid=10**12):
    rows=model['inequalities'];r=model['radii'];n=len(r)
    weights=[]
    for i,x in enumerate(numerical):
        # scipy reports nonpositive multipliers for minimizing -sign*d[k].
        q=max(0,round(-x*grid))
        if q: weights.append((i,F(q,grid)))
    residual=[F(sign if k==coordinate else 0) for k in range(n)]
    upper=F(0)
    for i,q in weights:
        assert q>=0
        row=rows[i];upper+=q*row['upper']
        for k,a in enumerate(row['coefficients']):residual[k]-=q*a
    correction=sum(abs(e)*v for e,v in zip(residual,r))
    return dict(coordinate=coordinate,sign=sign,weights=weights,
                residual=residual,box_correction=correction,
                upper=upper+correction)

def contract(model,answer):
    certs=[];new=[]
    for k,d in enumerate(answer['duals_for_discovery']):
        lo=bound(model,d['lower_dual'],k,-1)
        hi=bound(model,d['upper_dual'],k,1)
        certs.extend([lo,hi])
        m,r=model['midpoints'][k],model['radii'][k]
        a=max(m-r,m-lo['upper']);b=min(m+r,m+hi['upper'])
        # Outward grid rounding controls rational size without losing rigor.
        scale=10**12
        a=max(m-r,F(math.floor(a*scale),scale))
        b=min(m+r,F(math.ceil(b*scale),scale))
        new.append([a,b])
    return new,certs

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--rounds',type=int,default=20)
    ap.add_argument('--resume',action='store_true')
    args=ap.parse_args();source=args.source or R.ARCHIVE/'work/phase2/conditional/mask438-adaptive.json'
    state,parent=(E.load_state(source) if args.resume else (E.root_state(source),None))
    override=None;rounds=[];start=time.monotonic()
    for k in range(args.rounds):
        model=S.build(state,override);answer=S.solve(model,state)
        record=dict(index=k,model=model,discovery_status=answer['status'])
        if answer['status']!=0:
            rounds.append(record);break
        updated,certs=contract(model,answer)
        record.update(bound_certificates=certs,certified_box=updated)
        rounds.append(record)
        widths=[float((updated[3*j+a][1]-updated[3*j+a][0])/state['B']) for j in range(11) for a in (0,1)]
        print(json.dumps(dict(round=k,rows=len(model['inequalities']),maxwidth=max(widths),seconds=time.monotonic()-start)),flush=True)
        E.save(args.output,dict(schema='exact_affine_sat_contraction_v1',source=dict(path=str(source.resolve()),sha256=E.sha(source)),parent=parent,rounds=rounds,
                arithmetic_bounds_verified=True,geometric_model_independently_audited=False,root_independently_audited=False,
                global_optimality_proved=False,mask_capture_proved=False,seconds=time.monotonic()-start,
                dependencies={str(p):E.sha(p) for p in [Path(__file__),Path(R.__file__),Path(S.__file__)]}))
        if updated==override:break
        override=updated
    print(json.dumps(dict(final_box=override),default=str),flush=True)

if __name__=='__main__':main()
