# Exact global D4 bridge

This is the missing logical link between exclusion of all 2,180 noncandidate
closed-cell cases at the rational cap U and capture of candidate case 438 at
sides S <= T. It requires no separate capture theorem for cases 999, 1462, or
1659. It does require the precise finite geometric assertion described below.

The new standalone checker `audit_d4_bridge.py` was prepared and reviewed but
**has not been executed in this finalization pass**. Its output must be obtained before claiming a fresh replay.
An archived independent checker and receipt already support the same finite
assertion; their reproducibility issue and its repair are recorded below.

## Hypotheses and conventions

Set

    U = 387708359002281417731 / 10^20.

Let T be the algebraic side of the exact known eleven-square construction,
with T < U. All square side lengths here are one. Every smaller container is
placed concentrically in the U-square, so its center coordinates are measured
in the positive frame [0,U]^2.

The cover cells C_0,...,C_15 are the exact closed normalized Voronoi cells in
`center-cover-symmetric-exact.json`. A physical center p is represented by

    z = (p - (1/2,1/2))/(U-1).

Every square center lies in [1/2,U-1/2]^2, because its horizontal and vertical
half-widths are at least 1/2. Thus z lies in [0,1]^2, covered by these cells.

Every physical cell has diameter strictly less than one. Distinct unit squares
have center distance at least one: otherwise their open inscribed disks of
radius 1/2 overlap. Therefore two centers cannot lie in the same cover cell.
In particular, assigning each center any containing closed cell automatically
gives eleven distinct labels. Boundary choices need no numerical tie-break.

The half-turn H(z)=(1-z_x,1-z_y) satisfies

    H(C_j) = C_(15-j).

The checker verifies this equality from the exact polygons. A raw occupied
mask J is an increasing eleven-tuple. Its canonical representative is

    min_lex(J, sorted(15-j for j in J)).

The 2,184 canonical representatives are the increasing lexicographic list of
these representatives over all 4,368 eleven-subsets. **Indices are zero-based.**
The four candidate entries are:

| Index | Canonical occupied cells |
|---|---|
| 438 | 0,1,2,3,4,8,9,10,11,13,15 |
| 999 | 0,1,2,4,6,7,9,10,12,14,15 |
| 1462 | 0,1,3,5,6,8,9,11,12,13,14 |
| 1659 | 0,2,3,4,5,6,7,11,12,13,14 |

The global exclusion premise must say that each of the other 2,180 **closed-cell
antecedents** is impossible at side U. These are the antecedents used by the
geometric checkers: centers belong to specified closed polygons. The premise
is stronger than a claim about selected floating-point labels or half-open
cells. The final global union must establish this precise scope.

The capture premise must say: a packing of side S<=T, with centered U-frame
occupied assignment exactly J_438, is the known construction after the
certified label map and rigid symmetry. In particular no such packing exists
for S<T. The case438 composition uses this same centered U-frame, including
its exact U-to-T coordinate translation.

## Four views represent all eight square symmetries

Use the following maps on normalized centers:

    g_0(x,y) = (x,y),
    g_1(x,y) = (1-x,y),
    g_2(x,y) = (1-y,x),
    g_3(x,y) = (y,x).

Together with H*g_0,...,H*g_3 they are all eight elements of D4. No assertion
that reflection or a quarter-turn permutes the sixteen cover cells is needed
or made. Only H has the exact cell permutation above. The other views are
handled by intersections of transformed closed polygons.

For a four-tuple of cell labels l=(l_0,l_1,l_2,l_3), define the closed region

    R_l = intersection_(g=0,...,3) g_g^{-1}(C_(l_g)).

The source-independent exact overlay computation finds precisely 220 nonempty
regions: 212 polygons and **8 singleton points**. There are no segment regions
for this particular input. The algorithm retains any lower-dimensional closed
intersection, so the singletons are genuine alternatives in the finite model.
Each stage's number of nonempty label tuples is 16,56,124,220.

For two overlay regions R_r,R_s define

    D_rs = (U-1)^2 max_{x in R_r, y in R_s} ||x-y||^2.

The maximum is attained on pairs of vertices, including singleton vertices,
because squared distance is convex on the product of the two polytopes. The
exact distance table contains 1,572 pairs with D_rs<1. No feasible packing can
select both regions in such a pair. Equality D_rs=1 is not a ban; legal square
contact is not discarded.

## The finite assertion

Let A be the six raw masks consisting of J_999,J_1462,J_1659 and their H-images.
For each identity-view mask J in {J_999,J_1462,J_1659}, the following finite
selection problem has no solution:

* Choose one nonempty overlay region r_i for every owner i in J, with
  l_0(r_i)=i.
* In each of views 1,2,3, the eleven selected labels are distinct and their
  set belongs to A.
* No selected region pair occurs in the strictly forbidden distance table.

The archived independent audit enumerates all 6^3=216 target-view mask triples
for each source J, then exhausts an independent finite matching search. Its
recorded search-node counts are 1,232, 1,882, and 759. All three results are
UNSAT. The conclusion is stronger than a statement about square orientations:
the relaxation allows any centers in the selected regions and only uses
necessary center-distance constraints.

The new standalone checker uses a different search: possible-target bitsets,
minimum-remaining-domain choice, and pairwise forward filtering. Its invariant
is that a candidate region remains only if it is compatible with every chosen
region and at least one remaining raw target in every view. At a terminal
assignment there are eleven distinct labels contained in an allowed eleven-set,
so that set is exactly the selected view mask. Every option not ruled out by
these necessary conditions is recursively visited. There is no node budget,
timeout shortcut, numerical pruning, or producer-claimed UNSAT status.

## Proof of the bridge, including arbitrary cell-boundary ties

Assume the 2,180 noncandidate closed-cell cases have been excluded. Let P be a
packing at a side S<=U. The packing and all its D4 images remain valid in the
centered U-square. Every valid closed-cell assignment of every such image must
have one of the four candidate canonical masks: an excluded assignment would
itself instantiate its forbidden closed-cell antecedent.

Suppose, for contradiction, that no D4 image of P has a valid assignment exactly
J_438. An assignment with raw mask H(J_438) is also impossible, because applying
H to that image and to its labels produces a valid assignment exactly J_438.
Thus all assignments of all D4 images have canonical masks in
{999,1462,1659}.

Choose an assignment of P. If its raw mask is the H-image of its canonical mask,
replace P by H(P) and replace every label j by 15-j. The identity-view occupied
mask is now one of J_999,J_1462,J_1659.

For each of g_1(P),g_2(P),g_3(P), choose any containing closed-cell label for each
square center. Choices may be made independently across views. There can be no
repeated label in any view by the strict cell-capacity bound. Track each of the
same eleven centers across the views. Its four chosen labels define a nonempty
R_l, since the center belongs to all four inverse-image cells. Therefore this
packing supplies eleven of the enumerated overlay regions.

All transformed raw masks belong to A by the supposition. No selected region
pair can be banned, since its actual center distance is at least one. The
selection consequently solves one of the finite problems just proved UNSAT,
a contradiction.

Hence some D4 image has a valid assignment J_438. If the original formulation
of the finite conclusion gives only canonical case438, one additional H-turn
converts its raw mask to exactly J_438. This remains a D4 image.

This argument covers centers on any number of cell boundaries. It neither
replaces a closed cell by its interior nor presumes that a deterministic
boundary-label rule commutes with D4.

## Global optimality composition

Assume independently verified inputs establish:

1. The exact candidate is a packing at side T, and T<U.
2. All 2,180 noncandidate canonical closed-cell cases are impossible at U.
3. The finite D4 assertion above, with these exact cover/source conventions.
4. The complete case438 capture theorem for every S<=T in the centered U-frame.

If a packing existed at some S<T, put it concentrically in the U-square. The
D4 bridge produces an image with occupied assignment exactly J_438. The
capture theorem then forces it to be the exact candidate. The exact candidate
spans T in both container axes, so it cannot fit in a square of side S<T. This
contradiction proves the lower bound T. The verified construction supplies the
matching upper bound, completing optimality.

No limiting or compactness argument is needed. A packing at S<T is directly
subject to the finite closed-cell proof. If one instead phrases optimality as
an infimum, any infimum below T would imply existence of some admissible side
strictly below T, already excluded by this argument.

## Sources, existing acceptance, and fresh replay

The frozen inputs are:

| Workspace-relative path | SHA256 |
|---|---|
| `research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json` | `df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e` |
| `research/phase3/work/phase2/geometry/cover_overlay_exact.json` | `845b5f748843dd60fa7e290a5ea1a304da4e439ae229bd73a841aec816f4e700` |
| `research/phase3/work/phase2/geometry/overlay_distance_pairs.json` | `4f960f4001faa6c9c1e7521f3a2344f71e10b41cd38a6425f6821cc1fd2ccd47` |

The archived independent checker and acceptance receipt are
`research/phase3/work/phase3/audit/audit_candidate_orbit.py` and
`candidate-orbit-independent-audit.json`. The receipt binds checker SHA256
`5f2a0ac8d627134ef952bd00363130270513049f69a08e2427d9c1bbada51e30`.
It is an explicitly conditional theorem and must not be counted as an
unconditional noncandidate exclusion.

Its final redundant check reads a producer result at
`research/phase3/work/phase3/reductions/candidate-orbit-result.json`, whose
recorded SHA256 is `a3bf615f215d561ae74701e2b77cb0fd7e3cce560d72f156db8d15fed8c3a5be`.
That file is missing from the local recovered bundle. The independent geometry
and finite enumeration do not use its contents to prune or prove UNSAT; it only
compares the already obtained conclusion with the producer's conclusion.

The new `audit_d4_bridge.py` removes this unnecessary dependency. It additionally
checks the canonical list ordering and exact half-turn cell indexing directly.
It is self-contained Python with exact rational arithmetic and imports neither
the producer CSP nor its polygon routines. Its eventual output deliberately
keeps `global_optimality_proved=false`: it establishes the conditional bridge,
while the final global consumer must bind the completed 2,180-case union and
case438 capture separately.

A replay command is:

    research/.venv/bin/python research/finalization/global-composition/audit_d4_bridge.py

The source review passes for this mathematical implication. Fresh execution of
this new checker, and validation of the returned global/candidate proof bundles,
remain separate acceptance obligations.
