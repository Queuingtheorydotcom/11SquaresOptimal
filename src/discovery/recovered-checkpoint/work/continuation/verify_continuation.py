#!/usr/bin/env python3
"""Check exact algebraic premises of the strict-core continuation theorem.

This checker intentionally does not rerun or replace the complete charge
sweeps. Its conclusion is conditional on those original scans. It imports no
repository verifier and uses only Python's standard library and rational math.
"""

import argparse
from decimal import Decimal, localcontext
from fractions import Fraction as Q
from hashlib import sha256
from itertools import product
import json
from pathlib import Path


PIN = "57e9927da5c13f42dd8bcbf8f08c84363635fece626657ee63a810c61cd44458"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def quadratic_minimum(coefficients, a, b):
    """Exact minimum on a closed rational interval, including a vertex."""
    p0, p1, p2 = coefficients
    candidates = [a, b]
    if p2 > 0:
        vertex = -p1 / (2 * p2)
        if a < vertex < b:
            candidates.append(vertex)
    return min(p0 + p1 * u + p2 * u * u for u in candidates)


def width(u):
    return (1 + 2 * u - u * u) / (1 + u * u)


def decimal(q):
    with localcontext() as ctx:
        ctx.prec = 65
        return str(Decimal(q.numerator) / Decimal(q.denominator))


def verify(path):
    raw = path.read_bytes()
    digest = sha256(raw).hexdigest()
    require(digest == PIN, "Certificate does not match the pinned original.")
    certificate = json.loads(raw)
    L, A = Q(certificate["L"]), Q(certificate["A"])
    require(L == Q(191, 50) and A == Q(764, 775), "Unexpected scales.")
    margin = Q(1, 10**12)
    delta = margin / 3
    A_new = A - delta
    cursor = Q(0)
    minimum_new_numerator = None
    minimum_original_endpoint_margin = None
    checks = 0

    for row_number, row in enumerate(certificate["entries"]):
        a, b, t, B = map(Q, row)
        context = f"row {row_number}"
        require(a == cursor and 0 <= a < b < 1, f"Angle coverage: {context}")
        require(0 <= t < 1 and 0 < B < A, f"Invalid core: {context}")
        cursor = b
        q = min(width(a), width(b))
        require(0 < q and q * q < 2, f"Endpoint width bound: {context}")
        # q <= w(u) throughout the row; denominator 1+u^2 is positive.
        require(quadratic_minimum((1-q, Q(2), -1-q), a, b) >= 0,
                f"Centre envelope: {context}")
        r = A * q / 2
        require(0 < r < L / 2 and B * width(t) / 2 <= r,
                f"Original scanned domain: {context}")

        # Numerators of cos(theta(u)-theta(t)) and sin(...), with the
        # common positive denominator (1+t^2)(1+u^2).
        cr = (1-t*t, 4*t, -(1-t*t))
        sr = (-2*t, 2*(1-t*t), 2*t)
        T = 1 + t*t
        for e, f in product((-1, 1), repeat=2):
            base = [-B * (e*cr[i] + f*sr[i]) for i in range(3)]
            # Universal original full-side slack >= margin.
            original = base.copy()
            original[0] += (A-margin)*T
            original[2] += (A-margin)*T
            require(quadratic_minimum(original, a, b) >= 0,
                    f"Original uniform margin: {context}, signs {e,f}")

            # A-delta-B*g(u)-delta*q*w(u) > 0. This is the precise
            # containment inequality after the coordinatewise clipping.
            continued = base.copy()
            continued[0] += (A-delta)*T - delta*q*T
            continued[1] -= 2*delta*q*T
            continued[2] += (A-delta)*T + delta*q*T
            new_min = quadratic_minimum(continued, a, b)
            require(new_min > 0,
                    f"Translated strict containment: {context}, signs {e,f}")
            minimum_new_numerator = (new_min if minimum_new_numerator is None
                                     else min(minimum_new_numerator, new_min))
            checks += 1

        for u in (a, b):
            den = T*(1+u*u)
            cv = sum(cr[i]*u**i for i in range(3)) / den
            sv = sum(sr[i]*u**i for i in range(3)) / den
            endpoint_margin = A - B*(abs(cv)+abs(sv))
            minimum_original_endpoint_margin = (
                endpoint_margin if minimum_original_endpoint_margin is None
                else min(minimum_original_endpoint_margin, endpoint_margin))

    require(cursor*cursor + 2*cursor > 1, "Catalogue does not cover pi/4.")
    gamma = certificate["minimum_units"]
    budget = certificate["budget_units"]
    require(type(gamma) is int and type(budget) is int,
            "Integral charge units required.")
    require(11*gamma > budget, "No strict counting surplus.")
    bound = L/A_new
    return {
        "status": "PASS_EXACT_CONTINUATION_PREMISES",
        "scope": "All-row rational geometry and unchanged counting algebra; "
                 "conditional on successful original complete charge sweeps.",
        "certificate_sha256": digest,
        "intervals": len(certificate["entries"]),
        "original_margin_inequalities": checks,
        "translated_strict_containment_inequalities": checks,
        "minimum_original_endpoint_margin": str(minimum_original_endpoint_margin),
        "minimum_translated_quadratic_numerator": str(minimum_new_numerator),
        "L": str(L),
        "original_parent_side": str(A),
        "uniform_original_margin": str(margin),
        "parent_side_decrease": str(delta),
        "new_parent_side": str(A_new),
        "new_strict_lower_bound": str(bound),
        "new_bound_decimal": decimal(bound),
        "improvement_over_31_over_8": str(bound-Q(31,8)),
        "improvement_decimal": decimal(bound-Q(31,8)),
        "counting_surplus_units": 11*gamma-budget,
        "weight_denominator": certificate["weight_denominator"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.certificate)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
