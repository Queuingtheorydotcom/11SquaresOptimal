# Source review: why an unconditional v9 PASS is a continuum case exclusion

This is a source review, not a new execution of the certificates or controls. No acceptance defect was found in the fresh-wall-seed, unconditioned path examined below. Acceptance still requires a complete fresh replay with the frozen sources, exact input hashes, and the strict result checks in the final transport verifier. This note does not certify that any unfinished replay has passed, and does not prove global optimality.

## Frozen scope

The reviewed verifier is `eleven-square-verification/research/phase3/work/phase3/hull/audit_capture_v9.py`, SHA-256 `95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c`. The source-bound dependency inventory is `eleven-square-verification/code/v9-dependency-pins.json`; its fixed SHA-256 in the final adapter is `8a46589d35e3bbd1efce02b2a196db5ddb636a85259bf7f30d6b31daa65b01f8`.

The relevant mathematical sources, with their frozen hashes, are:

| Source relative to the package's `research/phase3/` | SHA-256 |
| --- | --- |
| `work/phase3/hull/arrangement_audit_v2.py` | `0dfc3d4ca546cf465d39bc75c534eeca133099a5283acae95810c4e957f3fc0b` |
| `work/phase3/hull/arrangement_audit.py` | `df050facaf26edfb6e5320cb82f529462d7fc108a6076807073ec80f55eb7351` |
| `work/phase3/hull/own_hull_constraints.py` | `93eaafff20aed1eea0d4115e9c7fb1b11658cdd59c0d0b2f076c7ed1348ac476` |
| `work/phase3/collision/validate_collision_kernel_v3.py` | `3108b1a4aade301b286ccaf72429569f2dff96f48a6869e39616c0805d745905` |
| `work/geometry/audit_wall_kernel.py` | `f442d798796e6017225dea528c9bcf7b4fbeb3c2c3e6262f68de2e43ff542660` |
| `work/phase3/hull/audit_residual_kernel.py` | `f4ec7eda8eb78cfa93d9c298dbaddb8e7e605417b0b73ac6b6de7d9421440be4` |
| `current/research/optimality/audit/audit_center_cover.py` | `7de546ee4eb3695f3874ae238567584a08c8317380ec83c0a67bae2160412d65` |

These identities are the existing frozen pins, not newly computed hashes in this review. Source locations below refer to those exact versions.

## The case theorem and induction invariant

Fix a specified occupied-cell set, the rational container side
`U = 387708359002281417731/100000000000000000000`, and `L=191/50`, `B=L/U`.
For each owner, the checker maintains (a) a convex hull K of points strictly inside every square still possible for that owner, and (b) a closed outer center-domain cover for every allowed angle. Every valid packing consistent with the cell assignment must obey these invariants. A contradiction obtained by preserving them excludes that entire occupancy case.

The final wrapper requires the full assigned eleven-cell set, the exact U/B and cover, empty constraints, an independently verified wall seed, and a true mask exclusion. An unconditional result therefore has no extra position, angle, or contact assumptions. It remains conditioned on its stated occupancy case.

## 1. Arbitrary independent rotations, closed cells, and ties

A square is unchanged by a quarter turn. Thus every independent orientation can be represented by `theta in [0,pi/2]`, with `t=tan(theta/2) in [0,1]` and exact rational functions
`c(t)=(1-t^2)/(1+t^2)`, `s(t)=2t/(1+t^2)`.
No relation between different owners' angles is imposed.

`Replay.__init__` in v9, beginning at line 138, constructs each owner's seed intervals exactly as `[k/bins,(k+1)/bins]`, including both endpoints. It independently checks the seed domains. Completed updates require consecutive intervals with an exact running cursor and the full ending endpoint (lines 306–309 and 348–349). Partner covers have their own complete cursor check. Consequently this is interval verification over the continuum, not verification at finitely sampled angles. Unconditioned angle ranges remain `[0,1]`; singleton conditional ranges are explicitly rejected rather than discarded.

The cover verifier `audit_center_cover.audit` (line 33) reconstructs each closed Voronoi cell using all feasible boundary-line intersections, verifies its vertices, strict physical diameter bound, and the complete list of 4,368 eleven-cell selections. Every center belongs to at least one such nearest-site cell, including tied centers. Choose any fixed tie rule. Two centers assigned to the same cell would have distance strictly below one, so their open inscribed disks of radius one-half would overlap. Therefore eleven nonoverlapping unit squares receive eleven distinct labels. Closed cell domains retain tied boundary configurations; no generic-position assumption is made.

The reduction from 4,368 selections to 2,184 canonical cases additionally uses a whole-packing half turn. The v9 center-cover helper does not itself reprove that quotient. This is a composition dependency: the original baseline field checkers explicitly verified the center and vertex involution `i -> 15-i`, and the baseline aggregate independently rebuilt the canonical enumeration. The final global ledger must retain that verified cover/symmetry premise.

## 2. Wall envelopes and strict seed ownership

A legal center in a square of field side L satisfies `h(t) <= x,y <= L-h(t)`, where `h(t)=B(c(t)+s(t))/2`. On a closed row `[a,b]`, the minimum of `c+s` occurs at an endpoint. The seed checker also verifies the corresponding concave quadratic endpoint inequalities, giving an outer envelope containing every legal center at every angle in that row. These non-strict envelope cuts allow wall contact.

Every seed point is either certified by a strict vertex-distance bound below `1/4` in unit coordinates, or by `audit_wall_kernel.check_point` (line 51). The latter subdivides the entire closed angular interval, encloses both body-coordinate projections by exact rational interval arithmetic over the wall-clipped convex cell, and requires a strictly positive margin from one-half. Failure to resolve an interval returns failure. Convexity extends the verified vertex bounds over the full center polygon. The finite convex hull of these strictly interior points remains strictly inside each possible owner square.

## 3. Strict cores and why forbidden boundaries are valid

For every nonempty row, v9 `_validated_core` (line 50) checks a full-dimensional convex polygon Q. Each vertex must satisfy both signed body-coordinate inequalities strictly for the entire closed row. Multiplication by positive `1+t^2` turns these into rational quadratics. `positive_quadratic` checks the endpoints and, when present, the interior minimum. Hence the entire closed Q lies strictly inside the square for every angle in the row.

If another owner's hull K is strictly inside its square, a center `x in K-Q` forces some point `k=x+q` to lie strictly inside both squares. Thus the **closed** Minkowski polygon `K-Q`, including its boundary, is forbidden. This does not confuse mere contact between the actual square boundaries with forbidden interior overlap: both K and Q have already been proved strictly interior. v9 `residual_cover` (line 118) constructs these Minkowski regions from all vertex sums and exact convex hulls.

Universal pair-collision cuts obey the same principle. `collision_halfplanes` (line 41) constructs every facet of `Q_j-Q_i` and requires
`n*x <= h + min_{y in D_j} n*y`
for each row of the partner's complete possible-pose cover. This proves inclusion in `y+Q_j-Q_i` for every possible partner center y. The caller independently verifies each partner domain, strict core, predecessor, and complete angle cover. An entirely empty partner cover is handled as an explicit contradiction; it is not accepted by the collision validator as an unchecked vacuous universal premise.

## 4. Exact coverage, including points, segments, and contacts

`clipped`, `bounded_rows`, and `intersection_polygon` work with non-strict rational halfplanes. Bounding-box inequalities keep point and segment domains bounded and explicit. Pairwise line intersections retain their endpoints or isolated point; a zero-area domain is not silently treated as empty.

For a two-dimensional domain, `arrangement_audit_v2.union_cover` (line 102) splits at polygon vertex abscissae. On each open slab, its selected vertical interval chain has affine endpoints. Every chain link and its final reach are checked across the slab, with exact further splitting at a failed affine inequality's root. An uncovered interval or exhausted budget returns failure. The finite union of the supplied closed polygons then contains the dense slab interior, hence its closure: all boundary edges, event lines, and vertices of the domain. This closed-set argument explains why zero-area residual pieces need not be used to establish coverage of a full-dimensional domain.

A point or segment domain takes the separate v9 `lower_dimensional_cover` path (line 72). It parameterizes the segment by `[0,1]`, intersects each covering region's halfplanes with that interval, and proves the resulting closed intervals cover the entire parameter range without gaps. The same formula handles a singleton with zero direction. No positive-area argument is used for these domains.

All these checks establish the necessary implication: a feasible center cannot be in a strict-overlap forbidden region and must therefore be in a retained residual polygon. Overlarge residuals only weaken exclusion; they do not remove possible configurations.

## 5. Necessary owner cuts and safe promotion

`own_hull_constraints` proves upper bounds E for the square's support over a whole angle interval by four exact nonnegative quadratic checks. Every already owned point p must remain inside the actual square, so
`max_K n*p - E <= n*center <= min_K n*p + E`.
The four supplied midpoint-axis cuts are accepted only if their normalized inequalities match the independently derived necessary cuts. These are consequences of ownership, not additional branch assumptions, and their non-strict form preserves contact.

For a core facet `n*q <= h` and residual center set R, a proposed new owned point must satisfy `n*p <= h + min_R n*x`. This puts it in `x+Q` for every still-possible center x. V9 recomputes those halfplanes from every residual vertex and every angular row. Promotion occurs only after the full row cover is complete. `verify_convex_combinations` independently checks each compressed point as a nonnegative rational barycentric combination, with weights summing to one, of previously owned or newly proved kernel points. Strict interior ownership is therefore preserved. An incomplete last step cannot promote anything.

## 6. Contradiction and unconditional acceptance

The two recognized contradictions are checked in v9 lines 377–386:

- `all_parent_poses_forbidden`: an actually checked complete update has no residual center in any angular row of a required owner.
- `owned_hulls_intersect`: two distinct required owners have intersecting strict-interior hulls, forcing interior overlap of their squares. The separating-axis test includes all hull edge normals and coordinate axes; the latter also distinguish separated collinear segments or point hulls.

Parent sources and their seed are hash-bound and recursively replayed; an ancestor's reported success alone is not trusted. Additional branch constraints must include every inherited constraint. They therefore cannot disappear later in a chain. The final `unconditional` calculation (line 402) requires an actual checked contradiction and an empty constraint list. In the fresh generic path, guard sources must be null and the final guard empty. Merely entering a local guard does not give this unconditional exclusion.

## Acceptance boundary and remaining work

A complete fresh PASS with the reviewed dependency/import bindings establishes a continuum exclusion at rational U for its named case, allowing arbitrary independent rotations, closed cell boundaries, square–square touching, and square–container touching. Embedding a smaller square container into the U container supplies the usual monotonic implication for a full exhaustive case proof.

This source review does not replace the currently running per-case exact replay. It also does not supply the remaining occupancy cases, the candidate-case argument, or the final disjoint complete ledger. The fresh-wall-seed path was examined; cached or externally audited Phase2 root modes are outside this note. Python/GMP exact-rational arithmetic, the standard runtime, and the identified mathematical source files remain the computational trusted base.
