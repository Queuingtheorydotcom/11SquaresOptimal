#!/usr/bin/env python3
"""Exact counterexample to extending point-depth bounds to majority charges.

This is an explanatory three-square fractional example. It is neither the
missing historical 28-square scalar obstruction nor an eleven-square packing.
"""
from fractions import Fraction as F
import json
from pathlib import Path


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def interior(square, p):
    center, u, v = square
    d = tuple(x-y for x, y in zip(p, center))
    return abs(dot(d, u)) < F(1, 2) and abs(dot(d, v)) < F(1, 2)


def verify():
    if not __debug__:
        raise RuntimeError("Run without -O; exact assertions are required")
    squares = [
        ((F(1, 2), F(1, 2)), (F(1), F(0)), (F(0), F(1))),
        ((F(6, 5), F(3, 10)), (F(3, 5), F(4, 5)), (F(-4, 5), F(3, 5))),
        ((F(4, 5), F(7, 5)), (F(1), F(0)), (F(0), F(1))),
    ]
    sites = [(F(9, 10), F(2, 5)), (F(1, 2), F(19, 20)), (F(6, 5), F(91, 100))]
    for center, u, v in squares:
        assert dot(u, u) == dot(v, v) == 1 and dot(u, v) == 0
    capture = [[interior(sq, p) for p in sites] for sq in squares]
    assert capture == [[True, True, False], [True, False, True], [False, True, True]]
    # A intersect C lies in x<=1, y>=9/10. B's v-projection there is
    # -(4/5)(x-6/5)+(3/5)(y-3/10), minimized at x=1,y=9/10.
    triple_projection_lower = -F(4, 5)*(1-F(6, 5)) + F(3, 5)*(F(9, 10)-F(3, 10))
    assert triple_projection_lower == F(13, 25) > F(1, 2)
    # Thus the closed triple intersection is empty; depth is at most two.
    # All vertices become contained in [0,23/10]^2 after shifting y by 2/5.
    for center, u, v in squares:
        for a in (-1, 1):
            for b in (-1, 1):
                p = [center[j] + (a*u[j]+b*v[j])/2 + (F(2, 5) if j else 0) for j in range(2)]
                assert all(0 <= x <= F(23, 10) for x in p)
    return {
        "status": "EXACT_RATIONAL_EXAMPLE_VERIFIED",
        "square_weight": "1/2",
        "closed_weighted_pointwise_depth_upper": "1",
        "two_of_three_feature_weighted_depth": "3/2",
        "two_of_three_disjoint_core_budget": "1",
        "capture": capture,
        "triple_separation_projection_lower": str(triple_projection_lower),
        "containing_side_after_translation": "23/10",
        "scope": "Point-depth feasibility alone does not imply nonlinear majority-feature budget feasibility. This is not an eleven-square packing or a recovered historical certificate."
    }


if __name__ == "__main__":
    result = verify()
    Path(__file__).with_name("scalar-barrier-scope.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
