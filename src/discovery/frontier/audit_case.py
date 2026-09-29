"""Use the frozen independent checker with native exact rational arithmetic."""
from pathlib import Path
import os
import runpy
import sys
import gmpy2  # Preload the native extension; archive contains a Linux binary.

ROOT = Path(__file__).resolve().parents[1] / 'phase3'
os.environ['ELEVEN_RATIONAL_BACKEND'] = 'gmp'
os.environ['ELEVEN_PACKING_ROOT'] = str(ROOT / 'current')
checker = ROOT / 'work/phase3/hull/audit_capture_v9.py'
sys.path.insert(0, str(checker.parent))
sys.path.insert(0, str(ROOT / 'work/phase2/hull'))
sys.argv[0] = str(checker)
runpy.run_path(str(checker), run_name='__main__')
