#!/usr/bin/env python3
"""Independent exact audit of an acyclic conditional-owned-point proof DAG."""
from fractions import Fraction as F
from pathlib import Path
import argparse,json,hashlib
import audit_conditional_ownership as base
import audit_wall_kernel as wall
from audit_kernel_survivor import hull_intersects
if not __debug__:raise RuntimeError('Assertions must be enabled')
def parse(groups):return [[tuple(map(F,p)) for p in g] for g in groups]
def digest(groups):return hashlib.sha256(json.dumps(groups,default=str,separators=(',',':')).encode()).hexdigest()
def prove_row_union(proof,prior,mask,poly,B,L):
    owner=proof['owner'];point=tuple(map(F,proof['point']))
    sites=[point]+[p for j in mask if j!=owner for p in prior[j]]
    rows={tuple(map(F,r['interval'])):r for r in proof['records'] if r['status'].startswith('PASS')}
    accepted=[tuple(map(F,r)) for r in proof['accepted']]
    assert not proof['pending'] and not proof['failed']
    assert accepted and accepted[0][0]==0 and accepted[-1][1]==1
    assert all(x[1]==y[0] for x,y in zip(accepted,accepted[1:]))
    counts=0
    for lo,hi in accepted:
        assert 0<=lo<hi<=1
        r=rows[(lo,hi)];t=(lo+hi)/2;c,s=base.cs(t); widths=[];factors=[]
        for v in (lo,hi):
            cv,sv=base.cs(v);dot=c*cv+s*sv;cross=abs(c*sv-s*cv)
            assert dot>0 and dot>=cross
            widths.append(cv+sv);factors.append(dot+cross)
        core=(B-F(1,10**12))/max(factors)
        assert core==F(r['core_side']) and t==F(r['reference_half_angle']) and core*max(factors)<B
        h=B*min(widths)/2;domain=poly
        for axis in (0,1):domain=base.clip(base.clip(domain,axis,h,True),axis,L-h,False)
        ans=base.rectangle_cover(domain,sites,core,t);assert ans['passed'],ans
        counts+=ans['slabs']
    return len(accepted),counts
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('receipt',type=Path);ap.add_argument('--packet',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--structure-only',action='store_true');args=ap.parse_args()
    d=json.loads(args.receipt.read_text());packet=json.loads(args.packet.read_text());cover=json.loads(base.COVER.read_text())
    assert d['cover_sha256']==base.sha(base.COVER) and d['packet_sha256']==base.sha(args.packet)
    U=F(d['parent_Uplus']);L=F(191,50);B=L/U
    assert U==wall.U and B==wall.B==F(d['parent_side'])
    mask=d['mask'];assert mask==packet['mask']==cover['canonical_eleven_cell_subsets'][d['mask_index']]
    polysunit=wall.read_cells();polys=[[tuple(B*x for x in v) for v in p] for p in polysunit]
    groups=parse(packet['ownership_points_field']);seed_count=0;seed_leaves=0
    for j,group in enumerate(groups):
        for p in group:
            if not args.structure_only:
                ans=wall.check_point(polysunit[j],tuple(v/B for v in p));assert ans['passed']
                seed_leaves+=ans['leaves']
            seed_count+=1
    checks=[];covered=[]
    for round_num,round_data in enumerate(d['rounds'],1):
        assert round_data['index']==round_num and parse(round_data['prior_owned_points'])==groups
        prior=parse(round_data['prior_owned_points']);assert digest(prior)==round_data['prior_snapshot_sha256']
        for idx,p in enumerate(d['proofs']):
            if p['round']!=round_num:continue
            assert p['prior_snapshot_sha256']==digest(prior) and p['owner'] in mask
            point=tuple(map(F,p['point']));gen=tuple(B*(F(1,2)+(U-1)*F(x)) for x in cover['cells'][p['owner']]['center'])
            assert point==tuple(gen[k]+B*F(p['radius'])*F(p['direction'][k]) for k in (0,1))
            if args.structure_only:
                accepted=[tuple(map(F,r)) for r in p['accepted']]
                assert accepted and accepted[0][0]==0 and accepted[-1][1]==1
                assert all(x[1]==y[0] for x,y in zip(accepted,accepted[1:]))
                assert not p['pending'] and not p['failed']
                passes={tuple(map(F,r['interval'])) for r in p['records'] if r['status'].startswith('PASS')}
                assert all(pair in passes for pair in accepted)
                rows,slabs=len(accepted),0
            else:
                rows,slabs=prove_row_union(p,prior,mask,polys[p['owner']],B,L)
            assert point not in groups[p['owner']]
            groups[p['owner']].append(point);covered.append(idx)
            checks.append(dict(proof_index=idx,round=round_num,owner=p['owner'],angle_rows=rows,rectangle_slabs=slabs))
            if len(checks)%20==0:print('Proof records checked:',len(checks),flush=True)
    assert sorted(covered)==list(range(len(d['proofs']))) and groups==parse(d['owned_points'])
    contradiction=None
    if d['contradiction'] and not args.structure_only:
        i,j=d['contradiction']['owners'];assert i in mask and j in mask and i!=j
        assert hull_intersects(groups[i],groups[j])
        contradiction=dict(owners=[i,j],owned_hulls_intersect=True)
    out=dict(status='PASS_STRUCTURAL_DAG_AUDIT_ONLY' if args.structure_only else 'PASS_INDEPENDENT_CONDITIONAL_CLOSURE_AUDIT',
       source_sha256=base.sha(args.receipt),packet_sha256=base.sha(args.packet),cover_sha256=base.sha(base.COVER),
       checker_dependencies={str(p.name):base.sha(p) for p in (Path(__file__),Path(base.__file__),Path(wall.__file__),Path(__file__).with_name('audit_kernel_survivor.py'))},
       mask_index=d['mask_index'],unconditional_seed_points=seed_count,unconditional_seed_leaves=seed_leaves,
       acyclic_rounds=len(d['rounds']),conditional_points=len(checks),exact_angle_rows=sum(x['angle_rows'] for x in checks),
       exact_rectangle_slabs=sum(x['rectangle_slabs'] for x in checks),proofs=checks,contradiction=contradiction,
       global_optimality_proved=False,mask_exclusion_proved=contradiction is not None,
       geometry_independently_replayed=not args.structure_only,
       scope=('Only dependency snapshots, acyclic proof references, accepted partitions and output groups were checked; geometry was not independently replayed.' if args.structure_only else 'Seeds independently proved by rational wall-envelope intervals; all learned points independently proved by rational rectangle union coverage using only the immutable preceding-round snapshot.'))
    args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='proofs'},indent=2))
if __name__=='__main__':main()
