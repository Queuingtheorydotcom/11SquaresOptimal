"""Discharge exact D4 branch antecedents after independent geometric replay.

The finite support proof and source-complete 1931 exclusion baseline are named
premises. The geometry audit must be newly executed; this adapter binds it and
checks necessity of every added constraint, not a replacement for that replay.
"""
if not __debug__:
    raise SystemExit("This exact proof consumer requires assertions; -O and -OO are refused.")

from pathlib import Path
from fractions import Fraction as F
import argparse,hashlib,json,sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'phase3'
sys.path.insert(0,str(HERE.parent/'global-math'))
import overlay_field_halfplanes_v2 as necessity

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
GEOMETRY_CHECKER_SHA256='95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c'
GEOMETRY_DEPENDENCY_PATHS={
    'audit_capture_v9.py':'work/phase3/hull/audit_capture_v9.py',
    'arrangement_audit_v2.py':'work/phase3/hull/arrangement_audit_v2.py',
    'rational.py':'work/phase3/hull/rational.py',
    'validate_collision_kernel_v3.py':'work/phase3/collision/validate_collision_kernel_v3.py',
    'own_hull_constraints.py':'work/phase3/hull/own_hull_constraints.py',
    'audit_residual_kernel.py':'work/phase3/hull/audit_residual_kernel.py',
    'arrangement_audit.py':'work/phase3/hull/arrangement_audit.py',
    'audit_wall_kernel.py':'work/geometry/audit_wall_kernel.py',
    'audit_kernel_survivor.py':'work/geometry/audit_kernel_survivor.py',
    'audit_center_cover.py':'current/research/optimality/audit/audit_center_cover.py',
}

def referenced_path(ref,owner):
    path=Path(ref)
    return (path if path.is_absolute() else owner.parent/path).resolve()

def checked_ancestry(source_path,audit,seed_path,seed_hash,U,B,mask,index):
    chain=[];seen=set();path=source_path.resolve()
    while True:
        fingerprint=sha(path)
        assert fingerprint not in seen,'Cyclic/repeated source ancestry'
        seen.add(fingerprint);node=read(path)
        assert node['schema']=='exact_generic_owned_hull_v1' and node['guard_source'] is None
        assert node['mask']==mask and node['mask_index']==index
        assert F(node['U'])==U and F(node['B'])==B
        assert referenced_path(node['source']['path'],path)==seed_path
        assert node['source']['sha256']==seed_hash
        chain.append((path,fingerprint,node))
        if node['parent'] is None:break
        parent=referenced_path(node['parent']['path'],path)
        assert sha(parent)==node['parent']['sha256'],'Parent reference drift'
        path=parent
    chain.reverse()
    assert len(audit['nodes'])==len(chain),'Audit ancestry inventory mismatch'
    inherited=[]
    for record,(path,fingerprint,node) in zip(audit['nodes'],chain):
        assert Path(record['path']).resolve()==path and record['sha256']==fingerprint
        assert record['node']==node['node_id']
        assert record['constraints']==node['constraints']
        assert record['branch_exclusion_proved']==bool(node['contradiction'])
        assert record['inside_local_guard'] is False
        assert all(c in node['constraints'] for c in inherited),'Dropped inherited antecedent'
        for c in node['constraints']:
            assert set(c)=={'owner','normal','upper_field'},'Unsupported ancestry antecedent'
            assert type(c['owner']) is int and c['owner'] in mask and len(c['normal'])==2
            assert any(map(F,c['normal']))
        inherited=node['constraints']
    assert inherited==audit['constraints']
    return chain


def validate(source_path,audit_path):
    source_path=Path(source_path).resolve();audit_path=Path(audit_path).resolve()
    d=read(source_path);r=read(audit_path)
    assert r['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
    assert r['branch_exclusion_proved'] and not r['inside_local_guard']
    assert r['source_sha256']==sha(source_path)
    assert d['terminal'] and d['contradiction'] and d['guard_source'] is None
    assert r['constraints']==d['constraints']
    assert r['mask_index']==d['mask_index'] and r['mask']==d['mask']
    assert r['bootstrap']['kind']=='independently_verified_wall_seed'
    assert r['root_audit_sha256'] is None
    seed_path=referenced_path(d['source']['path'],source_path);seed=read(seed_path)
    assert sha(seed_path)==r['root_sha256']==d['source']['sha256']
    assert seed['schema']=='generic_wall_seed_v1'
    assert seed['mask']==d['mask'] and seed['mask_index']==d['mask_index']
    cover_path=ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
    cover=read(cover_path)
    assert r['cover_sha256']==sha(cover_path)
    assert d['mask']==cover['canonical_eleven_cell_subsets'][d['mask_index']]
    U=F(387708359002281417731,10**20);L=F(191,50);B=L/U
    assert F(d['U'])==F(r['parent_Uplus'])==F(seed['U'])==U
    assert F(d['B'])==F(r['parent_side'])==F(seed['B'])==B
    assert r['required_antecedent_mask']==d['mask']
    assert r['final_state_sha256']==digest(d['final_state'])
    assert r['bootstrap']['full_angle_domain']==['0','1']
    assert r['bootstrap']['angle_rows']==len(d['mask'])*seed['bins']
    assert r['bootstrap']['seed_vertices']==len(r['seed_ownership_checks'])
    assert all(check['passed'] is True for check in r['seed_ownership_checks'])
    ancestry=checked_ancestry(source_path,r,seed_path,sha(seed_path),U,B,d['mask'],d['mask_index'])
    assert set(r['dependencies'])==set(GEOMETRY_DEPENDENCY_PATHS),'Incomplete audit dependency inventory'
    assert r['dependencies']['audit_capture_v9.py']==GEOMETRY_CHECKER_SHA256
    for name,relpath in GEOMETRY_DEPENDENCY_PATHS.items():
        assert r['dependencies'][name]==sha(ROOT/relpath),(name,'changed dependency')
    conditions=[]
    for c in d['constraints']:
        assert set(c)=={'owner','normal','upper_field'},'Only necessary closed center halfplanes allowed'
        assert type(c['owner']) is int and len(c['normal'])==2
        conditions.append((c['owner'],tuple(map(F,c['normal'])),F(c['upper_field'])))
    necessity.checked_context.cache_clear()
    hulls,support,geometry,_,_=necessity.checked_context()
    assert F(hulls['U'])==U
    assert support['checker_sha256']==sha(HERE.parent/'global-math/audit_all_overlay_support.py')
    assert geometry['checker_sha256']==sha(HERE.parent/'global-math/audit_overlay_geometry.py')
    necessity.verify_constraints(d['mask_index'],conditions,L)
    baseline=ROOT/'work/phase3/audit/overall-union-snapshot-bc3563a0c995.json'
    assert sha(baseline)=='bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545'
    assert d['mask_index'] in read(baseline)['remaining_canonical_mask_indices']
    return dict(status='PASS_D4_ANTECEDENTS_DISCHARGED_EXACT_MASK_EXCLUSION',
        source=str(source_path.resolve()),source_sha256=sha(source_path),
        geometric_audit=str(audit_path.resolve()),geometric_audit_sha256=sha(audit_path),
        checker_sha256=sha(__file__),necessity_checker_sha256=sha(necessity.__file__),
        source_hulls_sha256=sha(necessity.HULLS),
        support_replay_sha256=sha(necessity.HULLS.with_name('independent-replay.json')),
        geometry_replay_sha256=sha(HERE.parent/'global-math/overlay-geometry-independent-replay.json'),
        baseline_sha256=sha(baseline),mask_index=d['mask_index'],mask=d['mask'],
        parent_Uplus=str(U),parent_side=str(B),necessary_halfplanes_checked=len(conditions),
        checked_ancestry=[dict(path=str(p),sha256=h) for p,h,n in ancestry],
        geometry_checker_sha256=GEOMETRY_CHECKER_SHA256,
        mask_exclusion_proved=True,global_optimality_proved=False,
        scope='Unconditional case exclusion conditional on the explicitly named, source-complete1931 baseline; all added center assumptions are independently proved necessary.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('audit',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=validate(a.source,a.audit)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
