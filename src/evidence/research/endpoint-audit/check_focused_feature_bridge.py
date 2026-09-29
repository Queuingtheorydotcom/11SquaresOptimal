"""Third-source check of nonlinear contact features and branch matrices.

Uses the frozen exact witness/field, but builds the raw branch inventory
directly from elementary corner inequalities rather than tangent options.
Does not establish global capture or re-prove the analytic Taylor lemma.
"""
from pathlib import Path
from fractions import Fraction
from itertools import product
import hashlib
import json
import sys
import time

if not __debug__:
    raise SystemExit('Assertions must remain enabled.')

D = Path(__file__).resolve().parent
SOURCE = D.parent / 'recovered-checkpoint/research/jlevy/packing'
sys.path[:0] = [str(SOURCE), str(SOURCE/'src')]
from cases.trump11 import isolation_radius as ir


def scalar(v):
    return tuple((c.numerator, c.denominator) for c in v.coeffs)


def gradient(values):
    return tuple(scalar(v) for v in values)


def main():
    start = time.monotonic()
    w = ir.load_witness()
    functions = ir.elementary_functions(w, Fraction(1, 64))
    contacts = {c.pair: c for c in w.contacts}
    features = {}
    for f in functions:
        if f.kind == 'pair' and f.subject[:2] in contacts:
            features.setdefault(f.subject[:5], []).append(f)
    assert len(features) == 8*14
    choices = {pair: [] for pair in sorted(contacts)}
    active = inactive = 0
    actual_features = set()
    for key, fs in sorted(features.items()):
        assert len(fs) == 4
        assert {f.subject[-1] for f in fs} == set(range(4))
        signs = [f.value.sign() for f in fs]
        if min(signs) < 0:
            inactive += 1
            continue
        assert min(signs) == 0, 'A touching pair cannot have a strict feature.'
        active += 1
        actual_features.add(key)
        rowkeys = tuple(sorted({gradient(f.gradient) for f in fs if f.value.is_zero()}))
        pair = key[:2]
        alias = f'{pair[0]}-{pair[1]}/{key[2]}.{key[3]}/{key[4]}'
        options = [o for o in contacts[pair].options if alias in o.aliases]
        assert len(options) == 1
        assert rowkeys == tuple(sorted(gradient(r.coefficients) for r in options[0].rows))
        choices[pair].append(rowkeys)
    assert (active, inactive) == (24, 88)
    assert sum(len(o.aliases) for c in contacts.values() for o in c.options) == active

    # Rebuild all raw nonlinear selections directly from corner features.
    walls = tuple(sorted(gradient(f.gradient) for f in functions
                         if f.kind == 'wall' and f.value.is_zero()))
    assert walls == tuple(sorted(gradient(r.coefficients) for r in w.walls))
    raw = 0
    matrices = set()
    for selection in product(*(choices[pair] for pair in sorted(choices))):
        raw += 1
        matrices.add(tuple(sorted(walls + tuple(row for feature in selection for row in feature))))
    expected = {tuple(sorted(gradient(r.coefficients) for r in b['rows'])) for b in w.branches}
    assert raw == 512
    assert len(matrices) == 128 and matrices == expected

    frozen = D.parent/'global-math/focused1024-local-box-independent.json'
    receipt = json.loads(frozen.read_text())
    excluded = {tuple(r['subject'][:5]) for r in receipt['feature_stability']}
    assert excluded == set(features)-actual_features and len(excluded) == 88
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    out = {
        'status': 'PASS_THIRD_SOURCE_NONLINEAR_FEATURE_BRANCH_BRIDGE',
        'contact_pairs': 14, 'features': len(features),
        'active_features': active, 'inactive_features': inactive,
        'raw_nonlinear_selections': raw, 'distinct_derivative_matrices': len(matrices),
        'frozen_local_receipt_sha256': sha(frozen),
        'script_sha256': sha(__file__),
        'source_hashes': {str(p.relative_to(SOURCE)): sha(p) for p in (
            SOURCE/'cases/trump11/packing.py', SOURCE/'cases/trump11/isolation_radius.py',
            SOURCE/'cases/trump11/tangent_cones.py', SOURCE/'src/sqpack/field.py')},
        'scope': 'Exact feature-to-row and raw-branch completeness cross-check only; global capture is an external premise.',
        'seconds': time.monotonic()-start,
    }
    (D/'focused-feature-bridge-review.json').write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
