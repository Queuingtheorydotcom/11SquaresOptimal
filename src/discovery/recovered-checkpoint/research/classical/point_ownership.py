#!/usr/bin/env python3
"""Exact strictly unavoidable corner-point ownership cuts.

This emits necessary QF_NRA constraints, not an UNSAT certificate.
Coordinates X_i,Y_i are doubled square centers as in global formulation.
"""
from pathlib import Path
from fractions import Fraction as F
import argparse,json,sys
A=F(2707106,1000000)

def num(v):
 v=F(v)
 if v<0:return f'(- {num(-v)})'
 return str(v.numerator) if v.denominator==1 else f'(/ {v.numerator} {v.denominator})'
def asum(terms):return '(+ '+' '.join(terms)+')'
def count(bools):return asum([f'(ite {b} 1.0 0.0)' for b in bools])
def emit(n=11):
 lines=['; Strict corner ownership from the n=5 four-point proof.',
        '; Necessary conditions only; not a proof of global infeasibility.',
        '(declare-fun cp_sqrt2 () Real)',
        '(assert (> cp_sqrt2 0))',
        '(assert (= (* cp_sqrt2 cp_sqrt2) 2))',
        '(declare-fun cp_q () Real)',
        f'(assert (= (* cp_q (+ 2 (/ cp_sqrt2 2))) {num(A)}))',
        '(assert (and (> cp_q 0) (< cp_q 1)))']
 for corner in range(4):
  sx=corner%2;sy=corner//2
  ox=f'(- L {num(A)})' if sx else '0'
  oy=f'(- L {num(A)})' if sy else '0'
  for i in range(n):
   width=f'(+ c_{i} s_{i})'
   xw=f'(>= (- X_{i} {width}) (* 2 {ox}))' if sx else f'(<= (+ X_{i} {width}) {num(2*A)})'
   yw=f'(>= (- Y_{i} {width}) (* 2 {oy}))' if sy else f'(<= (+ Y_{i} {width}) {num(2*A)})'
   lines.append(f'(define-fun cp_window_{corner}_{i} () Bool (and {xw} {yw}))')
  lines.append(f'(define-fun cp_load_{corner} () Real {count([f"cp_window_{corner}_{i}" for i in range(n)])})')
  for p in range(4):
   lx='cp_q' if p%2==0 else f'(- {num(A)} cp_q)'
   ly='cp_q' if p//2==0 else f'(- {num(A)} cp_q)'
   lines += [f'(define-fun cp_px_{corner}_{p} () Real (+ {ox} {lx}))',f'(define-fun cp_py_{corner}_{p} () Real (+ {oy} {ly}))']
   for i in range(n):
    dx=f'(- (* 2 cp_px_{corner}_{p}) X_{i})';dy=f'(- (* 2 cp_py_{corner}_{p}) Y_{i})'
    u=f'(+ (* {dx} c_{i}) (* {dy} s_{i}))';v=f'(- (* {dy} c_{i}) (* {dx} s_{i}))'
    interior=f'(and (< {u} 1) (> {u} (- 1)) (< {v} 1) (> {v} (- 1)))'
    outside=f'(or (> {u} 1) (< {u} (- 1)) (> {v} 1) (< {v} (- 1)))'
    lines += [f'(define-fun cp_inside_{corner}_{p}_{i} () Bool {interior})',f'(define-fun cp_outside_{corner}_{p}_{i} () Bool {outside})']
   lines.append(f'(assert (<= {count([f"cp_inside_{corner}_{p}_{i}" for i in range(n)])} 1))')
  for i in range(n):
   inside=[f'cp_inside_{corner}_{p}_{i}' for p in range(4)];outside=[f'cp_outside_{corner}_{p}_{i}' for p in range(4)]
   lines += [f'(assert (=> cp_window_{corner}_{i} (or {" ".join(inside)})))',
             f'(assert (=> (and (= cp_load_{corner} 4) cp_window_{corner}_{i}) (= {count(inside)} 1)))',
             f'(assert (=> (and (= cp_load_{corner} 4) (not cp_window_{corner}_{i})) (and {" ".join(outside)})))']
 return '\n'.join(lines)+'\n'

def verify():
 if not __debug__:raise RuntimeError("Run without -O; assertions verify proof premises.")
 import z3
 # Exact rational threshold comparison; q is uniquely fixed by positive sqrt2.
 assert (A-2)**2<F(1,2)
 root=Path(__file__).resolve().parents[2]
 sys.path.insert(0,str(root/'work/global'))
 from generate_global_obligation import generate
 outcomes={}
 for n,L,poses,label in [(1,F(31,8),[(F(1,2),F(1,2))],'single_corner_strict_capture'),(9,F(31,8),[(F(2*x+1,2),F(2*y+1,2)) for y in range(3) for x in range(3)],'nine_grid_saturated_corner')]:
  body=generate(n,bound=4,query=False)+emit(n)+f'(assert (= L {num(L)}))\n'
  for i,(x,y) in enumerate(poses):
   body+=f'(assert (and (= X_{i} {num(2*x)}) (= Y_{i} {num(2*y)}) (= c_{i} 1) (= s_{i} 0)))\n'
  s=z3.Solver();s.from_string(body);s.set(timeout=10000)
  status=s.check();assert status==z3.sat,(label,status)
  if n==1:
   # The unscaled (1,1) would only be boundary contact; (q,q) is strict.
   control=z3.Solver();control.set(timeout=10000);control.from_string(body+'(assert (not cp_inside_0_0_0))');assert control.check()==z3.unsat
  if n==9:
   control=z3.Solver();control.set(timeout=10000);control.from_string(body+'(assert (not (= cp_load_0 4)))');assert control.check()==z3.unsat
  outcomes[label]=str(status)
 # Full11 file must parse with the unchanged global geometry.
 s=z3.Solver();s.from_string(generate(11,query=False)+emit(11))
 return {'status':'PASS_POINT_OWNERSHIP_FORMULATION_CHECKS','checks':outcomes,'full_11_assertions':len(s.assertions()),'scope':'Exact proof premises, parser and pinned feasible controls; full11 instance remains unsolved.'}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path(__file__).with_name('point-ownership-cuts.smt2'));args=ap.parse_args()
 result=verify();args.output.write_text(emit());args.output.with_suffix('.checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
