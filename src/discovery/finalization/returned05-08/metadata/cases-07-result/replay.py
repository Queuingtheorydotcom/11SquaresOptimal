#!/usr/bin/env python3
"""Replay packet-07 exclusions from the immutable returned receipts.

Usage: python replay.py [--mask 1673] [--workdir /path/to/extracted-code]
Requires Python 3.12 with native gmpy2 2.3.1, SymPy 1.14, NumPy 2.5.3.
Do not run with -O or -OO.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

assert __debug__, 'Assertions are proof obligations.'
HERE = Path(__file__).resolve().parent
CHECKER = '95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c'
COVER = 'df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
SUPPLEMENT = '3f4fb8332b47405ae5f6be8c26a8e2a8062e32d4719675d28738a9d556bfa1c7'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def check_manifest():
    seen = set()
    for line in (HERE / 'SHA256SUMS').read_text().splitlines():
        digest, relative = line.split('  ', 1)
        path = HERE / relative
        assert path.is_file() and sha(path) == digest, relative
        seen.add(relative)
    expected = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*')
                if p.is_file() and p.name != 'SHA256SUMS'}
    assert seen == expected, (sorted(expected - seen), sorted(seen - expected))

def run(destination, masks):
    work = destination / 'code'
    work.mkdir(parents=True, exist_ok=True)
    for name in ('case-tools.zip', 'case-tools-supplement.zip'):
        with zipfile.ZipFile(HERE / 'tools' / name) as z:
            z.extractall(work)
    assert sha(HERE / 'tools/case-tools-supplement.zip') == SUPPLEMENT
    wrapper = work / 'research/frontier/audit_case.py'
    checker = work / 'research/phase3/work/phase3/hull/audit_capture_v9.py'
    cover = work / 'research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json'
    assert sha(checker) == CHECKER and sha(cover) == COVER
    cert = work / 'research/frontier'
    for p in (HERE / 'certificates').iterdir():
        if p.is_file():
            shutil.copyfile(p, cert / p.name)
    assert sha(cert / 'center-cover-symmetric-exact.json') == COVER
    result = json.loads((HERE / 'result.json').read_text())
    environment = dict(os.environ, OPENBLAS_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
    for row in result['results']:
        m = row['mask_index']
        if masks and m not in masks:
            continue
        if not row['mask_exclusion_proved']:
            print(f'{m}: unresolved in returned result; no exclusion to replay')
            continue
        source = cert / Path(row['source']).name
        original = HERE / row['independent_audit']
        output = destination / f'mask{m}-replayed.json'
        assert sha(source) == row['source_sha256']
        assert sha(original) == row['independent_audit_sha256']
        subprocess.run([sys.executable, str(wrapper), str(source), '--output', str(output)],
                       check=True, cwd=work, env=environment, stdout=subprocess.DEVNULL)
        audited = json.loads(output.read_text())
        archived = json.loads(original.read_text())
        assert audited['status'] == 'PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
        assert audited['mask_exclusion_proved'] is True
        assert audited['mask_index'] == m and audited['mask'] == row['occupied_cells']
        assert audited['constraints'] == [] and audited['parent_Uplus'] == result['parent_Uplus']
        assert audited['source_sha256'] == row['source_sha256']
        assert audited['dependencies']['audit_capture_v9.py'] == CHECKER
        assert audited['cover_sha256'] == COVER
        for key in ('status','mask_index','mask','constraints','source_sha256','root_sha256',
                    'final_state_sha256','mask_exclusion_proved','continuum_canonical_masks_excluded'):
            assert audited[key] == archived[key], (m,key)
        assert m in audited['transferred_canonical_mask_indices']
        print(f'{m}: PASS independent exact replay')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mask', type=int, action='append', help='Repeat selected index only')
    parser.add_argument('--workdir', type=Path, help='Keep extracted code and checker outputs here')
    args = parser.parse_args()
    check_manifest()
    if args.workdir:
        args.workdir.mkdir(parents=True, exist_ok=True)
        run(args.workdir.resolve(), set(args.mask or []))
    else:
        with tempfile.TemporaryDirectory(prefix='packet07-replay-') as directory:
            run(Path(directory), set(args.mask or []))

if __name__ == '__main__':
    main()
