"""Freeze integer typed proposal after finite stress; geometry still unproved."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,math
import numpy as np
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).parent/'typed_masks'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    maskid=2045;repair=BASE/'mask2045-repair3.npz';stress=BASE/'mask2045-stress4.npz';meta=json.loads(repair.with_suffix('.json').read_text());smeta=json.loads(stress.with_suffix('.json').read_text());assert smeta['deficient_count']==0 and smeta['D4_deficient_after_half_margin_relaxation']==0
    z=np.load(repair);selected=z['selected_columns'];w=z['weights'];gamma=z['gamma'];D=10**8;relax=(11-meta['budget'])/22
    wi=np.array([math.ceil(float(x)*D) for x in w],np.int64);threshold=[math.floor(max(0,float(x)-relax)*D) for x in gamma]
    for i in range(8):threshold[i]=threshold[15-i]=min(threshold[i],threshold[15-i])
    capacities=z['budget'].astype(np.int64);budget=int(wi@capacities)
    coverfile=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json';cover=json.loads(coverfile.read_text());mask=cover['canonical_eleven_cell_subsets'][maskid]
    surplus=sum(threshold[i] for i in mask)-budget;assert surplus>0
    # Exact integer arithmetic over all retained numerically captured rows.
    q=z['typed_rows'].astype(np.int64)@wi;cells=z['typed_cells'];allslack=q-np.array(threshold,np.int64)[cells];assert allslack.min()>=0
    z2=np.load(stress);q2=z2['rows'].astype(np.int64)@wi;slack2=q2-np.array(threshold,np.int64)[z2['cells']];assert slack2.min()>=0
    source=ROOT/'research/true_catalogue/round6-cutround12-surplus-3.8754-full/proposal.json';old=json.loads(source.read_text());c={key:old[key] for key in ['L','coordinate_denominator','point_orbits','charge_orbits','floor_threshold_charge','majority_staircase_subdivisions'] if key in old}
    full=np.zeros(len(c['point_orbits'])+len(c['charge_orbits']),np.int64);full[selected]=wi
    for i,p in enumerate(c['point_orbits']):p[2]=int(full[i])
    for j,g in enumerate(c['charge_orbits']):g['weight']=int(full[len(c['point_orbits'])+j])
    c.update(A=meta['core_side'],weight_denominator=D,budget_units=budget,minimum_units=0,discovery_note='Typed-mask field proposal. No uniform minimum or global bound is claimed.')
    passing=[]
    for index,m in enumerate(cover['canonical_eleven_cell_subsets']):
        excess=sum(threshold[i] for i in m)-budget
        if excess>0:passing.append(dict(mask_index=index,mask=m,conditional_counting_surplus_units=excess))
    corners={0,3,12,15}
    corner_ids=[i for i,m in enumerate(cover['canonical_eleven_cell_subsets']) if len(corners.intersection(m))<=1]
    assert corner_ids==[r['mask_index'] for r in passing]
    packet=dict(status='FROZEN_FINITE_STRESS_PASSED_TYPED_PROPOSAL',certificate=c,cover_sha256=sha(coverfile),parent_Uplus=cover['side_upper'],fixed_homothety_B=meta['homothety_B'],discovery_core_side=meta['core_side'],discovery_core_epsilon='1/10000000000',mask_index=maskid,mask=mask,threshold_units=threshold,conditional_counting_surplus_units=surplus,threshold_sum_units=sum(threshold[i] for i in mask),half_margin_relaxation_per_cell_float=relax,threshold_halfturn_equalities_exact=True,source_proposal_sha256=sha(source),weight_source=dict(file=str(repair.relative_to(ROOT)),sha256=sha(repair)),fresh_stress_source=dict(file=str(stress.relative_to(ROOT)),sha256=sha(stress),poses=5000,tight_threshold_deficits=0,D4_relaxed_threshold_deficits=0),integer_finite_checks=dict(training_profiles=len(q),minimum_training_slack_units=int(allslack.min()),fresh_poses=len(q2),minimum_fresh_slack_units=int(slack2.min()),scope='Exact integer arithmetic on numerically captured coefficient tables, not an exact geometric replay.'),all_canonical_masks_with_conditional_counting_gap=len(passing),mask_arithmetic_file='mask2045-round3-mask-arithmetic.json',cells_outside_target_unverified=sorted(set(range(16))-set(mask)),cells_outside_target_and_its_halfturn=[0,15],positive_feature_orbits=int((wi>0).sum()),geometry_coverage=False,global_optimality=False,scope='Frozen proposal for exact conditional cell coverage. Passing finite stress does not exclude any continuum mask. All16 thresholds are retained, but no cell is marked geometrically verified.')
    output=BASE/'mask2045-round3-packet.json';output.write_text(json.dumps(packet,indent=2)+'\n')
    arithmetic=dict(status='EXACT_INTEGER_CONDITIONAL_MASK_ARITHMETIC',packet_sha256=sha(output),cover_sha256=sha(coverfile),mask_count=len(passing),masks=passing,corner_classification=dict(status='PASS_EXACT_SET_EQUALITY',corner_cells=sorted(corners),condition='At most one occupied corner cell',arithmetic_mask_indices=[r['mask_index'] for r in passing],combinatorial_mask_indices=corner_ids,all_canonical_masks_compared=len(cover['canonical_eleven_cell_subsets']),canonical_count=len(corner_ids),unquotiented_count=276,unquotiented_count_formula='C(12,11)+4*C(12,10)=12+264=276',conditional_structural_theorem='If all16 cell thresholds receive complete continuum coverage, every11-square packing in the Uplus container occupies at least two corner cells.'),required_geometry='Every occupied cell of a listed mask must satisfy its threshold on the full continuous domain before that mask is excluded.',continuum_masks_excluded=0)
    (BASE/'mask2045-round3-mask-arithmetic.json').write_text(json.dumps(arithmetic,indent=2)+'\n')
    print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=sha(output),budget_units=budget,threshold_units=threshold,surplus_units=surplus,positive_features=packet['positive_feature_orbits'],potential_masks=len(passing),minimum_integer_finite_slack=int(allslack.min()),minimum_fresh_slack=int(slack2.min()))))
if __name__=='__main__':main()
