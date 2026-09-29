"""Exact-solver probe for nine five-cross saturated ownership branches.

An UNSAT result here would need its scope and solver trust audited; timeout is
not a proof. This script records status without claiming a global result.
"""
from pathlib import Path
from itertools import product
import sys,json,time
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/global'));from generate_global_obligation import generate
from point_ownership import emit,num
import z3
S=F(3877084,1000000);masks=[3,3,12,5,10,4,8];choices=[(0,0),(0,1),(1,1)]
base=generate(7,bound=4,query=False)+emit(7)+f'(assert (= L {num(S)}))\n'
for i,m in enumerate(masks):
 for corner in range(4):base+=f'(assert {"" if m&(1<<corner) else "(not "}cp_window_{corner}_{i}{"" if m&(1<<corner) else ")"})\n'
res=[]
for (lc,tl),(rc,tr) in product(choices,repeat=2):
 owned=[[1,2],[5,6],[1+4*(2+tl),2+4*(2+tr)],[4,lc+8],[7,3-rc+8]]
 used={v for g in owned for v in g}
 owned += [[next(v for v in (8,9,13) if v not in used)],[next(v for v in (10,11,14) if v not in used)]]
 body=base
 for i in range(7):
  for p in range(16):
   ix=p%4;iy=p//4;corner=ix//2+2*(iy//2);site=ix%2+2*(iy%2)
   body+=f'(assert cp_{"inside" if p in owned[i] else "outside"}_{corner}_{site}_{i})\n'
 solver=z3.Solver();solver.set(timeout=20000);solver.from_string(body);start=time.monotonic();status=solver.check();row={'choices':[lc,tl,rc,tr],'status':str(status),'seconds':time.monotonic()-start};res.append(row);print(row,flush=True)
 (Path(__file__).with_name('seven-owner-exact.json')).write_text(json.dumps({'status':'EXACT_SOLVER_BRANCH_PROBE','branches':res,'scope':'Seven-square ownership necessary subproblem, not whole11; UNSAT entries require solver-trust review; unknown is no conclusion.'},indent=2)+'\n')
 if status==z3.sat:
  (Path(__file__).with_name('seven-owner-sat-model.txt')).write_text(str(solver.model()));break
