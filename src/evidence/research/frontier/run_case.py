"""Run unchanged exact engines on a fresh remaining case; audit separately."""
from pathlib import Path
import argparse
import json
import sys

if not __debug__:raise SystemExit('Assertions must remain enabled.')

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / 'phase3'
sys.path.insert(0, str(ROOT / 'work/phase3/generic'))
import generic_pose_engine_v5 as seed_engine
sys.path.insert(0, str(ROOT / 'work/phase3/capture'))
import capture_engine_self_v1 as engine

def main():
    p = argparse.ArgumentParser()
    p.add_argument('mask', type=int)
    p.add_argument('--seconds', type=float, default=120)
    p.add_argument('--bins', type=int, default=64)
    p.add_argument('--partners', type=int, default=0)
    p.add_argument('--passes', type=int, default=30)
    a = p.parse_args()
    out = HERE / f'mask{a.mask}-self-v1.json'
    if out.exists():
        raise FileExistsError(out)
    known = json.loads((ROOT / 'work/phase3/audit/overall-union-snapshot-bc3563a0c995.json').read_text())
    assert a.mask in known['remaining_canonical_mask_indices']
    assert a.mask not in [438,999,1462,1659,1383,1839]
    state = seed_engine.seed_state(a.mask, a.bins, out.with_name(out.stem+'-seed.json'))
    priority = [i for i in [5,6,9,10,1,2] if i in state['mask']][:2]
    engine.run_node(state, out, a.seconds, a.passes, priority, True, out.stem,
                    None, a.partners)

if __name__ == '__main__':
    main()
