# Eleven unit squares: exact endpoint and certificate proof

**Verification handoff, 27 September 2026.** The 173 returned cases have
completed fresh exact replay. The strict 2,007-case earlier union, the exact
D4 computation, and all nine packaged candidate stages have passed their
respective checks. These are completed component results, not an executed
final global acceptance check.

The final combined verifier and independent full replay
are provided for local execution. `ONE_COMMAND.md` gives the command.
The newly assembled end-to-end runner has not itself been executed. Therefore
this document presents the exact mathematical proof with explicit computational
acceptance conditions, and does not yet assert final global acceptance. Earlier
references below to pending exclusion/integration obligations describe those
final composition gates; they do not mean the 173 component replays are unfinished.

The method uses exact rational geometry and exact algebraic-number calculations.
It is an inspectable computational-certificate proof, conditional on the stated
checker and arithmetic trust base, **not** a proof checked by a formal proof
assistant. No historical priority or novelty claim is made.

The construction is taken from the pinned upstream `jlevy/squares` sources in
the bundle. Their `packing/cases/trump11/packing.py` attributes the packing to
Walter Trump and says its reconstruction follows David Ellsworth's diagram.
Those historical credits are inherited from that source. The upstream
[local-isolation theorem](https://github.com/jlevy/squares/blob/main/packing/cases/trump11/isolation-theorem.md)
is a local theorem; it is not itself a claim of global optimality. The exact
archived source and its recorded content hashes, rather than the changing
public branch, define the inputs used here.

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

**Theorem, with explicit computational acceptance condition.** If the exact
construction verification, complete 2,180-case exclusion inventory, exact D4
bridge, and complete case438 capture described below are accepted with their
stated source and dependency bindings, then

$$ s_{11}=T. $$

The proof of this implication is given below. Section 9 states exactly what
must be checked to remove the outstanding verification condition.

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

`research/recovered-checkpoint/research/jlevy/packing/cases/trump11/packing.py`.

The local source loader also invokes an exact packing verifier before forming
any derivative matrices. The fresh source-bound algebra audit is
`research/local-radius/fresh-local-algebra.json`. The final package must retain
the pinned exact construction, its arithmetic dependencies and those bindings.

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

`research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json`.

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
`research/phase3/work/phase3/hull/audit_capture_v9.py`. Its exact geometric
rules are separate from the producer's discovery routines. Every accepted
receipt must bind its source trace, full ancestor chain, seed, cover, side U,
scale B, and executed checker dependencies. Counts, successful process exit,
and supplied status labels do not by themselves meet this requirement.

Some earlier exclusions use necessary D4 center halfplanes. Their use is
legitimate only through the separately audited support theorem and
`research/global-math/overlay_field_halfplanes_v2.py`, which checks each
halfplane on every original vertex of every independently surviving support
region. The discharge consumer checks these premises and the independent
conditional geometric contradiction. That dependency starts from the
immutable original 1,931-case exclusion baseline. It must remain acyclic; the
final four-candidate D4 bridge below is not used to prove its own
noncandidate-exclusion premise.

**Pending finite exclusion lemma.** Once the strict pre-return union and all
returned cases are independently accepted and merged, they must establish

$$ E=M\setminus C,\qquad |E|=2180, $$

where every member of E is impossible at the same cap U. Until that exact set
equality and its proof dependencies are checked, this lemma is a pending
obligation rather than an established premise.

The planned inventory has 2,007 pre-return exclusions and 173 returned cases.
The last older strict union contained only 1,997 cases; the ten additional
pre-return cases

`927,998,1111,1112,1114,1115,1124,1125,1128,1143`

must be source-bound into the strict 2,007-case union. The arithmetic
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
`research/finalization/global-composition/audit_d4_bridge.py`. It reconstructs
the cover and all overlay geometry, verifies the exact half-turn and index
conventions, checks every used distance ban, and exhausts a source-distinct
bitset search. No producer solver conclusion is accepted as a premise. The
source-bound final acceptance of its replay is an explicit global gate.

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
commutes with a symmetry. A complete proof of this lemma and its source
conventions is in `D4-BRIDGE-THEOREM.md` in this directory.

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
`research/global-math/audit_focused_local_box.py` and
`research/global-math/focused1024-local-box-independent.json`. They bind the
exact original coordinate packet and its fresh independent replay. A separate
review reconstructs the raw contact-feature enumeration; ten negative controls
check the local consumer's source, frame, angle and radius rejection rules.
The detailed analytic explanation is
`research/global-math/FOCUSED-LOCAL-RECTANGLE.md`.

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
contained in a square of side S<T. Thus, once the complete composition is
accepted, case438 has no packing of side below T. This is **not** a claim that
case438 is infeasible at U; cap-U perturbations are allowed by the proof's
scope.

The final candidate consumer is
`research/candidate-capture/audit_complete_capture438.py`. Its acceptance must
bind the unconditional Phase2 root, the three far-branch contradictions, the
full near-state ancestry, the focused local receipt, the complete partition,
and the exact endpoint/frame identities. Its latest executed receipt must
match the final checker source. An acceptance obtained before later source
edits is not acceptance of the later code.

## 9. All-or-nothing global verification conditions

The proof is ready to be asserted as a completed endpoint result only when the
final consumer establishes every condition below.

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

**D. Exact union.** The final manifest establishes

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
the final dependency binding. The theorem remains conditional on D until the
global consumer discharges that premise.

**F. Candidate theorem.** The final case438 composition is accepted for every
packing of side S<=T satisfying its closed-cell antecedent in the centered
U-frame. The local receipt, all geometric branch premises, exact angle seams,
label map and U-to-T translation must refer to the same source states.

**G. Final composition and published artifact.** The final proof manifest binds
A–F, includes every proof dependency, and claims no larger scope than their
logical implication. The prose and PDF correspond to that same accepted
manifest and preserve the statement that this is a computational certificate
proof. A formally verified theorem is not claimed.

At this draft stage B–D and final composition acceptance are explicitly pending.
D4 execution/receipt acceptance and final candidate source matching must be
recorded by the final verification run; no inferred success from this
draft or a stale status file fills those gates. If any condition fails or
remains unverified, the permitted conclusion is a conditional theorem and the
precise list of missing obligations, not global optimality.

## 10. Deduction of the optimum after acceptance

Assume A–G. If a packing existed at some side S<T, translate it into the
centered U-frame as in Section 3. By the complete exclusion union, its every
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

The final proof directory should contain the accepted global manifest, the
complete exclusion/capture inventory, all required source and data files or
hash-verified recoverable archives, and reproducible replay instructions.
The public upstream project and its local theorem provide provenance and local
mathematics; the global conclusion, if accepted, rests on the additional
complete case union, D4 bridge, and full candidate capture described here.
