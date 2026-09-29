from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];reg=json.loads((ROOT/'work/phase2/audit/current-union-independent-audit.json').read_text());E=reg['excluded_canonical_cases'];R=reg['remaining_canonical_cases'];N=len(reg['entries'])
lines=[]
for e in reg['entries']:
 owners=', '.join(map(str,e['required_owner_cells']));positive=', '.join(e['positive_cell_thresholds']);forced=sum(e['positive_cell_thresholds'].values());lines.append(f"| {e['base_mask_index']} | {owners} | {positive} | {forced} > {e['budget_units']} | {e['canonical_cases']} |")
report=rf'''# Eleven squares: exact continuation and remaining proof gap

**Full optimality has not been proved.** This continuation certifies {E} of the 2,184 canonical occupied-cell cases, leaving **{R} unresolved**. At the start of this continuation, 240 cases were excluded and 1,944 remained. The improvement is {E-240} additional exact case exclusions. It does not improve the established numerical bracket:

\[
3.8754 < s(11) \le T=3.877083590022814177307897060100962706376\ldots.
\]

Here $s(11)$ is the smallest container side for eleven unit squares, each allowed an independent rotation. The upper bound is the known construction. In the retained exact parameterization,

\[
T=\frac{{6u+4}}{{1+2u-u^2}},\qquad
5u^8-10u^7-2u^6+14u^5+12u^4-6u^3+2u^2+2u-1=0,
\]

where $u$ is the isolated root near $0.3657693$. The exact algebraic comparison used here is $T<U$, with

\[
U=\frac{{387708359002281417731}}{{10^{{20}}}}.
\]

The separate global lower bound 3.8754 was retained and audited in the preceding checkpoint. This continuation's replay verifies the new case exclusions; it does not replay that larger lower-bound certificate.

## What has been proved

Every field certificate in the table excludes a specified occupied-cell pattern, and also its whole-packing half-turn. The cells are the 16 rational Voronoi polygons in the supplied exact cover; they are not assumed to be a rectangular grid. Cell labels are zero-based. The cover and half-turn enumeration reduce all 4,368 eleven-cell subsets to 2,184 canonical cases. Cell boundaries and independent square orientations are retained in the proofs.

| Base case | Required occupied cells | Positively charged cells | Forced charge > capacity | Canonical extensions |
|---|---|---|---|---|
'''+'\n'.join(lines)+rf'''

The extension counts overlap. Their independently recomputed **union**, not their sum, is {E}. The four known candidate cases, 438, 999, 1462 and 1659, all survive. `verified-union.json` contains the complete excluded and unresolved index lists, with source hashes.

A particularly strong new result is the four-cell obstruction

\[
\{{0,4,8,12\}}\quad\text{{cannot all be occupied}}.
\]

Its half-turn closure alone excludes 764 canonical cases. Its certificate uses just one majority-hull resource of capacity one and forces both middle cells, 4 and 8, to consume it.

## Why the certificates are proofs

Work in a rational container of side $L=191/50$, with equal parent-square side $B=L/U$. Any packing in a container of side $S\le T$ can be mapped into this frame and its squares shrunk about their centers to side $B$. Thus excluding a configuration in this frame excludes it at every $S\le T$.

For an odd set of $2k-1$ resource sites, a convex core is charged when it meets the convex hull of every $k$-site subset. Two disjoint compact convex cores cannot both be charged: a strict separating line puts at least $k$ of the sites on a side whose convex hull misses one of the two cores. Each such resource consequently has capacity one across a packing. Ordinary point resources and the other retained resource types use their separately checked counting bounds.

Certain rational points are proved strictly inside any legal parent assigned to each cell. If two distinct occupied cells' squares overlap one of these owned points, the packing is impossible. These conditional restrictions allow a certificate to force a positive charge in specified cells. In each table row, the sum of those forced charges exceeds the total resource capacity.

The geometric inequalities are checked for **all** centers and angles, not just sampled placements. A full closed half-angle partition covers $t=\tan(\theta/2)$ from 0 to 1. On each interval, rational strict cores are proved contained in every legal parent orientation. Exact wall bounds and the rational cell polygon form a legal-center outer domain. The verifier proves that domain covered by charge regions and forbidden owned-point capture regions.

There are two geometric implementations. The producer creates complete exact certificates. The independent checker reconstructs the positive-charge regions and proves whole-domain coverage by rational polygon unions, without importing the producer's spatial sweep, staircase or patcher. It separately checks cover enumeration, resource budgets, strict containment, ownership, angular coverage, the algebraic side comparison and transfer to other cell patterns. All 3,390 positive-threshold angular rows of the current registry receive this second geometric check. This is a computer-assisted proof of the listed exclusions, not a proof-assistant formalization.

## Other rigorous progress, and its limits

A new propagation rule uses the entire convex hull of mandatory owned points. If $K_j$ lies strictly in a different parent and $Q$ is an assigned strict core, a center in the Minkowski sum $K_j+(-Q)$ is forbidden. Subtracting these regions provides exact outer covers of the remaining poses. Intersecting the cores over those covers proves additional mandatory owned points. Every iteration uses a frozen previous-round snapshot, preventing circular reasoning.

An independent audit checked a snapshot for case 438: 130 unconditional seeds, 217 newly derived points, 1,983 angular rows and 57,994 rational arrangement slabs. That snapshot covers two complete propagation rounds and six complete cells of the next round. **It proves localization facts, not exclusion or entry into a local guard.** Later adaptive and branch experiments retain their own status and are not silently promoted to theorems.

The finite LP screen examined all 1,944 previously unresolved cases and suggested exclusions for all but seven under its original sampled family. Exact checks subsequently rejected numerous suggestions by finding a missed legal parent-square pose. Such a witness refutes the proposed field certificate; it is not an eleven-square packing or a counterexample to optimality. Repaired proposals enter the theorem registry only after complete exact verification.

New ordinary-point resources remove one numerical obstruction in case 1383, but the tested weighted fields still encountered missed legal poses or incomplete geometry. No exclusion of 1383 is counted here. Rotated-cover matching and joint overlay relaxations also left surviving abstract assignments; those experiments provide no additional exclusions.

## The exact missing step

A full proof requires discharging **every one of the remaining {R} cases**. A case must either be proved infeasible or have every feasible pose forced into one of the certified local neighborhoods of the known construction. The existing local isolation result does not imply that global capture statement.

There is currently no certificate covering this remaining universal claim. Neither a numerical optimizer's failure to find a packing, a positive gap on finite sample rows, nor substantial shrinkage of pose bounds closes it. The archive therefore keeps `global_optimality_proved: false` explicitly.

## Reproduction and provenance

The accompanying `eleven-square-continuation-2026-09-27.zip` contains the exact packets, independent audits, complete frontier, retained failed attempts, portable replay runner and proof dependencies. Follow README.md. A fresh replay of all 13 certificates from the portable bundle passed and independently reproduced 1,514 exclusions and 670 unresolved cases. `proof_registry.json` is the portable list of the {N} included certificates; `SHA256SUMS.json` binds the files. The original research checkpoint and its source attribution remain identified in the archive.

The strongest conclusion established by this work is the case-exclusion theorem above and the unchanged bracket for $s(11)$. A complete optimality proof is still missing.
'''
(ROOT/'deliverables/11-square-phase2-report.md').write_text(report)
print(json.dumps(dict(excluded=E,remaining=R,certificates=N,report='deliverables/11-square-phase2-report.md')))
