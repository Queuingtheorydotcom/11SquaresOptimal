"""Complete inventory binding for the reviewed native v4 center-split profile.

Geometry replay remains the obligation of the source-pinned audit receipts.
This module independently checks their exhaustive partition and dependencies.
"""
from pathlib import Path
from fractions import Fraction as F
from strict_generic_inventory import Validator, need, sha, referenced_path, ROOT, RESEARCH, U, B, COVER_HASH, ADAPTER, ADAPTER_HASH, CACHED_FILES

TREE_DEP = ROOT / 'work/phase3/hull/audit_tree_batch_v4.py'
TREE_DEP_HASH = '04ceb52e087c7e2fec72a512bffb4b147e99391898d6ce1491215965bb715f8a'
TREE_ADAPTER = RESEARCH / 'endpoint-audit/audit_native_tree.py'
TREE_ADAPTER_HASH = '32ed54cabef554a3cfe2f795e8ff81a6b7d143b996dbeb1b096b4cae5fa1a3cb'
DEFAULT_TREE = RESEARCH / 'endpoint-audit/mask1383-two-branch-tree.json'


def validate(path, tree_path=None, validator=None):
    v = validator or Validator()
    path = Path(path).resolve()
    tree_path = Path(tree_path or DEFAULT_TREE).resolve()
    loaded = {}
    def read(p):
        p = Path(p).resolve()
        if p not in loaded:
            loaded[p] = v.read(p)
        return loaded[p]
    r, audit_hash = read(path)
    tree, tree_hash = read(tree_path)
    need(r['status'] == 'PASS_INDEPENDENT_PARTIAL_TREE_AUDIT', 'Unsupported tree audit profile')
    need(r['complete'] is True and r['mask_exclusion_proved'] is True and
         r['mask_reduced_to_local_guard'] is False and r['global_optimality_proved'] is False and
         r['generic_mode'] is True and r['unresolved_leaf_ids'] == [], 'Tree audit is incomplete or conditional')
    need(r['tree_sha256'] == tree_hash and tree['schema'] == 'generic_binary_partition_tree_v1', 'Tree binding differs')
    need(r['root_audit_sha256'] is None, 'Unsupported tree root premise')
    mask, index = r['mask'], r['mask_index']
    need(type(index) is int and 0 <= index < 2184 and mask == sorted(set(mask)) and
         all(type(i) is int for i in mask) and set(mask) <= set(v.canonical[index]) and
         r['required_antecedent_mask'] == mask == tree['mask'] and tree['mask_index'] == index, 'Tree antecedent differs')
    need(F(r['parent_Uplus']) == U and F(r['parent_side']) == B and r['cover_sha256'] == COVER_HASH, 'Wrong tree exact domain')
    expected_deps = set(v.pins) - CACHED_FILES | {TREE_DEP.name}
    need(set(r['dependencies']) == expected_deps, 'Incomplete tree dependency inventory')
    for name in expected_deps:
        dep, pin = ((TREE_DEP, TREE_DEP_HASH) if name == TREE_DEP.name else
                    (ROOT/v.pins[name]['path'], v.pins[name]['sha256']))
        need(r['dependencies'][name] == pin == sha(dep), 'Changed reviewed tree dependency: ' + name)
    # audit_native_cached imports these two modules before exposing its
    # dependency checker; bind the adapter's transitive executable imports.
    for name in CACHED_FILES:
        pin = v.pins[name]
        need(sha(ROOT/pin['path']) == pin['sha256'], 'Changed native adapter import: ' + name)
    need(r['rational_backend'] == 'gmp' and r['rational_backend_version'] == v.native_version and
         r['rational_binary_sha256'] == v.native_hash, 'Tree native rational backend differs')
    adapters = r['native_portability_adapters']
    wanted = {TREE_ADAPTER.resolve(): TREE_ADAPTER_HASH, ADAPTER.resolve(): ADAPTER_HASH}
    need(len(adapters) == len(wanted), 'Missing/extra tree native adapter')
    seen = set()
    for item in adapters:
        p = referenced_path(item['path'], path)
        need(p in wanted and p not in seen and item['sha256'] == wanted[p] == sha(p), 'Wrong/duplicate tree native adapter')
        seen.add(p)

    seed_path = referenced_path(tree['root_source']['path'], tree_path)
    _, seed_hash = read(seed_path)
    need(seed_hash == r['root_sha256'] == tree['root_source']['sha256'], 'Tree root seed binding differs')
    root_path = referenced_path(tree['root_receipt']['path'], tree_path)
    root, root_hash = read(root_path)
    need(tree['root_receipt']['sha256'] == root_hash and root['constraints'] == [], 'Tree root receipt is conditional or changed')
    premises = {}
    for item in r['premise_audits']:
        p = referenced_path(item['path'], path)
        need(sha(p) == item['sha256'] and item['sha256'] not in premises, 'Changed/duplicate tree premise')
        proved = v._validate(p)
        need(proved['root_sha256'] == seed_hash and proved['mask'] == mask and proved['mask_index'] == index, 'Tree premise antecedent differs')
        premises[item['sha256']] = proved
    need(any(p['source_sha256'] == root_hash for p in premises.values()), 'Tree root is not independently verified unconditionally')

    producers = {}
    def chain(terminal_path, allowed):
        result, visited = [], set()
        p = terminal_path
        while True:
            node, h = read(p)
            need(h not in visited, 'Cyclic tree producer ancestry')
            visited.add(h)
            need(node['schema'] == 'exact_generic_owned_hull_v1' and node['guard_source'] is None, 'Unsupported tree producer')
            need(node['mask'] == mask and node['mask_index'] == index and F(node['U']) == U and F(node['B']) == B, 'Tree producer antecedent differs')
            constraints = node['constraints']
            need(type(constraints) is list and constraints == allowed[:len(constraints)] and len(constraints) <= len(allowed), 'Extraneous producer branch assumption')
            need(referenced_path(node['source']['path'], p) == seed_path and node['source']['sha256'] == seed_hash, 'Tree producer root differs')
            final = node['final_state']
            need(final['constraints'] == constraints and final['mask'] == mask and final['mask_index'] == index and F(final['U']) == U and F(final['B']) == B, 'Tree final state antecedent differs')
            need(final['source'] == node['source'] and final['guard_source'] is None and final['guard'] == {}, 'Tree final root/guard differs')
            need(node['mask_exclusion_proved'] is False and node['global_optimality_proved'] is False and bool(node['closed']) == bool(node['contradiction']), 'Tree producer checker/closure claim differs')
            need(h not in producers or producers[h][0] == p, 'Producer aliased by multiple paths')
            producers[h] = (p, node)
            result.append((h, node))
            if node['parent'] is None:
                need(constraints == [], 'Conditional tree bootstrap')
                break
            parent = referenced_path(node['parent']['path'], p)
            need(sha(parent) == node['parent']['sha256'], 'Changed tree producer parent')
            p = parent
        result.reverse()
        for (_, parent), (_, child) in zip(result, result[1:]):
            need(parent['constraints'] == child['constraints'][:len(parent['constraints'])], 'Branch assumptions disappear in producer ancestry')
        return result

    nodes = tree['nodes']
    need(type(nodes) is dict and nodes and 'r' in nodes and nodes['r']['parent'] is None, 'Missing tree root')
    need(nodes['r']['receipt'] == tree['root_receipt'], 'Tree root identities differ')
    seen_tree, leaves = set(), []
    def visit(name, conditions, parent_receipt=None):
        need(name in nodes and name not in seen_tree, 'Missing/repeated tree node')
        seen_tree.add(name)
        n = nodes[name]
        p = referenced_path(n['receipt']['path'], tree_path)
        node, h = read(p)
        need(h == n['receipt']['sha256'], 'Changed tree node source')
        ancestry = chain(p, conditions)
        need(node['constraints'] == conditions, 'Tree receipt does not match its exact partition branch')
        ancestry_hashes = [a for a, _ in ancestry]
        need(root_hash in ancestry_hashes and (parent_receipt is None or parent_receipt in ancestry_hashes), 'Tree branch does not descend from partition parent')
        if n['status'] == 'SPLIT':
            need(not node['contradiction'], 'Already contradicted split node')
            split = n['split']
            need(split['kind'] == 'center' and type(split['owner']) is int and split['owner'] in mask and
                 type(split['axis']) is int and split['axis'] in (0, 1), 'Unsupported partition kind/owner/axis')
            need(set(split['children']) == {'le', 'ge'} and len(set(split['children'].values())) == 2, 'Partition does not contain both distinct closed halves')
            bound = F(split['bound_centered_unit'])
            for side, sign in (('le', 1), ('ge', -1)):
                child = split['children'][side]
                need(child in nodes and nodes[child]['parent'] == name and nodes[child]['side'] == side, 'Partition child linkage differs')
                normal = [0, 0]
                normal[split['axis']] = sign
                # Field centers are B*(unit-center + U/2); opposite signs at
                # the same exact threshold prove an exhaustive closed cover.
                constraint = dict(owner=split['owner'], normal=normal,
                                  upper_field=str(sign*B*(U/2+bound)), axis=split['axis'],
                                  bound_centered_unit=str(bound), keep=side)
                visit(child, conditions+[constraint], h)
        else:
            need(n['status'] == 'CLOSED_BY_CONTRADICTION' and node['closed'] is True and
                 node['terminal'] is True and bool(node['contradiction']), 'Unproved/open tree leaf')
            leaves.append(dict(id=name, receipt_sha256=h, branch_exclusion_proved=True, inside_local_guard=False))
    visit('r', [])
    need(seen_tree == set(nodes), 'Unreachable extra tree node')
    need(r['checked_leaves'] == leaves and r['closed_leaves_in_snapshot'] == len(leaves), 'Missing/duplicated tree leaf receipt')

    records = r['nodes']
    need(type(records) is list and len(records) == len(producers), 'Missing/extra tree ancestry record')
    seen_records, used_premises = set(), set()
    for record in records:
        h = record['sha256']
        need(h in producers and h not in seen_records, 'Missing/duplicated tree ancestry identity')
        p, node = producers[h]
        need(referenced_path(record['path'], path) == p, 'Tree ancestry path differs')
        if node['parent'] is not None:
            need(node['parent']['sha256'] in seen_records, 'Tree ancestry records are out of induction order')
        seen_records.add(h)
        need(record['node'] == node['node_id'] and record['constraints'] == node['constraints'] and
             record['branch_exclusion_proved'] is bool(node['contradiction']) and record['inside_local_guard'] is False, 'Tree node audit antecedent/conclusion differs')
        need(record['rows'] == sum(len(s['rows']) for s in node['steps']) and record['complete_steps'] == sum(bool(s['complete']) for s in node['steps']), 'Truncated tree node row/step inventory')
        for key in ('rows', 'complete_steps', 'arrangement_slabs', 'promoted_grid_vertices'):
            need(type(record[key]) is int and record[key] >= 0, 'Invalid tree node statistic')
        if 'cached_from_audit_sha256' in record:
            cache = record['cached_from_audit_sha256']
            need(cache in premises and h in premises[cache]['records'], 'Orphaned cached tree induction')
            stripped = lambda d: {k:v for k,v in d.items() if k != 'cached_from_audit_sha256'}
            need(stripped(record) == stripped(premises[cache]['records'][h]), 'Cached tree record changed')
            used_premises.add(cache)
    need(used_premises == set(premises), 'Unused tree premise')
    need(r['rows_replayed_this_run'] == sum(n['rows'] for n in records if 'cached_from_audit_sha256' not in n) and
         r['rows_in_cached_premises'] == sum(n['rows'] for n in records if 'cached_from_audit_sha256' in n), 'Fresh/cached tree row totals differ')
    cases = {i for i,J in enumerate(v.canonical) if set(mask) <= set(J) or set(mask) <= {15-j for j in J}}
    need(r['transferred_canonical_mask_indices'] == sorted(cases) and r['continuum_canonical_masks_excluded'] == len(cases), 'Tree transfer inventory differs')
    for p,h in v.inputs.items():
        need(sha(p) == h, 'Input changed during tree inventory validation')
    return dict(exclusion=True, mask=mask, mask_index=index, cases=cases, source=str(tree_path),
                source_sha256=tree_hash, root_sha256=seed_hash, audit=str(path), audit_sha256=audit_hash,
                nodes=len(producers), leaves=len(leaves), records={n['sha256']:n for n in records},
                dependency_profile='native_cached_v4_center_partition')
