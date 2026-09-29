#!/usr/bin/env python3
"""Fresh, independent exact v9 replay of packet 09 proof traces.

Requires Python 3.12, native gmpy2 2.3.1; the archived producer used
SymPy 1.14 and NumPy 2.5.3. Never run Python with -O or -OO.
Usage: python replay.py --mask 1847   (or --all)
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

if not __debug__:
    raise SystemExit('Assertions must remain enabled')
HERE = Path(__file__).resolve().parent
RESULT = json.loads((HERE/'result.json').read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_inventory():
    listed={}
    for line in (HERE/'SHA256SUMS').read_text().splitlines():
        expected,separator,name=line.partition('  ')
        assert separator and len(expected)==64 and name
        path=Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert name not in listed
        listed[name]=expected
    present={str(p.relative_to(HERE)):p for p in HERE.rglob('*')
             if p.is_file() and p.name!='SHA256SUMS'}
    assert set(present)==set(listed),'Missing or unlisted bundle files'
    for name,p in sorted(present.items()):
        assert sha(p)==listed[name],f'Bundle checksum mismatch: {name}'

def check_entry(entry,root):
    mask=entry['mask_index']
    if not entry['mask_exclusion_proved']:
        print(f'{mask}: unresolved; no completed proof to replay',flush=True)
        return False
    src=HERE/entry['source']; saved=HERE/entry['independent_audit']
    assert sha(src)==entry['source_sha256']
    assert sha(saved)==entry['independent_audit_sha256']
    assert sha(HERE/entry['root_seed'])==entry['root_seed_sha256']
    target=root/'research/frontier';target.mkdir(parents=True,exist_ok=True)
    source_paths=[entry['root_seed'],*(n['path'] for n in entry['source_ancestry'])]
    source_paths.append('certificates/center-cover-symmetric-exact.json')
    for relative in source_paths:
        shutil.copyfile(HERE/relative,target/Path(relative).name)
    checker=root/'research/phase3/work/phase3/hull/audit_capture_v9.py'
    assert sha(checker)==entry['checker_sha256']
    fresh=target/f'mask{mask}-fresh-independent.json'
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable,str(root/'research/frontier/audit_case.py'),
                    str(target/src.name),'--output',str(fresh)],check=True,cwd=root,env=env)
    actual=json.loads(fresh.read_text()); previous=json.loads(saved.read_text())
    fixed_fields=('status','source_sha256','mask_index','mask','parent_Uplus',
                  'cover_sha256','constraints','root_sha256','final_state_sha256',
                  'mask_exclusion_proved','branch_exclusion_proved',
                  'transferred_canonical_mask_indices','continuum_canonical_masks_excluded',
                  'bootstrap','seed_ownership_checks')
    assert all(actual[field]==previous[field] for field in fixed_fields)
    geometry=('sha256','node','complete_steps','rows','arrangement_slabs',
              'promoted_grid_vertices','constraints','branch_exclusion_proved')
    assert len(actual['nodes'])==len(previous['nodes'])
    assert all(all(a[f]==b[f] for f in geometry)
               for a,b in zip(actual['nodes'],previous['nodes']))
    assert actual['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
    assert actual['mask_exclusion_proved'] is True and actual['constraints']==[]
    print(f'{mask}: PASS exact v9 replay, {len(actual["nodes"])} nodes',flush=True)
    return True

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--mask',type=int)
    group.add_argument('--all',action='store_true')
    args=p.parse_args()
    check_inventory()
    chosen=[r for r in RESULT['results'] if args.all or r['mask_index']==args.mask]
    assert chosen,'Unknown assigned mask'
    with tempfile.TemporaryDirectory(prefix='cases09-replay-') as tmp:
        root=Path(tmp)
        with zipfile.ZipFile(HERE/'case-tools.zip') as z:
            z.extractall(root)
        succeeded=[check_entry(r,root) for r in chosen]
    if not all(succeeded):raise SystemExit(1)

if __name__=='__main__':main()
