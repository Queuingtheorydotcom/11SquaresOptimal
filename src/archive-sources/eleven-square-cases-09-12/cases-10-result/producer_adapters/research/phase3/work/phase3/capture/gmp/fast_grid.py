"""Exact GMP rational adapter for supplied inner-grid producer."""
from pathlib import Path
import sys
from gmpy2 import mpq

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'phase2/hull'))
import inner_grid as _grid

_grid.F = mpq
_grid.geom.F = mpq
geom = _grid.geom
inner_grid = _grid.inner_grid
