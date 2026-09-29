"""Native-platform adapter for the unchanged source-bound cached node audit.

The original cache checker hardcodes a Linux GMP binary pathname. This
adapter instead requires a cached native receipt to bind the actual loaded
GMP binary and version. All source hashes, recursive premise hashes, node
hashes, and geometric replay checks remain enforced.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import gmpy2

HERE = Path(__file__).resolve().parent
HULL = HERE.parent / 'phase3/work/phase3/hull'
sys.path.insert(0, str(HULL))
os.environ['ELEVEN_RATIONAL_BACKEND'] = 'gmp'
import audit_cached_node_v2 as runner
a = runner.a
cache = runner.cache


def dependencies_match(proof, path, seen=None):
    seen = set() if seen is None else seen
    fingerprint = a.sha(path)
    if fingerprint in seen:
        return
    seen.add(fingerprint)
    roots = [a.WORK/'phase3/hull', a.WORK/'phase3/collision',
             a.WORK/'phase2/hull', a.WORK/'geometry',
             a.ROOT/'research/optimality/audit']
    for name, digest in proof['dependencies'].items():
        assert any((root/name).is_file() and a.sha(root/name) == digest
                   for root in roots), 'Cached checker dependency changed: ' + name
    if proof.get('rational_backend') == 'gmp':
        assert a.rational.BACKEND == 'gmp'
        assert proof['rational_backend_version'] == a.rational.VERSION
        assert a.sha(a.rational.BINARY) == proof['rational_binary_sha256']
    for premise in proof.get('premise_audits', []):
        p = a.locate(premise['path'], path)
        assert a.sha(p) == premise['sha256']
        prior = json.loads(p.read_text())
        assert prior['root_sha256'] == proof['root_sha256']
        assert prior['root_audit_sha256'] == proof['root_audit_sha256']
        assert prior['status'] in (
            'PASS_INDEPENDENT_BRANCH_HULL_AUDIT',
            'PASS_INDEPENDENT_GENERIC_HULL_AUDIT',
            'PASS_INDEPENDENT_PARTIAL_TREE_AUDIT',
            'RUNNING_INDEPENDENT_TREE_AUDIT')
        dependencies_match(prior, p, seen)


if __name__ == '__main__':
    cache.dependencies_match = dependencies_match
    runner.main()
    output = Path(sys.argv[sys.argv.index('--output') + 1])
    result = json.loads(output.read_text())
    result['native_portability_adapter'] = {
        'path': str(Path(__file__).resolve()),
        'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope': 'Cached GMP binary identity is checked against the actually loaded native binary; mathematical replay unchanged.'
    }
    output.write_text(json.dumps(result, indent=2) + '\n')
