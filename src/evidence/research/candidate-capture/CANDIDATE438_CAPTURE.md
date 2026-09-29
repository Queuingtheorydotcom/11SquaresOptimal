# Capture of the candidate case 438

The computation closes the candidate case that remained open in the supplied
Phase 3 archive. It does not close the other occupied-cell cases and does not,
by itself, prove global optimality of the eleven-square construction.

Let

\[
T=\frac{6u+4}{1+2u-u^2}=3.8770835900228141773078970601\ldots,
\]

where \(u\in(0.36,0.37)\) is the isolated root of

\[
5u^8-10u^7-2u^6+14u^5+12u^4-6u^3+2u^2+2u-1=0.
\]

The antecedent is the exact occupied-cell mask
\(\{0,1,2,3,4,8,9,10,11,13,15\}\), indexed 438 in the archived centered
cover at the rational side cap
\(U=387708359002281417731/10^{20}>T\).

**Candidate-case conclusion.** Every packing of eleven unit squares with
side \(S\le T\) satisfying this antecedent is the known exact construction,
up to the specified quarter-turn and the associated label assignment.
Consequently it has \(S=T\).

The conclusion follows from four closed branches. Here \(y_{15}\) is the
center's vertical coordinate in the centered unit chart, and
\(t_i=\tan(\theta_i/2)\in[0,1]\) is the square's angle chart.

| Branch assumptions | Closure |
| --- | --- |
| \(y_{15}\le5/4\) | Exact geometric contradiction |
| \(y_{15}\ge5/4,\ t_{13}\le147/512\) | Exact geometric contradiction |
| \(y_{15}\ge5/4,\ t_{13}\ge147/512,\ t_2\le183/512\) | Exact geometric contradiction |
| \(y_{15}\ge5/4,\ t_{13}\ge147/512,\ t_2\ge183/512\) | Every remaining pose lies in a proved local isolation rectangle |

At each split the two inequalities are closed and overlap at equality, so
no boundary or limiting configuration is omitted.

The geometric arguments propagate unavoidable owned points, residual center
polygons, whole closed angular intervals, and pairwise nonintersection
constraints. Independent checkers replay every retained implication with
exact rational arithmetic. The root ownership replay checks 16,551 angular
rows. The last near-branch replay checks 127,630 additional rows, besides
22,811 rows imported from independently replayed and hash-bound premises.
All incomplete producer steps are unpromoted: they add no asserted constraint.

The near branch has 136 live pose rows containing 1,542 polygon vertices.
These whole polygons and angular intervals lie in a rectangular neighborhood
of the exact construction. This rectangle is wider than the previous
isotropic radius in selected angle coordinates, which is why the older
`1/248` capture test did not close the branch.

The new local argument retains all 128 audited active constraint branches.
For every branch and signed coordinate it verifies a nonnegative rational
dual inequality, using a directional second-derivative bound adapted to the
33 separate coordinate radii. All 8,448 inequalities are strict; the largest
ratio of curvature cost to available first-order margin is below 0.676506.
All 88 initially unavailable separating features remain unavailable on the
rectangle, as checked by strict Taylor bounds. The normalized perturbation
argument in `FOCUSED_LOCAL_BOX_LEMMA.md` therefore proves that the only
feasible point in the rectangle at side \(T\) is the exact construction.

The coordinate conversion is explicit. In the propagation field, the box
has side \(L=191/50\) and each parent square has side \(B=L/U\). If \(p\) is
a field center, put \(c=p/B-(U/2,U/2)\). The case symmetry is
\(Q(x,y)=(-y,x)\), and the local anchored center is

\[
Q^{-1}c+(T/2,T/2).
\]

Thus the difference between the cover's \(U/2\) and the local theorem's
\(T/2\) is included. Both angle endpoints 0 and 1 are included; they represent
the same square orientation modulo a quarter-turn. The exact reference axes
and the bijection of all eleven labels are independently checked.

A packing in a centered square of side \(S\le T\) remains feasible in
\([0,T]^2\) after this rigid coordinate map. Isolation makes it equal to
the exact construction. Exact corner identities show the construction touches
all four walls, so its horizontal and vertical spans are both \(T\), forcing
\(S=T\).

The proof objects are:

- `root14-independent-audit.json`: the unconditional ownership induction.
- `far15y-independent-audit.json`, `far13-independent-audit.json`, and
  `far2-independent-audit.json`: the three contradictory branches.
- `near1024-independent-audit.json`: the complete near-branch pose ancestry.
- `../global-math/focused1024-local-box-independent.json`: independent
  rectangle inclusion and local isolation arithmetic.
- `complete-capture438-audit.json`: the complete branch composition, source
  hashes, role mapping, frame conversion, and exact wall-span checks.

The final receipt deliberately records `global_optimality_proved: false`.
The other occupied-cell masks remain a separate mathematical obligation.
