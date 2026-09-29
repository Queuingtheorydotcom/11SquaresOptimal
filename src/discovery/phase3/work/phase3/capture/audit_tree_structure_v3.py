"""Independent branch-union and receipt-scope audit, without spatial replay."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,argparse
if not __debug__:raise SystemExit('Assertions must remain enabled')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def expected_constraint(owner,axis,bound,keep,U,B):
 sign=1 if keep=='le' else -1;n=[0,0];n[axis]=sign
 return dict(owner=owner,axis=axis,keep=keep,normal=n,bound_centered_unit=bound,upper_field=sign*B*(U/2+bound))
def normalize(c):
 d=dict(c)
 if d.get('kind')=='half_angle':d['bound_half_angle']=F(d['bound_half_angle'])
 else:d['bound_centered_unit']=F(d['bound_centered_unit']);d['upper_field']=F(d['upper_field'])
 return d
def audit(path):
 tree=json.loads(path.read_text());nodes=tree['nodes'];assert 'r' in nodes and nodes['r']['parent'] is None
 source=tree['root_source'];assert sha(source['path'])==source['sha256'];root=json.loads(Path(source['path']).read_text());U=F(root['parent_Uplus']);B=F(root['parent_side'])
 seen=set();closed=[];open_nodes=[]
 def visit(name,conditions,parent):
  assert name in nodes and name not in seen;seen.add(name);node=nodes[name];assert node['parent']==parent
  status=node['status']
  if 'receipt' in node:
   ref=node['receipt'];assert sha(ref['path'])==ref['sha256'];receipt=json.loads(Path(ref['path']).read_text())
   assert receipt['source']==source and list(map(normalize,receipt['constraints']))==conditions
   assert receipt['mask_index']==438 and receipt['mask_exclusion_proved'] is False and receipt['global_optimality_proved'] is False
   if status=='CLOSED_BY_CONTRADICTION':assert receipt['terminal'] and receipt['contradiction'];closed.append(name)
   if status=='CAPTURED_BY_LOCAL_GUARD':assert receipt['terminal'] and receipt['summary']['all_inside_guard'];closed.append(name)
  elif status in ('CLOSED_BY_CONTRADICTION','CAPTURED_BY_LOCAL_GUARD'):raise AssertionError('Closed leaf missing receipt')
  if status=='SPLIT':
   split=node['split'];owner=split['owner'];assert owner in root['mask']
   angular=split.get('kind')=='half_angle'
   if angular:
    bound=F(split['bound_half_angle']);lo,hi=F(0),F(1)
    for c in conditions:
     if c['owner']==owner and c.get('kind')=='half_angle':
      if c['keep']=='le':hi=min(hi,c['bound_half_angle'])
      else:lo=max(lo,c['bound_half_angle'])
    assert lo<bound<hi
   else:
    axis=split['axis'];bound=F(split['bound_centered_unit']);assert axis in (0,1)
   assert set(split['children'])=={'le','ge'}
   left,right=split['children']['le'],split['children']['ge'];assert left!=right
   for side,child in split['children'].items():
    assert nodes[child]['side']==side
    extra=dict(kind='half_angle',owner=owner,bound_half_angle=bound,keep=side) if angular else expected_constraint(owner,axis,bound,side,U,B)
    visit(child,conditions+[extra],name)
  elif status not in ('CLOSED_BY_CONTRADICTION','CAPTURED_BY_LOCAL_GUARD'):open_nodes.append(name)
 visit('r',[],None);assert seen==set(nodes)
 complete=not open_nodes
 assert bool(tree['complete'])==complete and bool(tree['local_guard_capture_proved'])==complete
 assert tree['global_optimality_proved'] is False
 return dict(status='PASS_BRANCH_PARTITIONS_AND_SCOPE',tree_sha256=sha(path),root_source_sha256=source['sha256'],nodes=len(nodes),closed_leaves=len(closed),unresolved_leaves=len(open_nodes),complete=complete,spatial_replay_performed=False,closed_leaf_ids=closed,unresolved_leaf_ids=open_nodes)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('tree',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();r=audit(a.tree)
 if a.output:a.output.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2))
