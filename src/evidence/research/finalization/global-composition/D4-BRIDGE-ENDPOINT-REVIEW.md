# Independent source review of the D4 bridge

**Source-review result: PASS.** No mathematical or search-completeness defect
was identified in `audit_d4_bridge.py` or `D4-BRIDGE-THEOREM.md`. This review
did not execute the checker, its geometry construction, or its finite search.
The root worker must obtain and bind the actual fresh result before claiming
fresh execution of this bridge.

## Closed geometry

The checker reconstructs each bounded Voronoi cell from every feasible
intersection of its defining rational boundary lines. Finite nearest-site
Voronoi cells cover the unit square, so no separate area-sum argument is
needed. Exact vertex comparisons establish the reported cells, and the
strict diameter checks establish injective center assignments. The half-turn
cell action and the complete lexicographic canonical indexing are checked
directly.

The inverse-image routine agrees with the stated four maps: identity,
horizontal reflection, quarter turn, and coordinate swap. The half-turn
compositions supply the other four elements of D4. This relies only on the
verified half-turn permutation of the cell inventory.

The clipping routine uses closed halfplanes. Its singleton and two-endpoint
representations preserve points and segments during successive intersections;
the full-dimensional clipping cells are put in counterclockwise hull order.
Distinct label tuples remain distinct even when their geometric regions
coincide. Consequently every independently chosen closed-cell assignment in
the four views appears among the reconstructed overlay regions, including
boundary-only alternatives.

Squared distance is convex on the product of the two convex regions, so a
maximum over pairs of vertices bounds every actual pair of points. A checked
maximum strictly below one after scaling by `(U-1)^2` forbids those two regions
in a unit-square packing. Equality is retained. The checker's distance list
need not contain every possible strict ban: using a subset gives a weaker
relaxation, whose eventual UNSAT conclusion is still sufficient.

## Finite-search invariant

Each variable is one occupied identity-view cell. Its initial options are
exactly the overlay regions with that identity label. For each other view,
the target bitset contains all still possible allowed eleven-cell masks.
Intersecting it with the masks containing a chosen label preserves every
target that could support a completion.

Filtering a future region by the current target bitsets imposes only necessary
conditions. Filtering it by compatibility with a chosen region imposes only
distinct labels and the verified strict distance bans. All earlier filters
remain in the passed child domains. Minimum-domain variable selection changes
the search order without discarding a possibility, and the loop visits every
remaining value.

At a terminal assignment, each target bitset is nonempty by induction: the
chosen option passed the corresponding nonempty-intersection test immediately
before the recursive call. Eleven pairwise distinct labels contained in an
allowed eleven-set equal that set. Thus a returned terminal list is a valid
solution of the finite relaxation; exhaustion with `None` proves there is no
such solution. The source has no node budget, time cutoff, numerical pruning,
or reliance on a producer's UNSAT flag.

## Conditional global implication

The premise must exclude noncandidate **closed-cell antecedents**, exactly as
stated. Every closed-cell assignment of every D4 image of a feasible packing
must then be a candidate assignment. If no D4 image had an assignment exactly
equal to case 438, none could have its half-turn raw mask either.

After choosing an identity assignment and applying a half turn if needed,
the source case is one of 999, 1462, or 1659. Independent containing-cell
choices in the other views cannot repeat a label by strict cell capacity.
Tracking each physical center across those choices supplies a nonempty
overlay region. Actual pair distances prevent every strict ban. This would
solve one of the three exhausted finite problems, which is impossible.

The proof therefore permits arbitrary boundary ties and requires no
equivariant tie-breaking rule. It establishes existence of a D4 image with a
valid assignment exactly equal to canonical case 438. Capture for that exact
antecedent, at actual sides `S<=T`, completes the remaining implication only
after its independently verified local chart and full branch coverage are
supplied.

The normalized map `(p-1/2)/(U-1)` is consistent with the propagation field
cell map `B/2+(L-B)z`: multiplication by `B=L/U` gives the latter exactly.
D4 maps about the normalized center therefore correspond to physical D4
maps about the padded U-container center. They preserve a concentric smaller
container, so applying capture to an image with `S<T` is valid.

## Acceptance boundary

Removing the archived producer-result comparison is mathematically sound
because the new checker independently reconstructs the geometry and exhausts
the finite relaxation. Its output appropriately leaves global optimality
false and names the noncandidate exclusion and case-438 capture premises.

This review verifies the implication and source logic. The final consumer
must separately bind successful checker execution, the full 2,180-case
exclusion union, and complete case-438 capture. The reviewed files' hashes
are recorded in `d4-bridge-endpoint-source-review.json`.
