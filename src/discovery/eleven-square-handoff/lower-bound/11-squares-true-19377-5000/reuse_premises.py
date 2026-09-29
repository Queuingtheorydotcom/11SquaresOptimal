"""Independent, exact premises for direct-origin TRUE receipt reuse."""
if not __debug__:raise SystemExit('Do not run with -O or -OO.')
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
from premises import need,read,filehash,canonical,digest,core_job

SAME='true-catalogue-same-job-receipt-transfer-v1'
MONOTONE='true-catalogue-monotone-retreat-transfer-v1'


def safe_file(root,name,paths,expected=None):
 p=Path(name)
 need(not p.is_absolute() and '..' not in p.parts and p.parts and p.parts[0]=='provenance','Unsafe provenance path')
 p=root/p;need(p.is_file() and not p.is_symlink(),'Missing/unsafe provenance member')
 if expected is not None:need(filehash(p)==expected,'Origin payload hash mismatch: '+name)
 paths.add(name);return read(p) if p.suffix=='.json' else None


def context_check(run):
 q=deepcopy(run);h=q.pop('context_sha256')
 need(digest(canonical(q))==h,'Origin context hash mismatch')
 need('receipt_transfer' not in run,'Nested receipt transfer needs an independent chain proof')


def semantic_data(c):
 q=deepcopy(c)
 for key in ('entries','A','bound','retreat_provenance'):q.pop(key,None)
 return q


def retreat_note(c,origins):
 note=c.get('retreat_provenance')
 if note is None:return
 required={'new_parent_side','new_target','old_parent_side','old_target','scope','source_proposal_sha256','weights_and_geometry_unchanged_except_parent_side'}
 need(set(note)==required and note['weights_and_geometry_unchanged_except_parent_side'] is True,'Unsupported retreat metadata')
 need(F(note['new_parent_side'])==F(c['A']) and F(note['new_target'])==F(c['bound']),'Wrong retreat target metadata')
 sources=[o for o in origins.values() if o['run']['input_proposal_sha256']==note['source_proposal_sha256']]
 need(sources and all(F(o['proposal']['A'])==F(note['old_parent_side']) and F(o['proposal']['bound'])==F(note['old_target']) for o in sources),'Unbound retreat origin metadata')
 need(F(note['old_parent_side'])<=F(c['A']) and F(note['old_target'])>=F(c['bound']),'Retreat metadata points in wrong direction')


def source_job(node,key,run,c):
 need('receipt_transfer' not in node,'Nested node receipt transfer is unsupported')
 identity={k:node[k] for k in ('context_sha256','entry','job')}
 need(node['context_sha256']==run['context_sha256'] and node['key']==key==digest(canonical(identity)),'Origin node identity mismatch')
 a,b,t,B=map(F,node['entry']);job=core_job(F(c['A']),F(c['L']),a,b,F(run['margin']))
 need(job==tuple(map(F,node['job'])) and (t,B)==job[:2],'Origin core is not its exact strict job')
 r=node['receipt']
 need(node['outcome']=='PASS' and r['status']=='PASS' and all(type(r.get(k)) is int and r[k]>=0 for k in ('minimum_units','cells','slabs')),'Origin leaf is not a valid PASS receipt')
 need(r['minimum_units']>=c['minimum_units'],'Origin leaf threshold fails')
 need(not any(x.get('deficient') for x in node.get('parent_checks',[])),'Origin PASS contains a deficient parent')
 return job


def validate_reuse(root,info,leaves):
 """Check every provenance byte and reconstruct a direct fresh replay DAG."""
 root=Path(root);run=info['run'];meta=run['receipt_transfer'];schema=meta['schema']
 need(schema in (SAME,MONOTONE),'Unsupported receipt reuse schema');paths=set()
 index=safe_file(root,'provenance/origins.json',paths,meta['origin_index_sha256'])
 need(index['schema']==schema,'Origin schema mismatch')
 helpers=meta['helper_sha256']
 names={'merge_receipts.py':'merge_receipts_used.py','monotone_merge.py':'monotone_merge_used.py'}
 if schema==SAME:helpers={'merge_receipts.py':helpers};names['merge_receipts.py']='merge_used.py'
 need(set(helpers)==({'merge_receipts.py'} if schema==SAME else set(names)),'Unexpected transfer helpers')
 for key,h in helpers.items():need(filehash(root/names[key])==h,'Transfer helper hash mismatch');paths.add(names[key])
 transfer=safe_file(root,'provenance/transfers.json',paths)
 merged=read(root/'MERGE_RESULT.json');paths.add('MERGE_RESULT.json')
 need(merged['status']==('PASS_SAME_JOB_TRANSFER_AND_UNCHANGED_ASSEMBLY' if schema==SAME else 'PASS_MONOTONE_TRANSFER_AND_UNCHANGED_ASSEMBLY'),'Transfer assembly is not complete')
 need(merged['context_sha256']==transfer['context_sha256']==run['context_sha256'],'Transfer destination context mismatch')
 need(merged['schema']==transfer['schema']==schema and transfer['origin_index_sha256']==meta['origin_index_sha256'],'Transfer schema/index mismatch')
 need(merged['provenance_sha256']==filehash(root/'provenance/transfers.json') and merged['result_sha256']==filehash(root/'RESULT.json'),'Transfer result payload mismatch')
 need(merged['helper_sha256']==meta['helper_sha256'],'Transfer result helper mismatch')
 origins={};target=info['candidate']
 common={'context_sha256','selected_rows','max_depth','receipt_transfer'}
 if schema==MONOTONE:common|={'input_proposal_sha256','fixed_proposal_sha256'}
 for item in index['origins']:
  oid=item['id'];need(isinstance(oid,str) and oid not in origins and oid.replace('_','').isalnum(),'Invalid/duplicate origin ID')
  if 'files' in item:
   files=item['files'];required={'run.json','RESULT.json','proposal.json','input-proposal.json','template.json','build_used.py'}
   need(required<=set(files)<=required|{'proxy.json'},'Missing/unexpected origin fixed files')
   fixed={}
   for name,record in files.items():
    need(record['path']==f'provenance/{oid}/{name}','Origin fixed path mismatch')
    fixed[name]=safe_file(root,record['path'],paths,record['sha256'])
   sr,sc,res=fixed['run.json'],fixed['proposal.json'],fixed['RESULT.json']
   initial=deepcopy(fixed['input-proposal.json']);initial.pop('exploratory_only',None);initial['entries']=[]
   need(initial==sc,'Origin input transformation differs')
   need(digest(canonical(sc))==sr['fixed_proposal_sha256'],'Origin fixed proposal mismatch')
   need(digest(canonical(fixed['template.json']))==sr['template_sha256'],'Origin template mismatch')
   for name,key in [('input-proposal.json','input_proposal_sha256'),('build_used.py','builder_sha256')]:need(files[name]['sha256']==sr[key],'Origin fixed byte binding differs')
   need(('proxy.json' in files)==(sr['proxy_sha256'] is not None),'Origin proxy missing/unexpected')
   if sr['proxy_sha256'] is not None:need(files['proxy.json']['sha256']==sr['proxy_sha256'],'Origin proxy hash differs')
  else:
   need(schema==SAME,'Monotone origin needs its original charge data')
   sr=safe_file(root,item['run_path'],paths,item['run_sha256']);res=safe_file(root,item['result_path'],paths,item['result_sha256'])
   sc=deepcopy(target);sc['entries']=[]
  context_check(sr);need(sr['context_sha256']==item['context_sha256']==res['context_sha256'],'Origin context identity differs')
  need({k:v for k,v in sr.items() if k not in common}=={k:v for k,v in run.items() if k not in common},'Origin changes predicate/checker/resource context')
  need(semantic_data(sc)==semantic_data(target),'Origin changes charge semantics or weights')
  need(F(sc['bound'])==F(sc['L'])/F(sc['A']) and F(sc['A'])<=F(target['A']),'Origin is not a valid ancestor side')
  if schema==SAME:need(F(sc['A'])==F(target['A']),'Same-job transfer changed parent side')
  if schema==MONOTONE:
   need(all(type(p[-1]) is int and p[-1]>=0 for p in sc['point_orbits']),'Negative/noninteger point weight')
   need(all(x.get('kind') in ('floor','majority_hull') and type(x['weight']) is int and x['weight']>=0 for x in sc['charge_orbits']),'Unsupported/nonmonotone charge family')
  roots={};nodes={};nodehash={}
  for rec in item['roots']:
   row=rec['row'];need(type(row) is int and row not in roots,'Duplicate/invalid origin row')
   need(rec['root_path']==f'provenance/{oid}/roots/{row}.json','Origin root path mismatch')
   rr=safe_file(root,rec['root_path'],paths,rec['root_sha256'])
   need(res['root_receipt_sha256'][str(row)]==rec['root_sha256'],'Origin result/root hash mismatch')
   need(rr['context_sha256']==sr['context_sha256'] and rr['row']==row,'Origin root identity mismatch');roots[row]=rr
   for nr in rec['nodes']:
    key=nr['key'];need(nr['path']==f'provenance/{oid}/nodes/{key}.json','Origin node path mismatch')
    nn=safe_file(root,nr['path'],paths,nr['sha256']);need(key not in nodes or nodes[key]==nn,'Conflicting origin node');nodes[key]=nn;nodehash[key]=nr['sha256']
  need(sorted(roots)==sr['selected_rows'] and res['completed_source_intervals']==len(roots) and not res['missing_source_intervals'],'Origin selected roots incomplete')
  origins[oid]={'run':sr,'proposal':sc,'roots':roots,'nodes':nodes,'nodehash':nodehash}
 for o in origins.values():retreat_note(o['proposal'],origins)
 retreat_note(target,origins)
 need(merged['origin_contexts']==[o['run']['context_sha256'] for o in origins.values()],'Origin context summary differs')
 replay={};rows=set();changed=0;replaced=[]
 for tr in transfer['transfers']:
  row=tr['row'];need(type(row) is int and row not in rows,'Repeated transfer row');rows.add(row)
  o=origins[tr['origin_id']];oldroot=o['roots'][row];newroot=read(root/f'roots/{row}.json')
  need(oldroot['status']=='PASS' and not oldroot['failed'],'Unproved origin root was transferred')
  need(filehash(root/f'provenance/{tr["origin_id"]}/roots/{row}.json')==tr['origin_root_sha256'],'Transfer origin root hash differs')
  need(filehash(root/f'roots/{row}.json')==tr['root_sha256'],'Transfer target root hash differs')
  need([x['origin_key'] for x in tr['leaves']]==oldroot['accepted_keys'] and [x['key'] for x in tr['leaves']]==newroot['accepted_keys'],'Transfer leaf mapping is incomplete')
  er=deepcopy(oldroot);er.update(context_sha256=run['context_sha256'],accepted_keys=newroot['accepted_keys']);need(er==newroot,'Target root changes more than context/keys')
  if tr['origin_id']!='base':replaced.append(row)
  for rec in tr['leaves']:
   ok,nk=rec['origin_key'],rec['key'];old=o['nodes'][ok];new=read(root/f'nodes/{nk}.json')
   need(o['nodehash'][ok]==rec['origin_node_sha256'] and filehash(root/f'nodes/{nk}.json')==rec['node_sha256'],'Transfer leaf byte hash differs')
   oj=source_job(old,ok,o['run'],o['proposal']);nj=tuple(map(F,new['job']))
   need(oj[0]==nj[0] and 0<oj[1]<=nj[1] and 0<=nj[2]<=oj[2],'Invalid monotone core/domain inclusion')
   need(old['entry'][:2]==new['entry'][:2] and rec['entry']==new['entry'] and rec['job']==new['job'],'Transferred interval/job differs')
   expected=deepcopy(old);expected.update(context_sha256=run['context_sha256'],key=nk,entry=new['entry'],job=new['job'])
   if schema==SAME:need(oj==nj,'Same-job transfer changed geometry')
   else:
    kind='identical_job' if oj==nj else 'monotone_core_domain'
    inclusion={'same_halfangle':True,'core_side_increase':str(nj[1]-oj[1]),'center_radius_decrease':str(oj[2]-nj[2])}
    for k,v in {'origin_entry':old['entry'],'origin_job':old['job'],'kind':kind,**inclusion}.items():need(rec[k]==v,'Stored monotone assertion differs')
    expected['receipt_transfer']={'schema':schema,'kind':kind,'origin_id':tr['origin_id'],'origin_key':ok,'origin_node_sha256':rec['origin_node_sha256'],'origin_entry':old['entry'],'origin_job':old['job'],**inclusion}
   need(expected==new,'Transferred node alters original receipt/payload')
   need(nk not in replay,'Duplicate target leaf transfer');replay[nk]=oj;changed+=int(oj!=nj)
 need(rows==set(range(info['source_intervals'])) and set(replay)=={x['key'] for x in leaves},'Transfer does not cover every target leaf')
 need(transfer['replaced_source_rows']==merged['replaced_source_rows']==sorted(replaced),'Replacement summary differs')
 need(merged['transferred_leaves']==len(leaves),'Transferred leaf count differs')
 if schema==MONOTONE:need(merged['monotone_leaves']==changed,'Monotone leaf count differs')
 return {'paths':sorted(paths),'replay_jobs':[replay[x['key']] for x in leaves],'monotone_jobs':changed,'origin_contexts':[o['run']['context_sha256'] for o in origins.values()]}
