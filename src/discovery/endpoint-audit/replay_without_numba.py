"""Replay unchanged verifier with its independent direct NumPy sweep backend.

The package imports numba solely as a performance decorator. This wrapper
turns that decorator into identity, then selects integer_sweep.accumulate's
existing direct=True path, which updates a full integer array instead of a
segment tree. No source file or geometric predicate is modified.
"""
import argparse
import functools
import importlib.util
import json
from pathlib import Path
import sys
import types

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent / 'eleven-square-handoff/six-case'
VERIFIER = PACKAGE / 'checkpoint_extract/research/optimality/asymmetric_coverage/verify.py'

numba = types.ModuleType('numba')
numba.njit = lambda f: f
sys.modules['numba'] = numba
spec = importlib.util.spec_from_file_location('asymmetric_endpoint', VERIFIER)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
import integer_sweep

direct_sweep = functools.partial(integer_sweep.accumulate, direct=True)
verifier.accumulate = direct_sweep
verifier.typed.accumulate = direct_sweep

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--packet', type=Path, default=PACKAGE / 'endpoint/mask800_r35_ext195_tenowner.json')
    p.add_argument('--output', type=Path, default=HERE / 'tenowner-direct-fresh-replay.json')
    p.add_argument('--cells')
    p.add_argument('--bins', type=int, default=32)
    p.add_argument('--max-depth', type=int, default=16)
    p.add_argument('--max-rows', type=int, default=8000)
    p.add_argument('--seconds', type=float, default=600)
    p.add_argument('--patch-nodes', type=int, default=5000)
    args = p.parse_args()
    verifier.run(args)
