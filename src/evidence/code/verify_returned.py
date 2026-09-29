"""Independently replay returned case traces, serially, from compressed inputs.

Only the frozen v9 checker executes mathematical proof rules. This adapter
extracts a single case, checks every byte hash, confines historical references
to that case's supplied objects, and records portable archive identities.
"""
from pathlib import Path, PurePosixPath
from fractions import Fraction
import argparse
import contextlib
import hashlib
import importlib
import json
import os
import sys
import tempfile
import time
import zipfile
import gmpy2

if not __debug__:
    raise SystemExit('Optimized Python is not a proof replay.')

BASE=Path(__file__).resolve().parents[1]
PH=BASE/'research/phase3'
RESULTS=BASE/'results/returned'
U=Fraction(387708359002281417731,10**20)
V9='95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c'
COVER_HASH='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
PINS_HASH='8a46589d35e3bbd1efce02b2a196db5ddb636a85259bf7f30d6b31daa65b01f8'
PLAN_HASH='ba2ba3eae20ffa7b88bbc8e97928a073d7c084d1976211fa16e5e6338860fcc1'
ASSIGNMENT_HASH='03d6e82a9bde1bad6cf6683081cff2b583d7f60fddb2c810c91e071cb4575864'

def need(test,message):
    if not test:raise ValueError(message)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

ADAPTER_AT_START=sha(__file__)

def source_identity():
    need(sha(__file__)==ADAPTER_AT_START,'Replay adapter changed while executing')
    return ADAPTER_AT_START

def read(path):return json.loads(Path(path).read_text())

def confined(name):
    path=(BASE/name).resolve()
    need(path.is_relative_to(BASE),'Path escapes verification directory')
    return path

def write(path,data):
    temporary=path.with_suffix('.writing')
    temporary.write_text(json.dumps(data,indent=2)+'\n')
    temporary.replace(path)

def load_checker():
    pins_path=BASE/'code/v9-dependency-pins.json'
    need(sha(pins_path)==PINS_HASH,'Dependency pin inventory changed')
    pins=read(pins_path)
    excluded={'audit_cached_node_v2.py','audit_tree_batch_v3.py'}
    expected={name:entry for name,entry in pins.items() if name not in excluded}
    for name,pin in expected.items():
        need(sha(PH/pin['path'])==pin['sha256'],'Changed reviewed checker dependency: '+name)
    os.environ['ELEVEN_RATIONAL_BACKEND']='gmp'
    os.environ['ELEVEN_PACKING_ROOT']=str(PH/'current')
    sys.path[:0]=[str(PH/'work/phase3/hull'),str(PH/'work/phase2/hull')]
    checker=importlib.import_module('audit_capture_v9')
    need(sha(checker.__file__)==V9,'Unexpected checker module')
    helper=importlib.import_module('audit_residual_kernel')
    need(Path(helper.__file__).resolve()==(PH/'work/phase3/hull/audit_residual_kernel.py').resolve(),
         'An unrecorded alternate residual helper was imported')
    for name,module in [('arrangement_audit_v2.py',checker.geo),('rational.py',checker.rational),
                        ('validate_collision_kernel_v3.py',checker.collision),
                        ('own_hull_constraints.py',checker.self_hull),('audit_residual_kernel.py',helper)]:
        need(sha(module.__file__)==expected[name]['sha256'],'Actual imported dependency differs: '+name)
    return checker,expected

def actual_dependencies(expected):
    for name,pin in expected.items():
        module=sys.modules.get(name.removesuffix('.py'))
        need(module is not None,'Required dependency was not imported: '+name)
        need(Path(module.__file__).resolve()==(PH/pin['path']).resolve() and
             sha(module.__file__)==pin['sha256'],'Actual imported dependency differs: '+name)

def transport_inventory(case):
    return [dict(member=i['member'],sha256=i['expected_sha256'],bytes=i['bytes'],
                 role=i['role'],basename=i['destination_name']) for i in case['stream_extract_members']]

def validate_fresh(fresh,case,dependencies,canonical,old):
    m=case['mask_index']
    required=('status','source_sha256','root_sha256','mask_index','mask','parent_Uplus',
              'parent_side','cover_sha256','constraints','final_state_sha256','bootstrap',
              'seed_ownership_checks','branch_exclusion_proved','mask_exclusion_proved',
              'required_antecedent_mask','transferred_canonical_mask_indices',
              'continuum_canonical_masks_excluded')
    for key in required:need(fresh[key]==old[key],'Fresh replay differs from submitted result: '+key)
    need(fresh['mask_index']==m and fresh['mask']==canonical[m] and
         fresh['required_antecedent_mask']==canonical[m],'Fresh result has wrong case')
    need(fresh['source_sha256']==case['source_sha256'] and fresh['root_sha256']==case['root_sha256'],
         'Fresh result has wrong proof sources')
    need(fresh['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT' and
         fresh['mask_exclusion_proved'] is True and fresh['branch_exclusion_proved'] is True,
         'The independent checker did not prove this case')
    need(fresh['constraints']==[] and fresh['global_optimality_proved'] is False,'Wrong proof scope')
    need(Fraction(fresh['parent_Uplus'])==U and
         Fraction(fresh['parent_side'])==Fraction(191,50)/U and fresh['cover_sha256']==COVER_HASH,
         'Wrong cap, scale, or cover')
    need(fresh['transferred_canonical_mask_indices']==[m] and fresh['continuum_canonical_masks_excluded']==1,
         'Unexpected support transfer')
    need(fresh['dependencies']=={k:v['sha256'] for k,v in dependencies.items()},'Incomplete dependency inventory')
    need(len(fresh['nodes'])==len(old['nodes']),'Different ancestry length')
    node_keys=('sha256','node','complete_steps','rows','arrangement_slabs','promoted_grid_vertices',
               'constraints','branch_exclusion_proved','inside_local_guard')
    for current,previous in zip(fresh['nodes'],old['nodes']):
        for key in node_keys:need(current[key]==previous[key],'Node replay differs: '+key)

def validate_checkpoint(case,dependencies,canonical):
    m=case['mask_index'];path=RESULTS/f'mask{m}-verified.json';done=read(path)
    exact=dict(status='PASS_FRESH_INDEPENDENT_RETURNED_CASE',mask_index=m,job_id=case['job_id'],
               occupied_cells=canonical[m],parent_Uplus=str(U),source_sha256=case['source_sha256'],
               root_sha256=case['root_sha256'],submitted_audit_sha256=case['saved_audit_sha256'],
               fresh_audit=f'results/returned/mask{m}-fresh-audit.json',archive=case['archive'],
               proof_objects=transport_inventory(case),checker_sha256=V9,adapter_sha256=source_identity(),
               dependencies={k:v['sha256'] for k,v in dependencies.items()},plan_sha256=PLAN_HASH,
               assignment_sha256=ASSIGNMENT_HASH,mask_exclusion_proved=True,global_optimality_proved=False,
               actual_residual_helper='research/phase3/work/phase3/hull/audit_residual_kernel.py')
    for key,value in exact.items():need(done[key]==value,'Invalid checkpoint binding: '+key)
    audit=confined(done['fresh_audit'])
    need(sha(audit)==done['fresh_audit_sha256'],'Fresh audit changed or missing')
    with zipfile.ZipFile(confined(case['archive'])) as z:
        raw=z.read(case['saved_audit_member'])
    need(hashlib.sha256(raw).hexdigest()==case['saved_audit_sha256'],'Submitted receipt changed')
    validate_fresh(read(audit),case,dependencies,canonical,json.loads(raw))
    return done

def safe_member(name):
    p=PurePosixPath(name)
    need(not p.is_absolute() and '..' not in p.parts,'Unsafe archive member')
    return p

def extract(z,entry,directory):
    member=entry['member'];safe_member(member)
    name=entry['destination_name']
    need(name==Path(name).name and name not in ('','.','..'),'Unsafe extraction filename')
    info=z.getinfo(member)
    need(not info.is_dir() and info.file_size==entry['bytes'],'Input size mismatch')
    need((info.external_attr>>16)&0o170000!=0o120000,'Archive symlink is not a proof object')
    target=directory/name;need(not target.exists(),'Duplicate extraction name')
    h=hashlib.sha256()
    with z.open(info) as source,target.open('wb') as dest:
        while chunk:=source.read(1<<20):
            h.update(chunk);dest.write(chunk)
    need(h.hexdigest()==entry['expected_sha256'],'Proof source bytes differ: '+member)
    return target

def check_case(case,archive,checker,dependencies,canonical):
    m=case['mask_index'];start=time.monotonic()
    need(type(m) is int and 0<=m<2184,'Invalid case index')
    out=RESULTS/f'mask{m}-fresh-audit.json'
    log=RESULTS/f'mask{m}-replay.log'
    transport=[]
    with zipfile.ZipFile(archive) as z,tempfile.TemporaryDirectory(prefix=f'mask{m}-',dir=BASE/'.work') as tmp:
        names=z.namelist();need(len(names)==len(set(names)),'Ambiguous duplicate ZIP members')
        directory=Path(tmp);allowed={}
        for item in case['stream_extract_members']:
            path=extract(z,item,directory)
            need(path.name not in allowed,'Ambiguous historical basename')
            allowed[path.name]=path
            transport.append(dict(member=item['member'],sha256=item['expected_sha256'],
                                  bytes=item['bytes'],role=item['role'],basename=path.name))
        source=allowed[PurePosixPath(case['source_member']).name]
        saved=allowed[PurePosixPath(case['saved_audit_member']).name]
        old=read(saved)
        need(sha(source)==case['source_sha256'] and sha(saved)==case['saved_audit_sha256'],'Final input binding failed')
        need(old['root_sha256']==case['root_sha256'],'Seed binding failed')
        need(old['mask_index']==m and old['mask']==canonical[m],'Wrong case or occupied cells')
        need(old['constraints']==[] and old['mask_exclusion_proved'] is True,'Returned case is conditional or unproved')
        need(Fraction(old['parent_Uplus'])==U and old['cover_sha256']==COVER_HASH,'Wrong rational container or cover')
        # Every resolver target is a hash-checked member of this single case.
        # The checker rechecks parent/seed hashes at each mathematical use.
        def locate(path,relative):
            name=PurePosixPath(str(path)).name
            need(name in allowed,'Reference outside supplied proof ancestry: '+str(path))
            return allowed[name].resolve()
        old_locate=checker.locate;old_argv=sys.argv[:]
        checker.locate=locate
        try:
            sys.argv=[str(checker.__file__),str(source),'--output',str(out)]
            with log.open('w') as stream,contextlib.redirect_stdout(stream):checker.main()
        finally:
            checker.locate=old_locate;sys.argv=old_argv
        fresh=read(out)
        actual_dependencies(dependencies)
        validate_fresh(fresh,case,dependencies,canonical,old)
        for item in transport:need(sha(allowed[item['basename']])==item['sha256'],'Input changed during replay')
    record=dict(status='PASS_FRESH_INDEPENDENT_RETURNED_CASE',mask_index=m,job_id=case['job_id'],
                occupied_cells=canonical[m],parent_Uplus=str(U),source_sha256=case['source_sha256'],
                submitted_audit_sha256=case['saved_audit_sha256'],fresh_audit=str(out.relative_to(BASE)),
                fresh_audit_sha256=sha(out),archive=str(archive.relative_to(BASE)),proof_objects=transport,
                checker_sha256=V9,adapter_sha256=source_identity(),dependencies=fresh['dependencies'],
                root_sha256=case['root_sha256'],plan_sha256=PLAN_HASH,assignment_sha256=ASSIGNMENT_HASH,
                actual_residual_helper='research/phase3/work/phase3/hull/audit_residual_kernel.py',
                mask_exclusion_proved=True,global_optimality_proved=False,seconds=time.monotonic()-start)
    write(RESULTS/f'mask{m}-verified.json',record)
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mask',type=int,action='append')
    p.add_argument('--resume',action='store_true')
    a=p.parse_args()
    RESULTS.mkdir(parents=True,exist_ok=True);(BASE/'.work').mkdir(exist_ok=True)
    need(sha(BASE/'inputs/CASE_ASSIGNMENTS.json')==ASSIGNMENT_HASH,'Frozen assignments changed')
    need(sha(BASE/'inputs/returned-replay-plan.json')==PLAN_HASH,'Frozen replay plan changed')
    assignment=read(BASE/'inputs/CASE_ASSIGNMENTS.json')
    required={m for j in assignment['jobs'] for m in j['mask_indices']}
    need(len(required)==173 and not required.intersection({438,999,1462,1659}),'Incomplete case assignment')
    plans=read(BASE/'inputs/returned-replay-plan.json')
    cases=plans['cases'];indices=[c['mask_index'] for c in cases]
    need(len(indices)==len(set(indices))==173 and set(indices)==required,'Replay plan does not cover exact assignments')
    for c in cases:
        job=next(j for j in assignment['jobs'] if j['job_id']==c['job_id'])
        need(c['mask_index'] in job['mask_indices'],'Case attached to wrong job')
    chosen=set(a.mask) if a.mask else required
    need(chosen and chosen<=required,'Empty or unassigned case selection')
    checker,dependencies=load_checker()
    cover=PH/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
    need(sha(cover)==COVER_HASH,'Cover bytes differ')
    canonical=read(cover)['canonical_eleven_cell_subsets']
    for c in cases:
        m=c['mask_index']
        if m not in chosen:continue
        destination=RESULTS/f'mask{m}-verified.json'
        if a.resume and destination.exists():
            validate_checkpoint(c,dependencies,canonical)
            print(json.dumps({'mask_index':m,'status':'REUSED_UNCHANGED_FRESH_REPLAY'}),flush=True)
            continue
        archive=confined(c['archive']);need(archive.is_file(),'Missing archive')
        print(json.dumps({'mask_index':m,'status':'REPLAY_START'}),flush=True)
        record=check_case(c,archive,checker,dependencies,canonical)
        print(json.dumps({k:record[k] for k in ('mask_index','status','seconds')}),flush=True)
    completed=[]
    for case in cases:
        m=case['mask_index']
        path=RESULTS/f'mask{m}-verified.json'
        if path.exists():
            validate_checkpoint(case,dependencies,canonical)
            completed.append(m)
    summary=dict(status='PASS_ALL_173_RETURNED_CASES' if len(completed)==173 else 'PARTIAL_FRESH_RETURNED_REPLAY',
                 completed_cases=completed,completed=len(completed),required=173,
                 unresolved_cases=sorted(required-set(completed)),checker_sha256=V9,
                 adapter_sha256=source_identity(),plan_sha256=PLAN_HASH,
                 assignment_sha256=ASSIGNMENT_HASH,global_optimality_proved=False)
    write(RESULTS/'SUMMARY.json',summary)
    print(json.dumps({'status':summary['status'],'completed':len(completed),'required':173}),flush=True)

if __name__=='__main__':main()
