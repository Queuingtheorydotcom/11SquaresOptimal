"""Exact GMP rational adapter for the supplied convex-cover producer.

The original fast producer module was absent from the handoff. This local
adapter uses the same exact polygon routines included with the handoff.
The independent v9 checker remains the acceptance criterion.
"""
from pathlib import Path
import sys
from gmpy2 import mpq

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'phase2/hull'))
import convex_cover as _base

_base.F = mpq
_base.L = mpq(191, 50)
L = _base.L
hull = _base.hull
rows = _base.rows
clip_linear = _base.clip_linear
twice_area = _base.twice_area
convex_difference = _base.convex_difference
row_geometry = _base.row_geometry
interval_cover = _base.interval_cover
