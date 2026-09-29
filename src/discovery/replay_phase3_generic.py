"""Freshly replay every generic geometry certificate in the saved snapshot."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,json,subprocess,sys,time,hashlib

base=Path(__file__).resolve().parent
root=base/'phase3'
out=base/'phase3-fresh-generic'
out.mkdir(exist_ok=True)
recipes=json.loads((root/'PHASE3_REPLAY_MANIFEST.json').read_text())['generic_recipes']
ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);a=ap.parse_args()
begin=time.monotonic()
def replay(item):
    i,e=item; dest=out/f'{i:02d}-{Path(e["source"]).stem}.json'; log=dest.with_suffix('.log')
    command=[sys.executable,str(base/'phase3_portable_replay.py'),*e['replay_command'][1:]]
    command[command.index('FRESH-OUTPUT.json')]=str(dest)
    start=time.monotonic()
    with log.open('w') as f:
        result=subprocess.run(command,cwd=root,stdout=f,stderr=subprocess.STDOUT)
    record=dict(index=i,source=e['source'],output=str(dest),log=str(log),exit_code=result.returncode,seconds=time.monotonic()-start)
    if result.returncode==0:
        got=json.loads(dest.read_text());old=json.loads((root/e['independent_audit']).read_text())
        keys=['status','source_sha256','mask_index','mask','parent_Uplus','parent_side','cover_sha256','constraints','final_state_sha256','root_sha256','root_audit_sha256','dependencies','branch_exclusion_proved','inside_local_guard','mask_exclusion_proved','global_optimality_proved']
        differences=[k for k in keys if got.get(k)!=old.get(k)]
        record.update(passed=not differences,different_invariant_fields=differences,
            fresh_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
            rows=sum(n['rows'] for n in got['nodes']),
            slabs=sum(n['arrangement_slabs'] for n in got['nodes']))
    else: record['passed']=False
    print(json.dumps(record),flush=True)
    return record
records=[]
with ThreadPoolExecutor(max_workers=a.workers) as pool:
    futures=[pool.submit(replay,p) for p in enumerate(recipes)]
    for f in as_completed(futures):
        records.append(f.result())
        (out/'progress.json').write_text(json.dumps(dict(completed=len(records),total=len(recipes),records=sorted(records,key=lambda r:r['index'])),indent=2)+'\n')
result=dict(status='PASS_FRESH_GENERIC_GEOMETRY' if all(r['passed'] for r in records) else 'INCOMPLETE_OR_FAILED',
    certificates=len(recipes),passed=sum(r['passed'] for r in records),seconds=time.monotonic()-begin,
    scope='Fresh independent geometry for all 34 generic certificates. Field certificates require their separate replays.',
    records=sorted(records,key=lambda r:r['index']))
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)
if result['passed']!=len(recipes):sys.exit(1)
