"""Exact conditional propagation with separately certified necessary D4 cuts.

The unchanged independent hull auditor sees these as branch antecedents.
A separate necessity adapter must discharge them before counting an exclusion.
"""
from pathlib import Path
import argparse,hashlib,json,sys

if not __debug__:raise SystemExit('Assertions must remain enabled.')

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'phase3'
sys.path.insert(0,str(HERE.parent/'global-math'))
import overlay_field_halfplanes_v2 as overlay
sys.path.insert(0,str(ROOT/'work/phase3/generic'))
import generic_pose_engine_v5 as seed_engine
sys.path.insert(0,str(ROOT/'work/phase3/capture'))
import capture_engine_self_v1 as engine

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('mask',type=int)
    ap.add_argument('--seconds',type=float,default=120)
    ap.add_argument('--bins',type=int,default=64)
    ap.add_argument('--partners',type=int,default=0)
    ap.add_argument('--passes',type=int,default=30)
    a=ap.parse_args()
    out=HERE/f'mask{a.mask}-overlay-v1.json'
    assert not out.exists(),'Keep all previous proof objects immutable'
    constraints=overlay.necessary_constraints(a.mask)
    overlay.verify_constraints(a.mask,constraints)
    state=seed_engine.seed_state(a.mask,a.bins,out.with_name(out.stem+'-seed.json'))
    state['constraints']=[dict(owner=i,normal=list(n),upper_field=h) for i,n,h in constraints]
    provenance=dict(status='CONDITIONAL_PROPAGATION_INPUTS_ONLY',mask_index=a.mask,
        source_hulls_sha256=hashlib.sha256(overlay.HULLS.read_bytes()).hexdigest(),
        adapter_sha256=hashlib.sha256(Path(overlay.__file__).read_bytes()).hexdigest(),
        baseline_sha256='bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545',
        constraints=state['constraints'],global_optimality_proved=False)
    out.with_name(out.stem+'-necessity-inputs.json').write_text(json.dumps(provenance,default=str,indent=2)+'\n')
    priority=[i for i in [5,6,9,10,1,2] if i in state['mask']][:2]
    engine.run_node(state,out,a.seconds,a.passes,priority,True,out.stem,None,a.partners)

if __name__=='__main__':main()
