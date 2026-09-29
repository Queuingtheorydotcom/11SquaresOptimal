"""Independently check the legal-parent witness by direct logical charges."""
from copy import deepcopy
from fractions import Fraction as F
from math import lcm
from pathlib import Path
import argparse,hashlib,json
from exact_mixed import expand
from majority_geometry import median_strips,require

def verify(witness_path,output):
    root=Path(__file__).resolve().parents[2]
    witness=json.loads(Path(witness_path).read_text())
    raw=(root/witness['certificate']).read_bytes();c=json.loads(raw)
    require(hashlib.sha256(raw).hexdigest()==witness['certificate_sha256'],'Certificate changed')
    proxy=deepcopy(c)
    for atom in proxy['charge_orbits']:
        if atom.get('kind')=='majority_hull':atom['kind']='threshold'
    points,pw,unused1,unused2,D=expand(proxy)
    t=F(witness['halfangle']);p,q=t.numerator,t.denominator
    C=q*q-p*p;S=2*p*q;R=q*q+p*p;A=F(witness['parent_side']);L=F(c['L'])
    require(A==F(c['A']) and C*C+S*S==R*R,'Parent shape mismatch')
    x,y=map(F,witness['center']);radius=A*(abs(C)+abs(S))/(2*R)
    require(radius<=x<=L-radius and radius<=y<=L-radius,'Parent is not contained')
    scale=lcm(2*D,(A/2).denominator,x.denominator,y.denominator)
    LD=int(L*D);factor=scale//(2*D);half=int(A*scale/2)*R
    uv=[(C*(2*a-LD)*factor+S*(2*b-LD)*factor,
         -S*(2*a-LD)*factor+C*(2*b-LD)*factor) for a,b in points]
    u=scale*(C*(x-L/2)+S*(y-L/2));v=scale*(-S*(x-L/2)+C*(y-L/2))
    require(u.denominator==v.denominator==1,'Noninteger witness projection')
    u,v=int(u),int(v)
    captured=[abs(u-a)<=half and abs(v-b)<=half for a,b in uv]
    point_charge=sum(w for w,hit in zip(pw,captured) if hit);floor_charge=majority_charge=0
    for atom in c['charge_orbits']:
        w=atom['weight'];k=atom['threshold'];kind=atom.get('kind','threshold')
        for group in atom['sets']:
            if kind=='majority_hull':
                require(len(group)==2*k-1,'Invalid majority cardinality')
                majority_charge+=w*all(lo<=a*u+b*v<=hi for a,b,lo,hi in
                                      median_strips([uv[i] for i in group],half))
            elif kind=='floor':floor_charge+=w*(sum(captured[i] for i in group)//k)
            else:raise ValueError('Unexpected feature kind in this witness')
    charge=point_charge+floor_charge+majority_charge
    require(charge==witness['true_charge_units']<c['minimum_units'],'No true-charge deficit')
    out=dict(status='PASS_EXACT_LEGAL_PARENT_TRUE_CHARGE_COUNTEREXAMPLE',
             contained_parent=True,point_units=point_charge,floor_units=floor_charge,
             true_majority_units=majority_charge,total_units=charge,
             threshold_units=c['minimum_units'],deficit_units=c['minimum_units']-charge,
             threshold_deficit_from_budget_units=c['budget_units']-11*charge,
             scope='Deficient pose for these weights only; not a packing or a universal method barrier')
    Path(output).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--witness',type=Path,default=Path(__file__).with_name('majority-legal-parent-witness.json'))
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('majority-parent-witness-verification.json'))
    args=parser.parse_args();verify(args.witness,args.output)

if __name__=='__main__':main()
