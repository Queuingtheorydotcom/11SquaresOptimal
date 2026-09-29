from pathlib import Path
import shutil,zipfile,json,hashlib
ROOT=Path('/workspace/scratch/6def36ddf53b');OUT=ROOT/'deliverables/eleven-square-continuation-2026-09-27'
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
for src in (ROOT/'work').rglob('*'):
 if not src.is_file() or 'deps' in src.relative_to(ROOT/'work').parts or '__pycache__' in src.parts:continue
 copy(src,OUT/src.relative_to(ROOT))
for src in (ROOT/'current/research/exact_checker').glob('*.py'):copy(src,OUT/src.relative_to(ROOT))
needed=[
'research/optimality/asymmetric_coverage/verify.py',
'research/optimality/typed_coverage/verify.py',
'research/optimality/global_capture/center-cover-symmetric-exact.json',
'research/optimality/global_capture/trump-cell-symmetric-assignments.json',
'research/optimality/global_capture/GLOBAL-CAPTURE-REDUCTION.md',
'research/optimality/audit/audit_center_cover.py',
'research/optimality/audit/audit_endpoint_rows.py',
'research/optimality/audit/asymmetric-coverage-independent-audit.json',
'research/optimality/audit/typed-coverage-independent-audit.json',
'research/optimality/endpoint_charge/exact-trump-endpoint-rows.json',
'work/construction/verify_trump.py',
'work/construction/CONSTRUCTION.md',
]
for name in needed:copy(ROOT/'current'/name,OUT/'current'/name)
# Preserve new research outputs as an overlay on the already saved input archive.
old=set()
for archive in (ROOT/'latest').glob('*.zip'):
 with zipfile.ZipFile(archive) as z:old.update(n.rstrip('/') for n in z.namelist())
new=[]
for src in (ROOT/'current').rglob('*'):
 if not src.is_file() or '__pycache__' in src.parts or src.suffix in ('.pyc','.nbc','.nbi'):continue
 rel=src.relative_to(ROOT/'current')
 if str(rel) not in old:
  copy(src,OUT/'current'/rel);new.append(str(rel))
for name in ['ATTRIBUTION.md','AUTHORS.md','LICENSE','LICENSING.md']:
 src=ROOT/'research/11-squares-certified-bound-main'/name
 if src.exists():copy(src,OUT/'upstream-notices'/name)
for src in (ROOT/'research/11-squares-certified-bound-main/NOTICES').glob('*'):
 if src.is_file():copy(src,OUT/'upstream-notices/NOTICES'/src.name)
report=ROOT/'deliverables/11-square-proof-progress-2026-09-27.md'
report.write_text(report.read_text().replace('complete numerical-independent geometric','complete exact geometric'))
copy(report,OUT/'REPORT.md')
inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'latest').glob('*.zip')}
(OUT/'PROVENANCE.json').write_text(json.dumps({'input_archives':inputs,'new_current_files':new,'global_optimality_proved':False,'purpose':'Two complete new forbidden-pattern proofs and retained research continuation.'},indent=2)+'\n')
print('bundle files',sum(p.is_file() for p in OUT.rglob('*')),'new current',len(new))
