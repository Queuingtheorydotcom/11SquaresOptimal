#!/usr/bin/env python3
"""Source-distinct replay of iterative owned-hull residual-domain contraction."""
from rational import F
import rational
from pathlib import Path
import argparse,hashlib,json,os,sys,time
import arrangement_audit as geo
WORK=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(WORK/'geometry'))
import audit_wall_kernel as wall
from audit_kernel_survivor import hull_intersects
if not __debug__:raise RuntimeError('Assertions must be enabled')
ROOT=Path(os.environ.get('ELEVEN_PACKING_ROOT',str(WORK.parent/'current'))).resolve()
COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
GUARDS=ROOT/'research/optimality/global_capture/local-capture-guards.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(poly):return [tuple(map(F,p)) for p in poly]
def groups_parse(groups):return [parse(p) for p in groups]
def canon(x):return json.dumps(x,default=str,sort_keys=True,separators=(',',':')).encode()
def verify_convex_combinations(original,receipt):
    pts=parse(receipt.get('vertices',receipt.get('points',[])));D=int(receipt['denominator'])
    assert len(pts)==len(receipt['witnesses']) and len(pts)<=receipt['directions']
    for p,w in zip(pts,receipt['witnesses']):
        assert p==tuple(map(F,w['point'])) and all((x*D).denominator==1 for x in p)
        ids=w['indices'];weights=list(map(F,w['weights']))
        assert len(ids)==len(weights) and 1<=len(ids)<=3 and all(0<=i<len(original) for i in ids)
        assert min(weights)>=0 and sum(weights)==1
        assert p==tuple(sum(a*original[i][k] for i,a in zip(ids,weights)) for k in (0,1))
    return pts
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('receipt',type=Path);ap.add_argument('--seed',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    begin=time.monotonic();d=json.loads(args.receipt.read_text());seed=json.loads(args.seed.read_text());cover=json.loads(COVER.read_text())
    assert d['cover_sha256']==seed['cover_sha256']==sha(COVER) and d['seed_sha256']==sha(args.seed)
    mask=d['mask'];assert d['mask_index']==seed['mask_index'] and mask==seed['mask']==cover['canonical_eleven_cell_subsets'][d['mask_index']]
    U=F(d['parent_Uplus']);B=geo.L/U;assert U==wall.U and B==wall.B==F(d['parent_side'])
    worlds=[[tuple(B*(F(1,2)+(U-1)*F(x)) for x in p) for p in c['vertices']] for c in cover['cells']]
    branch=d.get('branch');branch_start=None
    if branch:
        assert branch['owner'] in mask and branch['axis'] in (0,1) and branch['keep'] in ('le','ge')
        assert F(branch['bound_field'])==B*(U/2+F(branch['bound_centered_unit']))
        branch_start=d['resume']['completed_rounds']+1
        assert 1<=branch_start<=len(d['rounds'])+1
    groups=groups_parse(seed['owned_points']);seedchecks=0
    for owner in mask:
        for p in groups[owner]:
            # Keep the independent seed verifier's Fraction arithmetic pure;
            # some Python/GMP mixed-type paths construct nonstandard internals.
            ans=wall.check_point([tuple(wall.F(str(x/B)) for x in p) for p in worlds[owner]],tuple(wall.F(str(x/B)) for x in p))
            assert ans['passed'];seedchecks+=1
    guards=json.loads(GUARDS.read_text());assert d['local_guard_source_sha256']==sha(GUARDS)
    guard=next((g for g in guards['guards'] if g['mask']==mask),None);roles={r['cell']:r for r in guard['roles']} if guard else {}
    checks=[];previous={};derived=0;angles_deleted=0;guard_rounds=[]
    for ridx,rnd in enumerate(d['rounds'],1):
        prior=groups_parse(rnd['prior_owned_points']);assert prior==groups and rnd['index']==ridx
        assert hashlib.sha256(canon(prior)).hexdigest()==rnd['prior_snapshot_sha256']
        new_previous={};allguard=True
        for cell in rnd['cells']:
            owner=cell['owner'];assert owner in mask and owner not in new_previous
            other={j:geo.gift_hull(prior[j]) for j in mask if j!=owner};kernel=parse(cell['common_core_kernel']);allstrips=[];vertices=[];retained=[];cursor=F(0);slabs=0
            for rowidx,row in enumerate(cell['rows']):
                lo,hi=map(F,row['interval']);assert lo==cursor and lo<hi<=1;cursor=hi
                domain=worlds[owner]
                if branch and ridx>=branch_start and owner==branch['owner']:
                    n=[F(0),F(0)];n[branch['axis']]=1 if branch['keep']=='le' else -1
                    bound=F(branch['bound_field'])*(1 if branch['keep']=='le' else -1)
                    domain=geo.intersection_polygon(geo.polygon_rows(geo.gift_hull(domain))+[(n[0],n[1],bound)])
                base_domain=domain
                restriction=row.get('domain_restriction',{'kind':'original_cell'})
                if ridx>1 and owner in previous and 'input_domain' in row:
                    oldidx=restriction['previous_row'];assert isinstance(oldidx,int) and 0<=oldidx<len(previous[owner]['rows'])
                    old=previous[owner]['rows'][oldidx];oldlo,oldhi=map(F,old['interval']);assert oldlo<=lo<hi<=oldhi
                    oldverts=[p for poly in old['residual_polygons'] for p in parse(poly)]
                    assert restriction['previous_round']==ridx-1
                    if not oldverts:
                        assert restriction['kind']=='previous_angle_excluded';domain=[]
                    else:
                        assert restriction['kind']=='previous_residual_outer_support'
                        lines=geo.polygon_rows(geo.gift_hull(base_domain))
                        for b in restriction['bounds']:
                            n=tuple(map(F,b['normal']));up=F(b['upper'])
                            assert all(n[0]*p[0]+n[1]*p[1]<=up for p in oldverts)
                            lines.append((n[0],n[1],up))
                        domain=geo.intersection_polygon(lines)
                if 'input_domain' in row:assert geo.gift_hull(parse(row['input_domain']))==geo.gift_hull(domain)
                residual=[parse(p) for p in row['residual_polygons']]
                if domain:
                    ans=geo.audit_residual_cover(domain,other,lo,hi,U,residual);assert ans['passed'],(ridx,owner,rowidx,ans)
                    if 'core_side' in ans:
                        expected_side=ans['core_side'];expected_t=ans['reference_half_angle']
                    else:
                        # A nonempty inherited domain may have empty legal-wall
                        # intersection after angle refinement. Its row is valid;
                        # still reconstruct and bind the recorded core metadata.
                        empty,_,expected_side,expected_t=geo.interval_geometry(domain,other,None,lo,hi,U)
                        assert not empty and not residual and ans['status']=='EMPTY_DOMAIN'
                    assert F(row['core_side'])==expected_side and F(row['reference_half_angle'])==expected_t
                    slabs+=ans['accepted_slabs']
                else:assert not residual
                v=[p for poly in residual for p in poly]
                if v:
                    vertices.extend(v);retained.append([lo,hi]);t=F(row['reference_half_angle']);c,s=geo.cs(t);core=F(row['core_side']);expected=[]
                    for n in ((c,s),(-s,c)):
                        vals=[n[0]*x+n[1]*y for x,y in v];low=max(vals)-core/2;up=min(vals)+core/2;allstrips.append((n,low,up));expected.append((n,low,up))
                    actual=[(tuple(map(F,x['normal'])),F(x['lower']),F(x['upper'])) for x in row['common_core_strips']]
                    assert actual==expected
                else:assert not row['common_core_strips'];angles_deleted+=1
            assert [[str(a),str(b)] for a,b in retained]==cell['retained_angle_intervals']
            if cell['complete']:
                assert cursor==1
                for p in kernel:
                    assert all(0<=x<=geo.L for x in p)
                    assert all(lo<=n[0]*p[0]+n[1]*p[1]<=hi for n,lo,hi in allstrips)
                if vertices and 'inner_grid_compression' in cell:
                    original=geo.gift_hull(prior[owner]+kernel)
                    if 'compression_source_points' in cell:assert original==parse(cell['compression_source_points'])
                    if 'compression_source_hull' in cell:assert original==parse(cell['compression_source_hull'])
                    newpoints=verify_convex_combinations(original,cell['inner_grid_compression'])
                else:newpoints=kernel if vertices else []
                for p in newpoints:
                    if p not in groups[owner]:groups[owner].append(p);derived+=1
                if vertices:
                    bounds=[[min(p[k] for p in vertices),max(p[k] for p in vertices)] for k in (0,1)]
                    assert bounds==[list(map(F,b)) for b in cell['center_bounds_field']]
                if cell['inside_local_guard']:
                    assert guard
                    role=roles[owner]
                    assert all(any(F(a)<=lo and hi<=F(b) for a,b in role['half_angle_intervals']) for lo,hi in retained)
                    assert all(all(F(b[0])<=v/B-U/2<=F(b[1]) for v,b in zip(p,role['centered_box'])) for p in vertices)
            else:assert not kernel
            allguard &= bool(cell['complete'] and cell['inside_local_guard'])
            checks.append(dict(round=ridx,owner=owner,rows=len(cell['rows']),complete=cell['complete'],arrangement_slabs=slabs,retained_angle_rows=len(retained),kernel_vertices=len(kernel)))
            new_previous[owner]=cell
            print(json.dumps(checks[-1]),flush=True)
        guard_rounds.append(allguard and set(new_previous)==set(mask));previous=new_previous
    assert groups==groups_parse(d['owned_points'])
    contradiction=d['contradiction']
    if contradiction:
        if contradiction['kind']=='owned_hulls_intersect':
            i,j=contradiction['owners'];assert i in mask and j in mask and i!=j
            assert hull_intersects([tuple(wall.F(str(x)) for x in p) for p in groups[i]], [tuple(wall.F(str(x)) for x in p) for p in groups[j]])
        elif contradiction['kind']=='all_parent_poses_forbidden':
            cc=next(c for c in d['rounds'][contradiction['round']-1]['cells'] if c['owner']==contradiction['owner'])
            assert cc['complete'] and all(not r['residual_polygons'] for r in cc['rows'])
        else:raise AssertionError('Unsupported contradiction')
    assert not d['local_guard_geometry_captured'] or guard_rounds[-1]
    out=dict(status='PASS_INDEPENDENT_RESIDUAL_KERNEL_AUDIT',source_sha256=sha(args.receipt),seed_sha256=sha(args.seed),cover_sha256=sha(COVER),
             dependencies={p.name:sha(p) for p in (Path(__file__),Path(geo.__file__),Path(wall.__file__),Path(rational.__file__),WORK/'geometry/audit_kernel_survivor.py')},mask_index=d['mask_index'],
             rational_backend=rational.BACKEND,rational_backend_version=rational.VERSION,
             rational_binary_sha256=sha(rational.BINARY) if rational.BINARY else None,
             unconditional_seed_points_checked=seedchecks,derived_owned_points=derived,angle_rows_checked=sum(x['rows'] for x in checks),
             exact_arrangement_slabs=sum(x['arrangement_slabs'] for x in checks),excluded_angle_rows_across_rounds=angles_deleted,cells=checks,
             local_guard_geometry_captured=bool(d['local_guard_geometry_captured']),branch_condition=branch,
             branch_exclusion_proved=bool(contradiction) and bool(branch),mask_exclusion_proved=bool(contradiction) and not branch,global_optimality_proved=False,
             seconds=time.monotonic()-begin)
    args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='cells'},indent=2))
if __name__=='__main__':main()
