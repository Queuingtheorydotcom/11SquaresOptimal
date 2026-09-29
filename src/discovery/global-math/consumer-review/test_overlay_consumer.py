#!/usr/bin/env python3
"""Mutation controls for the antecedent-discharge consumer; never edits proof inputs."""
from pathlib import Path
from fractions import Fraction as F
import importlib.util,json,hashlib,copy,tempfile,subprocess,sys,time
D=Path(__file__).resolve().parent;ROOT=D.parents[1];FR=ROOT/'frontier'
consumer=FR/'audit_overlay_exclusion.py';spec=importlib.util.spec_from_file_location('reviewed_overlay_consumer',consumer);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
source=FR/'mask2175-overlay-v1.json';audit=FR/'mask2175-overlay-independent.json'
raw_d=json.load(open(source));raw_a=json.load(open(audit));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
start=time.time();original_hash=sha(consumer);baseline=C.validate(source,audit);tests=[]

def run_audit_mutation(name,mutate):
 a=copy.deepcopy(raw_a);mutate(a)
 with tempfile.TemporaryDirectory(prefix='overlay-consumer-',dir=D) as tmp:
  path=Path(tmp)/'audit.json';path.write_text(json.dumps(a))
  try:C.validate(source,path)
  except (AssertionError,ValueError,KeyError,TypeError,OSError) as e:tests.append({'control':name,'result':'REJECTED','exception':type(e).__name__});return
 raise RuntimeError('Mutation accepted: '+name)

cases=[
 ('nonpass_audit',lambda a:a.update(status='FAIL')),
 ('no_branch_contradiction',lambda a:a.update(branch_exclusion_proved=False)),
 ('local_guard_instead_of_contradiction',lambda a:a.update(inside_local_guard=True)),
 ('wrong_source_hash',lambda a:a.update(source_sha256='0'*64)),
 ('constraints_disagree',lambda a:a['constraints'].pop()),
 ('wrong_mask_index',lambda a:a.update(mask_index=438)),
 ('wrong_bootstrap',lambda a:a['bootstrap'].update(kind='unverified_seed')),
 ('external_root_audit',lambda a:a.update(root_audit_sha256='0'*64)),
 ('wrong_seed_hash',lambda a:a.update(root_sha256='0'*64)),
 ('wrong_cover_hash',lambda a:a.update(cover_sha256='0'*64)),
 ('wrong_U',lambda a:a.update(parent_Uplus='4')),
 ('wrong_B',lambda a:a.update(parent_side='1')),
 ('missing_nodes',lambda a:a.update(nodes=[])),
 ('duplicate_node',lambda a:a['nodes'].append(copy.deepcopy(a['nodes'][0]))),
 ('wrong_node_hash',lambda a:a['nodes'][0].update(sha256='0'*64)),
 ('wrong_node_name',lambda a:a['nodes'][0].update(node='different-node')),
 ('different_node_constraints',lambda a:a['nodes'][0]['constraints'].pop()),
 ('wrong_node_contradiction_flag',lambda a:a['nodes'][0].update(branch_exclusion_proved=False)),
 ('missing_dependency',lambda a:a['dependencies'].pop('own_hull_constraints.py')),
 ('extra_dependency',lambda a:a['dependencies'].update(unknown_checker='0'*64)),
 ('checker_hash_changed',lambda a:a['dependencies'].update({'audit_capture_v9.py':'0'*64})),
 ('kernel_hash_changed',lambda a:a['dependencies'].update({'own_hull_constraints.py':'0'*64})),
 ('wrong_final_state_digest',lambda a:a.update(final_state_sha256='0'*64)),
 ('incomplete_angle_domain',lambda a:a['bootstrap'].update(full_angle_domain=['0','1/2'])),
 ('incomplete_angle_row_count',lambda a:a['bootstrap'].update(angle_rows=1)),
 ('failed_seed_ownership_check',lambda a:a['seed_ownership_checks'][0].update(passed=False)),
 ('wrong_required_antecedent',lambda a:a.update(required_antecedent_mask=[0])),
]
for name,mutate in cases:run_audit_mutation(name,mutate)

# Bind coordinated source/audit mutations consistently, so the intended inner
# necessity/schema guard is reached. These are refusal controls, not geometric
# replays of the mutated source objects.
def coordinated(name,mutate):
 d=copy.deepcopy(raw_d);a=copy.deepcopy(raw_a);mutate(d)
 with tempfile.TemporaryDirectory(prefix='overlay-consumer-source-',dir=D) as tmp:
  sp=Path(tmp)/'source.json';ap=Path(tmp)/'audit.json'
  d['final_state']['constraints']=copy.deepcopy(d['constraints'])
  sp.write_text(json.dumps(d,separators=(',',':')))
  a['source_sha256']=sha(sp);a['constraints']=copy.deepcopy(d['constraints']);a['final_state_sha256']=C.digest(d['final_state'])
  a['nodes'][-1].update(path=str(sp),sha256=sha(sp),constraints=copy.deepcopy(d['constraints']))
  ap.write_text(json.dumps(a))
  try:C.validate(sp,ap)
  except (AssertionError,ValueError,KeyError,TypeError,OSError) as e:tests.append({'control':name,'result':'REJECTED','exception':type(e).__name__});return
 raise RuntimeError('Coordinated mutation accepted: '+name)
coordinated('unsupported_angle_constraint',lambda d:d['constraints'].append({'owner':d['mask'][0],'kind':'half_angle','keep':'le','bound_half_angle':'1/2'}))
coordinated('zero_normal',lambda d:d['constraints'][0].update(normal=['0','0']))
coordinated('owner_outside_mask',lambda d:d['constraints'][0].update(owner=0))
coordinated('narrowed_necessary_bound',lambda d:d['constraints'][0].update(upper_field=str(F(d['constraints'][0]['upper_field'])-F(1,10**12))))
coordinated('reversed_necessary_halfplane',lambda d:d['constraints'][0].update(normal=[str(-F(v)) for v in d['constraints'][0]['normal']],upper_field=str(-F(d['constraints'][0]['upper_field']))))
coordinated('unlisted_source_ancestor',lambda d:d.update(parent={'path':str(source),'sha256':sha(source)}))

for flag in ['-O','-OO']:
 p=subprocess.run([sys.executable,flag,str(consumer),str(source),str(audit),'--output',str(D/'must-not-exist.json')],capture_output=True,text=True)
 if p.returncode==0 or 'requires assertions' not in p.stderr:raise RuntimeError('Optimization flag not refused: '+flag)
 tests.append({'control':flag,'result':'REJECTED_AT_STARTUP'})

# Positive rescalings are mathematically equivalent and should be accepted.
c=raw_d['constraints'][0];q=F(7,3)
C.necessity.verify_constraints(raw_d['mask_index'],[(c['owner'],[q*F(v) for v in c['normal']],q*F(c['upper_field']))])
if sha(consumer)!=original_hash:raise RuntimeError('Consumer changed during review')
record={'status':'PASS_INDEPENDENT_CONSUMER_REVIEW_AND_MUTATION_CONTROLS','consumer':str(consumer),'consumer_sha256':original_hash,'necessity_adapter_sha256':sha(C.necessity.__file__),'source_sha256':sha(source),'geometric_audit_sha256':sha(audit),'reviewer_source_sha256':sha(Path(__file__)),'baseline_control_mask':baseline['mask_index'],'baseline_control_exclusion_proved':baseline['mask_exclusion_proved'],'negative_controls':tests,'negative_control_count':len(tests),'positive_rescaling_control':True,'seconds':time.time()-start,'scope':'Reviews and tests provenance, exact frames, complete ancestry/dependency inventory, unsupported-angle refusal, and necessary-halfplane discharge. Does not substitute for the separately completed v9 geometric replay or1931 baseline replay.'}
(D/'overlay-consumer-independent-review.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='negative_controls'},indent=2))
