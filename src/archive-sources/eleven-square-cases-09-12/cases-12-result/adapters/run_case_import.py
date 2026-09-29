"""Use the exact GMP adapters when duplicate legacy module names are present."""
import importlib.util
import runpy
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ADAPTERS = BASE / 'research/phase3/work/phase3/capture/gmp'

for name in ('fast_convex_v2', 'fast_grid'):
    spec = importlib.util.spec_from_file_location(name, ADAPTERS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

script = BASE / 'research/frontier/run_case.py'
sys.argv[0] = str(script)
runpy.run_path(str(script), run_name='__main__')
