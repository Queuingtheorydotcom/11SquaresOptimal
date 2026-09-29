"""Summarize this worker's research without promoting discovery to proof."""
from pathlib import Path
from collections import Counter
import hashlib,json,time
HERE=Path(__file__).resolve().parent;PHASE=HERE.parent;TOP=HERE.parents[1]
def read(p,d=None):
 try:return json.loads(p.read_text())
 except OSError:return d
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
field_audit_path=PHASE/'audit/current-union-independent-audit.json';field_audit=read(field_audit_path,{})
auditpath=PHASE/'audit/overall-union-independent-audit.json'
if not auditpath.exists():auditpath=field_audit_path
audit=read(auditpath,{})
receipts={p['packet_sha256']:p for p in field_audit.get('entries',[])}
proofs=[]
for producer in ['batch','batch_subset','batch_recursive','batch_root_recursive']:
 for r in read(PHASE/producer/'patterns.json',[]):
  packet=Path(r['packet']);gate=Path(r['gate']);p=read(packet);g=read(gate);digest=sha(packet)
  proofs.append(dict(producer=producer,mask=r['mask'],pattern_id=r.get('pattern_id'),final=r.get('final',False),required_cells=r['required_cells'],positive_cell_thresholds={str(i):v for i,v in enumerate(p['threshold_units']) if v},budget_units=p['certificate']['budget_units'],counting_surplus_units=p['conditional_counting_surplus_units'],packet=str(packet),packet_sha256=digest,gate=str(gate),gate_sha256=sha(gate),gate_status=g['status'],gate_rows=g['rows'],gate_hash_binding=(g['packet_sha256']==digest),included_in_current_independent_union_registry=digest in receipts,independent_receipt=receipts.get(digest)))
queues={}
for producer in ['batch_recursive','batch_root_recursive']:
 q=read(PHASE/producer/'queue-state.json',{})
 queues[producer]=dict(states=dict(Counter(x['status'] for x in q.values())),pending=len(read(PHASE/producer/'pending-candidates.json',[])))
report=dict(status='PARTIAL_EXACT_EXCLUSION_RESEARCH',timestamp_unix=time.time(),global_optimality_proved=False,scope='Complete exact producer certificates listed individually. The global conclusion is limited to the separately audited union; remaining masks are unresolved. Finite-only attempts and single-square refuters do not establish packing exclusions.',parent_Uplus=audit.get('parent_Uplus'),main_queue_counts=dict(Counter(r['state'] for r in read(HERE/'queue.json',[]))),recursive_queues=queues,global_independent_audit=dict(path=str(auditpath),sha256=sha(auditpath),excluded=audit.get('excluded_canonical_cases'),remaining=audit.get('remaining_canonical_cases')),producer_certificates=proofs,omission_refuter_pool_manifest=str(HERE/'omission-refuter-manifest.json'),source_review=str(HERE/'weighted-cover-source-review.json'))
generic=PHASE/'hull/mask1698-generic-v2-independent-audit.json'
if generic.exists():
 g=read(generic);report['additional_independent_replays']=[dict(path=str(generic),sha256=sha(generic),status=g['status'],mask_index=g['mask_index'],checker='audit_capture_v5.py',registry_edited=False)]
report['polygon_core_source_review']=str(HERE/'polygon-core-source-review.json')
report['closed_weighted_cover_source_review']=str(HERE/'closed-weighted-cover-source-review.json')
report['polygon_core_mathematical_lemma']=str(HERE/'POLYGON_CORE_ATOM_LEMMA.md')
generic_queue=read(HERE/'generic/queue.json',[])
if generic_queue:
 report['generic_queue']=dict(path=str(HERE/'generic/queue.json'),states=dict(Counter(r['state'] for r in generic_queue)),candidates=str(HERE/'generic/candidates.json'),scope='Producer contradictions require independent replay before contributing to the authoritative union.')
(HERE/'BATCH_RESEARCH_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(certificates=len(proofs),main_queue=report['main_queue_counts'],audit=report['global_independent_audit'])))
