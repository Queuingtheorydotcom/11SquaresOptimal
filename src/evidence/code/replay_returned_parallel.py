"""Parallel transport around the unchanged, strict returned-case verifier.

Each child proves one distinct case. It suppresses only its partial aggregate
SUMMARY write, preventing concurrent writers of that one file. The parent
then invokes the unchanged verifier's full --resume path, which independently
validates all 173 checkpoints and writes the sole authoritative summary.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time

BASE=Path(__file__).resolve().parents[1]
SOURCE=BASE/'code/verify_returned.py'

def load():
    spec=importlib.util.spec_from_file_location('strict_returned_verifier',SOURCE)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def main():
    if not __debug__:raise SystemExit('Assertions must be enabled')
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',type=int)
    parser.add_argument('--workers',type=int,default=6)
    parser.add_argument('--payload-budget-mb',type=int,default=360)
    args=parser.parse_args()
    if args.worker is not None:
        module=load();write=module.write
        def isolated_write(path,value):
            if path.resolve()==(module.RESULTS/'SUMMARY.json').resolve():return
            write(path,value)
        module.write=isolated_write
        sys.argv=[str(SOURCE),'--mask',str(args.worker)]
        module.main()
        return
    if args.workers<1 or args.payload_budget_mb<1:parser.error('Positive resource limits required')
    module=load();dependencies=module.load_checker()[1]
    plan=BASE/'inputs/returned-replay-plan.json'
    module.need(module.sha(plan)==module.PLAN_HASH,'Plan changed')
    cases=json.loads(plan.read_text())['cases']
    canonical=module.read(module.PH/'current/research/optimality/global_capture/center-cover-symmetric-exact.json')['canonical_eleven_cell_subsets']
    pending=[];reused=[]
    for case in cases:
        if (module.RESULTS/f"mask{case['mask_index']}-verified.json").exists():
            module.validate_checkpoint(case,dependencies,canonical);reused.append(case['mask_index'])
        else:pending.append(case)
    pending.sort(key=lambda c:(-c.get('recorded_audit_seconds',0),c['mask_index']))
    output=BASE/'results/returned';output.mkdir(parents=True,exist_ok=True)
    budget=args.payload_budget_mb*1_000_000;running={};completed=[];started=time.monotonic()
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
             NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    print(json.dumps({'status':'PARALLEL_REPLAY_START','reused':reused,'remaining':len(pending),
                      'max_workers':args.workers,'payload_budget_bytes':budget}),flush=True)
    try:
        while pending or running:
            used=sum(item['bytes'] for item in running.values())
            while pending and len(running)<args.workers:
                chosen=next((c for c in pending if c['peak_case_payload_bytes']+used<=budget),None)
                if chosen is None:
                    if running:break
                    chosen=pending[0]  # A sole larger case must remain runnable.
                pending.remove(chosen);mask=chosen['mask_index']
                stream=(output/f'mask{mask}-worker.log').open('w')
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',str(mask)],
                                       stdout=stream,stderr=subprocess.STDOUT,env=env)
                running[mask]=dict(child=child,stream=stream,bytes=chosen['peak_case_payload_bytes'],case=chosen)
                used+=chosen['peak_case_payload_bytes']
                print(json.dumps({'status':'START','mask_index':mask,'active':len(running)}),flush=True)
            for mask,item in list(running.items()):
                status=item['child'].poll()
                if status is None:continue
                item['stream'].close();del running[mask]
                if status:raise RuntimeError(f'Case {mask} failed with exit {status}; inspect its worker log')
                module.validate_checkpoint(item['case'],dependencies,canonical)
                completed.append(mask)
                print(json.dumps({'status':'PASS','mask_index':mask,'completed':len(completed)+len(reused),
                                  'required':173,'seconds':time.monotonic()-started}),flush=True)
            if running:time.sleep(.2)
    finally:
        for item in running.values():item['child'].terminate()
        for item in running.values():
            try:item['child'].wait(timeout=5)
            except subprocess.TimeoutExpired:item['child'].kill();item['child'].wait()
            item['stream'].close()
    sys.argv=[str(SOURCE),'--resume'];module.main()
    summary=module.read(output/'SUMMARY.json')
    module.need(summary['status']=='PASS_ALL_173_RETURNED_CASES' and summary['completed']==173,
                'Parallel jobs did not establish the complete required set')
    record=dict(status='PASS_PARALLEL_TRANSPORT_AND_COMPLETE_STRICT_CHECKPOINT_VALIDATION',
                launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                verifier_sha256=module.source_identity(),summary_sha256=module.sha(output/'SUMMARY.json'),
                case_verification_rules_changed=False,suppressed_output='Per-child partial SUMMARY.json only',
                reused_cases=reused,fresh_cases=sorted(completed),max_workers=args.workers,
                payload_budget_bytes=budget,seconds=time.monotonic()-started,global_optimality_proved=False)
    (output/'PARALLEL_TRANSPORT.json').write_text(json.dumps(record,indent=2)+'\n')

if __name__=='__main__':main()
