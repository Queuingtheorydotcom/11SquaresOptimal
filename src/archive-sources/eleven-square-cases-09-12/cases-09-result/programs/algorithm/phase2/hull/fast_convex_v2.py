"""Portable exact geometry adapter for the omitted native producer module.

All operations delegate to the bundled rational implementation.  The v9
checker independently replays the geometry and binds this file by SHA-256.
"""

from convex_cover import (
    L,
    F,
    cs,
    hull,
    rows,
    clip_linear,
    convex_difference,
    twice_area,
    row_geometry,
    interval_cover,
)
