"""Mutation controls for the complete native center-partition inventory."""
from copy import deepcopy
from pathlib import Path
import json
import time
from strict_generic_inventory import sha
from strict_tree_inventory import validate, DEFAULT_TREE
HERE=Path(__file__).resolve().parent
OUT=HERE/'tree-inventory-mutations'
OUT.mkdir(exist_ok=True)
AUDIT=HERE.parent/'endpoint-audit/mask1383-final-independent-tree-audit.json'
original=json.loads(AUDIT.read_text())
tree=json.loads(DEFAULT_TREE.read_text())

def main():
    start=time.monotonic()
    tests=[]
    def add(name, mutate_audit=None, mutate_tree=None):
        a=deepcopy(original);t=deepcopy(tree)
        if mutate_audit:mutate_audit(a)
        if mutate_tree:mutate_tree(t)
        tp=DEFAULT_TREE
        if mutate_tree:
            tp=OUT/(name+'-tree.json');tp.write_text(json.dumps(t,indent=2)+'\n')
            a['tree_sha256']=sha(tp)
        ap=OUT/(name+'-audit.json');ap.write_text(json.dumps(a,indent=2)+'\n')
        tests.append((name,ap,tp))
    add('false_complete',lambda a:a.update(complete=False))
    add('unresolved_leaf',lambda a:a.update(unresolved_leaf_ids=['r.ge']))
    add('missing_dependency',lambda a:a['dependencies'].pop('audit_tree_batch_v4.py'))
    add('missing_adapter',lambda a:a['native_portability_adapters'].pop())
    add('wrong_native_backend',lambda a:a.update(rational_binary_sha256='0'*64))
    add('missing_root_premise',lambda a:a.update(premise_audits=[]))
    add('one_closed_leaf_omitted',lambda a:a['checked_leaves'].pop())
    add('terminal_nodes_only',lambda a:a.update(nodes=[n for n in a['nodes'] if n['branch_exclusion_proved']]))
    add('cached_ancestor_omitted',lambda a:a['nodes'].pop(0))
    add('duplicated_record',lambda a:a['nodes'].append(deepcopy(a['nodes'][-1])))
    add('bad_cached_origin',lambda a:a['nodes'][0].update(cached_from_audit_sha256='0'*64))
    add('wrong_fresh_row_total',lambda a:a.update(rows_replayed_this_run=1))
    add('tree_missing_half',mutate_tree=lambda t:t['nodes']['r']['split']['children'].pop('ge'))
    add('tree_duplicate_half',mutate_tree=lambda t:t['nodes']['r']['split']['children'].update(ge='r.le'))
    add('tree_missing_leaf_node',mutate_tree=lambda t:t['nodes'].pop('r.ge'))
    add('tree_changed_threshold',mutate_tree=lambda t:t['nodes']['r']['split'].update(bound_centered_unit='3/2'))
    add('tree_wrong_child_source',mutate_tree=lambda t:t['nodes']['r.ge'].update(receipt=deepcopy(t['nodes']['r.le']['receipt'])))
    add('tree_wrong_parent',mutate_tree=lambda t:t['nodes']['r.ge'].update(parent='r.le'))
    add('tree_unreachable_extra_leaf',mutate_tree=lambda t:t['nodes'].update(extra=deepcopy(t['nodes']['r.le'])))
    controls=[]
    for name,ap,tp in tests:
        began=time.monotonic()
        try:
            validate(ap,tp)
        except (ValueError,KeyError) as e:
            result=dict(name=name,rejected=True,reason=type(e).__name__+': '+str(e),audit_sha256=sha(ap),tree_sha256=sha(tp),seconds=time.monotonic()-began)
        else:
            raise AssertionError('Malformed tree accepted: '+name)
        controls.append(result)
        (HERE/'tree-inventory-mutation-controls.json').write_text(json.dumps(dict(status='RUNNING',controls=controls),indent=2)+'\n')
        print(name,'REJECTED',result['reason'],flush=True)
    authentic=validate(AUDIT,DEFAULT_TREE)
    result=dict(status='PASS_COMPLETE_TREE_INVENTORY_MUTATION_CONTROLS',controls=controls,
                controls_rejected=len(controls),validator_sha256=sha(HERE/'strict_tree_inventory.py'),
                generic_validator_sha256=sha(HERE/'strict_generic_inventory.py'),
                authentic_audit_sha256=authentic['audit_sha256'],authentic_tree_sha256=authentic['source_sha256'],
                authentic_nodes=authentic['nodes'],authentic_leaves=authentic['leaves'],authentic_cases=sorted(authentic['cases']),
                seconds=time.monotonic()-start,scope='Inventory and exact partition controls; geometric replay is separate.')
    (HERE/'tree-inventory-mutation-controls.json').write_text(json.dumps(result,indent=2)+'\n')
    print('ALL CONTROLS PASS',flush=True)
if __name__=='__main__':main()
