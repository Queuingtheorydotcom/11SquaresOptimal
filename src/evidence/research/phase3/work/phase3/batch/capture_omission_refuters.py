"""Recover exact legal parents from failed owner-deletion experiments."""
from pathlib import Path
import hashlib, json, os, subprocess, sys
HERE=Path(__file__).resolve().parent
TOP=HERE.parents[1]
ROOT=TOP.parent/'current'
BASE=ROOT/'research/optimality/deficit_geometry/physical_features'
ENV={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONPATH':str(TOP/'audit/deps')}
manifest=HERE/'omission-refuter-manifest.json'
records=json.loads(manifest.read_text()) if manifest.exists() else []
done={r['gate_sha256'] for r in records}
for line in (HERE/'history.jsonl').read_text().splitlines():
 r=json.loads(line)
 if r.get('event') not in {'OWNER_MINIMIZATION','CHARGED_CELL_MINIMIZATION'} or r.get('last')!='REFUTED_BY_LEGAL_PARENT':continue
 gate=Path(r['gate']);digest=hashlib.sha256(gate.read_bytes()).hexdigest()
 if digest in done:continue
 stem=f'mask{r["mask"]}-p3batchomitpool{digest[:12]}'
 ex=BASE/(stem+'-exact.npz');ji=BASE/(stem+'-jitter.npz')
 with (HERE/(stem+'.log')).open('w') as f:
  subprocess.run([sys.executable,str(BASE/'add_exact_refuter.py'),str(gate),'--output',str(ex)],cwd=ROOT,env=ENV,stdout=f,stderr=subprocess.STDOUT,check=True)
  subprocess.run([sys.executable,str(BASE/'jitter_refuter.py'),str(ex),'--output',str(ji),'--count','128'],cwd=ROOT,env=ENV,stdout=f,stderr=subprocess.STDOUT,check=True)
 d=dict(mask=r['mask'],gate=str(gate),gate_sha256=digest,packet=r['packet'],exact=str(ex),jitter=str(ji),exact_sha256=hashlib.sha256(ex.read_bytes()).hexdigest(),jitter_sha256=hashlib.sha256(ji.read_bytes()).hexdigest())
 records.append(d);done.add(digest);tmp=manifest.with_suffix('.tmp');tmp.write_text(json.dumps(records,indent=2)+'\n');tmp.replace(manifest)
 print(json.dumps(dict(mask=r['mask'],source=gate.name,exact=ex.name)),flush=True)
