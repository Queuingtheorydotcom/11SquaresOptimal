#!/usr/bin/env python3
"""Replay immutable eleven-square candidate evidence from a relocated package.

Only paths, output destinations, and interpreter setup are adapted. Frozen
checker/data bytes and arithmetic are unchanged. Run one stage per process.
This launcher does not impose an operating-system CPU quota.
"""
from pathlib import Path
import argparse, dataclasses, hashlib, importlib.machinery, importlib.util, json, os, sys, sysconfig, types

if not __debug__:
    raise SystemExit('Assertions must remain enabled; -O and -OO are unsupported.')

ORIGINAL_WORKSPACE_PREFIX='/workspace/eleven-square'
ORIGINAL_WORKSPACE=Path(ORIGINAL_WORKSPACE_PREFIX)
STAGES=('composition','focused','feature-bridge','local-algebra','local-baseline','local-weighted',
        'construction','cover','consumer-tests','root-geometry',
        'far15-geometry','far13-geometry','far2-geometry','near-geometry')
P_OPEN=Path.open
P_RESOLVE=Path.resolve
P_STAT=Path.stat
P_LSTAT=Path.lstat

def inside(path,root):
    try:path.relative_to(root);return True
    except ValueError:return False

def absolute(path):
    return Path(os.path.abspath(os.fspath(path)))

def need(test,message):
    if not test:raise ValueError(message)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('stage',choices=STAGES)
    ap.add_argument('--package-root',type=Path,default=Path(__file__).resolve().parents[1])
    args=ap.parse_args()
    package=P_RESOLVE(args.package_root,strict=True)
    need((package/'research/candidate-capture').is_dir(),'Missing packaged candidate sources')
    results=package/'results/candidate-replay';results.mkdir(parents=True,exist_ok=True)
    results=P_RESOLVE(results,strict=True)
    need(inside(results,package),'Results directory escapes package through symlink')
    output=results/(args.stage+'.json')
    launcher_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    os.chdir(package)
    sys.dont_write_bytecode=True
    for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[name]='1'
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    os.environ['ELEVEN_PACKING_ROOT']=str(package/'research/phase3/current')
    # Fraction replay is platform-independent. Historical GMP bytes are read
    # only as provenance by the unchanged composition; they are never loaded.
    os.environ['ELEVEN_RATIONAL_BACKEND']='fraction'

    runtime=set()
    for p in sysconfig.get_paths().values():
        if p:runtime.add(P_RESOLVE(Path(p)))
    # Restrict these to actual library directories, not an entire workspace.
    runtime={p for p in runtime if p.name not in ('bin','Scripts','include') and
             any(part in ('lib','lib64','Lib','site-packages','dist-packages') for part in p.parts)}
    for prefix in (sys.base_prefix,sys.base_exec_prefix,sys.prefix,sys.exec_prefix):
        for suffix in ('lib','lib64','Lib','DLLs'):
            p=Path(prefix)/suffix
            if p.is_dir():runtime.add(P_RESOLVE(p))
    runtime=sorted(runtime,key=str)
    redirects={}
    opened=set();remapped=set();written=set()

    def relocate(path):
        p=absolute(path)
        # The final package can itself be a child of the historical workspace.
        if inside(p,package):return p
        if any(inside(p,r) for r in runtime):return p
        # Archive path strings are POSIX, including when the replay host is
        # Windows. Match before a drive is supplied by host absolute().
        raw=os.fsdecode(os.fspath(path)).replace('\\','/')
        if raw==ORIGINAL_WORKSPACE_PREFIX or raw.startswith(ORIGINAL_WORKSPACE_PREFIX+'/'):
            suffix=raw[len(ORIGINAL_WORKSPACE_PREFIX):].lstrip('/')
            q=package/Path(*suffix.split('/')) if suffix else package
            remapped.add((raw,str(q)))
            return q
        if inside(p,ORIGINAL_WORKSPACE):
            q=package/p.relative_to(ORIGINAL_WORKSPACE)
            remapped.add((str(p),str(q)))
            return q
        return p

    def proof_path(path):
        p=P_RESOLVE(relocate(path))
        need(inside(p,package),'Proof reference escapes package: '+str(path))
        return p

    def resolve(self,strict=False):return P_RESOLVE(relocate(self),strict=strict)
    def stat(self,*,follow_symlinks=True):return P_STAT(relocate(self),follow_symlinks=follow_symlinks)
    def lstat(self):return P_LSTAT(relocate(self))
    def path_open(self,mode='r',buffering=-1,encoding=None,errors=None,newline=None):
        p=relocate(self)
        if any(c in mode for c in 'wax+'):
            p=redirects.get(str(p),p)
        return P_OPEN(p,mode,buffering,encoding,errors,newline)
    Path.resolve=resolve;Path.stat=stat;Path.lstat=lstat;Path.open=path_open

    def audit_io(event,values):
        if event!='open' or not values or isinstance(values[0],int):return
        path,mode,flags=values
        if not isinstance(path,(str,bytes,os.PathLike)):return
        p=P_RESOLVE(absolute(os.fsdecode(path)))
        write=any(c in (mode or '') for c in 'wax+') or bool(flags &
            (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if write:
            need(inside(p,results),'Write outside packaged replay results refused: '+str(p))
            written.add(str(p.relative_to(package)));return
        if inside(p,package):
            if p.suffix=='.pyc':
                # SourceFileLoader catches this and falls back to the .py file.
                raise FileNotFoundError('Packaged bytecode is disabled; verify source bytes')
            opened.add(str(p.relative_to(package)));return
        if any(inside(p,r) for r in runtime):return
        if str(p) in ('/dev/null','/dev/urandom','/dev/random'):return
        raise PermissionError('Read outside package/runtime refused: '+str(p))
    sys.addaudithook(audit_io)

    flat_sources={
      'rational':'research/phase3/work/phase3/hull/rational.py',
      'arrangement_audit':'research/phase3/work/phase3/hull/arrangement_audit.py',
      'arrangement_audit_v2':'research/phase3/work/phase3/hull/arrangement_audit_v2.py',
      'audit_residual_kernel':'research/phase3/work/phase3/hull/audit_residual_kernel.py',
      'audit_wall_kernel':'research/phase3/work/geometry/audit_wall_kernel.py',
      'audit_kernel_survivor':'research/phase3/work/geometry/audit_kernel_survivor.py',
      'validate_collision_kernel_v3':'research/phase3/work/phase3/collision/validate_collision_kernel_v3.py',
      'own_hull_constraints':'research/phase3/work/phase3/hull/own_hull_constraints.py',
      'audit_center_cover':'research/phase3/current/research/optimality/audit/audit_center_cover.py'}
    algebra=package/'research/recovered-checkpoint/research/jlevy/packing'
    namespaces={'cases':algebra/'cases','cases.trump11':algebra/'cases/trump11',
                'sqpack':algebra/'src/sqpack'}
    # A caller must not smuggle already imported historical proof modules in.
    for name in list(sys.modules):
        if name in flat_sources or name in namespaces or name.startswith(('cases.','sqpack.')):
            del sys.modules[name]
    # Pin namespaces: an installed regular package must not override a local
    # namespace package merely because it occurs later on sys.path.
    for name,directory in namespaces.items():
        directory=proof_path(directory)
        module=types.ModuleType(name);module.__path__=[str(directory)];module.__package__=name
        module.__spec__=importlib.machinery.ModuleSpec(name,loader=None,is_package=True)
        module.__spec__.submodule_search_locations=[str(directory)]
        sys.modules[name]=module
        if '.' in name:setattr(sys.modules[name.rsplit('.',1)[0]],name.rsplit('.',1)[1],module)
    expected_origins={}
    class ProofSourceFinder:
        def find_spec(self,fullname,path=None,target=None):
            if fullname in flat_sources:
                source=package/flat_sources[fullname]
            elif fullname.startswith('cases.'):
                source=algebra/Path(*fullname.split('.')).with_suffix('.py')
            elif fullname.startswith('sqpack.'):
                source=algebra/'src'/Path(*fullname.split('.')).with_suffix('.py')
            else:return None
            source=proof_path(source)
            need(source.is_file(),'Missing declared proof source module: '+fullname)
            expected_origins[fullname]=source
            loader=importlib.machinery.SourceFileLoader(fullname,str(source))
            return importlib.util.spec_from_file_location(fullname,source,loader=loader)
    sys.meta_path.insert(0,ProofSourceFinder())
    sys.path[:]=[str(package/'code')]+[p for p in sys.path if p and
        any(inside(P_RESOLVE(absolute(p)),r) for r in runtime)]

    def check_origins():
        for name,expected in expected_origins.items():
            module=sys.modules.get(name)
            need(module is not None and getattr(module,'__file__',None) is not None,
                 'Missing imported proof module identity: '+name)
            need(proof_path(module.__file__)==expected,'Imported proof source mismatch: '+name)

    def load(relative,name):
        path=proof_path(package/relative)
        need(path.is_file(),'Missing packaged checker '+relative)
        sys.path.insert(0,str(path.parent))
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        spec.loader.exec_module(module)
        check_origins()
        return module

    def invoke(relative,arguments,name='immutable_checker',configure=None):
        path=proof_path(package/relative)
        sys.argv=[str(path),*map(str,arguments)]
        module=load(relative,name)
        if configure:configure(module)
        need(hasattr(module,'main'),'Expected explicit checker main function')
        module.main()
        return module

    def redirect(relative,target=output):redirects[str(package/relative)]=target
    cp='research/candidate-capture/'
    old='research/recovered-checkpoint/'
    comparison=None
    if args.stage=='composition':
        invoke(cp+'audit_complete_capture438.py',['--output',output])
    elif args.stage=='focused':
        invoke('research/global-math/audit_focused_local_box.py',
               [package/(cp+'focused1024-local-certificate.json'),'--output',output])
    elif args.stage=='feature-bridge':
        redirect('research/endpoint-audit/focused-feature-bridge-review.json')
        invoke('research/endpoint-audit/check_focused_feature_bridge.py',[])
    elif args.stage in ('local-algebra','local-baseline','local-weighted'):
        choices={
          'local-algebra':('research/classical/replay_trump_local.py','research/classical/trump-local-independent-replay.json'),
          'local-baseline':('work/continuation/audit_local_radius.py','work/continuation/local-radius-independent-audit.json'),
          'local-weighted':('work/continuation/audit_weighted_coordinate_radius.py','work/continuation/weighted-coordinate-radius-independent-audit.json')}
        source,destination=choices[args.stage];redirect(old+destination)
        invoke(old+source,[])
    elif args.stage=='cover':
        redirect('research/local-radius/fresh-center-cover-verification.json')
        load('research/local-radius/replay_center_cover.py','immutable_cover_wrapper')
    elif args.stage=='consumer-tests':
        destination=results/'consumer-tests';destination.mkdir(exist_ok=True)
        module=invoke('research/global-math/test_complete_capture438.py',[],
                      configure=lambda m:setattr(m,'OUT',destination))
        result=json.loads((destination/'review.json').read_text())
        output.write_text(json.dumps(result,indent=2)+'\n')
    elif args.stage=='construction':
        source=package/(old+'research/jlevy/packing')
        sys.path[:0]=[str(source),str(source/'src')]
        from cases.trump11 import packing
        from sqpack.verify import verify_packing,exact_sign
        from fractions import Fraction
        squares,T,field=packing.build()
        report=verify_packing(squares,T,sign=exact_sign,check_shapes=True,bucket=False)
        need(report.valid and report.n==11 and report.pairs_tested==55,'Exact construction failed')
        need(packing.side_satisfies_published_polynomial(T,field),'Wrong side polynomial')
        U=Fraction(387708359002281417731,10**20)
        need(exact_sign(field.rational(U)-T)>0,'Exact side is not below rational cap')
        contacts=[]
        for k in (0,1):
            for v,wall in ((field.zero,'lower'),(T,'upper')):
                corners=[(i,j) for i,S in enumerate(squares) for j,p in enumerate(S) if (p[k]-v).is_zero()]
                need(corners,'Missing exact opposite-wall contact')
                contacts.append({'axis':k,'wall':wall,'corners':corners})
        output.write_text(json.dumps({'status':'PASS_EXACT_CONSTRUCTION_AND_SIDE_CAP',
            'report':dataclasses.asdict(report),'side_polynomial_checked':True,
            'T_strictly_below_U':True,'opposite_wall_contacts':contacts,
            'global_optimality_proved':False},indent=2)+'\n')
    elif args.stage=='root-geometry':
        invoke('research/phase3/work/phase3/hull/audit_residual_kernel_v2.py',[
            package/'research/phase3/work/phase2/conditional/mask438-adaptive.json',
            '--seed',package/'research/phase3/work/phase2/conditional/mask438-seed.json',
            '--output',output])
        expected=package/(cp+'root14-independent-audit.json')
        fields=['status','source_sha256','seed_sha256','cover_sha256','mask_index',
                'unconditional_seed_points_checked','derived_owned_points','angle_rows_checked',
                'exact_arrangement_slabs','excluded_angle_rows_across_rounds','cells']
        comparison=(expected,fields)
    else:
        root_audit=results/'root-geometry.json'
        need(root_audit.is_file(),'Run root-geometry before portable branch replays')
        names={
          'far15-geometry':('far15y-self-300.json','far15y-independent-audit.json'),
          'far13-geometry':('far13-collision-180.json','far13-independent-audit.json'),
          'far2-geometry':('tree438-facet/r110.json','far2-independent-audit.json'),
          'near-geometry':('near-refined1024-240.json','near1024-independent-audit.json')}
        node,reference=names[args.stage]
        def strict_locate(module):
            def locate(path,relative):
                # Explicit historical-root relocation only: no basename search
                # or broad 'work' suffix fallback is used by this package run.
                p=proof_path(path)
                need(p.is_file(),'Missing declared packaged proof reference: '+str(path))
                return p
            module.locate=locate
        invoke(cp+'audit_capture_portable.py',[package/(cp+node),'--root-audit',root_audit,
            '--output',output],configure=strict_locate)
        fields=['status','source_sha256','root_sha256','mask_index','mask','parent_Uplus',
                'parent_side','cover_sha256','constraints','final_state_sha256',
                'branch_exclusion_proved','inside_local_guard','mask_exclusion_proved']
        comparison=(package/(cp+reference),fields)

    if comparison:
        expected,fields=comparison
        fresh=json.loads(output.read_text());prior=json.loads(expected.read_text())
        for field in fields:need(fresh[field]==prior[field],'Portable geometry differs at '+field)
        comparison={'historical_receipt':str(expected.relative_to(package)),
                    'compared_mathematical_fields':fields,'all_equal':True,
                    'note':'Backend identity, timings, parent-audit hashes and cache inventories may differ; source bytes and final mathematical conclusions agree.'}
    need(output.is_file(),'Checker did not produce its declared result')
    check_origins()
    trace={'status':'PASS_PACKAGE_ONLY_REPLAY','stage':args.stage,
           'launcher_sha256':launcher_sha,'output':str(output.relative_to(package)),
           'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
           'package_proof_files_read':sorted(opened),'historical_paths_remapped':sorted(remapped),
           'files_written':sorted(written),'ordinary_runtime_read_roots':list(map(str,runtime)),
           'proof_module_origins':{k:str(v.relative_to(package)) for k,v in expected_origins.items()},
           'source_bytecode_disabled':True,'historical_evidence_modified':False,
           'io_trace_scope':'Python open audit events after launcher setup; this is not an operating-system sandbox. Consumer -O/-OO controls run in child interpreters that refuse before proof input reads.',
           'geometry_result_comparison':comparison,'global_optimality_proved':False}
    (results/(args.stage+'-io.json')).write_text(json.dumps(trace,indent=2)+'\n')
    print(json.dumps({'stage':args.stage,'result':str(output),'trace':str(results/(args.stage+'-io.json'))}))

if __name__=='__main__':main()
