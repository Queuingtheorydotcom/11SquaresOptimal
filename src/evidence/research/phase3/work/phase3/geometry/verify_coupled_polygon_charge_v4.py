#!/usr/bin/env python3
"""Exact charge coverage on domains restricted by a verified owned-hull chain.

This checker never substitutes a derived point into a wall-ownership check.
The required antecedent is every cell in the source mask. A separate source-
bound independent chain replay establishes both owned hulls and old residual
domains; the physical charge checker then covers the remaining center domain.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse,hashlib,importlib.util,json,math,os,sys,time
if not __debug__:raise RuntimeError('Assertions must be enabled')
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[1]
ROOT=Path(os.environ.get('ELEVEN_PACKING_ROOT',WORK.parent/'current')).resolve()
ASYM=ROOT/'research/optimality/asymmetric_coverage/verify.py'
CV=WORK/'phase2/hull/convex_cover.py'
PIN={ASYM:'3bce6069052493d6fe910a7d83cbf2108a4fe7d80eef4f48663e06a3286b7d2b',CV:'cb2dfd8b2402da293f69e3f8fa1e057b200955d848d8c7bd07d2e77d44be4ac0'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
 if not ok:raise ValueError(msg)
def load(name,path):
 need(sha(path)==PIN[path],'Frozen mathematical dependency changed: '+str(path));spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
av=load('asymmetric_charge_verified',ASYM);cv=load('convex_owned_cover',CV)
sys.path.insert(0,str(WORK/'phase3/deps'));sys.path.insert(0,str(WORK/'phase3/capture/gmp'))
import fast_core_v2 as polycore
import polygon_charge as pc
import verify_collision_charge as kernels
def parse(p):return [tuple(map(F,v)) for v in p]
def canon(x):return json.dumps(x,default=str,sort_keys=True,separators=(',',':')).encode()
def locate(path):
 p=Path(path)
 if p.is_file():return p
 if 'work' in p.parts:
  q=WORK/Path(*p.parts[p.parts.index('work')+1:])
  if q.is_file():return q
 raise FileNotFoundError(path)
def intersects(A,B):
 """Closed convex intersection; equality counts as forbidden."""
 for P in (A,B):
  for n,b in cv.rows(P):
   if all(n[0]*q[0]+n[1]*q[1]>b for q in (B if P is A else A)):return False
 return True
def parent_hull(witness):
 x,y=map(F,witness['center']);t=F(witness['half_angle']);side=F(witness['side']);c,s=cv.cs(t)
 return [(x+side*(a*c-b*s)/2,y+side*(a*s+b*c)/2) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
def own_envelope(world,K,lo,hi):
 t=(lo+hi)/2;c,s=cv.cs(t);factors=[]
 for e in (lo,hi):
  ce,se=cv.cs(e);dot=c*ce+s*se;cr=abs(c*se-s*ce);need(dot>0 and dot>=cr,'Own envelope interval too wide');factors.append(dot+cr)
 extent=av.PARENT*max(factors)/2;constraints=[]
 for n in ((c,s),(-s,c)):
  values=[n[0]*x+n[1]*y for x,y in K];lower=max(values)-extent;upper=min(values)+extent;constraints.append(dict(normal=n,lower=lower,upper=upper,extent=extent));world=cv.clip_linear(world,n,upper);world=cv.clip_linear(world,(-n[0],-n[1]),-lower)
 return world,constraints

def coupled_cover(world,others,partners,lo,hi,U,max_pieces):
 domain,Q,core=polycore.row_geometry(world,lo,hi,U)
 metadata=dict(core_vertices=Q,core_side=core['old_core_side'],reference_half_angle=core['reference_half_angle'],outer_domain=domain,core_kind='certified_polygon',collision_regions=[])
 if not domain:return dict(passed=True,status='PASS_EMPTY_OUTER_DOMAIN',remaining=[],**metadata)
 minus=[(-x,-y) for x,y in Q];regions=[pc.geo.hull([(pc.F(p[0])+q[0],pc.F(p[1])+q[1]) for p in H for q in minus]) for H in others.values() if H]
 for owner in others:
  result=partners[owner].kernel(Q,domain)
  need(result['status']!='EMPTY_PARTNER_COVER','Already-empty partner cover needs explicit contradiction')
  polygon=pc.geo.hull(result['vertices'])
  if len(polygon)>=3 and pc.geo.twice_area(polygon)>0:
   regions.append(polygon);metadata['collision_regions'].append(dict(owner=owner,vertices=polygon,exact_full_kernel=True,live_partner_rows=result['live_rows'],source_kernel_vertices=len(result['vertices'])))
 regions.sort(key=pc.geo.twice_area,reverse=True);return dict(**pc.geo.union_cover(domain,regions,max_pieces),**metadata)

def exact_refuter(answer,data,world,others,own,partners,cell,t,threshold):
 point=answer.get('low_charge_center')
 if not point:return None
 c,s=cv.cs(t);radius=av.PARENT*(c+s)/2
 cen=tuple(max(radius,min(av.L-radius,F(round(float(F(x))*10**12),10**12))) for x in point)
 if not all(n[0]*cen[0]+n[1]*cen[1]<=b for n,b in cv.rows(world)):return None
 witness=dict(center=cen,half_angle=t,side=av.PARENT);P=parent_hull(witness)
 if any(intersects(P,H) for H in others.values()):return None
 if not all(all(n[0]*p[0]+n[1]*p[1]<b for n,b in cv.rows(P)) for p in own):return None
 uv=[((c*x+s*y)/data[4],(-s*x+c*y)/data[4]) for x,y in data[0]];center=(c*cen[0]+s*cen[1],-s*cen[0]+c*cen[1]);half=av.PARENT/2
 scale=math.lcm(half.denominator,*(v.denominator for p in uv+[center] for v in p));charge=av.true_charge(data,[tuple(int(v*scale) for v in p) for p in uv],int(half*scale),tuple(int(v*scale) for v in center))
 if charge>=threshold:return None
 epsilon=F(1,10**12);Qi=[(pc.F((av.PARENT-epsilon)*(a*c-b*s)/2),pc.F((av.PARENT-epsilon)*(a*s+b*c)/2)) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))];C=tuple(map(pc.F,cen));D=[tuple(map(pc.F,p)) for p in world]
 for owner in others:
  K=partners[owner].kernel(Qi,D)['vertices']
  if K and all(n[0]*C[0]+n[1]*C[1]<=h for n,h in pc.geo.rows(K)):return None
 witness.update(charge_units=charge,required_units=threshold,wall_legal=True,contains_own_hull=True,avoids_other_owned_hulls=True,universal_collision_blockers=[])
 return witness

def verify_premise(packet,source,seed,audit,paths):
 need(packet['ownership_source_sha256']==audit['source_sha256']==sha(paths.ownership),'Generic source hash mismatch')
 need(audit['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT','Missing independent generic replay')
 need(source['schema']=='exact_generic_owned_hull_v1','Wrong generic source schema')
 need(not source['constraints'] and not source['final_state']['constraints'],'A branch-conditioned state is not a full-mask antecedent')
 need(source['mask']==source['final_state']['mask']==packet['mask']==packet['required_antecedent_mask'],'Full-mask antecedent mismatch')
 need(audit['mask']==packet['mask'] and audit['mask_index']==packet['mask_index'] and not audit['constraints'],'Generic audit antecedent mismatch')
 need(source['mask_index']==packet['mask_index'],'Generic mask index mismatch')
 need(F(source['U'])==F(packet['parent_Uplus']) and F(source['B'])==av.L/F(source['U']),'Generic side mismatch')
 root_path=locate(source['source']['path']);root=json.loads(root_path.read_text());root_audit_path=paths.root_audit;root_audit=json.loads(root_audit_path.read_text())
 need(sha(root_path)==source['source']['sha256']==audit['root_sha256']==root_audit['source_sha256'],'Generic root hash mismatch')
 need(sha(root_audit_path)==audit['root_audit_sha256'],'Generic root audit hash mismatch')
 need(root_audit['status']=='PASS_INDEPENDENT_RESIDUAL_KERNEL_AUDIT' and not root_audit.get('branch_condition'),'Invalid root ownership premise')
 need(root['mask']==packet['mask'] and root['mask_index']==packet['mask_index'] and F(root['parent_Uplus'])==F(source['U']),'Root antecedent mismatch')
 need(packet['ownership_seed_sha256']==root['seed_sha256']==root_audit['seed_sha256']==sha(paths.seed),'Seed hash mismatch')
 need(seed['mask']==packet['mask'],'Wrong seed mask')
 need(packet['cover_sha256']==root['cover_sha256']==root_audit['cover_sha256']==av.typed.sha(av.typed.COVER)==av.typed.COVER_SHA256,'Cover mismatch')
 need(audit['cover_sha256']==packet['cover_sha256'] and F(audit['parent_Uplus'])==F(source['U']) and F(audit['parent_side'])==F(source['B']),'Generic audit geometry mismatch')
 need(audit.get('nodes') and all(not n['constraints'] for n in audit['nodes']),'Generic replay contains branch conditions')
 need(audit['nodes'][-1]['sha256']==sha(paths.ownership),'Final generic node was not replayed')
 roots=[WORK/'phase3/hull',WORK/'phase3/audit',WORK/'phase3/collision',WORK/'phase2/hull',WORK/'geometry']
 for receipt in (audit,root_audit):
  for name,digest in receipt['dependencies'].items():need(any((r/name).is_file() and sha(r/name)==digest for r in roots),'Audit dependency changed: '+name)
  if receipt.get('rational_backend')=='gmp':need(any(sha(p)==receipt['rational_binary_sha256'] for p in (WORK/'phase3/deps/gmpy2').glob('*.so')),'Exact rational binary changed')
 state=source['final_state'];need(set(map(int,state['groups']))==set(packet['mask'])==set(map(int,state['cells'])),'Incomplete generic final state')
 need(audit['final_state_sha256']==hashlib.sha256(canon(state)).hexdigest(),'Generic final state not audit-bound')
 need(F(state['U'])==F(source['U']) and F(state['B'])==F(source['B']) and state['mask_index']==packet['mask_index'] and state['source']==source['source'],'Ancillary final-state geometry mismatch')
 cover=json.loads(av.typed.COVER.read_text());B=av.L/F(source['U']);expected_world=[[tuple(B/2+(av.L-B)*F(x) for x in p) for p in c['vertices']] for c in cover['cells']]
 need([parse(P) for P in state['world']]==expected_world,'Final-state cover coordinates mismatch')
 for owner,rows in state['cells'].items():
  cursor=F(0)
  for row in rows:
   lo,hi=map(F,row['interval']);need(lo==cursor and lo<hi<=1,'Generic final angle partition incomplete');cursor=hi
  need(cursor==1,'Generic final quarter turn missing')
 return dict(status='SOURCE_BOUND_INDEPENDENT_GENERIC_POSE_PREMISE',audit_sha256=sha(paths.ownership_audit),source_sha256=sha(paths.ownership),seed_sha256=sha(paths.seed),root_sha256=sha(root_path),root_audit_sha256=sha(root_audit_path),required_antecedent_mask=packet['mask'],final_state_sha256=hashlib.sha256(canon(state)).hexdigest(),audit_dependencies=audit['dependencies'],root_audit_dependencies=root_audit['dependencies'])

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('packet',type=Path);p.add_argument('--ownership',type=Path,required=True);p.add_argument('--seed',type=Path,required=True);p.add_argument('--ownership-audit',type=Path,required=True);p.add_argument('--root-audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--cells');p.add_argument('--seconds',type=float,default=600);p.add_argument('--max-rows',type=int,default=6000);p.add_argument('--max-depth',type=int,default=14);p.add_argument('--patch-nodes',type=int,default=5000);p.add_argument('--max-pieces',type=int,default=10000);a=p.parse_args()
 packet=json.loads(a.packet.read_text());source=json.loads(a.ownership.read_text());seed=json.loads(a.seed.read_text());audit=json.loads(a.ownership_audit.read_text());premise=verify_premise(packet,source,seed,audit,a)
 cover=json.loads(av.typed.COVER.read_text());mask=packet['mask'];gamma=packet['threshold_units'];av.U=F(packet['parent_Uplus']);av.PARENT=av.L/av.U
 need(mask==cover['canonical_eleven_cell_subsets'][packet['mask_index']],'Noncanonical mask')
 need(F(19377,5000)<=av.U<=av.typed.U,'Side outside audited range')
 need(len(gamma)==16 and all(type(x)is int and x>=0 for x in gamma),'Invalid cell charges')
 data=av.expand(packet['certificate']);prepared=av.prepare_majority(data);surplus=sum(gamma[j] for j in mask)-packet['certificate']['budget_units'];need(surplus>0,'No budget contradiction')
 state=source['final_state'];hulls={j:cv.hull(parse(state['groups'][str(j)])) for j in mask};last={j:(None,dict(rows=state['cells'][str(j)])) for j in mask}

 partners={}
 for owner in mask:
  rows=[]
  for row in state['cells'][str(owner)]:
   lo,hi=map(pc.F,row['interval']);D=pc.geo.hull([p for poly in row['residual_polygons'] for p in poly]);Q=polycore.polygon_core(lo,hi,pc.F(packet['parent_Uplus']))['vertices'] if D else []
   rows.append(dict(core=Q,domain=D,reference=row['reference']))
  partners[owner]=kernels.col.PartnerCover(rows)

 selected=list(map(int,a.cells.split(','))) if a.cells else mask;need(selected and len(set(selected))==len(selected) and set(selected)<=set(mask),'Bad selected cells')
 begin=time.monotonic();records=[];done=[];stopped=False;last_snapshot=[-float("inf")]
 def save(force=True):
  now=time.monotonic()
  if not force and now-last_snapshot[0]<15:return None
  last_snapshot[0]=now
  complete=set(selected)==set(mask) and len(done)==len(mask) and all(c['complete'] for c in done)
  out=dict(status='PASS_EXACT_DERIVED_HULL_MASK_EXCLUSION' if complete else 'INCOMPLETE_DERIVED_HULL_CHARGE_COVERAGE',continuum_masks_excluded=int(complete),global_optimality_proved=False,mask_index=packet['mask_index'],mask=mask,required_antecedent_mask=mask,packet_sha256=sha(a.packet),cover_sha256=packet['cover_sha256'],parent_Uplus=str(av.U),parent_side=str(av.PARENT),ownership_premise=premise,budget_units=packet['certificate']['budget_units'],threshold_sum_units=sum(gamma[j] for j in mask),counting_surplus_units=surplus,rows=len(records),seconds=time.monotonic()-begin,cells=done,records=records,dependencies={str(k):sha(k) for k in [Path(__file__),ASYM,CV,Path(polycore.__file__),Path(pc.__file__),Path(pc.geo.__file__),Path(kernels.__file__),kernels.COLLISION]},scope='Only all eleven cells with complete quarter-turn coverage, combined with the independently replayed full-mask ownership antecedent, excludes this mask. No within-field symmetry transfer or global optimality claim.')
  tmp=a.output.with_suffix(a.output.suffix+'.tmp');tmp.write_text(json.dumps(out,default=str,separators=(',',':'))+'\n');tmp.replace(a.output);return out
 for cell in selected:
  accepted=[];unresolved=[];ridx,lastcell=last[cell];others={j:h for j,h in hulls.items() if j!=cell}
  pending=[(F(r['interval'][0]),F(r['interval'][1]),0,oldidx) for oldidx,r in reversed(list(enumerate(lastcell['rows'])))]
  while pending:
   if len(records)>=a.max_rows or time.monotonic()-begin>=a.seconds:stopped=True;break
   lo,hi,depth,oldidx=pending.pop();tick=time.monotonic();old=lastcell['rows'][oldidx];world=cv.hull([p for poly in old['residual_polygons'] for p in parse(poly)])
   record=dict(cell=cell,interval=[lo,hi],depth=depth,prior_state="final_state",prior_reference=old["reference"],prior_row=oldidx,prior_residual_outer_hull=world)
   if gamma[cell]==0:record['status']='PASS_NONNEGATIVE_ZERO_THRESHOLD'
   elif not world:record['status']='PASS_PRIOR_EXCLUDED_ANGLE'
   else:
    restricted_world,own_constraints=own_envelope(world,hulls[cell],lo,hi);record['own_center_constraints']=own_constraints;record['own_restricted_world']=restricted_world;restricted=coupled_cover(restricted_world,others,partners,lo,hi,av.U,a.max_pieces);record['domain_restriction']=restricted;record['core_side']=restricted['core_side'];record['reference_half_angle']=restricted['reference_half_angle'];record['pieces']=[];record['core_vertices']=restricted['core_vertices'];record['core_kind']='certified_polygon'
    if restricted['passed']:record['status']='PASS_CONDITIONAL_HULL_COVER'
    elif restricted['status'] in ('PIECE_BUDGET','DEGENERATE_OUTER_DOMAIN'):record['status']='UNRESOLVED_'+restricted['status']
    else:
     record['status']='PASS_PHYSICAL_CHARGE_ON_RESIDUAL'
     for index,poly in enumerate(restricted['remaining']):
      answer=pc.verify(packet['certificate'],restricted['core_vertices'],poly,gamma[cell],a.max_pieces)
      if not answer['status'].startswith('PASS') and depth>=2:
       witness=exact_refuter(answer,data,world,others,hulls[cell],partners,cell,(lo+hi)/2,gamma[cell])
       if witness:answer.update(status='REFUTED_COUPLED_ONE_BODY_CHARGE',parent_witness=witness)
      record['pieces'].append(dict(piece=index,**answer))
      if not answer['status'].startswith('PASS'):record['status']=answer['status'];break
   record['seconds']=time.monotonic()-tick;records.append(record)
   status=record['status']
   if status.startswith('PASS'):accepted.append((lo,hi))
   elif status.startswith('REFUTED'):unresolved.append((lo,hi));stopped=True;break
   elif depth<a.max_depth:
    mid=(lo+hi)/2;pending.extend([(mid,hi,depth+1,oldidx),(lo,mid,depth+1,oldidx)])
   else:unresolved.append((lo,hi))
   if len(records)%25==0:save(False);print(json.dumps(dict(cell=cell,rows=len(records),accepted=len(accepted),pending=len(pending),status=status,seconds=time.monotonic()-begin)),flush=True)
  cursor=F(0)
  for lo,hi in sorted(accepted):
   if lo!=cursor:break
   cursor=hi
  done.append(dict(cell=cell,complete=not pending and not unresolved and cursor==1,threshold_units=gamma[cell],accepted=sorted(accepted),pending=pending,unresolved=unresolved));save()
  if stopped:break
 out=save();print(json.dumps({k:v for k,v in out.items() if k not in ('records','cells','dependencies','ownership_premise')},default=str,indent=2))
if __name__=='__main__':main()
