"""Exact branch-conditional owned-hull propagation. Phase2 inputs are immutable.

Each completed cell step is promoted immediately, with an explicit prior-hull
snapshot. This is an acyclic induction, not a simultaneous ownership assumption.
"""
from pathlib import Path
from gmpy2 import mpq as F
import sys,json,time,hashlib,argparse,copy
if not __debug__:raise SystemExit('Assertions must remain enabled')
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/phase2/hull'))
sys.path.insert(0,str(Path(__file__).parent/'gmp'))
import fast_convex_v2 as geo
import fast_grid as inner_grid
sys.path.insert(0,str(ROOT/'work/phase3/core'))
try:import fast_core_v2 as stronger
except ImportError:stronger=None
L=geo.L
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(x):return json.dumps(x,default=str,sort_keys=True,separators=(',',':')).encode()
def digest(x):return hashlib.sha256(canon(x)).hexdigest()
def poly(x):return [tuple(map(F,p)) for p in x]
def save(p,d):
 q=p.with_suffix('.writing');q.write_text(json.dumps(d,default=str,indent=1)+'\n');q.replace(p)
def intersect(a,b):
 if not a or not b:return False
 for p in (a,b):
  for n,z in geo.rows(p):
   aa=[n[0]*x+n[1]*y for x,y in a];bb=[n[0]*x+n[1]*y for x,y in b]
   if max(aa)<min(bb) or max(bb)<min(aa):return False
 return True
DIRECTIONS=((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))
def outer(vertices,world,grid=10**8):
 if not vertices:return [],[]
 result=world;bounds=[]
 for n in DIRECTIONS:
  m=max(n[0]*x+n[1]*y for x,y in vertices)
  b=F(-((-m.numerator*grid)//m.denominator),grid)
  assert all(n[0]*x+n[1]*y<=b for x,y in vertices)
  bounds.append(dict(normal=n,upper=b));result=geo.clip_linear(result,n,b)
 return result,bounds
def min_boundaries(core,vertices):
 return [dict(normal=n,upper=b+min(n[0]*x+n[1]*y for x,y in vertices)) for n,b in geo.rows(core)]
def root_state(source):
 d=json.loads(source.read_text());assert d['mask_index']==438
 for p,h in d['dependencies'].items():assert sha(p)==h
 U=F(d['parent_Uplus']);B=L/U
 coverpath=ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
 assert sha(coverpath)==d['cover_sha256'];cv=json.loads(coverpath.read_text())
 world=[[tuple(B/2+(L-B)*F(x) for x in p) for p in c['vertices']] for c in cv['cells']]
 final=[r for r in d['rounds'] if r.get('complete')][-1]
 assert final['index']==len(d['rounds'])
 groups={i:geo.hull(poly(d['owned_points'][i])) for i in d['mask']}
 cells={}
 for c in final['cells']:
  rows=[]
  for i,row in enumerate(c['rows']):
   ps=[poly(p) for p in row['residual_polygons']];vv=[p for q in ps for p in q]
   domain,bounds=outer(vv,world[c['owner']])
   rows.append(dict(interval=list(map(F,row['interval'])),residual_polygons=ps,outer_domain=domain,outer_bounds=bounds,reference=dict(kind='phase2',round=final['index'],owner=c['owner'],row=i)))
  cells[c['owner']]=rows
 gp=ROOT/'current/research/optimality/global_capture/local-capture-guards.json'
 guard=next(g for g in json.loads(gp.read_text())['guards'] if g['mask']==d['mask'])
 return dict(U=U,B=B,mask=d['mask'],world=world,groups=groups,cells=cells,constraints=[],guard={r['cell']:r for r in guard['roles']},source=dict(path=str(source),sha256=sha(source)),guard_source=dict(path=str(gp),sha256=sha(gp)))
def clip_constraints(domain,owner,constraints):
 for constraint in constraints:
  if constraint['owner']==owner:domain=geo.clip_linear(domain,tuple(constraint['normal']),F(constraint['upper_field']))
 return domain
def load_state(receipt):
 d=json.loads(Path(receipt).read_text());assert d['schema']=='exact_branch_owned_hull_v1'
 for p,h in d['dependencies'].items():assert sha(p)==h
 raw=d['final_state'];state=dict(raw)
 state['U']=F(raw['U']);state['B']=F(raw['B']);state['world']=[poly(p) for p in raw['world']]
 state['groups']={int(k):poly(v) for k,v in raw['groups'].items()};state['guard']={int(k):v for k,v in raw['guard'].items()}
 state['cells']={}
 for owner,rows in raw['cells'].items():
  state['cells'][int(owner)]=[dict(interval=list(map(F,r['interval'])),residual_polygons=[poly(p) for p in r['residual_polygons']],outer_domain=poly(r['outer_domain']),outer_bounds=r['outer_bounds'],reference=r['reference']) for r in rows]
 return state,dict(path=str(Path(receipt).resolve()),sha256=sha(receipt))
def summary(state):
 out=[];captured=True
 for owner in state['mask']:
  live=[r for r in state['cells'][owner] if r['residual_polygons']]
  vertices=[p for r in live for q in r['residual_polygons'] for p in q]
  if not vertices:return dict(all_inside_guard=False,empty_owner=owner,cells=out)
  bounds=[[min(p[k] for p in vertices)/state['B']-state['U']/2,max(p[k] for p in vertices)/state['B']-state['U']/2] for k in (0,1)]
  role=state['guard'][owner]
  inside=all(F(a)<=x and y<=F(b) for (x,y),(a,b) in zip(bounds,role['centered_box']))
  inside=inside and all(any(F(a)<=r['interval'][0]<r['interval'][1]<=F(b) for a,b in role['half_angle_intervals']) for r in live)
  captured=captured and inside
  out.append(dict(owner=owner,centered_unit_bounds=bounds,retained_rows=len(live),inside_guard=inside))
 return dict(all_inside_guard=captured,cells=out)
def run_node(state,output,seconds=180,passes=6,priority=None,use_polygon=True,node_id='0',parent=None):
 start=time.monotonic();deadline=start+seconds;steps=[];contradiction=None
 priority=priority or []
 def center(owner):
  p=state['groups'][owner];return tuple(sum(q[k] for q in p)/len(p) for k in (0,1))
 centers={i:center(i) for i in state['mask']}
 nearest=sorted(state['mask'],key=lambda i:min((sum((centers[i][k]-centers[j][k])**2 for k in (0,1)) for j in priority),default=0))
 order=list(dict.fromkeys(priority+nearest))
 initial=dict(groups=state['groups'],cell_references={i:[r['reference'] for r in state['cells'][i]] for i in state['mask']})
 initial=copy.deepcopy(initial);next_id=0
 def write(terminal=False):
  dependencies=[Path(__file__),Path(geo.__file__),Path(inner_grid.__file__),Path(inner_grid.geom.__file__)]
  if stronger and use_polygon:dependencies.append(Path(stronger.__file__))
  payload=dict(schema='exact_branch_owned_hull_v1',node_id=node_id,parent=parent,source=state['source'],mask_index=438,mask=state['mask'],U=state['U'],B=state['B'],constraints=state['constraints'],guard_source=state['guard_source'],initial=initial,steps=steps,final_state=state,summary=summary(state),contradiction=contradiction,terminal=terminal,closed=bool(contradiction) or summary(state)['all_inside_guard'],mask_exclusion_proved=False,global_optimality_proved=False,seconds=time.monotonic()-start,dependencies={str(p):sha(p) for p in dependencies})
  save(output,payload)
 for sweep in range(passes):
  changed=False
  for owner in order:
   if time.monotonic()>deadline:break
   oldrows=state['cells'][owner];prior=copy.deepcopy(state['groups']);kernel=geo.hull([(0,0),(L,0),(L,L),(0,L)]);rows=[];allvertices=[]
   for ix,old in enumerate(oldrows):
    if time.monotonic()>deadline:break
    lo,hi=old['interval'];domain=clip_constraints(old['outer_domain'],owner,state['constraints'])
    if not domain:ans=dict(remaining=[],status='EMPTY_PRIOR_OR_BRANCH_DOMAIN');core=[]
    else:
     if stronger and use_polygon:
      ans=stronger.interval_cover(domain,{i:p for i,p in prior.items() if i!=owner},None,lo,hi,state['U'],max_pieces=3000)
      core=ans['core_vertices']
     else:
      ans=geo.interval_cover(domain,{i:p for i,p in prior.items() if i!=owner},None,lo,hi,state['U'],max_pieces=3000)
      _,core,_,_=geo.row_geometry(domain,lo,hi,state['U'])
    remaining=ans['remaining'];vv=[p for q in remaining for p in q];allvertices.extend(vv)
    constraints=min_boundaries(core,vv) if vv else []
    for h in constraints:kernel=geo.clip_linear(kernel,h['normal'],h['upper'])
    newdomain,bounds=outer(vv,state['world'][owner])
    rows.append(dict(interval=[lo,hi],prior_reference=old['reference'],input_domain=domain,core_vertices=core,residual_polygons=remaining,status=ans['status'],common_core_halfplanes=constraints,outer_domain=newdomain,outer_bounds=bounds,reference=dict(kind='phase3',node=node_id,step=next_id,row=ix)))
   complete=len(rows)==len(oldrows)
   step=dict(index=next_id,sweep=sweep,owner=owner,prior_owned_hulls=prior,prior_sha256=digest(prior),rows=rows,complete=complete,common_owned_kernel=kernel if complete else [])
   if complete:
    state['cells'][owner]=rows
    if not allvertices:contradiction=dict(kind='all_parent_poses_forbidden',owner=owner,step=next_id)
    else:
     base=geo.hull(prior[owner]+kernel);compression=inner_grid.inner_grid(base,denominator=10**8,directions=16)
     step['compression_source_hull']=base;step['inner_grid_compression']=compression
     state['groups'][owner]=geo.hull(prior[owner]+poly(compression['vertices']))
     changed=changed or state['groups'][owner]!=prior[owner]
     for a in state['mask']:
      for b in state['mask']:
       if a<b and intersect(state['groups'][a],state['groups'][b]):contradiction=dict(kind='owned_hulls_intersect',owners=[a,b],step=next_id,hulls=[state['groups'][a],state['groups'][b]])
   steps.append(step);next_id+=1
   s=summary(state);write()
   cell=next((c for c in s['cells'] if c['owner']==owner),{})
   print(json.dumps(dict(node=node_id,sweep=sweep,owner=owner,complete=complete,retained=cell.get('retained_rows'),widths=[float(b-a) for a,b in cell.get('centered_unit_bounds',[])],closed=bool(contradiction) or s['all_inside_guard'],seconds=time.monotonic()-start)),flush=True)
   if contradiction or s['all_inside_guard'] or not complete:break
  if contradiction or summary(state)['all_inside_guard'] or time.monotonic()>deadline or not changed:break
 write(True)
 return state,contradiction,summary(state)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--seconds',type=float,default=180);ap.add_argument('--passes',type=int,default=6);ap.add_argument('--owner',type=int,default=15);ap.add_argument('--axis',type=int,default=1);ap.add_argument('--bound',default='5/4');ap.add_argument('--keep',choices=['le','ge'],default='le');ap.add_argument('--square-core',action='store_true');ap.add_argument('--resume-node',action='store_true');ap.add_argument('--node-id',default='0');ap.add_argument('--no-new-constraint',action='store_true');args=ap.parse_args()
 if args.resume_node:state,parent=load_state(args.source)
 else:state,parent=root_state(args.source),None
 if not args.no_new_constraint:
  normal=[0,0];normal[args.axis]=1 if args.keep=='le' else -1
  field=state['B']*(state['U']/2+F(args.bound))*(1 if args.keep=='le' else -1)
  state['constraints'].append(dict(owner=args.owner,normal=normal,upper_field=field,axis=args.axis,bound_centered_unit=F(args.bound),keep=args.keep))
 run_node(state,args.output,args.seconds,args.passes,[args.owner],not args.square_core,args.node_id,parent)
if __name__=='__main__':main()
