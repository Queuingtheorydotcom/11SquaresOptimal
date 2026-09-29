#!/usr/bin/env python3
"""Small-receipt mutation controls for the capture composition consumer.

Immutable node payloads are read once; subsequent controls reuse their unmodified data. The
script never edits a proof input or reruns the geometry producer.
"""
from pathlib import Path
import contextlib,copy,hashlib,importlib.util,io,json,subprocess,sys,tempfile,time
D=Path(__file__).resolve().parent;HERE=D.parent/'candidate-capture';OUT=D/'capture438-consumer-review'
CHECKER=HERE/'audit_complete_capture438.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=True);start=time.monotonic();initial_checker_hash=sha(CHECKER)
 spec=importlib.util.spec_from_file_location('capture438_consumer_under_review',CHECKER);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
 original_read=C.read;cache={}
 # The consumer only reads these source fields. Retaining unmodified compact
 # views avoids keeping hundreds of megabytes of already-hash-bound steps.
 def cached_read(path):
  p=Path(path).resolve();h=C.sha(p);key=(str(p),h)
  if key not in cache:
   v=original_read(p)
   if 'node_id' in v and 'final_state' in v:
    keep={'node_id','source','parent','mask','mask_index','U','B','constraints','contradiction','final_state'}
    v={k:value for k,value in v.items() if k in keep}
   elif 'coordinate_dual_tests' in v:
    # The full proposal is hash-bound by the consumer; its arithmetic is the
    # separately replayed local-checker premise and is not read here.
    v={k:value for k,value in v.items() if k not in {'coordinate_dual_tests','unavailable_feature_checks'}}
   cache[key]=v
  return cache[key]
 C.read=cached_read
 def invoke(extra,name):
  output=OUT/(name+'-result.json');sys.argv=[str(CHECKER),'--output',str(output),*extra]
  with contextlib.redirect_stdout(io.StringIO()):C.main()
  return json.loads(output.read_text())
 positive=invoke([],'positive')
 if positive['status']!='PASS_COMPLETE_CANDIDATE438_CAPTURE_COMPOSITION' or not positive['candidate_mask_capture_proved']:raise RuntimeError('Positive composition failed')
 rows=[]
 def check(name,flag,filename,mutate):
  a=copy.deepcopy(original_read(filename));mutate(a)
  with tempfile.TemporaryDirectory(prefix='mutation-',dir=OUT) as tmp:
   path=Path(tmp)/'audit.json';path.write_text(json.dumps(a))
   try:invoke([flag,str(path)],name)
   except (AssertionError,ValueError,KeyError,TypeError,OSError) as e:
    rows.append({'name':name,'rejected':True,'reason':str(e)});return
  raise RuntimeError('Invalid receipt accepted: '+name)
 root=HERE/'root14-independent-audit.json';far=HERE/'far15y-independent-audit.json';cached=HERE/'far13-independent-audit.json';near=HERE/'near1024-independent-audit.json';local=D/'focused1024-local-box-independent.json'
 rootcases=[('root_failed',lambda a:a.update(status='FAIL')),('root_missing_dependency',lambda a:a['dependencies'].pop('audit_wall_kernel.py')),('root_conditioned',lambda a:a.update(branch_condition={'owner':0,'keep':'le','bound_half_angle':'1/2'})),('root_wrong_seed',lambda a:a.update(seed_sha256='0'*64)),('root_wrong_cover',lambda a:a.update(cover_sha256='0'*64)),('root_incomplete_round',lambda a:a.update(cells=[dict(c,complete=False) for c in a['cells']]))]
 for n,f in rootcases:check(n,'--root-audit',root,f)
 farcases=[('leaf_failed',lambda a:a.update(status='RUNNING_INDEPENDENT_TREE_AUDIT')),('leaf_wrong_root',lambda a:a.update(root_sha256='0'*64)),('leaf_wrong_mask',lambda a:a.update(mask_index=999)),('leaf_wrong_scale',lambda a:a.update(parent_side='1')),('leaf_missing_dependencies',lambda a:a.update(dependencies={})),('leaf_extra_dependency',lambda a:a['dependencies'].update(unknown='0'*64)),('leaf_missing_nodes',lambda a:a.update(nodes=[])),('leaf_duplicate_node',lambda a:a['nodes'].append(copy.deepcopy(a['nodes'][0]))),('leaf_nodes_reordered',lambda a:a['nodes'].reverse()),('leaf_wrong_node_identity',lambda a:a['nodes'][-1].update(node='unproved')),('leaf_wrong_node_assumptions',lambda a:a['nodes'][-1].update(constraints=[])),('leaf_wrong_node_contradiction',lambda a:a['nodes'][-1].update(branch_exclusion_proved=False)),('leaf_wrong_final_digest',lambda a:a.update(final_state_sha256='0'*64)),('leaf_not_excluded',lambda a:a.update(branch_exclusion_proved=False))]
 for n,f in farcases:check(n,'--far15-audit',far,f)
 check('cache_missing_premises','--far13-audit',cached,lambda a:a.update(premise_audits=[]))
 check('cache_changed_premise_hash','--far13-audit',cached,lambda a:a['premise_audits'][0].update(sha256='0'*64))
 check('cache_unproved_node','--far13-audit',cached,lambda a:a['nodes'][0].update(cached_from_audit_sha256='0'*64))
 check('near_changed_state','--near-audit',near,lambda a:a.update(final_state_sha256='0'*64))
 localcases=[('local_failed',lambda a:a.update(status='FAIL')),('local_wrong_checker',lambda a:a.update(checker_sha256='0'*64)),('local_wrong_source',lambda a:a.update(source_sha256='0'*64)),('local_changed_state',lambda a:a.update(final_state_sha256='0'*64)),('local_wrong_scope',lambda a:a.update(local_rectangle_isolation_proved=False)),('local_missing_coordinates',lambda a:a.update(coordinate_certificates_checked=8447)),('local_nonstrict_dual',lambda a:a.update(worst_dual_ratio='1')),('local_negative_dual',lambda a:a.update(worst_dual_ratio='-1')),('local_missing_features',lambda a:a.update(feature_stability=[])),('local_duplicate_feature',lambda a:a['feature_stability'].__setitem__(0,copy.deepcopy(a['feature_stability'][1]))),('local_missing_roles',lambda a:a['inclusion'].pop()),('local_duplicate_role',lambda a:a['inclusion'].append(copy.deepcopy(a['inclusion'][0]))),('local_outside_working_box',lambda a:a['radii'].__setitem__(0,'1')),('local_bad_guard_binding',lambda a:a.update(guard_assignment_source_sha256='0'*64))]
 for n,f in localcases:check(n,'--local-audit',local,f)
 for opt in ['-O','-OO']:
  p=subprocess.run([sys.executable,opt,str(CHECKER),'--output',str(OUT/'forbidden.json')],capture_output=True,text=True)
  if p.returncode==0 or 'assertions' not in p.stderr:raise RuntimeError('Optimized mode not refused')
  rows.append({'name':opt,'rejected':True,'reason':p.stderr.strip()})
 if sha(CHECKER)!=initial_checker_hash:raise RuntimeError('Consumer changed during review')
 result={'status':'PASS_INDEPENDENT_CAPTURE438_CONSUMER_MUTATION_REVIEW','consumer_sha256':initial_checker_hash,'test_driver_sha256':sha(__file__),'positive_receipt_sha256':sha(OUT/'positive-result.json'),'local_receipt_sha256':sha(local),'controls':rows,'control_count':len(rows),'geometry_replayed':False,'scope':'Checks the composition consumer and malformed small receipts. Separately completed exact geometry and local-dual replays remain premises. No global optimality is claimed.','seconds':time.monotonic()-start}
 (OUT/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='controls'},indent=2))
if __name__=='__main__':main()
