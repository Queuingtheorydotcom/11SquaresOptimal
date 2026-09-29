"""Bind fresh independent exclusions to the fixed source-complete baseline.

This is an inventory/union checker, not a substitute for the geometric replay.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import hashlib
import json
import subprocess
import sys

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
inventory_dir=HERE.parent/'audit-lower-bound'
inventory_pins={
    'strict_generic_inventory.py':'7df54d904bb5d0cc609a4765eeafc3fb57922bcb3a4b210082df9fda36266530',
    'strict_tree_inventory.py':'ed615c62af1e9be3287e0d41dbec849dcc72a281ed7a9f5f1b567156060832cb',
    'strict-inventory-pins.json':'8a46589d35e3bbd1efce02b2a196db5ddb636a85259bf7f30d6b31daa65b01f8',
}
for name,h in inventory_pins.items():assert sha(inventory_dir/name)==h
sys.path.insert(0,str(inventory_dir))
from strict_generic_inventory import validate as validate_generic
from strict_tree_inventory import validate as validate_tree
entries=[]
audit_paths=sorted(HERE.glob('mask*-independent.json'))
audit_paths+=sorted((HERE.parent/'endpoint-audit').glob('mask*-final-independent-audit.json'))
for audit_path in audit_paths:
    r=read(audit_path)
    if not r.get('mask_exclusion_proved'):continue
    proved=validate_generic(audit_path)
    cases=proved['cases']
    entries.append(dict(mask=proved['mask_index'],source=proved['source'],source_sha256=proved['source_sha256'],
        audit=proved['audit'],audit_sha256=proved['audit_sha256'],
        proof_kind=proved['dependency_profile'],ancestry_nodes=proved['nodes'],new_cases=sorted(cases-union)))
    union|=cases
tree_audit=HERE.parent/'endpoint-audit/mask1383-final-independent-tree-audit.json'
if tree_audit.exists():
    proved=validate_tree(tree_audit)
    cases=proved['cases']
    entries.append(dict(mask=proved['mask_index'],source=proved['source'],source_sha256=proved['source_sha256'],
        audit=proved['audit'],audit_sha256=proved['audit_sha256'],
        proof_kind=proved['dependency_profile'],ancestry_nodes=proved['nodes'],
        checked_leaves=proved['leaves'],new_cases=sorted(cases-union)))
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
fresh_baseline=HERE.parent/'PHASE3_FRESH_REPLAY_RESULT.json'
fresh_binding=None
if fresh_baseline.exists():
    subprocess.run([sys.executable,str(HERE.parent/'aggregate_phase3_fresh.py')],
                   stdout=subprocess.DEVNULL,check=True)
    fresh=read(fresh_baseline)
    assert fresh['status']=='PASS_FRESH_INDEPENDENT_1931_CASE_UNION'
    assert fresh['authoritative_snapshot_sha256']==sha(baseline_path)
    assert fresh['excluded_canonical_mask_indices']==baseline['excluded_canonical_mask_indices']
    fresh_binding=dict(path=str(fresh_baseline),sha256=sha(fresh_baseline))
result=dict(status='PASS_IMMUTABLE_SAVED_BASELINE_PLUS_FRESH_GEOMETRY_EXTENSION',
    baseline_path=str(baseline_path),baseline_sha256=sha(baseline_path),baseline_excluded=1931,
    fresh_baseline_geometry_replay_completed=bool(fresh_binding),fresh_baseline_replay=fresh_binding,
    inventory_checkers=inventory_pins,
    extension_entries=entries,
    excluded_canonical_mask_indices=sorted(union),excluded_canonical_cases=len(union),
    remaining_canonical_mask_indices=sorted(set(range(2184))-union),remaining_canonical_cases=2184-len(union),
    global_optimality_proved=False)
(HERE/'extended-union.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if not k.endswith('_indices')},indent=2))
