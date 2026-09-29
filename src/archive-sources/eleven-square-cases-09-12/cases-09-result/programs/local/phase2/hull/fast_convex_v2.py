"""Local adapter exposing the archived exact convex-cover implementation.

The supplied case-tools archive omits the original fast_convex_v2 module.
This adapter uses the bundled pure-Python exact rational functions instead.
Any proof source produced with it still requires independent v9 replay.
"""
import convex_cover as _base
from gmpy2 import mpq

_base.F = mpq
from convex_cover import *
