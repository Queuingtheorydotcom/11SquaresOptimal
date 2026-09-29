#!/usr/bin/env python3
"""Verify SHA256SUMS, then independently replay packet-08 case audits."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for line in (HERE/'SHA256SUMS').read_text().splitlines():
    expected,name=line.split('  ',1);actual=sha(HERE/name)
    if actual!=expected:raise SystemExit(f'Hash mismatch: {name}')
results=json.loads((HERE/'result.json').read_text())['results']
checker=HERE/'research/phase3/work/phase3/hull/audit_capture_v9.py'
assert sha(checker)=='95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c'
for row in results:
    a=row['independent_audit'];s=row['source']
    if not a:
        print(f"{row['mask_index']}: unresolved; no independent audit")
        continue
    recorded=json.loads((HERE/a).read_text());assert sha(HERE/s)==row['source_sha256']
    with tempfile.TemporaryDirectory() as tmp:
        target=Path(tmp)/'audit.json'
        command=[sys.executable,str(HERE/'research/frontier/audit_case.py'),str(HERE/s),'--output',str(target)]
        subprocess.run(command,check=True,cwd=HERE,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'})
        fresh=json.loads(target.read_text())
    for key in ('status','source_sha256','root_sha256','mask_index','mask',
                'parent_Uplus','cover_sha256','constraints','mask_exclusion_proved'):
        assert fresh[key]==recorded[key],(row['mask_index'],key)
    assert [n['sha256'] for n in fresh['nodes']]==[n['sha256'] for n in recorded['nodes']]
    assert fresh['mask_exclusion_proved']==row['mask_exclusion_proved']
    print(f"{row['mask_index']}: independently replayed; excluded={fresh['mask_exclusion_proved']}")
print('Packet replay completed. Global optimality is not asserted.')
