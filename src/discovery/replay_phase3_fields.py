"""Fresh independent geometric audits of saved field certificate proof objects.

The archived producer and earlier producer replay are inputs; the independent
auditor reconstructs every positive-row coverage proof. This run does not rerun
the producer, which is redundant to the independent geometric check.
"""
from pathlib import Path
import json,subprocess,sys,time,hashlib
base=Path(__file__).resolve().parent;root=base/'phase3';out=base/'phase3-fresh-fields';out.mkdir(exist_ok=True)
recipes=json.loads((root/'PHASE3_REPLAY_MANIFEST.json').read_text())['field_recipes']
checkers={hashlib.sha256(p.read_bytes()).hexdigest():p for p in [root/'work/phase2/audit/audit_wall_mask_chain_v2.py',root/'work/phase3/audit/audit_wall_mask_chain_v3.py']}
records=[];begin=time.monotonic();cache={}
for i,e in enumerate(recipes):
    dest=out/f'{i:02d}-{Path(e["packet"]).stem}.json';log=dest.with_suffix('.log');checker=checkers[e['chain_checker_sha256']]
    command=[sys.executable,str(base/'phase3_portable_replay.py'),str(checker.relative_to(root)),e['packet'],e['producer_gate'],e['fresh_replay'],'--output',str(dest)]
    if checker in cache:command.extend(['--ownership-cache',str(cache[checker])])
    start=time.monotonic()
    with log.open('w') as f:r=subprocess.run(command,cwd=root,stdout=f,stderr=subprocess.STDOUT)
    record=dict(index=i,packet=e['packet'],output=str(dest),log=str(log),exit_code=r.returncode,seconds=time.monotonic()-start)
    if r.returncode==0:
        got=json.loads(dest.read_text());old=json.loads((root/e['independent_chain']).read_text())
        keys=['status','audit_checker_sha256','packet_sha256','cover_sha256','parent_Uplus','parent_side','exact_alpha_below_U','canonical_mask_index','mask','processed_rows','accepted_full_interval_leaves','budget_units','proved_positive_cells','threshold_sum_units','conditional_owner_support','independent_geometry_checker_sha256','independent_complete_positive_rows','continuum_canonical_masks_excluded','transferred_canonical_mask_indices','global_optimality_proved']
        diffs=[k for k in keys if got.get(k)!=old.get(k)]
        record.update(passed=not diffs,different_invariant_fields=diffs,positive_rows=got['independent_complete_positive_rows'],fresh_sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
        cache[checker]=dest
    else:record['passed']=False
    records.append(record);print(json.dumps(record),flush=True)
    (out/'progress.json').write_text(json.dumps(dict(completed=len(records),total=len(recipes),records=records),indent=2)+'\n')
    if not record['passed']:break
passed=sum(r['passed'] for r in records)
result=dict(status='PASS_FRESH_INDEPENDENT_FIELD_GEOMETRY' if passed==len(recipes) else 'INCOMPLETE_OR_FAILED',passed=passed,total=len(recipes),seconds=time.monotonic()-begin,
    scope='Fresh source-distinct geometric reconstruction of saved proof objects; producer was not rerun in this run.',records=records)
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)
if passed!=len(recipes):sys.exit(1)
