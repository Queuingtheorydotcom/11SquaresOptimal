"""Read-only ZIP metadata/header audit. Never imports or executes attachment code."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from collections import Counter
from fractions import Fraction
import hashlib, json, io
BASE=Path(__file__).resolve().parent
ZIP=Path('/home/researcher/Downloads/cases-05-to-08-results.zip')
PROJECT=BASE.parents[2]
ASSIGN=json.loads((PROJECT/'research/relay-handoff/CASE_ASSIGNMENTS.json').read_text())
JOBS={e['job_id']:e for e in ASSIGN['jobs']}
U='387708359002281417731/100000000000000000000'
B='382000000000000000000/387708359002281417731'
CHECKER='95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c'
COVER='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
WRAPPER='b101f74ced88502fc648cba2185563804298b6c965efcad6fb1c6422d043e1b1'
sha=lambda b:hashlib.sha256(b).hexdigest()
def short_header(z, member):
    with z.open(member) as stream:
        raw=stream.read(16384)
    text=raw.decode();decoder=json.JSONDecoder();i=1;out={}
    while True:
        while i<len(text) and text[i].isspace():i+=1
        if text[i:i+1] in ('}', ''):break
        try:
            key,i=decoder.raw_decode(text,i)
            while text[i].isspace():i+=1
            assert text[i]==':';i+=1
            while text[i].isspace():i+=1
            value,end=decoder.raw_decode(text,i)
        except (ValueError,IndexError):break
        if key in ('schema','node_id','parent','source','mask_index','mask','U','B','constraints','guard_source','cover_sha256','bins'):
            out[key]=value
        i=end
        while i<len(text) and text[i].isspace():i+=1
        if text[i:i+1]==',':i+=1
        else:break
    return out

def safety(n):
    p=PurePosixPath(n)
    return not p.is_absolute() and '..' not in p.parts and '\\' not in n

with ZipFile(ZIP) as z:
    infos=z.infolist();names=[x.filename for x in infos];idx={x.filename:x for x in infos}
    assert len(names)==len(set(names)), 'duplicate ZIP members'
    assert all(safety(n) for n in names), 'unsafe archive path'
    assert all((x.external_attr>>16)&0o170000!=0o120000 for x in infos), 'archive symlink'
    packets=[];cases=[];issues=[];metadata_hashed=[];dependency_records=[];header_bytes_limit=0
    for packet in ('05','06','07','08'):
        pref=f'eleven-square-middle-four/cases-{packet}-result/'
        sumsbytes=z.read(pref+'SHA256SUMS');sumrows=[line.split(maxsplit=1) for line in sumsbytes.decode().splitlines() if line.strip()]
        assert len(sumrows)==len({p for h,p in sumrows})
        sums={p:h for h,p in sumrows}
        assert all(safety(p) and len(h)==64 for p,h in sums.items())
        expected_names={pref+p for p in sums}
        actual_names={n for n in names if n.startswith(pref) and not n.endswith('/') and n!=pref+'SHA256SUMS'}
        missing=sorted(expected_names-set(names));unlisted=sorted(actual_names-expected_names)
        if missing or unlisted:issues.append(dict(packet=packet,kind='manifest_inventory',missing=missing,unlisted=unlisted))
        result_bytes=z.read(pref+'result.json');result=json.loads(result_bytes)
        assert sha(result_bytes)==sums['result.json']
        job=JOBS[f'cases-{packet}'];assigned=job['mask_indices'];rows=result['results']
        assert result['job_id']==job['job_id'] and result['parent_Uplus']==U
        assert result['status']=='complete' and result['global_optimality_proved'] is False
        assert result['assigned_mask_indices']==assigned==[r['mask_index'] for r in rows]
        assert len(assigned)==len(set(assigned))
        # Read only small metadata, not the source proof bodies.
        for n in names:
            if not n.startswith(pref):continue
            rel=n[len(pref):]
            if rel in sums and (rel in ('result.json','replay.py','proof.md','supplemental-provenance.json') or rel.endswith('-independent.json')):
                data=z.read(n);assert sha(data)==sums[rel]
                metadata_hashed.append(dict(member=n,sha256=sha(data),bytes=len(data)))
        packet_case_records=[]
        for row in rows:
            mask=row['mask_index'];saved_bytes=z.read(pref+row['independent_audit']);audit=json.loads(saved_bytes)
            assert sha(saved_bytes)==row['independent_audit_sha256']==sums[row['independent_audit']]
            assert row['status']=='proved' and row['proof_kind']=='unconditional_v9'
            assert row['mask_exclusion_proved'] is True and row['constraints']==[] and row['unresolved_obligations']==[]
            assert row['occupied_cells']==job['masks'][str(mask)]==audit['mask']==audit['required_antecedent_mask']
            assert audit['mask_index']==mask and audit['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
            assert audit['parent_Uplus']==U and audit['parent_side']==B and audit['cover_sha256']==COVER
            assert audit['source_sha256']==row['source_sha256']==sums[row['source']]
            assert row['checker_sha256']==audit['dependencies']['audit_capture_v9.py']==CHECKER
            assert audit['mask_exclusion_proved'] is True and audit['branch_exclusion_proved'] is True
            assert audit['inside_local_guard'] is False and audit['constraints']==[] and audit['global_optimality_proved'] is False
            assert audit['transferred_canonical_mask_indices']==[mask] and audit['continuum_canonical_masks_excluded']==1
            assert audit['bootstrap']['kind']=='independently_verified_wall_seed' and audit['bootstrap']['full_angle_domain']==['0','1']
            assert audit['root_audit_sha256'] is None
            required=[];node_headers=[]
            for node in audit['nodes']:
                candidates=[p for p,h in sums.items() if h==node['sha256'] and PurePosixPath(p).name==PurePosixPath(node['path']).name]
                assert len(candidates)==1,(mask,'node member',candidates)
                rel=candidates[0];member=pref+rel
                assert member in idx and node['constraints']==[] and node['inside_local_guard'] is False
                hdr=short_header(z,member);header_bytes_limit+=16384
                assert hdr['schema']=='exact_generic_owned_hull_v1' and hdr['mask_index']==mask
                assert hdr['mask']==row['occupied_cells'] and hdr['U']==U and hdr['B']==B
                assert hdr['constraints']==[] and hdr['guard_source'] is None
                assert hdr['source']['sha256']==audit['root_sha256']
                expected_parent=None if not node_headers else node_headers[-1]['sha256']
                assert (hdr['parent']['sha256'] if hdr['parent'] else None)==expected_parent
                node_headers.append(dict(member=member,sha256=node['sha256'],header=hdr))
                required.append(dict(member=member,expected_sha256=node['sha256'],bytes=idx[member].file_size,role='ancestry_node',destination_name=PurePosixPath(rel).name))
            assert node_headers[-1]['sha256']==row['source_sha256']
            assert audit['nodes'][-1]['branch_exclusion_proved'] is True
            seedcandidates=[p for p,h in sums.items() if h==audit['root_sha256'] and PurePosixPath(p).name==PurePosixPath(node_headers[-1]['header']['source']['path']).name]
            assert len(seedcandidates)==1,(mask,'seed member',seedcandidates)
            seed=pref+seedcandidates[0];assert seed in idx
            required.insert(0,dict(member=seed,expected_sha256=audit['root_sha256'],bytes=idx[seed].file_size,role='wall_seed',destination_name=PurePosixPath(seed).name))
            cover_candidates=[p for p,h in sums.items() if h==COVER and p.startswith('certificates/')]
            assert cover_candidates
            near=[p for p in cover_candidates if PurePosixPath(p).parent==PurePosixPath(row['source']).parent]
            coverrel=near[0] if near else cover_candidates[0]
            required.append(dict(member=pref+coverrel,expected_sha256=COVER,bytes=idx[pref+coverrel].file_size,role='cover',destination_name='center-cover-symmetric-exact.json'))
            required.append(dict(member=pref+row['independent_audit'],expected_sha256=row['independent_audit_sha256'],bytes=len(saved_bytes),role='saved_audit',destination_name=PurePosixPath(row['independent_audit']).name))
            assert len({r['destination_name'] for r in required})==len(required)
            record=dict(job_id=result['job_id'],mask_index=mask,occupied_cells=row['occupied_cells'],receipt_metadata_status='PASS_UNCONDITIONAL_CLAIM_AND_BINDING_METADATA',geometry_replayed_here=False,large_source_sha256_verified_here=False,result_member=pref+'result.json',result_sha256=sha(result_bytes),source_member=pref+row['source'],source_sha256=row['source_sha256'],saved_audit_member=pref+row['independent_audit'],saved_audit_sha256=row['independent_audit_sha256'],constraints=[],inside_local_guard=False,root_sha256=audit['root_sha256'],bootstrap=audit['bootstrap'],dependencies=audit['dependencies'],recorded_rational_backend=audit['rational_backend'],recorded_rational_backend_version=audit['rational_backend_version'],recorded_rational_binary_sha256=audit['rational_binary_sha256'],nodes=node_headers,stream_extract_members=required,peak_case_payload_bytes=sum(r['bytes'] for r in required),recorded_audit_seconds=audit['seconds'],recorded_audit_rows=sum(n['rows'] for n in audit['nodes']))
            cases.append(record);packet_case_records.append(record)
        packets.append(dict(job_id=result['job_id'],assigned_masks=assigned,assigned_count=len(assigned),proved_claim_count=len(rows),metadata_checked_count=len(rows),result_sha256=sha(result_bytes),sum_manifest_sha256=sha(sumsbytes),sum_manifest_entries=len(sums),missing_members=missing,unlisted_members=unlisted,source_payload_bytes=sum(c['peak_case_payload_bytes'] for c in packet_case_records)))
    # Check the small original checker/adapter bytes against all receipt dependency claims.
    common_dependencies=cases[0]['dependencies']
    assert all(c['dependencies']==common_dependencies for c in cases)
    for packet in ('05','06','07','08'):
        pref=f'eleven-square-middle-four/cases-{packet}-result/'
        if packet in ('05','07'):
            subdir='inputs' if packet=='05' else 'tools'
            tool_member=pref+subdir+'/case-tools.zip';supp_member=pref+subdir+'/case-tools-supplement.zip'
            tools={}
            for archive_member in (tool_member,supp_member):
                raw=z.read(archive_member)
                with ZipFile(io.BytesIO(raw)) as inner:
                    for info in inner.infolist():
                        assert safety(info.filename)
                        if info.filename.endswith('.py'):
                            assert info.file_size<200000
                            tools[info.filename]=(inner.read(info.filename),archive_member+'!'+info.filename)
        else:
            codepref=pref+('code/' if packet=='06' else '')
            tools={n[len(codepref):]:(z.read(n),n) for n in names if n.startswith(codepref+'research/') and n.endswith('.py')}
        wrapper=tools['research/frontier/audit_case.py'];assert sha(wrapper[0])==WRAPPER
        dependency_records.append(dict(packet=packet,role='native_GMP_wrapper',member=wrapper[1],sha256=sha(wrapper[0])))
        d=BASE/'reviewed-code'/f'cases-{packet}';d.mkdir(parents=True,exist_ok=True);(d/'audit_case.py.txt').write_bytes(wrapper[0])
        for basename,expected in common_dependencies.items():
            found=[(name,b,member) for name,(b,member) in tools.items() if PurePosixPath(name).name==basename and sha(b)==expected]
            assert len(found)==1,(packet,basename,len(found))
            name,b,member=found[0]
            dependency_records.append(dict(packet=packet,role='receipt_dependency',member=member,sha256=sha(b),bytes=len(b)))
            (d/(basename+'.txt')).write_bytes(b)
    report=dict(status='PASS_METADATA_ONLY_REPLAY_REQUIRED',archive=str(ZIP),archive_bytes=ZIP.stat().st_size,archive_sha256=None,archive_member_count=len(infos),archive_uncompressed_bytes=sum(x.file_size for x in infos),safe_member_paths=True,duplicate_members=False,packets=packets,case_count=len(cases),distinct_cases=len({c['mask_index'] for c in cases}),all_57_assignments_covered=True,all_saved_receipts_unconditional=True,all_dependency_source_bytes_match_frozen_v9=True,large_source_hashes_checked=False,geometry_replayed=False,global_optimality_proved=False,issues=issues,metadata_hashed=metadata_hashed,dependency_files_hashed=dependency_records,header_read_limit_per_node_bytes=16384,node_header_count=sum(len(c['nodes']) for c in cases),cases=cases)
    (BASE/'METADATA_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    plan=dict(status='PLANNED_NOT_EXECUTED',archive=str(ZIP),root_worker_only=True,max_concurrent_geometry_workers=1,required_checker_sha256=CHECKER,required_wrapper_sha256=WRAPPER,reuse_existing_reviewed_runtime=True,per_case_output_parent='research/finalization/returned05-08/fresh-replays',per_case_scratch_parent='research/finalization/returned05-08/scratch',retain_original_archives=True,cases=[{k:c[k] for k in ('job_id','mask_index','source_member','source_sha256','saved_audit_member','saved_audit_sha256','root_sha256','stream_extract_members','peak_case_payload_bytes','recorded_audit_seconds')} for c in cases])
    (BASE/'STREAMING_REPLAY_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],cases=len(cases),node_headers=report['node_header_count'],issues=issues,peak_case=max(cases,key=lambda c:c['peak_case_payload_bytes'])['mask_index'],peak_case_bytes=max(c['peak_case_payload_bytes'] for c in cases),largest_single_node_bytes=max(r['bytes'] for c in cases for r in c['stream_extract_members']),small_dependency_checks=len(dependency_records)),indent=2))
