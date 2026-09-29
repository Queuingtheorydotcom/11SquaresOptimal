"""Materialize packet-05 evidence without modifying the immutable receipts."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
SCOPE = ROOT.parent
FRONTIER = ROOT / 'research/frontier'
DEST = SCOPE / 'cases-05-result'
CERTS = DEST / 'certificates'
INPUTS = DEST / 'inputs'
ASSIGNMENTS = json.loads((SCOPE / 'handoff/CASE_ASSIGNMENTS.json').read_text())
JOB = next(j for j in ASSIGNMENTS['jobs'] if j['job_id'] == 'cases-05')
U = '387708359002281417731/100000000000000000000'
CHECKER = '95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def transfer(path, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or sha(target) != sha(path):
        shutil.copy2(path, target)
    return target.relative_to(DEST).as_posix()


DEST.mkdir(exist_ok=True)
CERTS.mkdir(exist_ok=True)
INPUTS.mkdir(exist_ok=True)
transfer(ROOT / 'case-tools.zip', INPUTS / 'case-tools.zip')
transfer(SCOPE / 'review_tools/case-tools-supplement.zip', INPUTS / 'case-tools-supplement.zip')
transfer(SCOPE / 'review_tools/continuation-no-resplit.zip', INPUTS / 'continuation-no-resplit.zip')
transfer(SCOPE / 'handoff/05-case-exclusions.md', INPUTS / '05-case-exclusions.md')
transfer(ROOT / 'process_cases.py', INPUTS / 'process_cases.py')
transfer(ROOT / 'build_result.py', INPUTS / 'build_result.py')
cover = ROOT / 'research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json'
transfer(cover, CERTS / cover.name)
wall = ROOT / 'research/phase3/work/geometry/wall_ownership_groups.json'
transfer(wall, CERTS / wall.name)

results = []
rows = []
total_producer = total_audit = 0.0
for index in JOB['mask_indices']:
    paths = sorted(p for p in FRONTIER.glob(f'mask{index}-*.json') if p.is_file())
    for path in paths:
        transfer(path, CERTS / path.name)
    source_candidates = [p for p in paths if not p.name.endswith('-seed.json')
                         and not p.name.endswith('-independent.json')]
    source_candidates.sort(key=lambda p: (int('refined' in p.name),
                                           int('resume' in p.name or 'continued' in p.name),
                                           int(p.stem.rsplit('v', 1)[-1]) if p.stem.rsplit('v', 1)[-1].isdigit() else 0))
    audit_path = FRONTIER / f'mask{index}-independent.json'
    audit = json.loads(audit_path.read_text()) if audit_path.is_file() else None
    accepted = bool(audit and audit.get('status') == 'PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
                    and audit.get('mask_index') == index and audit.get('parent_Uplus') == U
                    and audit.get('mask_exclusion_proved') is True and audit.get('constraints') == []
                    and audit.get('dependencies', {}).get('audit_capture_v9.py') == CHECKER)
    source = (next((p for p in source_candidates if sha(p) == audit['source_sha256']), None)
              if audit else None)
    if source is None and source_candidates:
        source = source_candidates[-1]
    payload = json.loads(source.read_text()) if source else None
    accepted = accepted and source is not None and payload.get('terminal') is True \
        and payload.get('contradiction') is not None and audit['nodes'][-1]['sha256'] == sha(source)
    if payload:
        total_producer += sum(float(json.loads(p.read_text()).get('seconds', 0))
                              for p in source_candidates)
    if audit:
        total_audit += float(audit.get('seconds', 0))
    if accepted:
        assert audit['source_sha256'] == sha(source)
        assert index in audit['transferred_canonical_mask_indices']
    live = ({str(i): sum(bool(row['residual_polygons']) for row in cell_rows)
             for i, cell_rows in payload['final_state']['cells'].items()}
            if payload else {})
    live = {k: v for k, v in live.items() if v}
    entry = {
        'mask_index': index,
        'occupied_cells': JOB['masks'][str(index)],
        'status': 'proved' if accepted else 'unresolved',
        'mask_exclusion_proved': bool(accepted),
        'constraints': [] if accepted else (audit.get('constraints', []) if audit else []),
        'proof_kind': 'unconditional_v9' if accepted else 'unresolved_exact_propagation',
        'source': f'certificates/{source.name}' if source else None,
        'source_sha256': sha(source) if source else None,
        'independent_audit': f'certificates/{audit_path.name}' if audit else None,
        'independent_audit_sha256': sha(audit_path) if audit else None,
        'checker_sha256': CHECKER if audit else None,
        'unresolved_obligations': [] if accepted else [
            'The exact residual polygons in the cited source final_state.cells remain '
            f'for owners and live angle rows {live}; establish an exhaustive '
            'unconditional contradiction for those center-angle domains and replay '
            'the complete ancestry with the independent v9 checker.'
        ],
    }
    results.append(entry)
    contradiction = payload.get('contradiction') if payload else None
    rows.append((index, entry['status'], source.name if source else 'none',
                 str(len(payload['steps'])) if payload else '0',
                 (f"{contradiction['kind']} (owner {contradiction.get('owner', '-')})" if contradiction else 'none'),
                 audit.get('status', 'none') if audit else 'none'))

complete = all(r['status'] == 'proved' for r in results)
result = {
    'job_id': 'cases-05',
    'status': 'complete' if complete else 'partial',
    'parent_Uplus': U,
    'assigned_mask_indices': JOB['mask_indices'],
    'results': results,
    'global_optimality_proved': False,
}
(DEST / 'result.json').write_text(json.dumps(result, indent=2) + '\n')

table = '\n'.join('| ' + ' | '.join(map(str, r)) + ' |' for r in rows)
proof = f'''# Exact exclusion attempt for cases-05

## Theorem and scope

For each index in the table, take the eleven closed unit squares, independent
orientations, the exact closed center cells, and the rational container side
`U = {U}` specified in `inputs/05-case-exclusions.md`. A row marked **proved**
has no such packing. This certificate bundle establishes {sum(r['status']=='proved' for r in results)}
of the {len(results)} assigned case exclusions. It does not establish global
optimality of the eleven-square packing.

## Exact proof method

The field map sends a centered container coordinate `c` to
`(L/U)(c+(U/2,U/2))`, where `L=191/50`. A unit square becomes a square of side
`B=L/U` in `[0,L]^2`; a center cell becomes the affine image of its specified
rational Voronoi polygon. Each orientation is represented by its own half-angle
`t` in the full closed interval `[0,1]`. Quarter-turn symmetry of a square
permits this individual orientation parametrization.

The fresh seed partitions every owner's full angle interval into 32 or 64
adjacent closed subintervals as recorded in each seed's exact `bins` field,
and clips each complete closed center cell only by a
necessary wall-containment envelope. The exact minimum of `cos(theta)+sin(theta)`
on an interval is attained at an endpoint. At each seed point, the separate wall
kernel verifies with rational inequalities that it lies **strictly inside** every
legal square of that owner, for all center and angle choices. The v9 replay
recomputes these premises, including the center cover hash
`df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e`.

The producer then propagates owned hulls. Because an owner's finitely many
strictly owned points all lie in the interior of its convex square, their
convex hull also lies in its interior. For an angle interval, a polygonal core
`Q` has every vertex certified strictly inside every square at that interval's
angle: after multiplying the four supporting-square inequalities by `1+t²`,
the assertion reduces to positivity of rational quadratics on a closed
interval, checked at endpoints and any interior minimum. A possible center
cannot lie in the Minkowski region `K + (-Q)` for another owner's hull `K`,
since this would force overlapping square interiors. Exact convex polygon
subtraction retains the remaining domains; completed updates promote only
points the owner square must contain. The independent v9 checker reconstructs
each update using separate rational hull and vertical-arrangement coverage
routines. Its replay checks each prior hull, interval cover, polygon core,
residual domain, and promotion before accepting a terminal contradiction.

All inequalities and polygon vertices are rational; interval endpoints,
container contact, cell boundaries, and inter-square contact are included.
No additional center, orientation, or contact assumptions were imposed.
The proof checker is `audit_capture_v9.py` at SHA-256 `{CHECKER}`.
For a proved row, the final source receipt is terminal, reports a contradiction,
and its complete seed and receipt ancestry is bound by hashes to a v9 audit
with empty constraints and `mask_exclusion_proved: true`. The contradiction
`all_parent_poses_forbidden` means one required owner's entire closed
center-angle domain is excluded by the verified induction; `owned_hulls_intersect`
means two mandatory strict-interior hulls intersect. Either contradicts a
legal packing. An open row is not an exclusion: its retained exact residual
domains are in the source receipt's `final_state.cells` and must still be
discharged.

## Case outcomes

| Index | Outcome | Final source | Completed steps | Terminal contradiction | Independent audit |
| --- | --- | --- | ---: | --- | --- |
{table}

The receipts and audit outputs are byte-preserved under `certificates/`, along
with seed ancestry and the exact cover. `replay.py` regenerates a clean work
tree from the pinned tool archives and reruns the independent checker.
Producer search elapsed time represented in the receipts totals about
`{total_producer:.1f}` seconds; checker receipt time totals about
`{total_audit:.1f}` seconds. These sums omit interrupted exploratory checks,
launcher, import, and file-copy
overhead. The environment was Python 3.12.14, gmpy2 2.3.1, SymPy 1.14.0,
NumPy 2.3.5. Python assertions must remain enabled.

The original case-tools bundle omitted four exact runtime source files. The
included `case-tools-supplement.zip` contains those verified original files;
its SHA-256 is `3f4fb8332b47405ae5f6be8c26a8e2a8062e32d4719675d28738a9d556bfa1c7`.
The `continuation-no-resplit.zip` used for 1499 (SHA-256
`196c5167064e0d9ab8b07f0602d2c77af647604ef9356857841756f8844d30c6`)
reproduces its source-bound no-resplit continuation.
'''
(DEST / 'proof.md').write_text(proof)

replay = '''#!/usr/bin/env python3
"""Re-audit all proved cases from immutable packet-05 receipts."""
import argparse, hashlib, json, os
from pathlib import Path
import shutil, subprocess, sys, tempfile, zipfile

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    root = Path(__file__).resolve().parent
    data = json.loads((root / 'result.json').read_text())
    p = argparse.ArgumentParser()
    p.add_argument('--workdir', type=Path, help='Fresh scratch directory to retain extracted sources and new audits')
    p.add_argument('--indices', nargs='*', type=int,
                   help='Optional assigned indices; by default replay every proved case')
    args = p.parse_args()
    if args.workdir:
        work = args.workdir.resolve()
        work.mkdir(parents=True, exist_ok=True)
        temporary = None
    else:
        temporary = tempfile.TemporaryDirectory(prefix='cases-05-replay-')
        work = Path(temporary.name)
    for name in ('case-tools.zip', 'case-tools-supplement.zip', 'continuation-no-resplit.zip'):
        with zipfile.ZipFile(root / 'inputs' / name) as archive:
            archive.extractall(work)
    frontier = work / 'research/frontier'
    for source in (root / 'certificates').glob('*.json'):
        shutil.copy2(source, frontier / source.name)
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
    assert sys.flags.optimize == 0, 'Python assertions are required'
    for entry in data['results']:
        if entry['status'] != 'proved':
            continue
        index = entry['mask_index']
        if args.indices and index not in args.indices:
            continue
        source = frontier / Path(entry['source']).name
        assert sha(source) == entry['source_sha256']
        output = work / f'mask{index}-replayed-audit.json'
        cmd = [sys.executable, str(frontier / 'audit_case.py'), str(source), '--output', str(output)]
        with (work / f'mask{index}-replay.log').open('w') as log:
            subprocess.run(cmd, cwd=work, env=env, check=True, stdout=log, stderr=subprocess.STDOUT)
        report = json.loads(output.read_text())
        assert report['status'] == 'PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
        assert report['mask_exclusion_proved'] is True and report['constraints'] == []
        assert report['source_sha256'] == sha(source)
        print(f'PASS {index}', flush=True)
    print('Independent replay passed for every proved packet-05 case.')

if __name__ == '__main__':
    main()
'''
(DEST / 'replay.py').write_text(replay)

with (DEST / 'SHA256SUMS').open('w') as f:
    for path in sorted(DEST.rglob('*')):
        if path.is_file() and path.name != 'SHA256SUMS':
            f.write(f'{sha(path)}  {path.relative_to(DEST).as_posix()}\n')
print(DEST, 'proved', sum(r['status']=='proved' for r in results), 'of', len(results),
      'producer_seconds', round(total_producer, 1), 'audit_seconds', round(total_audit, 1))
