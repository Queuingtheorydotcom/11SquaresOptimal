"""Create disjoint, self-contained research assignments; perform no geometry search."""
from pathlib import Path
import hashlib
import json
from itertools import combinations

HERE=Path(__file__).resolve().parent
R=HERE.parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
snapshot=R/'audit-lower-bound/frontier-count-crosscheck.json'
count=read(snapshot)
cover_path=R/'phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json'
cover=read(cover_path)
turn=lambda J:tuple(sorted(15-i for i in J))
canonical=sorted({min(J,turn(J)) for J in combinations(range(16),11)})
assert list(map(list,canonical))==cover['canonical_eleven_cell_subsets']
candidate={438,999,1462,1659}
pending=sorted(set(count['remaining_cases'])-candidate)
assert len(pending)==173 and count['excluded']==2007 and count['remaining']==177
sites='\n'.join(f"| {i} | {c['center'][0]} | {c['center'][1]} |" for i,c in enumerate(cover['cells']))
jobs=[]
cursor=0
for j in range(12):
    size=len(pending)//12+(j<len(pending)%12)
    masks=pending[cursor:cursor+size];cursor+=size
    name=f'{j+1:02d}-case-exclusions.md';job_id=f'cases-{j+1:02d}'
    rows='\n'.join(f"| {m} | {', '.join(map(str,canonical[m]))} |" for m in masks)
    saved=[m for m in masks if (R/f'frontier/mask{m}-self-v1.json').exists()]
    job=dict(job_id=job_id,document=name,mask_indices=masks,
             masks={str(m):list(canonical[m]) for m in masks},
             optional_existing_producer_sources=saved,
             acceptance='Independently checked unconditional exclusion at rational U, for every assigned case.')
    jobs.append(job)
    text=rf'''# {job_id}: exclude {len(masks)} exact eleven-square cases

## Your assignment

Prove that each case in the table below is impossible. Return exact, independently
checkable proofs. A complete result for this packet proves only these cases,
not global optimality. Work only on these assigned indices to avoid duplication.
If a case remains open, identify it explicitly and return the useful verified
partial work. Never assume that the requested conclusion must be true.

This document is mathematically self-contained. The accompanying
`case-tools.zip` supplies an existing exact search engine and a separate checker
as a practical starting point. The full original continuation archive is useful
for context, but is not required to understand the theorem below.

| Case index | Eleven occupied cells |
| --- | --- |
{rows}

## Exact theorem to prove

Set

\[
U=\frac{{387708359002281417731}}{{100000000000000000000}}.
\]

There are eleven closed unit squares, with independently chosen orientations,
inside \([-U/2,U/2]^2\), and their interiors must be pairwise disjoint. For the
case with occupied-cell set \(J\), label the squares by \(i\in J\). Square
\(i\)'s center is required to lie in the closed cell \(C_i\) defined next.
Prove that **no such configuration exists**. Contact between squares or with
container walls is allowed. All center-cell boundaries are included.

Define the following sixteen rational sites \(a_i\) in \([0,1]^2\).

| Cell | Site x | Site y |
| --- | --- | --- |
{sites}

Define

\[
V_i=\{{q\in[0,1]^2:2(a_k-a_i)\cdot q\le
\|a_k\|^2-\|a_i\|^2\ \text{{for every }}k\}},
\qquad
C_i=(U-1)\bigl(V_i-(1/2,1/2)\bigr).
\]

This fully specifies the closed polygon for every square center. The index is
zero-based in the sorted list
`sorted({{min(J, sorted(15-i for i in J)) : J in combinations(range(16),11)}})`;
the explicit cell sets above are authoritative if another implementation uses
a different numbering convention.

Every square orientation can be represented by \(t\in[0,1]\), with
\(\cos\theta=(1-t^2)/(1+t^2)\), \(\sin\theta=2t/(1+t^2)\).
Both endpoints and all intermediate angles must be covered. Labels identify
cells, not a common orientation or a presumed contact pattern.

## Available method and files

Use `research/frontier/run_case.py` for a fresh wall-seeded propagation and
`research/frontier/audit_case.py` for the frozen, source-distinct v9 geometric
replay. If propagation stalls, `research/frontier/refine_case.py` bisects its
angle intervals, retains more exact polygon support directions, and uses up to
five collision partners. This refinement closed all five stalled cases tried
in the preceding batch, but success on the present cases is not assumed.

The independent checker is
`research/phase3/work/phase3/hull/audit_capture_v9.py`, SHA-256
`95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c`.
The exact cover is
`research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json`,
SHA-256 `df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e`.

The original implementation uses field scale \(L=191/50\), \(B=L/U\):
the field center is \(B(c+(U/2,U/2))\) and the field square side is \(B\).
Keep that conversion exact. Unconditional cases need no lower-bound assumption
and no candidate local theorem.

Optional saved producer files exist locally for case indices
`{saved}`. These are **not accepted proofs** until their entire source ancestry
passes the independent checker. If those files were not supplied to you,
regenerate the case from its fresh wall seed instead.

## Suggested workflow

Use one worker by default and keep any larger CPU budget explicit. Do not
launch the old all-cases batch. In the code archive's workspace layout, after
installing native `gmpy2` for your Python, substitute one assigned integer for M:

```sh
python research/frontier/run_case.py M --seconds 120
python research/frontier/refine_case.py research/frontier/maskM-self-v1.json --output research/frontier/maskM-refined-v1.json --seconds 180
python research/frontier/audit_case.py research/frontier/maskM-refined-v1.json --output research/frontier/maskM-independent.json
```

If the first producer already contradicts the case, audit that source directly.
If a refinement remains open, another refinement can use its output as the
next source. Producers refuse to overwrite an existing output. Never run with
Python `-O` or `-OO`; assertions are proof obligations. Preserve all ancestors.
An interrupted or timed-out producer is not a contradiction.

You may develop stronger methods, including exact center or angle splits.
Every split must be an exhaustive closed cover, and every leaf must be proved.
Do not add arbitrary center/angle/contact assumptions. If using D4-derived
necessary conditions, separately prove and bind their necessity; a conditional
contradiction alone does not exclude this case. Pure mathematical proofs are
also welcome, provided every step and boundary case is explicit.

## Required returned files

Return a directory or ZIP named `{job_id}-result` containing:

1. `proof.md`: precise theorem, proof method, all assumptions, mathematical
   justification of any new inference rule, and a case-by-case outcome.
2. `result.json`: the format below, with one entry for **every** assigned index.
3. `certificates/`: complete successful producer traces, all source ancestors,
   independent audit outputs, and any branch tree and necessity certificates.
4. `replay.py` or exact replay commands plus required dependency versions.
5. `SHA256SUMS`: hashes of all returned inputs, programs, and proof artifacts.

```json
{{
  "job_id": "{job_id}",
  "status": "complete_or_partial_or_failed",
  "parent_Uplus": "387708359002281417731/100000000000000000000",
  "assigned_mask_indices": {json.dumps(masks)},
  "results": [
    {{
      "mask_index": {masks[0]},
      "occupied_cells": {json.dumps(list(canonical[masks[0]]))},
      "status": "proved_or_unresolved",
      "mask_exclusion_proved": false,
      "constraints": [],
      "proof_kind": "unconditional_v9_or_complete_tree_or_other",
      "source": "relative/path.json",
      "source_sha256": "actual SHA-256",
      "independent_audit": "relative/path.json",
      "independent_audit_sha256": "actual SHA-256",
      "checker_sha256": "actual SHA-256",
      "unresolved_obligations": ["Explain any remaining gap"]
    }}
  ],
  "global_optimality_proved": false
}}
```

Replace placeholder values; repeat the result entry for every assigned case.
Set `complete` only when all assigned cases have independent proofs. A passing
producer flag, an unverified solver result, a floating-point infeasibility claim,
or an incomplete branch tree does not qualify. If no exact proof is obtained,
return `partial` with the remaining domains and the exact missing obligation.

## How this fits the full project

The known construction has side approximately 3.8770835900228141773. The current
receipt inventory lists 2,007 excluded cases and 177 remaining; its final strict
merge is a separate audit assignment. Four remaining construction patterns
(438, 999, 1462, 1659) are deliberately absent from these exclusion packets.
They require local capture and symmetry composition, not contradictions at U.
The twelve case packets partition the other 173 indices exactly.
'''
    (HERE/name).write_text(text)
assert cursor==173 and sorted(m for j in jobs for m in j['mask_indices'])==pending
manifest=dict(status='FROZEN_RELAY_ASSIGNMENTS_NOT_AN_OPTIMALITY_PROOF',
    source_snapshot=str(snapshot.relative_to(R.parent)),source_snapshot_sha256=sha(snapshot),
    last_strict_union='research/frontier/union-snapshot-93856c2b8cd8.json',
    last_strict_excluded=1997,latest_receipt_count_excluded=2007,
    latest_receipt_count_remaining=177,final_ledger_merge_pending=True,
    baseline_fresh_replay='research/PHASE3_FRESH_REPLAY_RESULT.json',
    baseline_excluded=1931,candidate_masks=sorted(candidate),
    case_job_count=12,noncandidate_cases=173,jobs=jobs,global_optimality_proved=False)
(HERE/'CASE_ASSIGNMENTS.json').write_text(json.dumps(manifest,indent=2)+'\n')
(HERE/'frozen-frontier-count-crosscheck.json').write_bytes(snapshot.read_bytes())
print('Wrote twelve disjoint case packets covering 173 cases.')
