"""Run unchanged exact tree replay with reviewed native cache identity checks."""
import hashlib
import json
from pathlib import Path
import sys
import audit_native_cached as native
import audit_tree_batch_v4 as tree

if __name__ == '__main__':
    tree.dependencies_match = native.dependencies_match
    tree.main()
    output = Path(sys.argv[sys.argv.index('--output')+1])
    result = json.loads(output.read_text())
    result['native_portability_adapters'] = [
        dict(path=str(p.resolve()), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        for p in (Path(__file__), Path(native.__file__))
    ]
    result['native_portability_scope'] = (
        'Only cached GMP binary identity is checked against the actually loaded native '
        'binary; source bindings, exact partition checks, and geometric replay are unchanged.')
    output.write_text(json.dumps(result, indent=2)+'\n')
