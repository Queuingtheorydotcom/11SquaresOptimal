"""Bounded sequential retry queue for completed, unresolved plain cases."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

if not __debug__:
    raise SystemExit('Assertions must remain enabled.')
HERE = Path(__file__).resolve().parent
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1')
STATUS = HERE/'refined-batch-status.json'
PROTECTED = {438, 999, 1462, 1659, 1383, 1839, 455, 655}

def read(path):
    return json.loads(path.read_text())

def save(records):
    temp = STATUS.with_suffix('.writing')
    temp.write_text(json.dumps(records, indent=2)+'\n')
    temp.replace(STATUS)

def eligible(done):
    answer = []
    for filename in ('batch-status.json', 'all-batch-status.json'):
        try:
            statuses = read(HERE/filename)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        for item in statuses:
            m = item['mask_index']
            if m in PROTECTED or m in done:
                continue
            if item.get('terminal') and not item.get('contradiction'):
                if (HERE/f'mask{m}-overlay-exclusion.json').exists():
                    continue
                answer.append(m)
    return sorted(set(answer))

def task(mask, records):
    record = dict(mask_index=mask, phase='refining', stages=[],
                  independent_audit_passed=False)
    records.append(record)
    save(records)
    source = HERE/f'mask{mask}-self-v1.json'
    assert read(source)['terminal'] and not read(source)['constraints']
    for stage in range(1,4):
        output = HERE/f'mask{mask}-refined-v{stage}.json'
        if output.exists():
            raise FileExistsError(output)
        with output.with_suffix('.producer.log').open('w') as log:
            result = subprocess.run([sys.executable, str(HERE/'refine_case.py'),
                str(source), '--output', str(output), '--seconds', '180'],
                env=ENV, stdout=log, stderr=subprocess.STDOUT)
        item = dict(stage=stage, source=str(output), returncode=result.returncode)
        record['stages'].append(item)
        if result.returncode or not output.exists():
            record['phase']='producer_failed'; save(records); return
        data = read(output)
        item['contradiction'] = data.get('contradiction')
        save(records)
        if data.get('contradiction'):
            assert data['terminal'] and not data['constraints']
            record['phase']='independent_replay'; save(records)
            audit = HERE/f'mask{mask}-independent.json'
            assert not audit.exists()
            with audit.with_suffix('.log').open('w') as log:
                result = subprocess.run([sys.executable,str(HERE/'audit_case.py'),
                    str(output),'--output',str(audit)], env=ENV,
                    stdout=log,stderr=subprocess.STDOUT)
            record.update(audit=str(audit),audit_returncode=result.returncode)
            if result.returncode==0:
                a=read(audit)
                record['independent_audit_passed']=(
                    a['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT'
                    and a['mask_exclusion_proved'] and not a['constraints'])
            record['phase']=('independently_excluded' if record['independent_audit_passed']
                             else 'independent_replay_failed')
            save(records); return
        source = output
    record['phase']='unresolved_after_three_refinements'; save(records)

def main():
    if STATUS.exists():
        raise FileExistsError(STATUS)
    records=[]; save(records)
    for _ in range(8):
        choices=eligible({r['mask_index'] for r in records})
        if not choices:
            time.sleep(30)
            choices=eligible({r['mask_index'] for r in records})
        if not choices:
            break
        task(choices[0],records)
        print(json.dumps(records[-1]),flush=True)

if __name__=='__main__':
    main()
