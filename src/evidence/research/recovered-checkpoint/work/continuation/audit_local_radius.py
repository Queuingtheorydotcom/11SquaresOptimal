"""Independent exact acceptance of the retained local-radius inverse witnesses.

No floating inverses are computed. Polynomial values use power-basis interval
bounds, and inverse residuals use plain Python integer matrix arithmetic.
The previously independent tangent/stress replay is bound by input hashes.
"""
from fractions import Fraction as Q
from hashlib import sha256
from pathlib import Path
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'research/jlevy/packing'
sys.path[:0] = [str(SOURCE), str(SOURCE / 'src')]
from cases.trump11 import isolation_radius as ir
from cases.trump11 import packing


def require(test, message):
    if not test:
        raise ValueError(message)


def polynomial(coefficients, point):
    return sum(Q(c) * point ** i for i, c in enumerate(coefficients))


def main():
    start = time.monotonic()
    path = ROOT / 'research/classical/trump-local-conservative-radius.json'
    raw = path.read_bytes()
    proposed = json.loads(raw)
    prior_path = ROOT / 'research/classical/trump-local-independent-replay.json'
    prior = json.loads(prior_path.read_text())
    require(prior['status'] == 'PASS_INDEPENDENT_LOCAL_ALGEBRA_CHECKS', 'Missing prior algebra replay')
    for name, expected in proposed['source_hashes'].items():
        require(sha256((SOURCE / name).read_bytes()).hexdigest() == expected, 'Changed geometry source')
    for name, expected in prior['source_sha256'].items():
        require(proposed['source_hashes'][name] == expected, 'Prior replay has different geometry')
    require(proposed['tangent_record_sha256'] == prior['record_sha256'] ==
            sha256(ir.RECORD.read_bytes()).hexdigest(), 'Tangent/stress record mismatch')
    witness = ir.load_witness()
    record = ir.load_record()
    lo, hi = map(Q, proposed['root_interval'])
    original_lo, original_hi = map(Q, packing.U_INTERVAL)
    polynomial_coefficients = list(reversed(packing.U_MIN_POLY))
    require(original_lo <= lo < hi <= original_hi, 'Root interval left its isolating bracket')
    require(polynomial(polynomial_coefficients, lo) * polynomial(polynomial_coefficients, hi) < 0,
            'Root interval does not retain the isolated root')
    # The source field constructor proves that the original bracket has one
    # root. The independent earlier replay checks this with SymPy as well.
    powers = [(lo ** i, hi ** i) for i in range(len(polynomial_coefficients) - 1)]
    cache = {}

    def interval(value):
        coefficients = tuple(value.coeffs)
        if coefficients not in cache:
            lower = upper = Q(0)
            for c, (left, right) in zip(coefficients, powers):
                first, second = c * left, c * right
                lower += min(first, second)
                upper += max(first, second)
            cache[coefficients] = (lower, upper)
        return cache[coefficients]

    require(interval(witness.side)[1] < 4, 'Side not below four')
    box, curvature, lipschitz = Q(1, 64), Q(16), Q(12)
    require(Q(3, 2) ** 2 > 2, 'Invalid rational sqrt(2) bound')
    reach = Q(3, 2) * (4 + 2 * box)
    require(reach + 6 * Q(3, 2) < curvature, 'Hessian coefficient sum exceeds K')
    require(reach + 3 * Q(3, 2) < lipschitz, 'Gradient coefficient sum exceeds L')
    functions = ir.elementary_functions(witness, box)
    require(len(functions) == 1936, 'Incomplete elementary-function inventory')
    identity = ir.identify_rows(witness, functions)
    gaps = []
    for function in functions:
        if function.value.is_zero():
            continue
        a, b = interval(function.value)
        require(a > 0 or b < 0, 'A nonzero gap lacks an interval sign proof')
        gaps.append(min(abs(a), abs(b)))
    gap = min(gaps)
    require(gap > Q(1, 250), 'Simple strict gap bound failed')
    receipts = {r['branch']: r for r in proposed['branches']}
    require(len(receipts) == len(proposed['branches']) == 128 and
            set(receipts) == set(range(128)), 'Incomplete inverse-witness list')
    results = []
    for branch in witness.branches:
        index = branch['branch']
        certificate = record['branches']['records'][index]['certificate']
        data = receipts[index]
        rows = branch['rows']
        pivots = certificate['pivot_rows']
        require(len(rows) == 42 and len(pivots) == len(set(pivots)) == 33, 'Wrong branch shape')
        DB, DJ = data['matrix_approximation_denominator'], data['inverse_denominator']
        require(type(DB) is int and type(DJ) is int and DB > 0 and DJ > 0, 'Invalid rational scale')
        integers = []
        for pivot in pivots:
            row = []
            for value in rows[pivot].coefficients:
                a, b = interval(value)
                q = round((a + b) * DB / 2)
                require(Q(q - 1, DB) <= a <= b <= Q(q + 1, DB), 'Minor entry enclosure failed')
                row.append(q)
            require(len(row) == 33, 'Wrong matrix width')
            integers.append(row)
        J = data['rounded_inverse']
        require(len(J) == 33 and all(len(row) == 33 and all(type(v) is int for v in row) for row in J),
                'Inverse proposal is not an integer33-square matrix')
        norm = Q(max(sum(abs(v) for v in row) for row in J), DJ)
        residual = 0
        for i in range(33):
            row_sum = 0
            for j in range(33):
                value = (DB * DJ if i == j else 0) - sum(J[i][k] * integers[k][j] for k in range(33))
                row_sum += abs(value)
            residual = max(residual, row_sum)
        error = Q(residual, DB * DJ) + norm * Q(33, DB)
        require(error < 1, 'Neumann criterion failed')
        H = norm / (1 - error)
        require(error == Q(data['residual_upper']) and H == Q(data['inverse_norm_upper']),
                'Independent integer residual differs from retained receipt')
        stress = ir.reconstruct_stress(rows, certificate, witness.field)
        minimum = min(interval(value)[0] for value in stress)
        total = sum(interval(value)[1] for value in stress)
        require(minimum > 0, 'Stress interval positivity failed')
        T = total / minimum
        require(H < 89 and T < 158, 'Simple uniform norm/stress bounds failed')
        results.append((H, T, 1 / (H * T), error))
    kappa = min(r[2] for r in results)
    radius = Q(proposed['radius_lower'])
    require(0 < radius <= min(box, gap / lipschitz, 2 * kappa / curvature),
            'Recorded open radius is not certified by independent enclosures')
    closed = Q(1, 120000)
    require(closed < min(box, Q(1, 3000), Q(1, 8 * 89 * 158)), 'Closed radius inequality failed')
    result = {
        'status': 'PASS_INDEPENDENT_QUANTITATIVE_RADIUS_AUDIT',
        'receipt_sha256': sha256(raw).hexdigest(),
        'generator_sha256': sha256((ROOT / 'research/classical/quantitative_trump_local.py').read_bytes()).hexdigest(),
        'proof_sha256': sha256((ROOT / 'research/classical/TRUMP-LOCAL-RADIUS.md').read_bytes()).hexdigest(),
        'prior_algebra_replay_sha256': sha256(prior_path.read_bytes()).hexdigest(),
        'branches': len(results), 'variables': 33, 'distinct_tied_gradients_used': identity['distinct_branch_rows'],
        'elementary_functions': len(functions), 'independent_power_basis_gap_lower': str(gap),
        'open_radius': str(radius), 'closed_radius': str(closed),
        'uniform_inverse_norm_strict_upper': 89, 'uniform_stress_ratio_strict_upper': 158,
        'maximum_residual_upper': str(max(r[3] for r in results)),
        'curvature_upper': str(curvature), 'lipschitz_upper': str(lipschitz),
        'acceptance': 'Plain integer inverse residuals and independent power-basis rational enclosures; no floating linear algebra.',
        'scope': 'Labelled anchored33-variable local fixed-side isolation only. Existing branch enumeration and prior independently replayed stress identities are retained; no global optimality.',
        'seconds': time.monotonic() - start,
    }
    destination = Path(__file__).with_name('local-radius-independent-audit.json')
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'independent_power_basis_gap_lower'}, indent=2))


if __name__ == '__main__':
    main()
