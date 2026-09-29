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
S=F(3877084,1000000);masks=[3,3,12,5,10];choices=[(0,0),(0,1),(1,1)]
base=generate(5,bound=4,query=False)+emit(5)+f'(assert (= L {num(S)}))\n'
for i,m in enumerate(masks):
 for corner in range(4):base+=f'(assert {"" if m&(1<<corner) else "(not "}cp_window_{corner}_{i}{"" if m&(1<<corner) else ")"})\n'
res=[]
for (lc,tl),(rc,tr) in [((0,1),(0,1))]:
 owned=[[1,2],[5,6],[1+4*(2+tl),2+4*(2+tr)],[4,lc+8],[7,3-rc+8]];body=base
 for i in range(5):
  for p in range(16):
   ix=p%4;iy=p//4;corner=ix//2+2*(iy//2);site=ix%2+2*(iy%2)
   body+=f'(assert cp_{"inside" if p in owned[i] else "outside"}_{corner}_{site}_{i})\n'
 origins=[(F(29,20),F(0)),(F(29,20),F(1)),(F(29,20),F(12,5)),(F(2,5),F(29,20)),(F(49,20),F(29,20))]
 for i,(x,y) in enumerate(origins):body+=f'(assert (and (= X_{i} {num(2*x+1)}) (= Y_{i} {num(2*y+1)}) (= c_{i} 1) (= s_{i} 0)))\n'
 solver=z3.Solver();solver.set(timeout=10000);solver.from_string(body);status=solver.check();assert status==z3.sat,status
 out={'status':'PASS_EXACT_FIVE_ARM_OWNERSHIP_COUNTERMODEL','outer_side':str(S),'window_side':str(F(2707106,1000000)),'origins':[[str(x),str(y)] for x,y in origins],'choices':[0,1,0,1],'owned_grid_site_indices':owned,'scope':'Exact axis-aligned five-square ownership counterexample to any five-arm-only exclusion. All16sites satisfy exactinside/outside requirements. Not11squares.'}
 Path(__file__).with_name('five-arm-owner-countermodel.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
