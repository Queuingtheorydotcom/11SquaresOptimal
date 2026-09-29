"""Independent integer replay of nine-parent fixed-family charge obstruction."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
from itertools import combinations
from math import lcm
from pathlib import Path
import json
import time

from exact_mixed import expand


def require(test,message):
    if not test:raise ValueError(message)


def main():
    root=Path(__file__).resolve().parents[2];start=time.monotonic()
    source=root/'research/features/candidate-majority-round3.json'
    witness=root/'research/stromquist/true-critical-parent-controls.json'
    raw=source.read_bytes();wraw=witness.read_bytes();c=json.loads(raw);proof=json.loads(wraw)
    require(sha256(raw).hexdigest()=='57467372e2ec61f9018e38870260638dad7b92ce7ff423010a4e9612be6ef7a2','Fixed source changed')
    A=F(proof['exact_parent_side']);L=F(c['L']);D=c['coordinate_denominator'];LD=int(L*D)
    require(A==F(7640,7751) and L/A==F(proof['target']),'Wrong exact target')
    # Revalidate all source site/D4 and feature premises, not its stale entries.
    proxy=deepcopy(c)
    for a in proxy['charge_orbits']:
        if a.get('kind')=='majority_hull':a['kind']='threshold'
    validated_points,_,_,_,_=expand(proxy)
    points=[];point_orbit=[];budgets=[]
    for i,(x,y,_) in enumerate(c['point_orbits']):
        orbit=sorted({(a,b) for u,v in ((x,y),(y,x)) for a in (u,LD-u) for b in (v,LD-v)})
        points.extend(orbit);point_orbit.extend([i]*len(orbit));budgets.append(len(orbit))
    require(points==validated_points,'Independent physical site order differs')
    for atom in c['charge_orbits']:
        kind=atom.get('kind','threshold');m=len(atom['sets'][0]);k=atom['threshold']
        require(kind in ('threshold','floor','majority_hull'),'Unexpected feature kind')
        require(kind!='majority_hull' or m==2*k-1,'Invalid majority')
        budgets.append(len(atom['sets'])*(m//k))
    coefficients=[];records=[]
    scale=lcm(2*D,(A/2).denominator);factor=scale//(2*D)
    require(len(proof['exact_controls'])==len(proof['multiplicities'])==9,'Wrong witness count')
    require(all(type(n) is int and n>0 for n in proof['multiplicities']) and sum(proof['multiplicities'])==11,'Wrong total multiplicity')
    for pose,mult in zip(proof['exact_controls'],proof['multiplicities']):
        t=F(pose['halfangle']);x,y=map(F,pose['center']);p,q=t.numerator,t.denominator
        C,S,R=q*q-p*p,2*p*q,q*q+p*p
        require(C*C+S*S==R*R and 0<=t<=1,'Invalid rational orientation')
        radius=A*(abs(C)+abs(S))/(2*R)
        require(radius<=x<=L-radius and radius<=y<=L-radius,'Parent violates containment')
        uv=[(factor*(C*(2*a-LD)+S*(2*b-LD)),factor*(-S*(2*a-LD)+C*(2*b-LD))) for a,b in points]
        half=int(A*scale/2)*R
        u=scale*(C*(x-L/2)+S*(y-L/2));v=scale*(-S*(x-L/2)+C*(y-L/2))
        den=lcm(u.denominator,v.denominator);U,V=int(u*den),int(v*den);H=half*den
        captured=[abs(U-a*den)<=H and abs(V-b*den)<=H for a,b in uv]
        row=[0]*len(budgets)
        for orbit,hit in zip(point_orbit,captured):row[orbit]+=int(hit)
        for j,atom in enumerate(c['charge_orbits'],start=len(c['point_orbits'])):
            kind,k=atom.get('kind','threshold'),atom['threshold']
            for group in atom['sets']:
                if kind=='majority_hull':
                    P=[uv[i] for i in group]
                    normals=[(1,0),(0,1)]+[(b[1]-a[1],a[0]-b[0]) for a,b in combinations(P,2)]
                    hit=True
                    for a,b in normals:
                        if not a and not b:continue
                        median=sorted(a*x0+b*y0 for x0,y0 in P)[len(P)//2]
                        if abs(a*U+b*V-median*den)>H*(abs(a)+abs(b)):
                            hit=False;break
                    row[j]+=int(hit)
                else:
                    h=sum(captured[i] for i in group)
                    row[j]+=h//k if kind=='floor' else int(h>=k)
        coefficients.append(row)
        records.append(dict(halfangle=str(t),center=list(map(str,(x,y))),multiplicity=mult,contained=True))
    total=[sum(n*row[i] for n,row in zip(proof['multiplicities'],coefficients)) for i in range(len(budgets))]
    excess=[v-b for v,b in zip(total,budgets)]
    require(max(excess)<=0,'A fixed-family budget is exceeded')
    out=dict(status='PASS_EXACT_FIXED_ROUND3_TRUE_CHARGE_FAMILY_BARRIER',
             source_sha256=sha256(raw).hexdigest(),witness_sha256=sha256(wraw).hexdigest(),
             exact_parent_side=str(A),target_side=str(L/A),variables=len(budgets),
             physical_sites=len(points),distinct_poses=len(records),total_pose_multiplicity=11,
             budgets=budgets,multiplicity_weighted_coefficients=total,exact_rows=coefficients,poses=records,
             maximum_budget_excess=max(excess),tight_columns=sum(v==b for v,b in zip(total,budgets)),
             new_packing_bound_proved=False,known_construction_optimality_proved=False,
             scope='Fixed source feature family only, arbitrary nonnegative weights. Poses need not be mutually disjoint; added features or sites can invalidate this obstruction.',
             seconds=time.monotonic()-start)
    path=Path(__file__).with_name('round3-true-barrier-audit.json');path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('budgets','multiplicity_weighted_coefficients','exact_rows','poses')},indent=2))


if __name__=='__main__':main()
