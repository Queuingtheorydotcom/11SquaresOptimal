"""Independent exact ceiling-weight provenance; not a placement proof."""
from fractions import Fraction as F
from hashlib import sha256
import argparse
import io
import json
from pathlib import Path
import numpy as np


def audit(certificate,checkpoint,output):
    raw=Path(certificate).read_bytes();c=json.loads(raw)
    weights_raw=Path(checkpoint).read_bytes()
    with np.load(io.BytesIO(weights_raw)) as archive:
        weights=archive['weights'].copy()
    stored=[row[2] for row in c['point_orbits']]+[a['weight'] for a in c['charge_orbits']]
    if weights.ndim!=1 or len(weights)!=len(stored):raise ValueError('Weight vector order/length mismatch')
    if not np.all(np.isfinite(weights)) or np.min(weights)<0:raise ValueError('Expected finite nonnegative weights')
    D=c['weight_denominator']
    if type(D) is not int or D<=0:raise ValueError('Invalid weight denominator')
    for i,(weight,actual) in enumerate(zip(weights,stored)):
        if type(actual) is not int:raise ValueError('Nonintegral certificate weight')
        rational=F(float(weight))*D
        expected=-((-rational.numerator)//rational.denominator)
        if actual!=expected:raise ValueError('Exact ceiling mismatch at variable '+str(i))
    L=F(c['L']);Dcoord=c['coordinate_denominator'];LD=int(L*Dcoord);budget=0
    for x,y,w in c['point_orbits']:
        orbit={(a,b) for u,v in ((x,y),(y,x)) for a in (u,LD-u) for b in (v,LD-v)}
        budget+=len(orbit)*w
    for atom in c['charge_orbits']:
        capacity=1 if atom.get('kind') in ('edge_or','convex_clique','majority_hull') else len(atom['sets'][0])//atom['threshold']
        budget+=capacity*len(atom['sets'])*atom['weight']
    if budget!=c['budget_units']:raise ValueError('Independent budget differs')
    if 11*c['minimum_units']<=budget:raise ValueError('Insufficient strict required charge')
    result=dict(status='PASS_EXACT_CEILING_WEIGHT_AND_BUDGET_AUDIT',
                certificate_sha256=sha256(raw).hexdigest(),checkpoint_sha256=sha256(weights_raw).hexdigest(),
                checked_weights=len(stored),positive_weights=sum(w>0 for w in stored),
                exact_binary_float_ceiling=True,weight_denominator=D,budget_units=budget,
                required_units=c['minimum_units'],required_counting_surplus_units=11*c['minimum_units']-budget,
                all_charge_sweeps_checked=False,new_bound_proved=False,
                scope='Weight provenance and independent budget only; feature, containment, and full charge verification are separate')
    Path(output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('certificate',type=Path);p.add_argument('checkpoint',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    audit(a.certificate,a.checkpoint,a.output)
