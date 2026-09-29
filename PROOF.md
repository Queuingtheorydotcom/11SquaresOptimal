# Optimality of the eleven-square packing

This is the mathematical exposition of the computer-assisted certificate argument.
The theorem allows arbitrary independent rotations and legal boundary contact.
It uses exact rational geometry and exact algebraic arithmetic. The repository
contains its checker and discovery sources and the required certificate inputs;
execution logs are deliberately omitted. See [reproduction instructions](docs/REPRODUCING.md)
and [publication changes](docs/PUBLICATION.md) for the validation scope of this public copy.

The known construction is credited to Walter Trump. The bundled upstream
`jlevy/squares` construction credits David Ellsworth for its reconstruction
diagram. No priority claim or completed proof-assistant formalization is made.

## 1. Statement and exact endpoint

A packing consists of eleven congruent closed unit squares in a closed square
container, with pairwise disjoint interiors. Each small square may rotate
independently. Boundary contact between small squares, or with the container,
is allowed. Let s_11 be the infimum of admissible container side lengths.

Let u be the unique real root in `(9/25,37/100)` of

$$
5u^8-10u^7-2u^6+14u^5+12u^4-6u^3+2u^2+2u-1=0,
$$

and define

$$
T=\frac{6u+4}{1+2u-u^2}.
$$

The construction gives an admissible packing at T, approximately 3.87708. Its
side also satisfies

$$
T^8-20T^7+178T^6-842T^5+1923T^4-496T^3
-6754T^2+12420T-6865=0.
$$

The definition through the isolated root u specifies which algebraic root is
intended; the side polynomial alone is not a sufficient endpoint definition.

**Theorem (computer-assisted certificate proof).** For eleven congruent unit
squares with pairwise disjoint interiors in a square container, allowing
arbitrary independent rotations, the minimum container side is

$$ s_{11}=T=3.8770835900228141773078970601\ldots. $$

The proof combines the exact construction, the complete 2,180-case exclusion
inventory, the exact D4 bridge, and complete case438 capture. Their computational
premises are encoded by the supplied source-bound certificate data. The mathematical
implications and the checker trust boundary are explained below; a successful
status string by itself is not a substitute for those implications or for
correct implementation of the checker rules.

## 2. Exact construction and upper bound

Put

$$
c=\frac{1-u^2}{1+u^2},\qquad s=\frac{2u}{1+u^2}.
$$

Then c²+s²=1, with c,s positive. Write

$$
\begin{aligned}
\rho&=1-(T-3)c,\\
\eta&=\frac{(1+\rho)c-1}{s},\\
v&=c-s,\\
\zeta&=\frac{T-1}{s}-\rho-(3+\eta)\frac{c}{s},\\
x_0&=1+\frac{2}{c}-(T-2)\frac{s}{c}.
\end{aligned}
$$

For `(a,b)` let A(a,b) be the axis-aligned square
`[a,a+1] × [b,b+1]`. Let

$$
F(x,y)=(1,1)+
\begin{pmatrix}c&-s\\s&c\end{pmatrix}(x,y-\rho).
$$

The eleven squares are the following six axis-aligned squares:

$$
A(0,0),\quad A(T-1,0),\quad A(x_0,T-1),\quad
A(0,T-1),\quad A(1,T-1),\quad A(0,T-2),
$$

and the five images under F of

$$
A(0,0),\quad A(\eta,-1),\quad A(1,v),\quad
A(\eta+1,v-1),\quad A(\eta+2,-\zeta).
$$

These are the formulas in the bundled exact construction module. The rotation
identity proves that every image is a unit square. The remaining upper-bound
verification is finite: all 44 vertices must lie in `[0,T]²`, and each of the
55 pairs must have a weak separating axis. For convex polygons it is enough
to test the edge-normal directions of the two polygons. Weak separation is
essential here because contacts are legal.

The bundled exact verifier performs these checks in the number field Q(u).
It reduces expressions modulo the defining polynomial, uses an isolating
interval for the specified real root, and proves the signs of nonzero
expressions by rational interval refinement. Equalities are checked
algebraically, not by an approximate tolerance. Root isolation and the
algebraic identities are included in the source-bound algebra audit. The
original construction module is

`work/evidence/research/recovered-checkpoint/research/jlevy/packing/cases/trump11/packing.py`.

The local source loader also invokes an exact packing verifier before forming
any derivative matrices. The fresh source-bound algebra audit is
`work/evidence/research/local-radius/fresh-local-algebra.json`. The evidence package
retains the pinned exact construction, its arithmetic dependencies and those
bindings.

The exact construction has corners on both opposite walls in each coordinate.
Its horizontal and vertical spans are therefore both T. This fact is checked
again in the final candidate composition. The upper bound s_11<=T follows.

## 3. Uniform coordinate framework for every smaller packing

Fix the rational cap

$$
U=\frac{387708359002281417731}{10^{20}},
$$

for which the exact algebraic comparison gives T<U. Also put

$$ L=\frac{191}{50},\qquad B=\frac{L}{U}. $$

Here L is a computational coordinate scale; it is not a claimed packing side
for unit squares. Multiplication by B sends unit squares to squares of side B
and the U-container to `[0,L]²`.

Suppose a counterexample packing has side S<T. Translate its container so that
it is centered in `[0,U]²`; its occupied container becomes

$$
[(U-S)/2,(U+S)/2]^2.
$$

This operation does not scale or rotate the small squares. Consequently every
such counterexample is a valid packing in the cap U, to which all cap-U
exclusions apply.

Write p for a center in this positive physical U-frame and p_f=Bp for its
scaled field coordinate. Each unit square has horizontal and vertical
half-width at least 1/2, so

$$ p\in[1/2,U-1/2]^2. $$

The normalized center coordinate is

$$ z=\frac{p-(1/2,1/2)}{U-1}\in[0,1]^2. $$

An orientation may be represented by θ in the whole closed interval
`[0,π/2]`, with the two endpoint orientations describing the same square.
Set t=tan(θ/2), so t belongs to `[0,1]` and

$$
\cos\theta=\frac{1-t^2}{1+t^2},\qquad
\sin\theta=\frac{2t}{1+t^2}.
$$

This changes the parameterization, not the physical square. It does not assume
that all eleven orientations are equal. Every orientation row used in the
certificates is a closed interval in this full chart; endpoint and
lower-dimensional cases are retained.

## 4. Closed center cover and the 2,184 cases

The proof uses sixteen closed Voronoi cells C_0,...,C_15 covering `[0,1]²`.
Their rational sites and exact vertices are supplied by

`work/evidence/research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json`.

Its source hash is
`df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e`.

The exact checker reconstructs each cell from the unit-square inequalities and
the nearest-site halfplanes

$$
2(q-p)\mathbin{\cdot}z\le \|q\|^2-\|p\|^2.
$$

Thus coverage is a mathematical consequence of choosing a nearest site for
every point of `[0,1]²`; it does not depend only on summing polygon areas.
All cell vertices are reconstructed by exact boundary-line intersections.
The checker proves

$$ (U-1)^2\operatorname{diam}(C_j)^2<1\quad(0\le j<16). $$

Two centers of interior-disjoint unit squares have distance at least one,
since their open radius-1/2 inscribed disks have disjoint interiors. Therefore
a physical cover cell contains at most one center. Choosing any containing
closed cell for each of the eleven centers gives eleven distinct labels.
Arbitrary choices at cell boundaries are allowed.

There are `binom(16,11)=4368` raw eleven-cell masks. The exact half-turn
H(z)=(1-z_x,1-z_y) satisfies H(C_j)=C_(15-j). Canonicalization replaces an
increasing eleven-tuple J by the lexicographically smaller of J and H(J).
No eleven-mask is fixed by this involution: its cell orbits have size two,
whereas eleven is odd. There are therefore 2,184 canonical cases, listed in
lexicographic order with **zero-based** indices. This enumeration and the
half-turn identity are checked directly.

Let M={0,...,2183} be the complete index set and put

$$ C=\{438,999,1462,1659\}. $$

The candidate masks are:

| Index | Increasing cell tuple |
|---|---|
| 438 | 0,1,2,3,4,8,9,10,11,13,15 |
| 999 | 0,1,2,4,6,7,9,10,12,14,15 |
| 1462 | 0,1,3,5,6,8,9,11,12,13,14 |
| 1659 | 0,2,3,4,5,6,7,11,12,13,14 |

A case antecedent means that the eleven centers admit the specified assignment
to the **closed** physical cells. It imposes no numerical or half-open
boundary-label convention.

## 5. What an exact case-exclusion certificate proves

A case exclusion must prove that its closed-cell antecedent is impossible for
a packing in the U-container. The argument used by the geometric certificates
is an induction on exact outer pose domains and exact strict inner owned
hulls. This section explains why its verified steps imply mathematical
infeasibility; the large finite lists of rational polygons remain in the
bundled certificate files.

For each occupied cell, an outer pose cover contains every possible center
and orientation of that square. Each angle row has a center polygon or finite
union of polygons. Separately, an owned hull consists of points guaranteed to
be strictly inside that same square in every surviving pose. These are
opposite inclusion directions and must not be interchanged.

Initial ownership is proved either by an exact open-inscribed-disk test or by
the independently checked wall-kernel inequalities with positive margin.
All sixteen cell geometries, initial angle rows and legal-wall envelopes are
checked. An inherited seed requires its own source-bound ownership audit;
a summary stating that a hull is owned does not establish ownership.

For a closed angle interval, the checker verifies a convex polygon Q contained
strictly inside every square orientation in that interval. Substituting the
half-angle formulas reduces each core projection inequality to positivity
of a rational quadratic on a closed interval. Endpoints and any interior
quadratic minimum are checked exactly.

If K is a different square's owned hull, any center in the closed Minkowski
sum K+(-Q) makes the squares overlap in their interiors. Strict inner
containment makes the closed boundary of this forbidden set safe to remove;
without strict containment it could represent legal touching. A universal
collision kernel likewise excludes a center only after proving collision
against **every** row of a complete partner pose cover. Its facet bounds are
checked from exact vertex sums and minimum support over the partner domains.
An empty partner cover is handled as an explicit contradiction, not as an
unchecked empty universal quantifier.

The residual-cover check proves that every old center is in a verified
forbidden region or in the new residual regions. It uses independently
reconstructed rational polygon arrangements and separate point/segment
coverage. It must retain cell boundaries and zero-area residuals. A common
inner kernel can be promoted only after a complete allowed angle cover has
been checked. Exact convex-combination certificates justify the retained
inner-hull vertices. Self-hull cuts are necessary consequences of already
proved ownership, not extra assumptions about a candidate construction.

A verified terminal contradiction is either:

* a complete pose cover of an owner with no surviving center/orientation; or
* intersection of two hulls independently proved to be strictly inside
  different squares.

Both contradict any actual packing satisfying the node's antecedents. A
conditional branch contradiction becomes an unconditional case exclusion
only after its branch assumptions are discharged by a complete partition or
an independently proved necessity theorem.

The core independent checker is the frozen
`work/evidence/research/phase3/work/phase3/hull/audit_capture_v9.py`. Its exact geometric
rules are separate from the producer's discovery routines. Every accepted
receipt must bind its source trace, full ancestor chain, seed, cover, side U,
scale B, and executed checker dependencies. Counts, successful process exit,
and supplied status labels do not by themselves meet this requirement.

Some earlier exclusions use necessary D4 center halfplanes. Their use is
legitimate only through the separately audited support theorem and
`work/evidence/research/global-math/overlay_field_halfplanes_v2.py`, which checks each
halfplane on every original vertex of every independently surviving support
region. The discharge consumer checks these premises and the independent
conditional geometric contradiction. That dependency starts from the
immutable original 1,931-case exclusion baseline. It must remain acyclic; the
final four-candidate D4 bridge below is not used to prove its own
noncandidate-exclusion premise.

**Finite exclusion lemma.** The accepted strict pre-return union and returned
case replays, combined by the final consumer, establish

$$ E=M\setminus C,\qquad |E|=2180, $$

where every member of E is impossible at the same cap U. The consumer checks
the exact set equality and its dependency bindings, rather than inferring it
from the total count.

The accepted inventory has 2,007 pre-return exclusions and 173 returned cases.
An older strict union contained only 1,997 cases; the ten additional
pre-return cases

`927,998,1111,1112,1114,1115,1124,1125,1128,1143`

are source-bound into the accepted strict 2,007-case union. The arithmetic
`2007+173=2180` is not a substitute for verifying set membership, disjointness,
source completeness and the absence of conditional assumptions.

## 6. The exact D4 reduction to case438

Assume the finite exclusion lemma. Then every valid closed-cell assignment
of every D4 image of a feasible packing has a canonical mask in C. This
universal statement follows because any assignment in an excluded case would
instantiate that case's forbidden closed-cell antecedent.

Use four normalized-coordinate views

$$
g_0(x,y)=(x,y),\quad g_1(x,y)=(1-x,y),\quad
 g_2(x,y)=(1-y,x),\quad g_3(x,y)=(y,x).
$$

Together with their half-turn images they represent all eight square
symmetries. Quarter-turns and reflections need not permute the cover cells.
For every four-label tuple l, form the closed intersection

$$ R_l=\bigcap_{k=0}^{3}g_k^{-1}(C_{l_k}). $$

Exact reconstruction gives 220 nonempty regions: 212 polygons and eight
singleton points. The singletons are included. For each retained forbidden
pair of regions, the checker proves

$$
(U-1)^2\max_{x\in R_l,\ y\in R_m}\|x-y\|^2<1.
$$

The maximum is found on vertex pairs, by convexity of squared distance. These
1,572 strict distance bans are necessary conditions; no equality-at-one pair
is discarded.

Consider the six raw masks obtained from canonical cases 999,1462,1659 and
their half-turns. The exact finite checker proves the following assertion:
for each identity-view source case 999,1462,1659, it is impossible to choose
one overlay region per occupied owner such that all three transformed view
masks are among those six raw masks, all view labels are distinct, and no
chosen pair violates a strict distance ban. This is an exhaustive finite
relaxation of center geometry. Its UNSAT result does not depend on any
unproved assertion about possible square orientations.

The standalone checker is
`work/evidence/research/finalization/global-composition/audit_d4_bridge.py`. It reconstructs
the cover and all overlay geometry, verifies the exact half-turn and index
conventions, checks every used distance ban, and exhausts a source-distinct
bitset search. No producer solver conclusion is accepted as a premise. The
source-bound acceptance of its replay is included in the final global result.

To derive the geometric consequence, suppose no D4 image of a packing has a
valid occupied assignment exactly J_438. A raw H(J_438) assignment is also
impossible, because applying H gives J_438. Every D4 image therefore has only
assignments from the other three canonical candidates.

Choose an identity assignment and, if needed, physically half-turn the whole
packing and its labels so that this assignment is canonical. Independently
choose containing closed-cell labels for the same eleven centers in each of
the other three views. Distinct centers have distinct labels in every view.
The four labels of each center identify a nonempty closed overlay region.
These eleven regions avoid all strict distance bans and have transformed
masks among the six allowed raw masks. They would solve the finite problem,
a contradiction.

Thus some D4 image admits exactly J_438. This reasoning includes arbitrary
cell-boundary ties and does not assume that a deterministic tie-break
commutes with a symmetry. Additional detail about this lemma and its source conventions is in the
[archived D4 bridge note](src/evidence/docs/D4-BRIDGE-THEOREM.md). Its opening
execution-status paragraph predates the completed run; its mathematical lemma
and its warning that the bridge needs the noncandidate exclusions remain valid.

## 7. Local contact analysis and the focused isolation rectangle

The local calculation is performed around the exact construction, with its
container fixed as `[0,T]²` and with its eleven square labels fixed. A
perturbation has 33 coordinates: two center displacements and one angular
displacement in radians for each square.

Non-overlap of two convex squares is equivalent to weak separation along an
edge axis of one of them. A separation feature consists of the owner of the
axis, one of its two perpendicular axes, and the choice of separation order.
For each feature, all four corners of the other square must satisfy the
corresponding weak projection inequality. The elementary wall and corner
gap functions are analytic in the 33 perturbation coordinates.

The exact construction has fourteen contacting square pairs. For these pairs
there are 112 possible separation features. Exact sign checks classify 24 as
available at the construction and 88 as unavailable. Each unavailable feature
has a particular corner gap that is strictly negative. Noncontact-pair
conditions may be omitted from this necessary local system: omitting
constraints weakens the system and cannot exclude a feasible packing.

The available contact choices give 512 raw selections and 128 distinct
reduced derivative matrices, each with 42 necessary tied rows, including the
necessary wall rows. This enumeration is checked from the exact elementary
gradients, including aliases having the same gradient. No assumed contact
graph is imposed on the nearby packing: the negative-feature estimates prove
that the other separation features remain unavailable throughout the region
under consideration.

Let r_0,...,r_32 be the positive coordinate radii in the focused local receipt.
They bound centers in unit-length coordinates and angles in radians. All are
within the analytic working box of radius 1/64. This working box is distinct
from the previously published uniform isolation radius 1/248; the focused
rectangle need not be contained in that smaller uniform ball.

For square i write w_i=r_(3i+2). If an elementary pair gap uses an axis owned
by square o and a corner of square p, a valid second-derivative bound for a
direction inside this coordinate rectangle is

$$
\begin{aligned}
K={}&D_{op}w_o^2
 +2\sqrt{(r_{3o}+r_{3p})^2+(r_{3o+1}+r_{3p+1})^2}\,w_o\\
&+\frac{1}{\sqrt2}(w_o+w_p)^2.
\end{aligned}
$$

Here D_op is an exact upper bound on center separation throughout the old
analytic working box. The terms bound rotation of the center projection,
its mixed derivative, and the other corner's relative rotation. A wall gap
has bound `K=w_i²/sqrt(2)`. All square roots are replaced by checked rational
upper bounds. For a gradient with multiple elementary-function aliases the
maximum bound is used.

For each of the 88 unavailable features, the checker proves

$$
g(0)+\sum_j|\partial_jg(0)|r_j+K/2<0.
$$

Taylor's theorem keeps its selected corner gap negative throughout the whole
closed rectangle. Consequently every feasible perturbation selects one of
the 128 derivative branches.

For each branch matrix A and each signed coordinate σe_j, a retained
nonnegative rational dual vector λ has a rigorously bounded residual

$$ \|\lambda^{\mathsf T}A-\sigma e_j^{\mathsf T}\|_1\le\epsilon_j. $$

The exact original residual check is independently replayed. With K_i the new
row curvature bounds, put `M_j=sum_i λ_i K_i` and `R=max_k r_k`. The focused
checker verifies, for all `128·33·2=8448` signed-coordinate certificates,

$$ M_j<2(r_j-\epsilon_j R). $$

The largest verified left-to-right ratio is approximately 0.6765052083, below
one. The gap tests and dual tests use exact rational comparisons; this decimal
is only an explanatory summary.

To prove isolation, suppose a nonzero feasible perturbation h lies in the
closed rectangle and put

$$ \tau=\max_j |h_j|/r_j,\qquad 0<\tau\le1. $$

Choose a saturated coordinate and the dual sign opposite its displacement.
The selected tied gap inequalities and Taylor's theorem give
`A_i h >= -τ²K_i/2`. Multiplying by the nonnegative dual and bounding its
residual yields

$$ \tau r_j\le\epsilon_j\tau R+\tau^2M_j/2. $$

The preceding strict inequality forces τ>1, a contradiction. Hence only the
zero perturbation is feasible in the rectangle. This argument also excludes
nonzero perturbations on its boundary.

The independent checker and receipt are
`work/evidence/research/global-math/audit_focused_local_box.py` and
`work/evidence/research/global-math/focused1024-local-box-independent.json`. They bind the
exact original coordinate packet and its fresh independent replay. A separate
review reconstructs the raw contact-feature enumeration; ten negative controls
check the local consumer's source, frame, angle and radius rejection rules.
The detailed analytic explanation is
`work/evidence/research/global-math/FOCUSED-LOCAL-RECTANGLE.md`.

## 8. Complete case438 capture and the exact U-to-T bridge

Case438 has an unconditional closed-cell antecedent and a complete orientation
cover at the rational cap. Its proof uses the following four closed branches,
where y_15 is the centered physical coordinate of the square in owner cell 15:

1. `y_15 <= 5/4`;
2. `y_15 >= 5/4` and `t_13 <= 147/512`;
3. `y_15 >= 5/4`, `t_13 >= 147/512`, and `t_2 <= 183/512`;
4. `y_15 >= 5/4`, `t_13 >= 147/512`, and `t_2 >= 183/512`.

The first three branches have independently checked geometric contradictions.
The fourth has an independently checked outer pose induction whose final state
contains every surviving pose under those three near-side conditions. The
closed inequalities overlap at equality and cover every possibility; no strict
branch gap is discarded.

The final near state has 136 live closed angular rows and 1,542 center vertices.
The independent focused-box checker encloses all their centers and full angle
intervals in the local isolation rectangle. Convexity then covers every
center polygon, not only its vertices. For axis squares the intervals near
`t=1` are converted using `(t-1)/(t+1)`, the half-angle parameter after a quarter
turn. The t=0 and t=1 endpoints are both retained. Angular radii are obtained
from exact bounds on the derivative of `2 arctan(t)`; t is never identified with
an angle measured in radians.

The center chart is crucial. The case438 symmetry is the quarter turn
`Q(x,y)=(-y,x)`. Given a field center p_f, the corresponding positive-T-frame
local center is exactly

$$
Q^{-1}\!\left(\frac{p_f}{B}-(U/2,U/2)\right)+(T/2,T/2).
$$

This formula includes the U-T translation. It does not identify the rational
cap with the algebraic endpoint or ignore their difference. A packing centered
in a square of side S<=T is mapped by this rigid coordinate change into
`[0,T]²`. Its deviations from the exact construction are therefore the same
33 coordinates to which the fixed-container local theorem applies.

The local theorem forces the near-branch packing to be the exact construction.
Since that construction spans T in both coordinate directions, it cannot be
contained in a square of side S<T. Thus the accepted complete composition
establishes that case438 has no packing of side below T. This is **not** a
claim that case438 is infeasible at U; cap-U perturbations are allowed by the
proof's scope.

The final candidate consumer is
`work/evidence/research/candidate-capture/audit_complete_capture438.py`. Its accepted
receipt binds the unconditional Phase2 root, the three far-branch contradictions,
the full near-state ancestry, the focused local receipt, the complete partition,
and the exact endpoint/frame identities. The final consumer checks that the
executed receipt matches the accepted checker source. This matters because acceptance obtained before later source
edits would not be acceptance of the later code.

## 9. Accepted global verification obligations

The completed chain and final consumer discharge the following computational
obligations. They also provide a review checklist for an independent verifier: a
replacement implementation must establish the same mathematical statements,
not merely reproduce a matching number of successful exits.

**A. Exact construction and arithmetic.** The specified real root is uniquely
isolated; the displayed construction is a packing in `[0,T]²`; T<U; and the
construction spans T in both coordinate axes. All exact algebra dependencies
and their actual executed versions are bound.

**B. Strict pre-return union.** There is a source-complete, independently
accepted set E_old of exactly 2,007 noncandidate canonical indices at cap U.
It includes the ten cases absent from the older 1,997-case strict union, with
complete source-bound proofs rather than ledger assertions. Every conditional
exclusion has its assumptions independently discharged. Dependency reuse is
explicit and acyclic.

**C. Returned cases.** The twelve returned packets establish a set E_new of
exactly 173 assigned noncandidate cases. The actual source and seed bytes,
not only declared hashes or file headers, are verified. Full ancestry,
checker identity, rational frame, closed-cell scope and empty residual branch
assumptions are checked. A supplied audit status, a wrapper's successful exit,
or a metadata-only review cannot substitute for the required proof acceptance.

**D. Exact union.** The final consumer establishes from its manifest-bound inputs

$$
E_{\rm old}\cap E_{\rm new}=\varnothing,
\qquad E_{\rm old}\cup E_{\rm new}=M\setminus C.
$$

Duplicate receipts do not count twice. Missing cases, mismatched zero-based
indices, unproved transfer to supersets, or a side smaller than the declared
cap invalidate this condition.

**E. D4 lemma.** The exact closed-cover/overlay finite computation is accepted
with the frozen source hashes, verified half-turn and canonical conventions,
and a fresh source-bound acceptance receipt. A replay log is insufficient as
the final dependency binding. The bridge theorem is conditional on D; the
accepted global consumer discharges that premise using the exact exclusion union.

**F. Candidate theorem.** The final case438 composition is accepted for every
packing of side S<=T satisfying its closed-cell antecedent in the centered
U-frame. The local receipt, all geometric branch premises, exact angle seams,
label map and U-to-T translation must refer to the same source states.

**G. Final composition and published artifact.** The final proof manifest binds
A–F, includes every proof dependency, and claims no larger scope than their
logical implication. This release-level exposition refers to that accepted
manifest and preserves the statement that this is a computational certificate proof. It is an
explanation outside the immutable evidence manifest, not an extra computational
premise. A formally verified theorem is not claimed.

The source project records a completed calculation of these obligations.
The public copy must be evaluated using the explicit publication validation
scope; its preparation is not itself a new full geometric replay. No claim
is made that implementation or mathematical mistakes are impossible. An independent review must examine the
mathematical reductions and the source implementing them; reproducing the run
provides reproducibility evidence, while formal verification would establish
the checker implications within a proof assistant.

## 10. Deduction of the optimum

Suppose, for contradiction, that a packing exists at some side S<T. Translate
it into the centered U-frame as in Section 3 and apply the accepted lemmas. By the complete exclusion union, its every
valid closed-cell assignment, and those of each D4 image, must have a canonical
mask in C. By the exact D4 lemma, some image admits precisely J_438. D4 preserves
the concentric side-S container and all square shapes. The complete candidate
theorem then forces that image to be the exact construction of span T, contrary
to S<T.

There is therefore no packing at any side below T. The exact construction in
Section 2 supplies a packing at T, so s_11=T. No compactness or limiting-step
assumption is needed: the argument directly excludes every putative smaller
packing. All uses of strictness concern certified inner containment or a
strict center-distance obstruction; legal touching and closed cover boundaries
remain in the problem throughout.

## 11. Proof data and trust boundary

The equations and induction above explain what is proved by the finite
calculations. The complete rational coordinate lists, combinatorial
inventories, dual coefficients and geometric traces are supplied as proof data,
not replaced by decimals in this document. Their checkers use integer/rational
arithmetic, exact number-field reduction and justified interval bounds. Search
heuristics may propose certificates, but their reported success is not an
acceptance rule.

The operational trust base comprises the displayed mathematical reductions,
the reviewed checker source and dependencies, exact arithmetic libraries and
runtime, and the computing system executing them. Source hashes identify
those inputs; hashes alone do not establish the truth of the recorded geometry.
Independent source review and source-distinct reconstruction reduce common
failure modes but do not turn this into a proof-assistant development.

The evidence directory contains the accepted global manifest, the complete
exclusion/capture inventory, the source and data files used by the verifier,
and replay scripts. Execution logs and pre-resume snapshots are not included
in this publication; they are not mathematical proof objects. The public upstream project and its
local theorem provide provenance and local mathematics; the global conclusion
rests on the additional complete case union, D4 bridge, and full candidate
capture described here.


## 12. How the 23 verification stages support the theorem

The table explains each verification stage. A stage name is an operational label;
its mathematical force comes from the checked rules described above.

| Stage | Recorded name | Role in the proof |
|---:|---|---|
| 1 | `original-package-check` | Check the initial package bindings before replay. |
| 2 | `baseline-full-geometry` | Replay the baseline geometric certificates supporting 1,931 excluded canonical cases. |
| 3 | `prior-76-full-geometry` | Replay the 76 extension certificates and their required geometry. |
| 4 | `returned-173-full-geometry` | Replay the 173 returned case certificates. |
| 5 | `prior-strict-integration` | Bind the earlier results into the strict 2,007-case exclusion union and discharge the supported conditional premises. |
| 6 | `symmetry` | Reconstruct the exact D4 overlay and exhaust the finite reduction to case438. |
| 7 | `candidate-construction` | Verify the exact witness and endpoint data. |
| 8 | `candidate-cover` | Check the closed center cover and relevant candidate conventions. |
| 9 | `candidate-local-algebra` | Reconstruct source-bound algebraic packing/contact data. |
| 10 | `candidate-local-baseline` | Replay the original exact local certificate checks. |
| 11 | `candidate-local-weighted` | Replay the coordinatewise dual and curvature calculations used by the focused argument. |
| 12 | `candidate-focused` | Check the focused rectangle, negative features and strict weighted dual inequalities. |
| 13 | `candidate-feature-bridge` | Check the relationship between elementary geometric separation features and the local derivative branches. |
| 14 | `candidate-root-geometry` | Replay the unconditional candidate root geometry. |
| 15 | `candidate-far15-geometry` | Replay the first far-branch contradiction. |
| 16 | `candidate-far13-geometry` | Replay the second far-branch contradiction. |
| 17 | `candidate-far2-geometry` | Replay the third far-branch contradiction. |
| 18 | `candidate-near-geometry` | Replay the surviving near branch and its full geometry ancestry. |
| 19 | `candidate-composition` | Bind the branch partition, geometry and local theorem into the case438 capture conclusion. |
| 20 | `candidate-consumer-tests` | Exercise acceptance/rejection controls for the candidate consumer. These tests supplement source review; they are not themselves a packing theorem. |
| 21 | `candidate-summary` | Bind the candidate results into the summary consumed by final composition. |
| 22 | `fresh-manifest` | Record the accepted input bytes and identities. |
| 23 | `final-global-composition` | Check the complete noncandidate union, the D4 premise discharge and candidate conclusion together. |

The baseline uses 59 field certificates and 34 generic certificates. A
certificate may imply exclusions for more than one full eleven-cell case, so
93 baseline certificates and 1,931 baseline exclusions are different counts.
The transfer from a smaller occupied antecedent to a containing eleven-cell
case must be justified by containment of the antecedent: every full packing
in the larger case would restrict to a forbidden subconfiguration. The
accepted ledger performs the corresponding exact mask bookkeeping.

The final exclusion count is

$$ 1931+76+173=2180=2184-4. $$

This equation is useful for orientation but does not prove exhaustion. The
final consumer checks the actual canonical sets, excludes duplicate counting,
and leaves exactly `438,999,1462,1659`. The D4 theorem uses precisely that
four-element residual set. The local theorem then handles the exact occupied
assignment `438` after its global capture argument.

The earlier computations used to discover a certificate need not be repeated
to validate it. A replay checks the rational data, the inclusion directions,
the exact inequalities and the proof dependencies. If a discovery heuristic
made an unsound suggestion, a sound checker would reject it. Conversely,
accepting a certificate requires a sound checker; deterministic reexecution
alone cannot prove the source's mathematical correctness.

## 13. Reading and independently reviewing this release

Start with Sections 1, 3, 4, 6, 8 and 10 to understand the global implication.
Then inspect Section 5 together with the geometric checker sources to review
the largest family of finite exclusions. Finally inspect Section 7 and its
local algebra/checker sources to review the endpoint argument. The complete
coordinate lists and dual vectors are machine-readable proof data; there is
no need to print them in this exposition to make their role explicit.

Useful entry points are:

| Artifact | Purpose |
|---|---|
| [Global consumer](src/evidence/code/verify_recorded_proof.py) | Final set, premise and source-binding checks. |
| [Full replay runner](src/evidence/RUN_ALL.py) | Orchestrate the expensive geometric replays and final composition. |
| `work/evidence/inputs/PROOF_MANIFEST.json` | Identify the exact input bytes accepted by the final consumer. |
| `work/evidence/results/GLOBAL_PROOF.json` | State the accepted theorem, exact endpoint and premise receipts. |
| `work/evidence/results/baseline-portable/HISTORICAL_BASELINE_RESULT.json` | Identify the baseline union and its source-bound records. |
| `work/evidence/results/prior-union/PRIOR_UNION_RESULT.json` | Record strict integration of the 76 extension cases. |
| `work/evidence/results/returned/SUMMARY.json` | Identify the 173 returned exclusions. |
| `work/evidence/results/d4-bridge.json` | Record the independently reconstructed exact symmetry bridge. |
| `work/evidence/results/candidate-replay/summary.json` | Bind the local/capture/composition stage results. |
| [Continuum scope review](src/evidence/docs/V9_CONTINUUM_SCOPE_REVIEW.md) | Explain how the reviewed geometric checker handles all real poses, closed boundaries and strict ownership. |
| [Focused rectangle argument](src/evidence/research/global-math/FOCUSED-LOCAL-RECTANGLE.md) | Detail the analytic estimates behind the focused local theorem. |

A reviewer should distinguish three kinds of statements:

1. A **mathematical rule**, such as strict ownership implying that a closed
   Minkowski region is forbidden. Its validity is a theorem about continuous
   geometry and cannot be established by counting successful case files.
2. A **certificate instance**, such as a specified rational polygon, interval
   or nonnegative dual vector satisfying the premises of that rule. Its finite
   algebraic checks are what exact replay performs.
3. An **integration statement**, such as the equality of the excluded set with
   the complement of the four candidate cases. This binds checked instances
   to the full problem and prevents omissions, stale receipts, wrong frames or
   conditional results from being counted as unconditional exclusions.

The final theorem needs all three. Neither a numerical packing search nor a
collection of local rigidity certificates alone supplies the exhaustive global
argument.

An independent implementation may use different geometric algorithms or proof
data, provided it proves the same implications. For example, it may replace
the polygon-cover arrangement procedure with a triangulation certificate, or
replace the existing finite D4 search with an independently checked exhaustive
tree. It must preserve degenerate closed intersections and the exact cap,
scaling, labels and branch conditions.

## 14. Exactness, boundaries, and scope: points that must survive reuse

**The irrational endpoint and rational cap have different jobs.** The exact
construction and local isolation are expressed at T. Most global geometric
exclusions operate at U>T, allowing rational coefficients. Monotonicity embeds
a putative smaller packing into U; the exact rigid coordinate map in Section 8
then embeds that same centered packing into the T-frame for the local theorem.
There is no approximation step replacing one side length by the other.

**The scale B changes both squares and coordinates.** In the field frame, the
container side is L and each small square side is B. Reading the field
certificates as eleven unit squares in a side-L container would be an incorrect
interpretation. Returning from field to physical coordinates divides by B.

**Angles are continuous.** The pose rows cover closed intervals of the
half-angle parameter t. Polynomial inequalities are verified on whole intervals.
The focused rectangle uses actual angular displacements in radians, bounded
from t by the derivative of `2 arctan(t)` and the quarter-turn chart change.
Finite angular sampling would not prove the result.

**Contacts remain legal.** Feasible non-overlap and wall containment use weak
inequalities. Strictness appears only where needed to justify a forbidden
interior-overlap region or a strict center-distance obstruction. Neither
zero-area residuals nor equality cases in the branch partition are silently
removed.

**Symmetry is applied to the physical packing.** The half-turn induces the
verified label involution, but other D4 elements need not permute the cells.
Their action is handled by exact intersections of inverse-image cells. The
proof never needs an arbitrary cell-boundary tie-break to commute with D4.

**Local isolation becomes global only after capture.** The local theorem says
that a particular rectangle around a particular exact labeled construction
contains no different feasible packing in its fixed T-container. The case
exclusions, D4 bridge and complete four-way capture partition establish that
every hypothetical smaller packing reaches that rectangle. All these links
are essential to the final conclusion.

**The theorem does not depend on historical novelty.** This document records
the argument and its executed computational evidence. Attribution of the
construction follows the pinned sources. No priority claim, publication claim,
or claim of completed outside peer review is part of the proof.

## 15. Relationship to a future formal proof

This release is a reproducible computational certificate proof with an explicit
mathematical and software trust boundary. It contains no completed Lean
formalization. A future formalization should make the above implications
machine-checked, rather than treat `PASS_COMPLETE_ELEVEN_SQUARE_OPTIMALITY` as
an axiom.

A suitable division is to prove the geometric and analytic rules once, express
the rational/algebraic witnesses as finite data, and prove soundness of their
checkers. The expensive discovery searches may remain outside Lean. A formal
final theorem would combine: existence of the exact construction at T;
completeness of the center-cover/canonical-case reduction; sound case exclusions;
the symmetry bridge; the complete candidate capture; and the local isolation
argument with its exact frame conversion.

The recorded Python results are useful reference outputs for debugging such
an implementation. Their role is evidential and practical; the future formal
proof must independently establish that the accepted finite checks imply the
actual theorem about arbitrary eleven-square packings. Source hashes establish
identity of evidence, not mathematical truth. A completed formalization would
therefore reduce the present trust in the checker implementations and prose
reductions, while retaining the usual trust in its proof kernel and execution
environment.
