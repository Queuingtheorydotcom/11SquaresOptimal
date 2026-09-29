"""Read bounded ZIP metadata and small JSON/source members; never execute them."""
from pathlib import Path, PurePosixPath
from collections import Counter
import zipfile,json,io,hashlib
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
ASSIGN=ROOT/'relay-handoff/CASE_ASSIGNMENTS.json'
assign=json.loads(ASSIGN.read_text());jobs={j['job_id']:j for j in assign['jobs']}
pins=json.loads((ROOT/'audit-lower-bound/strict-inventory-pins.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
U='387708359002281417731/100000000000000000000'
COVER='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
BASE_DEPS=set(pins)-{'audit_cached_node_v2.py','audit_tree_batch_v3.py'}
LIMIT=200000
allrows=[];packets=[];containers=[]
for pair in ['01-to-02','03-to-04']:
 archive=Path('/home/researcher/Downloads')/f'eleven-square-cases-{pair}-verified.zip'
 with zipfile.ZipFile(archive) as z:
  members={e.filename:e for e in z.infolist()}
  duplicates=[n for n,c in Counter(e.filename for e in z.infolist()).items() if c>1]
  unsafe=[n for n in members if PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts]
  def small(n):
   assert members[n].file_size<=LIMIT,(n,'not small')
   return z.read(n)
  sums={}
  for line in small('SHA256SUMS').decode().splitlines():
   h,n=line.split('  ',1);assert n not in sums;sums[n]=h
  top_assignment=small('CASE_ASSIGNMENTS.json')
  containers.append(dict(path=str(archive),archive_bytes=archive.stat().st_size,members=len(members),duplicate_names=duplicates,unsafe_names=unsafe,top_manifest_members=len(sums),top_manifest_unlisted=sorted(set(members)-set(sums)-{'SHA256SUMS'}),top_manifest_missing=sorted(set(sums)-set(members)),assignments_match_frozen_bytes=top_assignment==ASSIGN.read_bytes(),assignments_sha256=sha(top_assignment)))
  for number in ([1,2] if pair=='01-to-02' else [3,4]):
   job_id=f'cases-{number:02d}';prefix=job_id+'-result/';result_bytes=small(prefix+'result.json');result=json.loads(result_bytes);job=jobs[job_id]
   checks=[]
   def check(c,label):checks.append(dict(check=label,passed=bool(c)))
   check(result['job_id']==job_id,'job_id');check(result['status']=='complete','complete_claim');check(result['global_optimality_proved'] is False,'no_global_claim');check(result['parent_Uplus']==U,'exact_U');check(result['assigned_mask_indices']==job['mask_indices'],'frozen_assigned_list');check([r['mask_index'] for r in result['results']]==job['mask_indices'],'ordered_complete_unique_results')
   psums={}
   for line in small(prefix+'SHA256SUMS').decode().splitlines():
    h,n=line.split('  ',1);assert n not in psums;psums[n]=h
   if number<=2:
    software={n[len(prefix):]:('outer',n) for n in members if n.startswith(prefix+'research/')}
    nested=None
   else:
    zipname=prefix+('software/case-tools.zip' if number==3 else 'inputs/case-tools.zip')
    assert members[zipname].file_size<1000000
    nested=zipfile.ZipFile(io.BytesIO(z.read(zipname)))
    software={n:('inner',n) for n in nested.namelist()}
   def source_bytes(key):
    kind,n=software[key]
    if kind=='outer':return small(n)
    assert nested.getinfo(n).file_size<=LIMIT
    return nested.read(n)
   receipts=[]
   for row in result['results']:
    index=row['mask_index'];p=prefix+row['independent_audit'];raw=small(p);r=json.loads(raw)
    issues=[]
    def require(c,s):
     if not c:issues.append(s)
    require(row['occupied_cells']==job['masks'][str(index)],'wrong_assigned_cells')
    require(row['status']=='proved' and row['mask_exclusion_proved'] is True and row['constraints']==[] and row['unresolved_obligations']==[],'unproved_result')
    require(sha(raw)==row['independent_audit_sha256']==psums[row['independent_audit']]==sums[p],'audit_hash_binding')
    require(prefix+row['source'] in members,'source_missing')
    require(row['source_sha256']==r['source_sha256']==psums[row['source']]==sums[prefix+row['source']],'source_declared_hash_binding')
    require(r['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT' and r['mask_exclusion_proved'] is True and r['branch_exclusion_proved'] is True,'saved_audit_status')
    require(r['mask_index']==index and r['mask']==row['occupied_cells'],'saved_mask')
    require(r['constraints']==[] and r['inside_local_guard'] is False and r['global_optimality_proved'] is False and r['root_audit_sha256'] is None,'saved_unconditional_domain')
    require(r['parent_Uplus']==U and r['cover_sha256']==COVER,'saved_U_cover')
    require(r['transferred_canonical_mask_indices']==[index] and r['continuum_canonical_masks_excluded']==1,'saved_transfer')
    require(set(r['dependencies'])==BASE_DEPS,'dependency_name_inventory')
    actualdeps={};differences={}
    for name,digest in r['dependencies'].items():
     candidates=[k for k in software if Path(k).name==name]
     matches=[]
     for k in candidates:
      h=sha(source_bytes(k))
      if h==digest:matches.append(k)
     require(bool(matches),'missing_dependency_bytes:'+name)
     actualdeps[name]=dict(sha256=digest,matching_sources=matches)
     if name in pins and digest!=pins[name]['sha256']:differences[name]=dict(returned=digest,earlier_reviewed=pins[name]['sha256'])
    nodes=[]
    for n in r['nodes']:
     rel='certificates/'+Path(n['path']).name
     require(prefix+rel in members,'missing_node_member:'+rel)
     require(psums.get(rel)==n['sha256']==sums.get(prefix+rel),'node_declared_hash_binding:'+rel)
     require(n['constraints']==[] and n['inside_local_guard'] is False,'conditional_ancestor_record')
     require('cached_from_audit_sha256' not in n,'unexpected_cached_node')
     nodes.append(dict(member=prefix+rel,sha256=n['sha256'],bytes=members[prefix+rel].file_size,rows=n['rows']))
    require(bool(nodes) and nodes[-1]['sha256']==row['source_sha256'],'terminal_record_binding')
    seed_matches=[prefix+n for n,h in psums.items() if h==r['root_sha256']]
    require(len(seed_matches)==1,'seed_manifest_match')
    receipt=dict(mask=index,audit_member=p,audit_sha256=sha(raw),result_source=prefix+row['source'],saved_source_sha256=row['source_sha256'],issues=issues,dependency_differences_from_earlier_profile=differences,dependencies=actualdeps,nodes=nodes,seed_members=seed_matches,seed_ownership_checks=len(r['seed_ownership_checks']),backend=r['rational_backend'],backend_version=r['rational_backend_version'],backend_binary_sha256=r['rational_binary_sha256'])
    receipts.append(receipt);allrows.append(receipt)
   assignment_path=prefix+('assignment.md' if number==1 else ('inputs/02-case-exclusions.md' if number==2 else ('software/03-case-exclusions.md' if number==3 else 'inputs/04-case-exclusions.md')))
   check(assignment_path in members and small(assignment_path)==(ROOT/'relay-handoff'/f'{number:02d}-case-exclusions.md').read_bytes(),'assignment_document_exact_bytes')
   packet=dict(job_id=job_id,result_sha256=sha(result_bytes),replay_sha256=sha(small(prefix+'replay.py')),checks=checks,case_count=len(receipts),producer_nodes=sum(len(r['nodes']) for r in receipts),saved_rows=sum(n['rows'] for r in receipts for n in r['nodes']),saved_seed_checks=sum(r['seed_ownership_checks'] for r in receipts),manifest_members=len(psums),manifest_missing=sorted(n for n in psums if prefix+n not in members),manifest_unlisted=sorted(n[len(prefix):] for n in members if n.startswith(prefix) and n[len(prefix):] not in psums and n!=prefix+'SHA256SUMS'),receipts=receipts)
   packets.append(packet)
result=dict(status='STATIC_SMALL_MEMBER_AUDIT_ONLY',scope='Read central directory, manifests, small result/audit/source members and two sub-megabyte nested tool ZIPs. No large producer or seed files read, no full archive integrity test, no full file SHA checks, and no returned code executed.',frozen_assignments_sha256=sha(ASSIGN.read_bytes()),containers=containers,packets=packets,total_cases=len(allrows),distinct_cases=len({r['mask'] for r in allrows}),receipt_issues=[dict(mask=r['mask'],issues=r['issues']) for r in allrows if r['issues']])
(OUT/'metadata-audit.json').write_text(json.dumps(result,indent=2)+'\n')
for p in packets:
 print(p['job_id'],'cases',p['case_count'],'nodes',p['producer_nodes'],'rows',p['saved_rows'],'seedchecks',p['saved_seed_checks'],'checks',p['checks'],'missing',p['manifest_missing'],'unlisted',p['manifest_unlisted'])
 print('dependency profiles',list({json.dumps(r['dependency_differences_from_earlier_profile'],sort_keys=True) for r in p['receipts']}))
print('issues',result['receipt_issues']);print('container checks',containers)
