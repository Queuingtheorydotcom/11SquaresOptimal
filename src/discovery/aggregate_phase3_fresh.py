"""Assemble exactly the immutable 1931-case baseline after all fresh replays pass."""
if not __debug__:
    raise RuntimeError('Assertions must be enabled; optimized mode is not a proof replay')

from pathlib import Path
from itertools import combinations
from fractions import Fraction
import hashlib
import json
import gmpy2

BASE = Path(__file__).resolve().parent
ROOT = BASE / 'phase3'
MANIFEST_SHA256 = '53ef66cc8c1ee5e937fcd645a7bb831d96a65487b422d52cf67fb7d3c9b4ce61'
REFERENCE_PATH = 'work/phase3/audit/overall-union-snapshot-bc3563a0c995.json'
REFERENCE_SHA256 = 'bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545'
FIELD_REGISTRY_PATH = 'work/phase3/audit/field-union-snapshot-bb38353a08fa.json'
FIELD_REGISTRY_SHA256 = 'bb38353a08fade475096cf35cb4576dc5eec2d1ee005e9c4d8dcb11e462f976b'
COVER_PATH = 'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
COVER_SHA256 = 'df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
U = Fraction(387708359002281417731, 10**20)
L = Fraction(191, 50)
B = L / U
CANDIDATES = [438, 999, 1462, 1659]


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def turn(mask):
    return tuple(sorted(15-i for i in mask))


def validate_snapshot_binding(manifest):
    assert manifest['overall_union'] == REFERENCE_PATH
    assert manifest['overall_union_sha256'] == REFERENCE_SHA256
    assert manifest['field_registry'] == FIELD_REGISTRY_PATH
    assert manifest['field_registry_sha256'] == FIELD_REGISTRY_SHA256
    assert manifest['global_optimality_proved'] is False


def validate_inventory(recipes, records, count, key, digest_key):
    """Reject omitted, substituted, repeated, or reordered proof inventory entries."""
    assert len(recipes) == len(records) == count
    assert len({entry[key] for entry in recipes}) == count
    assert len({entry[digest_key] for entry in recipes}) == count
    assert len({entry[key] for entry in records}) == count
    assert len({entry['output'] for entry in records}) == count
    assert [entry['index'] for entry in records] == list(range(count))
    assert [entry[key] for entry in recipes] == [entry[key] for entry in records]
    for record in records:
        assert record['passed'] is True and record['exit_code'] == 0
        assert record['different_invariant_fields'] == []


def main():
    native_sha256 = sha(Path(gmpy2.gmpy2.__file__))
    assert sha(ROOT / 'PHASE3_REPLAY_MANIFEST.json') == MANIFEST_SHA256
    manifest = read(ROOT / 'PHASE3_REPLAY_MANIFEST.json')
    validate_snapshot_binding(manifest)
    assert sha(ROOT / REFERENCE_PATH) == REFERENCE_SHA256
    assert sha(ROOT / FIELD_REGISTRY_PATH) == FIELD_REGISTRY_SHA256
    reference = read(ROOT / REFERENCE_PATH)
    field_registry = read(ROOT / FIELD_REGISTRY_PATH)
    field = read(BASE / 'phase3-fresh-fields/RESULT.json')
    generic = read(BASE / 'phase3-fresh-generic/RESULT.json')
    assert field['status'] == 'PASS_FRESH_INDEPENDENT_FIELD_GEOMETRY'
    assert field['passed'] == field['total'] == 59
    assert generic['status'] == 'PASS_FRESH_GENERIC_GEOMETRY'
    assert generic['passed'] == generic['certificates'] == 34
    validate_inventory(manifest['field_recipes'], field['records'], 59, 'packet', 'packet_sha256')
    validate_inventory(manifest['generic_recipes'], generic['records'], 34, 'source', 'source_sha256')

    canonical = sorted({min(mask, turn(mask)) for mask in combinations(range(16), 11)})
    cover = read(ROOT / COVER_PATH)
    assert sha(ROOT / COVER_PATH) == COVER_SHA256
    assert len(canonical) == cover['canonical_eleven_cell_selections'] == 2184
    assert list(map(list, canonical)) == cover['canonical_eleven_cell_subsets']
    assert list(map(list, combinations(range(16), 11))) == cover['all_eleven_cell_subsets']
    assert cover['symmetry_cell_involution'] == list(range(15, -1, -1))
    assert U <= Fraction(cover['side_upper'])
    for registry in (reference, field_registry):
        assert registry['cover_sha256'] == COVER_SHA256
        assert Fraction(registry['parent_Uplus']) == U
        assert registry['canonical_cases'] == 2184
        assert registry['known_candidate_canonical_mask_indices'] == CANDIDATES
        assert registry['known_candidate_masks_survive'] is True
        assert registry['global_optimality_proved'] is False
    assert reference['excluded_canonical_cases'] == 1931
    assert reference['remaining_canonical_cases'] == 253
    assert reference['field_cases'] == field_registry['excluded_canonical_cases'] == 1904
    assert reference['generic_cases'] == 34 and reference['generic_cases_beyond_fields'] == 27

    union = set()
    rows = []
    for recipe, record in zip(manifest['field_recipes'], field['records'], strict=True):
        assert sha(record['output']) == record['fresh_sha256']
        audit = read(record['output'])
        packet = read(ROOT / recipe['packet'])
        assert audit['packet_sha256'] == sha(ROOT / recipe['packet']) == recipe['packet_sha256']
        assert sha(ROOT / recipe['independent_chain']) == recipe['chain_sha256']
        assert audit['audit_checker_sha256'] == recipe['chain_checker_sha256']
        assert audit['producer_receipt_sha256'] == sha(ROOT / recipe['producer_gate'])
        assert audit['fresh_replay_sha256'] == sha(ROOT / recipe['fresh_replay'])
        assert audit['status'] == 'PASS_INDEPENDENT_COMPLETE_WALL_MASK_CHAIN_AUDIT'
        assert audit['cover_sha256'] == packet['cover_sha256'] == COVER_SHA256
        assert Fraction(audit['parent_Uplus']) == Fraction(packet['parent_Uplus']) == U
        assert Fraction(audit['parent_side']) == B
        assert Fraction(packet['certificate']['L']) == L
        if 'fixed_homothety_B' in packet:
            assert Fraction(packet['fixed_homothety_B']) == B
        assert audit['canonical_mask_index'] == packet['mask_index']
        if 'mask_index' in recipe:
            assert packet['mask_index'] == recipe['mask_index']
        assert audit['mask'] == packet['mask'] == list(canonical[packet['mask_index']])
        assert audit['angular_parameter_domain'] == ['0', '1']
        assert audit['global_optimality_proved'] is False
        owners = set(packet.get('conditional_owner_support', packet['mask']))
        thresholds = packet['threshold_units']
        budget = packet['certificate']['budget_units']
        positive = {i for i in packet['mask'] if thresholds[i] > 0}
        assert audit['budget_units'] == budget
        assert audit['proved_positive_cells'] == sorted(positive)
        assert audit['proved_cell_thresholds'] == {str(i): thresholds[i] for i in positive}
        assert set(audit['conditional_owner_support']) == owners
        applies = lambda mask: owners <= set(mask) and sum(thresholds[i] for i in positive if i in mask) > budget
        cases = {i for i, mask in enumerate(canonical) if applies(mask) or applies(turn(mask))}
        assert sorted(cases) == audit['transferred_canonical_mask_indices']
        rows.append(dict(family='field', source=recipe['packet'], source_sha256=recipe['packet_sha256'], fresh_audit=record['output'], fresh_audit_sha256=record['fresh_sha256'], cases=sorted(cases)))
        union |= cases
    field_union = set(union)
    assert len(field_union) == 1904
    assert sorted(field_union) == field_registry['excluded_canonical_mask_indices']

    generic_union = set()
    for recipe, record in zip(manifest['generic_recipes'], generic['records'], strict=True):
        assert sha(record['output']) == record['fresh_sha256']
        audit = read(record['output'])
        packet = read(ROOT / recipe['source'])
        assert audit['source_sha256'] == sha(ROOT / recipe['source']) == recipe['source_sha256']
        assert audit['root_sha256'] == sha(ROOT / recipe['root']) == recipe['root_sha256']
        assert audit['root_audit_sha256'] == recipe['root_audit_sha256'] is None
        assert audit['dependencies'] == recipe['dependencies']
        assert audit['status'] == 'PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
        assert Fraction(audit['parent_Uplus']) == Fraction(packet['U']) == U
        assert Fraction(audit['parent_side']) == Fraction(packet['B']) == B
        assert audit['cover_sha256'] == COVER_SHA256
        assert audit['mask_index'] == packet['mask_index']
        assert audit['mask'] == packet['mask'] == list(canonical[packet['mask_index']])
        assert audit['rational_backend'] == 'gmp'
        assert audit['rational_backend_version'] == gmpy2.version()
        assert audit['rational_binary_sha256'] == native_sha256
        assert audit['mask_exclusion_proved'] is True and audit['branch_exclusion_proved'] is True
        assert audit['constraints'] == [] and audit['inside_local_guard'] is False
        assert audit['global_optimality_proved'] is False
        assert audit['bootstrap']['kind'] == 'independently_verified_wall_seed'
        assert audit['bootstrap']['full_angle_domain'] == ['0', '1']
        owners = set(audit['mask'])
        cases = {i for i, mask in enumerate(canonical) if owners <= set(mask) or owners <= set(turn(mask))}
        assert cases == {audit['mask_index']}
        rows.append(dict(family='generic', source=recipe['source'], source_sha256=recipe['source_sha256'], fresh_audit=record['output'], fresh_audit_sha256=record['fresh_sha256'], cases=sorted(cases)))
        generic_union |= cases
        union |= cases
    assert len(generic_union) == 34 and len(generic_union - field_union) == 27
    assert sorted(union) == reference['excluded_canonical_mask_indices']
    remaining = sorted(set(range(2184)) - union)
    assert len(union) == 1931 and len(remaining) == 253
    assert remaining == reference['remaining_canonical_mask_indices']
    assert not union.intersection(CANDIDATES)
    result = dict(status='PASS_FRESH_INDEPENDENT_1931_CASE_UNION', field_certificates=59, generic_certificates=34,
        field_cases=len(field_union), generic_cases=len(generic_union), excluded=len(union), remaining=len(remaining),
        excluded_canonical_mask_indices=sorted(union), remaining_canonical_mask_indices=remaining,
        authoritative_snapshot_path=REFERENCE_PATH, authoritative_snapshot_sha256=REFERENCE_SHA256,
        replay_manifest_sha256=MANIFEST_SHA256, cover_sha256=COVER_SHA256, parent_Uplus=str(U), parent_side=str(B),
        native_gmp_version=gmpy2.version(), native_gmp_binary_sha256=native_sha256,
        portability_wrapper_sha256=sha(BASE / 'phase3_portable_replay.py'),
        field_replay_driver_sha256=sha(BASE / 'replay_phase3_fields.py'),
        generic_replay_driver_sha256=sha(BASE / 'replay_phase3_generic.py'),
        field_replay_result_sha256=sha(BASE / 'phase3-fresh-fields/RESULT.json'),
        generic_replay_result_sha256=sha(BASE / 'phase3-fresh-generic/RESULT.json'),
        aggregation_checker_sha256=sha(__file__), global_optimality_proved=False,
        scope='Fresh independent geometry for all accepted field and generic proof objects in the immutable 1931-case baseline, plus exact union reconstruction. Producer discovery traces were not regenerated; source-distinct whole-domain geometry was reconstructed. Later new exclusions are outside this baseline receipt.',
        certificates=rows)
    (BASE / 'PHASE3_FRESH_REPLAY_RESULT.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('certificates', 'excluded_canonical_mask_indices', 'remaining_canonical_mask_indices')}, indent=2))


if __name__ == '__main__':
    main()
