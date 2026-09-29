"""Exact rational adapter for supplied strict polygon-core producer."""
from pathlib import Path
import sys
from gmpy2 import mpq

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'phase2/hull'))
import convex_cover as base
base.F = mpq
base.L = mpq(191, 50)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import polygon_core as _core
_core.F = mpq
_core.L = base.L

polygon_core = _core.polygon_core
interval_cover = _core.interval_cover
