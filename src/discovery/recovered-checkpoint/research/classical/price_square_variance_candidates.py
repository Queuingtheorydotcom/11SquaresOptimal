#!/usr/bin/env python3
"""Numerical reduced-cost pricing of exact accepted captured-pattern rules.

Only positive-mass poses of an immutable LP dual are used. No LP/certificate
input is mutated. D4 images of (group,pattern) are deduplicated together, so a
pattern that breaks a group's stabilizer receives the correct larger budget.
"""
from pathlib import Path
from fractions import Fraction as F
from hashlib import sha256
import argparse,json,time
import numpy as np


def filehash(path):
    h=sha256()
    with path.open('rb') as f:
        while data:=f.read(1024*1024):h.update(data)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidates',type=Path,required=True)
    p.add_argument('--dual',type=Path,required=True)
    p.add_argument('--resolve-active-full-family',action='store_true',help='Two small exploratory LPs on the old active poses only')
    p.add_argument('--output',type=Path,required=True);args=p.parse_args();started=time.monotonic()
    candidates=json.loads(args.candidates.read_bytes());source=Path(candidates['source'])
    assert filehash(source)==candidates['source_sha256']
    c=json.loads(source.read_bytes());D=c['coordinate_denominator'];LD=int(F(c['L'])*D)
    ps=[]
    for x,y,_ in c['point_orbits']:
        ps.extend(sorted({(a,b) for u,v in ((x,y),(y,x)) for a in (u,LD-u) for b in (v,LD-v)}))
    lookup={p:i for i,p in enumerate(ps)};assert len(lookup)==len(ps)
    maps=[]
    for swap in (False,True):
        for fx in (False,True):
            for fy in (False,True):
                transformed=[]
                for x,y in ps:
                    if swap:x,y=y,x
                    transformed.append(lookup[(LD-x if fx else x,LD-y if fy else y)])
                maps.append(transformed)
    pool=np.load(args.dual);A=float(pool['A']);assert abs(A-float(F(candidates['maximum_core_side'])))<1e-15
    dual=-pool['duals'];active=np.flatnonzero(dual>1e-9);masses=dual[active]
    poses=pool['placements'][active];xy=np.array(ps,dtype=float)/D
    dx=xy[None,:,0]-poses[:,None,1];dy=xy[None,:,1]-poses[:,None,2]
    co=np.cos(poses[:,0,None]);si=np.sin(poses[:,0,None])
    # Tiny inward guard makes boundary uncertainty lower, not inflate, scores.
    capture=(abs(co*dx+si*dy)<=A/2-1e-11)&(abs(-si*dx+co*dy)<=A/2-1e-11)
    old_rows=pool['rows'][active]
    old_budgets=np.array([len({(a,b) for u,v in ((x,y),(y,x)) for a in (u,LD-u) for b in (v,LD-v)})
                          for x,y,_ in c['point_orbits']]
                         +[len(g['sets'])*(len(g['sets'][0])//g['threshold']) for g in c['charge_orbits']],float)
    old_ratios=(masses@old_rows)/old_budgets
    results=[];new_columns=[]
    for index,rule in enumerate(candidates['rules']):
        ids=rule['sites'];pattern=rule['pattern_global'];k=c['charge_orbits'][rule['orbit']]['threshold']
        images=sorted({(tuple(sorted(mp[i] for i in ids)),tuple(sorted(mp[i] for i in pattern))) for mp in maps})
        baseline=np.zeros(len(active),dtype=np.int16);new=np.zeros(len(active),dtype=np.int16)
        for group,support in images:
            threshold=capture[:,group].sum(axis=1)>=k
            extra=capture[:,support].all(axis=1)
            baseline+=threshold;new+=threshold|extra
        price=float(masses@new);budget=len(images)
        multiplicity=budget/len(c['charge_orbits'][rule['orbit']]['sets'])
        assert multiplicity==int(multiplicity)
        old_true=old_rows[:,len(c['point_orbits'])+rule['orbit']].astype(float)*multiplicity
        old_true_price=float(masses@old_true)
        new_columns.append(new.copy())
        results.append(dict(candidate_index=index,orbit=rule['orbit'],pattern_local=rule['pattern_local'],
                            budget=budget,dual_price=price,price_over_budget=price/budget,
                            threshold_price=float(masses@baseline),added_price=float(masses@(new-baseline)),
                            source_true_price=old_true_price,price_gain_over_source_true=price-old_true_price,
                            active_poses_gaining_over_source_true=int(np.count_nonzero(new>old_true)),
                            active_poses_losing_to_source_true=int(np.count_nonzero(new<old_true)),
                            active_poses_with_added_capture=int(np.count_nonzero(new>baseline)),
                            has_variance_disk_witness=any(q['proof']['kind']=='variance_disks' for q in rule['proofs'])))
    resolved=None
    if args.resolve_active_full_family:
        from scipy.optimize import linprog
        rows=np.asarray(old_rows,float);extra=np.array(new_columns,float).T
        new_budgets=np.array([q['budget'] for q in results],float)
        options={'threads':1,'time_limit':30.0}
        base=linprog(old_budgets,A_ub=-rows,b_ub=-np.ones(len(active)),bounds=(0,None),method='highs-ds',options=options)
        assert base.success,base.message
        full_mass=-base.ineqlin.marginals;full_old_ratios=(full_mass@rows)/old_budgets
        assert full_old_ratios.max()<1+1e-7
        full_new_ratios=(full_mass@extra)/new_budgets
        augmented=linprog(np.r_[old_budgets,new_budgets],A_ub=-np.c_[rows,extra],
                          b_ub=-np.ones(len(active)),bounds=(0,None),method='highs-ds',options=options)
        assert augmented.success,augmented.message
        for q,ratio in zip(results,full_new_ratios):q['all_old_columns_active_pose_dual_ratio']=float(ratio)
        resolved=dict(scope='Only the119original dual-active poses; no all170182-pose check.',
                      old_family_budget=float(base.fun),augmented_budget=float(augmented.fun),
                      finite_active_pose_gain=float(base.fun-augmented.fun),
                      existing_maximum_ratio=float(full_old_ratios.max()),
                      new_maximum_ratio=float(full_new_ratios.max()),
                      positive_new_prices=int(np.count_nonzero(full_new_ratios>1+1e-8)),
                      new_columns_used=int(np.count_nonzero(augmented.x[len(old_budgets):]>1e-9)),
                      used_rules=[dict(candidate_index=i,weight=float(v)) for i,v in enumerate(augmented.x[len(old_budgets):]) if v>1e-9])
    results.sort(key=lambda q:q['price_over_budget'],reverse=True)
    out=dict(status='NUMERICAL_IMMUTABLE_DUAL_PRICING',source=str(source),source_sha256=filehash(source),
             candidates=str(args.candidates),candidates_sha256=filehash(args.candidates),dual=str(args.dual),
             dual_sha256=filehash(args.dual),A=A,finite_pool_budget=float(pool['budget']),
             total_pool_poses=len(dual),positive_mass_poses=len(active),positive_dual_mass=float(masses.sum()),
             dropped_dual_mass=float(dual[(dual>0)&(dual<=1e-9)].sum()),capture_inward_guard=1e-11,
             candidates_priced=len(results),positive_reduced_cost_count=sum(q['price_over_budget']>1+1e-8 for q in results),
             existing_columns_above_budget=int(np.count_nonzero(old_ratios>1+1e-8)),
             existing_maximum_price_over_budget=float(old_ratios.max()),
             rules_with_price_gain_over_source_true=sum(q['price_gain_over_source_true']>1e-8 for q in results),
             best_price_over_budget=results[0]['price_over_budget'],results=results,
             all_old_columns_active_pose_resolve=resolved,
             seconds=time.monotonic()-started,
             scope='Numerical pricing only. The supplied dual may come from a restricted-column LP; existing-column violations are reported, so positive new-column prices alone do not prove a new-family gain. Candidate budgets were checked separately at the recorded A. No modified LP, continuum verification, TRUE-OR-support union, or packing bound.')
    args.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='results'},indent=2));print(json.dumps(results[:12],indent=2))


if __name__=='__main__':main()
