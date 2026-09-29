#!/usr/bin/env python3
"""Bounded formulation checks, NOT a proof of the eleven-square theorem.

Requires z3-solver only for these tests; the generator itself has no external
dependencies. No unpinned eleven-square solve is performed here.
"""

from fractions import Fraction as F
import unittest

import z3

from generate_global_obligation import alpha_root_certificate, generate


def pinned_solver(squares, assignments, bound=11):
    solver = z3.SolverFor("QF_NRA")
    solver.set(timeout=5000)
    solver.from_string(generate(squares, bound, query=False))
    for name, value in assignments.items():
        solver.add(z3.Real(name) == z3.RealVal(str(F(value))))
    return solver


def square(index, c, s, x, y):
    return {f"c_{index}": c, f"s_{index}": s, f"X_{index}": x, f"Y_{index}": y}


class FormulationChecks(unittest.TestCase):
    def test_alpha_isolation(self):
        certificate = alpha_root_certificate()
        self.assertEqual(certificate["endpoint_variations"], [4, 3])
        self.assertEqual(certificate["roots_in_interval"], 1)
        self.assertEqual(certificate["total_real_roots"], 2)

    def test_full_eleven_square_syntax(self):
        # Parse only; solving this unrestricted formula is the missing theorem.
        assertions = z3.parse_smt2_string(generate(11, query=False))
        self.assertEqual(len(assertions), 137)

    def test_one_axis_aligned_square_boundary(self):
        assignments = {"L": 1, **square(0, 1, 0, 1, 1)}
        self.assertEqual(pinned_solver(1, assignments, bound=2).check(), z3.sat)
        assignments["L"] = F(99, 100)
        self.assertEqual(pinned_solver(1, assignments, bound=2).check(), z3.unsat)

    def test_one_rotated_square_boundary(self):
        assignments = {"L": F(7, 5), **square(0, F(3, 5), F(4, 5), F(7, 5), F(7, 5))}
        self.assertEqual(pinned_solver(1, assignments, bound=2).check(), z3.sat)
        assignments["L"] = F(139, 100)
        self.assertEqual(pinned_solver(1, assignments, bound=2).check(), z3.unsat)

    def test_touching_and_overlap(self):
        assignments = {"L": 2, **square(0, 1, 0, 1, 1), **square(1, 1, 0, 3, 1)}
        self.assertEqual(pinned_solver(2, assignments, bound=3).check(), z3.sat)
        assignments["X_1"] = F(299, 100)
        self.assertEqual(pinned_solver(2, assignments, bound=3).check(), z3.unsat)

    def test_all_four_axes_both_signs(self):
        # With i at angle 0 and j at (cos,sin)=(3/5,4/5), the scaled
        # separating threshold is 12/5 on each of the four axes. Each
        # fixture below touches along exactly its designated axis family.
        axes = [(F(1), F(0)), (F(0), F(1)), (F(3, 5), F(4, 5)), (F(-4, 5), F(3, 5))]
        threshold = F(12, 5)
        for expected_axis, (ax, ay) in enumerate(axes):
            for sign in (-1, 1):
                dx, dy = sign * threshold * ax, sign * threshold * ay
                successful = [k for k, (ux, uy) in enumerate(axes)
                              if abs(dx * ux + dy * uy) >= threshold]
                self.assertEqual(successful, [expected_axis])
                assignments = {"L": 10, **square(0, 1, 0, 10, 10),
                               **square(1, F(3, 5), F(4, 5), 10 + dx, 10 + dy)}
                self.assertEqual(pinned_solver(2, assignments).check(), z3.sat)
                # Move inward by an exact 1%: every separating axis fails.
                assignments["X_1"] = 10 + F(99, 100) * dx
                assignments["Y_1"] = 10 + F(99, 100) * dy
                self.assertEqual(pinned_solver(2, assignments).check(), z3.unsat)

    def test_unpinned_small_bounds(self):
        # The n=1 cases have free positions and orientations. The n=2 case
        # leaves positions free while pinning both orientations horizontally.
        self.assertEqual(pinned_solver(1, {}, bound=1).check(), z3.unsat)
        self.assertEqual(pinned_solver(1, {}, bound=F(101, 100)).check(), z3.sat)
        self.assertEqual(pinned_solver(2, {"c_0": 1, "s_0": 0, "c_1": 1, "s_1": 0}, bound=3).check(), z3.sat)


if __name__ == "__main__":
    print("Checking the formulation only; eleven-square optimality remains UNSOLVED.")
    unittest.main(verbosity=2)
