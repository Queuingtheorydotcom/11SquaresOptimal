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
sys.path.insert(0,str(ROOT/'work/phase3/capture/gmp'))
import fast_convex_v2 as geo
import fast_grid as inner_grid
sys.path.insert(0,str(ROOT/'work/phase3/core'))
try:import fast_core_v2 as stronger
except ImportError:stronger=None
sys.path.insert(0,str(ROOT/'work/phase3/shared'))
import collision_kernel as collision
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
def clip_constraints(domain,owner,constraints):
 for constraint in constraints:
  if constraint['owner']==owner and constraint.get('kind')!='half_angle':domain=geo.clip_linear(domain,tuple(constraint['normal']),F(constraint['upper_field']))
 return domain
def angular_range(owner,constraints):
 lo,hi=F(0),F(1)
 for c in constraints:
  if c['owner']==owner and c.get('kind')=='half_angle':
   if c['keep']=='le':hi=min(hi,F(c['bound_half_angle']))
   else:lo=max(lo,F(c['bound_half_angle']))
 assert lo<hi,'Branches must retain a nonzero closed angular interval'
 return lo,hi
def partner_rows(state,owner):
 lo,hi=angular_range(owner,state['constraints']);result=[]
 for old in state['cells'][owner]:
  a,b=old['interval'];a,b=max(a,lo),min(b,hi)
  if a>=b:continue
  domain=clip_constraints(old['outer_domain'],owner,state['constraints'])
  core=list(stronger.polygon_core(a,b,state['U'])['vertices']) if domain else []
  result.append(dict(interval=[a,b],domain=domain,core=core,reference=old['reference']))
 assert result and result[0]['interval'][0]==lo and result[-1]['interval'][1]==hi
 assert all(a['interval'][1]==b['interval'][0] for a,b in zip(result,result[1:]))
 return result
def load_state(receipt):
 d=json.loads(Path(receipt).read_text());assert d['schema']=='exact_generic_owned_hull_v1'
 for p,h in d['dependencies'].items():assert sha(p)==h
 raw=d['final_state'];state=dict(raw)
 state['U']=F(raw['U']);state['B']=F(raw['B']);state['world']=[poly(p) for p in raw['world']]
 state['groups']={int(k):poly(v) for k,v in raw['groups'].items()};state['guard']={int(k):v for k,v in raw['guard'].items()}
 state['cells']={}
 for owner,rows in raw['cells'].items():
  state['cells'][int(owner)]=[dict(interval=list(map(F,r['interval'])),residual_polygons=[poly(p) for p in r['residual_polygons']],outer_domain=poly(r['outer_domain']),outer_bounds=r['outer_bounds'],reference=r['reference']) for r in rows]
 return state,dict(path=str(Path(receipt).resolve()),sha256=sha(receipt))
def summary(state):
 out=[]
 for owner in state['mask']:
  live=[r for r in state['cells'][owner] if r['residual_polygons']]
  vv=[p for r in live for q in r['residual_polygons'] for p in q]
  bounds=[[min(p[k] for p in vv)/state['B']-state['U']/2,max(p[k] for p in vv)/state['B']-state['U']/2] for k in (0,1)] if vv else []
  out.append(dict(owner=owner,centered_unit_bounds=bounds,retained_rows=len(live)))
 return dict(all_inside_guard=False,cells=out)
def run_node(state,output,seconds=180,passes=6,priority=None,use_polygon=True,node_id='0',parent=None,collision_partners=3):
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
  dependencies=[Path(__file__),Path(geo.__file__),Path(inner_grid.__file__),Path(inner_grid.geom.__file__),Path(collision.__file__)]
  if stronger and use_polygon:dependencies.append(Path(stronger.__file__))
  payload=dict(schema='exact_generic_owned_hull_v1',node_id=node_id,parent=parent,source=state['source'],mask_index=state['mask_index'],mask=state['mask'],U=state['U'],B=state['B'],constraints=state['constraints'],guard_source=state['guard_source'],initial=initial,steps=steps,final_state=state,summary=summary(state),contradiction=contradiction,terminal=terminal,closed=bool(contradiction) or summary(state)['all_inside_guard'],mask_exclusion_proved=False,global_optimality_proved=False,seconds=time.monotonic()-start,dependencies={str(p):sha(p) for p in dependencies})
  save(output,payload)
 for sweep in range(passes):
  changed=False
  for owner in order:
   if time.monotonic()>deadline:break
   oldrows=state['cells'][owner];prior=copy.deepcopy(state['groups']);kernel=geo.hull([(0,0),(L,0),(L,L),(0,L)]);rows=[];allvertices=[]
   def current_center(j):
    p=prior[j];return tuple(sum(q[k] for q in p)/len(p) for k in (0,1))
   ci=current_center(owner)
   partners=sorted((j for j in state['mask'] if j!=owner),key=lambda j:sum((current_center(j)[k]-ci[k])**2 for k in (0,1)))[:collision_partners]
   cover_inputs={j:partner_rows(state,j) for j in partners}
   covers={j:collision.PartnerCover(cover_inputs[j]) for j in partners}
   amin,amax=angular_range(owner,state['constraints']);planned=[]
   for old in oldrows:
    a,b=old['interval'];a,b=max(a,amin),min(b,amax)
    if a<b:planned.append((old,a,b))
   assert planned and planned[0][1]==amin and planned[-1][2]==amax
   assert all(a[2]==b[1] for a,b in zip(planned,planned[1:]))
   for ix,(old,lo,hi) in enumerate(planned):
    if time.monotonic()>deadline:break
    domain=clip_constraints(old['outer_domain'],owner,state['constraints'])
    if not domain:ans=dict(remaining=[],status='EMPTY_PRIOR_OR_BRANCH_DOMAIN');core=[]
    else:
     if stronger and use_polygon:
      ans=stronger.interval_cover(domain,{i:p for i,p in prior.items() if i!=owner},None,lo,hi,state['U'],max_pieces=3000)
      core=ans['core_vertices']
     else:
      ans=geo.interval_cover(domain,{i:p for i,p in prior.items() if i!=owner},None,lo,hi,state['U'],max_pieces=3000)
      _,core,_,_=geo.row_geometry(domain,lo,hi,state['U'])
    remaining=ans['remaining'];collision_regions=[]
    if remaining and core:
     for j in partners:
      answer=covers[j].kernel(core,ans.get('outer_domain',domain))
      # An empty partner cover will be discharged when that owner is updated.
      if answer['status']=='EMPTY_PARTNER_COVER':continue
      region=answer['vertices']
      if len(region)<3 or geo.twice_area(region)==0:continue
      collision_regions.append(dict(partner=j,**answer))
      updated=[]
      for piece in remaining:
       if geo.twice_area(piece)==0:updated.append(piece)
       else:updated.extend(geo.convex_difference(piece,region))
      remaining=updated
      if not remaining:break
    vv=[p for q in remaining for p in q];allvertices.extend(vv)
    constraints=min_boundaries(core,vv) if vv else []
    for h in constraints:kernel=geo.clip_linear(kernel,h['normal'],h['upper'])
    newdomain,bounds=outer(vv,state['world'][owner])
    rows.append(dict(interval=[lo,hi],prior_reference=old['reference'],input_domain=domain,core_vertices=core,residual_polygons=remaining,status=ans['status'],collision_regions=collision_regions,common_core_halfplanes=constraints,outer_domain=newdomain,outer_bounds=bounds,reference=dict(kind='phase3',node=node_id,step=next_id,row=ix)))
   complete=len(rows)==len(planned)
   step=dict(index=next_id,sweep=sweep,owner=owner,prior_owned_hulls=prior,prior_sha256=digest(prior),prior_partner_pose_covers=cover_inputs,prior_partner_pose_covers_sha256=digest(cover_inputs),allowed_half_angle=[amin,amax],rows=rows,complete=complete,common_owned_kernel=kernel if complete else [])
   if complete:
    state['cells'][owner]=rows
    if not allvertices:contradiction=dict(kind='all_parent_poses_forbidden',owner=owner,step=next_id)
    else:
     base=geo.hull(prior[owner]+kernel);compression=inner_grid.inner_grid(base,denominator=10**8,directions=16)
     step['compression_source_hull']=base;step['inner_grid_compression']=compression
     state['groups'][owner]=geo.hull(prior[owner]+poly(compression['vertices']))
     changed=changed or state['groups'][owner]!=prior[owner] or [(r['interval'],r['outer_domain']) for r in oldrows]!=[(r['interval'],r['outer_domain']) for r in rows]
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
def seed_state(mask_index,bins,seedpath,owner_support=None):
 coverpath=ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
 groupspath=ROOT/'work/geometry/wall_ownership_groups.json'
 cv=json.loads(coverpath.read_text());wg=json.loads(groupspath.read_text())
 assert sha(coverpath)=='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
 U=F(wg['parent_Uplus']);B=L/U;canonical_mask=cv['canonical_eleven_cell_subsets'][mask_index]
 mask=canonical_mask if owner_support is None else sorted(owner_support)
 assert mask and set(mask)<=set(canonical_mask) and len(mask)==len(set(mask))
 assert U==F('387708359002281417731/100000000000000000000')
 world=[[tuple(B/2+(L-B)*F(x) for x in p) for p in c['vertices']] for c in cv['cells']]
 groups={i:geo.hull(poly(wg['groups'][i])) for i in mask}
 cells={}
 for owner in mask:
  cells[owner]=[]
  for k in range(bins):
   lo,hi=F(k,bins),F(k+1,bins)
   domain,_,_,_=geo.row_geometry(world[owner],lo,hi,U)
   cells[owner].append(dict(interval=[lo,hi],residual_polygons=[domain] if domain else [],outer_domain=domain,outer_bounds=[],reference=dict(kind='wall_seed',owner=owner,row=k)))
 seed=dict(schema='generic_wall_seed_v1',mask_index=mask_index,mask=mask,U=U,B=B,world=world,groups=groups,cells=cells,bins=bins,
           cover_source=dict(path=str(coverpath),sha256=sha(coverpath)),wall_groups_source=dict(path=str(groupspath),sha256=sha(groupspath)),
           producer_source=dict(path=str(Path(__file__)),sha256=sha(Path(__file__))))
 save(seedpath,seed)
 return dict(U=U,B=B,mask=mask,mask_index=mask_index,world=world,groups=groups,cells=cells,constraints=[],guard={},source=dict(path=str(seedpath),sha256=sha(seedpath)),guard_source=None)

def load_phase2(source,auditpath):
 d=json.loads(source.read_text());audit=json.loads(auditpath.read_text())
 assert audit['status']=='PASS_INDEPENDENT_RESIDUAL_KERNEL_AUDIT' and audit['source_sha256']==sha(source)
 assert audit['mask_index']==d['mask_index']
 for p,h in d['dependencies'].items():assert sha(p)==h
 U=F(d['parent_Uplus']);B=L/U
 coverpath=ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
 assert sha(coverpath)==d['cover_sha256'];cv=json.loads(coverpath.read_text())
 assert d['mask']==cv['canonical_eleven_cell_subsets'][d['mask_index']]
 world=[[tuple(B/2+(L-B)*F(x) for x in p) for p in c['vertices']] for c in cv['cells']]
 groups={i:geo.hull(poly(d['owned_points'][i])) for i in d['mask']}
 cells={}
 for step in d['rounds']:
  for c in step['cells']:
   if not c['complete']:continue
   rows=[]
   for i,row in enumerate(c['rows']):
    ps=[poly(p) for p in row['residual_polygons']];vv=[p for q in ps for p in q]
    domain,bounds=outer(vv,world[c['owner']])
    rows.append(dict(interval=list(map(F,row['interval'])),residual_polygons=ps,outer_domain=domain,outer_bounds=bounds,reference=dict(kind='phase2',round=step['index'],owner=c['owner'],row=i)))
   cells[c['owner']]=rows
 assert set(cells)==set(d['mask'])
 return dict(U=U,B=B,mask=d['mask'],mask_index=d['mask_index'],world=world,groups=groups,cells=cells,constraints=[],guard={},source=dict(path=str(source),sha256=sha(source),independent_audit_path=str(auditpath),independent_audit_sha256=sha(auditpath)),guard_source=None)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mask',type=int);ap.add_argument('--owner-support');ap.add_argument('--source',type=Path);ap.add_argument('--resume-node',action='store_true');ap.add_argument('--source-audit',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--seconds',type=float,default=90);ap.add_argument('--bins',type=int,default=32);ap.add_argument('--passes',type=int,default=8);ap.add_argument('--partners',type=int,default=3);ap.add_argument('--priority',default='');args=ap.parse_args()
 parent=None
 if args.resume_node:
  assert args.source and args.output
  state,parent=load_state(args.source);mask=state['mask_index'];out=args.output
 elif args.source:
  assert args.source_audit
  state=load_phase2(args.source,args.source_audit);mask=state['mask_index'];out=args.output or Path(__file__).parent/f'mask{mask}-resumed.json'
 else:
  assert args.mask is not None
  mask=args.mask;out=args.output or Path(__file__).parent/f'mask{mask}-generic-v5.json';state=seed_state(mask,args.bins,out.with_name(out.stem+'-seed.json'),None if args.owner_support is None else [int(x) for x in args.owner_support.split(',')])
 run_node(state,out,seconds=args.seconds,passes=args.passes,node_id=out.stem,parent=parent,collision_partners=args.partners,priority=[int(x) for x in args.priority.split(',') if x])
if __name__=='__main__':main()
