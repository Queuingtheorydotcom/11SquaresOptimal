#!/usr/bin/env python3
"""Verify the portable historical baseline, or explicitly replay its geometry.

Default work is never implicit: choose reuse, field, generic, all, or summary.
Proof files and original receipts remain byte-identical. Only addresses and
native GMP loading are adapted; mathematical checkers are immutable.
"""
if not __debug__:
    raise SystemExit('Optimized Python (-O/-OO) is not a proof verification mode.')

import argparse
import builtins
import copy
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig

HERE = 'research/finalization/baseline-portable/'
INVENTORY = HERE + 'SOURCE_INVENTORY.json'
INVENTORY_SHA = 'eb86c86ca071bc3a6286cec3c7d90bef62800a96154dc1ccf6be74ac45eb80fb'
CONSUMER = HERE + 'baseline_reconstruct.py'
CONSUMER_SHA = 'ec47984510e847bbbb87dc924d8865fb5ff4510f0ce7c8558f55531b502a1b0c'
HISTORICAL = 'research/PHASE3_FRESH_REPLAY_RESULT.json'
HISTORICAL_SHA = '04fa1ebb37f5dace29946224fe8c7c5d8a1bedb4fa860c65b359f4200415de57'
HISTORICAL_GMP = '4fdf5fbaea9d3c4f756f9f656d0d7656fc4a66c82a8e921f326e570702dc463d'
GMP_VERSION = '2.3.1'
MANIFEST = 'research/phase3/PHASE3_REPLAY_MANIFEST.json'
RESULT_DIR = 'results/baseline-portable'
COUNTS = {'field': 59, 'generic': 34}
RAW_OPEN, RAW_IO_OPEN = builtins.open, io.open
P_OPEN, P_RESOLVE, P_STAT, P_LSTAT = Path.open, Path.resolve, Path.stat, Path.lstat


def need(value, message):
    if not value:
        raise ValueError(message)


def within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def absolute(path):
    return Path(os.path.abspath(os.fspath(path)))


def digest(path):
    h = hashlib.sha256()
    with RAW_OPEN(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    with RAW_OPEN(path, encoding='utf-8') as stream:
        return json.load(stream)


class Package:
    def __init__(self, root):
        self.root = P_RESOLVE(root, strict=True)
        self.launcher = P_RESOLVE(Path(__file__), strict=True)
        need(within(self.launcher, self.root), 'Use the launcher copied inside the package')
        self.launcher_sha = digest(self.launcher)
        self.inventory_path = self.confined(INVENTORY)
        need(digest(self.inventory_path) == INVENTORY_SHA, 'Source inventory changed')
        inv = read_json(self.inventory_path)
        need(inv['schema'] == 'eleven_square_baseline_portable_inventory_v1', 'Wrong inventory schema')
        need(inv['archive_members'] == 398 and inv['external_local_artifacts'] == 100, 'Wrong inventory cardinality')
        need(inv['historical_native_gmp_version'] == GMP_VERSION, 'Historical GMP version changed')
        need(inv['historical_native_gmp_binary_sha256'] == HISTORICAL_GMP, 'Historical GMP provenance changed')
        need(inv['consumer_path'] == CONSUMER and inv['consumer_sha256'] == CONSUMER_SHA, 'Union consumer changed')
        self.original = Path(inv['original_workspace'])
        need(self.original.is_absolute(), 'Historical workspace must be absolute')
        self.expected = {}
        for item in inv['files']:
            key = item['path']
            p = self.confined(key)
            need(key not in self.expected, 'Duplicate declared source')
            need(len(item['sha256']) == 64, 'Invalid source digest')
            self.expected[key] = item['sha256']
        need(len(self.expected) == 498, 'Incomplete source inventory')
        need(self.expected[HISTORICAL] == HISTORICAL_SHA, 'Historical receipt pin differs')
        self.common = set(inv['common_paths'])
        need(self.common <= self.expected.keys(), 'Unlisted common source')
        self.groups = {}
        for group in inv['groups']:
            key = (group['family'], group['index'])
            need(key not in self.groups, 'Duplicate proof group')
            need(set(group['input_paths']) <= self.expected.keys(), 'Unlisted group source')
            self.groups[key] = set(group['input_paths'])
        need(set(self.groups) == {(f, i) for f, n in COUNTS.items() for i in range(n)}, 'Incomplete proof groups')
        self.results = self.confined(RESULT_DIR)
        self.results.mkdir(parents=True, exist_ok=True)
        need(P_RESOLVE(self.results) == self.results, 'Results directory is redirected')
        self.path_mappings = set()
        self.verified = {}
        self.manifest = self.read(MANIFEST)
        self.historical = self.read(HISTORICAL)
        self.records = {}
        for family, plural in [('field', 'fields'), ('generic', 'generic')]:
            collection = self.read('research/phase3-fresh-' + plural + '/RESULT.json')
            records = collection['records']
            need(len(records) == COUNTS[family], 'Wrong historical record count')
            need([r['index'] for r in records] == list(range(COUNTS[family])), 'Wrong historical order')
            for record in records:
                self.records[family, record['index']] = record
        self.certs = {}
        for cert in self.historical['certificates']:
            key = cert['family'], self.key(cert['fresh_audit'])
            need(key not in self.certs, 'Duplicate historical certificate')
            self.certs[key] = cert
        need(len(self.certs) == 93, 'Wrong certificate inventory')

    def confined(self, relative):
        rel = Path(relative)
        need(not rel.is_absolute() and '..' not in rel.parts, 'Unsafe package relative path: ' + str(rel))
        p = P_RESOLVE(self.root / rel)
        need(within(p, self.root), 'Path escapes package through a symlink: ' + str(rel))
        # Preserve source identity: reject even an internal symlink alias.
        need(p == absolute(self.root / rel), 'Declared path is redirected: ' + str(rel))
        return p

    def key(self, value):
        p = Path(value)
        if p.is_absolute():
            p = absolute(p)
            if within(p, self.root):
                p = p.relative_to(self.root)
            elif within(p, self.original):
                old = p
                p = p.relative_to(self.original)
                self.path_mappings.add((str(old), p.as_posix()))
            else:
                raise ValueError('Undeclared absolute historical path: ' + str(p))
        need('..' not in p.parts, 'Parent traversal in reference')
        return p.as_posix()

    def source(self, value):
        key = self.key(value)
        need(key in self.expected, 'Unlisted proof source: ' + key)
        return self.confined(key)

    def hash(self, value):
        key = self.key(value)
        if key in self.expected:
            actual = digest(self.source(key))
            need(actual == self.expected[key], 'Source hash mismatch: ' + key)
            self.verified[key] = actual
            return actual
        path = self.confined(key)
        need(within(path, self.results), 'Unlisted proof hash: ' + key)
        return digest(path)

    def read(self, value):
        key = self.key(value)
        if key in self.expected:
            self.hash(key)
            return read_json(self.source(key))
        path = self.confined(key)
        need(within(path, self.results), 'Unlisted proof read: ' + key)
        return read_json(path)

    def verify(self, paths):
        for key in sorted(paths):
            self.hash(key)

    def load_consumer(self):
        path = self.confined(CONSUMER)
        need(digest(path) == CONSUMER_SHA, 'Union reconstruction source changed')
        spec = importlib.util.spec_from_file_location('baseline_portable_union', path)
        module = importlib.util.module_from_spec(spec)
        # Compile source explicitly; never use a pre-existing bytecode cache.
        exec(compile(P_OPEN(path).read(), str(path), 'exec'), module.__dict__)
        return module

    def result_path(self, family, index):
        return self.results / f'{family}-{index:02d}.json'

    def trace_path(self, family, index):
        return self.results / f'{family}-{index:02d}.trace.json'

    def write(self, path, data):
        need(within(P_RESOLVE(path), self.results), 'Output escaped result directory')
        with RAW_OPEN(path, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2)
            stream.write('\n')

    def guards(self):
        need(digest(self.launcher) == self.launcher_sha, 'Launcher changed during run')
        need(digest(self.inventory_path) == INVENTORY_SHA, 'Inventory changed during run')
        need(digest(self.confined(CONSUMER)) == CONSUMER_SHA, 'Consumer changed during run')

    def provenance(self):
        return dict(adapter_sha256=self.launcher_sha, source_inventory_sha256=INVENTORY_SHA,
                    union_consumer_sha256=CONSUMER_SHA, historical_receipt_sha256=HISTORICAL_SHA)


def normalized_receipt(package, family, receipt):
    result = copy.deepcopy(receipt)
    if family == 'field':
        for item in result['control_receipts']:
            item['path'] = package.key(item['path'])
            need(item['path'] in package.expected, 'Unknown control receipt path')
            need(item['sha256'] == package.expected[item['path']], 'Control receipt binding differs')
    else:
        # Exactly these non-geometric fields may vary. All other nested values,
        # including hashes, statuses, constraints, coverage, and root, must match.
        need(type(result['seconds']) in (int, float) and result['seconds'] >= 0, 'Invalid elapsed time')
        del result['seconds']
        need(result['rational_backend'] == 'gmp' and result['rational_backend_version'] == GMP_VERSION,
             'Wrong rational backend')
        del result['rational_binary_sha256']
        for item in result['nodes']:
            item['path'] = package.key(item['path'])
            need(item['path'] in package.expected, 'Unknown ancestry node path')
            need(item['sha256'] == package.expected[item['path']], 'Ancestry node binding differs')
    return result


def compare_receipt(package, family, index, fresh, native_sha):
    record = package.records[family, index]
    old = package.read(record['output'])
    need(package.hash(record['output']) == record['fresh_sha256'], 'Historical record digest differs')
    cert = package.certs[family, package.key(record['output'])]
    need(cert['fresh_audit_sha256'] == record['fresh_sha256'], 'Historical aggregate digest differs')
    if family == 'generic':
        need(old['rational_binary_sha256'] == HISTORICAL_GMP, 'Historical binary provenance differs')
        need(fresh['rational_binary_sha256'] == native_sha, 'Fresh receipt does not identify actual native binary')
    need(normalized_receipt(package, family, fresh) == normalized_receipt(package, family, old),
         'Fresh receipt differs semantically from its historical receipt')


def reuse(package):
    package.verify(package.expected)
    computed = package.load_consumer().reconstruct(package.root / 'research', package.read,
        package.hash, GMP_VERSION, HISTORICAL_GMP)
    # Full equality includes all93 source/receipt hashes, exact case lists,
    # provenance and every recorded aggregate field. Original JSON is untouched.
    need(computed == package.historical, 'Historical complete union receipt differs')
    package.guards()
    result = dict(status='PASS_HISTORICAL_BASELINE_BINDINGS_AND_EXACT_UNION',
        fresh_geometry_replayed=False, field_certificates=59, generic_certificates=34,
        excluded=1931, remaining=253,
        excluded_canonical_mask_indices=computed['excluded_canonical_mask_indices'],
        remaining_canonical_mask_indices=computed['remaining_canonical_mask_indices'],
        historical_native_gmp_version=GMP_VERSION, historical_native_gmp_binary_sha256=HISTORICAL_GMP,
        verified_source_files=498, verified_source_hashes=dict(sorted(package.verified.items())),
        path_mappings=[dict(original=a, package_relative=b) for a, b in sorted(package.path_mappings)],
        global_optimality_proved=False,
        scope='Exact recomposition and source binding of previously completed independent geometric audits; no geometric replay in this invocation.',
        **package.provenance())
    package.write(package.results / 'HISTORICAL_BASELINE_RESULT.json', result)
    print(json.dumps({k: result[k] for k in ('status', 'fresh_geometry_replayed', 'excluded', 'remaining', 'verified_source_files')}))


SOURCES = {
    'rational': 'work/phase3/hull/rational.py',
    'arrangement_audit': 'work/phase3/hull/arrangement_audit.py',
    'arrangement_audit_v2': 'work/phase3/hull/arrangement_audit_v2.py',
    'audit_residual_kernel': 'work/phase3/hull/audit_residual_kernel.py',
    'audit_wall_kernel': 'work/geometry/audit_wall_kernel.py',
    'audit_kernel_survivor': 'work/geometry/audit_kernel_survivor.py',
    'validate_collision_kernel': 'work/phase3/collision/validate_collision_kernel.py',
    'validate_collision_kernel_v2': 'work/phase3/collision/validate_collision_kernel_v2.py',
    'audit_center_cover': 'current/research/optimality/audit/audit_center_cover.py',
    'audit_endpoint_rows': 'current/research/optimality/audit/audit_endpoint_rows.py',
    'verify_trump': 'current/work/construction/verify_trump.py',
    'independent_patch_cover': 'work/phase2/audit/independent_patch_cover.py',
    'independent_weighted_cover': 'work/phase3/audit/independent_weighted_cover.py',
}


def stage(package, family, index):
    need((family, index) in package.groups, 'Invalid certificate selection')
    recipe = package.manifest[family + '_recipes'][index]
    selected = package.common | package.groups[family, index]
    selected |= {package.key(package.records[family, index]['output']), HISTORICAL, MANIFEST}
    selected |= {'research/phase3-fresh-fields/RESULT.json', 'research/phase3-fresh-generic/RESULT.json'}
    if family == 'field':
        checkers = ['work/phase2/audit/audit_wall_mask_chain_v2.py', 'work/phase3/audit/audit_wall_mask_chain_v3.py']
        matches = [x for x in checkers if package.expected['research/phase3/' + x] == recipe['chain_checker_sha256']]
        need(len(matches) == 1, 'Field checker identity is ambiguous')
        checker = matches[0]
        arguments = [str(package.source('research/phase3/' + recipe[k])) for k in ('packet', 'producer_gate', 'fresh_replay')]
    else:
        command = recipe['replay_command']
        need(len(command) == 5 and command[0] == 'python' and command[3:] == ['--output', 'FRESH-OUTPUT.json'], 'Unexpected generic recipe')
        checker = command[1]
        need(checker in ('work/phase3/hull/audit_capture_v4.py', 'work/phase3/hull/audit_capture_v5.py', 'work/phase3/hull/audit_capture_v6.py'), 'Unrecognized generic checker')
        need(command[2] == recipe['source'] and recipe['root_audit_sha256'] is None, 'Unexpected generic root or source')
        arguments = [str(package.source('research/phase3/' + recipe['source']))]
    checker_path = package.source('research/phase3/' + checker)
    selected.add('research/phase3/' + checker)
    package.verify(selected)
    package.guards()
    # Native dependency is loaded before archive paths enter the import search.
    # No Linux binary from the archive is used, and no historical identity is
    # substituted for the actual current binary identity.
    for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    import gmpy2
    need(gmpy2.version() == GMP_VERSION, 'Fresh replay requires native gmpy2 2.3.1')
    native_path = P_RESOLVE(Path(gmpy2.gmpy2.__file__), strict=True)
    native_sha = digest(native_path)
    if family == 'field':
        import numpy
        import sympy
    runtime = set()
    for value in sysconfig.get_paths().values():
        if value:
            p = P_RESOLVE(Path(value))
            if p.name not in ('bin', 'Scripts', 'include') and any(x in ('lib', 'lib64', 'Lib', 'site-packages', 'dist-packages') for x in p.parts):
                runtime.add(p)
    for prefix in (sys.base_prefix, sys.base_exec_prefix, sys.prefix, sys.exec_prefix):
        for suffix in ('lib', 'lib64', 'Lib', 'DLLs'):
            p = Path(prefix) / suffix
            if p.is_dir():
                runtime.add(P_RESOLVE(p))
    runtime.add(native_path.parent)
    archive = package.root / 'research/phase3'
    allowed = {package.source(x) for x in selected}
    allowed |= {package.launcher, package.inventory_path, package.confined(CONSUMER)}
    opened, written, remapped, origins = set(), set(), set(), {}
    sys.dont_write_bytecode = True
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['ELEVEN_RATIONAL_BACKEND'] = 'gmp'
    os.environ['ELEVEN_PACKING_ROOT'] = str(archive / 'current')
    os.chdir(archive)

    def physical(value):
        p = absolute(value)
        if within(p, package.root) or any(within(p, r) for r in runtime):
            return p
        if within(p, package.original):
            q = package.root / p.relative_to(package.original)
            remapped.add((str(p), str(q.relative_to(package.root))))
            return q
        return p

    def proof_reference(value, relative):
        p = Path(value)
        candidates = set()
        if not p.is_absolute():
            candidates.update((archive / p, Path(relative).parent / p))
        else:
            candidates.add(physical(p))
            # Archived Linux paths have variable prefixes. The suffix must be
            # a complete work/... or current/... member AND a declared input.
            # No basename fallback or external filesystem probe is permitted.
            for marker in ('work', 'current'):
                for i, part in enumerate(p.parts):
                    if part == marker:
                        candidates.add(archive / Path(*p.parts[i:]))
        valid = {P_RESOLVE(q) for q in candidates if P_RESOLVE(q) in allowed}
        need(len(valid) == 1, 'Unlisted or ambiguous proof reference: ' + str(value))
        q = next(iter(valid))
        remapped.add((str(value), str(q.relative_to(package.root))))
        return q

    def mapped_resolve(self, strict=False):
        return P_RESOLVE(physical(self), strict=strict)
    def mapped_stat(self, *, follow_symlinks=True):
        return P_STAT(physical(self), follow_symlinks=follow_symlinks)
    def mapped_lstat(self):
        return P_LSTAT(physical(self))
    def mapped_path_open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        return P_OPEN(physical(self), mode, buffering, encoding, errors, newline)
    def mapped_open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        if not isinstance(file, int):
            file = physical(os.fsdecode(file))
        return RAW_OPEN(file, mode, buffering, encoding, errors, newline, closefd, opener)
    def mapped_io_open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        if not isinstance(file, int):
            file = physical(os.fsdecode(file))
        return RAW_IO_OPEN(file, mode, buffering, encoding, errors, newline, closefd, opener)
    Path.resolve, Path.stat, Path.lstat, Path.open = mapped_resolve, mapped_stat, mapped_lstat, mapped_path_open
    builtins.open, io.open = mapped_open, mapped_io_open

    def write_target(value):
        p = P_RESOLVE(absolute(os.fsdecode(value)))
        need(within(p, package.results), 'Write outside result directory refused: ' + str(p))
        return p

    def audit_io(event, values):
        if event == 'open' and values and not isinstance(values[0], int):
            value, mode, flags = values
            if not isinstance(value, (str, bytes, os.PathLike)):
                return
            p = P_RESOLVE(absolute(os.fsdecode(value)))
            writing = any(c in (mode or '') for c in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if writing:
                written.add(str(write_target(p).relative_to(package.root)))
                return
            if within(p, package.results):
                opened.add(str(p.relative_to(package.root)))
                return
            if within(p, package.root):
                if p.suffix == '.pyc':
                    raise FileNotFoundError('Packaged bytecode disabled')
                need(p in allowed, 'Unlisted package proof read: ' + str(p))
                opened.add(str(p.relative_to(package.root)))
                return
            if any(within(p, r) for r in runtime):
                return
            if str(p) in ('/dev/null', '/dev/urandom', '/dev/random'):
                return
            raise PermissionError('Read outside declared package/runtime: ' + str(p))
        if event in ('os.remove', 'os.rmdir', 'os.mkdir') and values:
            write_target(values[0])
        elif event in ('os.rename', 'os.link') and len(values) >= 2:
            write_target(values[0]); write_target(values[1])
        elif event == 'os.symlink':
            raise PermissionError('Replay does not require symlink creation')
    sys.addaudithook(audit_io)

    sources = {name: archive / rel for name, rel in SOURCES.items()}
    sources['baseline_frozen_checker'] = checker_path
    for name in sources:
        sys.modules.pop(name, None)
    class SourceFinder:
        def find_spec(self, fullname, path=None, target=None):
            if fullname not in sources:
                return None
            p = sources[fullname]
            need(p in allowed, 'Module source is outside declared proof group')
            need(digest(p) == package.expected[str(p.relative_to(package.root))], 'Imported checker source changed')
            origins[fullname] = p
            loader = importlib.machinery.SourceFileLoader(fullname, str(p))
            return importlib.util.spec_from_file_location(fullname, p, loader=loader)
    sys.meta_path.insert(0, SourceFinder())
    sys.path[:] = [p for p in sys.path if p and any(within(P_RESOLVE(absolute(p)), r) for r in runtime)]
    import baseline_frozen_checker as checker_module
    if family == 'generic':
        checker_module.locate = proof_reference
    output = package.result_path(family, index)
    sys.argv = [str(checker_path), *arguments, '--output', str(output)]
    # Deliberately no ownership-cache or root-audit: replay every geometric
    # premise afresh. The original checker's mathematical functions are intact.
    checker_module.main()
    fresh = package.read(output)
    compare_receipt(package, family, index, fresh, native_sha)
    for name, p in origins.items():
        need(P_RESOLVE(Path(sys.modules[name].__file__)) == p, 'Loaded module origin differs: ' + name)
        need(digest(p) == package.expected[str(p.relative_to(package.root))], 'Loaded module changed: ' + name)
    for name, module in list(sys.modules.items()):
        origin = getattr(module, '__file__', None)
        if origin and within(P_RESOLVE(absolute(origin)), archive):
            need(name in origins, 'Unpinned proof module was imported: ' + name)
    package.verify(selected)
    package.guards()
    need(digest(native_path) == native_sha and gmpy2.version() == GMP_VERSION, 'Native GMP changed during replay')
    trace = dict(status='PASS_FRESH_BASELINE_CERTIFICATE', family=family, index=index,
        output=str(output.relative_to(package.root)), output_sha256=package.hash(output),
        source=recipe['packet' if family == 'field' else 'source'],
        source_sha256=recipe['packet_sha256' if family == 'field' else 'source_sha256'],
        checker=str(checker_path.relative_to(package.root)), checker_sha256=package.hash(checker_path),
        historical_fresh_audit=package.key(package.records[family, index]['output']),
        historical_fresh_audit_sha256=package.records[family, index]['fresh_sha256'],
        native_gmp_version=GMP_VERSION, native_gmp_binary_sha256=native_sha,
        native_gmp_binary_path=str(native_path), fresh_geometry_replayed=True,
        semantic_comparison='Full recursive equality; only explicit receipt path fields, generic elapsed seconds, and generic actual native binary digest are normalized.',
        selected_source_hashes={k: package.expected[k] for k in sorted(selected)},
        imported_source_hashes={name: dict(path=str(p.relative_to(package.root)), sha256=package.expected[str(p.relative_to(package.root))]) for name, p in sorted(origins.items())},
        opened_package_files=sorted(opened), written_files=sorted(written),
        path_mappings=[dict(original=a, package_relative=b) for a, b in sorted(remapped)],
        **package.provenance())
    package.write(package.trace_path(family, index), trace)
    print(json.dumps(dict(status=trace['status'], family=family, index=index)))


def summary(package):
    package.verify(package.expected)
    overrides = {}
    binaries = set()
    trace_hashes = {}
    for family, count in COUNTS.items():
        for index in range(count):
            trace_path = package.trace_path(family, index)
            trace = package.read(trace_path)
            need(trace['status'] == 'PASS_FRESH_BASELINE_CERTIFICATE' and trace['fresh_geometry_replayed'] is True, 'Missing fresh PASS')
            need(trace['family'] == family and trace['index'] == index, 'Fresh trace case substitution')
            for key, value in package.provenance().items():
                need(trace[key] == value, 'Fresh trace provenance changed: ' + key)
            expected_output = package.result_path(family, index)
            need(trace['output'] == str(expected_output.relative_to(package.root)), 'Fresh output path substituted')
            need(package.hash(expected_output) == trace['output_sha256'], 'Fresh output digest differs')
            need(trace['native_gmp_version'] == GMP_VERSION, 'Fresh GMP version differs')
            need(len(trace['native_gmp_binary_sha256']) == 64, 'Missing native binary identity')
            for path, value in trace['selected_source_hashes'].items():
                need(package.expected.get(path) == value, 'Stage source digest differs')
            recipe = package.manifest[family + '_recipes'][index]
            source_key = 'packet' if family == 'field' else 'source'
            need(trace['source'] == recipe[source_key] and trace['source_sha256'] == recipe[source_key + '_sha256'], 'Fresh trace source substitution')
            if family == 'generic':
                checker = 'research/phase3/' + recipe['replay_command'][1]
            else:
                candidates = ['research/phase3/work/phase2/audit/audit_wall_mask_chain_v2.py',
                              'research/phase3/work/phase3/audit/audit_wall_mask_chain_v3.py']
                matches = [p for p in candidates if package.expected[p] == recipe['chain_checker_sha256']]
                need(len(matches) == 1, 'Ambiguous summary field checker')
                checker = matches[0]
            need(trace['checker'] == checker and trace['checker_sha256'] == package.expected[checker], 'Fresh trace checker substitution')
            required = package.common | package.groups[family, index]
            required |= {package.key(package.records[family, index]['output']), HISTORICAL, MANIFEST,
                         'research/phase3-fresh-fields/RESULT.json', 'research/phase3-fresh-generic/RESULT.json', checker}
            need(required == trace['selected_source_hashes'].keys(), 'Stage source inventory differs')
            imported = trace['imported_source_hashes']
            need('baseline_frozen_checker' in imported, 'Missing actual checker import binding')
            module_sources = {name: 'research/phase3/' + path for name, path in SOURCES.items()}
            module_sources['baseline_frozen_checker'] = checker
            for name, binding in imported.items():
                need(name in module_sources and binding['path'] == module_sources[name], 'Imported module path differs')
                need(binding['sha256'] == package.expected[binding['path']], 'Imported module source differs')
            record = package.records[family, index]
            need(trace['historical_fresh_audit'] == package.key(record['output']) and trace['historical_fresh_audit_sha256'] == record['fresh_sha256'], 'Historical comparison target changed')
            fresh = package.read(expected_output)
            compare_receipt(package, family, index, fresh, trace['native_gmp_binary_sha256'])
            binaries.add(trace['native_gmp_binary_sha256'])
            overrides[family, index] = dict(output=str(expected_output), fresh_sha256=trace['output_sha256'])
            trace_hashes[f'{family}-{index:02d}'] = package.hash(trace_path)
    need(len(overrides) == 93 and len(binaries) == 1, 'All93 stages must use one native GMP identity')
    native_sha = next(iter(binaries))
    computed = package.load_consumer().reconstruct(package.root / 'research', package.read,
        package.hash, GMP_VERSION, native_sha, overrides)
    need(computed['excluded_canonical_mask_indices'] == package.historical['excluded_canonical_mask_indices'], 'Fresh union differs from historical union')
    package.guards()
    result = dict(status='PASS_PORTABLE_FRESH_1931_CASE_BASELINE', fresh_geometry_replayed=True,
        field_certificates=59, generic_certificates=34, excluded=1931, remaining=253,
        excluded_canonical_mask_indices=computed['excluded_canonical_mask_indices'],
        remaining_canonical_mask_indices=computed['remaining_canonical_mask_indices'],
        native_gmp_version=GMP_VERSION, native_gmp_binary_sha256=native_sha,
        fresh_stage_trace_sha256=trace_hashes, verified_source_files=498,
        global_optimality_proved=False, **package.provenance())
    package.write(package.results / 'FRESH_BASELINE_RESULT.json', result)
    print(json.dumps({k: result[k] for k in ('status', 'fresh_geometry_replayed', 'excluded', 'remaining')}))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--package-root', type=Path, required=True)
    ap.add_argument('mode', choices=('reuse', 'field', 'generic', 'all', 'summary'))
    ap.add_argument('--index', type=int)
    args = ap.parse_args()
    package = Package(args.package_root)
    if args.mode in COUNTS:
        need(args.index is not None, 'A single certificate index is required')
        stage(package, args.mode, args.index)
    else:
        need(args.index is None, '--index applies only to field/generic modes')
        if args.mode == 'reuse':
            reuse(package)
        elif args.mode == 'summary':
            summary(package)
        else:
            # Each stage gets a clean import namespace. No parallel workers,
            # hidden cache reuse, automatic resume, or trust in existing traces.
            reuse(package)
            for family, count in COUNTS.items():
                for index in range(count):
                    log = package.results / f'{family}-{index:02d}.log'
                    with RAW_OPEN(log, 'w', encoding='utf-8') as stream:
                        subprocess.run([sys.executable, str(package.launcher), '--package-root',
                            str(package.root), family, '--index', str(index)],
                            stdout=stream, stderr=subprocess.STDOUT, check=True)
            summary(package)


if __name__ == '__main__':
    main()
