#!/usr/bin/env python3
"""Exact charge coverage on domains restricted by a verified owned-hull chain.

This checker never substitutes a derived point into a wall-ownership check.
The required antecedent is every cell in the source mask. A separate source-
bound independent chain replay establishes both owned hulls and old residual
domains; the physical charge checker then covers the remaining center domain.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,sys,time
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
def verify_premise(packet,source,seed,audit,paths):
 # This function deliberately does NOT establish derived ownership. The result
 # is only a conditional geometric implication and can never exclude a mask.
 need(packet['ownership_source_sha256']==sha(paths.ownership),'Generic source hash mismatch')
 need(source['schema']=='exact_generic_owned_hull_v1','Wrong generic source schema')
 need(source['mask']==packet['mask']==packet['required_antecedent_mask'] and not source['constraints'],'Bad explicit geometric antecedent')
 need(F(source['U'])==F(packet['parent_Uplus']) and F(source['B'])==av.L/F(source['U']),'Wrong side')
 need(packet['ownership_seed_sha256']==sha(paths.seed),'Wrong original seed')
 need(packet['cover_sha256']==av.typed.sha(av.typed.COVER)==av.typed.COVER_SHA256,'Cover mismatch')
 state=source['final_state'];need(set(map(int,state['groups']))==set(packet['mask'])==set(map(int,state['cells'])),'Incomplete assumed final state')
 for owner,rows in state['cells'].items():
  cursor=F(0)
  for row in rows:
   lo,hi=map(F,row['interval']);need(lo==cursor and lo<hi<=1,'Assumed source angle partition incomplete');cursor=hi
  need(cursor==1,'Assumed source quarter turn missing')
 return dict(status='UNPROVED_GENERIC_STATE_ASSUMPTION',antecedent_proved=False,source_sha256=sha(paths.ownership),seed_sha256=sha(paths.seed),required_antecedent_mask=packet['mask'],final_state_sha256=hashlib.sha256(canon(state)).hexdigest(),assumptions=['Every reported final owned hull is strictly inside its occupied parent.','Every reported final residual union covers all possible assigned centers throughout its stated angle interval.'],scope='Pure geometric charge implication under explicit assumptions. A complete independent generic-state replay is still required; this file cannot exclude a mask.')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('packet',type=Path);p.add_argument('--ownership',type=Path,required=True);p.add_argument('--seed',type=Path,required=True);p.add_argument('--ownership-audit',type=Path);p.add_argument('--root-audit',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--cells');p.add_argument('--seconds',type=float,default=600);p.add_argument('--max-rows',type=int,default=6000);p.add_argument('--max-depth',type=int,default=14);p.add_argument('--patch-nodes',type=int,default=5000);p.add_argument('--max-pieces',type=int,default=10000);a=p.parse_args()
 packet=json.loads(a.packet.read_text());source=json.loads(a.ownership.read_text());seed=json.loads(a.seed.read_text());audit=json.loads(a.ownership_audit.read_text()) if a.ownership_audit else None;premise=verify_premise(packet,source,seed,audit,a)
 cover=json.loads(av.typed.COVER.read_text());mask=packet['mask'];gamma=packet['threshold_units'];av.U=F(packet['parent_Uplus']);av.PARENT=av.L/av.U
 need(mask==cover['canonical_eleven_cell_subsets'][packet['mask_index']],'Noncanonical mask')
 need(F(19377,5000)<=av.U<=av.typed.U,'Side outside audited range')
 need(len(gamma)==16 and all(type(x)is int and x>=0 for x in gamma),'Invalid cell charges')
 data=av.expand(packet['certificate']);prepared=av.prepare_majority(data);surplus=sum(gamma[j] for j in mask)-packet['certificate']['budget_units'];need(surplus>0,'No budget contradiction')
 state=source['final_state'];hulls={j:cv.hull(parse(state['groups'][str(j)])) for j in mask};last={j:(None,dict(rows=state['cells'][str(j)])) for j in mask}

 selected=list(map(int,a.cells.split(','))) if a.cells else mask;need(selected and len(set(selected))==len(selected) and set(selected)<=set(mask),'Bad selected cells')
 begin=time.monotonic();records=[];done=[];stopped=False
 def save():
  complete=set(selected)==set(mask) and len(done)==len(mask) and all(c['complete'] for c in done)
  out=dict(status='PASS_CONDITIONAL_CHARGE_GEOMETRY_ONLY' if complete else 'INCOMPLETE_CONDITIONAL_CHARGE_GEOMETRY',physical_geometry_complete=complete,antecedent_proved=False,mask_exclusion_proved=False,continuum_masks_excluded=0,global_optimality_proved=False,mask_index=packet['mask_index'],mask=mask,required_antecedent_mask=mask,packet_sha256=sha(a.packet),cover_sha256=packet['cover_sha256'],parent_Uplus=str(av.U),parent_side=str(av.PARENT),ownership_premise=premise,budget_units=packet['certificate']['budget_units'],threshold_sum_units=sum(gamma[j] for j in mask),counting_surplus_units=surplus,rows=len(records),seconds=time.monotonic()-begin,cells=done,records=records,dependencies={str(k):sha(k) for k in [Path(__file__),ASYM,CV]},scope='Exact geometric implication under the EXPLICITLY UNPROVED generic-state ownership and pose-cover assumptions. No mask exclusion is claimed even if every charge row passes. Independent source replay and combined validation remain required.')
  tmp=a.output.with_suffix(a.output.suffix+'.tmp');tmp.write_text(json.dumps(out,default=str,indent=2)+'\n');tmp.replace(a.output);return out
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
    restricted=cv.interval_cover(world,others,None,lo,hi,av.U,a.max_pieces);record['domain_restriction']=restricted;record['core_side']=restricted['core_side'];record['reference_half_angle']=restricted['reference_half_angle'];record['pieces']=[]
    if restricted['passed']:record['status']='PASS_CONDITIONAL_HULL_COVER'
    elif restricted['status'] in ('PIECE_BUDGET','DEGENERATE_OUTER_DOMAIN'):record['status']='UNRESOLVED_'+restricted['status']
    else:
     record['status']='PASS_PHYSICAL_CHARGE_ON_RESIDUAL'
     for index,poly in enumerate(restricted['remaining']):
      answer=av.verify_interval(data,prepared,poly,lo,hi,gamma[cell],a.patch_nodes)
      if answer['status']=='REFUTED_BY_LEGAL_PARENT':
       P=parent_hull(answer['parent_witness']);blocked=[j for j,H in others.items() if intersects(P,H)]
       if blocked:answer.update(status='UNRESOLVED_PARENT_MEETS_OWNED_HULL',blocking_owners=blocked)
       else:answer['status']='REFUTED_CONDITIONAL_ONE_BODY_CHARGE'
      record['pieces'].append(dict(piece=index,**answer))
      if not answer['status'].startswith('PASS'):record['status']=answer['status'];break
   record['seconds']=time.monotonic()-tick;records.append(record)
   status=record['status']
   if status.startswith('PASS'):accepted.append((lo,hi))
   elif status.startswith('REFUTED'):unresolved.append((lo,hi));stopped=True;break
   elif depth<a.max_depth:
    mid=(lo+hi)/2;pending.extend([(mid,hi,depth+1,oldidx),(lo,mid,depth+1,oldidx)])
   else:unresolved.append((lo,hi))
   if len(records)%25==0:save();print(json.dumps(dict(cell=cell,rows=len(records),accepted=len(accepted),pending=len(pending),status=status,seconds=time.monotonic()-begin)),flush=True)
  cursor=F(0)
  for lo,hi in sorted(accepted):
   if lo!=cursor:break
   cursor=hi
  done.append(dict(cell=cell,complete=not pending and not unresolved and cursor==1,threshold_units=gamma[cell],accepted=sorted(accepted),pending=pending,unresolved=unresolved));save()
  if stopped:break
 out=save();print(json.dumps({k:v for k,v in out.items() if k not in ('records','cells','dependencies','ownership_premise')},default=str,indent=2))
if __name__=='__main__':main()
