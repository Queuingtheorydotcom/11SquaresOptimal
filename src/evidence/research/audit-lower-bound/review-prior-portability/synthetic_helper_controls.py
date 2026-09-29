#!/usr/bin/env python3
"""Exercise only AST-extracted adapter I/O helpers on tiny synthetic files.

No proof consumer is imported/executed, and no proof-data input is read.
The real Python audit mechanism observes the extracted helper calls.
"""
import ast
import builtins
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ADAPTER = HERE.parents[1] / 'finalization/prior-union/replay_portable.py'
OUTPUT = HERE / 'SYNTHETIC_HELPER_CONTROLS.json'
source_bytes = ADAPTER.read_bytes()
source = ast.parse(source_bytes, filename=str(ADAPTER))
main = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
helper_names = {
    'physical', 'checked_physical', 'mapped_resolve', 'mapped_stat',
    'mapped_lstat', 'mapped_path_open', 'mapped_open', 'mapped_io_open',
    'write_target', 'audit_io',
}
helpers = [n for n in source.body if isinstance(n, ast.FunctionDef) and n.name in {'need', 'within', 'absolute'}]
helpers += [n for n in main.body if isinstance(n, ast.FunctionDef) and n.name in helper_names]
assert {n.name for n in helpers} == helper_names | {'need', 'within', 'absolute'}
overlap = [n for n in main.body if isinstance(n, ast.Expr) and any(
    isinstance(c, ast.Constant) and c.value == 'Output directory overlaps immutable proof inputs'
    for c in ast.walk(n))]
assert len(overlap) == 1
helper_code = compile(ast.Module(body=helpers, type_ignores=[]), str(ADAPTER), 'exec')
overlap_code = compile(ast.Module(body=overlap, type_ignores=[]), str(ADAPTER), 'exec')
originals = {name: getattr(Path, name) for name in ('resolve', 'stat', 'lstat', 'open')}
original_open, original_io_open = builtins.open, io.open
controls = []


def check(name, action):
    try:
        detail = action()
    except Exception as error:
        controls.append(dict(name=name, passed=False, exception=type(error).__name__, detail=str(error)))
    else:
        controls.append(dict(name=name, passed=True, detail=detail))


def expect_error(action, kind, fragment):
    try:
        action()
    except kind as error:
        assert fragment in str(error), str(error)
        return dict(rejected_as=type(error).__name__, reason_fragment=fragment)
    raise AssertionError('Expected rejection was not raised')


with tempfile.TemporaryDirectory(prefix='prior-portable-helpers-') as tmp:
    fixture = Path(tmp).resolve()
    historical = fixture / 'historical'
    package = historical / 'relocated-package'
    results = package / 'results/prior-union'
    native = package / '.venv/lib/gmpy2/native.so'
    runtime_external = fixture / 'runtime/lib'
    for directory in (results, package/'research', historical/'research', native.parent, runtime_external):
        directory.mkdir(parents=True, exist_ok=True)
    proof = package/'research/item.json'
    old_proof = historical/'research/item.json'
    missing = package/'research/missing.json'
    old_missing = historical/'research/missing.json'
    unlisted = package/'research/unlisted.json'
    outside = fixture/'outside.json'
    bytecode = package/'research/pinned.pyc'
    sibling = native.with_name('other.so')
    ordinary_runtime = runtime_external/'library.py'
    manifest, launcher = package/'inventory.json', package/'launcher.py'
    for path, payload in {
        proof:'PACKAGE', old_proof:'HISTORICAL-MUST-NOT-BE-READ', old_missing:'HISTORICAL-ONLY',
        unlisted:'UNLISTED', outside:'OUTSIDE', bytecode:'SYNTHETIC-BYTECODE',
        native:'SYNTHETIC-NATIVE', sibling:'SYNTHETIC-SIBLING', ordinary_runtime:'RUNTIME',
        manifest:'MANIFEST', launcher:'LAUNCHER',
    }.items():
        path.write_text(payload)
    results_link = package/'results-link'
    results_link.symlink_to(package/'research', target_is_directory=True)
    ns = dict(Path=Path, os=os, P_OPEN=originals['open'], P_RESOLVE=originals['resolve'],
              P_STAT=originals['stat'], P_LSTAT=originals['lstat'], BUILTIN_OPEN=original_open,
              IO_OPEN=original_io_open, original=historical, package=package, results=results,
              native_binary=native, runtime=[native.parent.parent, runtime_external],
              declared={p:'synthetic' for p in (proof, missing, bytecode, manifest, launcher)},
              logical_to_physical={old_proof:proof, old_missing:missing},
              physical_to_logical={proof:old_proof, missing:old_missing},
              opened=set(), written=set(), remapped=set())
    exec(helper_code, ns)

    def overlap_control(target, rejected):
        saved = ns['results']
        ns['results'] = originals['resolve'](target)
        try:
            if rejected:
                return expect_error(lambda:exec(overlap_code,ns),ValueError,'overlaps immutable proof inputs')
            exec(overlap_code,ns)
            return 'Accepted disjoint results directory'
        finally:
            ns['results'] = saved

    check('output_research_overlap_rejected', lambda:overlap_control(package/'research',True))
    check('resolved_results_symlink_overlap_rejected', lambda:overlap_control(results_link,True))
    check('disjoint_results_directory_accepted', lambda:overlap_control(results,False))

    enabled = [True]
    def audit_dispatch(event, values):
        if enabled[0]:
            ns['audit_io'](event,values)
    sys.addaudithook(audit_dispatch)
    Path.resolve=ns['mapped_resolve']; Path.stat=ns['mapped_stat']; Path.lstat=ns['mapped_lstat']; Path.open=ns['mapped_path_open']
    builtins.open=ns['mapped_open']; io.open=ns['mapped_io_open']
    interfaces = {
        'Path.open':lambda p:Path(p).open('r'),
        'builtins.open':lambda p:builtins.open(p,'r'),
        'io.open':lambda p:io.open(p,'r'),
    }

    def read_with(opener,path):
        with opener(path) as stream:
            return stream.read(),Path(stream.name)

    def check_mapping(opener):
        content,actual=read_with(opener,old_proof)
        assert content=='PACKAGE' and actual==proof
        return 'Historical pathname read the declared relocated file'

    def check_payload(path,payload):
        content,_=read_with(interfaces['builtins.open'],path)
        assert content==payload
        return 'Read expected synthetic bytes'

    def write(path):
        with builtins.open(path,'w') as stream:stream.write('RESULT')

    try:
        for name,opener in interfaces.items():
            check(name+'_historical_mapping',lambda opener=opener:check_mapping(opener))
            check(name+'_missing_package_no_historical_fallback',lambda opener=opener:expect_error(
                lambda:read_with(opener,old_missing),FileNotFoundError,'missing.json'))
        check('mapped_resolve_preserves_root_identity',lambda: (
            ns['need'](historical.resolve()==package,'Root did not relocate'), 'Root resolves to package')[1])
        check('mapped_stat_does_not_fall_back',lambda:expect_error(
            lambda:old_missing.stat(),FileNotFoundError,'missing.json'))
        check('unlisted_package_read_rejected',lambda:expect_error(
            lambda:check_payload(unlisted,'UNLISTED'),ValueError,'Unlisted package proof read refused'))
        check('outside_read_rejected',lambda:expect_error(
            lambda:check_payload(outside,'OUTSIDE'),PermissionError,'Read outside package/runtime refused'))
        check('packaged_bytecode_rejected_even_if_declared',lambda:expect_error(
            lambda:check_payload(bytecode,'SYNTHETIC-BYTECODE'),FileNotFoundError,'Packaged bytecode disabled'))
        check('exact_native_runtime_binary_accepted',lambda:check_payload(native,'SYNTHETIC-NATIVE'))
        check('native_runtime_sibling_inside_package_rejected',lambda:expect_error(
            lambda:check_payload(sibling,'SYNTHETIC-SIBLING'),ValueError,'Unlisted package proof read refused'))
        check('ordinary_external_runtime_read_accepted',lambda:check_payload(ordinary_runtime,'RUNTIME'))
        check('native_binary_write_rejected',lambda:expect_error(
            lambda:write(native),ValueError,'Write outside this replay result directory refused'))
        check('declared_proof_write_rejected',lambda:expect_error(
            lambda:write(proof),ValueError,'Write outside this replay result directory refused'))
        check('results_write_accepted',lambda:(write(results/'result.json'),check_payload(results/'result.json','RESULT'))[1])
        check('outside_results_mkdir_rejected',lambda:expect_error(
            lambda:os.mkdir(package/'unexpected-directory'),ValueError,'Write outside this replay result directory refused'))
        check('proof_content_preserved',lambda:check_payload(proof,'PACKAGE'))
    finally:
        enabled[0]=False
        for name,original in originals.items():setattr(Path,name,original)
        builtins.open=original_open;io.open=original_io_open

    trace=dict(package_files_opened=sorted(ns['opened']),files_written=sorted(ns['written']),
               historical_references_remapped=len(ns['remapped']))

result=dict(status='PASS_SYNTHETIC_ADAPTER_IO_CONTROLS' if all(c['passed'] for c in controls) else 'FAIL_SYNTHETIC_ADAPTER_IO_CONTROLS',
            adapter_path=str(ADAPTER),adapter_sha256=hashlib.sha256(source_bytes).hexdigest(),
            extraction='AST selected exact function definitions and the exact output-overlap guard; adapter module/main were not imported or executed',
            audit_mechanism='Actual sys.addaudithook events with the extracted audit_io function enabled during synthetic I/O',
            controls=controls,total=len(controls),passed=sum(c['passed'] for c in controls),
            synthetic_trace=trace,proof_consumers_imported=False,proof_validation_performed=False,
            geometric_replay_performed=False,large_input_hashing_performed=False)
OUTPUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','adapter_sha256','total','passed')}))
if result['passed']!=result['total']:raise SystemExit(1)
