"""Freeze the one exact-refuter repair as finite-only; no fresh stress claim."""
from pathlib import Path
import json,hashlib,copy,math
import numpy as np
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).parent/'typed_masks'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    weightsfile=BASE/'mask2045-repair4.npz';z=np.load(weightsfile);meta=json.loads(weightsfile.with_suffix('.json').read_text());assert meta['exact_additional_typed_rows']==40
    original=BASE/'mask2045-round3-packet.json';old=json.loads(original.read_text());D=10**8;w=np.array([math.ceil(float(v)*D) for v in z['weights']],np.int64);selected=z['selected_columns'];relax=(11-meta['budget'])/22
    gamma=[math.floor(max(0,float(v)-relax)*D) for v in z['gamma']]
    for i in range(8):gamma[i]=gamma[15-i]=min(gamma[i],gamma[15-i])
    budget=int(w@z['budget'].astype(np.int64));mask=old['mask'];surplus=sum(gamma[i] for i in mask)-budget;assert surplus>0
    score=z['typed_rows'].astype(np.int64)@w;slack=score-np.array(gamma,np.int64)[z['typed_cells']];assert slack.min()>=0
    c=copy.deepcopy(old['certificate']);full=np.zeros(len(c['point_orbits'])+len(c['charge_orbits']),np.int64);full[selected]=w
    for i,p in enumerate(c['point_orbits']):p[2]=int(full[i])
    for j,g in enumerate(c['charge_orbits']):g['weight']=int(full[len(c['point_orbits'])+j])
    c['budget_units']=budget;c['discovery_note']='One changed-weight repair after exact refuters. Finite profiles only; no fresh stress or continuum verification.'
    coverfile=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json';cover=json.loads(coverfile.read_text());passing=[]
    for i,m in enumerate(cover['canonical_eleven_cell_subsets']):
        excess=sum(gamma[k] for k in m)-budget
        if excess>0:passing.append(dict(mask_index=i,mask=m,conditional_counting_surplus_units=excess))
    corners={0,3,12,15};cornerids=[i for i,m in enumerate(cover['canonical_eleven_cell_subsets']) if len(corners.intersection(m))<=1];assert cornerids==[r['mask_index'] for r in passing]
    fixture=BASE/'pilot1234-exact-D4-captures.npz'
    packet=dict(status='FINITE_EXACT_REFUTER_REPAIR_NOT_FRESH_STRESS_TESTED',certificate=c,cover_sha256=sha(coverfile),parent_Uplus=cover['side_upper'],fixed_homothety_B=meta['homothety_B'],discovery_core_side=meta['core_side'],discovery_core_epsilon='1/10000000000',mask_index=2045,mask=mask,threshold_units=gamma,threshold_sum_units=sum(gamma[i] for i in mask),conditional_counting_surplus_units=surplus,threshold_halfturn_equalities_exact=True,half_margin_relaxation_per_cell_float=relax,positive_feature_orbits=int((w>0).sum()),source_repair=dict(file=weightsfile.name,sha256=sha(weightsfile),report_sha256=sha(weightsfile.with_suffix('.json'))),exact_refuter_profiles=dict(file=fixture.name,sha256=sha(fixture),count=40),finite_integer_arithmetic=dict(retained_profiles=len(score),minimum_slack_units=int(slack.min()),scope='Exact integer arithmetic on retained capture vectors, most generated numerically; the40 explicit refuter/control rows have independent exact capture.'),fresh_stress_tested=False,geometry_coverage=False,continuum_masks_excluded=0,global_optimality=False,all_canonical_masks_with_conditional_counting_gap=len(passing),mask_arithmetic_file='mask2045-round4-mask-arithmetic.json',scope='One changed-weight repair has positive finite margin after adding all four exact pilot refuters and a corner control. No fresh stress or exact continuum check of these weights has run. This is an unverified geometric proposal, not a mask exclusion.')
    output=BASE/'mask2045-round4-finite-packet.json';output.write_text(json.dumps(packet,indent=2)+'\n')
    arithmetic=dict(status='EXACT_INTEGER_CONDITIONAL_MASK_ARITHMETIC',packet_sha256=sha(output),mask_count=len(passing),masks=passing,exact_equivalence_to_at_most_one_corner=True,corner_cells=sorted(corners),all_canonical_masks_compared=2184,continuum_masks_excluded=0)
    (BASE/'mask2045-round4-mask-arithmetic.json').write_text(json.dumps(arithmetic,indent=2)+'\n')
    print(json.dumps(dict(file=str(output.relative_to(ROOT)),sha256=sha(output),budget_units=budget,surplus_units=surplus,threshold_units=gamma,minimum_retained_integer_slack=int(slack.min()),potential_masks=len(passing))))
if __name__=='__main__':main()
