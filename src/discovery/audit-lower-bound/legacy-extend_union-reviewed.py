"""Bind fresh independent exclusions to the fixed source-complete baseline.

This is an inventory/union checker, not a substitute for the geometric replay.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import hashlib
import json

if not __debug__:raise SystemExit('Assertions must remain enabled.')

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'phase3'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
baseline_path=ROOT/'work/phase3/audit/overall-union-snapshot-bc3563a0c995.json'
assert sha(baseline_path)=='bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545'
baseline=read(baseline_path)
cover_path=ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
cover=read(cover_path)
assert sha(cover_path)==baseline['cover_sha256']
turn=lambda J:tuple(sorted(15-i for i in J))
canonical=sorted({min(J,turn(J)) for J in combinations(range(16),11)})
assert list(map(list,canonical))==cover['canonical_eleven_cell_subsets']
union=set(baseline['excluded_canonical_mask_indices'])
roots=[ROOT/'work/phase3/hull',ROOT/'work/phase3/collision',ROOT/'work/phase2/hull',
       ROOT/'work/geometry',ROOT/'current/research/optimality/audit']
entries=[]
audit_paths=sorted(HERE.glob('mask*-independent.json'))
extra=HERE.parent/'endpoint-audit/mask1839-final-independent-audit.json'
if extra.exists():audit_paths.append(extra)
for audit_path in audit_paths:
    r=read(audit_path)
    if not r.get('mask_exclusion_proved'):continue
    assert r['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
    assert r['branch_exclusion_proved'] and r['constraints']==[]
    assert F(r['parent_Uplus'])==F(baseline['parent_Uplus'])
    assert r['cover_sha256']==sha(cover_path)
    assert r['bootstrap']['kind']=='independently_verified_wall_seed'
    for name,h in r['dependencies'].items():
        assert any((p/name).is_file() and sha(p/name)==h for p in roots),(name,'changed checker')
    for premise in r.get('premise_audits',[]):
        assert sha(premise['path'])==premise['sha256']
    if 'native_portability_adapter' in r:
        adapter=r['native_portability_adapter']
        assert sha(adapter['path'])==adapter['sha256']
    for node in r['nodes']:
        assert sha(node['path'])==node['sha256']
    source_path=Path(r['nodes'][-1]['path']);source=read(source_path)
    assert sha(source_path)==r['source_sha256']
    seed=Path(source['source']['path']);assert sha(seed)==r['root_sha256']
    assert source['constraints']==[] and source['contradiction'] and source['terminal']
    assert source['mask']==r['mask']==read(seed)['mask']
    support=set(r['mask']);assert support<=set(canonical[r['mask_index']])
    cases={i for i,J in enumerate(canonical) if support<=set(J) or support<=set(turn(J))}
    assert sorted(cases)==r['transferred_canonical_mask_indices']
    entries.append(dict(mask=r['mask_index'],source=str(source_path),source_sha256=sha(source_path),
        audit=str(audit_path),audit_sha256=sha(audit_path),new_cases=sorted(cases-union)))
    union|=cases
for proof_path in sorted(HERE.glob('mask*-overlay-exclusion.json')):
    from audit_overlay_exclusion import validate
    proof=read(proof_path)
    assert proof['checker_sha256']==sha(HERE/'audit_overlay_exclusion.py')=='f3eefa77e6f02b977d6bfe38e5bc7e1e32fd6e355de7d226c803291b9a6ea5e1'
    assert proof['necessity_checker_sha256']=='ee942f83af21aa2ab58b080b37cc95d5064d37b0458cfd2b93c2be8ab7ba1c74'
    assert proof==validate(Path(proof['source']),Path(proof['geometric_audit']))
    cases={proof['mask_index']}
    entries.append(dict(mask=proof['mask_index'],source=proof['source'],source_sha256=proof['source_sha256'],
        audit=str(proof_path),audit_sha256=sha(proof_path),proof_kind='necessary_D4_cuts_and_independent_geometry',
        new_cases=sorted(cases-union)))
    union|=cases
assert not union.intersection([438,999,1462,1659])
result=dict(status='PASS_IMMUTABLE_SAVED_BASELINE_PLUS_FRESH_GEOMETRY_EXTENSION',
    baseline_path=str(baseline_path),baseline_sha256=sha(baseline_path),baseline_excluded=1931,
    fresh_baseline_geometry_replay_completed=False,extension_entries=entries,
    excluded_canonical_mask_indices=sorted(union),excluded_canonical_cases=len(union),
    remaining_canonical_mask_indices=sorted(set(range(2184))-union),remaining_canonical_cases=2184-len(union),
    global_optimality_proved=False)
(HERE/'extended-union.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if not k.endswith('_indices')},indent=2))
