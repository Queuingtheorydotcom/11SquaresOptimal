# A directly checked quantitative neighborhood of Trump's packing

**Later, stronger checked result:** the [coordinate-certificate extension](TRUMP-LOCAL-COORDINATE-RADIUS.md) gives closed radius $1/248$ and open radius $0.004042573473645$, with an independent exact replay. The conservative proof and witnesses below remain valid.

This derives a conservative explicit radius from the **existing** full-variable tangent packet in [jlevy/squares](https://github.com/jlevy/squares). It does not establish global optimality. It does not accept the source's larger retained radius without replaying that radius's separate modulus certificates.

Let $z_*$ be the exact labelled Trump pose and $U$ its side. In the anchored chart

$$
z=(x_0,y_0,\theta_0,\ldots,x_{10},y_{10},\theta_{10}),
$$

angles are in radians and the container is $[0,U]^2$. The exact checks below prove:

> **Concrete local exclusion.** If $z$ is a packing in $[0,U]^2$ and
> $\|z-z_*\|_\infty\le 1/120000$, then $z=z_*$. A packing at any side $S<U$ cannot have such a labelled pose.

The computed branch-dependent bounds also certify the larger **open** radius

$$
\rho=\frac{8944486691}{10^{15}}=0.000008944486691.
$$

The smaller closed radius makes a convenient box for future global-cover pruning. Relabelling and symmetry images can each receive their corresponding box. These boxes do not cover arbitrary other packings.

## Verified inputs

The [earlier replay](TRUMP-LOCAL-REPLAY.md) reconstructs all 512 raw separating-feature branches and their 128 derivative-distinct matrices $A_b\in\mathbb Q(u)^{42\times33}$. Each has a strictly positive stress $\lambda_b$ with $A_b^T\lambda_b=0$ and an invertible 33-row minor $B_b$. The exact packing, source hashes and branch map agree with the retained author packet.

The new [checker](quantitative_trump_local.py) reconstructs these objects and matches every branch row to a smooth zero-valued elementary wall or pair function. It uses no numerical face-LP bound. [Exact receipts](trump-local-conservative-radius.json) retain the rational inverse proposals and every branch bound. Floating arithmetic only proposes inverse matrices; the following acceptance inequalities use integers and fractions.

## Rational inverse and stress bounds

For every minor $B$, exact rational interval evaluation on an isolating interval of width below $10^{-45}$ gives a rational approximation $\widehat B$ with entrywise error at most $10^{-12}$. A proposed inverse $J$ is rounded to denominator $10^9$.

The checker calculates

$$
e=\|I-J\widehat B\|_\infty
  +\|J\|_\infty\frac{33}{10^{12}}<1
$$

exactly. The first term is an integer-matrix calculation after clearing denominators. Consequently the Neumann series gives

$$
\|B^{-1}\|_\infty\le H:=\frac{\|J\|_\infty}{1-e}.
$$

Rational interval evaluation of the reconstructed stresses gives

$$
\frac{\sum_j\lambda_j}{\min_j\lambda_j}\le T.
$$

All 128 branches satisfy the especially simple exact bounds **$H<89$ and $T<158$**. The largest inverse-residual bound is below $1.282\cdot10^{-8}$.

For $a_j$ the rows of $A$ and $\delta=\max_j(-a_jv)$, positivity and $\sum_j\lambda_ja_jv=0$ imply $\delta\ge0$ and $|a_jv|\le T\delta$ for every row. Since every row of $B$ is among these rows,

$$
\|v\|_\infty\le H\|Bv\|_\infty\le HT\delta.
$$

Thus the cone modulus is at least $1/(HT)$. The minimum computed branch-dependent lower bound is approximately $0.0000715558935321$; no numerical value is used for acceptance.

## Uniform nonlinear and branch-stability bounds

Work first in the larger chart box $\|z-z_*\|_\infty\le1/64$. Exact evaluation proves $U<4$. The distance between two centers anywhere in this box is therefore less than

$$
D:=\frac32\left(4+\frac1{32}\right)=\frac{387}{64},
$$

using $\sqrt2<3/2$. A pair's elementary separating function has the form

$$
g(z)=\varepsilon n(\theta_i)\cdot
\bigl(c_j-c_i+R(\theta_j)q\bigr)-\frac12,
\qquad \varepsilon\in\{-1,1\},\quad \|q\|_2=1/\sqrt2.
$$

Its gradient coefficient sum is at most $D+3\sqrt2<12$. Its Hessian absolute-entry sum is at most $D+6\sqrt2<16$: center-angle mixed entries contribute at most $4\sqrt2$, the rotating corner's four angle-angle entries contribute $2\sqrt2$, and the owner-angle second derivative of the center term contributes $D$. Wall functions satisfy smaller bounds. Hence

$$
|g(z_*+v)-g(z_*)-\nabla g(z_*)\cdot v|
\le 8\|v\|_\infty^2.
$$

Exact interval evaluation of all 1,936 elementary function values proves every nonzero value has absolute value above $1/250$. Thus within radius $1/3000$, the gradient bound 12 keeps every initially negative separating-corner gap strictly negative. An unavailable separating feature cannot become available. Every feasible pose there therefore selects one of the complete retained raw branches, and all its active rows satisfy

$$
a_jv\ge-8\|v\|_\infty^2.
$$

With $r=\|v\|_\infty>0$, the linear and nonlinear bounds imply

$$
\frac r{HT}\le\delta\le8r^2,
\qquad\text{hence}\qquad r\ge\frac1{8HT}>
\frac1{8\cdot89\cdot158}=\frac1{112496}.
$$

Since $1/120000<\min\{1/64,1/3000,1/112496\}$, this proves the stated closed-box exclusion. Using each exact $H_bT_b$ instead gives the recorded larger open radius.

Any pose at a smaller side embeds in $[0,U]^2$. The only pose left in this box is $z_*$, which reaches the far walls of its exact container, so it cannot fit a smaller side. No symmetry-distance or quantitative curvature packet from the source is needed for this implication.

## Scope and reproduction

This is a checked quantitative consequence of an existing local proof. It uses the existing exact geometry and branch construction, with a different, conservative cone-modulus certificate. The retained author's approximately $0.00404257$ radius remains outside this replay's claim. No statement locates every possible eleven-square packing in these small boxes.

From the workspace root:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python research/classical/quantitative_trump_local.py
```

The run uses one worker and about 20 seconds in the shared environment.
