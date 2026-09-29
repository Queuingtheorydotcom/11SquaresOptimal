# Fresh local-isolation replay, 27 September 2026

The saved closed radius **1/248** passed a fresh replay. This remains a local
theorem in the labelled, anchored 33-coordinate chart, with angles in radians.
It does not put an arbitrary feasible packing in that chart neighborhood.

Three separate archived checkers were executed without altering their source:

* The algebra replay verified all 128 derivative-distinct branches (512 raw
  branches), each with exact positive stress and rank 33. Polynomial identities
  were checked by rational polynomial reduction; rank witnesses were checked
  modulo primes. Output: `fresh-local-algebra.json`.
* The conservative-radius audit reconstructed the analytic and inverse-witness
  bounds. Output: `fresh-baseline-radius.json`.
* The weighted-coordinate audit checked all 8,448 nonnegative rational vectors,
  all 55 center-distance bounds, 119 tied-gradient curvature bounds, and the 88
  unavailable-feature certificates. It established the closed radius 1/248
  and the open radius 808514694729/200000000000000.
  Output: `fresh-weighted-coordinate-radius.json`.

The older recovered checkpoint retained the coordinate witnesses but omitted
its upstream source checkout. Five public files were recovered from
`jlevy/squares` revision `c55726e1e885227f63110131c0a914665175ff89`; each matched
the exact hash already named in the retained proof inputs. The same pinned
revision supplied `src/sqpack/exact_lp.py` and `src/sqpack/verify.py`, which the
geometry modules import. The local `replay.py` wrapper redirects the output
receipt only, preserving the archived receipts and all hash-bound input files.
The fresh audits retain links to the original input receipts; their scientific
contents were checked separately in this replay instead of replacing those
immutable links with different timestamp-bearing receipts.

The reviewed finite-branch geometry and analytic Hessian argument remain part
of the mathematical trust base. These computations do not constitute a formal
proof-assistant verification or a global capture theorem.

Two additional global prerequisites were freshly replayed separately:

* `fresh-construction-verification.json` verifies the exact attaining packing:
  eleven unit squares, 55 separating-axis pair checks, 14 touching pairs, and
  20 vertex coordinates on container boundaries. The rational interval for its
  algebraic side lies strictly below the common rational endpoint cap used by
  the exclusion certificates.
* `fresh-center-cover-verification.json` reconstructs the symmetric cover from
  all feasible boundary-line intersections, checks its strict capacity-one
  diameter bounds, and verifies all 16 half-turn cell identities and all 2,184
  canonical subsets. These are necessary case reductions, not exclusions.

Reproduce from the project directory:

```
research/.venv/bin/python research/local-radius/replay.py replay_trump_local.py
research/.venv/bin/python research/local-radius/replay.py audit_local_radius.py
research/.venv/bin/python research/local-radius/replay.py
```
