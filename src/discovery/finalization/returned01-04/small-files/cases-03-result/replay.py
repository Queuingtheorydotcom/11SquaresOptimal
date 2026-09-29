#!/usr/bin/env python3
"""Verify all packet-03 receipts with the frozen independent rational checker."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

assert __debug__, 'Python assertions are proof obligations; do not use -O/-OO'
BASE = Path(__file__).resolve().parent
CERT = BASE / 'certificates'
U = '387708359002281417731/100000000000000000000'
CHECKER = '95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c'
COVER = 'df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read_manifest():
    lines = (BASE / 'SHA256SUMS').read_text().splitlines()
    for line in lines:
        h, relative = line.split('  ', 1)
        p = BASE / relative
        assert p.is_file(), p
        assert sha(p) == h, ('hash mismatch', relative)
    return len(lines)

def verify_chain(source, audit, workspace):
    """Check producer ancestry and shipped code without trusting path strings."""
    chain=[]
    current=source
    while True:
        node=json.loads(current.read_text())
        assert node['terminal'] is True, ('intermediate checkpoint',current)
        assert node['schema']=='exact_generic_owned_hull_v1'
        for original, expected in node['dependencies'].items():
            parts=Path(original).parts
            assert 'research' in parts, original
            local=workspace / Path(*parts[parts.index('research'):])
            assert local.is_file() and sha(local)==expected, ('program dependency',original)
        chain.append(sha(current))
        if node['parent'] is None:
            root_ref=node['source']
            seed=CERT / Path(root_ref['path']).name
            assert seed.is_file() and sha(seed)==root_ref['sha256']
            root=json.loads(seed.read_text())
            assert root['schema']=='generic_wall_seed_v1'
            cover=workspace / 'research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json'
            groups=workspace / 'research/phase3/work/geometry/wall_ownership_groups.json'
            producer=workspace / 'research/phase3/work/phase3/generic/generic_pose_engine_v5.py'
            assert root['cover_source']['sha256']==sha(cover)
            assert root['wall_groups_source']['sha256']==sha(groups)
            assert root['producer_source']['sha256']==sha(producer)
            assert audit['root_sha256']==sha(seed)
            break
        parent=node['parent']
        current=CERT / Path(parent['path']).name
        assert current.is_file() and sha(current)==parent['sha256']
    assert [n['sha256'] for n in audit['nodes']]==list(reversed(chain))

def same_stable_audit(record, fresh):
    keys = ('status','source_sha256','mask_index','mask','parent_Uplus','parent_side',
            'cover_sha256','constraints','final_state_sha256','root_sha256',
            'bootstrap','seed_ownership_checks','branch_exclusion_proved',
            'inside_local_guard','mask_exclusion_proved','global_optimality_proved',
            'transferred_canonical_mask_indices','continuum_canonical_masks_excluded',
            'dependencies','rational_backend','rational_backend_version')
    for key in keys:
        assert record[key] == fresh[key], ('audit mismatch',key)
    assert len(record['nodes']) == len(fresh['nodes'])
    nodekeys = ('sha256','node','complete_steps','rows','arrangement_slabs',
                'promoted_grid_vertices','constraints','branch_exclusion_proved',
                'inside_local_guard')
    for old, new in zip(record['nodes'], fresh['nodes']):
        for key in nodekeys:
            assert old[key] == new[key], ('node mismatch',key)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proved-only', action='store_true',
                        help='skip open partial receipts while independently checking proved cases')
    args = parser.parse_args()
    print('Verified',read_manifest(),'artifact hashes',flush=True)
    result = json.loads((BASE / 'result.json').read_text())
    assert result['job_id'] == 'cases-03' and result['parent_Uplus'] == U
    assert len(result['assigned_mask_indices']) == len(result['results']) == 15
    assert [r['mask_index'] for r in result['results']] == result['assigned_mask_indices']
    assert result['global_optimality_proved'] is False
    assert result['status']==('complete' if all(r['mask_exclusion_proved'] for r in result['results']) else 'partial')
    with tempfile.TemporaryDirectory(prefix='packet03-replay-') as tmp:
        workspace = Path(tmp)
        with zipfile.ZipFile(BASE / 'software/case-tools.zip') as archive:
            archive.extractall(workspace)
        original = BASE / 'software/recovered-gmp'
        dst = workspace / 'research/phase3/work/phase3/capture/gmp'
        dst.mkdir(parents=True, exist_ok=True)
        for src in original.glob('*.py'):
            shutil.copy2(src, dst / src.name)
        coredst = workspace / 'research/phase3/work/phase3/core'
        coredst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original / 'fast_core_v2.py',coredst / 'fast_core_v2.py')
        for src in (BASE / 'software/extra-producer').rglob('*.py'):
            dst = workspace / src.relative_to(BASE / 'software/extra-producer')
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
        checker = workspace / 'research/phase3/work/phase3/hull/audit_capture_v9.py'
        cover = workspace / 'research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json'
        assert sha(checker) == CHECKER and sha(cover) == COVER
        assert sha(CERT / cover.name) == COVER
        for r in result['results']:
            m = r['mask_index']
            src = BASE / r['source']
            audit = BASE / r['independent_audit']
            assert sha(src)==r['source_sha256']
            assert sha(audit)==r['independent_audit_sha256']
            assert r['checker_sha256']==CHECKER
            d = json.loads(src.read_text());a = json.loads(audit.read_text())
            assert d['mask_index']==a['mask_index']==m
            assert d['mask']==a['mask']==r['occupied_cells']
            assert str(d['U'])==a['parent_Uplus']==U
            assert d['constraints']==a['constraints']==r['constraints']==[]
            assert a['source_sha256']==sha(src)
            verify_chain(src,a,workspace)
            if args.proved_only and r['status'] != 'proved':
                print(m, 'open (not replayed)',flush=True)
                continue
            out = workspace / f'mask{m}-fresh-independent.json'
            cmd = [sys.executable, '-B',str(workspace / 'research/frontier/audit_case.py'),
                   str(src),'--output',str(out)]
            env = dict(os.environ,OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
            with (workspace / f'mask{m}-replay.log').open('w') as log:
                subprocess.run(cmd,cwd=workspace,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            fresh = json.loads(out.read_text())
            same_stable_audit(a,fresh)
            if r['status']=='proved':
                assert a['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
                assert a['branch_exclusion_proved'] is True
                assert a['mask_exclusion_proved'] is True
                assert m in a['transferred_canonical_mask_indices']
                assert r['mask_exclusion_proved'] is True
            else:
                assert a['mask_exclusion_proved'] is False
                assert r['mask_exclusion_proved'] is False
            print(m,r['status'],'independent replay passed',flush=True)
    print('Packet 03 replay complete',flush=True)

if __name__=='__main__':
    main()
