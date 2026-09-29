"""Inspect small returned records and bounded JSON headers; execute no archive code."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from fractions import Fraction
import hashlib
import json

D = Path(__file__).resolve().parent
ARCHIVE = Path('/home/researcher/Downloads/eleven-square-cases-09-12.zip')
CHECKER = '95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c'
COVER = 'df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
U = Fraction(387708359002281417731, 10**20)
sha = lambda b: hashlib.sha256(b).hexdigest()


def header(z, name):
    with z.open(name) as stream:
        s = stream.read(8192).decode()
    decoder = json.JSONDecoder()
    p = s.index('{') + 1
    result = {}
    while True:
        while s[p].isspace() or s[p] == ',':
            p += 1
        key, p = decoder.raw_decode(s, p)
        while s[p].isspace():
            p += 1
        assert s[p] == ':'
        p += 1
        while s[p].isspace():
            p += 1
        if key in ('initial', 'world', 'steps', 'groups', 'cells'):
            return result
        value, p = decoder.raw_decode(s, p)
        result[key] = value


def main():
    records = []
    replay_cases = []
    packet_summaries = []
    headers_checked = 0
    small_bytes = 0
    with ZipFile(ARCHIVE) as z:
        info = z.infolist()
        names = set(z.namelist())
        assert len(names) == len(info)
        assert not any(Path(n).is_absolute() or '..' in Path(n).parts for n in names)
        assignments_bytes = z.read('handoff/CASE_ASSIGNMENTS.json')
        assignments = json.loads(assignments_bytes)
        jobs = {j['job_id']: j for j in assignments['jobs']}
        tools_bytes = z.read('cases-09-result/case-tools.zip')
        small_bytes += len(tools_bytes) + len(assignments_bytes)
        with ZipFile(BytesIO(tools_bytes)) as tools:
            tool_names = tools.namelist()
            assert not any(Path(n).is_absolute() or '..' in Path(n).parts for n in tool_names)
            checker_bytes = tools.read('research/phase3/work/phase3/hull/audit_capture_v9.py')
            assert sha(checker_bytes) == CHECKER
            dependencies = {}
            for n in tool_names:
                if n.endswith('.py'):
                    b = tools.read(n)
                    dependencies.setdefault(Path(n).name, set()).add(sha(b))
            cover_bytes = tools.read('research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json')
            assert sha(cover_bytes) == COVER
            canonical = json.loads(cover_bytes)['canonical_eleven_cell_subsets']

        seen = set()
        for packet in range(9, 13):
            prefix = f'cases-{packet:02d}-result/'
            ledger_bytes = z.read(prefix+'result.json')
            ledger = json.loads(ledger_bytes)
            sums_bytes = z.read(prefix+'SHA256SUMS')
            sums = {}
            for line in sums_bytes.decode().splitlines():
                h, name = line.split('  ', 1)
                assert name not in sums and len(h) == 64
                assert not Path(name).is_absolute() and '..' not in Path(name).parts
                sums[name] = h
            actual = {n[len(prefix):] for n in names if n.startswith(prefix) and not n.endswith('/') and n != prefix+'SHA256SUMS'}
            assert set(sums) == actual
            assert sha(ledger_bytes) == sums['result.json']
            job = jobs[f'cases-{packet:02d}']
            expected = job['mask_indices']
            assert ledger['status'] == 'complete'
            assert ledger['assigned_mask_indices'] == expected
            assert [r['mask_index'] for r in ledger['results']] == expected
            assert len(expected) == 14
            assert Fraction(ledger['parent_Uplus']) == U
            assert ledger['global_optimality_proved'] is False
            tool_name = ('programs/' if packet == 11 else '')+'case-tools.zip'
            other_tools = z.read(prefix+tool_name)
            assert sha(other_tools) == sha(tools_bytes) == sums[tool_name]
            packet_rows = 0
            for row in ledger['results']:
                i = row['mask_index']
                assert i not in seen
                seen.add(i)
                assert row['occupied_cells'] == job['masks'][str(i)] == canonical[i]
                assert row['status'] == 'proved' and row['mask_exclusion_proved'] is True
                assert row['constraints'] == [] and row['unresolved_obligations'] == []
                assert row['checker_sha256'] == CHECKER
                assert sums[row['source']] == row['source_sha256']
                audit_bytes = z.read(prefix+row['independent_audit'])
                small_bytes += len(audit_bytes)
                assert sha(audit_bytes) == row['independent_audit_sha256'] == sums[row['independent_audit']]
                audit = json.loads(audit_bytes)
                assert audit['status'] == 'PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
                assert audit['mask_exclusion_proved'] is True and audit['branch_exclusion_proved'] is True
                assert audit['constraints'] == [] and audit['inside_local_guard'] is False
                assert audit['mask_index'] == i and audit['mask'] == canonical[i]
                assert audit['required_antecedent_mask'] == canonical[i]
                assert audit['transferred_canonical_mask_indices'] == [i]
                assert audit['continuum_canonical_masks_excluded'] == 1
                assert Fraction(audit['parent_Uplus']) == U
                assert Fraction(audit['parent_side'])*U == Fraction(191, 50)
                assert audit['source_sha256'] == row['source_sha256']
                assert audit['cover_sha256'] == COVER
                assert audit['root_audit_sha256'] is None
                assert audit['bootstrap']['kind'] == 'independently_verified_wall_seed'
                assert audit['bootstrap']['full_angle_domain'] == ['0', '1']
                assert not audit.get('premise_audits')
                assert audit['rational_backend'] == 'gmp' and audit['rational_backend_version'] == '2.3.1'
                for name, h in audit['dependencies'].items():
                    assert h in dependencies[name], (i, name, h)
                for node in audit['nodes']:
                    assert 'cached_from_audit_sha256' not in node
                    assert node['constraints'] == []
                    assert node['complete_steps'] > 0 and node['rows'] > 0
                nodes = {n['sha256']: n for n in audit['nodes']}
                assert len(nodes) == len(audit['nodes'])
                node_paths = {}
                for h, node in nodes.items():
                    matching = [n for n in sums if Path(n).name == Path(node['path']).name]
                    assert len(matching) == 1
                    relative = matching[0]
                    assert sums[relative] == h
                    node_paths[h] = relative
                assert row['source_sha256'] in nodes
                chain = []
                current = row['source_sha256']
                while current is not None:
                    assert current not in chain
                    chain.append(current)
                    h = header(z, prefix+node_paths[current])
                    headers_checked += 1
                    assert h['schema'] == 'exact_generic_owned_hull_v1'
                    assert h['mask_index'] == i and h['mask'] == canonical[i]
                    assert h['constraints'] == [] and h['guard_source'] is None
                    assert Fraction(h['U']) == U and Fraction(h['B'])*U == Fraction(191, 50)
                    assert h['source']['sha256'] == audit['root_sha256']
                    seed_candidates = [n for n in sums if Path(n).name == Path(h['source']['path']).name]
                    assert len(seed_candidates) == 1
                    seed_path = seed_candidates[0]
                    assert sums[seed_path] == audit['root_sha256']
                    parent = h['parent']
                    if parent is None:
                        current = None
                    else:
                        assert parent['sha256'] in nodes
                        assert Path(parent['path']).name == Path(node_paths[parent['sha256']]).name
                        current = parent['sha256']
                assert set(chain) == set(nodes)
                seed = header(z, prefix+seed_path)
                headers_checked += 1
                assert seed['schema'] == 'generic_wall_seed_v1'
                assert seed['mask_index'] == i and seed['mask'] == canonical[i]
                assert Fraction(seed['U']) == U and Fraction(seed['B'])*U == Fraction(191, 50)
                local = D/'references'/prefix/row['independent_audit']
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_bytes(audit_bytes)
                count = sum(n['rows'] for n in nodes.values())
                packet_rows += count
                records.append({'packet': packet, 'mask_index': i,
                    'occupied_cells': canonical[i], 'source': prefix+row['source'],
                    'declared_source_sha256': row['source_sha256'],
                    'independent_audit': prefix+row['independent_audit'],
                    'verified_audit_sha256': sha(audit_bytes),
                    'declared_root_seed_sha256': audit['root_sha256'],
                    'supplied_ancestry_nodes': len(nodes), 'declared_exact_rows': count,
                    'constraints': [], 'receipt_claims_unconditional_exclusion': True,
                    'large_source_and_seed_bytes_hashed_here': False,
                    'geometry_replayed_here': False,
                    'runtime_binary_sha256': audit['rational_binary_sha256'],
                    'saved_audit_seconds': audit['seconds']})
                cover_member = prefix+str(Path(seed_path).parent/'center-cover-symmetric-exact.json')
                if cover_member not in names:
                    cover_member = 'cases-09-result/certificates/center-cover-symmetric-exact.json'
                members = [(prefix+seed_path, audit['root_sha256'], 'wall_seed')]
                members += [(prefix+node_paths[h], h, 'ancestry_node') for h in reversed(chain)]
                members += [(cover_member, COVER, 'cover'),
                            (prefix+row['independent_audit'], sha(audit_bytes), 'saved_audit')]
                replay_cases.append({
                    'job_id': f'cases-{packet:02d}', 'mask_index': i, 'mask': canonical[i],
                    'archive': str(ARCHIVE), 'root_prefix': prefix.rstrip('/'),
                    'source_member': prefix+row['source'], 'source_sha256': row['source_sha256'],
                    'saved_audit_member': prefix+row['independent_audit'], 'saved_audit_sha256': sha(audit_bytes),
                    'root_sha256': audit['root_sha256'],
                    'stream_extract_members': [
                        {'member': member, 'expected_sha256': digest, 'bytes': z.getinfo(member).file_size,
                         'role': role, 'destination_name': Path(member).name}
                        for member, digest, role in members],
                    'peak_case_payload_bytes': sum(z.getinfo(member).file_size for member, _, _ in members),
                    'recorded_audit_seconds': audit['seconds'],
                    'recorded_rows': count, 'constraints': [],
                })
            packet_summaries.append({'packet': packet, 'assigned_cases': expected,
                                     'receipts_checked': 14, 'declared_rows': packet_rows,
                                     'result_sha256': sha(ledger_bytes), 'manifest_member_inventory_complete': True})
        assert len(seen) == 56 and seen.isdisjoint(assignments['candidate_masks'])
        strict = json.loads((D.parents[1]/'frontier/union-snapshot-93856c2b8cd8.json').read_text())
        all_jobs = {i for j in assignments['jobs'] for i in j['mask_indices']}
        missing_pre_handoff = sorted(set(range(2184))-set(strict['excluded_canonical_mask_indices'])-all_jobs-set(assignments['candidate_masks']))
        result = {
            'status': 'PASS_SMALL_RECORD_AND_SOURCE_REVIEW_PENDING_LARGE_TRACE_HASHES',
            'archive': str(ARCHIVE), 'archive_bytes': ARCHIVE.stat().st_size,
            'archive_sha256_checked_here': False, 'member_count': len(info),
            'total_uncompressed_bytes': sum(i.file_size for i in info),
            'metadata_inspection_only': True, 'attachment_code_executed': False,
            'full_archive_extracted': False, 'geometry_replayed': False,
            'frozen_checker_sha256': CHECKER, 'shared_case_tools_sha256': sha(tools_bytes),
            'bounded_json_headers_checked': headers_checked,
            'packet_summaries': packet_summaries, 'case_records': records,
            'distinct_packet_cases': sorted(seen), 'global_optimality_proved': False,
            'global_composition': {
                'last_strict_exclusions': 1997, 'latest_receipt_count_exclusions': 2007,
                'assigned_noncandidate_cases_all_12_packets': len(all_jobs),
                'candidate_cases': assignments['candidate_masks'],
                'pre_handoff_cases_requiring_strict_merge': missing_pre_handoff,
                'conditional_total_noncandidate_exclusions': 2007+len(all_jobs),
                'scope': 'All 12 assignments plus the verified 2007-case pre-handoff union would leave exactly the four candidate patterns; packets 09-12 alone establish no such global inventory.'},
            'pending': ['Hash every complete large producer and seed member against its manifest and claimed bindings.',
                        'Complete the source-bound global exclusion inventory, including the ten pre-handoff strict-merge cases.',
                        'Keep saved receipt review distinct from any fresh geometric replay.',
                        'Complete all four candidate-case capture and exact chart/orbit obligations before claiming optimality.'],
        }
        (D/'metadata-review.json').write_text(json.dumps(result, indent=2)+'\n')
        plan = {
            'status': 'PLANNED_NOT_EXECUTED', 'archive': str(ARCHIVE),
            'root_worker_only': True, 'max_concurrent_geometry_workers': 1,
            'required_checker_sha256': CHECKER,
            'required_wrapper_sha256': 'b101f74ced88502fc648cba2185563804298b6c965efcad6fb1c6422d043e1b1',
            'reuse_existing_reviewed_runtime': True,
            'per_case_output_parent': 'research/finalization/returned09-12/fresh-replays',
            'per_case_scratch_parent': 'research/finalization/returned09-12/scratch',
            'retain_original_archives': True,
            'recorded_audit_seconds_sum': sum(r['recorded_audit_seconds'] for r in replay_cases),
            'source_and_seed_full_member_hashes_require_verification_during_streaming': True,
            'cases': replay_cases,
        }
        (D/'STREAMING_REPLAY_PLAN.json').write_text(json.dumps(plan, indent=2)+'\n')
        print(json.dumps({k: result[k] for k in ['status','bounded_json_headers_checked','packet_summaries','global_composition']},indent=2))


if __name__ == '__main__':
    main()
