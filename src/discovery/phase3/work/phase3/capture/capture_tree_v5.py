"""Complete binary halfplane partitions; unresolved leaves remain explicit."""
from pathlib import Path
import argparse,json,time,copy
import capture_engine_v4 as E
F=E.F
def constraint(state,owner,axis,bound,keep):
 sign=1 if keep=='le' else -1;n=[0,0];n[axis]=sign
 return dict(owner=owner,normal=n,upper_field=sign*state['B']*(state['U']/2+bound),axis=axis,bound_centered_unit=bound,keep=keep)
def angle_constraint(owner,bound,keep):
 return dict(kind='half_angle',owner=owner,bound_half_angle=bound,keep=keep)
def split_choice(state):
 # Refine every uncertain pose variable while any part remains outside guard.
 # Restricting choices to exterior variables can leave coarse interior cores.
 options=[]
 for cell in E.summary(state)['cells']:
  owner=cell['owner'];guard=state['guard'][owner]
  for axis,((lo,hi),(a,b)) in enumerate(zip(cell['centered_unit_bounds'],guard['centered_box'])):
   a,b=F(a),F(b)
   if hi<=lo:continue
   low_excess=max(a-lo,F(0));high_excess=max(hi-b,F(0))
   if max(low_excess,high_excess)>0:
    if low_excess>=high_excess:bound=(lo+min(a,hi))/2;far='le'
    else:bound=(hi+max(b,lo))/2;far='ge'
   else:
    bound=(lo+hi)/2;far='le' if bound<(a+b)/2 else 'ge'
   D=10**6;rounded=F((bound*D).numerator//(bound*D).denominator,D)
   if lo<rounded<hi:bound=rounded
   options.append((hi-lo,max(low_excess,high_excess),dict(kind='center',owner=owner,axis=axis,bound_centered_unit=bound,far=far)))
  live=[r['interval'] for r in state['cells'][owner] if r['residual_polygons']];components=[]
  for a,b in live:
   if components and components[-1][1]==a:components[-1][1]=b
   else:components.append([a,b])
  allowed=[list(map(F,p)) for p in guard['half_angle_intervals']]
  for a,b in components:
   mid=(a+b)/2;nearest=min(allowed,key=lambda p:max(p[0]-mid,mid-p[1],F(0)))
   far='le' if mid<sum(nearest)/2 else 'ge';exterior=not any(x<=a and b<=y for x,y in allowed)
   options.append((F(3,2)*(b-a),F(exterior)*(b-a),dict(kind='half_angle',owner=owner,bound_half_angle=mid,far=far)))
 if not options:return None
 return max(options,key=lambda p:(p[0],p[1],p[2]['owner']))[2]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--closed-far',type=Path);ap.add_argument('--output-dir',type=Path,required=True);ap.add_argument('--seconds',type=float,default=1200);ap.add_argument('--node-seconds',type=float,default=120);ap.add_argument('--passes',type=int,default=8);ap.add_argument('--max-nodes',type=int,default=31);ap.add_argument('--resume-tree',type=Path);ap.add_argument('--collision-partners',type=int,default=4);args=ap.parse_args()
 args.output_dir.mkdir(parents=True,exist_ok=True);treepath=args.output_dir/'tree.json';start=time.monotonic();deadline=start+args.seconds
 root=E.root_state(args.source);ancestor=None
 if args.resume_tree:
  previous=json.loads(args.resume_tree.read_text());assert previous['root_source']==root['source']
  nodes=previous['nodes'];pending=previous['pending'];ancestor=dict(path=str(args.resume_tree.resolve()),sha256=E.sha(args.resume_tree))
  for node_id,node in nodes.items():
   if node['status']=='RUNNING':
    receipt=args.resume_tree.parent/(node_id+'.json');d=json.loads(receipt.read_text())
    assert d['schema']=='exact_branch_owned_hull_v1'
    pending.append(dict(id=node_id,parent_receipt=str(receipt.resolve()),add=None,priority=d['constraints'][-1]['owner'],depth=len(node_id)-1))
    node['status']='PENDING'
 else:
  closed=json.loads(args.closed_far.read_text())
  assert closed['terminal'] and closed['contradiction'] and closed['constraints']==[json.loads(json.dumps(constraint(root,15,1,F(5,4),'le'),default=str))]
  assert closed['source']==root['source']
  nodes={'r':dict(status='SPLIT',parent=None,split=dict(owner=15,axis=1,bound_centered_unit=F(5,4),children={'le':'r0','ge':'r1'})),
         'r0':dict(status='CLOSED_BY_CONTRADICTION',receipt=dict(path=str(args.closed_far.resolve()),sha256=E.sha(args.closed_far)),parent='r',side='le'),
         'r1':dict(status='PENDING',parent='r',side='ge')}
  pending=[dict(id='r1',parent_receipt=None,add=constraint(root,15,1,F(5,4),'ge'),priority=15,depth=1)]
 done=0
 def write():
  leaves=[v for v in nodes.values() if v['status']!='SPLIT'];complete=bool(leaves) and all(v['status'] in ('CLOSED_BY_CONTRADICTION','CAPTURED_BY_LOCAL_GUARD') for v in leaves)
  E.save(treepath,dict(schema='binary_center_halfplane_capture_tree_v1',root_source=root['source'],ancestor=ancestor,nodes=nodes,pending=pending,complete=complete,local_guard_capture_proved=complete,global_optimality_proved=False,closed_leaves=sum(v['status'] in ('CLOSED_BY_CONTRADICTION','CAPTURED_BY_LOCAL_GUARD') for v in leaves),unresolved_leaves=sum(v['status'] not in ('CLOSED_BY_CONTRADICTION','CAPTURED_BY_LOCAL_GUARD') for v in leaves),seconds=time.monotonic()-start,driver_sha256=E.sha(__file__)))
 write()
 while pending and done<args.max_nodes and time.monotonic()<deadline:
  item=pending.pop();node_id=item['id']
  if item['parent_receipt']:state,parent=E.load_state(Path(item['parent_receipt']))
  else:state,parent=copy.deepcopy(root),None
  
  if item['add'] is not None:state['constraints'].append(item['add'])
  out=args.output_dir/(node_id+'.json')
  nodes[node_id]['status']='RUNNING';write()
  state,contradiction,summary=E.run_node(state,out,min(args.node_seconds,max(1,deadline-time.monotonic())),args.passes,[item['priority']],True,node_id+'-v5',parent,args.collision_partners)
  done+=1;record=nodes[node_id];record['receipt']=dict(path=str(out.resolve()),sha256=E.sha(out))
  if contradiction:record['status']='CLOSED_BY_CONTRADICTION'
  elif summary['all_inside_guard']:record['status']='CAPTURED_BY_LOCAL_GUARD'
  else:
   choice=split_choice(state)
   if choice is None:record['status']='UNRESOLVED_ANGLE_LOCALIZATION'
   else:
    record['status']='SPLIT';record['split']=dict(**choice,children={'le':node_id+'0','ge':node_id+'1'})
    far=choice['far'];near='ge' if far=='le' else 'le'
    # LIFO explores the farther-from-guard child first.
    for side in (near,far):
     child=node_id+('0' if side=='le' else '1');nodes[child]=dict(status='PENDING',parent=node_id,side=side)
     pending.append(dict(id=child,parent_receipt=str(out.resolve()),add=(angle_constraint(choice['owner'],choice['bound_half_angle'],side) if choice.get('kind')=='half_angle' else constraint(state,choice['owner'],choice['axis'],choice['bound_centered_unit'],side)),priority=choice['owner'],depth=item['depth']+1))
  write();print(json.dumps(dict(tree_node=node_id,status=record['status'],pending=len(pending),nodes_done=done,seconds=time.monotonic()-start)),flush=True)
 write()
if __name__=='__main__':main()
