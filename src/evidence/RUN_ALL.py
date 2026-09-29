#!/usr/bin/env python3
"""One-command full exact verification. Stops at the first failure.

Run with the supplied working Python environment or install requirements.txt.
The complete combined run has not yet finished. A checked recovery mode can
reuse stages 1-4 from the run stopped by the missing stage-5 argument.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, shutil, subprocess, sys, time

BASE=Path(__file__).resolve().parent

def need(value,message):
    if not value:raise ValueError(message)

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def read(path):return json.loads(path.read_text())

def confined(root,name):
    relative=Path(name)
    need(not relative.is_absolute() and '..' not in relative.parts,'Unsafe recovery path')
    target=root/relative
    need(target.resolve()==target.absolute() and target.is_file(),'Missing or redirected recovery file: '+str(target))
    return target

def check_saved_geometry(snapshot,source_hashes):
    """Check receipt bindings; the successful original run did the geometry."""
    def saved(name,expected=None):
        relative=Path(name)
        need(relative.parts[0]=='results','Recovery reference is not a result')
        p=confined(snapshot,relative.relative_to('results'))
        if expected is not None:need(sha(p)==expected,'Saved output hash differs: '+name)
        return read(p)
    def bound_sources(bindings):
        for name,digest in bindings.items():
            need(source_hashes.get(name)==digest,'Saved checker/input changed: '+name)

    baseline=saved('results/baseline-portable/FRESH_BASELINE_RESULT.json')
    need(baseline['status']=='PASS_PORTABLE_FRESH_1931_CASE_BASELINE' and
         baseline['fresh_geometry_replayed'] is True,'Missing complete fresh baseline')
    need((baseline['field_certificates'],baseline['generic_certificates'],baseline['excluded'])==(59,34,1931),
         'Incomplete fresh baseline inventory')
    bound_sources({'research/finalization/baseline-portable/verify_baseline.py':baseline['adapter_sha256'],
                   'research/finalization/baseline-portable/baseline_reconstruct.py':baseline['union_consumer_sha256'],
                   'research/finalization/baseline-portable/SOURCE_INVENTORY.json':baseline['source_inventory_sha256']})
    wanted={f'{family}-{i:02d}' for family,count in [('field',59),('generic',34)] for i in range(count)}
    need(set(baseline['fresh_stage_trace_sha256'])==wanted,'Missing baseline trace')
    for key,digest in baseline['fresh_stage_trace_sha256'].items():
        trace=saved('results/baseline-portable/'+key+'.trace.json',digest)
        family,index=key.split('-')
        need(trace['status']=='PASS_FRESH_BASELINE_CERTIFICATE' and trace['fresh_geometry_replayed'] is True and
             trace['family']==family and trace['index']==int(index),'Wrong baseline trace')
        need(trace['adapter_sha256']==baseline['adapter_sha256'] and
             trace['output']=='results/baseline-portable/'+key+'.json','Baseline output identity differs')
        bound_sources(trace['selected_source_hashes'])
        saved(trace['output'],trace['output_sha256'])

    prior=saved('results/prior-geometry/SUMMARY.json')
    need(prior['status']=='PASS_ALL_76_FRESH_PRIOR_EXTENSION_GEOMETRY' and
         prior['extension_cases']==76 and prior['overlay_premise_stages']==2 and
         prior['imported_historical_node_caches'] is False,'Missing complete prior geometry')
    inventory_name='research/finalization/prior-union/SOURCE_INVENTORY.json'
    bound_sources({'code/replay_prior_geometry.py':prior['adapter_sha256'],
                   inventory_name:prior['source_inventory_sha256']})
    entries=read(BASE/inventory_name)['entries']
    wanted={'overlay-geometry','overlay-support'}|{f"mask{e['mask_index']}" for e in entries}
    need(len(entries)==76 and len(wanted)==78 and set(prior['children'])==wanted,'Prior child inventory differs')
    for key,binding in prior['children'].items():
        need(binding['path']=='results/prior-geometry/'+key+'-verified.json','Wrong prior child path')
        child=saved(binding['path'],binding['sha256'])
        expected='PASS_FRESH_PRIOR_EXTENSION_GEOMETRY' if key.startswith('mask') else 'PASS_FRESH_'+key.upper().replace('-','_')
        need(child['status']==expected and child['adapter_sha256']==prior['adapter_sha256'] and
             child['source_inventory_sha256']==prior['source_inventory_sha256'] and
             child['imported_historical_node_caches'] is False,'Unaccepted prior child')
        if key.startswith('mask'):need(child['mask_index']==int(key[4:]),'Prior case substituted')
        bound_sources(child['input_bindings'])
        need(bool(child['outputs']),'Prior child has no output')
        for name,digest in child['outputs'].items():saved(name,digest)

    returned=saved('results/returned/SUMMARY.json')
    plan=read(BASE/'inputs/returned-replay-plan.json')['cases']
    wanted={c['mask_index'] for c in plan}
    need(returned['status']=='PASS_ALL_173_RETURNED_CASES' and
         returned['completed']==returned['required']==len(plan)==len(wanted)==173 and
         len(returned['completed_cases'])==173 and set(returned['completed_cases'])==wanted and
         returned['unresolved_cases']==[],'Missing complete returned geometry')
    bound_sources({'code/verify_returned.py':returned['adapter_sha256'],
                   'inputs/returned-replay-plan.json':returned['plan_sha256'],
                   'inputs/CASE_ASSIGNMENTS.json':returned['assignment_sha256']})
    for case in plan:
        m=case['mask_index'];record=saved(f'results/returned/mask{m}-verified.json')
        need(record['status']=='PASS_FRESH_INDEPENDENT_RETURNED_CASE' and record['mask_index']==m and
             record['mask_exclusion_proved'] is True and record['adapter_sha256']==returned['adapter_sha256'] and
             record['checker_sha256']==returned['checker_sha256'] and
             record['source_sha256']==case['source_sha256'] and record['root_sha256']==case['root_sha256'] and
             record['plan_sha256']==returned['plan_sha256'] and record['assignment_sha256']==returned['assignment_sha256'],
             'Returned checkpoint differs')
        need(record['fresh_audit']==f'results/returned/mask{m}-fresh-audit.json','Returned output substituted')
        audit=saved(record['fresh_audit'],record['fresh_audit_sha256'])
        need(audit['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT' and audit['mask_index']==m and
             audit['mask_exclusion_proved'] is True and audit['source_sha256']==case['source_sha256'] and
             audit['root_sha256']==case['root_sha256'],'Returned audit does not match its checkpoint')

def prepare_resume(run_id,jobs):
    need(run_id==Path(run_id).name and run_id not in ('','.','..'),'Use the saved run directory name')
    old=BASE/'run-history'/run_id
    need(old.resolve()==old.absolute() and old.is_dir(),'Missing or redirected saved run')
    progress_path=confined(old,'progress.json');records=read(progress_path)
    need(len(records)==5 and [r['stage'] for r in records]==[name for name,args in jobs[:5]],
         'This recovery mode requires a run stopped at stage 5')
    need(all(r['exit_code']==0 for r in records[:4]) and records[4]['exit_code']==2,
         'The first four stages must have passed, followed by the stage-5 argument error')
    error=confined(old,'prior-strict-integration.log').read_text()
    need('the following arguments are required: --package-root' in error,'Not the supported stage-5 failure')
    original=confined(old,'original-manifest.json')
    need(sha(original)==sha(BASE/'inputs/PROOF_MANIFEST.json'),'The package manifest changed since this run')
    manifest=read(original);hashes={};total=0
    need(manifest['schema']=='eleven-square-proof-manifest-v1','Wrong saved manifest')
    for item in manifest['files']:
        name=item['path'];p=confined(BASE,name)
        need(name not in hashes,'Duplicate manifest entry')
        need(p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],'Packaged input changed: '+name)
        hashes[name]=item['sha256'];total+=item['bytes']
    need(len(hashes)==manifest['file_count'] and total==manifest['logical_bytes'],'Incomplete saved manifest')
    snapshot=old/'partial-results'
    need(snapshot.is_dir() and snapshot.resolve()==snapshot.absolute(),'Missing saved completed results')
    check_saved_geometry(snapshot,hashes)
    files=[]
    for p in sorted(snapshot.rglob('*')):
        need(not p.is_symlink(),'Linked recovery output')
        if p.is_file():files.append(dict(path=str(p.relative_to(snapshot)),bytes=p.stat().st_size,sha256=sha(p)))
    logs=[]
    for row in records[:4]:
        logfile=confined(BASE,row['log'])
        need(logfile.parent==old and logfile.stat().st_size>0,'Missing completed stage log')
        logs.append(dict(path=row['log'],sha256=sha(logfile)))
    metadata=dict(schema='eleven-square-stage4-recovery-v1',source_run=run_id,
                  source_progress_sha256=sha(progress_path),source_manifest_sha256=sha(original),
                  completed_stage_logs=logs,saved_result_files=files,
                  scope='Reuse the four stages that actually completed; verify input and receipt bindings without rerunning their geometry.')
    return old,records[:4],metadata

def build_jobs():
    jobs=[
      ('original-package-check',['code/verify_recorded_proof.py','--output','results/recorded-proof-check.json']),
      ('baseline-full-geometry',['research/finalization/baseline-portable/verify_baseline.py','--package-root',str(BASE),'all']),
      ('prior-76-full-geometry',['code/replay_prior_geometry.py','--stage','all']),
      ('returned-173-full-geometry',['code/verify_returned.py']),
      ('prior-strict-integration',['code/replay_prior.py','--package-root',str(BASE)]),
      ('symmetry',['code/verify_d4.py']),
    ]
    for stage in ['construction','cover','local-algebra','local-baseline','local-weighted','focused','feature-bridge',
                  'root-geometry','far15-geometry','far13-geometry','far2-geometry','near-geometry','composition','consumer-tests']:
        jobs.append(('candidate-'+stage,['code/replay_candidate.py',stage]))
    jobs.extend([
      ('candidate-summary',['code/summarize_candidate_replay.py',str(BASE)]),
      ('fresh-manifest',['code/seal_inputs.py']),
      ('final-global-composition',['code/verify_recorded_proof.py','--output','results/GLOBAL_PROOF.json']),
    ])
    return jobs

def main():
    if not __debug__:raise SystemExit('Do not use -O or -OO.')
    ap=argparse.ArgumentParser(description=__doc__)
    recovery=ap.add_mutually_exclusive_group()
    recovery.add_argument('--resume-after-stage4',metavar='RUN_ID',help='Validate and reuse stages 1-4 from the stage-5 argument failure')
    recovery.add_argument('--check-resume',metavar='RUN_ID',help='Only validate saved recovery inputs; do not run any stages or change results')
    args=ap.parse_args()
    os.chdir(BASE);jobs=build_jobs();resume=None
    run_id=args.resume_after_stage4 or args.check_resume
    if run_id:
        print('Checking saved stage 1-4 results and unchanged proof inputs...',flush=True)
        resume=prepare_resume(run_id,jobs)
        print('PASS: saved baseline, 76 prior cases, and 173 returned cases are available for reuse.',flush=True)
        if args.check_resume:return
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    history=BASE/'run-history'/stamp;history.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',
             OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    # Retain the original evidence so an interrupted or failed run is recoverable.
    shutil.copytree(BASE/'results',history/'original-results')
    shutil.copy2(BASE/'inputs/PROOF_MANIFEST.json',history/'original-manifest.json')
    records=[];started=time.monotonic();start_index=0
    try:
        if resume:
            old,completed,metadata=resume
            (history/'RESUMED_FROM.json').write_text(json.dumps(metadata,indent=2)+'\n')
            shutil.move(str(BASE/'results'),str(history/'before-resume-results'))
            shutil.copytree(old/'partial-results',BASE/'results')
            for item in metadata['saved_result_files']:
                p=confined(BASE/'results',item['path'])
                need(p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],'Recovery copy changed: '+item['path'])
            records=[dict(row,reused_from=run_id) for row in completed];start_index=4
            (history/'progress.json').write_text(json.dumps(records,indent=2)+'\n')
            print(f'[1-4/{len(jobs)}] PASS - reusing verified results from {run_id}',flush=True)
        for i,(name,args) in enumerate(jobs[start_index:],start_index+1):
            print(f'[{i}/{len(jobs)}] {name} - running',flush=True)
            logfile=history/(name+'.log');begin=time.monotonic()
            with logfile.open('w') as stream:
                run=subprocess.run([sys.executable,'-B',*args],env=env,stdout=stream,stderr=subprocess.STDOUT)
            row=dict(stage=name,exit_code=run.returncode,seconds=time.monotonic()-begin,log=str(logfile.relative_to(BASE)))
            records.append(row)
            (history/'progress.json').write_text(json.dumps(records,indent=2)+'\n')
            if run.returncode:raise RuntimeError(f'{name} failed. Read {logfile}')
            print(f'[{i}/{len(jobs)}] {name} - PASS ({row["seconds"]:.1f}s)',flush=True)
        global_result=json.loads((BASE/'results/GLOBAL_PROOF.json').read_text())
        if global_result.get('status')!='PASS_COMPLETE_ELEVEN_SQUARE_OPTIMALITY' or global_result.get('global_optimality_proved') is not True:
            raise RuntimeError('Final global result did not accept the theorem')
        for file,status in [
          ('results/baseline-portable/FRESH_BASELINE_RESULT.json','PASS_PORTABLE_FRESH_1931_CASE_BASELINE'),
          ('results/prior-geometry/SUMMARY.json','PASS_ALL_76_FRESH_PRIOR_EXTENSION_GEOMETRY'),
          ('results/returned/SUMMARY.json','PASS_ALL_173_RETURNED_CASES')]:
            if json.loads((BASE/file).read_text()).get('status')!=status:raise RuntimeError('Missing full replay result: '+file)
        result=dict(status='PASS_FULL_REPLAY_AND_GLOBAL_COMPOSITION',stages=records,seconds=time.monotonic()-started,
                    global_result_sha256=hashlib.sha256((BASE/'results/GLOBAL_PROOF.json').read_bytes()).hexdigest(),
                    runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        if resume:result['resumed_from']=run_id
        (history/'COMPLETE.json').write_text(json.dumps(result,indent=2)+'\n')
        print('\nPASS: full geometric replay and global composition completed.',flush=True)
        print('Proof result: '+str(BASE/'results/GLOBAL_PROOF.json'))
        print('Full-run receipt: '+str(history/'COMPLETE.json'))
    except BaseException as error:
        # Preserve partial output for diagnosis, then restore original evidence.
        if (BASE/'results').exists():shutil.move(str(BASE/'results'),str(history/'partial-results'))
        shutil.copytree(history/'original-results',BASE/'results')
        shutil.copy2(history/'original-manifest.json',BASE/'inputs/PROOF_MANIFEST.json')
        print('\nSTOPPED: '+str(error),file=sys.stderr)
        print('Original evidence restored. Logs and partial outputs: '+str(history),file=sys.stderr)
        raise

if __name__=='__main__':main()
