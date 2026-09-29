#!/usr/bin/env python3
"""Independent algebraic acceptance checks on jlevy's retained local packet.

The existing repository supplies the exact packing, derivative matrices, branch
enumeration, and a proposal for the stress (reconstructed by its field solver).
This checker independently accepts that proposal by rational polynomial
reduction, rational interval positivity, and modular full-rank tests. It does
not replay the quantitative curvature or radius calculation.
"""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
from math import isqrt
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'research/jlevy/packing'
sys.path[:0]=[str(SOURCE),str(SOURCE/'src')]
import sympy as sp
from cases.trump11 import tangent_cones as tc
from cases.trump11 import packing


def need(ok,message):
    if not ok:raise ValueError(message)


def evaluate(poly,x):
    answer=0
    for c in reversed(poly):answer=answer*x+c
    return answer


def enclose(poly,lo,hi):
    a=b=F(0)
    for c in reversed(poly):
        values=(a*lo,a*hi,b*lo,b*hi)
        a,b=min(values)+c,max(values)+c
    return a,b


def add_product(out,left,right):
    for i,a in enumerate(left):
        if a:
            for j,b in enumerate(right):
                if b:out[i+j]+=a*b


def remainder(poly,modulus):
    result=list(poly);degree=len(modulus)-1
    for i in range(len(result)-1,degree-1,-1):
        if result[i]:
            scale=result[i]/modulus[-1]
            for j,c in enumerate(modulus):result[i-degree+j]-=scale*c
    return result[:degree]


def prime(n):
    return n>=2 and all(n%d for d in range(2,isqrt(n)+1))


def modular_rank(matrix,p,root):
    rows=[]
    for row in matrix:
        converted=[]
        for value in row:
            total=0
            for c in reversed(value.coeffs):
                if c.denominator%p==0:return None
                total=(total*root+c.numerator*pow(c.denominator,-1,p))%p
            converted.append(total)
        rows.append(converted)
    rank=0
    for col in range(len(rows[0])):
        pivot=next((i for i in range(rank,len(rows)) if rows[i][col]),None)
        if pivot is None:continue
        rows[rank],rows[pivot]=rows[pivot],rows[rank]
        inv=pow(rows[rank][col],-1,p)
        rows[rank]=[(v*inv)%p for v in rows[rank]]
        for i in range(rank+1,len(rows)):
            factor=rows[i][col]
            if factor:rows[i]=[(a-factor*b)%p for a,b in zip(rows[i],rows[rank])]
        rank+=1
    return rank


def main():
    started=time.monotonic()
    path=SOURCE/'campaign/series/series-000-smoke-and-calibration/results/exp-013-h-026-trump-tangent.json'
    record=json.loads(path.read_text());squares,side,field=packing.build()
    walls,incidences,centres=tc.wall_rows(squares,side,field)
    contacts=tc.contact_options(squares,centres,field)
    groups=tc.enumerate_branch_groups(walls,contacts)
    records=tc.index_complete_records(record['branches']['records'],groups)
    need(len(groups)==128 and sum(g['raw_selection_count'] for g in groups.values())==512,
         'Wrong branch coverage')
    need(len(walls)==20 and len(contacts)==14,'Wrong active inventory')
    modulus=list(map(F,reversed(packing.U_MIN_POLY)))
    x=sp.Symbol('x');poly=sp.Poly(sum(sp.Rational(c.numerator,c.denominator)*x**i
                                  for i,c in enumerate(modulus)),x)
    lo,hi=map(F,packing.U_INTERVAL)
    need(poly.is_irreducible,'Defining polynomial irreducibility failed')
    need(poly.count_roots(sp.Rational(lo),sp.Rational(hi))==1,'Root isolation failed')
    need(evaluate(modulus,lo)*evaluate(modulus,hi)<0,'Root does not change sign')
    modular_choices=[]
    for p in range(101,2000):
        if prime(p):
            for r in range(p):
                if evaluate(modulus,r)%p==0:modular_choices.append((p,r))
        if len(modular_choices)>=20:break
    need(modular_choices,'No modular rank witnesses found')
    output=[];refinements=0
    for index,(_,group) in enumerate(sorted(groups.items())):
        rows=group['rows'];cert=records[index]['certificate'];pivots=cert['pivot_rows']
        free={int(i):F(w) for i,w in cert['free_weights'].items()}
        need(len(rows)==42 and all(len(row.coefficients)==33 for row in rows),'Wrong matrix shape')
        need(len(pivots)==33 and len(set(pivots))==33,'Invalid pivot list')
        need(set(pivots).isdisjoint(free) and set(pivots)|set(free)==set(range(42)),
             'Stress coordinates do not partition rows')
        minor=[list(rows[i].coefficients) for i in pivots]
        rank_witness=next(((p,r) for p,r in modular_choices
                           if modular_rank(minor,p,r)==33),None)
        need(rank_witness is not None,'No full-rank modular certificate')
        matrix=[[rows[p].coefficients[j] for p in pivots] for j in range(33)]
        rhs=[-sum((rows[i].coefficients[j]*field.rational(w) for i,w in free.items()),
                  field.zero) for j in range(33)]
        proposal=tc.exact_solve(matrix,rhs,field)
        need(proposal is not None,'Stress proposal failed')
        stress=[None]*42
        for i,w in free.items():stress[i]=list(field.rational(w).coeffs)
        for i,w in zip(pivots,proposal):stress[i]=list(w.coeffs)
        # Acceptance below uses plain Fraction polynomials, not field equality/sign.
        for j in range(33):
            total=[F(0)]*15
            for row,weight in zip(rows,stress):add_product(total,row.coefficients[j].coeffs,weight)
            need(not any(remainder(total,modulus)),'Independent stress identity failed')
        while True:
            bounds=[enclose(w,lo,hi) for w in stress]
            if all(a>0 for a,b in bounds):break
            need(not any(b<=0 for a,b in bounds),'Stress has a nonpositive weight')
            mid=(lo+hi)/2
            if evaluate(modulus,lo)*evaluate(modulus,mid)<0:hi=mid
            else:lo=mid
            refinements+=1;need(refinements<1000,'Positivity proof exceeded limit')
        output.append(dict(branch=index,row_count=42,rank=33,prime=rank_witness[0],
                           modular_root=rank_witness[1],positive_stresses=42,
                           exact_zero_residual_coordinates=33))
        if index%32==31:print(f'Independent checks: {index+1}/128 branches',flush=True)
    source_files=['cases/trump11/packing.py','cases/trump11/tangent_cones.py','src/sqpack/field.py']
    out=dict(status='PASS_INDEPENDENT_LOCAL_ALGEBRA_CHECKS',existing_author='jlevy/squares repository',
             record_path=str(path.relative_to(ROOT)),record_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
             source_sha256={f:hashlib.sha256((SOURCE/f).read_bytes()).hexdigest() for f in source_files},
             branches=output,raw_branches=512,derivative_branches=128,variables=33,
             rational_root_interval=list(map(str,(lo,hi))),root_refinements=refinements,
             polynomial_irreducible=True,isolated_root_count=1,
             acceptance='Independent rational polynomial residuals, positive interval bounds, and modular33x33 ranks; existing source supplies derivatives, branches, and stress proposals',
             scope='Existing full33-variable qualitative local isolation, together with the reviewed finite-branch argument. No quantitative radius/curvature replay, no global optimality claim.',
             seconds=time.monotonic()-started,python_version=sys.version)
    destination=Path(__file__).with_name('trump-local-independent-replay.json')
    destination.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='branches'},indent=2))


if __name__=='__main__':main()
