from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
manifest=json.loads((root/'SHA256SUMS.json').read_text())
for name,expected in manifest.items():
 p=root/name
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
  raise SystemExit('Integrity failure: '+name)
print('PASS',len(manifest),'hashed files')
