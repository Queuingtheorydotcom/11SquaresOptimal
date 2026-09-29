"""Exact integer sweep with conservative direct-majority-hull rectangles.

The discrete checker is preserved in exact_mixed.py. This module adds the
majority_hull kind via inner staircases; its logical charge is the TRUE closed
majority polygon indicator, not the sum on shared staircase boundaries.
"""
from bisect import bisect_left,bisect_right
from collections import defaultdict
from copy import deepcopy
from fractions import Fraction as F
from itertools import combinations
from math import comb,lcm
from pathlib import Path
import argparse,hashlib,json,time
import numpy as np

from exact_mixed import validate as discrete_validate,geometry as discrete_geometry
from integer_sweep import accumulate,trig,need
from majority_geometry import majority_rectangles,majority_rectangles_in_domain
from majority_precompute import row_strips


def validate(c):
    proxy=deepcopy(c);majority=[];remove=[]
    for atom in proxy.get('charge_orbits',[]):
        if atom.get('kind')!='majority_hull':continue
        groups=atom['sets'];k=atom['threshold'];w=atom['weight']
        need(groups and type(k) is int and 1<=k<=4,'Invalid majority threshold')
        need(not atom.get('multiset',False),'Majority groups require distinct sites')
        need(all(len(group)==2*k-1 and len(set(group))==len(group) for group in groups),
             'Majority group must have exactly 2*k-1 distinct sites')
        atom['kind']='threshold'  # Same D4 requirements and same unit budget.
        if w:
            for group in groups:
                majority.append((tuple(group),k,w))
                for j in range(k,len(group)+1):
                    coefficient=(-1)**(j-k)*comb(j-1,k-1)*w
                    remove.extend((tuple(sorted(part)),coefficient)
                                  for part in combinations(group,j))
    data,jobs,margin=discrete_validate(proxy)
    points,pw,subsets,coefficients,D=data
    if majority:
        totals=defaultdict(int)
        for group,weight in zip(subsets,coefficients):totals[tuple(sorted(group))]+=weight
        for group,weight in remove:totals[group]-=weight
        surviving=[(group,weight) for group,weight in totals.items() if weight]
        subsets=[group for group,weight in surviving]
        coefficients=[weight for group,weight in surviving]
    return (points,pw,subsets,coefficients,D,majority),jobs,margin


def geometry(points,pw,subsets,coefficients,D,majority,t,B,H,meta=False,subdivisions=4,
             verify_staircase_corners=False,domain_conditional=True,prepared=None,
             conditional_features=None):
    if not majority:
        return discrete_geometry(points,pw,subsets,coefficients,D,t,B,H,meta=meta)
    p,q=t.numerator,t.denominator;C=q*q-p*p;S=2*p*q;R=q*q+p*p
    LD=int(F(191,50)*D);scale=lcm(2*D,(B/2).denominator,H.denominator);factor=scale//(2*D)
    h=int(H*scale);half=int(B*scale/2)*R
    uv=[(C*(2*x-LD)*factor+S*(2*y-LD)*factor,
         -S*(2*x-LD)*factor+C*(2*y-LD)*factor) for x,y in points]
    poly=[(C*x+S*y,-S*x+C*y) for x,y in [(-h,-h),(h,-h),(h,h),(-h,h)]]
    rect={}
    def insert(indices,w):
        if not w:return
        xx=[uv[i][0] for i in indices];yy=[uv[i][1] for i in indices]
        z=(max(xx)-half,min(xx)+half,max(yy)-half,min(yy)+half)
        if z[0]<z[1] and z[2]<z[3]:rect[z]=rect.get(z,0)+w
    for i,w in enumerate(pw):insert([i],w)
    for group,w in zip(subsets,coefficients):insert(group,w)
    staircase_count=0;feature_rectangles=[]
    if prepared is not None:need(len(prepared)==len(majority),'Prepared majority length mismatch')
    for feature_index,(group,k,w) in enumerate(majority):
        sites=[uv[i] for i in group]
        strips=(row_strips(prepared[feature_index],sites,half,C,S,R,factor)
                if prepared is not None else None)
        use_conditional=domain_conditional and (conditional_features is None or feature_index in conditional_features)
        if use_conditional:
            rectangles=majority_rectangles_in_domain(sites,half,poly,
                                                     subdivisions,verify_staircase_corners,strips)
        else:
            rectangles=majority_rectangles(sites,half,subdivisions,
                                          verify_corners=verify_staircase_corners,strips=strips)
        staircase_count+=len(rectangles)
        if meta:feature_rectangles.append(rectangles)
        for rectangle in rectangles:rect[rectangle]=rect.get(rectangle,0)+w
    rect={r:w for r,w in rect.items() if w}
    absolute=sum(abs(w) for w in rect.values())
    need(absolute<2**50,'Row rectangle accumulation exceeds the exactness bound')
    rr=list(rect);ww=np.array(list(rect.values()),np.int64)
    xe=sorted({p[0] for p in poly}|{v for r in rr for v in r[:2]})
    ye=sorted({p[1] for p in poly}|{v for r in rr for v in r[2:]})
    xi={v:i for i,v in enumerate(xe)};yi={v:i for i,v in enumerate(ye)}
    ev=np.array(sorted([(xi[r[0]],i,1) for i,r in enumerate(rr)]+
                       [(xi[r[1]],i,-1) for i,r in enumerate(rr)]),np.int64).reshape((-1,3))
    yl=np.array([yi[r[2]] for r in rr],np.int64);yh=np.array([yi[r[3]] for r in rr],np.int64)
    first=np.full(len(xe)-1,-1,np.int64);last=first.copy();edges=[]
    for k,(u,v) in enumerate(poly):
        z,w=poly[(k+1)%4]
        if z==u:continue
        if z<u:u,v,z,w=z,w,u,v
        edges.append((u,z,w-v,v*(z-u)-u*(w-v),z-u))
    left=min(p[0] for p in poly);right=max(p[0] for p in poly)
    for k,(a,b) in enumerate(zip(xe,xe[1:])):
        if a<left or b>right:continue
        crossings=[]
        for u,z,m,n,d in edges:
            if u<=a and b<=z:crossings.extend([(m*a+n,d),(m*b+n,d)])
        need(len(crossings)==4,'polygon edge count');bn,bd=crossings[0];tn,td=bn,bd
        for n,d in crossings[1:]:
            if n*bd<bn*d:bn,bd=n,d
            if n*td>tn*d:tn,td=n,d
        first[k]=bisect_right(ye,F(bn)/bd)-1;last[k]=bisect_left(ye,F(tn)/td)
        need(0<=first[k]<last[k]<=len(ye)-1,'query range')
    arrays=(len(ye)-1,ev[:,0],ev[:,1],ev[:,2],yl,yh,ww,first,last)
    if meta:
        return arrays,dict(poly=poly,xe=xe,ye=ye,rect=rr,weights=list(map(int,ww)),
                           C=C,S=S,R=R,scale=scale,uv=uv,half=half,
                           majority_features=len(majority),majority_rectangles=staircase_count,
                           feature_rectangles=feature_rectangles,
                           absolute_rectangle_units=absolute,subdivisions=subdivisions,
                           domain_conditional=domain_conditional)
    return arrays


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certificate',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--subdivisions',type=int)
    parser.add_argument('--rows',help='Optional comma-separated selected rows; not a full proof')
    parser.add_argument('--direct',action='store_true')
    parser.add_argument('--unconditional',action='store_true',help='Use strictly interior integer staircases')
    args=parser.parse_args();raw=args.certificate.read_bytes();c=json.loads(raw)
    subdivisions=args.subdivisions if args.subdivisions is not None else c.get('majority_subdivisions',4)
    need(type(subdivisions) is int and subdivisions>=1,'Invalid subdivisions')
    data,jobs,margin=validate(c)
    selected=list(range(len(jobs))) if args.rows is None else sorted(set(map(int,args.rows.split(','))))
    need(selected and all(0<=i<len(jobs) for i in selected),'Invalid row selection')
    start=time.monotonic();rows=[]
    for i in selected:
        arrays=geometry(*data,*jobs[i],subdivisions=subdivisions,domain_conditional=not args.unconditional)
        value,cells,winner=accumulate(*arrays,direct=args.direct)
        need(value>=c['minimum_units'],'Coverage fails at row '+str(i))
        rows.append({'row':i,'minimum_units':int(value),'cells':int(cells),
                     'slabs':int(np.count_nonzero(arrays[-2]>=0))})
        if len(rows)%100==0:print('ROWS',len(rows),'/',len(selected),flush=True)
    full=selected==list(range(len(jobs)))
    minimum=min(row['minimum_units'] for row in rows)
    result={'status':('PASS_FULL_EXACT_MAJORITY_HULL_REPLAY' if full else
                      'PASS_SELECTED_MAJORITY_HULL_ROWS_NOT_A_FULL_PROOF'),
            'certificate_sha256':hashlib.sha256(raw).hexdigest(),
            'full_catalogue_scanned':full,'intervals':len(jobs),'rows_scanned':len(rows),
            'bound':str(F(c['L'])/F(c['A'])),'minimum_units':minimum,
            'budget_units':c['budget_units'],'counting_surplus_units':11*minimum-c['budget_units'],
            'strict_core_margin':str(margin),'majority_subdivisions':subdivisions,
            'domain_conditional_rectangles':not args.unconditional,
            'slabs':sum(row['slabs'] for row in rows),'cells':sum(row['cells'] for row in rows),
            'rows':rows,'seconds':time.monotonic()-start}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


if __name__=='__main__':main()
