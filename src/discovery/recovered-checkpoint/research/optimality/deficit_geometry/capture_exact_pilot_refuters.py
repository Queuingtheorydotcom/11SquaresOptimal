"""Exact full-family captures for four typed-pilot refuters and a corner control."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,hashlib,math
import numpy as np
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).parent/'typed_masks'
sys.path.insert(0,str(ROOT/'research/stromquist'));sys.path.insert(0,str(ROOT/'research/majority_patches'))
from fast_exact_parent import FastExactParentModel
from true_parent import ExactParentModel
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    packetfile=BASE/'mask2045-round3-packet.json';packet=json.loads(packetfile.read_text());c=packet['certificate'];L=F(c['L']);U=F(packet['parent_Uplus']);B=L/U;core=B-F(1,10**10)
    exact=FastExactParentModel(c);parentmodel=exact.at_side(B);coremodel=exact.at_side(core);weights=np.array(exact.weights,np.int64)
    pc=dict(c);pc['A']=str(B);slowparent=ExactParentModel(pc);pc=dict(c);pc['A']=str(core);slowcore=ExactParentModel(pc)
    coverfile=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json';cover=json.loads(coverfile.read_text());sites=[tuple(map(F,z['center'])) for z in cover['cells']]
    paths=['mask2045-pilot.json','mask2045-cell5-pilot.json','mask2045-cell6-pilot.json','mask2045-relaxed1-cell1.json'];fixtures=[]
    for name in paths:
        p=ROOT/'research/optimality/typed_coverage'/name;r=json.loads(p.read_text());record=r['records'][-1];assert record['status']=='REFUTED_BY_LEGAL_PARENT'
        fixtures.append(dict(source=str(p.relative_to(ROOT)),source_sha256=sha(p),reported_cell=record['cell'],**record['parent_witness']))
    fixtures.append(dict(source='additional_exact_axis_aligned_corner_control',half_angle='0',center=[str(B/2),str(B/2)],side=str(B)))
    selected=np.load(BASE/'mask2045-repair3.npz')['selected_columns'];typed=[];cells=[];poses=[];allrecords=[];parentrows=[];corerows=[];upper=[None]*16
    for fi,fixture in enumerate(fixtures):
        t=F(fixture['half_angle']);center=tuple(map(F,fixture['center']));assert F(fixture['side'])==B
        prow=parentmodel.row(t,center);crow=coremodel.row(t,center);charge=int(prow@weights)
        if 'charge_units' in fixture:assert charge==fixture['charge_units']
        assert np.array_equal(prow,slowparent.row(t,center));assert np.array_equal(crow,slowcore.row(t,center));assert np.all(crow<=prow);slowparent.cache.clear();slowcore.cache.clear()
        parentrows.append(prow);corerows.append(crow);images=[]
        for swap in (0,1):
            for sx in (-1,1):
                for sy in (-1,1):
                    vv=center[::-1] if swap else center;cc=tuple(v if sign==1 else L-v for sign,v in zip((sx,sy),vv));tt=t if sx*sy*(-1 if swap else 1)==1 else (1-t)/(1+t)
                    rp=parentmodel.row(tt,cc);rr=coremodel.row(tt,cc);assert np.array_equal(rp,prow);assert np.array_equal(rr,crow)
                    u=tuple((v-L/2)/B/(U-1)+F(1,2) for v in cc);dd=[sum((v-z)**2 for v,z in zip(u,site)) for site in sites];members=[i for i,d in enumerate(dd) if d==min(dd)]
                    for k in members:
                        typed.append(rr[selected]);cells.append(k);poses.append([2*math.atan(float(tt)),*map(float,cc)]);upper[k]=charge if upper[k] is None else min(upper[k],charge)
                    images.append(dict(swap=bool(swap),sx=sx,sy=sy,half_angle=str(tt),center=list(map(str,cc)),closed_cells=members))
        allrecords.append(dict(fixture=fixture,full_parent_charge_units=charge,strict_core_charge_units=int(crow@weights),independent_exact_models_agree=True,full_coefficient_D4_invariance=True,D4_closed_cells=sorted({k for image in images for k in image['closed_cells']}),images=images))
    assert all(x is not None for x in upper)
    capsum=sum(upper[k] for k in packet['mask']);M=c['budget_units']
    output=BASE/'pilot1234-exact-D4-captures';np.savez_compressed(output.with_suffix('.npz'),typed_rows=np.array(typed,np.uint8),typed_cells=np.array(cells,np.int64),poses=np.array(poses),full_parent_rows=np.array(parentrows),discovery_core_rows=np.array(corerows),selected_columns=selected)
    report=dict(status='PASS_EXACT_TYPED_REFUTERS_AND_CORNER_CONTROL',packet_sha256=sha(packetfile),cover_sha256=sha(coverfile),parent_side=str(B),strict_core_side=str(core),pilot_refuter_count=4,additional_corner_control=True,typed_D4_rows=len(typed),records=allrecords,fixed_weight_cell_threshold_upper_bounds=upper,target_maximum_threshold_sum_from_exact_parents=capsum,fixed_weight_budget_units=M,target_maximum_possible_counting_surplus=capsum-M,fixed_weight_typed_threshold_repair_impossible=bool(capsum<=M),scope='Each entry is an independently legal parent, not a simultaneous packing. Any universal cell threshold for this unchanged nonnegative monotone field is bounded above by these exact parent charges; inscribed cores cannot exceed the parent charge. Negative maximum surplus rules out repairing this field by threshold changes alone.')
    output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='records'}))
if __name__=='__main__':main()
