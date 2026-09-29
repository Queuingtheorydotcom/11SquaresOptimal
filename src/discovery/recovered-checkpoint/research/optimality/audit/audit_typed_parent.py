#!/usr/bin/env python3
"""Independently recapture an exact deficient full parent from a typed pilot."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'research/stromquist'))
from fast_exact_parent import FastExactParentModel

def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    pilot=ROOT/'research/optimality/typed_coverage/mask2045-pilot.json'
    packet=ROOT/'research/optimality/deficit_geometry/typed_masks/mask2045-round3-packet.json'
    coverfile=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
    result=json.loads(pilot.read_text());proposal=json.loads(packet.read_text());cover=json.loads(coverfile.read_text())
    need(sha(packet)==result['packet_sha256'],'pilot proposal hash differs')
    failed=[r for r in result['records'] if r['status']=='REFUTED_BY_LEGAL_PARENT']
    need(len(failed)==1,'expected one exact parent refutation')
    record=failed[0];witness=record['parent_witness'];center=tuple(map(F,witness['center']));t=F(witness['half_angle'])
    parent=F(witness['side']);L=F(191,50);U=F(969271,250000)
    need(parent==L/U,'wrong parent normalization')
    c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);radius=parent*(c+s)/2
    slacks=[z-radius for z in center]+[L-radius-z for z in center]
    need(all(x>=0 for x in slacks),'parent not contained in fixed frame')
    normalized=tuple((x-L/2)/(parent*(U-1))+F(1,2) for x in center)
    need(all(0<=x<=1 for x in normalized),'center outside fixed cover box')
    sites=[tuple(map(F,r['center'])) for r in cover['cells']]
    cell=record['cell'];distance=lambda p:sum((a-b)**2 for a,b in zip(normalized,p))
    nearest_slacks=[distance(p)-distance(sites[cell]) for j,p in enumerate(sites) if j!=cell]
    need(min(nearest_slacks)>0,'parent center is not strictly in claimed Voronoi cell')
    model=FastExactParentModel(proposal['certificate']).at_side(parent)
    row=model.row(t,center);charge=sum(int(a)*int(b) for a,b in zip(row,model.weights))
    threshold=witness['required_units']
    need(charge==witness['charge_units']==99630778 and charge<threshold,'independent logical charge differs')
    need(threshold==max(proposal['threshold_units'][i] for i in proposal['mask'] if min(i,15-i)==cell),'required representative threshold differs')
    required_side=(2*max(abs(x-L/2) for x in center)+parent*(c+s))/parent
    alpha_lower=F(387708359002281417730789706010096270637645566846,10**47)
    receipt={'status':'PASS_INDEPENDENT_EXACT_TYPED_PARENT_REFUTATION','pilot_sha256':sha(pilot),
             'proposal_sha256':sha(packet),'cover_sha256':sha(coverfile),
             'cell':cell,'half_angle':str(t),'center':[str(x) for x in center],'parent_side':str(parent),
             'exact_charge_units':charge,'required_units':threshold,'deficit_units':threshold-charge,
             'minimum_frame_containment_slack':str(min(slacks)),
             'minimum_strict_Voronoi_distance_difference':str(min(nearest_slacks)),
             'smallest_concentric_unit_container_side_for_this_parent':str(required_side),
             'required_unit_side_approximate':float(required_side),
             'also_contained_at_exact_alpha_by_certified_lower_bound':required_side<=alpha_lower,
             'scope':'One individually legal parent refutes the specified conditional charge threshold. No compatible eleven-square packing and no mask exclusion is claimed.'}
    (HERE/'mask2045-parent-independent-audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['center','minimum_strict_Voronoi_distance_difference','smallest_concentric_unit_container_side_for_this_parent']},indent=2))

if __name__=='__main__':main()
