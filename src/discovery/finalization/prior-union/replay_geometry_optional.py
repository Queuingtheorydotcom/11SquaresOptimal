#!/usr/bin/env python3
"""Optional fresh replay of all 76 prior extensions; no historical node caches.

Use --stage all for a sequential complete run, or one named stage/mask.
Frozen mathematical checker files and input receipts are never edited.
"""
if not __debug__:
    raise SystemExit('Assertions must be enabled; optimized Python is refused.')
import argparse,builtins,contextlib,hashlib,importlib.machinery,importlib.util,io,json,os,subprocess,sys,sysconfig,time
from pathlib import Path

MANIFEST='research/finalization/prior-union/SOURCE_INVENTORY.json'
MANIFEST_HASH='bec43e9ea5d9f3e3dbfdad6a07bf58190ba8edaac815732266a3201b1386b800'
PINS='research/audit-lower-bound/strict-inventory-pins.json'
PINS_HASH='8a46589d35e3bbd1efce02b2a196db5ddb636a85259bf7f30d6b31daa65b01f8'
V9_HASH='95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c'
TREE_TARGET='research/endpoint-audit/mask1383-two-branch-tree.json'
GEOMETRY='research/global-math/overlay-geometry-independent-replay.json'
SUPPORT='research/global-math/all-overlay-support-253/independent-replay.json'
HULLS='research/global-math/all-overlay-support-253/supported-center-hulls.json'
P_OPEN=Path.open;P_RESOLVE=Path.resolve;P_STAT=Path.stat;P_LSTAT=Path.lstat
RAW_OPEN=builtins.open;RAW_IO_OPEN=io.open
NODE_KEYS=('sha256','node','complete_steps','rows','arrangement_slabs','promoted_grid_vertices','constraints','branch_exclusion_proved','inside_local_guard')
COMMON=('status','root_sha256','root_audit_sha256','mask_index','mask','required_antecedent_mask','parent_Uplus','parent_side','cover_sha256','transferred_canonical_mask_indices','continuum_canonical_masks_excluded','mask_exclusion_proved','global_optimality_proved')

def need(test,message):
    if not test:raise ValueError(message)
def inside(p,r):
    try:p.relative_to(r);return True
    except ValueError:return False
def absolute(p):return Path(os.path.abspath(os.fspath(p)))
def raw_sha(p):
    h=hashlib.sha256()
    with RAW_OPEN(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,r):Path(p).write_text(json.dumps(r,indent=2)+'\n')
def same_keys(a,b,keys):
    for k in keys:need(a[k]==b[k],'Fresh mathematical field differs: '+k)

class Package:
    def __init__(self,base):
        self.base=P_RESOLVE(base,strict=True);self.result=self.base/'results/prior-geometry'
        self.result.mkdir(parents=True,exist_ok=True);self.result=P_RESOLVE(self.result,strict=True)
        need(inside(self.result,self.base),'Results escape package')
        m=P_RESOLVE(self.base/MANIFEST,strict=True);need(inside(m,self.base),'Manifest escapes package')
        need(raw_sha(m)==MANIFEST_HASH,'Source inventory changed')
        self.inventory=read(m);self.original=Path(self.inventory['original_workspace'])
        self.declared={};self.checked={};self.checking=set();self.reads=set();self.writes=set();self.origins={};self.redirect={}
        for item in self.inventory['files']:
            rel=Path(item['target']);need(not rel.is_absolute() and '..' not in rel.parts,'Unsafe target')
            p=P_RESOLVE(self.base/rel);need(inside(p,self.base) and not inside(p,self.result),'Unsafe input/result overlap')
            need(p not in self.declared and Path(item['source'])==self.original/rel,'Ambiguous address mapping')
            self.declared[p]=item['expected_sha256']
        self.launcher=P_RESOLVE(Path(__file__));need(inside(self.launcher,self.base),'Use packaged launcher')
        self.launcher_hash=raw_sha(self.launcher);self.declared[self.launcher]=self.launcher_hash;self.declared[P_RESOLVE(m)]=MANIFEST_HASH
        import gmpy2
        need(gmpy2.version()=='2.3.1','Use gmpy2 version2.3.1')
        self.native=P_RESOLVE(Path(gmpy2.gmpy2.__file__));self.native_hash=raw_sha(self.native)
        self.runtime=set()
        for value in sysconfig.get_paths().values():
            if value:
                p=P_RESOLVE(Path(value))
                if p.name not in ('bin','Scripts','include') and any(s in ('lib','lib64','Lib','site-packages','dist-packages') for s in p.parts):self.runtime.add(p)
        for prefix in (sys.base_prefix,sys.base_exec_prefix,sys.prefix,sys.exec_prefix):
            for suffix in ('lib','lib64','Lib','DLLs'):
                p=Path(prefix)/suffix
                if p.is_dir():self.runtime.add(P_RESOLVE(p))
        self.runtime.add(self.native.parent)
        os.chdir(self.base);sys.dont_write_bytecode=True
        os.environ['ELEVEN_RATIONAL_BACKEND']='gmp';os.environ['ELEVEN_PACKING_ROOT']=str(self.base/'research/phase3/current')
        for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
        self.install_io()
        need(self.hash_input(self.base/PINS)==PINS_HASH,'Dependency pins changed')
        pins=self.frozen(self.base/PINS)
        self.expected={k:v for k,v in pins.items() if k not in ('audit_cached_node_v2.py','audit_tree_batch_v3.py')}
        sources={k[:-3]:self.base/'research/phase3'/v['path'] for k,v in self.expected.items()}
        sources.update(audit_tree_batch_v4=self.base/'research/phase3/work/phase3/hull/audit_tree_batch_v4.py',audit_overlay_exclusion=self.base/'research/frontier/audit_overlay_exclusion.py',overlay_field_halfplanes_v2=self.base/'research/global-math/overlay_field_halfplanes_v2.py')
        self.sources=sources
        for k in sources:sys.modules.pop(k,None)
        owner=self
        class Finder:
            def find_spec(self,fullname,path=None,target=None):
                if fullname not in sources:return None
                p=sources[fullname];owner.hash_input(p);owner.origins[fullname]=p
                return importlib.util.spec_from_file_location(fullname,p,loader=importlib.machinery.SourceFileLoader(fullname,str(p)))
        sys.meta_path.insert(0,Finder())
        sys.path[:]=[p for p in sys.path if p and any(inside(P_RESOLVE(absolute(p)),r) for r in self.runtime)]
    def mapped(self,path):
        p=absolute(path)
        if inside(p,self.base):return p
        if any(inside(p,r) for r in self.runtime):return p
        if inside(p,self.original):return self.base/p.relative_to(self.original)
        return p
    def input(self,ref,owner=None):
        p=Path(ref);candidates=[]
        if p.is_absolute():candidates.append(self.mapped(p))
        else:
            candidates.extend([self.base/p,self.base/'research/phase3'/p])
            if owner is not None:candidates.append(Path(owner).parent/p)
        # Retained archive references identify work/current directories. This
        # suffix rule still requires membership in the exact pinned inventory.
        for marker in ('work','current'):
            if marker in p.parts and p.parts.count(marker)==1:candidates.append(self.base/'research/phase3'/Path(*p.parts[p.parts.index(marker):]))
        found={P_RESOLVE(q) for q in candidates if P_RESOLVE(q) in self.declared}
        need(len(found)==1,'Missing/ambiguous declared reference: '+str(ref));q=found.pop();self.hash_input(q);return q
    def hash_input(self,p):
        p=P_RESOLVE(p);need(p in self.declared,'Undeclared input: '+str(p))
        if p not in self.checked:
            self.checking.add(p)
            try:h=raw_sha(p)
            finally:self.checking.remove(p)
            need(h==self.declared[p],'Input hash differs: '+str(p));self.checked[p]=h
        return self.checked[p]
    def frozen(self,p):
        p=self.input(p)
        # RAW_OPEN deliberately bypasses derived-output redirects, but remains
        # inside the audit hook and exact immutable-input allowlist.
        with RAW_OPEN(p) as f:return json.load(f)
    def install_io(self):
        owner=self
        def address(p):
            q=owner.mapped(p);return owner.redirect.get(q,q)
        def resolve(p,strict=False):return P_RESOLVE(address(p),strict=strict)
        def stat(p,*,follow_symlinks=True):return P_STAT(address(p),follow_symlinks=follow_symlinks)
        def lstat(p):return P_LSTAT(address(p))
        def popen(p,mode='r',buffering=-1,encoding=None,errors=None,newline=None):return P_OPEN(address(p),mode,buffering,encoding,errors,newline)
        def bopen(file,*args,**kwargs):return RAW_OPEN(file if isinstance(file,int) else address(os.fsdecode(file)),*args,**kwargs)
        def iopen(file,*args,**kwargs):return RAW_IO_OPEN(file if isinstance(file,int) else address(os.fsdecode(file)),*args,**kwargs)
        Path.resolve=resolve;Path.stat=stat;Path.lstat=lstat;Path.open=popen;builtins.open=bopen;io.open=iopen
        def writable(p):
            p=P_RESOLVE(absolute(os.fsdecode(p)));need(inside(p,owner.result),'Write outside fresh results refused');owner.writes.add(str(p.relative_to(owner.base)))
        def audit(event,args):
            if event=='open' and args and not isinstance(args[0],int):
                p,mode,flags=args;p=P_RESOLVE(absolute(os.fsdecode(p)))
                writing=any(c in (mode or '') for c in 'wax+') or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
                if writing:writable(p);return
                if inside(p,owner.result):owner.reads.add(str(p.relative_to(owner.base)));return
                if p==owner.native:return
                if inside(p,owner.base):
                    if p.suffix=='.pyc':raise FileNotFoundError('Packaged bytecode disabled')
                    need(p in owner.declared,'Unlisted package proof read refused: '+str(p))
                    if p not in owner.checking:owner.hash_input(p)
                    owner.reads.add(str(p.relative_to(owner.base)));return
                if any(inside(p,r) for r in owner.runtime):return
                if str(p) in ('/dev/null','/dev/random','/dev/urandom'):return
                raise PermissionError('External proof read refused: '+str(p))
            if event in ('os.mkdir','os.remove','os.rmdir') and args:writable(args[0])
            elif event in ('os.rename','os.link') and len(args)>=2:writable(args[0]);writable(args[1])
            elif event=='os.symlink':raise PermissionError('Symlink creation refused')
        sys.addaudithook(audit)
    def checker(self):
        import audit_capture_v9 as a
        need(self.hash_input(Path(a.__file__))==V9_HASH,'Wrong geometry checker')
        a.locate=self.input
        return a
    def dependencies(self):
        for name,pin in self.expected.items():
            module=sys.modules.get(name[:-3]);p=self.base/'research/phase3'/pin['path']
            need(module is not None and P_RESOLVE(Path(module.__file__))==p,'Actual imported dependency differs: '+name)
            need(self.hash_input(p)==pin['sha256'],'Imported source bytes differ')
    def source_rows(self,value):
        return {k:dict(v,path=str(self.input(v['path']).relative_to(self.base))) for k,v in value.items()}
    def compare_nodes(self,new,old):
        need(len(new)==len(old),'Ancestry inventory length differs')
        for n,o in zip(new,old):
            same_keys(n,o,NODE_KEYS);need(self.input(n['path'])==self.input(o['path']),'Ancestry path differs')
            need('cached_from_audit_sha256' not in n,'Historical node cache was imported')
    def finish(self,key,record,outputs):
        for p,h in list(self.checked.items()):need(raw_sha(p)==h,'Input changed during fresh replay')
        record.update(adapter_sha256=self.launcher_hash,source_inventory_sha256=MANIFEST_HASH,
            outputs={str(p.relative_to(self.base)):raw_sha(p) for p in outputs},
            input_bindings={str(p.relative_to(self.base)):h for p,h in self.checked.items()},
            proof_module_origins={k:str(v.relative_to(self.base)) for k,v in self.origins.items()},
            current_native_binary_sha256=self.native_hash,imported_historical_node_caches=False,
            mathematical_checker_sources_modified=False,global_optimality_proved=False)
        write(self.result/(key+'-verified.json'),record);print(json.dumps({k:v for k,v in record.items() if k not in ('outputs','input_bindings','proof_module_origins')},indent=2))
    def fresh_parent(self,key,target):
        r=read(self.result/(key+'-verified.json'));need(r['adapter_sha256']==self.launcher_hash and r['source_inventory_sha256']==MANIFEST_HASH,'Fresh parent adapter/input binding differs')
        p=self.result/target;need(r['outputs'][str(p.relative_to(self.base))]==raw_sha(p),'Fresh parent output differs');return p

def geometry_case(p,mask):
    start=time.monotonic();entry=next((e for e in p.inventory['entries'] if e['mask_index']==mask),None);need(entry is not None,'Mask not in frozen76')
    old=p.frozen(p.base/entry['audit_target']);need(p.hash_input(p.base/entry['audit_target'])==entry['audit_sha256'],'Selected receipt changed')
    a=p.checker();out=p.result/f'mask{mask}-fresh-audit.json';log=p.result/f'mask{mask}-replay.log'
    if entry['kind']=='native_cached_v4_center_partition':
        import audit_tree_batch_v4 as tree
        sys.argv=[str(tree.__file__),str(p.input(TREE_TARGET)),'--generic','--output',str(out)]
        with log.open('w') as f,contextlib.redirect_stdout(f):tree.main()
        fresh=read(out);same_keys(fresh,old,COMMON+('tree_sha256','checked_leaves','closed_leaves_in_snapshot','unresolved_leaf_ids','generic_mode','complete','mask_reduced_to_local_guard'))
        need(fresh['premise_audits']==[] and fresh['rows_in_cached_premises']==0,'Historical tree cache imported')
        need(fresh['rows_replayed_this_run']==sum(n['rows'] for n in old['nodes'])==36600,'Incomplete fresh tree row inventory')
    else:
        saved=old
        if entry['kind']=='necessary_D4_cuts_and_independent_geometry':saved=p.frozen(p.input(old['geometric_audit']))
        source=p.input(saved['nodes'][-1]['path']);sys.argv=[str(a.__file__),str(source),'--output',str(out)]
        with log.open('w') as f,contextlib.redirect_stdout(f):a.main()
        fresh=read(out);same_keys(fresh,saved,COMMON+('source_sha256','constraints','final_state_sha256','bootstrap','seed_ownership_checks','branch_exclusion_proved','inside_local_guard'))
        old_nodes=saved['nodes']
        need(not fresh.get('premise_audits'),'Historical generic cache imported')
        if mask==1839:need(sum(n['rows'] for n in fresh['nodes'])==20207,'Incomplete1839 ancestry')
        old_for_nodes=saved
    p.dependencies();expected={k:v['sha256'] for k,v in p.expected.items()}
    need(fresh['rational_backend']=='gmp' and fresh['rational_backend_version']=='2.3.1' and
         fresh['rational_binary_sha256']==p.native_hash,'Fresh native arithmetic binding differs')
    if mask==1383:expected['audit_tree_batch_v4.py']=p.hash_input(p.sources['audit_tree_batch_v4'])
    need(fresh['dependencies']==expected,'Fresh dependency inventory differs')
    p.compare_nodes(fresh['nodes'],old['nodes'] if mask==1383 else old_for_nodes['nodes'])
    need(fresh['global_optimality_proved'] is False and fresh['root_audit_sha256'] is None,'Unsupported root/scope')
    outputs=[out]
    if entry['kind']=='necessary_D4_cuts_and_independent_geometry':
        p.redirect[p.base/GEOMETRY]=p.fresh_parent('overlay-geometry','overlay-geometry-fresh.json')
        p.redirect[p.base/SUPPORT]=p.fresh_parent('overlay-support','overlay-support-fresh.json')
        p.redirect[p.base/HULLS]=p.fresh_parent('overlay-support','overlay-hulls-fresh.json')
        import audit_overlay_exclusion as discharge
        actual=discharge.validate(source,out)
        changed={'source','geometric_audit','geometric_audit_sha256','source_hulls_sha256','support_replay_sha256','geometry_replay_sha256','checked_ancestry'}
        same_keys(actual,old,set(old)-changed)
        need(set(actual)==set(old),'Overlay output schema differs')
        need(p.input(actual['source'])==p.input(old['source']),'Overlay source differs')
        need(actual['geometric_audit_sha256']==raw_sha(out),'Fresh geometry binding differs')
        for key,target in [('source_hulls_sha256',HULLS),('support_replay_sha256',SUPPORT),('geometry_replay_sha256',GEOMETRY)]:need(actual[key]==raw_sha(p.redirect[p.base/target]),'Fresh overlay premise binding differs')
        need(len(actual['checked_ancestry'])==len(old['checked_ancestry']),'Overlay ancestry length differs')
        for n,o in zip(actual['checked_ancestry'],old['checked_ancestry']):need(n['sha256']==o['sha256'] and p.input(n['path'])==p.input(o['path']),'Overlay ancestry differs')
        derived=p.result/f'mask{mask}-fresh-discharge.json';write(derived,actual);outputs.append(derived)
    else:need(fresh['mask_exclusion_proved'] is True and fresh['transferred_canonical_mask_indices']==[mask],'Case not excluded')
    p.finish(f'mask{mask}',dict(status='PASS_FRESH_PRIOR_EXTENSION_GEOMETRY',mask_index=mask,profile=entry['kind'],saved_audit_sha256=entry['audit_sha256'],rows_replayed=sum(n['rows'] for n in fresh['nodes']),seconds=time.monotonic()-start),outputs)

def overlay_stage(p,stage):
    start=time.monotonic();is_geometry=stage=='overlay-geometry'
    script=p.base/'research/global-math'/('audit_overlay_geometry.py' if is_geometry else 'audit_all_overlay_support.py')
    old=p.frozen(p.base/(GEOMETRY if is_geometry else SUPPORT))
    geo=p.result/'overlay-geometry-fresh.json';support=p.result/'overlay-support-fresh.json';hulls=p.result/'overlay-hulls-fresh.json'
    if is_geometry:p.redirect[p.base/GEOMETRY]=geo
    else:
        p.redirect[p.base/GEOMETRY]=p.fresh_parent('overlay-geometry',geo.name)
        p.redirect[p.base/SUPPORT]=support;p.redirect[p.base/HULLS]=hulls
    p.hash_input(script)
    spec=importlib.util.spec_from_file_location('fresh_'+stage.replace('-','_'),script);module=importlib.util.module_from_spec(spec)
    with (p.result/(stage+'-replay.log')).open('w') as f,contextlib.redirect_stdout(f):spec.loader.exec_module(module)
    new=read(geo if is_geometry else support)
    need(set(new)==set(old),'Overlay premise schema differs');same_keys(new,old,set(old)-{'seconds','sources'})
    need(p.source_rows(new['sources'])==p.source_rows(old['sources']),'Overlay premise sources differ')
    outputs=[geo] if is_geometry else [support,hulls]
    if not is_geometry:
        got=read(hulls);wanted=p.frozen(p.base/HULLS)
        need(set(got)==set(wanted),'Supported hull schema differs');same_keys(got,wanted,set(wanted)-{'parent_independent_replay_sha256','parent_geometry_replay_sha256'})
        need(got['parent_independent_replay_sha256']==raw_sha(support) and got['parent_geometry_replay_sha256']==raw_sha(geo),'Fresh supported hull parent differs')
    p.finish(stage,dict(status='PASS_FRESH_'+stage.upper().replace('-','_'),seconds=time.monotonic()-start),outputs)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--package-root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--stage',choices=['case','overlay-geometry','overlay-support','all'],required=True);ap.add_argument('--mask',type=int);args=ap.parse_args()
    base=P_RESOLVE(args.package_root,strict=True)
    if args.stage=='all':
        need(args.mask is None,'--mask applies only to case stage');manifest=base/MANIFEST;need(raw_sha(manifest)==MANIFEST_HASH,'Source inventory changed');inventory=read(manifest)
        stages=[('overlay-geometry',None),('overlay-support',None)]+[('case',e['mask_index']) for e in inventory['entries']]
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
        records={};start=time.monotonic()
        for stage,mask in stages:
            cmd=[sys.executable,'-B',str(P_RESOLVE(Path(__file__))),'--package-root',str(base),'--stage',stage]
            if mask is not None:cmd+=['--mask',str(mask)]
            subprocess.run(cmd,check=True,env=env)
            name=f'mask{mask}' if mask is not None else stage;path=base/'results/prior-geometry'/(name+'-verified.json');r=read(path)
            need(r['adapter_sha256']==raw_sha(__file__) and r['source_inventory_sha256']==MANIFEST_HASH,'Child binding differs');records[name]=dict(path=str(path.relative_to(base)),sha256=raw_sha(path))
        write(base/'results/prior-geometry/SUMMARY.json',dict(status='PASS_ALL_76_FRESH_PRIOR_EXTENSION_GEOMETRY',extension_cases=76,overlay_premise_stages=2,children=records,adapter_sha256=raw_sha(__file__),source_inventory_sha256=MANIFEST_HASH,imported_historical_node_caches=False,seconds=time.monotonic()-start,baseline1931_replayed_in_this_stage=False,global_optimality_proved=False));return
    p=Package(base)
    if args.stage=='case':need(args.mask is not None,'case stage requires --mask');geometry_case(p,args.mask)
    else:need(args.mask is None,'--mask applies only to case stage');overlay_stage(p,args.stage)

if __name__=='__main__':main()
