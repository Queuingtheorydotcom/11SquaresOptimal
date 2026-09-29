#!/usr/bin/env python3
"""Write source-bound Phase3 report and complete replay recipe manifest."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 registry=read(HERE/'current-union-independent-audit.json');entries=read(HERE/'audit_entries.json')
 old=read(ROOT/'work/phase2/audit/full_replay_manifest.json');oldrecipes={r['packet']:r for r in old['recipes']}
 entries_by_packet={e['packet']:e for e in entries};recipes=[];table=[];positive=processed=0;phase3positive=0;phase3proofs=0
 for r in registry['entries']:
  e=entries_by_packet[r['packet_path']];chain=read(ROOT/e['chain']);positive+=chain['independent_complete_positive_rows'];processed+=chain['processed_rows']
  isnew=e['chain'].startswith('work/phase3/');phase3positive+=chain['independent_complete_positive_rows'] if isnew else 0;phase3proofs+=isnew
  if e['packet'] in oldrecipes:recipe=dict(oldrecipes[e['packet']])
  else:recipe=dict(mask_index=r['base_mask_index'],packet=e['packet'],producer_gate=e['producer_gate'],fresh_replay=e['fresh_replay'],independent_chain=e['chain'],bins=e['bins'],max_depth=14,max_rows=30000,seconds=300,patch_nodes=5000)
  recipe['packet_sha256']=r['packet_sha256'];recipe['chain_sha256']=r['chain_sha256'];recipe['chain_checker_sha256']=chain['audit_checker_sha256'];recipes.append(recipe)
  table.append('| '+str(r['base_mask_index'])+' | '+','.join(map(str,r['required_owner_cells']))+' | '+str(r['budget_units'])+' | '+str(chain['independent_complete_positive_rows'])+' | '+str(r['canonical_cases'])+' |')
 manifest=dict(scope='Ordinary full-quarter-turn physical charge certificates only; every retained row has source-distinct independent weighted or threshold-one geometry. Conditional hull/capture/orbit lemmas are separate and contribute no unconditional cases here.',registry_sha256=sha(HERE/'current-union-independent-audit.json'),adapter='work/geometry/verify_wall_aware_mask.py',independent_chain_checker='work/phase3/audit/audit_wall_mask_chain_v3.py',independent_geometry_checker='work/phase3/audit/independent_weighted_cover.py',ownership_cache='work/new_mask_audit/mask2045-minimized-independent-chain-audit.json',union_checker='work/phase3/audit/audit_union_registry_v3.py',recipes=recipes)
 (HERE/'full_replay_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 report=f'''# Independent Phase3 exclusion audit

**{registry['excluded_canonical_cases']} of 2,184 canonical closed-cell cases are independently excluded; {registry['remaining_canonical_cases']} remain unresolved. Optimality is not yet proved.** The four known candidate cases 438, 999, 1462, and 1659 remain in the frontier.

This exact registry retains {len(recipes)} field certificates, including {phase3proofs} new Phase3 certificates. Their full producer replays contain {processed:,} processed angular rows. All {positive:,} accepted positive-threshold rows, including {phase3positive:,} Phase3 rows, have independent complete-domain rational geometry proofs. The frozen Phase2 baseline excluded 1,514 cases; the present union adds {registry['excluded_canonical_cases']-1514} beyond that baseline. Counts are unions, not sums of each certificate's transfer count.

The parent side is the rational number `U = 387708359002281417731/10^20`. Exact algebraic arithmetic proves the candidate side is below U. Each field proof forbids its cases at U and hence at every smaller container side. Integer point/feature weights are nonnegative; odd TRUE-majority features have capacity one, threshold/floor features have their checked finite support capacity. A complete weighted charge lower bound exceeding this capacity budget contradicts a packing.

Every proof checks all eleven physical cells and their complete half-angle partitions over [0,1]. An independent exact polygon arrangement covers each entire legal center domain, rather than trusting the producer's staircase or patch choices. Union atoms are charged once even when their polygon pieces overlap. Finitely many closed weighted indicator regions extend a dense-interior lower bound to every boundary point. Strict core containment transfers those closed core charges to actual square interiors.

The universal wall-aware owned points reuse a hash-bound independently proved Phase1 ownership receipt. Their exact owner, point, parent side, cover, and checker bindings are validated. This is a retained prior proof dependency, not a claim to freshly rerun all earlier wall projections in each Phase3 certificate. The same fixed field is applied to a packing or its complete half-turn image; no within-field reflection of individual rows is used.

| Base case | Required owner cells | Budget units | Independently covered positive rows | Transferred canonical cases |
|---:|---|---:|---:|---:|
'''+ '\n'.join(table)+f'''

The authoritative union receipt is `current-union-independent-audit.json` (SHA-256 `{manifest['registry_sha256']}`). `remaining-mask-indices.json` lists the unresolved frontier. `full_replay_manifest.json` records every packet, producer gate, replay, independent chain receipt, exact hash, and replay parameter.

`CANDIDATE_ORBIT_LEMMA.md` and its independent receipt establish a conditional D4 reduction: once all noncandidate cases are excluded, every surviving packing has an image in case 438. They add no cases to this registry. Branch-conditioned ownership/capture receipts are also separate premises requiring an exhaustive branch-cover argument and the local optimality theorem before any global conclusion.
'''
 (HERE/'PHASE3_AUDIT_REPORT.md').write_text(report)
 print(json.dumps(dict(excluded=registry['excluded_canonical_cases'],remaining=registry['remaining_canonical_cases'],certificates=len(recipes),positive_rows=positive,phase3_positive_rows=phase3positive)))
if __name__=='__main__':main()
