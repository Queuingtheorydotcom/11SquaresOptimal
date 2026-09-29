"""Discharge exact D4 branch antecedents after independent geometric replay.

The finite support proof and source-complete 1931 exclusion baseline are named
premises. The geometry audit must be newly executed; this adapter binds it and
checks necessity of every added constraint, not a replacement for that replay.
"""
from pathlib import Path
from fractions import Fraction as F
import argparse,hashlib,json,sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'phase3'
sys.path.insert(0,str(HERE.parent/'global-math'))
import overlay_field_halfplanes_v2 as necessity

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())

def validate(source_path,audit_path):
    d=read(source_path);r=read(audit_path)
    assert r['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
    assert r['branch_exclusion_proved'] and not r['inside_local_guard']
    assert r['source_sha256']==sha(source_path)
    assert d['terminal'] and d['contradiction'] and d['guard_source'] is None
    assert r['constraints']==d['constraints']
    assert r['mask_index']==d['mask_index'] and r['mask']==d['mask']
    assert r['bootstrap']['kind']=='independently_verified_wall_seed'
    assert r['root_audit_sha256'] is None
    seed_path=Path(d['source']['path']);seed=read(seed_path)
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
    assert r['nodes'] and r['nodes'][-1]['sha256']==sha(source_path)
    for node in r['nodes']:
        assert sha(node['path'])==node['sha256']
    dep_roots=[ROOT/'work/phase3/hull',ROOT/'work/phase3/collision',ROOT/'work/phase2/hull',
               ROOT/'work/geometry',ROOT/'current/research/optimality/audit']
    assert r['dependencies']['audit_capture_v9.py']==sha(ROOT/'work/phase3/hull/audit_capture_v9.py')
    for name,h in r['dependencies'].items():
        assert any((p/name).is_file() and sha(p/name)==h for p in dep_roots),(name,'changed dependency')
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
        mask_exclusion_proved=True,global_optimality_proved=False,
        scope='Unconditional case exclusion conditional on the explicitly named, source-complete1931 baseline; all added center assumptions are independently proved necessary.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('audit',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=validate(a.source,a.audit)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
