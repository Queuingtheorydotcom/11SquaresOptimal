"""Identify all packaged source bytes and completed evidence for final review.

This creates an integrity manifest, never a mathematical acceptance result.
Run only after the component verifications and documentation are finalized.
"""
from pathlib import Path
import hashlib,json
BASE=Path(__file__).resolve().parents[1]
EXCLUDED={'results/GLOBAL_PROOF.json','results/recorded-proof-check.json',
          'inputs/PROOF_MANIFEST.json'}
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    files=[]
    for folder in ('research','code','inputs','docs','results'):
        for p in sorted((BASE/folder).rglob('*')):
            relative=p.relative_to(BASE).as_posix()
            if p.is_symlink():raise ValueError('Symlink in proof package: '+relative)
            if not p.is_file() or '__pycache__' in p.parts or p.suffix in ('.pyc','.log','.writing'):continue
            if relative in EXCLUDED:continue
            if relative.startswith('results/') and p.suffix!='.json':continue
            files.append(dict(path=relative,bytes=p.stat().st_size,sha256=sha(p)))
    for name in ('requirements.txt',):
        p=BASE/name;files.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p)))
    assert len(files)==len({r['path'] for r in files})
    out=dict(schema='eleven-square-proof-manifest-v1',purpose='Content integrity; not proof acceptance',
             files=sorted(files,key=lambda r:r['path']),file_count=len(files),
             logical_bytes=sum(r['bytes'] for r in files),global_optimality_proved=False)
    path=BASE/'inputs/PROOF_MANIFEST.json';path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'manifest_sha256':sha(path),'files':len(files),'bytes':out['logical_bytes']}))
if __name__=='__main__':main()
