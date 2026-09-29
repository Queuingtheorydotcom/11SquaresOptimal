"""Discover exclusions with all four exact cover views; independent replay required."""
from pathlib import Path
import json,hashlib,subprocess,time
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
registry=ROOT/'work/phase3/audit/current-union-independent-audit.json'
snapshot=registry.read_bytes();a=json.loads(snapshot);tag=hashlib.sha256(snapshot).hexdigest()[:12]
out=HERE/('overlay-'+tag);out.mkdir(exist_ok=True)
(out/'registry-snapshot.json').write_bytes(snapshot)
geometry=ROOT/'work/phase2/geometry'
overlay=geometry/'cover_overlay_exact.json';distance=geometry/'overlay_distance_pairs.json'
cover=ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
o=json.loads(overlay.read_text());d=json.loads(distance.read_text());c=json.loads(cover.read_text())
assert o['cover_sha256']==sha(cover) and d['overlay_sha256']==sha(overlay)
bit=lambda r:sum(1<<i for i in r)
patterns={bit(r) for e in a['entries'] for r in [e['required_owner_cells'],[15-i for i in e['required_owner_cells']]]}
records=[];start=time.monotonic()
for iteration in range(10):
    rows=[f"{len(o['regions'])} {len(d['pairs'])} {len(c['canonical_eleven_cell_subsets'])} {len(patterns)}",
          *[str(x) for x in sorted(patterns)],*[' '.join(map(str,r['labels'])) for r in o['regions']],
          *[' '.join(map(str,r['regions'])) for r in d['pairs']],*[str(bit(J)) for J in c['canonical_eleven_cell_subsets']]]
    inp=out/f'input-{iteration}.txt';receipt=out/f'receipt-{iteration}.txt'
    inp.write_text('\n'.join(rows)+'\n')
    result=subprocess.run([str(geometry/'overlay_csp'),str(inp),str(receipt),'2000000'],capture_output=True,text=True,check=True)
    lines=receipt.read_text().splitlines();excluded=[int(x.split()[1]) for x in lines if x.startswith('EXCLUDED ')]
    records.append(dict(iteration=iteration,excluded=excluded,summary=lines[-1],input_sha256=sha(inp),receipt_sha256=sha(receipt)))
    print(json.dumps(records[-1]),flush=True)
    if not excluded:break
    for idx in excluded:
        J=c['canonical_eleven_cell_subsets'][idx];patterns.update([bit(J),bit([15-j for j in J])])
(out/'result.json').write_text(json.dumps(dict(status='DISCOVERY_REQUIRES_INDEPENDENT_REPLAY',records=records,
    registry_sha256=hashlib.sha256(snapshot).hexdigest(),cover_sha256=sha(cover),overlay_sha256=sha(overlay),
    distance_sha256=sha(distance),solver_source_sha256=sha(geometry/'overlay_csp.cpp'),
    solver_binary_sha256=sha(geometry/'overlay_csp'),seconds=time.monotonic()-start),indent=2)+'\n')
