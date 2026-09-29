#!/usr/bin/env python3
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
