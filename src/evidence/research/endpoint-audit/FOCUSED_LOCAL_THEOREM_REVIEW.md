# Third-source review of the focused local rectangle

**Result: passed.** The mathematical argument in
`../global-math/FOCUSED-LOCAL-RECTANGLE.md` and its implementation in
`../global-math/audit_focused_local_box.py` have no defect identified by this
review. The source pose domains and their complete branch ancestry remain
external premises. This review establishes neither whole-case capture nor
global optimality.

The frozen focused checker was freshly rerun into
`focused1024-third-source-replay.json`. Every scientific and source-binding
field agrees with the frozen receipt; only elapsed runtime differs. It checks
136 surviving pose rows, 1,542 center vertices, 8,448 signed-coordinate dual
certificates, and all 88 unavailable features. The largest dual ratio remains
approximately 0.6765052083.

## Directional curvature

For one elementary pair inequality, apart from its sign and a constant, write
the smooth function as

\[
g=a_o\cdot(d+z),
\]

where the axis \(a_o\) has unit length, \(d=c_p-c_o\), and \(z\) is a corner
offset of the other square. Let \(v\) be the center-difference velocity and
\(\omega_o,\omega_p\) the two angular velocities along a straight segment
in the 33-coordinate chart. Direct differentiation gives

\[
g''=-a_o\cdot d\,\omega_o^2
     +2Ja_o\cdot v\,\omega_o
     -a_o\cdot z\,(\omega_p-\omega_o)^2.
\]

The axis owner's own supporting edge contributes the constant \(1/2\), so
there is no omitted motion of an owner corner. Unit-square corner offsets
have length \(1/\sqrt2\). Hence the checker's bound

\[
K=D_{op}r_{\theta,o}^2+2V_{op}r_{\theta,o}
 +(1/\sqrt2)(r_{\theta,o}+r_{\theta,p})^2
\]

is valid, where
\(V_{op}^2=(r_{x,o}+r_{x,p})^2+(r_{y,o}+r_{y,p})^2\).
Its rational square-root upper bounds are outward bounds, checked by exact
integer arithmetic. The center reach \(D_{op}\) is explicitly checked against
the exact squared witness separation plus \(2\sqrt2/64\), covering the
entire old working box. All proposed coordinate radii lie within that box.
A wall corner needs only \((1/\sqrt2)r_\theta^2\).

Taking the maximum over all zero-valued elementary functions with the same
gradient is essential and is implemented correctly. A zero first angular
derivative does not remove that variable from the curvature calculation.

## Nonlinear features and branch completeness

For every touching pair, the separating-axis theorem supplies eight raw
features: two choices of axis owner, two axes, and two orders. A feature is
the conjunction of the four corresponding corner inequalities. The checker
keeps one negative corner inequality strictly negative throughout the
rectangle for every initially unavailable feature, using

\[
g(0)+\sum_j |\partial_jg(0)|r_j+K/2<0.
\]

The new independent cross-check `check_focused_feature_bridge.py` reconstructs
the raw alternatives directly from these elementary corner inequalities. It
confirms 14 touching pairs, 112 total features, 24 active features, and exactly
88 unavailable features. For every active feature its tied elementary
gradients equal the corresponding tangent option's complete row set.

Enumerating all raw corner-feature choices independently gives 512 nonlinear
selections and exactly the same 128 derivative matrices as the retained
branch inventory. The 88 omitted features are exactly those listed in the
focused receipt's strict Taylor stability certificates. These results are
recorded in `focused-feature-bridge-review.json`.

All active wall constraints are included. Conditions for previously separated
pairs and inactive wall inequalities can be omitted from this necessary
system: every feasible packing still satisfies the selected contact and
active-wall conditions. No completeness assertion for those omitted
constraints is needed to obtain a contradiction from this weaker system.

## The normalized displacement argument

Let \(\delta\ne0\) lie in the rectangle and set
\(\tau=\max_j |\delta_j|/r_j\), so \(0<\tau\le1\). Choose a saturated
coordinate and the retained signed dual with sign opposite to that
coordinate. Nonnegative dual weights, the certified residual norm
\(\epsilon\), and Taylor's theorem give

\[
0\le-\tau r_j+\epsilon\tau R+\frac12\tau^2M,
\qquad R=\max_k r_k.
\]

The strict tested inequality \(M<2(r_j-\epsilon R)\), with positive right
side, forces \(\tau>1\). All 66 signed-coordinate choices occur in every
one of the 128 branches. The argument therefore excludes every nonzero
feasible displacement in the closed rectangle. It makes no claim about a
uniform ball whose radius equals the largest individual coordinate radius.

## Chart and container conversion

The source field has square side \(B=(191/50)/U\). The inverse of the recorded
quarter turn is applied to the exact centered coordinates, giving

\[
(x,y)\longmapsto(y/B-U/2,\ U/2-x/B).
\]

The checker compares this pair to the algebraically enclosed witness center
minus \((T/2,T/2)\). Thus the displacement is exactly the one obtained by
adding \((T/2,T/2)\) and using the fixed anchored local chart. The rational
search cap \(U\) is never substituted for the algebraic witness side \(T\).
For a centered packing of side \(S\le T\), the resulting configuration is
feasible in the anchored container of side \(T\).

For axis squares, the half-angle branches near zero and one respectively
select the angle representatives \(2\arctan t\) and
\(2\arctan t-\pi/2\). The two rational bounds in the checker cover these
branches, including their seam endpoints. Tilted squares use a single chart
near the exact isolated root; the checker's mean-value estimate bounds the
full angular interval, including algebraic endpoint uncertainty. All angle
radii are in radians. The role assignment is checked to be a bijection and
the witness's actual edge directions are checked exactly.

## Scope and recorded inputs

The feature cross-check shares the frozen exact number-field and witness
implementation. The elementary smooth functions and their directional
derivatives were also reviewed analytically above. The fresh weighted-dual
replay supplies the previously established residual bounds and nonnegative
weights; its hash is bound in the focused receipt.

To use the theorem as a closed search leaf, an independent geometric replay
must establish the entire source pose domain with its stated branch
conditions. The full parent partition must then cover every case being
claimed captured. A hypothetical smaller-side packing can be padded to side
\(T\), where local isolation forces it to be the spanning construction and
gives the final contradiction. These source-coverage steps remain separate
from the local theorem reviewed here.

The exact hashes of the reviewed note, checker, frozen receipt, proposal,
fresh replay, and feature cross-check are in
`focused-local-theorem-review.json`. No frozen proof source or receipt was
modified by this review.
