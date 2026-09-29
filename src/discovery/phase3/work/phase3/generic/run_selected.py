"""Bounded independent research attempts on cases not yet in the audited union."""
from pathlib import Path
import json,os,subprocess,sys,time
HERE=Path(__file__).parent;ROOT=HERE.parents[2]
cover=json.loads((ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json').read_text())
records=[];start=time.monotonic()
for mask in [1745,2158,1698,1866,1876]:
    audited=json.loads((ROOT/'work/phase3/audit/current-union-independent-audit.json').read_text())
    if mask not in audited['remaining_canonical_mask_indices']:
        print(json.dumps(dict(mask=mask,status='ALREADY_AUDITED_EXCLUDED')),flush=True);continue
    cells=cover['canonical_eleven_cell_subsets'][mask]
    priority=[i for i in [5,6,9,10,1,2] if i in cells][:2]
    with (HERE/f'mask{mask}-selected.log').open('w') as log:
        p=subprocess.run([sys.executable,str(HERE/'generic_pose_engine_v2.py'),'--mask',str(mask),'--seconds','150','--passes','8','--priority',','.join(map(str,priority))],stdout=log,stderr=subprocess.STDOUT)
    path=HERE/f'mask{mask}-generic-v2.json'
    d=json.loads(path.read_text()) if path.exists() else {}
    rec=dict(mask=mask,returncode=p.returncode,contradiction=d.get('contradiction'),source=str(path),
             seconds=d.get('seconds'),independently_audited=False)
    records.append(rec);print(json.dumps(rec),flush=True)
    (HERE/'selected-results.json').write_text(json.dumps(dict(records=records,elapsed=time.monotonic()-start),indent=2)+'\n')
