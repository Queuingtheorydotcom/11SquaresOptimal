#!/usr/bin/env python3
"""Independent tree-wrapper controls using frozen real branch topology.

Only topology, halfspace partitions and path/premise bindings are exercised;
node geometry is proved by separate full induction replays.
"""
import copy,hashlib,json
from pathlib import Path
from types import SimpleNamespace
import audit_tree_batch_v4 as c
a=c.a
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=Path(__file__).with_name('tree438v3-final-audit-snapshot.json');tree=json.loads(p.read_text())
 source=a.locate(tree['root_source']['path'],p);root=json.loads(source.read_text())
 r=SimpleNamespace(mask=root['mask'],source_hash=sha(source),U=a.F(root['parent_Uplus']),B=a.F(root['parent_side']),root=root)
 closed,unresolved=c.check_partition(tree,p,r);assert len(closed)==20 and len(unresolved)==4
 controls=[]
 def reject(name,bad):
  try:c.check_partition(bad,p,r)
  except (AssertionError,KeyError):controls.append(name)
  else:raise AssertionError('False partition accepted: '+name)
 bad=copy.deepcopy(tree);children=bad['nodes']['r']['split']['children'];children['ge']=children['le'];reject('duplicate_children',bad)
 bad=copy.deepcopy(tree);del bad['nodes'][bad['nodes']['r']['split']['children']['le']];reject('missing_child',bad)
 bad=copy.deepcopy(tree);bad['nodes']['disconnected']=dict(status='PENDING',parent=None);reject('disconnected_extra_node',bad)
 bad=copy.deepcopy(tree);left=bad['nodes']['r']['split']['children']['le'];bad['nodes'][left]['side']='ge';reject('incorrect_child_side',bad)
 bad=copy.deepcopy(tree);bad['nodes']['r']['split']['children']['le']='r';reject('cycle',bad)
 bad=copy.deepcopy(tree);s=bad['nodes']['r']['split'];key='bound_half_angle' if s.get('kind')=='half_angle' else 'bound_centered_unit';s[key]=str(a.F(s[key])+a.F(1,10**50));reject('tiny_bound_change_breaks_leaf_path',bad)
 bad=copy.deepcopy(tree);node=next(n for n in bad['nodes'].values() if n.get('split',{}).get('kind')=='half_angle');node['split']['bound_half_angle']='2';reject('angular_cut_outside_allowed_interval',bad)
 out=dict(status='PASS_EXACT_TREE_PARTITION_CONTROLS',wrapper_sha256=sha(c.__file__),input_sha256=sha(p),
          valid_nodes=len(tree['nodes']),closed_leaves=20,unresolved_leaves=4,rejected_mutations=controls,
          scope='Exhaustive binary topology and source-bound path constraints only; leaf geometry requires the separate induction audit.')
 Path(__file__).with_name('tree-partition-controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
