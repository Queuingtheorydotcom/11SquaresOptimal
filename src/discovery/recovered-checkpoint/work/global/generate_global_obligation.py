#!/usr/bin/env python3
"""Generate the complete, presently UNSOLVED global packing obligation.

The emitted QF_NRA instance is SAT iff n unit squares fit inside a square
of side L strictly below the selected bound.  An emitted file is not an
UNSAT certificate.  No global solver call is made by this program.

The implementation and exact root isolation use the Python standard library.
"""

from __future__ import annotations

import argparse
from fractions import Fraction as F
from pathlib import Path


# Ascending powers. The candidate side is the unique root in ALPHA_INTERVAL.
ALPHA_POLYNOMIAL = (-6865, 12420, -6754, -496, 1923, -842, 178, -20, 1)
ALPHA_INTERVAL = (F(387708359002280, 10**14), F(387708359002282, 10**14))


def _trim(poly):
    poly = list(map(F, poly))
    while poly and poly[-1] == 0:
        poly.pop()
    return poly


def _remainder(dividend, divisor):
    a, b = _trim(dividend), _trim(divisor)
    if not b:
        raise ZeroDivisionError("zero polynomial")
    while a and len(a) >= len(b):
        offset, factor = len(a) - len(b), a[-1] / b[-1]
        for j, value in enumerate(b):
            a[j + offset] -= factor * value
        a = _trim(a)
    return a


def _evaluate(poly, x):
    value = F(0)
    for coefficient in reversed(poly):
        value = value * x + coefficient
    return value


def _variations(values):
    signs = [1 if value > 0 else -1 for value in values if value]
    return sum(a != b for a, b in zip(signs, signs[1:]))


def alpha_root_certificate():
    """Return an exact rational Sturm check of the selected root interval."""
    p = list(map(F, ALPHA_POLYNOMIAL))
    sequence = [p, [i * p[i] for i in range(1, len(p))]]
    while True:
        remainder = _remainder(sequence[-2], sequence[-1])
        if not remainder:
            break
        sequence.append([-value for value in remainder])
    lower, upper = ALPHA_INTERVAL
    if not _evaluate(p, lower) or not _evaluate(p, upper):
        raise AssertionError("root interval has a root endpoint")
    va = _variations([_evaluate(q, lower) for q in sequence])
    vb = _variations([_evaluate(q, upper) for q in sequence])
    if va - vb != 1:
        raise AssertionError("root interval does not isolate one real root")
    negative_inf = _variations([
        q[-1] * (-1 if (len(q) - 1) % 2 else 1) for q in sequence
    ])
    positive_inf = _variations([q[-1] for q in sequence])
    return {
        "interval": [str(lower), str(upper)],
        "endpoint_variations": [va, vb],
        "roots_in_interval": va - vb,
        "total_real_roots": negative_inf - positive_inf,
        "sturm_sequence_length": len(sequence),
    }


def number(value):
    """An exact SMT-LIB Real numeral, without floating-point conversion."""
    value = F(value)
    if value < 0:
        return f"(- {number(-value)})"
    if value.denominator == 1:
        return str(value.numerator)
    return f"(/ {value.numerator} {value.denominator})"


def polynomial_expression(variable):
    expression = number(ALPHA_POLYNOMIAL[-1])
    for coefficient in reversed(ALPHA_POLYNOMIAL[:-1]):
        expression = f"(+ (* {expression} {variable}) {number(coefficient)})"
    return expression


def generate(squares=11, bound=None, *, query=True):
    """Generate exact SMT-LIB. bound=None selects the algebraic candidate.

    The reusable prefix with query=False is useful for separately checking
    pinned small examples. It has exactly the same packing constraints.
    """
    if squares < 1:
        raise ValueError("at least one square is required")
    if bound is not None and F(bound) <= 0:
        raise ValueError("the bound must be positive")
    lines = [
        "; COMPLETE GLOBAL COUNTEREXAMPLE SEARCH -- NOT AN UNSAT CERTIFICATE",
        "; SAT means a packing with side L strictly less than the bound.",
        "; No fixed contact graph or discrete orientation assumption is used.",
        "(set-logic QF_NRA)",
        "(declare-fun L () Real)",
        "(assert (> L 0))",
    ]
    if bound is None:
        certificate = alpha_root_certificate()
        lines.extend([
            "; alpha is isolated exactly by rational Sturm arithmetic:",
            f"; {certificate}",
            "(declare-fun alpha () Real)",
            f"(assert (= {polynomial_expression('alpha')} 0))",
            f"(assert (> alpha {number(ALPHA_INTERVAL[0])}))",
            f"(assert (< alpha {number(ALPHA_INTERVAL[1])}))",
            "(assert (< L alpha))",
        ])
    else:
        lines.append(f"(assert (< L {number(bound)}))")

    for i in range(squares):
        c, s, x, y = (f"{letter}_{i}" for letter in ("c", "s", "X", "Y"))
        lines.append(f"; square {i}: center=({x}/2,{y}/2), axes=({c},{s}),(-{s},{c})")
        lines.extend(f"(declare-fun {name} () Real)" for name in (c, s, x, y))
        lines.extend([
            f"(assert (>= {c} 0))",
            f"(assert (>= {s} 0))",
            f"(assert (= (+ (* {c} {c}) (* {s} {s})) 1))",
        ])
        for coordinate in (x, y):
            lines.extend([
                f"(assert (>= {coordinate} (+ {c} {s})))",
                f"(assert (<= {coordinate} (- (* 2 L) (+ {c} {s}))))",
            ])

    for i in range(squares):
        for j in range(i + 1, squares):
            tag = f"{i}_{j}"
            dx, dy, dot, cross = (f"{name}_{tag}" for name in ("dx", "dy", "dot", "cross"))
            lines.extend([
                f"; pair {i},{j}: all four separating-axis families, both signs",
                f"(define-fun {dx} () Real (- X_{j} X_{i}))",
                f"(define-fun {dy} () Real (- Y_{j} Y_{i}))",
                f"(define-fun {dot} () Real (+ (* c_{i} c_{j}) (* s_{i} s_{j})))",
                f"(define-fun {cross} () Real (- (* c_{i} s_{j}) (* s_{i} c_{j})))",
            ])
            projections = []
            for k in (i, j):
                projections.extend([
                    f"(+ (* {dx} c_{k}) (* {dy} s_{k}))",
                    f"(- (* {dy} c_{k}) (* {dx} s_{k}))",
                ])
            branches = []
            for projection in projections:
                for signed in (projection, f"(- {projection})"):
                    branches.append(
                        f"(and (>= {signed} (+ 1 {dot} {cross})) "
                        f"(>= {signed} (- (+ 1 {dot}) {cross})))"
                    )
            lines.append("(assert (or\n  " + "\n  ".join(branches) + "\n))")

    if query:
        lines.extend(["(check-sat)", "(exit)"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--squares", type=int, default=11)
    parser.add_argument("--bound", type=F, help="optional rational bound, e.g. 97/25")
    parser.add_argument("--output", type=Path, default=Path("global_alpha_11.smt2"))
    args = parser.parse_args()
    document = generate(args.squares, args.bound)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document, encoding="utf-8")
    print(f"Wrote {args.output}: {args.squares} squares; global result remains UNSOLVED.")
    if args.bound is None:
        print(alpha_root_certificate())


if __name__ == "__main__":
    main()
