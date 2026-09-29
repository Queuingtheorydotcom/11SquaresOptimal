"""Exact subthreshold generic-cell extraction for majority_mixed.geometry.

The sweep uses integer charges while event coordinates may be rational. Every
raw cell retains all rectangle event boundaries, including boundaries at which
different feature changes cancel in the total charge. Only indices enter the
Numba kernel. Coordinates returned by iter_low_cells are unchanged from meta.

Taking closures of these generic cells gives a safe outer cover of low TRUE
logical charge inside the legal domain: the true charge is upper
semicontinuous, and the surrogate is a lower bound at generic legal points.
Surrogate rectangle sums on shared boundaries must not be used as true charge.
"""
from dataclasses import dataclass
from typing import Iterator
import numpy as np
from numba import njit


def require(value, message):
    if not value:
        raise ValueError(message)


@njit
def _update(mn, mx, lazy, k, a, b, lo, hi, weight):
    if hi <= a or b <= lo:
        return
    if lo <= a and b <= hi:
        mn[k] += weight
        mx[k] += weight
        lazy[k] += weight
        return
    mid = (a+b)//2
    _update(mn, mx, lazy, 2*k, a, mid, lo, hi, weight)
    _update(mn, mx, lazy, 2*k+1, mid, b, lo, hi, weight)
    mn[k] = lazy[k] + min(mn[2*k], mn[2*k+1])
    mx[k] = lazy[k] + max(mx[2*k], mx[2*k+1])


@njit
def _collect(mn, mx, lazy, k, a, b, lo, hi, carry, cutoff, found):
    if hi <= a or b <= lo or carry+mn[k] >= cutoff:
        return
    if mn[k] == mx[k]:
        found.append((max(a, lo), min(b, hi), carry+mn[k]))
        return
    mid = (a+b)//2
    _collect(mn, mx, lazy, 2*k, a, mid, lo, hi, carry+lazy[k], cutoff, found)
    _collect(mn, mx, lazy, 2*k+1, mid, b, lo, hi, carry+lazy[k], cutoff, found)


@njit
def _extract(nv, evindex, atomindex, sign, ylo, yhi, weights, first, last, cutoff):
    n = 1
    while n < nv:
        n *= 2
    mn = np.zeros(2*n, np.int64)
    mx = np.zeros(2*n, np.int64)
    lazy = np.zeros(2*n, np.int64)
    p = 0
    out = [(np.int64(-1), np.int64(-1), np.int64(-1), np.int64(-1))]
    out.pop()
    for i in range(len(first)):
        while p < len(evindex) and evindex[p] == i:
            j = atomindex[p]
            _update(mn, mx, lazy, 1, 0, n, ylo[j], yhi[j], sign[p]*weights[j])
            p += 1
        if first[i] >= 0:
            found = [(np.int64(-1), np.int64(-1), np.int64(-1))]
            found.pop()
            _collect(mn, mx, lazy, 1, 0, n, first[i], last[i], np.int64(0), cutoff, found)
            for lo, hi, z in found:
                out.append((i, lo, hi, z))
    return out


@dataclass
class LowCells:
    """Compact exact sweep result; generic cells are expanded lazily."""
    runs: list
    xe: list
    ye: list
    cutoff: int
    total_generic_cells: int

    @property
    def stats(self):
        return {
            "cutoff_units": self.cutoff,
            "minimum_below_cutoff_units": min((int(r[3]) for r in self.runs), default=None),
            "low_run_count": len(self.runs),
            "low_generic_cells": sum(int(hi-lo) for i, lo, hi, z in self.runs),
            "total_generic_cells": self.total_generic_cells,
            "queried_cell_domain": "Conservative slab cover; clip rectangles to meta.poly before patching",
        }

    def iter_cells(self) -> Iterator[tuple]:
        """Yield (x0,x1,y0,y1,z) in exact projected lattice coordinates.

        z is constant on the OPEN rectangle. Its closure is used for the
        subsequent exact polygon patch; z need not hold on its boundary.
        """
        for i, lo, hi, z in self.runs:
            for j in range(lo, hi):
                yield (self.xe[i], self.xe[i+1], self.ye[j], self.ye[j+1], int(z))

    def iter_indexed_cells(self) -> Iterator[tuple]:
        """Yield (x_index,y_index,x0,x1,y0,y1,z), with stable grid indices."""
        for i, lo, hi, z in self.runs:
            for j in range(lo, hi):
                yield (int(i), int(j), self.xe[i], self.xe[i+1],
                       self.ye[j], self.ye[j+1], int(z))

    def merged_boxes(self):
        """Merge only rectangles having exactly the same generic total charge.

        Individual proxy feature indicators need NOT be constant on a merged
        box. A patch verifier must handle their internal changes explicitly.
        """
        slabs = {}
        for i, lo, hi, z in self.runs:
            row = slabs.setdefault(int(i), [])
            if row and row[-1][1] == lo and row[-1][2] == z:
                row[-1] = (row[-1][0], int(hi), int(z))
            else:
                row.append((int(lo), int(hi), int(z)))
        active = {}
        merged = []
        for i in sorted(slabs):
            nxt = {}
            for lo, hi, z in slabs[i]:
                key = (lo, hi, z)
                if key in active and active[key][1] == i:
                    nxt[key] = (active[key][0], i+1)
                else:
                    nxt[key] = (i, i+1)
            for key, value in active.items():
                if key not in nxt or nxt[key][0] != value[0]:
                    merged.append((*value, *key))
            active = nxt
        merged.extend((*value, *key) for key, value in active.items())
        return [(self.xe[a], self.xe[b], self.ye[lo], self.ye[hi], z)
                for a, b, lo, hi, z in merged]


def extract_low_cells(arrays, meta, cutoff):
    """Extract every queried generic rectangle with surrogate charge < cutoff.

    Compatible with majority_mixed.geometry(...,meta=True). No geometry module
    imports are performed here, avoiding accidental module-name collisions
    between the supplied checker and the extended checker.
    """
    require(type(cutoff) is int and -(2**50) < cutoff < 2**50,
            "Integral cutoff outside supported exact charge range")
    nv, evindex, atomindex, sign, yl, yh, weights, first, last = arrays
    require(nv == len(meta["ye"])-1 and len(first) == len(meta["xe"])-1,
            "Geometry metadata does not match sweep arrays")
    require(sum(abs(int(w)) for w in weights) < 2**50, "Unsafe accumulation bound")
    require(all(x < y for x, y in zip(meta["xe"], meta["xe"][1:])) and
            all(x < y for x, y in zip(meta["ye"], meta["ye"][1:])), "Unordered events")
    total = sum(int(b-a) for a, b in zip(first, last) if a >= 0)
    runs = _extract(*arrays, cutoff)
    return LowCells(runs, meta["xe"], meta["ye"], cutoff, total)


def selfcheck():
    """Compare complete low-cell sets against direct signed rectangle sums."""
    rng = np.random.default_rng(318)
    cases = 0
    for _ in range(40):
        nv, nx, m = 19, 12, 31
        xl = rng.integers(0, nx-1, m)
        xh = np.array([rng.integers(x+1, nx+1) for x in xl])
        yl = rng.integers(0, nv-1, m)
        yh = np.array([rng.integers(y+1, nv+1) for y in yl])
        weights = rng.integers(-100, 101, m)
        ev = np.array(sorted([(int(xl[j]), j, 1) for j in range(m)] +
                             [(int(xh[j]), j, -1) for j in range(m)]), np.int64)
        first = rng.integers(0, nv, nx, dtype=np.int64)
        last = np.array([rng.integers(a+1, nv+1) for a in first], np.int64)
        first[rng.integers(0, nx)] = -1
        cutoff = int(rng.integers(-200, 201))
        arrays = (nv, ev[:, 0], ev[:, 1], ev[:, 2], yl, yh, weights, first, last)
        meta = {"xe": list(range(nx+1)), "ye": list(range(nv+1))}
        low = extract_low_cells(arrays, meta, cutoff)
        got = {(i, j): z for i, j, x0, x1, y0, y1, z in low.iter_indexed_cells()}
        expected = {}
        for i in range(nx):
            if first[i] < 0:
                continue
            for j in range(first[i], last[i]):
                z = sum(int(weights[q]) for q in range(m)
                        if xl[q] <= i < xh[q] and yl[q] <= j < yh[q])
                if z < cutoff:
                    expected[(i, j)] = z
        require(got == expected, "Low-cell sweep differs from direct exact accumulation")
        require(low.stats["low_generic_cells"] == len(expected), "Low-cell count mismatch")
        merged = {(i, j): z for x0, x1, y0, y1, z in low.merged_boxes()
                  for i in range(x0, x1) for j in range(y0, y1)}
        require(merged == expected, "Equal-charge rectangular merging changed the cell set")
        cases += 1
    return {"status": "PASS_EXACT_LOW_CELL_CONTROLS", "independent_cases": cases}


if __name__ == "__main__":
    print(selfcheck())
