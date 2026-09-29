from pathlib import Path
import shutil,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'deliverables/eleven-square-continuation-2026-09-27';OUT=ROOT/'deliverables/eleven-square-phase2-2026-09-27';D=Path(__file__).parent
REG=ROOT/'work/phase2/audit/current-union-independent-audit.json';reg=json.loads(REG.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def copy(s,d):d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,d)
if not OUT.exists():shutil.copytree(BASE,OUT)
for cache in list(OUT.rglob('__pycache__')):
 if cache.is_dir():shutil.rmtree(cache)
for s in (ROOT/'work').rglob('*'):
 if not s.is_file() or any(x in s.relative_to(ROOT/'work').parts for x in ['deps','__pycache__']):continue
 if s.suffix in ['.pyc','.nbc','.nbi'] or s.name in ['matching_transfer','overlay_csp']:continue
 copy(s,OUT/s.relative_to(ROOT))
for rel in ['research/optimality/global_capture/local-capture-guards.json','research/optimality/deficit_geometry/physical_features/family.json']:
 copy(ROOT/'current'/rel,OUT/'current'/rel)
old=set()
for archive in (ROOT/'latest').glob('*.zip'):
 with zipfile.ZipFile(archive) as z:old.update(n.rstrip('/') for n in z.namelist())
for s in (ROOT/'current').rglob('*'):
 if s.is_file() and '__pycache__' not in s.parts and s.suffix not in ['.pyc','.nbc','.nbi'] and str(s.relative_to(ROOT/'current')) not in old:copy(s,OUT/s.relative_to(ROOT))
entries=[]
recipes={r['mask_index']:r for r in json.loads((ROOT/'work/phase2/audit/full_replay_manifest.json').read_text())['recipes']}
for e in reg['entries']:
 p=ROOT/e['packet_path'];c=ROOT/e['chain_path'];r=json.loads(c.read_text());idx=e['base_mask_index'];gate=ROOT/recipes[idx]['fresh_replay']
 assert sha(gate)==r['fresh_replay_sha256']
 entries.append(dict(mask_index=idx,packet=str(p.relative_to(ROOT)),reference_gate=str(gate.relative_to(ROOT)),independent_chain=str(c.relative_to(ROOT)),required_cells=e['required_owner_cells'],positive_cells=e['positive_cell_thresholds'],budget=e['budget_units']))
manifest=dict(entries=entries,excluded_canonical_mask_indices=reg['excluded_canonical_mask_indices'],remaining_canonical_mask_indices=reg['remaining_canonical_mask_indices'],global_optimality_proved=False)
(OUT/'proof_registry.json').write_text(json.dumps(manifest,indent=2)+'\n');copy(D/'replay_proofs.py',OUT/'replay_proofs.py');copy(REG,OUT/'verified-union.json')
copy(ROOT/'deliverables/11-square-phase2-report.md',OUT/'REPORT.md')
(OUT/'README.md').write_text(f'''# Eleven-square exact continuation\n\n**This archive is not a complete optimality proof.** It contains {len(entries)} independently audited exact field certificates whose half-turn transfers exclude {reg['excluded_canonical_cases']} of 2,184 canonical occupied-cell cases. {reg['remaining_canonical_cases']} remain. Read REPORT.md.\n\n## Fresh verification\n\nUse Python 3.12 with assertions enabled. Install requirements.txt, then run:\n\n```sh\npython check_manifest.py\npython replay_proofs.py --output-dir fresh-replay\n```\n\nThe runner recomputes each complete geometric certificate, compares it against the preserved reference, independently verifies every positive-threshold angular row by exact whole-domain polygon unions, and reconstructs the transferred case union. Its final RESULT.json must retain `global_optimality_proved: false`. All required proof dependencies are included. Numerical exploration needs additional SciPy and the original research datasets; it is not part of this verification interface.\n\nThe source-distinct ownership audit is computed for the first proof and reused only with matching exact points and checker identity thereafter. This is a computer-assisted proof of the listed exclusions, not a proof-assistant formalization. The other incomplete, rejected, or exploratory outputs are retained with their original status. The frozen Phase1 runner has been replaced by the larger registry runner; the earlier report is superseded by REPORT.md.\n\nThe separate global lower bound 3.8754 is retained from the earlier research checkpoint and is not replayed by this runner. Exploratory script absolute paths are historical; the documented verification interface is portable.\n''')
(OUT/'remaining_frontier.json').write_text(json.dumps(dict(remaining_canonical_cases=reg['remaining_canonical_cases'],remaining_canonical_mask_indices=reg['remaining_canonical_mask_indices'],global_optimality_proved=False),indent=2)+'\n')
(OUT/'PROVENANCE.json').write_text(json.dumps(dict(purpose='Independently verified Phase2 forbidden-pattern registry and retained research continuation',global_optimality_proved=False,previous_checkpoint_sha256=sha(ROOT/'deliverables/eleven-square-continuation-2026-09-27.zip'),original_input_provenance=json.loads((BASE/'PROVENANCE.json').read_text()),registry_sha256=sha(REG)),indent=2)+'\n')
files={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.json'}
(OUT/'SHA256SUMS.json').write_text(json.dumps(files,indent=2)+'\n')
print(json.dumps(dict(bundle=str(OUT),files=len(files),proofs=len(entries),excluded=reg['excluded_canonical_cases'],remaining=reg['remaining_canonical_cases'])))
