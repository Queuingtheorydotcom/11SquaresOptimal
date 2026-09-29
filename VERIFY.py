#!/usr/bin/env python3
"""Prepare and replay all geometric/algebraic stages, or inspect the public inputs."""
from pathlib import Path
import argparse, os, shutil, subprocess, sys
from tools.content import ROOT, load_index, materialize

def main():
    if not __debug__:
        raise SystemExit('Do not use Python -O or -OO: assertions must be enabled.')
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prepare-only', action='store_true', help='Decode certificates without executing proof checks')
    ap.add_argument('--check-package', action='store_true', help='Check distribution integrity/privacy; NOT a proof replay')
    ap.add_argument('--workspace', type=Path, default=ROOT/'work', help='Empty or partially prepared output directory')
    args = ap.parse_args()
    if args.check_package:
        subprocess.run([sys.executable, '-B', str(ROOT/'tools/check_package.py')], check=True)
        return
    index = load_index()
    work = args.workspace.resolve()
    if not work.exists():
        needed = sum(index['objects'][h]['bytes'] for h in index['files'].values())
        existing = work.parent
        while not existing.exists():
            existing = existing.parent
        if shutil.disk_usage(existing).free < needed + 2_000_000_000:
            raise SystemExit(f'Preparation needs approximately {needed/1e9:.1f} GB plus 2 GB working space. Use --workspace on a larger disk.')
    materialize(index, work)
    if args.prepare_only:
        print('PREPARED_INPUTS_ONLY — no geometric proof replay was performed.')
        return
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1',
               OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    result = subprocess.run([sys.executable, '-B', str(work/'evidence/RUN_ALL.py')],
                            cwd=work/'evidence', env=env)
    if result.returncode:
        raise SystemExit(result.returncode)
    print('Full replay driver completed. Inspect its newly generated global result and stage record.')

if __name__ == '__main__':
    main()
