"""Compose the exact theorem from unchanged, source-bound checked evidence.

This verifies the complete bundle and recorded mathematical results. It does
not rerun every geometric computation. Full replay has separate entry points.
No global PASS is emitted unless every set, source, and composition gate passes.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import argparse,hashlib,importlib.util,importlib.machinery,types,json,sys,time

BASE=Path(__file__).resolve().parents[1]
U=F(387708359002281417731,10**20);B=F(191,50)/U
CANDIDATES={438,999,1462,1659}
BASELINE='04fa1ebb37f5dace29946224fe8c7c5d8a1bedb4fa860c65b359f4200415de57'
COVER='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
SOURCE_PINS={
 'code/verify_returned.py':'27636b27332d5890424be5771cb9324725c430727ea1adacfafd1fa8f1695296',
 'research/finalization/baseline-portable/verify_baseline.py':'85a2ce60a17bc3f3c8f890d7961cf2d35e881595d76feb7a7dab513023f0589c',
 'research/finalization/baseline-portable/baseline_reconstruct.py':'ec47984510e847bbbb87dc924d8865fb5ff4510f0ce7c8558f55531b502a1b0c', 
 'research/candidate-capture/audit_complete_capture438.py':'0ca02cfb0fa5304251f80fff0356dd63e33a87ffb74b8ada5c5a17cfa8afa040',
 'research/phase3/work/phase3/hull/audit_capture_v9.py':'95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c',
 'research/audit-lower-bound/strict_generic_inventory.py':'7df54d904bb5d0cc609a4765eeafc3fb57922bcb3a4b210082df9fda36266530',
 'research/audit-lower-bound/strict_tree_inventory.py':'b6a298ccfa1a27911b3e88c832f890a983e0c6e7c374455808e42eb730626059',
 'research/finalization/global-composition/audit_d4_bridge.py':'f44b2a589ba201ea49ef971245790b885529702537a1dd45640ae51752de6b09',
 'code/replay_candidate.py':'fb8866d02e42aaf674e2ce966c8ab3fe0eb70e0d4f3957f7afd14cd117436d4b',
 'code/replay_prior.py':'e2292e844827d811d61f8cefb0158442febae097cbcdc92e414dd59f018dde14',
}
STAGES={
 'construction':'PASS_EXACT_CONSTRUCTION_AND_SIDE_CAP',
 'cover':'PASS_INDEPENDENT_EXACT_CENTER_COVER_AUDIT',
 'local-algebra':'PASS_INDEPENDENT_LOCAL_ALGEBRA_CHECKS',
 'local-baseline':'PASS_INDEPENDENT_QUANTITATIVE_RADIUS_AUDIT',
 'local-weighted':'PASS_INDEPENDENT_WEIGHTED_COORDINATE_RADIUS_AUDIT',
 'focused':'PASS_INDEPENDENT_FOCUSED_RECTANGLE_LOCAL_ISOLATION',
 'feature-bridge':'PASS_THIRD_SOURCE_NONLINEAR_FEATURE_BRANCH_BRIDGE',
 'composition':'PASS_COMPLETE_CANDIDATE438_CAPTURE_COMPOSITION',
 'consumer-tests':'PASS_INDEPENDENT_CAPTURE438_CONSUMER_MUTATION_REVIEW',
}

def need(value,message):
    if not value:raise ValueError(message)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def path(name):
    p=(BASE/name).resolve();need(p.is_relative_to(BASE),'Path outside proof package');return p
def raw(name):return json.loads(path(name).read_text())
def load_source(name,module_name):
    spec=importlib.util.spec_from_file_location(module_name,path(name))
    module=importlib.util.module_from_spec(spec)
    exec(compile(path(name).read_bytes(),str(path(name)),'exec'),module.__dict__)
    return module

def validate(manifest_name='inputs/PROOF_MANIFEST.json'):
    manifest=raw(manifest_name);need(manifest['schema']=='eleven-square-proof-manifest-v1','Wrong manifest')
    inventory={};total=0
    for record in manifest['files']:
        name=record['path'];p=path(name)
        need(name not in inventory and not Path(name).is_absolute() and '..' not in Path(name).parts,'Duplicate/unsafe input')
        need(p.is_file() and not (BASE/name).is_symlink(),'Missing/linked proof input: '+name)
        need(p.stat().st_size==record['bytes'] and sha(p)==record['sha256'],'Input bytes changed: '+name)
        inventory[name]=record['sha256'];total+=record['bytes']
    need(len(inventory)==manifest['file_count'] and total==manifest['logical_bytes'],'Incomplete manifest')
    def bound(name,expected=None):
        need(name in inventory,'Unmanifested premise: '+name)
        if expected is not None:need(inventory[name]==expected,'Wrong source identity: '+name)
        return raw(name)
    for name,h in SOURCE_PINS.items():need(inventory.get(name)==h,'Reviewed code changed: '+name)
    # Imported proof modules execute source bytes, never cached bytecode.
    class SourceLoader(importlib.machinery.SourceFileLoader):
        def get_code(self,fullname):
            source=Path(self.path).resolve();relative=source.relative_to(BASE).as_posix()
            need(inventory.get(relative)==sha(source),'Unbound imported proof source')
            return compile(source.read_bytes(),str(source),'exec')
    class SourceFinder:
        def find_spec(self,fullname,search_path=None,target=None):
            spec=importlib.machinery.PathFinder.find_spec(fullname,search_path,target)
            if spec and spec.origin and Path(spec.origin).resolve().is_relative_to(BASE):
                need(spec.origin.endswith('.py'),'Non-source packaged proof import')
                spec.loader=SourceLoader(fullname,spec.origin)
                return spec
            return None
    sys.meta_path.insert(0,SourceFinder())
    bound('research/PHASE3_FRESH_REPLAY_RESULT.json',BASELINE)
    cover_name='research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json'
    cover=bound(cover_name,COVER)
    turn=lambda J:tuple(sorted(15-j for j in J))
    canonical=sorted({min(J,turn(J)) for J in combinations(range(16),11)})
    need(len(canonical)==2184 and list(map(list,canonical))==cover['canonical_eleven_cell_subsets'],'Wrong canonical universe')
    evidence=[]
    def premise(name,status):
        value=bound(name);need(value['status']==status,'Unaccepted premise: '+name)
        evidence.append(dict(path=name,sha256=inventory[name],status=status));return value

    old=bound('research/PHASE3_FRESH_REPLAY_RESULT.json')
    baseline=premise('results/baseline-portable/HISTORICAL_BASELINE_RESULT.json',
                     'PASS_HISTORICAL_BASELINE_BINDINGS_AND_EXACT_UNION')
    need(baseline['fresh_geometry_replayed'] is False,'Historical reuse incorrectly described')
    need(baseline['field_certificates']==59 and baseline['generic_certificates']==34 and
         baseline['excluded']==1931 and baseline['remaining']==253,'Incomplete baseline proof family')
    need(baseline['excluded_canonical_mask_indices']==old['excluded_canonical_mask_indices'],
         'Baseline reuse disagrees with actual earlier fresh computation')
    need(baseline['historical_receipt_sha256']==BASELINE,'Wrong historical baseline')

    baseline_dir='research/finalization/baseline-portable/'
    need(baseline['adapter_sha256']==inventory[baseline_dir+'verify_baseline.py'] and
         baseline['union_consumer_sha256']==inventory[baseline_dir+'baseline_reconstruct.py'],
         'Baseline source identity differs')
    bi=bound(baseline_dir+'SOURCE_INVENTORY.json',baseline['source_inventory_sha256'])
    need(len(bi['files'])==baseline['verified_source_files']==498,'Baseline source list incomplete')
    for item in bi['files']:need(inventory.get(item['path'])==item['sha256'],'Baseline proof source missing')

    prior=premise('results/prior-union/PRIOR_UNION_RESULT.json','PASS_STRICT_PRIOR_76_EXTENSION_INTEGRATION')
    need(prior['fresh_baseline_geometry_replay_completed'] is True and
         prior['fresh_baseline_replay']['sha256']==BASELINE,'Prior union lacks the completed baseline')
    need(prior['extension_receipts']==prior['distinct_extension_cases']==76,'Missing extension receipts')
    need(prior['excluded_canonical_cases']==2007 and prior['remaining_canonical_cases']==177,'Wrong prior union size')
    need(prior['new_cases_since_previous_strict']==[927,998,1111,1112,1114,1115,1124,1125,1128,1143],
         'Ten-case reconciliation differs')
    prepared_name='research/finalization/prior-union/SOURCE_INVENTORY.json'
    prepared=bound(prepared_name,prior['prepared_inventory_sha256'])
    trace=bound('results/prior-union/PORTABLE_PRIOR_IO_TRACE.json')
    need(trace['status']=='PASS_PACKAGE_ONLY_PRIOR_INTEGRATION' and
         trace['launcher_sha256']==inventory['code/replay_prior.py'] and
         trace['output_sha256']==inventory['results/prior-union/PRIOR_UNION_RESULT.json'] and
         trace['outside_package_proof_fallback'] is False,'Prior package execution unbound')
    need(prior['integration_checker_sha256']==trace['integration_checker_sha256']==
         inventory['research/finalization/prior-union/integrate_prior_union.py'],'Prior integrator changed')
    validated_name='results/prior-union/validated-source-inventory.json' 
    validated=bound(validated_name,prior['validated_source_inventory_sha256'])
    need(validated['status']=='PASS_STREAMED_SOURCE_BINDINGS','Prior source inventory incomplete')
    need(len(prepared['files'])==len(validated['files'])==304,'Prior proof source inventory differs')
    for p,v in zip(prepared['files'],validated['files'],strict=True):
        need(p['target']==v['target'] and p['expected_sha256']==v['sha256']==inventory.get(p['target']),
             'Prior source not preserved: '+p['target'])
    old_cases=set(old['excluded_canonical_mask_indices']);prior_cases=set(prior['excluded_canonical_mask_indices'])
    need(len(old_cases)==1931 and old_cases<=prior_cases,'Prior set lost baseline cases')
    extension_cases=set()
    need(len(prior['extension_entries'])==len(prepared['entries'])==76,'Incomplete extension inventory')
    for accepted,selection in zip(prior['extension_entries'],prepared['entries'],strict=True):
        need(accepted['audit_sha256']==selection['audit_sha256']==inventory.get(selection['audit_target']),
             'Extension receipt binding changed')
        need(accepted['cases']==selection['expected_cases']==[selection['mask_index']],
             'Extension case identity changed')
        extension_cases.update(accepted['cases'])
    need(len(extension_cases)==76 and not old_cases&extension_cases and old_cases|extension_cases==prior_cases,
         'Extension union not exact')

    returned=premise('results/returned/SUMMARY.json','PASS_ALL_173_RETURNED_CASES')
    checker=load_source('code/verify_returned.py','global_returned_checkpoint_consumer')
    dependencies=checker.load_checker()[1]
    need(returned['adapter_sha256']==inventory['code/verify_returned.py']==checker.source_identity(),
         'Returned replay used another adapter')
    need(returned['plan_sha256']==checker.PLAN_HASH==inventory['inputs/returned-replay-plan.json'] and
         returned['assignment_sha256']==checker.ASSIGNMENT_HASH==inventory['inputs/CASE_ASSIGNMENTS.json'],
         'Returned assignment/source plan changed')
    plans=bound('inputs/returned-replay-plan.json')['cases'];assignment=bound('inputs/CASE_ASSIGNMENTS.json')
    assigned={m for job in assignment['jobs'] for m in job['mask_indices']}
    new_cases={c['mask_index'] for c in plans}
    need(len(plans)==len(new_cases)==len(assigned)==173 and new_cases==assigned,'Returned case set not exact')
    need(returned['completed']==returned['required']==173 and returned['unresolved_cases']==[] and
         set(returned['completed_cases'])==new_cases,'Returned summary omits cases')
    for case in plans:
        m=case['mask_index']
        bound(f'results/returned/mask{m}-verified.json');bound(f'results/returned/mask{m}-fresh-audit.json')
        need(case['archive'] in inventory,'Returned archive absent from proof manifest')
        checker.validate_checkpoint(case,dependencies,list(map(list,canonical)))
    need(len(prior_cases)==2007 and not prior_cases&new_cases,'Prior/returned cases overlap')
    excluded=prior_cases|new_cases
    need(len(excluded)==2180 and excluded==set(range(2184))-CANDIDATES,'Global exclusion universe has a gap')

    d4=premise('results/d4-bridge.json','PASS_EXACT_CONDITIONAL_D4_BRIDGE')
    need(d4['checker_sha256']==SOURCE_PINS['research/finalization/global-composition/audit_d4_bridge.py'],
         'Symmetry checker source mismatch')
    need(d4['conditional_d4_bridge_proved'] is True and d4['geometry_checked_from_source'] is True,
         'Symmetry lemma not proved')
    need(F(d4['U'])==U and d4['canonical_index_base']==0 and d4['canonical_count']==2184 and d4['raw_count']==4368,
         'Symmetry lemma uses another universe')
    need(d4['overlay_dimensions']=={'0':8,'2':212} and d4['strict_distance_bans']==1572,'Boundary geometry differs')
    need({r['source_canonical_index'] for r in d4['finite_search']}==CANDIDATES-{438} and
         all(r['status']=='UNSAT' for r in d4['finite_search']),'Symmetry search incomplete')
    d4_sources={'cover':cover_name,'overlay':'research/phase3/work/phase2/geometry/cover_overlay_exact.json',
                'distance':'research/phase3/work/phase2/geometry/overlay_distance_pairs.json'}
    for k,name in d4_sources.items():need(d4['sources'][k]['sha256']==inventory.get(name),'Symmetry source changed')
    need(set(d4['candidate_masks'])==set(map(str,CANDIDATES)) and len(d4['finite_search'])==3,
         'Incomplete D4 candidate inventory')
    expected_raw=sorted({canonical[i] for i in CANDIDATES-{438}}|{turn(canonical[i]) for i in CANDIDATES-{438}})
    need(d4['allowed_non_target_raw_masks']==list(map(list,expected_raw)),'Wrong D4 allowed masks')
    for k,J in d4['candidate_masks'].items():need(list(canonical[int(k)])==J,'Symmetry candidate mask differs')

    candidate=premise('results/candidate-replay/summary.json','PASS_PORTABLE_CANDIDATE_PACKAGE_REPLAY')
    need(candidate['stage_count']==len(STAGES)==len(candidate['stages']) and
         {r['stage'] for r in candidate['stages']}==set(STAGES),'Candidate stages incomplete')
    need(candidate['launcher_sha256']==inventory['code/replay_candidate.py'],'Candidate adapter changed')
    stage_data={}
    for s in candidate['stages']:
        name=s['stage'];expected_result=f'results/candidate-replay/{name}.json'
        need(s['result']==expected_result and s['status']==STAGES[name],'Candidate stage identity differs')
        value=bound(expected_result,s['result_sha256']);need(value['status']==STAGES[name],'Candidate result rejected')
        trace=bound(s['io_trace'],s['io_trace_sha256'])
        need(trace['status']=='PASS_PACKAGE_ONLY_REPLAY' and trace['stage']==name and
             trace['launcher_sha256']==candidate['launcher_sha256'] and
             trace['output_sha256']==s['result_sha256'],'Candidate execution not bound')
        need(trace['source_bytecode_disabled'] is True and trace['historical_evidence_modified'] is False,
             'Candidate source execution condition changed')
        for reference in trace['package_proof_files_read']:
            if reference.startswith(('research/','code/')):need(reference in inventory,'Missing read proof dependency')
        stage_data[name]=value
    cp=bound('inputs/candidate-composition-pins.json',
             'f5c66ab125f7a4695039197ae52b5ce5ee2dd2365142e4cf8488a220f250f5d5')
    selected=[{k:pair[k] for k in ('stage','accepted_premise','ignored_metadata_fields')}
              for pair in candidate['accepted_premise_comparisons']]
    need(selected==cp['comparisons'] and len(selected)==6,'Local comparison list or exceptions changed')
    for pair in candidate['accepted_premise_comparisons']:
        old_value=bound(pair['accepted_premise'],pair['accepted_premise_sha256'])
        skip=set(pair['ignored_metadata_fields']);clean=lambda d:{k:v for k,v in d.items() if k not in skip}
        need(clean(stage_data[pair['stage']])==clean(old_value),'Fresh/local historical conclusions differ')
    construction=stage_data['construction'];report=construction['report']
    need(report['valid'] is True and report['n']==11 and report['pairs_tested']==55 and report['failures']==[],
         'Attaining packing not verified')
    need(construction['T_strictly_below_U'] is True and construction['side_polynomial_checked'] is True,
         'Endpoint/cap comparison missing')
    need({(r['axis'],r['wall']) for r in construction['opposite_wall_contacts']}==
         {(i,w) for i in (0,1) for w in ('lower','upper')} and
         all(r['corners'] for r in construction['opposite_wall_contacts']),'Full span missing')
    c=stage_data['cover'];need(c['source_sha256']==COVER and c['half_turn_cells_checked']==16 and
         c['canonical_masks']==2184 and F(c['maximum_physical_diameter_squared'])<1,'Cover reduction unproved')
    capture=stage_data['composition']
    need(capture['checker_sha256']==SOURCE_PINS['research/candidate-capture/audit_complete_capture438.py'] and
         capture['mask_index']==438 and capture['required_antecedent_mask']==list(canonical[438]),'Capture case differs')
    need(capture['candidate_mask_capture_proved'] is True and capture['no_smaller_packing_for_this_mask'] is True,
         'Candidate implication absent')
    need(F(capture['parent_Uplus'])==U and F(capture['parent_side'])==B and
         capture['partition_covers_all_real_center_values_and_closed_half_angles'] is True and
         capture['coordinate_bridge']['U_to_T_translation_accounted_for'] is True,'Capture domain mismatch')
    need(capture['bound_premises']==cp['bound_premises'] and len(cp['bound_premises'])==24,
         'Capture premise inventory incomplete')
    need(capture['geometry_nodes']==cp['geometry_nodes'] and len(cp['geometry_nodes'])==10,
         'Capture ancestry inventory incomplete')
    for name,h in capture['geometry_nodes'].items():need(inventory.get(name)==h,'Capture ancestor changed')
    need(capture['local_rectangle_audit_sha256']==inventory['research/global-math/focused1024-local-box-independent.json'],
         'Capture uses different local theorem')
    for name,h in capture['bound_premises'].items():need(inventory.get(name)==h,'Capture premise changed: '+name)
    local=stage_data['focused']
    need(local['local_rectangle_isolation_proved'] is True and local['coordinate_certificates_checked']==8448 and
         0<F(local['worst_dual_ratio'])<1,'Local isolation not certified')
    need(local['source_sha256']==inventory['research/candidate-capture/near-refined1024-240.json'],
         'Local rectangle uses different near-state source')
    tests=stage_data['consumer-tests']
    need(tests['consumer_sha256']==capture['checker_sha256'],'Consumer tests use another checker')
    need(tests['control_count']==40==len(tests['controls']) and all(t['rejected'] for t in tests['controls']),
         'Consumer rejection controls incomplete')
    return dict(schema='eleven-square-global-proof-v1',status='PASS_COMPLETE_ELEVEN_SQUARE_OPTIMALITY',
        theorem='For eleven congruent unit squares with pairwise disjoint interiors in a square container, allowing arbitrary rotations, the minimum container side is T.',
        endpoint=dict(root_polynomial_descending=[5,-10,-2,14,12,-6,2,2,-1],root_isolating_interval=['9/25','37/100'],
                      side_formula='T=(6u+4)/(1+2u-u^2)',approximate_side='3.8770835900228141773078970601'),
        rational_cap=str(U),field_side=str(F(191,50)),homothety=str(B),
        canonical_cases=2184,baseline_exclusions=1931,prior_extensions=76,returned_exclusions=173,
        all_noncandidate_exclusions=len(excluded),excluded_canonical_mask_indices=sorted(excluded),
        surviving_canonical_cases=sorted(CANDIDATES),captured_case=438,
        symmetry_premise_discharged=True,exact_construction_verified=True,lower_bound_proved=True,
        global_optimality_proved=True,proof_kind='Computer-assisted exact certificate proof; not proof-assistant formalization',
        acceptance_mode='Integrity and strict composition of source-bound recorded computations',
        all_geometry_reexecuted_by_this_command=False,
        mathematical_argument='A smaller packing has a valid covered case; the exact noncandidate union and D4 lemma force a case438 image; capture and local isolation force the exact span-T construction, contradicting its smaller container. The exact construction attains T.',
        premises=evidence,proof_manifest=manifest_name,proof_manifest_sha256=sha(path(manifest_name)),
        input_files_checked=len(inventory),input_bytes_checked=total,checker_sha256=sha(__file__))

def main():
    if not __debug__:raise SystemExit('Assertions must remain enabled')
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results/recorded-proof-check.json');a=ap.parse_args()
    start=time.monotonic();result=validate();result['seconds']=time.monotonic()-start
    target=path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','all_noncandidate_exclusions','surviving_canonical_cases',
                                          'global_optimality_proved','proof_manifest_sha256','seconds')},indent=2))
if __name__=='__main__':main()
