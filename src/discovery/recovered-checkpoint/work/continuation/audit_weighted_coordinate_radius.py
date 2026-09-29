"""Independently accept the retained curvature-weighted local-coordinate duals.

Reads proposed rational coefficients; runs no LP, inverse, or floating algebra.
Uses plain-integer residuals and refined power-basis rational intervals rather
than the generating checker's Horner intervals. This retains the already
audited exact geometry and branch inventory, bound by their byte hashes.
"""
from fractions import Fraction as Q
from hashlib import sha256
from pathlib import Path
from math import isqrt
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'research/jlevy/packing'
sys.path[:0] = [str(SOURCE), str(SOURCE / 'src')]
from cases.trump11 import isolation_radius as ir
from cases.trump11 import packing
from cases.trump11 import tangent_cones as tc


def require(test, message):
    if not test:
        raise ValueError(message)


def polynomial(coefficients, point):
    return sum(Q(c) * point ** i for i, c in enumerate(coefficients))


def main():
    started = time.monotonic()
    proposal_path = ROOT / 'research/classical/trump-local-weighted-coordinate-radius.json'
    proposal_raw = proposal_path.read_bytes()
    proposed = json.loads(proposal_raw)
    baseline_path = ROOT / 'research/classical/trump-local-conservative-radius.json'
    baseline_raw = baseline_path.read_bytes()
    baseline = json.loads(baseline_raw)
    audit_path = Path(__file__).with_name('local-radius-independent-audit.json')
    audit = json.loads(audit_path.read_bytes())
    prior_path = ROOT / 'research/classical/trump-local-independent-replay.json'
    prior = json.loads(prior_path.read_bytes())
    require(proposed['status'] == 'PASS_FULL_EXACT_WEIGHTED_COORDINATE_RADIUS', 'Incomplete proposal')
    require(audit['status'] == 'PASS_INDEPENDENT_QUANTITATIVE_RADIUS_AUDIT', 'Missing baseline audit')
    require(proposed['input_sha256'] == audit['receipt_sha256'] == sha256(baseline_raw).hexdigest(),
            'Inherited baseline differs from independently checked baseline')
    require(audit['prior_algebra_replay_sha256'] == sha256(prior_path.read_bytes()).hexdigest(),
            'Previous algebra replay changed')
    for name, expected in baseline['source_hashes'].items():
        require(sha256((SOURCE / name).read_bytes()).hexdigest() == expected, 'Geometry source changed')
    for name, expected in prior['source_sha256'].items():
        require(baseline['source_hashes'][name] == expected, 'Prior branch source differs')
    require(baseline['tangent_record_sha256'] == prior['record_sha256'] ==
            sha256(ir.RECORD.read_bytes()).hexdigest(), 'Retained branch record changed')
    require(proposed['checker_sha256'] == sha256((ROOT / 'research/classical/weighted_coordinate_dual_trump_local.py').read_bytes()).hexdigest(),
            'Proposing checker changed')
    witness = ir.load_witness()
    lo, hi = map(Q, baseline['root_interval'])
    original_lo, original_hi = map(Q, packing.U_INTERVAL)
    modulus = list(reversed(packing.U_MIN_POLY))
    require(original_lo <= lo < hi <= original_hi, 'Root left original isolating bracket')
    sign_lo = polynomial(modulus, lo)
    require(sign_lo * polynomial(modulus, hi) < 0, 'Root bracket lacks a sign change')
    refinements = 0
    while hi - lo > Q(1, 10 ** 80):
        middle = (lo + hi) / 2
        sign_mid = polynomial(modulus, middle)
        require(sign_mid != 0, 'Unexpected rational root')
        if sign_lo * sign_mid < 0:
            hi = middle
        else:
            lo, sign_lo = middle, sign_mid
        refinements += 1
    powers = [(lo ** i, hi ** i) for i in range(len(modulus) - 1)]
    cache = {}

    def interval(value):
        coefficients = tuple(value.coeffs)
        if coefficients not in cache:
            require(len(coefficients) <= len(powers), 'Unexpected field degree')
            lower = upper = Q(0)
            for coefficient, (left, right) in zip(coefficients, powers):
                first, second = coefficient * left, coefficient * right
                lower += min(first, second)
                upper += max(first, second)
            cache[coefficients] = lower, upper
        return cache[coefficients]

    box, curvature, lipschitz = Q(1, 64), Q(16), Q(12)
    require(Q(baseline['box_radius']) == Q(proposed['box_radius']) == box,
            'Changed inherited analytic constants')
    require(Q(baseline['lipschitz_upper']) == lipschitz and interval(witness.side)[1] < 4,
            'Changed side/Lipschitz premise')
    reach = Q(3, 2) * (4 + 2 * box)
    require(reach + 6 * Q(3, 2) < curvature and reach + 3 * Q(3, 2) < lipschitz,
            'Global Hessian/gradient coefficient sums do not meet constants')
    functions = ir.elementary_functions(witness, box)
    require(len(functions) == 1936 and len(witness.contacts) == 14, 'Incomplete geometry inventory')
    root2, inverse_root2 = Q(proposed['sqrt2_upper']), Q(proposed['inverse_sqrt2_upper'])
    require(root2 > 0 and root2 * root2 > 2 and inverse_root2 > 0 and 2 * inverse_root2 * inverse_root2 > 1,
            'Invalid elementary square-root bounds')
    pair_curvatures = {}
    for first in range(11):
        for second in range(first + 1, 11):
            dx = witness.centres[second][0] - witness.centres[first][0]
            dy = witness.centres[second][1] - witness.centres[first][1]
            squared = interval(dx * dx + dy * dy)[1]
            require(squared > 0, 'Distinct witness centers required')
            denominator = 10 ** 9
            scaled = squared * denominator ** 2
            # This differs from the generator's ceil-before-isqrt order, but
            # proves the same rational upper bound directly by squaring.
            root = isqrt(scaled.numerator // scaled.denominator)
            if Q(root * root) < scaled:
                root += 1
            distance = Q(root, denominator)
            require(distance * distance >= squared, 'Center distance upper bound failed')
            pair_curvatures[first, second] = distance + 2 * root2 * box + 6 * root2
    function_curvatures = {}
    function_lipschitz = {}
    row_curvatures = {}
    for function in functions:
        bound = inverse_root2 if function.kind == 'wall' else pair_curvatures[function.subject[:2]]
        function_curvatures[function.label] = bound
        gradient_norm = sum(max(abs(lower), abs(upper)) for lower, upper in map(interval, function.gradient))
        function_lipschitz[function.label] = gradient_norm + bound * box
        if function.value.is_zero():
            key = ir.gradient_key(function.gradient)
            row_curvatures[key] = max(row_curvatures.get(key, Q(0)), bound)
    contact_pairs = {contact.pair for contact in witness.contacts}
    groups = {}
    for function in functions:
        if function.kind == 'pair' and function.subject[:2] in contact_pairs:
            groups.setdefault(function.subject[:5], []).append(function)
    require(len(groups) == 112 and all(len(members) == 4 for members in groups.values()),
            'Incomplete contact-feature cover')
    unavailable = {}
    available_labels = set()
    for feature, members in groups.items():
        negative = []
        zero_gradients = set()
        for member in members:
            if member.value.is_zero():
                zero_gradients.add(ir.gradient_key(member.gradient))
            else:
                lower, upper = interval(member.value)
                require(lower > 0 or upper < 0, 'Unresolved elementary sign')
                if upper < 0:
                    negative.append(member.subject[-1])
        if negative:
            unavailable[feature] = {member.subject[-1]: member for member in members}
        else:
            require(zero_gradients, 'An available contact feature has no zero corner')
            first, second, owner, axis, order = feature
            available_labels.add(f'{first}-{second}/{owner}.{axis}/{order}')
            rows = tc.feature_rows(witness.squares, witness.centres, witness.field,
                                   pair=(first, second), owner=owner, axis_index=axis, order=order)
            require(rows is not None and {tc.row_key(row) for row in rows} == zero_gradients,
                    'Active feature derivative rows do not equal its tied corner gradients')
    retained_labels = {alias for contact in witness.contacts for option in contact.options for alias in option.aliases}
    require(available_labels == retained_labels and len(available_labels) == proposed['active_features'] == 24,
            'Available features differ from the retained complete raw branch inventory')
    gap_receipts = proposed['unavailable_feature_proofs']
    require(len(gap_receipts) == len(unavailable) == 88, 'Unavailable feature receipts incomplete')
    seen = set()
    gap_radii = []
    for receipt in gap_receipts:
        key = tuple(receipt['feature'])
        require(key in unavailable and key not in seen, 'Duplicate or invalid unavailable feature')
        seen.add(key)
        corner = receipt['negative_corner']
        require(type(corner) is int and corner in unavailable[key], 'Invalid negative corner')
        member = unavailable[key][corner]
        lower, upper = interval(member.value)
        gap = Q(receipt['negative_gap_lower'])
        require(0 < gap <= -upper, 'Retained negative gap exceeds independent interval bound')
        per_function_lipschitz = Q(receipt['lipschitz_upper'])
        require(per_function_lipschitz >= function_lipschitz[member.label] > 0,
                'Retained Lipschitz constant is smaller than the independent coefficient bound')
        radius = Q(receipt['radius_lower'])
        require(radius == gap / per_function_lipschitz, 'Incorrect unavailable-feature radius')
        gap_radii.append(radius)
    require(seen == set(unavailable), 'Unavailable feature cover incomplete')
    gap_radius = min(gap_radii)
    require(gap_radius == Q(proposed['branch_stability_radius_lower']), 'Incorrect branch stability bound')

    D, DB = proposed['coefficient_denominator'], proposed['matrix_approximation_denominator']
    require(type(D) is int and type(DB) is int and D > 0 and DB > 0, 'Invalid rational scales')
    receipts = {record['branch']: record for record in proposed['branches']}
    require(len(receipts) == len(proposed['branches']) == 128 and set(receipts) == set(range(128)),
            'Incomplete branch receipts')
    global_radius = None
    maximum_error = Q(0)
    total = 0
    for branch in witness.branches:
        index = branch['branch']
        rows = branch['rows']
        require(len(rows) == 42 and all(len(row.coefficients) == 33 for row in rows), 'Wrong branch dimensions')
        integers = []
        for row in rows:
            approximate = []
            for coefficient in row.coefficients:
                lower, upper = interval(coefficient)
                q = round((lower + upper) * DB / 2)
                require(Q(q - 1, DB) <= lower <= upper <= Q(q + 1, DB), 'Matrix entry error exceeds 1/DB')
                approximate.append(q)
            integers.append(approximate)
        data = receipts[index]
        Krows = list(map(Q, data['row_curvature_upper']))
        require(len(Krows) == 42 and all(K >= row_curvatures[tc.row_key(row)] > 0 for K, row in zip(Krows, rows)),
                'Retained row curvature does not cover all tied nonlinear aliases')
        coordinates = {(item['coordinate'], item['sign']): item for item in data['certificates']}
        require(len(coordinates) == len(data['certificates']) == 66 and
                set(coordinates) == {(j, sign) for j in range(33) for sign in (-1, 1)},
                'Signed coordinate list incomplete')
        local_radius = None
        for (coordinate, sign), item in coordinates.items():
            weights = item['coefficients']
            require(len(weights) == 42 and all(type(weight) is int and weight >= 0 for weight in weights),
                    'Coordinate dual is not a nonnegative rational row combination')
            mass = Q(sum(weights), D)
            require(mass > 0 and mass == Q(item['mass']), 'Wrong coefficient mass')
            residual = 0
            for j in range(33):
                error = sum(weights[i] * integers[i][j] for i in range(42))
                if j == coordinate:
                    error -= sign * D * DB
                residual += abs(error)
            error = Q(residual, D * DB) + mass * Q(33, DB)
            require(0 <= error < 1 and error == Q(item['residual_upper']), 'Integer residual check failed')
            curvature_mass = sum(K * coefficient for K, coefficient in zip(Krows, weights)) / D
            require(curvature_mass > 0 and curvature_mass == Q(item['curvature_mass']), 'Incorrect weighted curvature sum')
            radius = 2 * (1 - error) / curvature_mass
            require(radius == Q(item['radius_lower']), 'Incorrect weighted radius')
            maximum_error = max(maximum_error, error)
            local_radius = radius if local_radius is None else min(local_radius, radius)
            total += 1
        require(local_radius == Q(data['weighted_radius_lower']), 'Incorrect branch radius')
        global_radius = local_radius if global_radius is None else min(global_radius, local_radius)
    require(total == proposed['signed_coordinate_certificates'] == 8448, 'Incomplete coordinate certificate count')
    require(global_radius == Q(proposed['weighted_radius_lower']), 'Incorrect global radius')
    limit = min(box, gap_radius, global_radius)
    opened, closed = Q(proposed['radius_open']), Q(proposed['radius_closed'])
    require(0 < opened <= limit and 0 < closed < limit, 'Radius exceeds independently checked limits')
    require(closed == Q(1, 248), 'Unexpected closed-radius claim')
    result = dict(
        status='PASS_INDEPENDENT_WEIGHTED_COORDINATE_RADIUS_AUDIT',
        proposal_sha256=sha256(proposal_raw).hexdigest(),
        inherited_baseline_sha256=sha256(baseline_raw).hexdigest(),
        baseline_audit_sha256=sha256(audit_path.read_bytes()).hexdigest(),
        prior_algebra_replay_sha256=sha256(prior_path.read_bytes()).hexdigest(),
        audit_script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        source_hashes=baseline['source_hashes'],
        root_refinements=refinements, root_interval=[str(lo), str(hi)],
        branches=128, raw_branches=512, signed_coordinate_certificates=total,
        active_features=24, unavailable_features=88,
        matrix_approximation_denominator=DB, coefficient_denominator=D,
        maximum_residual_upper=str(maximum_error), weighted_radius_lower=str(global_radius),
        branch_stability_radius_lower=str(gap_radius), box_radius=str(box),
        square_root_upper=str(root2), inverse_square_root_upper=str(inverse_root2),
        center_distance_upper_bounds=len(pair_curvatures), tied_gradient_curvature_bounds=len(row_curvatures),
        open_radius=str(opened), closed_radius=str(closed),
        acceptance='No LP or floating algebra; plain integer residuals, nonnegative rational coefficients, independently refined power-basis intervals, independently reconstructed row curvature and per-feature gradient bounds, and complete contact-feature branch stability.',
        scope='Labelled anchored33-coordinate fixed-side local isolation only; retained exact geometry and branch enumeration bound to independently audited inputs. No global optimality.',
        seconds=time.monotonic() - started,
    )
    destination = Path(__file__).with_name('weighted-coordinate-radius-independent-audit.json')
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('root_interval', 'branch_stability_radius_lower', 'source_hashes')}, indent=2))


if __name__ == '__main__':
    main()
