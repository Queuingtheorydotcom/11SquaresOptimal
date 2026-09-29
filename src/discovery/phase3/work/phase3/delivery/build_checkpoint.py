"""Freeze an honest, source-bound continuation checkpoint; not an optimality claim."""
from pathlib import Path
import hashlib,json,zipfile,time,sys
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'deliverables/eleven-square-phase2-2026-09-27'
DEST=ROOT/'deliverables/eleven-square-continuation-2026-09-27.zip'
TAG=sys.argv[1]
REG=ROOT/f'work/phase3/audit/overall-union-snapshot-{TAG}.json'
MAN=ROOT/f'work/phase3/audit/overall-replay-manifest-{TAG}.json'
reg=json.loads(REG.read_bytes());manifest=json.loads(MAN.read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(REG.read_bytes())==manifest['overall_union_sha256']
assert reg['global_optimality_proved'] is False
sources={}
def add_tree(folder,prefix):
 for p in sorted(folder.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts or p.suffix in ('.pyc','.nbc','.nbi','.tmp','.writing'):continue
  sources[str(prefix/p.relative_to(folder))]=p
add_tree(BASE,Path('.'))
# This deliverable contains the certified snapshot and its complete proof DAG.
# Keep active, unaudited research traces out of the published proof membership.
for p in sorted((ROOT/'work/phase3').rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts and (p.suffix in ('.py','.md','.cpp','.h','.hpp','.so') or 'deps' in p.parts):
  sources[str(p.relative_to(ROOT))]=p
def include(path):
 p=Path(path)
 if not p.is_absolute():p=ROOT/p
 assert p.is_file(),p
 sources[str(p.relative_to(ROOT))]=p
for e in manifest['field_recipes']:
 for key in ('packet','producer_gate','fresh_replay','independent_chain'):include(e[key])
for e in manifest['generic_recipes']:
 for key in ('source','independent_audit','root','root_audit'):
  if e.get(key):include(e[key])
 for node in e['nodes']:include(node['path'])
for p in (ROOT/'work/phase3/audit').glob('*.json'):
 if 'queue' not in p.name and 'monitor' not in p.name:include(p)
include(REG);include(MAN)
for key in ['overall_union_checker','field_registry']:
 original=ROOT/manifest[key];expected=manifest[key+'_sha256']
 if sha(original.read_bytes())!=expected:
  assert key=='overall_union_checker'
  frozen=ROOT/f'work/phase3/audit/overall-union-checker-{expected}.py'
  assert sha(frozen.read_bytes())==expected
  sources[manifest[key]]=frozen
 else:assert sha(original.read_bytes())==expected
for e in manifest['field_recipes']:
 assert sha((ROOT/e['packet']).read_bytes())==e['packet_sha256']
 assert sha((ROOT/e['independent_chain']).read_bytes())==e['chain_sha256']
for e in manifest['generic_recipes']:
 for key,hkey in [('source','source_sha256'),('independent_audit','audit_sha256'),('root','root_sha256')]:
  assert sha((ROOT/e[key]).read_bytes())==e[hkey]
excluded=reg['excluded_canonical_cases'];remaining=reg['remaining_canonical_cases']
report=f'''# Eleven-square packing: exact certification checkpoint

**This is not a completed optimality proof.** The independently audited union excludes **{excluded} of 2,184 canonical cases**, leaving **{remaining}**. It certifies **{excluded-1514} of the 670 cases** assigned at the start of this continuation. Counts are unions of overlapping certificates.

The supported global bracket remains

\\[
3.8754<s(11)\\le T=3.877083590022814177307897060100962706376\\ldots.
\\]

Here eleven unit squares may rotate independently. The exact candidate side is
\\(T=(6u+4)/(1+2u-u^2)\\), where the isolated root near0.3657693 satisfies
\\(5u^8-10u^7-2u^6+14u^5+12u^4-6u^3+2u^2+2u-1=0\\).
All new exclusions hold at the rational upper cap
\\(U=387708359002281417731/10^{{20}}>T\\).

## Certified exclusions

The rational16-cell Voronoi cover and whole-packing half-turn reduce4,368 eleven-cell subsets to2,184 cases. Complete closed center and angle domains are retained, including boundary positions. Work is scaled to container side\\(L=191/50\\), parent side\\(B=L/U\\).

| Proof family | Retained certificates | Covered cases |
|---|---:|---:|
| Exact physical charge fields | {len(manifest['field_recipes'])} | {reg['field_cases']} |
| Unconditional geometric contradictions | {len(manifest['generic_recipes'])} | {reg['generic_cases']} |
| Combined union | — | {excluded} |

Field certificates force a sum of integer charges exceeding the independently checked capacity of their resources. Their source-distinct auditor reconstructs all positive-threshold regions and checks exact whole-domain coverage. Generic certificates begin with independently proved wall ownership, propagate necessary pose domains and strict interior hulls, and end only when an occupied square has no possible pose. A proof for an occupied subset transfers to every containing case and its whole-packing half-turn.

The independent geometric checker uses exact rational arithmetic and reconstructs spatial unions separately from the producer. Discovery runs, legal-parent refutations, incomplete traces, and unaudited producer contradictions contribute no exclusions. The four known candidate cases438,999,1462,1659 all survive.

## New geometric ingredients

If\\(K_j\\) is proved strictly inside another square and\\(Q_i\\) is a strict core of the queried square, centers in\\(K_j-Q_i\\) are forbidden. Subtracting these regions gives a complete outer cover of surviving centers. Intersecting the corresponding parent interiors proves more owned points, so this rule can be iterated without circularity.

A stronger universal collision kernel uses a complete pose cover for square\\(j\\):
\\[
F_i=\\bigcap_{{r}}\\;\\bigcap_{{c\\in D_{{jr}}}}
  (c+Q_{{jr}}-Q_i).
\\]
Every center in\\(F_i\\) forces intersection of strict cores for every possible pose of square\\(j\\). Exact convex halfplanes compute this region, and an independent implementation checks the Minkowski geometry and its support bounds. This rule is used only with complete earlier pose covers.

Angular refinement subdivides existing closed intervals without losing endpoints. It has closed cases that reached a fixed point with coarser angle bounds. A further necessary condition, containment of each square's own proved hull, is being developed in separately versioned sources; it is not counted before independent replay.

## Remaining proof obligations

Every remaining noncandidate case must be excluded. A separately audited conditional symmetry lemma shows that **if only the four candidate cases survive**, a whole-packing dihedral symmetry places every feasible packing in case438. That lemma alone adds no exclusions.

Case438 still requires global capture: every feasible pose must enter a certified local neighborhood of the known construction. The existing local isolation theorem, of radius1/248 in its stated coordinates, does not establish that global assertion. Candidate branch contradictions and partially audited capture trees remain research progress, not a completed capture proof.

## Reproduction

The authoritative snapshot is `{manifest['overall_union']}`, SHA-256`{manifest['overall_union_sha256']}`. `PHASE3_REPLAY_MANIFEST.json` records exact source, audit, dependency and checker hashes together with replay recipes. `PHASE3_GENERIC_ENTRIES.json` fixes the generic membership of this snapshot. `SHA256SUMS.json` hashes every archived file; `check_manifest.py` checks archive integrity.

The earlier `replay_proofs.py` remains the fully exercised13-certificate Phase2 runner and reproduces1,514 exclusions. It is **not** a replay of this larger Phase3 union. Phase3 individual geometric replays have been run and passed in the working environment; use the new manifest's recipes for them. The archive retains the5.4MB exact-rational GMP dependency used by the receipts. Full fresh replay from this enlarged standalone archive has not yet been completed; no portability claim beyond the recorded interfaces is made.

The archive includes the prior portable checkpoint, current verification source code, and the complete accepted certificate DAG for this snapshot. New unaudited research traces and reproducible numerical discovery matrices are omitted. Original attribution and the separate3.8754 lower-bound provenance remain in the prior checkpoint materials. All full-optimality status fields remain false.
'''
# Repair prose spacing without altering mathematical literals or file identifiers.
for a,b in [('near0.','near 0.'),('rational16','rational 16'),('reduce4,','reduce 4,'),('to2,','to 2,'),('cases438','cases 438'),('case438','case 438'),('radius1/248','radius 1/248'),('exercised13','exercised 13'),('reproduces1,','reproduces 1,'),('the5.4MB','the 5.4 MB'),('separate3.','separate 3.')]:report=report.replace(a,b)
outreport=ROOT/'deliverables/11-square-proof-progress-2026-09-27.md';outreport.write_text(report)
readme=f'''# Eleven-square exact proof continuation\n\n**Global optimality is not proved.** This snapshot independently certifies {excluded} of2,184 cases, leaving{remaining}. Read REPORT.md before using any results.\n\nRun `python check_manifest.py` for archive integrity. The Phase3 recipes and fixed membership are in PHASE3_REPLAY_MANIFEST.json and PHASE3_GENERIC_ENTRIES.json. The retained root replay_proofs.py covers the earlier Phase2 result only.\n\nFor a fresh source-bound union reconstruction after the listed audits, use:\n\n```sh\npython work/phase3/audit/audit_overall_union.py --fields {manifest['field_registry']} --generic-entries PHASE3_GENERIC_ENTRIES.json --output fresh-overall-union.json\n```\n\nThis checks receipts, exact transfers and case union; it does not replace the individual geometric replays. Assertions must remain enabled.\n'''
extra={'REPORT.md':report.encode(),'README.md':readme.encode(),'PHASE3_REPLAY_MANIFEST.json':MAN.read_bytes(),'PHASE3_VERIFIED_UNION.json':REG.read_bytes(),'PHASE3_GENERIC_ENTRIES.json':(json.dumps([dict(source=e['source'],audit=e['audit']) for e in reg['generic_entries']],indent=2)+'\n').encode(),'PHASE2_REPORT.md':(BASE/'REPORT.md').read_bytes()}
sources.pop('SHA256SUMS.json',None)
for name in extra:sources.pop(name,None)
hashes={};size=0;start=time.monotonic();tmp=Path('/tmp/eleven-square-phase3-checkpoint.building.zip')
with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
 for name,p in sources.items():
  data=p.read_bytes();hashes[name]=sha(data);size+=len(data);z.writestr(name,data)
 for name,data in extra.items():hashes[name]=sha(data);size+=len(data);z.writestr(name,data)
 z.writestr('SHA256SUMS.json',json.dumps(hashes,indent=2)+'\n')
tmp.replace(DEST)
result=dict(archive=str(DEST),report=str(outreport),files=len(hashes),raw_bytes=size,archive_bytes=DEST.stat().st_size,archive_sha256=sha(DEST.read_bytes()),seconds=time.monotonic()-start,excluded=excluded,remaining=remaining,global_optimality_proved=False)
(ROOT/'work/phase3/delivery/checkpoint-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
