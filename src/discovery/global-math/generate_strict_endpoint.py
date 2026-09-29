#!/usr/bin/env python3
"""Generate the exact strict endpoint feasibility instance; does not solve it."""
from pathlib import Path
import argparse


def power(x, n):
    return f"(* {' '.join([x] * n)})" if n > 1 else x


def generate():
    out = [
        "; Existence is equivalent to an eleven-square packing below Trump's side.",
        "; This file is an unsolved exact QF_NRA instance, not a certificate.",
        "(set-logic QF_NRA)",
        "(declare-fun u () Real)",
        "(assert (> u (/ 36 100)))",
        "(assert (< u (/ 37 100)))",
        f"(assert (= (+ (* 5 {power('u',8)}) (* (- 10) {power('u',7)}) "
        f"(* (- 2) {power('u',6)}) (* 14 {power('u',5)}) "
        f"(* 12 {power('u',4)}) (* (- 6) {power('u',3)}) "
        f"(* 2 {power('u',2)}) (* 2 u) (- 1)) 0))",
        "(define-fun E () Real (+ 1 (* 2 u) (- (* u u))))",
        "(define-fun N () Real (+ (* 6 u) 4))",
    ]
    for i in range(11):
        for v in ('x', 'y', 't'):
            out.append(f"(declare-fun {v}{i} () Real)")
        out += [
            f"(define-fun D{i} () Real (+ 1 (* t{i} t{i})))",
            f"(define-fun A{i} () Real (- 1 (* t{i} t{i})))",
            f"(define-fun B{i} () Real (* 2 t{i}))",
            f"(define-fun H{i} () Real (+ A{i} B{i}))",
        ]
        for v in ('x', 'y'):
            out += [
                f"(assert (> (- (* 2 D{i} {v}{i}) H{i}) 0))",
                f"(assert (> (- (* 2 D{i} (- N (* E {v}{i}))) (* E H{i})) 0))",
            ]
    out += ["(assert (>= t0 0))", "(assert (<= t10 1))"]
    for i in range(10):
        out.append(f"(assert (<= t{i} t{i+1}))")
    for i in range(11):
        for j in range(i+1, 11):
            name = f"{i}_{j}"
            out += [
                f"(define-fun dx{name} () Real (- x{j} x{i}))",
                f"(define-fun dy{name} () Real (- y{j} y{i}))",
                f"(define-fun K{name} () Real (* (+ 1 (* t{i} t{j})) "
                f"(+ 1 (* t{i} t{j}) t{j} (- t{i}))))",
            ]
            axes = []
            for k, other in ((i,j), (j,i)):
                p = f"(* D{other} (+ (* A{k} dx{name}) (* B{k} dy{name})))"
                q = f"(* D{other} (+ (- (* B{k} dx{name})) (* A{k} dy{name})))"
                axes += [p, q]
            terms = [f"(> (- {signed} K{name}) 0)"
                     for a in axes for signed in (a, f"(- {a})")]
            out.append("(assert (or\n  " + "\n  ".join(terms) + "))")
    out += ["(check-sat)", "; No (get-model): the desired outcome is a certified unsat."]
    return "\n".join(out) + "\n"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=Path(__file__).with_name('strict-endpoint.smt2'))
    args = parser.parse_args()
    args.output.write_text(generate())
    print(f"Wrote unsolved exact instance: {args.output}")
    print('34 variables; 44 strict wall inequalities; 55 eight-way pair clauses.')
