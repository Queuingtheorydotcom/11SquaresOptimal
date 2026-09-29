# A focused rectangle around the eleven-square candidate

This proves a local statement conditional on the final pose domains in
`research/candidate-capture/near-refined1024-240.json`. The independent geometry
ancestry and branch coverage must separately establish that every packing in
its stated case enters those domains. No global optimality is inferred here.

The exact witness side is denoted by T. Centers in the source use the scaled
positive U-frame, with U = 387708359002281417731/10^20 and B = (191/50)/U.
The mask438 witness chart is the quarter turn Q(X,Y)=(-Y,X). For a source center
(x,y), its centered witness-chart coordinates are therefore

    Q^{-1}(x/B-U/2,y/B-U/2) = (y/B-U/2,U/2-x/B).

Adding (T/2,T/2) gives the witness's original positive T-frame. A packing in a
centered container of side S <= T satisfies the T-frame wall inequalities.
This formula includes the difference between U and T exactly; it does not
identify their centers by numerical rounding.

The independent checker reconstructs all target centers from the algebraic
witness and verifies its first six squares have angle zero and its final five
have half-angle alpha, the isolated degree-eight root. The inverse quarter
turn preserves square orientations modulo pi/2. For an axis square, an angle
row [a,b] near t=0 has |delta theta| <= 2b; a row near t=1 has
|delta theta| <= 2(1-a)/(1+a), using the square's quarter-turn symmetry. For a
tilted square, both t and alpha are nonnegative in the same chart, and

    |delta theta| <= 2 max(|a-alpha_upper|,|b-alpha_lower|)
                        / (1+min(a,alpha_lower)^2).

These follow from theta=2 arctan(t) and the mean value theorem. Each center
coordinate is enclosed by independently evaluating its algebraic witness
coordinate and all vertices of every surviving residual polygon. Convexity
then covers every polygon point. The resulting radii r_j are rounded outward
to multiples of 10^-10. All 136 surviving pose rows, containing 1,542 listed
vertices, fit this rectangle. Every radius is below the previously audited analytic working-box radius
1/64. This working box bounds the derivatives; it is distinct from
the older uniform isolation radius 1/248. The new angle radius for square 10
is about 0.006765 and exceeds 1/248.

For a contact elementary function with moving separating axis owned by square
o and other square p, write the center difference as d and the other square's
corner offset as z. Apart from a sign and constant, the gap is

    g = a_o . (d+z).

On a straight segment of perturbations bounded coordinatewise by the radii,
put w_i = r_{3i+2} and

    V_ij = sqrt((r_{3i}+r_{3j})^2+(r_{3i+1}+r_{3j+1})^2).

The second derivative is bounded in absolute value by

    K_g = D_ij w_o^2 + 2 V_ij w_o + (1/sqrt(2))(w_o+w_p)^2,

where D_ij bounds center separation throughout the old uniform chart. This is
the sum of the rotating center-projection term, its mixed derivative, and the
relative rotation of the other square's corner. A wall elementary function
has bound K_g=(1/sqrt(2))w_i^2. The checker independently bounds D_ij against
exact squared witness distances and uses rational upper bounds for square
roots. For a derivative row with several matching elementary functions, it
uses the maximum curvature bound.

For every unavailable contact feature, one of its corner inequalities has
negative value at the witness. The exact Taylor estimate

    g(0) + sum_j |partial_j g(0)| r_j + K_g/2 < 0

holds for all 88 such features. Thus none can become a separating feature
inside the rectangle. The previously audited enumeration of 128 derivative
branches consequently remains exhaustive for feasible packings in it.

For each branch and each signed coordinate j, the old audited nonnegative dual
vector gives that signed coordinate row up to residual l1 norm epsilon_j.
Let M_j be its weighted sum of the new curvature bounds. The checker proves

    M_j < 2 (r_j - epsilon_j max_k r_k)

for all 128*66 = 8,448 signed-coordinate certificates. The largest ratio of
left side to right side is approximately 0.6765052083.

To conclude local isolation, suppose a distinct feasible perturbation delta
lies in the closed rectangle. Put

    s = max_j |delta_j|/r_j,   0 < s <= 1.

Choose a saturated coordinate j and the dual certificate whose sign is
opposite to delta_j. Write delta=s*v, with |v_k|<=r_k. Every selected tied
inequality satisfies the Taylor bound g(delta)>=0, so its linear part is
bounded below by -K_g*s^2/2. The nonnegative dual and its residual then give

    s r_j <= epsilon_j s max_k r_k + M_j s^2/2.

After dividing by s, the displayed strict dual inequality forces s>1, a
contradiction. Hence the rectangle contains only the exact candidate packing
at side T, and no packing at a smaller side. This conclusion uses all
coordinatewise radii together; it does not assert a larger uniform ball.

The independent receipt is
`research/global-math/focused1024-local-box-independent.json` and the checker is
`research/global-math/audit_focused_local_box.py`. It binds the fresh independent
weighted-coordinate replay and the exact witness sources. The geometry source
and its branch assumptions remain explicit external premises.
