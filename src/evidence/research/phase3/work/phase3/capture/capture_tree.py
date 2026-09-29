"""Complete binary halfplane partitions; unresolved leaves remain explicit."""
from pathlib import Path
import argparse,json,time,copy
import capture_engine_gmp as E
F=E.F
def constraint(state,owner,axis,bound,keep):
 sign=1 if keep=='le' else -1;n=[0,0];n[axis]=sign
 return dict(owner=owner,normal=n,upper_field=sign*state['B']*(state['U']/2+bound),axis=axis,bound_centered_unit=bound,keep=keep)
def split_choice(state):
 options=[]
 for cell in E.summary(state)['cells']:
  owner=cell['owner'];guard=state['guard'][owner]
  for axis,((lo,hi),(a,b)) in enumerate(zip(cell['centered_unit_bounds'],guard['centered_box'])):
   a,b=F(a),F(b)
   if lo<a:options.append((a-lo,owner,axis,(lo+a)/2,'le'))
   if hi>b:options.append((hi-b,owner,axis,(hi+b)/2,'ge'))
 if not options:return None
 _,owner,axis,bound,far=max(options)
 # Round only the branch proposal; either complementary halfplanes cover all.
 D=10**6;bound=F((bound*D).numerator//(bound*D).denominator,D)
 return dict(owner=owner,axis=axis,bound_centered_unit=bound,far=far)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--closed-far',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True);ap.add_argument('--seconds',type=float,default=1200);ap.add_argument('--node-seconds',type=float,default=120);ap.add_argument('--passes',type=int,default=8);ap.add_argument('--max-nodes',type=int,default=31);args=ap.parse_args()
 args.output_dir.mkdir(parents=True,exist_ok=True);treepath=args.output_dir/'tree.json';start=time.monotonic();deadline=start+args.seconds
 root=E.root_state(args.source);closed=json.loads(args.closed_far.read_text())
 assert closed['terminal'] and closed['contradiction'] and closed['constraints']==[json.loads(json.dumps(constraint(root,15,1,F(5,4),'le'),default=str))]
 assert closed['source']==root['source']
 nodes={'r':dict(status='SPLIT',parent=None,split=dict(owner=15,axis=1,bound_centered_unit=F(5,4),children={'le':'r0','ge':'r1'})),
        'r0':dict(status='CLOSED_BY_CONTRADICTION',receipt=dict(path=str(args.closed_far.resolve()),sha256=E.sha(args.closed_far)),parent='r',side='le'),
        'r1':dict(status='PENDING',parent='r',side='ge')}
 pending=[dict(id='r1',parent_receipt=None,add=constraint(root,15,1,F(5,4),'ge'),priority=15,depth=1)]
 done=0
 def write():
  leaves=[v for v in nodes.values() if v['status']!='SPLIT'];complete=bool(leaves) and all(v['status'] in ('CLOSED_BY_CONTRADICTION','CAPTURED_BY_LOCAL_GUARD') for v in leaves)
  E.save(treepath,dict(schema='binary_center_halfplane_capture_tree_v1',root_source=root['source'],nodes=nodes,pending=pending,complete=complete,local_guard_capture_proved=complete,global_optimality_proved=False,closed_leaves=sum(v['status'] in ('CLOSED_BY_CONTRADICTION','CAPTURED_BY_LOCAL_GUARD') for v in leaves),unresolved_leaves=sum(v['status'] not in ('CLOSED_BY_CONTRADICTION','CAPTURED_BY_LOCAL_GUARD') for v in leaves),seconds=time.monotonic()-start,driver_sha256=E.sha(__file__)))
 write()
 while pending and done<args.max_nodes and time.monotonic()<deadline:
  item=pending.pop();node_id=item['id']
  if item['parent_receipt']:state,parent=E.load_state(Path(item['parent_receipt']))
  else:state,parent=copy.deepcopy(root),None
  state['constraints'].append(item['add']);out=args.output_dir/(node_id+'.json')
  nodes[node_id]['status']='RUNNING';write()
  state,contradiction,summary=E.run_node(state,out,min(args.node_seconds,max(1,deadline-time.monotonic())),args.passes,[item['priority']],True,node_id,parent)
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
     pending.append(dict(id=child,parent_receipt=str(out.resolve()),add=constraint(state,choice['owner'],choice['axis'],choice['bound_centered_unit'],side),priority=choice['owner'],depth=item['depth']+1))
  write();print(json.dumps(dict(tree_node=node_id,status=record['status'],pending=len(pending),nodes_done=done,seconds=time.monotonic()-start)),flush=True)
 write()
if __name__=='__main__':main()
