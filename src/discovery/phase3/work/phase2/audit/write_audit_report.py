#!/usr/bin/env python3
"""Render the current exact audit registry as a concise mathematical report."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
p=HERE/'current-union-independent-audit.json';d=json.loads(p.read_text());rows=[];nrows=0;naccepted=0
for e in d['entries']:
 packet=json.loads(Path(e['packet_path']).read_text());audit=json.loads(Path(e['chain_path']).read_text())
 nrows+=audit['independent_complete_positive_rows'];naccepted+=audit['accepted_full_interval_leaves']
 owners=', '.join(map(str,e['required_owner_cells']));pos=', '.join(e['positive_cell_thresholds'])
 arities=[len(f['indices']) for f in packet['certificate']['features'] if f['weight']]
 feature=f"{sum(packet['certificate']['point_weights'])} point units; TRUE arities {arities}"
 rows.append(f"| {e['base_mask_index']} | {owners} | {pos} | {e['budget_units']} | {e['canonical_cases']} | {feature} |")
text=f'''# Exact case-exclusion audit: {d['excluded_canonical_cases']} cases

The current independently checked certificates exclude **{d['excluded_canonical_cases']} of 2,184 canonical eleven-cell cases**, leaving **{d['remaining_canonical_cases']} unresolved cases**. They include the previously excluded case 2140. All four known candidate-containing cases, indices 438, 999, 1462, and 1659, survive. This is a partial proof; it does not prove global optimality.

The common rational container side is

\\[
U=387708359002281417731/10^{{20}}.
\\]

Each chain independently checks the exact algebraic sign \\(\\alpha<U\\), so its exclusions hold at every side \\(S\\leq\\alpha\\). Every smaller-container packing also fits in the side-\\(U\\) container.

## Certified conditional patterns

Cell labels are zero-based. Every listed positive cell has threshold one. All stated owner cells are required to be occupied; the remaining cells of an eleven-cell case are arbitrary. The transfer count includes whole-packing half turns. Counts overlap and must not be added without the exact union registry.

| Base case | Required owner cells | Positive cells | Capacity budget | Canonical transfers | Resources |
|---|---|---|---:|---:|---|
'''+ '\n'.join(rows)+f'''

The exact registry removes all overlaps. Its complete excluded list and remaining frontier are `current-union-independent-audit.json` and `remaining-mask-indices.json`.

## Independent geometry and proof chain

Across the current certificates, **{nrows} accepted positive-threshold angular rows** have source-distinct exact geometry proofs. The entire legal center domain is covered by rational TRUE median-halfplane regions and point-capture rectangles, including conditionally forbidden owned-point captures. The checker constructs these sets directly and subtracts their convex regions exactly; it does not call the producer's staircase, feature precomputation, low-cell extractor, or patcher. It also proves the leaves accepted by the producer's TRUE patch mechanism. Zero-threshold rows follow from nonnegative charge.

Each accepted row has an independent exact full-angle containment check: rational quadratic inequalities certify that its closed reference core lies strictly inside every parent square over the whole angular interval. All eleven physical cell partitions cover the complete half-angle domain \\[0,1\\], corresponding to a full quarter turn. There is no transfer of individual rows within an asymmetric field. The proofs retain closed center-domain boundaries: a finite closed union covering the dense full-dimensional domain covers its closure. Exact tests retain a positive gap of width \\(10^{{-50}}\\).

The original exact producer is also freshly replayed and must match the original gate apart from timing and portable dependency paths. Every packet and source dependency is hash-bound. The cover is independently reconstructed, all canonical masks are regenerated, and its strict cell diameter bounds imply one square center per occupied cell.

Strict ownership of the 188 supplied points is a retained earlier proof premise, explicitly checked against the same exact point/owner coordinates and checker hashes. Its independent certificate uses exact disk bounds for 114 points and source-distinct rational interval wall bounds for 74 points. Reusing this source-bound receipt avoids repeating an unchanged premise; it is not described as a fresh wall-geometry replay for every new field.

A point captured in another square's closed strict core would lie strictly inside both parents, so the added conditional charges vanish in a legal packing. Every TRUE support has \\(2k-1\\) distinct sites and capacity one: two interior-disjoint convex squares cannot both strictly straddle its median projection in a separating direction. Therefore the sum of original feature charges is bounded by the stated budget, while the positive cells force a larger sum.

For a target mask, the generic registry requires the same owner support and enough independently covered positive cells to exceed the budget. It applies the fixed certificate either to the packing or to its whole half-turn image. It independently enumerates the union of these canonical cases.

## Files and limits

`audit_wall_mask_chain_v2.py` is the complete chain checker. `independent_patch_cover.py` supplies the independent entire-domain polygon-union proofs. `audit_union_registry_v2.py` computes the exact union; `run_audit_batch.py` replays and audits new producer certificates with two workers. `audit_entries.json` records the current packet/receipt inputs.

The older one-map D4 closed-cell matching relaxation was also independently checked. At the original 240-case stage all 1,944 remaining cases had surviving matchings for all eight maps; this negative result establishes no new packing or exclusion. Later finite relaxations and iterative localization have their own scope and receipts.

The mask-438 conditional kernel contraction has been reviewed mathematically in `RESIDUAL_KERNEL_MATH_REVIEW.md`; its complete source-distinct snapshot replay belongs to `work/phase2/hull/audit_residual_kernel.py`. Partial contraction does not prove capture by a local guard.

No current result settles the remaining {d['remaining_canonical_cases']} cases or establishes the global hypothesis required to finish the optimality theorem.
'''
(HERE/'PHASE2_AUDIT_REPORT.md').write_text(text)
