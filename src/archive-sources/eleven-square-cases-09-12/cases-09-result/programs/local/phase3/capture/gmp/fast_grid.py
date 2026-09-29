"""Local adapter for the archived exact inner-grid module."""
import inner_grid as _base
from gmpy2 import mpq

_base.F = mpq
_base.geom.F = mpq

geom = _base.geom
inner_grid = _base.inner_grid
