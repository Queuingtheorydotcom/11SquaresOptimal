# Focused rectangular isolation at the eleven-square construction

This lemma concerns a labelled neighborhood of the known construction. It is
not a global packing theorem. The proposed focused box has passed an independent
arithmetic replay, and its source pose domains have passed a separate independent
geometry ancestry replay. Their complete case-438 composition is recorded in
`complete-capture438-audit.json`; independent review of that composition is a
separate final check.

Let `T` be the exact side of the construction, let `z*` be its anchored
center-and-angle chart in `[0,T]^2`, and choose positive rational coordinate
radii `r_j`. Put `R=max r_j`. Assume the box is contained in the previously
audited declared neighborhood, and that one negative elementary corner gap
has been certified throughout the box for every unavailable separating
feature. Every feasible packing in the box then selects one of the same
128 audited active branch matrices `A_b`.

For one pair elementary function, write its axis owner as `o`, the other
square as `p`, their center difference as `d`, and the other square's rotated
corner as `q`. Along a straight chart segment with angular velocities `w_o`
and `w_p` and center-difference velocity `v`, its second derivative, up to its
irrelevant overall sign, is

    -a·d w_o² + 2(Ja)·v w_o - a·q (w_o-w_p)².

Consequently a valid directional curvature bound on the radius box is

    K = D r_theta,o²
        + 2 sqrt((r_x,o+r_x,p)²+(r_y,o+r_y,p)²) r_theta,o
        + (1/sqrt(2)) (r_theta,o+r_theta,p)²,

where `D` is a proved bound for the center distance throughout the declared
box. Rational upper bounds replace both square roots. A wall corner has bound
`K=(1/sqrt(2)) r_theta²`. If several elementary functions have the same active
gradient, use the largest of their bounds for that row.

For every branch and signed coordinate, the existing audited nonnegative
dual vector `lambda` satisfies an entry-enclosure-certified error bound

    ||lambda^T A_b - sign*e_j||_1 <= epsilon.

Define `M=sum lambda_k K_k`. The sufficient strict test is

    M < 2 (r_j - epsilon R).

Indeed, suppose `h=z-z*` is nonzero and in the box, and set
`s=max_j |h_j|/r_j`, so `0<s<=1`. Choose a saturated coordinate `j` and the
signed certificate opposite to `h_j`. Feasibility and Taylor's theorem give

    (r_j-epsilon R) s <= (M/2) s².

The strict test contradicts `s<=1`. Hence the only feasible packing in the
box at side `T` is the construction itself.

The unavailable-feature test is also rectangular: for a corner gap with
negative value at the construction, certify

    value_upper + sum_j gradient_abs_upper,j * r_j + K/2 < 0.

This keeps all 88 excluded features unavailable. It does not presume a single
contact pattern among the 128 active branches.

## Coordinate bridge for case 438

The propagation field has side `L=191/50` and parent-square side `B=L/U`, where
`U` is the archived exact rational upper bound. Its centered unit coordinates
are `c=field_center/B-U/2`. The recorded case-438 symmetry is a quarter-turn
`Q(x,y)=(-y,x)`, together with a bijection between occupied cells and the
eleven construction labels. The anchored local coordinates are

    Q^{-1} c + (T/2,T/2).

Thus the use of `U/2` in the cover and `T/2` in the local theorem is explicit.
For any packing of side `S<=T`, centered embedding and this transformation
place it in `[0,T]^2`. Quarter-turn changes in a square's angle describe the
same square. Axis-square half-angle intervals near `1` use
`t -> (t-1)/(t+1)` to select the chart near angle zero. The tilted squares use
the same isolated algebraic half-angle as the exact construction. Bounds on
`2 atan(t)` follow from its derivative and rational interval endpoints.

The box in `focused1024-local-certificate.json` is derived from every
retained center vertex and full angular interval in the frozen pose receipt.
Its largest signed-coordinate ratio is about `0.676506`, strictly below one;
all 88 unavailable corner upper bounds are negative. Those numbers alone are
not a proof: the source-bound independent replay and the full branch
partition are required. They are supplied by
`../global-math/focused1024-local-box-independent.json`,
`near1024-independent-audit.json`, and the three far-branch audit receipts.
