"""Record portable provenance for finite-search refuter rows and numerical jitter.
Does not promote either artifact class into a continuum proof.
"""
from pathlib import Path
import hashlib,json,numpy as np
HERE=Path(__file__).resolve().parent;TOP=HERE.parents[2];BASE=TOP/'current/research/optimality/deficit_geometry/physical_features';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(Path(p).resolve().relative_to(TOP))
entries=[]
for item in json.loads((HERE/'multi-history.json').read_text()):
 m=item['mask'];entries.append((f'mask{m}-p2batchpool',Path(item['packet']),Path(item['receipt'])))
for iteration in [2,3]:
 entries.append((f'mask379-p2batchrepair{iteration}',BASE/f'mask379-p2batchrepair{iteration-1}-packet.json',BASE/f'mask379-p2batchrepair{iteration-1}-exact-gate.json'))
records=[];exact_total=0;numerical_total=0
for stem,packet,gate in entries:
 exact=BASE/(stem+'-exact.npz');jitter=BASE/(stem+'-jitter.npz');em=exact.with_suffix('.json');jm=jitter.with_suffix('.json');e=json.loads(em.read_text());j=json.loads(jm.read_text());r=json.loads(gate.read_text());assert r['records'][-1]['status']=='REFUTED_BY_LEGAL_PARENT';assert r['packet_sha256']==sha(packet)
 source=TOP/'current'/e['source_report'];assert sha(source)==sha(gate)==e['source_report_sha256'];assert e['source_packet_sha256']==sha(packet)
 with np.load(exact)as z:
  erows=len(z['rows']);assert erows==e['rows']==8;assert z['rows'].shape[1]==1232;assert (z['rows']<=z['parent_rows']).all();assert z['legal'].all();keys=sorted(z.files)
 with np.load(jitter)as z:nrows=len(z['rows'])
 assert j['rows']==nrows==1024 and j['exact_rows']==0 and j['geometry_coverage'] is False;assert j['source']==str(exact.relative_to(TOP/'current'))
 exact_total+=erows;numerical_total+=nrows
 records.append(dict(stem=stem,source_packet=dict(path=rel(packet),sha256=sha(packet)),source_gate=dict(path=rel(gate),sha256=sha(gate)),copied_source_report=dict(path=rel(source),sha256=sha(source)),exact_capture=dict(path=rel(exact),sha256=sha(exact),metadata_path=rel(em),metadata_sha256=sha(em),rows=erows,fields=keys),numerical_neighborhood=dict(path=rel(jitter),sha256=sha(jitter),metadata_path=rel(jm),metadata_sha256=sha(jm),rows=nrows,exact_rows=0),parent_Uplus=e['parent_Uplus']))
out=dict(status='COMPLETE_SOURCE_BOUND_FINITE_RESEARCH_POOL_MANIFEST',manifest_checker_sha256=sha(Path(__file__)),pool_items=len(records),original_three_feature_failure_items=13,cegar_repair_items=2,exact_rows_including_possible_duplicates=exact_total,numerical_rows_including_possible_duplicates=numerical_total,feature_count=1232,records=records,generators=[dict(path=rel(BASE/n),sha256=sha(BASE/n))for n in ['add_exact_refuter.py','jitter_refuter.py']],global_optimality_proved=False,continuum_masks_excluded_by_pool=0,scope='Exact captures of isolated legal parents and numerical neighborhoods for finite LP proposal generation. They do not prove feasibility of eleven squares and do not exclude a mask. Continuum conclusions require separately certified complete exact geometry gates.')
(HERE/'refuter-pool-provenance.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['records','generators','scope']}))
