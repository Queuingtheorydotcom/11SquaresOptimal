#!/usr/bin/env python3
"""Freeze a self-contained algebraic endpoint charge proposal, not a proof."""
from discover import *
import resource
statepath=OUT/'deep-adversarial1/state.npz';st=np.load(statepath);zm=np.load(OUT/'hard-poses1/model.npz');model={k:zm[k].item() if k=='nvar' else zm[k] for k in zm.files if k!='budget'}
D=10**9;weights=np.rint(st['weights']*D).astype(np.int64);on=np.flatnonzero(weights>0);budgets=st['budget'].astype(np.int64);mass=int(budgets@weights);threshold=int(np.min(st['rows'].astype(np.int64)@weights))
old=json.loads(FAMILY.read_text());contacts=json.loads(CONTACT.read_text());DEN=old['coordinate_denominator'];LD=int(Q(old['L'])*DEN);oldpoints=[]
for x,y,_ in old['point_orbits']:oldpoints.extend(sorted({(a,b) for p,q in ((x,y),(y,x)) for a in (p,LD-p) for b in (q,LD-q)}))
allrefs=[{'kind':'rational_family_site','original_point_index':i,'coordinates_coefficients':[[str(Q(x,DEN))]+['0']*7,[str(Q(y,DEN))]+['0']*7]} for i,(x,y) in enumerate(oldpoints)]
for oi,o in enumerate(contacts['orbits']):
 for mi,p in enumerate(o['members_coefficients']):allrefs.append({'kind':'algebraic_contact_site','contact_orbit':oi,'member':mi,'coordinates_coefficients':p})
features=[];needed=set()
for col in on:
 ps=np.flatnonzero(model['pids']==col);gs=np.flatnonzero(model['gids']==col)
 assert bool(len(ps))!=bool(len(gs))
 if len(ps):
  ids=list(map(int,ps));needed.update(ids);f={'column':int(col),'kind':'ordinary_point_orbit','members':ids,'budget':len(ids),'weight_units':int(weights[col])}
 else:
  sets=[];kinds=set();thresholds=set()
  for g in gs:
   ids=list(map(int,model['groups'][g,:model['length'][g]]));sets.append(ids);needed.update(ids);kinds.add(int(model['kinds'][g]));thresholds.add(int(model['thresholds'][g]))
  assert len(kinds)==1 and len(thresholds)==1
  kind=kinds.pop();th=thresholds.pop();assert kind in (0,1,3)
  f={'column':int(col),'kind':{0:'threshold',1:'floor',3:'majority_hull'}[kind],'threshold':th,'sets':sets,'budget':sum(len(s)//th for s in sets),'weight_units':int(weights[col])}
 assert f['budget']==budgets[col];features.append(f)
needed=sorted(needed);lookup={v:i for i,v in enumerate(needed)};sites=[dict(original_global_index=i,**allrefs[i]) for i in needed]
for f in features:
 if 'members'in f:f['members']=[lookup[i] for i in f['members']]
 else:f['sets']=[[lookup[i] for i in ss] for ss in f['sets']]
root=json.loads((ROOT/'research/optimality/endpoint_charge/exact-trump-endpoint-rows.json').read_text())['root_interval']
report={'status':'FINITE_DISCOVERY_PROPOSAL_WITH_KNOWN_ADVERSARIAL_FAILURES','global_optimality_proved':False,'L':'191/50','B':'(191/50)/alpha','alpha_expression':'(6*t+4)/(1+2*t-t^2)','field_minimal_polynomial_ascending':[-1,2,2,-6,12,14,-2,-10,5],'field_root_interval':root,'weight_denominator':D,'threshold_units_on_numerical_training_rows':threshold,'budget_units':mass,'finite_training_counting_surplus_units':11*threshold-mass,'training_row_count':len(st['rows']),'source_state_sha256':digest(statepath),'family_sha256':digest(FAMILY),'contact_sites_sha256':digest(CONTACT),'coordinate_convention':'Each site coordinate is eight ascending rational coefficients in the displayed degree-eight field. All listed D4 member sets are explicit.','sites':sites,'features':features}
dest=OUT/'frozen';dest.mkdir(exist_ok=True);(dest/'endpoint-contact-proposal.json').write_text(json.dumps(report,indent=2)+'\n')
# Known deficient poses are transported to exact rational half-angle and normalized
# center parameters. These are proposals for exact recapture, not certified rows.
witnesses=[]
failure_packet=np.load(OUT/'deep-adversarial1/final-failures.npz')
for pose,row in zip(failure_packet['poses'],failure_packet['rows']):
 score=int(row.astype(np.int64)@weights)
 if score>=threshold:continue
 theta,x,y=pose;q=Q(float(np.tan(theta/2))).limit_denominator(10**14);c=(1-q*q)/(1+q*q);s=2*q/(1+q*q);r=B/2*float(abs(c)+abs(s));span=L-2*r
 uu=Q(float(np.clip((x-r)/span,0,1))).limit_denominator(10**14);vv=Q(float(np.clip((y-r)/span,0,1))).limit_denominator(10**14)
 witnesses.append({'half_angle':str(q),'normalized_x':str(uu),'normalized_y':str(vv),'float_original_pose':pose.tolist(),'numerical_charge_units':score,'threshold_units':threshold})
(dest/'known-adversarial-poses.json').write_text(json.dumps({'status':'NUMERICAL_DEFICITS_REQUIRING_EXACT_RECAPTURE','core_B':'(191/50)/alpha','coordinate_formula':'r=B*(abs(c)+abs(s))/2; x=r+u*(L-2*r); y=r+v*(L-2*r)','witnesses':witnesses},indent=2)+'\n')
summary={k:v for k,v in report.items() if k not in ('sites','features','coordinate_convention','field_root_interval')};summary.update({'positive_features':len(features),'distinct_sites':len(sites),'known_adversarial_deficits':len(witnesses),'proposal_sha256':digest(dest/'endpoint-contact-proposal.json'),'peak_export_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
(dest/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
