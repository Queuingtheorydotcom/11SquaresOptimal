"""Prepare package inventory from small receipts and bounded source metadata.

Does not hash large files, run checkers, replay geometry, or copy proof data.
"""
from pathlib import Path
from collections import defaultdict
import hashlib,json,re
HERE=Path(__file__).resolve().parent
WORKSPACE=HERE.parents[2]
RESEARCH=WORKSPACE/'research'
MAX_SMALL=200000
SNAPSHOT=RESEARCH/'relay-handoff/frozen-frontier-count-crosscheck.json'
SNAPSHOT_HASH='ac6d560598823e612d8d8f03be6918601456064fe7c4c52a4bec31d3bb1ada2a'
PINNED={
'research/phase3/work/phase3/audit/overall-union-snapshot-bc3563a0c995.json':'bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545',
'research/PHASE3_FRESH_REPLAY_RESULT.json':'04fa1ebb37f5dace29946224fe8c7c5d8a1bedb4fa860c65b359f4200415de57',
'research/aggregate_phase3_fresh.py':'e6af5b32d54bb0cd675568b85425a63961e277c7d6b802877022baf3d24df691',
'research/audit-lower-bound/strict_generic_inventory.py':'7df54d904bb5d0cc609a4765eeafc3fb57922bcb3a4b210082df9fda36266530',
'research/audit-lower-bound/strict_tree_inventory.py':'b6a298ccfa1a27911b3e88c832f890a983e0c6e7c374455808e42eb730626059',
'research/audit-lower-bound/strict-inventory-pins.json':'8a46589d35e3bbd1efce02b2a196db5ddb636a85259bf7f30d6b31daa65b01f8',
'research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json':'df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e',
'research/endpoint-audit/audit_native_cached.py':'9bff671e43ccb3dc1296fa740c41bfa7978d8cc924caddfbeabaac63d260f06b',
'research/endpoint-audit/audit_native_tree.py':'32ed54cabef554a3cfe2f795e8ff81a6b7d143b996dbeb1b096b4cae5fa1a3cb',
'research/phase3/work/phase3/hull/audit_tree_batch_v4.py':'04ceb52e087c7e2fec72a512bffb4b147e99391898d6ce1491215965bb715f8a',
'research/frontier/audit_overlay_exclusion.py':'f3eefa77e6f02b977d6bfe38e5bc7e1e32fd6e355de7d226c803291b9a6ea5e1',
'research/global-math/overlay_field_halfplanes_v2.py':'ee942f83af21aa2ab58b080b37cc95d5064d37b0458cfd2b93c2be8ab7ba1c74',
'research/phase3/work/phase2/hull/audit_residual_kernel.py':'df5676c16d1ec946b12fb46fc6491594c04a042f9bfdca72eadc9316567be9c2',
'research/phase3/work/phase2/hull/arrangement_audit.py':'864f89da214e7a8aa6be720bdd94ff79018c730ed3c5c0b16d63489e7460b251',
}
items={};receipts={};headers={};issues=[]

def small(path):
 path=Path(path);assert path.stat().st_size<=MAX_SMALL,('not small',str(path))
 return path.read_bytes()

def read(path):return json.loads(small(path))
def digest(b):return hashlib.sha256(b).hexdigest()
def resolve(ref,owner=None):
 p=Path(ref)
 candidates=[p] if p.is_absolute() else [WORKSPACE/p]+([Path(owner).parent/p] if owner else [])
 found={p.resolve() for p in candidates if p.is_file()}
 assert len(found)==1,(ref,'ambiguous/missing source',list(map(str,found)))
 return found.pop()

def add(path,expected,role,used_by=None):
 p=resolve(path);rel=p.relative_to(WORKSPACE).as_posix()
 assert re.fullmatch('[0-9a-f]{64}',expected),(rel,expected)
 if rel in items:
  item=items[rel];assert item['expected_sha256']==expected,('conflicting source hashes',rel)
 else:
  size=p.stat().st_size
  item=dict(source=str(p),target=rel,expected_sha256=expected,bytes=size,roles=[],used_by=[],hash_status='DECLARED_NOT_REHASHED_LARGE_FILE')
  if size<=MAX_SMALL:
   assert digest(small(p))==expected,('changed small source',rel)
   item['hash_status']='SMALL_FILE_HASH_CHECKED'
  items[rel]=item
 if role not in item['roles']:item['roles'].append(role)
 if used_by is not None and used_by not in item['used_by']:item['used_by'].append(used_by)
 return p

def field(fragment,key):
 matches=list(re.finditer(r'"'+re.escape(key)+r'"\s*:',fragment))
 assert len(matches)==1,('nonunique/missing bounded metadata field',key,len(matches))
 return json.JSONDecoder().raw_decode(fragment[matches[0].end():].lstrip())[0]

def node_header(p):
 if p in headers:return headers[p]
 # Only metadata before the enormous initial state and the trailing dependency
 # object is read. Full JSON/hash validation belongs to the root worker.
 with p.open('rb') as f:
  head=f.read(8192).decode();f.seek(max(0,p.stat().st_size-32768));tail=f.read().decode()
 initial=re.search(r'"initial"\s*:',head)
 prefix=head[:initial.start()] if initial else head
 values={key:field(prefix,key) for key in ['schema','parent','source','mask_index','mask','U','B']}
 values['dependencies']=field(tail,'dependencies')
 headers[p]=values
 return values

def collect_audit(path,expected,role='independent_audit'):
 p=add(path,expected,role)
 if p in receipts:return receipts[p]
 a=read(p);receipts[p]=a
 for name,h in a['dependencies'].items():
  if name=='audit_tree_batch_v4.py':target=RESEARCH/'phase3/work/phase3/hull'/name
  else:target=RESEARCH/'phase3'/dep_pins[name]['path']
  add(target,h,'checker_dependency',a['mask_index'])
 for record in a['nodes']:
  n=add(resolve(record['path'],p),record['sha256'],'producer_node',a['mask_index'])
  head=node_header(n)
  assert head['schema']=='exact_generic_owned_hull_v1'
  assert head['mask_index']==a['mask_index'] and head['mask']==a['mask']
  add(resolve(head['source']['path'],n),head['source']['sha256'],'wall_seed',a['mask_index'])
  assert head['source']['sha256']==a['root_sha256']
  if head['parent'] is not None:add(resolve(head['parent']['path'],n),head['parent']['sha256'],'producer_parent',a['mask_index'])
  for ref,h in head['dependencies'].items():add(resolve(ref,n),h,'producer_program_provenance',a['mask_index'])
 for premise in a.get('premise_audits',[]):collect_audit(resolve(premise['path'],p),premise['sha256'],'cached_premise_audit')
 for adapter in ([a['native_portability_adapter']] if 'native_portability_adapter' in a else a.get('native_portability_adapters',[])):
  add(resolve(adapter['path'],p),adapter['sha256'],'native_portability_adapter',a['mask_index'])
 return a

assert digest(small(SNAPSHOT))==SNAPSHOT_HASH
snapshot=read(SNAPSHOT)
assert snapshot['extension_receipts']==76 and snapshot['excluded']==2007
for rel,h in PINNED.items():add(WORKSPACE/rel,h,'fixed_input')
add(SNAPSHOT,SNAPSHOT_HASH,'frozen_76_receipt_selection')
dep_pins=read(RESEARCH/'audit-lower-bound/strict-inventory-pins.json')
for name,pin in dep_pins.items():add(RESEARCH/'phase3'/pin['path'],pin['sha256'],'checker_dependency')
old_path=RESEARCH/'frontier/union-snapshot-93856c2b8cd8.json';old=read(old_path)
old_hash=digest(small(old_path));add(old_path,old_hash,'last_strict_union')
assert old['excluded_canonical_cases']==1997
pending=sorted(set(snapshot['excluded_cases'])-set(old['excluded_canonical_mask_indices']))
assert pending==[927,998,1111,1112,1114,1115,1124,1125,1128,1143]
entries=[]
for e in snapshot['entries']:
 p=add(e['audit'],e['audit_sha256'],'selected_exclusion_receipt',e['mask']);r=read(p)
 if r['status']=='PASS_D4_ANTECEDENTS_DISCHARGED_EXACT_MASK_EXCLUSION':
  kind='necessary_D4_cuts_and_independent_geometry'
  collect_audit(r['geometric_audit'],r['geometric_audit_sha256'],'overlay_geometry_audit')
  add(r['source'],r['source_sha256'],'overlay_terminal_source',e['mask'])
  for name,h in [('all-overlay-support-253/supported-center-hulls.json',r['source_hulls_sha256']),('all-overlay-support-253/independent-replay.json',r['support_replay_sha256']),('overlay-geometry-independent-replay.json',r['geometry_replay_sha256'])]:
   add(RESEARCH/'global-math'/name,h,'necessary_overlay_premise',e['mask'])
 elif r['status']=='PASS_INDEPENDENT_PARTIAL_TREE_AUDIT':
  kind='native_cached_v4_center_partition'
  collect_audit(p,e['audit_sha256'])
  tree=RESEARCH/'endpoint-audit/mask1383-two-branch-tree.json'
  add(tree,r['tree_sha256'],'exact_partition_tree',e['mask'])
  t=read(tree)
  add(resolve(t['root_source']['path'],tree),t['root_source']['sha256'],'wall_seed',e['mask'])
  for n in t['nodes'].values():add(resolve(n['receipt']['path'],tree),n['receipt']['sha256'],'tree_node_source',e['mask'])
 else:
  kind='native_cached_v9' if r.get('premise_audits') else 'direct_v9'
  collect_audit(p,e['audit_sha256'])
 entries.append(dict(mask_index=e['mask'],audit=str(p),audit_target=p.relative_to(WORKSPACE).as_posix(),audit_sha256=e['audit_sha256'],expected_cases=e['cases'],kind=kind,new_since_1997=e['mask'] in pending))
# Read only the small header, not the large finite support replay itself.
support_path=RESEARCH/'global-math/all-overlay-support-253/independent-replay.json'
with support_path.open() as f:prefix=f.read(4096)
for role,row in field(prefix,'sources').items():add(row['path'],row['sha256'],'overlay_support_'+role)
add(RESEARCH/'global-math/audit_all_overlay_support.py',field(prefix,'checker_sha256'),'overlay_support_checker')
g=read(RESEARCH/'global-math/overlay-geometry-independent-replay.json')
for role,row in g['sources'].items():add(row['path'],row['sha256'],'overlay_geometry_'+role)
add(RESEARCH/'global-math/audit_overlay_geometry.py',g['checker_sha256'],'overlay_geometry_checker')
# The recorded fresh-baseline root receipt is an immutable reusable premise.
# Its complete source package is the separate baseline task's responsibility.
fresh=read(RESEARCH/'PHASE3_FRESH_REPLAY_RESULT.json')
for key,relative in [('portability_wrapper_sha256','phase3_portable_replay.py'),('field_replay_driver_sha256','replay_phase3_fields.py'),('generic_replay_driver_sha256','replay_phase3_generic.py'),('field_replay_result_sha256','phase3-fresh-fields/RESULT.json'),('generic_replay_result_sha256','phase3-fresh-generic/RESULT.json')]:add(RESEARCH/relative,fresh[key],'fresh_baseline_provenance')
# Add actual historical imported helper paths; receipts hardcode sibling
# phase3 helpers, while the common wrapper puts phase2 first.
wrapper=RESEARCH/'frontier/audit_case.py';add(wrapper,digest(small(wrapper)),'historical_replay_wrapper')
for item in list(items.values()):
 if 'wall_seed' in item['roles']:
  p=Path(item['source'])
  with p.open('rb') as stream:
   stream.seek(max(0,p.stat().st_size-8192));tail=stream.read().decode()
  for key in ['cover_source','wall_groups_source','producer_source']:
   ref=field(tail,key);add(resolve(ref['path'],p),ref['sha256'],'seed_'+key)
for script in ['prepare_inventory.py','integrate_prior_union.py']:
 p=HERE/script;add(p,digest(small(p)),'integration_tool')
for p in list(items.values()):p['roles'].sort();p['used_by'].sort()
result=dict(schema='eleven_square_prior_union_package_inventory_v1',status='PREPARED_NOT_STRICTLY_EXECUTED',original_workspace=str(WORKSPACE),package_layout='Preserve each target path relative to the proof package root.',snapshot_sha256=SNAPSHOT_HASH,baseline_snapshot_sha256=PINNED['research/phase3/work/phase3/audit/overall-union-snapshot-bc3563a0c995.json'],baseline_fresh_receipt_sha256=PINNED['research/PHASE3_FRESH_REPLAY_RESULT.json'],last_strict_union_sha256=old_hash,expected_baseline_cases=1931,expected_extension_receipts=76,expected_distinct_additions=76,expected_union_cases=2007,expected_remaining_cases=177,pending_ten_cases=pending,strict_checker_pins={Path(p).name:h for p,h in PINNED.items() if 'strict_' in p or p.endswith('strict-inventory-pins.json')},entries=entries,files=sorted(items.values(),key=lambda x:x['target']),metadata_read_policy='Whole files at most 200000 bytes. Each large producer: at most 8192 header plus 32768 trailer bytes; each seed: 8192 trailer bytes; large support replay: 4096 header bytes. No large file hashing, copying, geometric replay or strict worker execution.',external_baseline_obligation='Separate baseline package must retain the already completed 59+34 geometric proofs; this inventory includes its pinned completed root receipt and provenance records.',runtime={'historical_native_gmp_version':'2.3.1','historical_native_binary_sha256':'4fdf5fbaea9d3c4f756f9f656d0d7656fc4a66c82a8e921f326e570702dc463d','new_geometric_replay_required':False,'inventory_job_worker_limit':1},issues=issues)
(HERE/'SOURCE_INVENTORY.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],entries=len(entries),files=len(items),small_hash_checked=sum(x['hash_status']=='SMALL_FILE_HASH_CHECKED' for x in items.values()),large_declared=sum(x['hash_status']!='SMALL_FILE_HASH_CHECKED' for x in items.values()),pending_ten_cases=pending),indent=2))
