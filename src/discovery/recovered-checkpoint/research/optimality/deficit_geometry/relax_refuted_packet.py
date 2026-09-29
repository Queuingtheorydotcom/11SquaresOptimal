"""Preserve weights and lower the two refuted half-turn partner thresholds."""
from pathlib import Path
import json,hashlib,copy,argparse
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).parent/'typed_masks'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--all-edge',action='store_true');args=ap.parse_args()
    source=BASE/'mask2045-round3-packet.json';packet=json.loads(source.read_text());old=copy.deepcopy(packet)
    proof=ROOT/'research/optimality/typed_coverage/mask2045-pilot.json';pilot=json.loads(proof.read_text());witness=pilot['records'][-1]['parent_witness'];assert pilot['records'][-1]['status']=='REFUTED_BY_LEGAL_PARENT'
    lowered=[1,2,4,7,8,11,13,14] if args.all_edge else [1,14]
    for i in lowered:packet['threshold_units'][i]=99500000
    gamma=packet['threshold_units'];M=packet['certificate']['budget_units'];mask=packet['mask']
    packet.update(status='UNVERIFIED_THRESHOLD_RELAXATION_OF_REFUTED_PROPOSAL',threshold_sum_units=sum(gamma[i] for i in mask),conditional_counting_surplus_units=sum(gamma[i] for i in mask)-M,mask_arithmetic_file='mask2045-round3-relaxed1-mask-arithmetic.json',replaces_refuted_packet=dict(file=source.name,sha256=sha(source),exact_refutation_report=str(proof.relative_to(ROOT)),report_sha256=sha(proof),refuted_cell=1,full_parent_charge_units=witness['charge_units'],old_threshold_units=old['threshold_units'][1],new_threshold_units=gamma[1],new_witness_slack_units=witness['charge_units']-gamma[1]),preserves_feature_weights_exactly=True,scope='The original candidate was exactly refuted despite passing finite stress. This alternate preserves every weight and lowers only gamma1 and gamma14. Existing accepted geometry remains mathematically valid under lowered thresholds, but no completed cell/mask coverage is asserted here.')
    if args.all_edge:
        fixture=BASE/'pilot1-exact-D4-captures.json';f=json.loads(fixture.read_text());assert f['refuted_cells']==lowered
        packet['scope']='The original candidate was exactly refuted despite passing finite stress. This alternate preserves every weight and lowers all8 edge thresholds, including every exactly verified D4 image of the refuter. Existing accepted geometry remains mathematically valid under lowered thresholds; complete coverage is still required.'
        packet['mask_arithmetic_file']='mask2045-round3-relaxed-edge-mask-arithmetic.json'
        packet['exact_D4_refutation_fixture']=dict(file=fixture.name,sha256=sha(fixture))
    packet['additionally_lowered_threshold_cells']=lowered
    assert packet['certificate']==old['certificate'];assert packet['conditional_counting_surplus_units']==(12062269 if args.all_edge else 18276454)
    coverfile=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json';cover=json.loads(coverfile.read_text());masks=[]
    for i,m in enumerate(cover['canonical_eleven_cell_subsets']):
        surplus=sum(gamma[k] for k in m)-M
        if surplus>0:masks.append(dict(mask_index=i,mask=m,conditional_counting_surplus_units=surplus))
    corners={0,3,12,15};ids=[i for i,m in enumerate(cover['canonical_eleven_cell_subsets']) if len(corners.intersection(m))<=1];assert ids==[r['mask_index'] for r in masks]
    packet['all_canonical_masks_with_conditional_counting_gap']=len(masks)
    output=BASE/('mask2045-round3-relaxed-edge-packet.json' if args.all_edge else 'mask2045-round3-relaxed1-packet.json');output.write_text(json.dumps(packet,indent=2)+'\n')
    arithmetic=dict(status='EXACT_INTEGER_CONDITIONAL_MASK_ARITHMETIC',packet_sha256=sha(output),mask_count=len(masks),masks=masks,corner_classification=dict(status='PASS_EXACT_SET_EQUALITY',corner_cells=sorted(corners),condition='At most one occupied corner cell',arithmetic_mask_indices=[r['mask_index'] for r in masks],combinatorial_mask_indices=ids,all_canonical_masks_compared=2184),continuum_masks_excluded=0)
    (BASE/packet['mask_arithmetic_file']).write_text(json.dumps(arithmetic,indent=2)+'\n')
    print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=sha(output),remaining_surplus_units=packet['conditional_counting_surplus_units'],new_witness_slack_units=witness['charge_units']-gamma[1],potential_masks=len(masks))))
if __name__=='__main__':main()
