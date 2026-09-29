#!/usr/bin/env python3
"""Collect completed package replays and compare their mathematical outputs."""
from pathlib import Path
import argparse,hashlib,json

def need(v,s):
    if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('package',type=Path);a=ap.parse_args()
    P=a.package.resolve();D=P/'results/candidate-replay';stages=['construction','cover','local-algebra','local-baseline','local-weighted','focused','feature-bridge','composition','consumer-tests']
    checks=[]
    launcher=sha(P/'code/replay_candidate.py')
    for s in stages:
        p=D/(s+'.json');t=D/(s+'-io.json');r=read(p);io=read(t)
        need(r['status'].startswith('PASS'),'Stage failed '+s)
        need(io['status']=='PASS_PACKAGE_ONLY_REPLAY' and io['stage']==s,'Wrong I/O trace '+s)
        need(io['launcher_sha256']==launcher and io['output_sha256']==sha(p),'Unbound I/O trace '+s)
        need(io['source_bytecode_disabled'] and not io['historical_evidence_modified'],'Unsafe source state '+s)
        need(all(not Path(q).is_absolute() and '..' not in Path(q).parts for q in io['package_proof_files_read']),'Invalid package read path '+s)
        checks.append({'stage':s,'status':r['status'],'result':str(p.relative_to(P)),'result_sha256':sha(p),
                       'io_trace':str(t.relative_to(P)),'io_trace_sha256':sha(t),
                       'logged_package_reads':len(io['package_proof_files_read']),
                       'historical_paths_remapped':len(io['historical_paths_remapped']),
                       'reported_checker_seconds':r.get('seconds')})
    comparisons=[]
    pairs=[('local-algebra','research/local-radius/fresh-local-algebra.json',{'seconds','python_version'}),
           ('local-baseline','research/local-radius/fresh-baseline-radius.json',{'seconds'}),
           ('local-weighted','research/local-radius/fresh-weighted-coordinate-radius.json',{'seconds'}),
           ('focused','research/global-math/focused1024-local-box-independent.json',{'seconds','source','proposal'}),
           ('feature-bridge','research/endpoint-audit/focused-feature-bridge-review.json',{'seconds'}),
           ('cover','research/local-radius/fresh-center-cover-verification.json',set())]
    for stage,path,skip in pairs:
        new,old=read(D/(stage+'.json')),read(P/path)
        clean=lambda v:{k:x for k,x in v.items() if k not in skip}
        need(clean(new)==clean(old),'Mathematical result differs from accepted premise: '+stage)
        comparisons.append({'stage':stage,'accepted_premise':path,'accepted_premise_sha256':sha(P/path),
                            'ignored_metadata_fields':sorted(skip),'remaining_fields_identical':True})
    c=read(D/'composition.json');tests=read(D/'consumer-tests.json')
    need(c['candidate_mask_capture_proved'] and c['no_smaller_packing_for_this_mask'],'Missing case438 theorem')
    need(not c['global_optimality_proved'],'Candidate lane must not assert global optimality')
    checker=P/'research/candidate-capture/audit_complete_capture438.py'
    need(c['checker_sha256']==tests['consumer_sha256']==sha(checker),'Consumer/checker source mismatch')
    need(tests['control_count']==len(tests['controls']) and all(v['rejected'] for v in tests['controls']),'Negative control not rejected')
    out={'status':'PASS_PORTABLE_CANDIDATE_PACKAGE_REPLAY','launcher_sha256':launcher,
         'composition_checker_sha256':sha(checker),'summary_script_sha256':sha(Path(__file__)),
         'stage_count':len(checks),'stages':checks,'accepted_premise_comparisons':comparisons,
         'negative_controls_rejected':tests['control_count'],'runtime_failures':[],
         'candidate_mask_capture_proved':True,'mask_index':438,
         'scope':'Actual side S<=exact T in mask438; complete noncandidate union and D4 bridge remain separate premises.',
         'no_smaller_packing_for_this_mask':True,'global_optimality_proved':False,
         'source_evidence_modified':False,'large_branch_geometry_replayed':False,
         'io_guarantee':'Proof stages executed with package-only Python open auditing and pinned proof source imports; ordinary runtime libraries allowed. This is not an OS sandbox.'}
    (D/'summary.json').write_text(json.dumps(out,indent=2)+'\n')
    lines=['# Packaged candidate replay: PASS','','All nine sequential stages passed. No launcher/runtime failure occurred and no mathematical evidence file was modified.','',
           '| Stage | Result | Seconds reported by checker |','| --- | --- | --- |']
    lines += [f"| {v['stage']} | {v['status']} | {v['reported_checker_seconds']} |" for v in checks]
    lines += ['',f"All {tests['control_count']} malformed-input/optimized-mode controls were rejected.",'',
              'Six independently replayed mathematical outputs equal their prior accepted premises after removing only the listed timing/runtime/path metadata. See summary.json for all result, checker and I/O-trace hashes.','',
              'The proved candidate statement remains mask438 at actual side S<=T. This report does not claim global optimality; the noncandidate exclusion union and D4 reduction are separate prerequisites.','',
              'No large branch geometry replay was repeated. Its already accepted source-bound independent receipts were verified by the complete composition.']
    (D/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:out[k] for k in ['status','stage_count','negative_controls_rejected','launcher_sha256','composition_checker_sha256','global_optimality_proved']},indent=2))
if __name__=='__main__':main()
