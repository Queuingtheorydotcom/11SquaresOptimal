"""Exact exhaustive binary partition discovery; independent audit is separate."""
from pathlib import Path
import argparse,copy,json,time,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'capture'))
import capture_engine_self_v1 as E
F=E.F
def choose(state):
 options=[]
 for c in E.summary(state)['cells']:
  owner=c['owner']
  for axis,(lo,hi) in enumerate(c['centered_unit_bounds']):
   if lo>=hi:continue
   mid=(lo+hi)/2;D=10**7;rounded=F((mid*D).numerator//(mid*D).denominator,D)
   if lo<rounded<hi:mid=rounded
   options.append((hi-lo,dict(kind='center',owner=owner,axis=axis,bound=mid)))
  components=[]
  for row in state['cells'][owner]:
   if not row['residual_polygons']:continue
   a,b=row['interval']
   if components and components[-1][1]==a:components[-1][1]=b
   else:components.append([a,b])
  for a,b in components:
   if a<b:options.append((F(3,2)*(b-a),dict(kind='half_angle',owner=owner,bound=(a+b)/2)))
 return max(options,key=lambda t:(t[0],t[1]['owner']))[1] if options else None
def cut(state,choice,side):
 owner=choice['owner'];bound=choice['bound']
 if choice['kind']=='half_angle':return dict(kind='half_angle',owner=owner,bound_half_angle=bound,keep=side)
 sign=1 if side=='le' else -1;normal=[0,0];normal[choice['axis']]=sign
 return dict(owner=owner,normal=normal,upper_field=sign*state['B']*(state['U']/2+bound),axis=choice['axis'],bound_centered_unit=bound,keep=side)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True);ap.add_argument('--seconds',type=float,default=1200);ap.add_argument('--node-seconds',type=float,default=45);ap.add_argument('--passes',type=int,default=6);ap.add_argument('--max-nodes',type=int,default=63);ap.add_argument('--partners',type=int,default=10);a=ap.parse_args()
 root,parent=E.load_state(a.source);assert not root['guard_source'] and not root['constraints'];assert not json.loads(a.source.read_text())['closed']
 a.output_dir.mkdir(parents=True,exist_ok=True);start=time.monotonic();deadline=start+a.seconds
 nodes={'r':dict(status='UNRESOLVED',parent=None,receipt=parent)};pending=[];done=0
 def split(node,state,receipt):
  choice=choose(state)
  if not choice:return
  nodes[node].update(status='SPLIT',split=dict(**choice,children={'le':node+'0','ge':node+'1'}))
  for side in ('ge','le'):
   child=node+('0' if side=='le' else '1');nodes[child]=dict(status='PENDING',parent=node,side=side)
   pending.append(dict(id=child,source=receipt['path'],constraint=cut(state,choice,side),priority=choice['owner']))
 def save():
  leaves=[v for v in nodes.values() if v['status']!='SPLIT'];closed=sum(v['status']=='CONTRADICTION' for v in leaves)
  E.save(a.output_dir/'tree.json',dict(schema='generic_binary_partition_tree_v1',root_receipt=parent,root_source=root['source'],mask_index=root['mask_index'],mask=root['mask'],U=root['U'],B=root['B'],nodes=nodes,pending=pending,closed_leaves=closed,unresolved_leaves=len(leaves)-closed,producer_exclusion_complete=bool(leaves) and closed==len(leaves),independently_audited=False,global_optimality_proved=False,driver_sha256=E.sha(__file__),seconds=time.monotonic()-start))
 split('r',root,parent);save()
 while pending and done<a.max_nodes and time.monotonic()<deadline:
  job=pending.pop();node=job['id'];state,previous=E.load_state(Path(job['source']));state['constraints'].append(job['constraint']);nodes[node]['status']='RUNNING';save()
  out=a.output_dir/(node+'.json');state,contradiction,summary=E.run_node(state,out,min(a.node_seconds,max(1,deadline-time.monotonic())),a.passes,[job['priority']],True,'generic'+str(root['mask_index'])+'-'+node,previous,a.partners)
  receipt=dict(path=str(out.resolve()),sha256=E.sha(out));nodes[node]['receipt']=receipt;done+=1
  if contradiction:nodes[node]['status']='CONTRADICTION'
  else:nodes[node]['status']='UNRESOLVED';split(node,state,receipt)
  save();print(json.dumps(dict(node=node,status=nodes[node]['status'],done=done,pending=len(pending),seconds=time.monotonic()-start)),flush=True)
 save()
if __name__=='__main__':main()
