"""Exact recapture and exact closed-cell assignment of the first typed refuter."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,math,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).parent/'typed_masks'
sys.path.insert(0,str(ROOT/'research/stromquist'));sys.path.insert(0,str(ROOT/'research/majority_patches'))
from fast_exact_parent import FastExactParentModel
from true_parent import ExactParentModel
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    pilotfile=ROOT/'research/optimality/typed_coverage/mask2045-pilot.json';pilot=json.loads(pilotfile.read_text());parent=pilot['records'][-1]['parent_witness']
    packetfile=BASE/'mask2045-round3-packet.json';packet=json.loads(packetfile.read_text());c=packet['certificate'];L=F(c['L']);U=F(packet['parent_Uplus']);B=L/U;core=B-F(1,10**10)
    t=F(parent['half_angle']);center=tuple(map(F,parent['center']));assert F(parent['side'])==B
    exact=FastExactParentModel(c);full=exact.at_side(B);small=exact.at_side(core);weights=np.array(exact.weights,np.int64)
    parentrow=full.row(t,center);corerow=small.row(t,center);assert int(parentrow@weights)==parent['charge_units']==99630778
    slowc=dict(c);slowc['A']=str(B);slow=ExactParentModel(slowc);assert np.array_equal(parentrow,slow.row(t,center))
    slowc=dict(c);slowc['A']=str(core);slow=ExactParentModel(slowc);assert np.array_equal(corerow,slow.row(t,center));assert np.all(corerow<=parentrow)
    coverfile=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json';cover=json.loads(coverfile.read_text());sites=[tuple(map(F,cell['center'])) for cell in cover['cells']]
    selected=np.load(BASE/'mask2045-repair3.npz')['selected_columns'];rows=[];cells=[];poses=[];records=[]
    for swap in (0,1):
        for sx in (-1,1):
            for sy in (-1,1):
                vv=center[::-1] if swap else center;cc=tuple(v if sign==1 else L-v for sign,v in zip((sx,sy),vv))
                tt=t if sx*sy*(-1 if swap else 1)==1 else (1-t)/(1+t)
                rr=small.row(tt,cc);rp=full.row(tt,cc);assert np.array_equal(rr,corerow);assert np.array_equal(rp,parentrow)
                u=tuple((v-L/2)/B/(U-1)+F(1,2) for v in cc)
                dd=[sum((v-z)**2 for v,z in zip(u,site)) for site in sites];members=[k for k,d in enumerate(dd) if d==min(dd)]
                for k in members:
                    rows.append(rr[selected]);cells.append(k);poses.append([2*math.atan(float(tt)),*map(float,cc)])
                records.append(dict(swap=bool(swap),sx=sx,sy=sy,half_angle=str(tt),center=list(map(str,cc)),closed_cells=members,full_parent_charge_units=int(rp@weights),discovery_core_charge_units=int(rr@weights),all_feature_coefficients_D4_invariant=True))
    assert sorted(cells)==[1,2,4,7,8,11,13,14]
    output=BASE/'pilot1-exact-D4-captures';np.savez_compressed(output.with_suffix('.npz'),typed_rows=np.array(rows,np.uint8),typed_cells=np.array(cells,np.int64),poses=np.array(poses),full_parent_row=parentrow,discovery_core_row=corerow,selected_columns=selected)
    report=dict(status='PASS_EXACT_REFUTER_CAPTURE_AND_D4_CLOSED_CELL_ASSIGNMENT',pilot_sha256=sha(pilotfile),packet_sha256=sha(packetfile),cover_sha256=sha(coverfile),parent_side=str(B),discovery_core_side=str(core),parent_charge_units=int(parentrow@weights),discovery_core_charge_units=int(corerow@weights),independent_exact_models_agree=True,all_eight_edge_cells_refuted_under_original_threshold=True,refuted_cells=sorted(cells),records=records,scope='Exact legal individual parents and strict cores, with exact D4 invariance and rational cell membership. These eight poses are not asserted to form a simultaneous packing.')
    output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='records'}))
if __name__=='__main__':main()
