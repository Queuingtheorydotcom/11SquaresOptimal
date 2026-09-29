"""Compare the existing inventory loop with the proposed strict validator.

Only receipt copies in this audit directory are mutated. Original proof
objects and root-owned consumers are read-only. No geometric claim is made.
"""
import ast
from copy import deepcopy
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import hashlib
import json
import time

from strict_generic_inventory import Validator, sha

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
ROOT = RESEARCH / 'phase3'
FRONTIER = RESEARCH / 'frontier'
MUTATIONS = HERE / 'inventory-mutations'
MUTATIONS.mkdir(exist_ok=True)
snapshot = HERE / 'legacy-extend_union-reviewed.py'
if not snapshot.exists():
    snapshot.write_text((FRONTIER / 'extend_union.py').read_text())
source = snapshot.read_text()
legacy_hash = hashlib.sha256(source.encode()).hexdigest()
tree = ast.parse(source)
loop = next(n for n in tree.body if isinstance(n, ast.For) and
            isinstance(n.target, ast.Name) and n.target.id == 'audit_path')
legacy_code = compile(ast.Module(body=[loop], type_ignores=[]), 'legacy-inventory-loop', 'exec')
baseline_path = ROOT / 'work/phase3/audit/overall-union-snapshot-bc3563a0c995.json'
baseline = json.loads(baseline_path.read_text())
cover_path = ROOT / 'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
turn = lambda J: tuple(sorted(15-i for i in J))
canonical = sorted({min(J, turn(J)) for J in combinations(range(16), 11)})


def legacy_accepts(path):
    env = dict(audit_paths=[path], F=F, Path=Path, sha=sha,
               read=lambda p: json.loads(Path(p).read_text()),
               baseline=baseline, cover_path=cover_path, canonical=canonical, turn=turn,
               union=set(baseline['excluded_canonical_mask_indices']), entries=[],
               roots=[ROOT/'work/phase3/hull', ROOT/'work/phase3/collision',
                      ROOT/'work/phase2/hull', ROOT/'work/geometry',
                      ROOT/'current/research/optimality/audit'])
    try:
        exec(legacy_code, env)
        return bool(env['entries']), None
    except Exception as exc:
        return False, type(exc).__name__ + ': ' + str(exc)


def strict_accepts(path):
    try:
        Validator().validate(path)
        return True, None
    except Exception as exc:
        return False, type(exc).__name__ + ': ' + str(exc)


def main():
    started = time.monotonic()
    direct_path = FRONTIER / 'mask2174-independent.json'
    cached_path = RESEARCH / 'endpoint-audit/mask1839-final-independent-audit.json'
    direct = json.loads(direct_path.read_text())
    cached = json.loads(cached_path.read_text())
    fixtures = []

    def case(name, original, change):
        r = deepcopy(original)
        change(r)
        fixtures.append((name, r))

    case('drop_all_dependencies', direct, lambda r: r.update(dependencies={}))
    case('drop_own_hull_dependency', direct, lambda r: r['dependencies'].pop('own_hull_constraints.py'))
    case('1839_keep_only_terminal_node', cached, lambda r: r.update(nodes=r['nodes'][-1:]))
    case('1839_drop_one_ancestor', cached, lambda r: r['nodes'].pop(1))
    case('1839_duplicate_ancestor', cached, lambda r: r['nodes'].insert(1, deepcopy(r['nodes'][0])))
    case('1839_reorder_ancestors', cached, lambda r: r['nodes'].__setitem__(slice(0, 2), r['nodes'][1::-1]))
    case('1839_remove_premise_audits', cached, lambda r: r.pop('premise_audits'))
    case('1839_remove_native_adapter', cached, lambda r: r.pop('native_portability_adapter'))
    case('1839_orphan_cached_node', cached, lambda r: r['nodes'][0].update(cached_from_audit_sha256='0'*64))
    case('wrong_native_binary', direct, lambda r: r.update(rational_binary_sha256='0'*64))
    case('wrong_native_version', direct, lambda r: r.update(rational_backend_version='0.0.0'))
    case('wrong_exact_parent_side', direct, lambda r: r.update(parent_side='1'))
    case('wrong_root_audit_premise', direct, lambda r: r.update(root_audit_sha256='0'*64))
    case('missing_seed_ownership_checks', direct, lambda r: r.update(seed_ownership_checks=[]))
    case('wrong_final_state_digest', direct, lambda r: r.update(final_state_sha256='0'*64))
    case('wrong_node_conclusion', direct, lambda r: r['nodes'][-1].update(branch_exclusion_proved=False))
    case('truncated_node_row_count', direct, lambda r: r['nodes'][-1].update(rows=1))
    case('invented_branch_in_node_record', direct, lambda r: r['nodes'][-1].update(constraints=[{'owner':r['mask'][0], 'normal':[1,0], 'upper_field':'0'}]))
    # This changes a nested receipt as well as all references to its bytes.
    # Merely validating the immediate premise hash therefore cannot reject it.
    premise_path = RESEARCH / 'endpoint-audit/mask1839-self-hull-first-independent-audit.json'
    bad_premise = json.loads(premise_path.read_text())
    bad_premise['nodes'] = bad_premise['nodes'][-1:]
    bad_path = MUTATIONS / 'nested-truncated-premise.json'
    bad_path.write_text(json.dumps(bad_premise, indent=2) + '\n')
    bad_hash = sha(bad_path)
    def replace_premise(r):
        old = r['premise_audits'][0]['sha256']
        r['premise_audits'][0].update(path=str(bad_path), sha256=bad_hash)
        for node in r['nodes']:
            if node.get('cached_from_audit_sha256') == old:
                node['cached_from_audit_sha256'] = bad_hash
    case('1839_truncated_nested_premise_with_updated_hash', cached, replace_premise)
    controls = []
    for name, r in fixtures:
        path = MUTATIONS / (name + '.json')
        path.write_text(json.dumps(r, indent=2) + '\n')
        old, old_reason = legacy_accepts(path)
        new, new_reason = strict_accepts(path)
        assert old and not new, (name, old, old_reason, new, new_reason)
        controls.append(dict(name=name, legacy_accepted=old, strict_accepted=new,
                             strict_rejection=new_reason, fixture_sha256=sha(path)))
        print(name, 'rejected', flush=True)
    authentic = []
    for path in (direct_path, cached_path):
        old, _ = legacy_accepts(path)
        new, reason = strict_accepts(path)
        assert old and new, (path, reason)
        authentic.append(dict(path=str(path), sha256=sha(path), accepted=True))
    result = dict(status='PASS_STRICT_INVENTORY_MUTATION_CONTROLS',
                  legacy_consumer_sha256=legacy_hash,
                  proposed_validator_sha256=sha(HERE/'strict_generic_inventory.py'),
                  authentic_receipts=authentic, controls=controls,
                  mutations_rejected=len(controls), seconds=time.monotonic()-started,
                  scope='Inventory binding tests only. Original geometry and proof files were not modified.')
    (HERE/'inventory-mutation-controls.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'controls'}, indent=2))


if __name__ == '__main__':
    main()
