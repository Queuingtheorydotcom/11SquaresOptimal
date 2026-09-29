"""Recheck every packet-12 exclusion with the frozen independent v9 checker.

Tested with Python 3.12.14, gmpy2 2.3.1, SymPy 1.14.0, NumPy 2.3.5.
Usage: python replay.py [--indices 2102 2122]
Do not run Python with -O or -OO: assertions are proof obligations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent
CHECKER = '95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c'
COVER = 'df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    if not __debug__:
        raise RuntimeError('Assertions must remain enabled')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--indices', nargs='+', type=int)
    args = parser.parse_args()
    expected = json.loads((ROOT / 'result.json').read_text())
    by_index = {row['mask_index']: row for row in expected['results']}
    indices = args.indices or expected['assigned_mask_indices']
    assert len(set(indices)) == len(indices) and all(n in by_index for n in indices)

    for line in (ROOT / 'SHA256SUMS').read_text().splitlines():
        value, relative = line.split('  ', 1)
        assert sha256(ROOT / relative) == value, f'Changed file: {relative}'

    with tempfile.TemporaryDirectory(prefix='eleven-packet12-') as temp:
        workspace = Path(temp)
        with ZipFile(ROOT / 'case-tools.zip') as bundle:
            assert all(not Path(name).is_absolute() and '..' not in Path(name).parts
                       for name in bundle.namelist())
            bundle.extractall(workspace)
        research = workspace / 'research'
        frontier = research / 'frontier'
        frontier.mkdir(exist_ok=True)
        for file in (ROOT / 'certificates').glob('*.json'):
            shutil.copy2(file, frontier / file.name)
        for name in ('fast_convex_v2.py', 'fast_grid.py'):
            dest = research / 'phase3/work/phase3/capture/gmp' / name
            dest.parent.mkdir(exist_ok=True)
            shutil.copy2(ROOT / 'adapters' / name, dest)
        dest = research / 'phase3/work/phase3/core/fast_core_v2.py'
        shutil.copy2(ROOT / 'adapters/fast_core_v2.py', dest)

        checker = research / 'phase3/work/phase3/hull/audit_capture_v9.py'
        cover = research / 'phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json'
        assert sha256(checker) == CHECKER and sha256(cover) == COVER
        assert sha256(frontier / cover.name) == COVER

        environment = os.environ.copy()
        environment['OPENBLAS_NUM_THREADS'] = '1'
        environment['PYTHONDONTWRITEBYTECODE'] = '1'
        for index in indices:
            row = by_index[index]
            source = frontier / Path(row['source']).name
            seed = frontier / f'mask{index}-self-v1-seed.json'
            receipt = json.loads((ROOT / row['independent_audit']).read_text())
            assert sha256(source) == row['source_sha256'] == receipt['source_sha256']
            assert sha256(seed) == receipt['root_sha256']
            assert sha256(ROOT / row['independent_audit']) == row['independent_audit_sha256']
            for node in receipt['nodes']:
                ancestor = frontier / Path(node['path']).name
                assert sha256(ancestor) == node['sha256'], ancestor

            target = workspace / f'audit-{index}.json'
            command = [sys.executable, str(research / 'frontier/audit_case.py'),
                       str(source), '--output', str(target)]
            done = subprocess.run(command, cwd=workspace, env=environment,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                  text=True, check=False)
            if done.returncode:
                raise RuntimeError(f'Independent checker failed case {index}: {done.stderr}')
            actual = json.loads(target.read_text())
            for key in ('status', 'mask_index', 'mask', 'parent_Uplus', 'constraints',
                        'source_sha256', 'root_sha256', 'mask_exclusion_proved',
                        'transferred_canonical_mask_indices'):
                assert actual[key] == receipt[key], (index, key)
            assert actual['status'] == 'PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
            assert actual['constraints'] == [] and actual['mask_exclusion_proved']
            assert index in actual['transferred_canonical_mask_indices']
            print(f'{index}: independent exact exclusion PASS', flush=True)

    print(f'Passed {len(indices)} selected packet-12 cases')


if __name__ == '__main__':
    main()
