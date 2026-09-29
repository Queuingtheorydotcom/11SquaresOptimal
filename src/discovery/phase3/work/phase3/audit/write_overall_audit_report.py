#!/usr/bin/env python3
"""Write a source-bound snapshot report for the combined audited frontier."""
from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def local(p):
    p=Path(p)
    if not p.is_absolute():p=ROOT/p
    return p.resolve()
def relative(p):return str(local(p).relative_to(ROOT))
def main():
    raw=(HERE/'overall-union-independent-audit.json').read_bytes()
    h=hashlib.sha256(raw).hexdigest();overall=json.loads(raw)
    snapshot=HERE/f'overall-union-snapshot-{h[:12]}.json';snapshot.write_bytes(raw)
    assert overall['status']=='PASS_INDEPENDENT_OVERALL_EXCLUSION_UNION'
    checker_hash=overall['checker_sha256'];checker_snapshot=HERE/f'overall-union-checker-{checker_hash}.py'
    if checker_snapshot.exists():assert sha(checker_snapshot)==checker_hash
    else:
        source=next((p for p in HERE.glob('audit_overall_union*.py') if sha(p)==checker_hash),None)
        assert source is not None,'No retained executable checker matches this snapshot'
        checker_snapshot.write_bytes(source.read_bytes())
    fieldpath=local(overall['field_registry']);assert sha(fieldpath)==overall['field_registry_sha256']
    fields=read(fieldpath)
    known={e['packet']:e for e in read(HERE/'audit_entries.json')}
    old={e['packet']:e for e in read(ROOT/'work/phase2/audit/full_replay_manifest.json')['recipes']}
    recipes=[];positive=0;processed=0
    for e in fields['entries']:
        packet=e['packet_path'];entry=known[packet];chain=read(local(e['chain_path']))
        assert sha(local(packet))==e['packet_sha256'] and sha(local(e['chain_path']))==e['chain_sha256']
        positive+=chain['independent_complete_positive_rows'];processed+=chain['processed_rows']
        recipe=dict(old[packet]) if packet in old else dict(packet=packet,producer_gate=entry['producer_gate'],fresh_replay=entry['fresh_replay'],independent_chain=entry['chain'],bins=entry['bins'],max_depth=14,max_rows=30000,seconds=300,patch_nodes=5000)
        recipe.update(packet_sha256=e['packet_sha256'],chain_sha256=e['chain_sha256'],chain_checker_sha256=chain['audit_checker_sha256'])
        recipes.append(recipe)
    generics=[];genericrows=0
    for e in overall['generic_entries']:
        source=local(e['source']);receipt=local(e['audit']);d=read(source);r=read(receipt)
        assert sha(source)==e['source_sha256'] and sha(receipt)==e['audit_sha256']
        checker=next(k for k in r['dependencies'] if k.startswith('audit_capture_v') and k.endswith('.py'))
        command=['python','work/phase3/hull/'+checker,e['source'],'--output','FRESH-OUTPUT.json']
        if d['source'].get('independent_audit_path'):command+=['--root-audit',relative(d['source']['independent_audit_path'])]
        genericrows+=sum(n['rows'] for n in r['nodes'])
        generics.append(dict(source=e['source'],source_sha256=e['source_sha256'],independent_audit=e['audit'],audit_sha256=e['audit_sha256'],root=relative(d['source']['path']),root_sha256=r['root_sha256'],root_audit=relative(d['source']['independent_audit_path']) if d['source'].get('independent_audit_path') else None,root_audit_sha256=r['root_audit_sha256'],required_owner_cells=e['required_owner_cells'],nodes=r['nodes'],dependencies=r['dependencies'],rational_backend=r['rational_backend'],rational_binary_sha256=r.get('rational_binary_sha256'),replay_command=command,environment={'ELEVEN_RATIONAL_BACKEND':'gmp','PYTHONPATH':'work/phase3/deps:work/audit/deps'}))
    manifest=dict(scope=overall['scope'],overall_union=relative(snapshot),overall_union_sha256=h,field_registry=overall['field_registry'],field_registry_sha256=overall['field_registry_sha256'],overall_union_checker=relative(checker_snapshot),overall_union_checker_sha256=overall['checker_sha256'],field_recipes=recipes,generic_recipes=generics,global_optimality_proved=False)
    manifest_bytes=(json.dumps(manifest,indent=2)+'\n').encode()
    manifest_snapshot=HERE/f'overall-replay-manifest-{h[:12]}.json'
    if manifest_snapshot.exists():assert manifest_snapshot.read_bytes()==manifest_bytes
    else:manifest_snapshot.write_bytes(manifest_bytes)
    (HERE/'overall_replay_manifest.json').write_bytes(manifest_bytes)
    report=f'''# Independently audited combined exclusion frontier

**{overall['excluded_canonical_cases']:,} of 2,184 canonical cases are excluded; {overall['remaining_canonical_cases']} remain. Full optimality is not proved.** All four known candidate cases, 438, 999, 1462, and 1659, remain.

The exact parent side is `387708359002281417731/10^20`. The frozen Phase2 baseline excluded 1,514 cases. The current combined union adds {overall['excluded_canonical_cases']-1514} beyond that baseline. Counts are unions, never sums of overlapping certificates.

| Proof family | Retained certificates | Cases covered | Cases added beyond fields |
|---|---:|---:|---:|
| Physical charge fields | {len(recipes)} | {overall['field_cases']} | — |
| Unconditional owned-hull and collision contradictions | {len(generics)} | {overall['generic_cases']} | {overall['generic_cases_beyond_fields']} |

The field certificates contain {processed:,} producer angular-row checks and {positive:,} independently covered positive-threshold rows. Their exact integer charge lower bounds exceed checked finite-support capacity budgets. Their wall-owned points retain a hash-bound independently checked Phase1 ownership proof.

The generic certificates independently replay {genericrows:,} pose rows. Their fresh wall seeds or independently audited prior ownership states establish the induction base. Every promoted owned hull, complete angular cover, collision region, residual-domain cover, and terminal contradiction is checked with exact rational arithmetic. Only contradictions with no branch constraints enter this union. A proved occupied subset transfers by containment to any eleven-cell case or its whole-packing half-turn image; the exact cover's half-turn identity is checked in the union auditor.

The authoritative source snapshot for this report is `{snapshot.name}` (SHA-256 `{h}`). `{manifest_snapshot.name}` records every field replay and generic source, prerequisite, checker, dependency hash, and replay command. The evolving frontier is `overall-remaining-mask-indices.json`.

The conditional candidate-orbit lemma and branch-local capture results contribute no exclusions here. Finishing the global proof still requires eliminating the remaining noncandidate cases and completing the local-optimality reduction for the surviving candidate geometry.
'''
    report_snapshot=HERE/f'OVERALL_AUDIT_REPORT_{h[:12]}.md'
    if report_snapshot.exists():assert report_snapshot.read_text()==report
    else:report_snapshot.write_text(report)
    (HERE/'OVERALL_AUDIT_REPORT.md').write_text(report)
    print(json.dumps(dict(excluded=overall['excluded_canonical_cases'],remaining=overall['remaining_canonical_cases'],field_certificates=len(recipes),generic_certificates=len(generics),positive_field_rows=positive,generic_rows=genericrows,snapshot=relative(snapshot),manifest=relative(manifest_snapshot),report=relative(report_snapshot))))
if __name__=='__main__':main()
