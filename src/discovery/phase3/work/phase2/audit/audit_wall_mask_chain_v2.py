#!/usr/bin/env python3
"""Independent full proof-chain verification plus producer replay comparison.

Every accepted positive row is independently covered by rational polygon unions
of direct median-hull regions and point-capture boxes; no producing geometry,
patcher, or staircase is imported. The source-bound producer replay is retained
as a cross-check. Only nonnegative fields with cell thresholds zero or one are
supported by the independent full-row geometry checker.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from collections import Counter
import argparse,hashlib,json,sys,os
ROOT=Path(os.environ.get('ELEVEN_PACKING_ROOT',str(Path(__file__).resolve().parents[3]/'current'))).resolve()
WORK=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/optimality/audit'))
sys.path.insert(0,str(WORK/'geometry'))
from audit_center_cover import audit as audit_cover
from audit_endpoint_rows import E,u,configuration,HornerSigns
from audit_wall_kernel import check_point
from independent_patch_cover import verify_row as independently_cover_row,controls as polygon_controls
PINNED={
 'research/optimality/asymmetric_coverage/verify.py':'3bce6069052493d6fe910a7d83cbf2108a4fe7d80eef4f48663e06a3286b7d2b',
 'research/optimality/typed_coverage/verify.py':'1e56f02ee9201ac93f289cbe1c777abc3f9fa9a72345a711b91381b33aa4e7a3',
}
COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
EXPECTED_COVER='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
WALL_AUDITOR_SHA='f442d798796e6017225dea528c9bcf7b4fbeb3c2c3e6262f68de2e43ff542660'
U_EXACT=F(387708359002281417731,10**20)
def need(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def portable_dependency(p):
 p=str(p)
 known=('current/research/optimality/asymmetric_coverage/verify.py',
        'work/geometry/verify_wall_aware_mask.py',
        'work/geometry/validate_wall_sites.py')
 for q in known:
  if p==q or p.endswith('/'+q):return q
 raise ValueError('unrecognized adapter dependency path '+p)
def local_dependency(p):
 q=portable_dependency(p)
 return ROOT/q[len('current/'):] if q.startswith('current/') else WORK/q[len('work/'):]
def strip_time(x):
 if isinstance(x,dict):return {k:({portable_dependency(p):d for p,d in v.items()} if k=='adapter_dependencies' else strip_time(v)) for k,v in x.items() if k!='seconds'}
 if isinstance(x,list):return [strip_time(v) for v in x]
 return x
def trig(t):return (1-t*t)/(1+t*t),2*t/(1+t*t)
def quadratic(a,b,c,lo,hi):
 pts=[lo,hi]
 if c>0 and lo<-b/(2*c)<hi:pts.append(-b/(2*c))
 return min(a+b*x+c*x*x for x in pts)>=0

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('packet',type=Path);ap.add_argument('producer',type=Path);ap.add_argument('replay',type=Path)
 ap.add_argument('--output',type=Path,required=True)
 ap.add_argument('--ownership-cache',type=Path,help='An earlier receipt from this auditor; every exact point key is checked')
 args=ap.parse_args(); packet=read(args.packet); producer=read(args.producer); replay=read(args.replay);cover=read(COVER)
 need(__debug__,'assertions must be enabled')
 for p,d in PINNED.items():need(sha(ROOT/p)==d,'audited upstream source changed: '+p)
 need(sha(WORK/'geometry/audit_wall_kernel.py')==WALL_AUDITOR_SHA,'independent ownership checker changed')
 need(sha(COVER)==EXPECTED_COVER,'cover changed')
 need(args.producer.resolve()!=args.replay.resolve(),'fresh replay must be a distinct output file')
 need(strip_time(producer)==strip_time(replay),'fresh replay differs from producer apart from timing')
 for p,d in replay['dependencies'].items():need(sha(ROOT/p)==d,'changed replay dependency '+p)
 for p,d in replay['adapter_dependencies'].items():need(sha(local_dependency(p))==d,'changed adapter dependency '+p)
 need(replay['packet_sha256']==sha(args.packet) and replay['cover_sha256']==packet['cover_sha256']==EXPECTED_COVER,'premise binding mismatch')
 need(replay['status']=='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION' and replay['continuum_masks_excluded']==1,'complete replay did not pass')
 need(replay['global_optimality_proved'] is False,'unjustified global claim')
 mask=packet['mask'];idx=packet['mask_index'];gamma=packet['threshold_units'];U=F(packet['parent_Uplus']);L=F(191,50);B=L/U
 need(U==U_EXACT and F(replay['parent_Uplus'])==U and F(replay['parent_side'])==B,'parent coordinates mismatch')
 need(type(idx) is int and 0<=idx<2184 and mask==cover['canonical_eleven_cell_subsets'][idx]==replay['mask'] and replay['mask_index']==idx,'canonical mask mismatch')
 need(len(mask)==11 and len(set(mask))==11,'mask not eleven distinct cells')
 need(len(gamma)==16 and all(type(w) is int and w>=0 for w in gamma),'bad thresholds')
 need(replay['within_field_symmetry_transfer'] is False and replay['full_quarter_turn'] is True,'invalid symmetry or angle claim')
 geometry=audit_cover(COVER)
 turn=lambda J:tuple(sorted(15-i for i in J))
 allmasks=list(combinations(range(16),11));canonical=sorted({min(J,turn(J)) for J in allmasks})
 need(len(canonical)==2184 and [list(J) for J in canonical]==cover['canonical_eleven_cell_subsets'],'canonical enumeration mismatch')
 for i in range(16):
  need(tuple(1-F(x) for x in cover['cells'][i]['center'])==tuple(map(F,cover['cells'][15-i]['center'])),'cover site half-turn mismatch')
  need({tuple(1-F(x) for x in p) for p in cover['cells'][i]['vertices']}=={tuple(map(F,p)) for p in cover['cells'][15-i]['vertices']},'cover polygon half-turn mismatch')
 unitcells=[[tuple(F(1,2)+(U-1)*F(x) for x in p) for p in c['vertices']] for c in cover['cells']]
 need(max(sum((a-b)**2 for a,b in zip(p,q)) for cell in unitcells for p in cell for q in cell)<1,'cells not injective')
 cert=packet['certificate'];D=cert['coordinate_denominator'];sites=cert['sites'];pw=cert['point_weights']
 need(F(cert['L'])==L and type(D) is int and D>0 and (L*D).denominator==1 and cert['weight_denominator']==1,'field normalization fails')
 need(sites and len(sites)==len(pw) and len(set(map(tuple,sites)))==len(sites),'field site/charge mismatch')
 need(all(len(p)==2 and all(type(v) is int and 0<=v<=L*D for v in p) for p in sites),'bad field point')
 need(all(type(w) is int and w>=0 for w in pw),'negative point charge')
 budget=sum(pw);arities=[]
 for feature in cert['features']:
  g=feature['indices'];k=feature['threshold'];w=feature['weight']
  need(feature['kind']=='majority_hull' and type(k) is int and 1<=k<=4 and len(g)==2*k-1 and len(set(g))==len(g),'invalid odd TRUE support')
  need(all(type(i) is int and 0<=i<len(sites) for i in g) and type(w) is int and w>=0 and not feature.get('multiset',False),'invalid TRUE support or weight')
  budget+=w;arities.append(len(g))
 threshold=sum(gamma[i] for i in mask)
 need(budget==cert['budget_units']==replay['budget_units'] and threshold==replay['threshold_sum_units'] and threshold>budget and replay['counting_surplus_units']==threshold-budget,'invalid counting gap')
 need(packet['conditional_ownership']==replay['conditional_ownership']=='cell_owned_points' and 'ownership_offsets_unit' not in packet,'unsupported ownership representation')
 groups=packet['ownership_points_field'];need(groups==replay['owned_points'] and len(groups)==16,'ownership field mismatch')
 support=packet.get('conditional_owner_support',mask)
 need(support==replay['conditional_owner_support'] and len(set(support))==len(support) and all(type(i) is int for i in support) and set(support)<=set(mask),'invalid conditional owner set')
 cached={}
 if args.ownership_cache:
  cache=read(args.ownership_cache)
  need(cache['status']=='PASS_INDEPENDENT_COMPLETE_WALL_MASK_CHAIN_AUDIT' and cache['independent_ownership_checker_sha256']==WALL_AUDITOR_SHA and cache['cover_sha256']==EXPECTED_COVER and F(cache['parent_Uplus'])==U,'invalid ownership cache scope')
  need(cache['audit_checker_sha256'] in (sha(__file__), '7eac7da790ca5cc5402cd511d848cf5f786535cef10fd1e7db764af5a982fd3d'),'ownership cache checker changed')
  if cache['audit_checker_sha256']!=sha(__file__):need(sha(WORK/'new_mask_audit/audit_wall_mask_chain.py')==cache['audit_checker_sha256'],'frozen cache checker changed')
  cached={(r['owner'],tuple(map(F,r['unit_point']))):r for r in cache['ownership_results']}
 ownership=[];disks=walls=0
 reported={(r['owner'],tuple(map(F,r['field_point']))):r for r in replay['ownership_receipts']}
 need(len(reported)==len(replay['ownership_receipts'])==sum(map(len,groups)),'duplicate/missing ownership receipt')
 for owner,group in enumerate(groups):
  need(type(group) is list and 1<=len(group)<=65 and len(set(map(tuple,group)))==len(group),'bad owner group')
  for p in group:
   point=tuple(map(F,p));need(len(point)==2 and all(0<=x<=L for x in point),'bad ownership point')
   unit=tuple(x/B for x in point);rr=reported[(owner,point)]
   need(tuple(map(F,rr['unit_point']))==unit,'ownership unit conversion mismatch')
   md=max(sum((a-b)**2 for a,b in zip(unit,v)) for v in unitcells[owner])
   if md<F(1,4):
    result=dict(passed=True,method='independent_exact_disk_vertex_bound',maximum_vertex_distance_squared=str(md));disks+=1
   else:
    walls+=1
    if (owner,unit) in cached:
     old=cached[(owner,unit)];need(old['passed'] is True and F(old['strict_projection_margin'])>0,'invalid cached strict wall proof')
     result={k:v for k,v in old.items() if k not in ('owner','unit_point')}
    else:
     result=check_point(unitcells[owner],unit)
     need(result['passed'] and F(result['strict_projection_margin'])>0,'independent wall proof failed')
     result['method']='independent_rational_interval_projection_bounds'
   ownership.append(dict(owner=owner,unit_point=list(map(str,unit)),**result))
 cells=replay['cells'];need(len(cells)==11 and {r['cell'] for r in cells}==set(mask),'missing/duplicate physical cells')
 accepted={};counts=Counter();independent_rows=[];direct_controls=polygon_controls()
 for row in replay['records']:
  counts[row['status']]+=1
  need(row['cell'] in mask,'row outside mask')
  if not row['status'].startswith('PASS'):continue
  i=row['cell'];a,b=map(F,row['interval']);key=(i,a,b)
  need(key not in accepted and F(0)<=a<b<=F(1),'invalid/duplicate accepted interval')
  need(row['status'] in ('PASS_STAIRCASE','PASS_TRUE_PATCH'),'accepted row status not covered by this audit')
  if row['status']=='PASS_STAIRCASE':need(type(row['proxy_minimum']) is int and row['proxy_minimum']>=gamma[i],'insufficient staircase bound')
  else:need(row['patches']['status']=='PASS','unproved patch receipt')
  t=(a+b)/2;c,s=trig(t);factors=[];widths=[]
  for z in (a,b):
   cz,sz=trig(z);dot=c*cz+s*sz;cross=abs(c*sz-s*cz)
   need(dot>0 and dot>=cross,'row angle too wide')
   factors.append(dot+cross);widths.append(cz+sz)
  factor=max(factors);core=(B-F(1,10**12))/factor;H=L/2-B*min(widths)/2
  need(F(row['reference_half_angle'])==t and F(row['core_side'])==core and F(row['parent_center_halfwidth'])==H,'core or envelope mismatch')
  need(quadratic(factor-c-s,2*(c-s),factor+c+s,a,t),'left full-angle containment fails')
  need(quadratic(factor-c+s,-2*(c+s),factor+c-s,t,b),'right full-angle containment fails')
  width=min(widths);need(quadratic(1-width,2,-1-width,a,b),'full-angle legal-wall envelope fails')
  need(0<core<B and core*factor<B and core*(c+s)/2<=L/2-H<L/2,'strict core containment fails')
  if gamma[i]>0:independent_rows.append(independently_cover_row(packet,cover,row))
  accepted[key]=row
 matched=set()
 for cell in cells:
  i=cell['cell'];need(cell['complete'] and not cell['pending'] and not cell['unresolved'] and cell['threshold_units']==gamma[i],'unfinished or wrong-threshold cell')
  cursor=F(0)
  for a,b in sorted(tuple(map(F,p)) for p in cell['accepted']):
   need(a==cursor and (i,a,b) in accepted,'angular gap or unproved accepted interval');cursor=b;matched.add((i,a,b))
  need(cursor==1,'angle cover incomplete')
 need(matched==set(accepted) and replay['rows']==len(replay['records']),'orphan leaves or row count mismatch')
 endpoint=ROOT/'research/optimality/endpoint_charge/exact-trump-endpoint-rows.json'
 signs=HornerSigns(read(endpoint)['root_interval']);_,alpha,_=configuration(E(u))
 need(signs.element(alpha-E(U.numerator)/U.denominator)<0,'alpha not strictly below U')
 controls=[]
 for name,source in [('asymmetric-coverage-independent-audit.json','research/optimality/asymmetric_coverage/verify.py'),('typed-coverage-independent-audit.json','research/optimality/typed_coverage/verify.py')]:
  path=ROOT/'research/optimality/audit'/name;r=read(path)
  need(r['controller_sha256']==PINNED[source] and r['status'].startswith('PASS'),'missing source-bound prior geometry/controller audit')
  controls.append(dict(path=str(path),sha256=sha(path)))
 positive=[i for i in mask if gamma[i]>0]
 # Every new target contains the same conditioned owners and enough already
 # audited positive cells. Other cells have no effect on the contradiction.
 def applicable(J):
  return set(support)<=set(J) and sum(gamma[i] for i in positive if i in J)>budget
 direct_transferred=[j for j,J in enumerate(canonical) if applicable(J)]
 transferred=[j for j,J in enumerate(canonical) if applicable(J) or applicable(turn(J))]
 need(idx in transferred,'base mask absent from transfer closure')
 output=dict(status='PASS_INDEPENDENT_COMPLETE_WALL_MASK_CHAIN_AUDIT',audit_checker_sha256=sha(__file__),
  independent_ownership_checker_sha256=WALL_AUDITOR_SHA,packet_sha256=sha(args.packet),producer_receipt_sha256=sha(args.producer),fresh_replay_sha256=sha(args.replay),
  cover_sha256=EXPECTED_COVER,control_receipts=controls,parent_Uplus=str(U),parent_side=str(B),exact_alpha_below_U=True,
  algebraic_root_source_sha256=sha(endpoint),canonical_mask_index=idx,mask=mask,full_physical_cells=11,
  angular_parameter_domain=['0','1'],processed_rows=len(replay['records']),accepted_full_interval_leaves=len(accepted),status_counts=dict(counts),
  original_point_capacity=sum(pw),TRUE_feature_arities=arities,TRUE_capacities=[1]*len(arities),budget_units=budget,
  proved_positive_cells=positive,proved_cell_thresholds={str(i):gamma[i] for i in positive},threshold_sum_units=threshold,conditional_owner_support=support,
  independent_geometry_checker_sha256=sha(Path(__file__).with_name('independent_patch_cover.py')),independent_geometry_controls=direct_controls,
  independent_complete_positive_rows=len(independent_rows),independent_row_proofs=independent_rows,
  ownership_points=len(ownership),ownership_disk_points=disks,ownership_wall_points=walls,ownership_results=ownership,
  continuum_base_masks_excluded=1,continuum_canonical_masks_excluded=len(transferred),transferred_canonical_mask_indices=transferred,
  direct_containment_canonical_mask_indices=direct_transferred,
  transfer_rule='For each canonical mask J, apply the same fixed certificate either to the packing itself or to its entire half-turn image. No within-field reflection of individual rows is used.',
  global_optimality_proved=False,geometry_trust='Fresh source-bound producer replay plus a source-distinct exact polygon-union coverage proof over the entire legal center domain for EVERY accepted positive-threshold row. Zero-threshold rows follow from independently checked charge nonnegativity.',
  scope='Each listed canonical case is impossible at rational side U and hence for every S <= U, including S <= alpha. No complete global optimality claim.')
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(output,indent=2)+'\n')
 print(json.dumps({k:v for k,v in output.items() if k not in ('ownership_results','independent_row_proofs')},indent=2))
if __name__=='__main__':main()
