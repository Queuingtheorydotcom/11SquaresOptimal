"""Proposed exact inventory binding for fresh generic v9 node audits.

This checks completeness of proof inventories, not their geometric claims.
Only the reviewed direct v9 and native cached-v9 profiles are supported.
Branch trees require their own complete partition validator.
"""
if not __debug__:
    raise SystemExit('Assertions must remain enabled for proof inventory validation.')

from collections import Counter
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import hashlib
import json
import gmpy2

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
ROOT = RESEARCH / 'phase3'
WORKSPACE = RESEARCH.parent
U = F(387708359002281417731, 10**20)
B = F(191, 50) / U
COVER = ROOT / 'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
COVER_HASH = 'df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
PINS = HERE / 'strict-inventory-pins.json'
PINS_HASH = '8a46589d35e3bbd1efce02b2a196db5ddb636a85259bf7f30d6b31daa65b01f8'
ADAPTER = RESEARCH / 'endpoint-audit/audit_native_cached.py'
ADAPTER_HASH = '9bff671e43ccb3dc1296fa740c41bfa7978d8cc924caddfbeabaac63d260f06b'
CACHED_FILES = {'audit_cached_node_v2.py', 'audit_tree_batch_v3.py'}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def referenced_path(ref, owner):
    p = Path(ref)
    candidates = [p] if p.is_absolute() else [WORKSPACE/p, Path(owner).parent/p]
    found = {q.resolve() for q in candidates if q.is_file()}
    need(len(found) == 1, 'Missing or ambiguous reference: ' + str(ref))
    return found.pop()


class Validator:
    def __init__(self):
        need(sha(PINS) == PINS_HASH, 'Changed review pin inventory')
        self.pins = json.loads(PINS.read_text())
        need(sha(COVER) == COVER_HASH, 'Changed center cover')
        cover = json.loads(COVER.read_text())
        turn = lambda J: tuple(sorted(15-i for i in J))
        self.canonical = sorted({min(J, turn(J)) for J in combinations(range(16), 11)})
        need(len(self.canonical) == 2184 and list(map(list, self.canonical)) == cover['canonical_eleven_cell_subsets'], 'Incomplete canonical cover')
        for i in range(16):
            need({tuple(1-F(v) for v in p) for p in cover['cells'][i]['vertices']} ==
                 {tuple(map(F, p)) for p in cover['cells'][15-i]['vertices']}, 'Half-turn transfer geometry differs')
        self.native_hash = sha(gmpy2.gmpy2.__file__)
        self.native_version = gmpy2.version()
        self.active = set()
        self.done = {}
        self.inputs = {}

    def read(self, path):
        path = Path(path).resolve()
        raw = path.read_bytes()
        fingerprint = hashlib.sha256(raw).hexdigest()
        need(path not in self.inputs or self.inputs[path] == fingerprint, 'Input changed while validating')
        self.inputs[path] = fingerprint
        return json.loads(raw), fingerprint

    def validate(self, path, require_exclusion=True):
        result = self._validate(Path(path).resolve())
        if require_exclusion:
            need(result['exclusion'], 'Receipt does not prove an unconditional exclusion')
        for source, fingerprint in self.inputs.items():
            need(sha(source) == fingerprint, 'Input changed while validating: ' + str(source))
        return result

    def _validate(self, path):
        r, receipt_hash = self.read(path)
        if receipt_hash in self.done:
            return self.done[receipt_hash]
        need(receipt_hash not in self.active, 'Cyclic audit-premise graph')
        self.active.add(receipt_hash)
        need(r['status'] == 'PASS_INDEPENDENT_GENERIC_HULL_AUDIT', 'Unsupported audit status')
        need(r['constraints'] == [] and r['inside_local_guard'] is False, 'Conditional/guarded generic audit')
        need(r['global_optimality_proved'] is False, 'Unexpected global claim')
        need(r['root_audit_sha256'] is None and r['bootstrap']['kind'] == 'independently_verified_wall_seed', 'Unsupported root premise')
        need(F(r['parent_Uplus']) == U and F(r['parent_side']) == B and r['cover_sha256'] == COVER_HASH, 'Wrong exact domain')
        mask, index = r['mask'], r['mask_index']
        need(type(index) is int and 0 <= index < 2184, 'Invalid mask index')
        need(mask and all(type(i) is int for i in mask) and mask == sorted(set(mask)), 'Invalid support mask')
        need(set(mask) <= set(self.canonical[index]) and r['required_antecedent_mask'] == mask, 'Antecedent mask mismatch')

        deps = r['dependencies']
        cached = bool(CACHED_FILES & set(deps))
        expected = set(self.pins) if cached else set(self.pins) - CACHED_FILES
        need(set(deps) == expected, 'Incomplete or unexpected dependency inventory')
        for name in expected:
            pin = self.pins[name]
            need(deps[name] == pin['sha256'] == sha(ROOT/pin['path']), 'Changed reviewed dependency: ' + name)
        need(r['rational_backend'] == 'gmp' and r['rational_backend_version'] == self.native_version and
             r['rational_binary_sha256'] == self.native_hash, 'Native rational backend binding differs')
        if cached:
            adapter = r['native_portability_adapter']
            need(Path(adapter['path']).resolve() == ADAPTER.resolve() and
                 adapter['sha256'] == ADAPTER_HASH == sha(ADAPTER), 'Missing/wrong native cache adapter')
        else:
            need(not r.get('premise_audits') and 'native_portability_adapter' not in r, 'Direct profile imports cached premises')

        records = r['nodes']
        need(type(records) is list and records, 'Empty node inventory')
        terminal_path = referenced_path(records[-1]['path'], path)
        terminal, terminal_hash = self.read(terminal_path)
        need(terminal_hash == r['source_sha256'], 'Terminal source binding differs')
        seed_path = referenced_path(terminal['source']['path'], terminal_path)
        seed, seed_hash = self.read(seed_path)
        need(seed_hash == r['root_sha256'] == terminal['source']['sha256'], 'Root seed binding differs')
        need(seed['schema'] == 'generic_wall_seed_v1' and seed['mask'] == mask and seed['mask_index'] == index, 'Seed antecedent differs')
        need(F(seed['U']) == U and F(seed['B']) == B, 'Seed scale differs')
        need(seed['cover_source']['sha256'] == COVER_HASH and sha(referenced_path(seed['cover_source']['path'], seed_path)) == COVER_HASH, 'Seed cover binding differs')
        need(set(seed['groups']) == set(map(str, mask)), 'Seed owner inventory differs')
        need(type(seed['bins']) is int and seed['bins'] > 0, 'Invalid seed bins')
        need(r['bootstrap']['full_angle_domain'] == ['0', '1'] and
             r['bootstrap']['angle_rows'] == len(mask)*seed['bins'], 'Root angle cover inventory differs')
        wanted_seeds = Counter((int(owner), tuple(F(x)/B for x in p))
                               for owner, points in seed['groups'].items() for p in points)
        got_seeds = Counter()
        for check in r['seed_ownership_checks']:
            need(check['passed'] is True, 'Unverified seed point')
            key = (check['owner'], tuple(map(F, check['unit_point'])))
            got_seeds[key] += 1
            if check.get('method') == 'exact_disk':
                need(F(check['maximum_vertex_distance_squared']) < F(1, 4), 'Non-strict seed disk')
            else:
                need(F(check['strict_projection_margin']) > 0, 'Non-strict wall seed')
        need(got_seeds == wanted_seeds and r['bootstrap']['seed_vertices'] == sum(wanted_seeds.values()), 'Missing/duplicated seed ownership checks')

        # Reconstruct producer ancestry independently of the supplied node list.
        chain, seen = [], set()
        node_path = terminal_path
        while True:
            node, fingerprint = self.read(node_path)
            need(fingerprint not in seen, 'Cyclic/repeated producer ancestry')
            seen.add(fingerprint)
            need(node['schema'] == 'exact_generic_owned_hull_v1' and node['guard_source'] is None, 'Unsupported/guarded producer node')
            need(node['mask'] == mask and node['mask_index'] == index and F(node['U']) == U and F(node['B']) == B, 'Ancestor antecedent differs')
            need(node['constraints'] == [] and node['final_state']['constraints'] == [], 'Branched ancestor in unconditional induction')
            need(referenced_path(node['source']['path'], node_path) == seed_path and node['source']['sha256'] == seed_hash, 'Ancestor root changed')
            final = node['final_state']
            need(final['mask'] == mask and final['mask_index'] == index and F(final['U']) == U and F(final['B']) == B, 'Ancestor final domain differs')
            need(final['source'] == node['source'] and final['guard_source'] is None and final['guard'] == {}, 'Ancestor final antecedent differs')
            need(node['mask_exclusion_proved'] is False and node['global_optimality_proved'] is False, 'Producer claiming checker status')
            need(bool(node['closed']) == bool(node['contradiction']), 'Generic closure differs from contradiction')
            chain.append((node_path, fingerprint, node))
            if node['parent'] is None:
                break
            parent = referenced_path(node['parent']['path'], node_path)
            need(sha(parent) == node['parent']['sha256'], 'Producer parent hash differs')
            node_path = parent
        chain.reverse()
        need(len(records) == len(chain), 'Missing or extraneous ancestry node')
        record_hashes = set()
        for record, (node_path, fingerprint, node) in zip(records, chain):
            need(referenced_path(record['path'], path) == node_path and record['sha256'] == fingerprint and fingerprint not in record_hashes, 'Node inventory order/hash/uniqueness differs')
            record_hashes.add(fingerprint)
            need(record['node'] == node['node_id'] and record['constraints'] == [], 'Node receipt identity/antecedent differs')
            need(record['branch_exclusion_proved'] is bool(node['contradiction']) and record['inside_local_guard'] is False, 'Node receipt conclusion differs')
            need(record['rows'] == sum(len(s['rows']) for s in node['steps']) and
                 record['complete_steps'] == sum(bool(s['complete']) for s in node['steps']), 'Truncated node row/step inventory')
            for key in ('rows', 'complete_steps', 'arrangement_slabs', 'promoted_grid_vertices'):
                need(type(record[key]) is int and record[key] >= 0, 'Invalid node statistic')
        need(r['final_state_sha256'] == digest(terminal['final_state']), 'Final-state digest differs')
        excluded = bool(terminal['contradiction'])
        need(r['branch_exclusion_proved'] is excluded and r['mask_exclusion_proved'] is excluded, 'Top-level conclusion differs')
        if excluded:
            need(terminal['terminal'] is True and terminal['closed'] is True, 'Exclusion source is unfinished')

        premise_results = {}
        for premise in r.get('premise_audits', []):
            premise_path = referenced_path(premise['path'], path)
            fingerprint = sha(premise_path)
            need(fingerprint == premise['sha256'] and fingerprint not in premise_results, 'Changed/duplicate premise receipt')
            proved = self._validate(premise_path)
            need(proved['root_sha256'] == seed_hash and proved['mask'] == mask, 'Cached premise root differs')
            premise_results[fingerprint] = proved
        used_premises = set()
        for record in records:
            if 'cached_from_audit_sha256' not in record:
                continue
            fingerprint = record['cached_from_audit_sha256']
            need(cached and fingerprint in premise_results, 'Orphaned cached node')
            source_records = premise_results[fingerprint]['records']
            need(record['sha256'] in source_records, 'Cached node absent from its proved premise')
            strip_cache = lambda x: {k:v for k,v in x.items() if k != 'cached_from_audit_sha256'}
            need(strip_cache(record) == strip_cache(source_records[record['sha256']]), 'Cached node receipt changed')
            used_premises.add(fingerprint)
        need(used_premises == set(premise_results), 'Unused/extraneous cached premise')
        if cached:
            need(r['rows_replayed_this_run'] == sum(n['rows'] for n in records if 'cached_from_audit_sha256' not in n) and
                 r['rows_in_cached_premises'] == sum(n['rows'] for n in records if 'cached_from_audit_sha256' in n), 'Fresh/cached row totals differ')
        cases = {i for i,J in enumerate(self.canonical)
                 if set(mask) <= set(J) or set(mask) <= {15-j for j in J}} if excluded else set()
        need(r['transferred_canonical_mask_indices'] == sorted(cases) and r['continuum_canonical_masks_excluded'] == len(cases), 'Transfer inventory differs')
        result = dict(exclusion=excluded, mask=mask, mask_index=index, cases=cases,
                      source=str(terminal_path), source_sha256=terminal_hash,
                      root_sha256=seed_hash, audit=str(path), audit_sha256=receipt_hash,
                      nodes=len(chain), records={n['sha256']:n for n in records},
                      dependency_profile='native_cached_v9' if cached else 'direct_v9')
        self.active.remove(receipt_hash)
        self.done[receipt_hash] = result
        return result


def validate(path, require_exclusion=True):
    return Validator().validate(path, require_exclusion)
