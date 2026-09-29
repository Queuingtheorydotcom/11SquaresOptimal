#!/usr/bin/env python3
"""Relocate only addresses for the source-frozen 76-case prior integration.

Proof bytes are immutable. Every proof read is confined to a declared package
file; ordinary interpreter/GMP library reads are separate runtime dependencies.
This performs inventory/composition checks, not new v9 geometric replay.
"""
if not __debug__:
    raise SystemExit('Assertions must remain enabled; -O/-OO is refused.')

import argparse,builtins,hashlib,importlib.machinery,importlib.util,io,json,os,sys,sysconfig
from pathlib import Path

INVENTORY_TARGET='research/finalization/prior-union/SOURCE_INVENTORY.json'
INVENTORY_SHA='bec43e9ea5d9f3e3dbfdad6a07bf58190ba8edaac815732266a3201b1386b800'
INTEGRATOR_TARGET='research/finalization/prior-union/integrate_prior_union.py'
INTEGRATOR_SHA='89f602362f6d129e2a539af1d971cb8ca6361a0cc4cb03c802616c6db67fa0bc'
GENERIC_SHA='7df54d904bb5d0cc609a4765eeafc3fb57922bcb3a4b210082df9fda36266530'
TREE_SHA='b6a298ccfa1a27911b3e88c832f890a983e0c6e7c374455808e42eb730626059'
HISTORICAL_GMP_VERSION='2.3.1'
HISTORICAL_GMP_SHA='4fdf5fbaea9d3c4f756f9f656d0d7656fc4a66c82a8e921f326e570702dc463d'
P_OPEN=Path.open
P_RESOLVE=Path.resolve
P_STAT=Path.stat
P_LSTAT=Path.lstat
BUILTIN_OPEN=builtins.open
IO_OPEN=io.open


def need(value,message):
    if not value:raise ValueError(message)


def within(path,root):
    try:path.relative_to(root);return True
    except ValueError:return False


def absolute(path):return Path(os.path.abspath(os.fspath(path)))


def raw_sha(path):
    h=hashlib.sha256()
    with BUILTIN_OPEN(path,'rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--package-root',type=Path,required=True)
    ap.add_argument('--output-relative',default='results/prior-union')
    args=ap.parse_args()
    package=P_RESOLVE(args.package_root,strict=True)
    need(package.is_dir(),'Missing package root')
    output_relative=Path(args.output_relative)
    need(not output_relative.is_absolute() and '..' not in output_relative.parts,'Unsafe output-relative path')
    results=P_RESOLVE(package/output_relative)
    need(within(results,package) and results!=package,'Results must stay in a package subdirectory')
    results.mkdir(parents=True,exist_ok=True)
    results=P_RESOLVE(results,strict=True)
    need(within(results,package),'Results escape package through symlink')
    manifest_path=P_RESOLVE(package/INVENTORY_TARGET,strict=True)
    need(within(manifest_path,package),'Inventory escapes package through symlink')
    need(raw_sha(manifest_path)==INVENTORY_SHA,'Prepared inventory changed')
    with BUILTIN_OPEN(manifest_path) as f:inventory=json.load(f)
    original=Path(inventory['original_workspace'])
    need(original.is_absolute(),'Historical logical workspace is not absolute')
    need(inventory['schema']=='eleven_square_prior_union_package_inventory_v1','Wrong inventory schema')
    need(inventory['expected_extension_receipts']==76,'Wrong prior receipt count')
    launcher=P_RESOLVE(Path(__file__),strict=True)
    need(within(launcher,package),'Use the packaged launcher, not an external copy')
    launcher_sha=raw_sha(launcher)
    declared={};logical_to_physical={};physical_to_logical={}
    for item in inventory['files']:
        rel=Path(item['target'])
        need(not rel.is_absolute() and '..' not in rel.parts,'Unsafe declared target')
        physical=P_RESOLVE(package/rel)
        need(within(physical,package),'Declared target escapes package')
        logical=absolute(item['source'])
        need(within(logical,original),'Declared logical source is outside historical workspace')
        need(logical==original/rel,'Logical source and portable target differ')
        need(physical not in declared and logical not in logical_to_physical,'Duplicate source identity')
        declared[physical]=item['expected_sha256']
        logical_to_physical[logical]=physical
        physical_to_logical[physical]=logical
    declared[manifest_path]=INVENTORY_SHA
    declared[launcher]=launcher_sha
    need(not any(within(p,results) for p in declared),
         'Output directory overlaps immutable proof inputs')
    need(declared.get(package/INTEGRATOR_TARGET)==INTEGRATOR_SHA,'Integration source pin differs')
    for rel,h in [('research/audit-lower-bound/strict_generic_inventory.py',GENERIC_SHA),('research/audit-lower-bound/strict_tree_inventory.py',TREE_SHA)]:
        need(declared.get(package/rel)==h,'Strict source pin differs')

    # Load ordinary numerical runtime before restricting proof imports. Its
    # binary remains an explicit external runtime dependency, not proof data.
    import gmpy2
    need(gmpy2.version()==HISTORICAL_GMP_VERSION,'Native gmpy2 2.3.1 is required')
    native_binary=P_RESOLVE(Path(gmpy2.gmpy2.__file__),strict=True)
    native_sha=raw_sha(native_binary)
    runtime=set()
    for value in sysconfig.get_paths().values():
        if value:
            p=P_RESOLVE(Path(value))
            if p.name not in ('bin','Scripts','include') and any(x in ('lib','lib64','Lib','site-packages','dist-packages') for x in p.parts):runtime.add(p)
    for prefix in (sys.base_prefix,sys.base_exec_prefix,sys.prefix,sys.exec_prefix):
        for suffix in ('lib','lib64','Lib','DLLs'):
            p=Path(prefix)/suffix
            if p.is_dir():runtime.add(P_RESOLVE(p))
    runtime.add(native_binary.parent)
    runtime=sorted(runtime,key=str)
    os.chdir(package)
    sys.dont_write_bytecode=True
    for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    opened=set();written=set();remapped=set();origins={};hashed_code={}

    def physical(path):
        p=absolute(path)
        if within(p,package):return p
        # An external venv may be inside the historical workspace. Runtime
        # exceptions permit ordinary library reads, never proof-source imports.
        if any(within(p,r) for r in runtime):return p
        if p in logical_to_physical:
            q=logical_to_physical[p];remapped.add((str(p),str(q)));return q
        if within(p,original):
            # Map directory identities and comparisons too, but an eventual
            # file open still requires membership in the exact declared map.
            q=package/p.relative_to(original);remapped.add((str(p),str(q)));return q
        return p

    def checked_physical(path):
        q=P_RESOLVE(physical(path))
        need(within(q,package),'Proof reference escapes package: '+str(path))
        need(q in declared,'Unlisted proof reference: '+str(path))
        return q

    def mapped_resolve(self,strict=False):return P_RESOLVE(physical(self),strict=strict)
    def mapped_stat(self,*,follow_symlinks=True):return P_STAT(physical(self),follow_symlinks=follow_symlinks)
    def mapped_lstat(self):return P_LSTAT(physical(self))
    def mapped_path_open(self,mode='r',buffering=-1,encoding=None,errors=None,newline=None):
        return P_OPEN(physical(self),mode,buffering,encoding,errors,newline)
    def mapped_open(file,mode='r',buffering=-1,encoding=None,errors=None,newline=None,closefd=True,opener=None):
        if not isinstance(file,int):file=physical(os.fsdecode(file))
        return BUILTIN_OPEN(file,mode,buffering,encoding,errors,newline,closefd,opener)
    def mapped_io_open(file,mode='r',buffering=-1,encoding=None,errors=None,newline=None,closefd=True,opener=None):
        if not isinstance(file,int):file=physical(os.fsdecode(file))
        return IO_OPEN(file,mode,buffering,encoding,errors,newline,closefd,opener)
    # Only this dedicated process is adapted. The original-workspace runner
    # remains unchanged and continues to refuse relocation when run directly.
    Path.resolve=mapped_resolve;Path.stat=mapped_stat;Path.lstat=mapped_lstat;Path.open=mapped_path_open
    builtins.open=mapped_open;io.open=mapped_io_open

    def write_target(path):
        p=P_RESOLVE(absolute(os.fsdecode(path)))
        need(within(p,results),'Write outside this replay result directory refused: '+str(p))
        return p

    def audit_io(event,values):
        if event=='open' and values and not isinstance(values[0],int):
            path,mode,flags=values
            if not isinstance(path,(str,bytes,os.PathLike)):return
            p=P_RESOLVE(absolute(os.fsdecode(path)))
            writing=any(c in (mode or '') for c in 'wax+') or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if writing:
                p=write_target(p);written.add(str(p.relative_to(package)));return
            if within(p,results):opened.add(str(p.relative_to(package)));return
            # A venv may live inside the package. This one already loaded and
            # independently recorded native binary is a runtime dependency,
            # not an exemption for other files under its containing directory.
            if p==native_binary:return
            if within(p,package):
                if p.suffix=='.pyc':raise FileNotFoundError('Packaged bytecode disabled; use pinned source')
                need(p in declared,'Unlisted package proof read refused: '+str(p))
                opened.add(str(p.relative_to(package)));return
            if any(within(p,r) for r in runtime):return
            if str(p) in ('/dev/null','/dev/urandom','/dev/random'):return
            raise PermissionError('Read outside package/runtime refused: '+str(p))
        if event in ('os.remove','os.rmdir','os.mkdir') and values:
            write_target(values[0])
        elif event in ('os.rename','os.link') and len(values)>=2:
            write_target(values[0]);write_target(values[1])
        elif event=='os.symlink':raise PermissionError('Symlink creation is not needed by the proof consumer')
    sys.addaudithook(audit_io)

    sources={
        'strict_generic_inventory':'research/audit-lower-bound/strict_generic_inventory.py',
        'strict_tree_inventory':'research/audit-lower-bound/strict_tree_inventory.py',
        'audit_overlay_exclusion':'research/frontier/audit_overlay_exclusion.py',
        'overlay_field_halfplanes_v2':'research/global-math/overlay_field_halfplanes_v2.py',
        'prior_integration_frozen':INTEGRATOR_TARGET,
    }
    for name in sources:sys.modules.pop(name,None)
    class SourceFinder:
        def find_spec(self,fullname,path=None,target=None):
            if fullname not in sources:return None
            p=checked_physical(package/sources[fullname])
            need(raw_sha(p)==declared[p],'Imported source hash differs: '+fullname)
            origins[fullname]=p;hashed_code[fullname]=declared[p]
            loader=importlib.machinery.SourceFileLoader(fullname,str(p))
            return importlib.util.spec_from_file_location(fullname,p,loader=loader)
    sys.meta_path.insert(0,SourceFinder())
    # No current-directory or historical-workspace import fallback.
    sys.path[:]=[p for p in sys.path if p and any(within(P_RESOLVE(absolute(p)),r) for r in runtime)]
    import strict_generic_inventory as generic
    OriginalValidator=generic.Validator
    class HistoricalReceiptValidator(OriginalValidator):
        def __init__(self):
            super().__init__()
            need(self.native_version==HISTORICAL_GMP_VERSION,'Loaded native runtime version changed')
            # These are immutable historical receipts; this inventory-only
            # process does not claim they were produced by today's binary.
            self.native_version=HISTORICAL_GMP_VERSION
            self.native_hash=HISTORICAL_GMP_SHA
    generic.Validator=HistoricalReceiptValidator
    import audit_overlay_exclusion as overlay
    original_overlay_validate=overlay.validate

    def logical_identity(value):
        p=checked_physical(value)
        need(p in physical_to_logical,'Output path has no historical logical identity')
        return str(physical_to_logical[p])

    def portable_overlay_validate(*args,**kwargs):
        answer=original_overlay_validate(*args,**kwargs)
        # Only explicit path fields change representation. This restores their
        # original logical identities so the unchanged full-receipt equality
        # comparison retains every mathematical/hash/status obligation.
        answer['source']=logical_identity(answer['source'])
        answer['geometric_audit']=logical_identity(answer['geometric_audit'])
        for row in answer['checked_ancestry']:row['path']=logical_identity(row['path'])
        return answer
    overlay.validate=portable_overlay_validate
    import prior_integration_frozen as consumer
    sys.argv=[str(package/INTEGRATOR_TARGET),'--workspace',str(package),
              '--inventory',str(manifest_path),'--inventory-sha256',INVENTORY_SHA,
              '--output-dir',str(results)]
    consumer.main()
    output=results/'PRIOR_UNION_RESULT.json'
    need(output.is_file(),'Strict consumer did not produce the declared result')
    for name,p in origins.items():
        module=sys.modules.get(name)
        need(module is not None and checked_physical(module.__file__)==p,'Imported module origin differs: '+name)
    trace=dict(status='PASS_PACKAGE_ONLY_PRIOR_INTEGRATION',launcher_sha256=launcher_sha,
        integration_checker_sha256=INTEGRATOR_SHA,source_inventory_sha256=INVENTORY_SHA,
        output=str(output.relative_to(package)),output_sha256=raw_sha(output),
        package_proof_files_read=sorted(opened),files_written=sorted(written),
        historical_paths_remapped=sorted(remapped),
        proof_module_origins={k:str(v.relative_to(package)) for k,v in origins.items()},
        proof_module_source_sha256=hashed_code,ordinary_runtime_read_roots=list(map(str,runtime)),
        historical_backend=dict(version=HISTORICAL_GMP_VERSION,binary_sha256=HISTORICAL_GMP_SHA),
        current_inventory_runtime=dict(version=gmpy2.version(),binary_sha256=native_sha),
        historical_receipt_bytes_changed=False,geometric_replay_performed=False,
        source_bytecode_disabled=True,outside_package_proof_fallback=False,
        adapter_changes=['Explicit historical-root/path mapping through declared package targets',
                         'Historical backend provenance checked independently of current runtime binary',
                         'Only three overlay output path-field locations restored to original logical identities'],
        io_trace_scope='Python open and filesystem-mutation audit events after setup; ordinary runtime libraries are allowed. This is not an operating-system sandbox.',
        global_optimality_proved=False)
    (results/'PORTABLE_PRIOR_IO_TRACE.json').write_text(json.dumps(trace,indent=2)+'\n')
    print(json.dumps(dict(status=trace['status'],result=str(output),trace=str(results/'PORTABLE_PRIOR_IO_TRACE.json'))))


if __name__=='__main__':main()
