"""Bounded research batch: producers never count as audited exclusions."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import subprocess
import sys
import argparse

HERE = Path(__file__).resolve().parent
CASES = [2174,2175,2176,2178,2182,2183,221,247,248,250,251,647,649,650,651,652]
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1')

def task(mask):
    out = HERE / f'mask{mask}-self-v1.json'
    record = dict(mask_index=mask, producer=str(out), independent_audit_passed=False)
    if not out.exists():
        with (HERE/f'mask{mask}-producer.log').open('w') as log:
            result = subprocess.run([sys.executable,str(HERE/'run_case.py'),str(mask)],
                env=ENV, stdout=log, stderr=subprocess.STDOUT)
        record['producer_returncode'] = result.returncode
    if out.exists():
        data = json.loads(out.read_text())
        record.update(contradiction=data.get('contradiction'), terminal=data.get('terminal'))
        if data.get('terminal') and data.get('contradiction') and data['constraints']==[]:
            audit = HERE / f'mask{mask}-independent.json'
            with (HERE/f'mask{mask}-independent.log').open('w') as log:
                result = subprocess.run([sys.executable,str(HERE/'audit_case.py'),str(out),'--output',str(audit)],
                    env=ENV, stdout=log, stderr=subprocess.STDOUT)
            record.update(audit=str(audit),audit_returncode=result.returncode)
            if result.returncode==0:
                d=json.loads(audit.read_text())
                record['independent_audit_passed']=(d['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
                    and d['mask_exclusion_proved'] and not d['constraints'])
    (HERE/f'mask{mask}-status.json').write_text(json.dumps(record,indent=2)+'\n')
    return record

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--all',action='store_true')
    args=parser.parse_args()
    cases=CASES
    label='batch-status.json'
    if args.all:
        snapshot=HERE.parent/'phase3/work/phase3/audit/overall-union-snapshot-bc3563a0c995.json'
        data=json.loads(snapshot.read_text())
        cases=[m for m in data['remaining_canonical_mask_indices']
               if m not in CASES+[438,999,1462,1659,1383,1839]]
        label='all-batch-status.json'
    records=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(task,m) for m in cases]):
            result=future.result();records.append(result)
            print(json.dumps(result),flush=True)
            (HERE/label).write_text(json.dumps(records,indent=2)+'\n')
