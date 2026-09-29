from pathlib import Path
import sys,json,time
root=Path('/workspace/scratch/6def36ddf53b/current/11-squares-true-19377-5000')
sys.path.insert(0,str(root))
import verify
start=time.monotonic()
verify.check_inventory(root)
verify.initialize(root/'catalogue')
info=verify.ENV[0]
n=len(verify.ENV[-1]);selected=sorted(set([0,1,2,n-3,n-2,n-1]+[(n-1)*k//10 for k in range(11)]))
rows=[]
for index in selected:
 t=time.monotonic();i,v,stage=verify.job(index)
 row=dict(index=i,minimum_units=v,stage=stage,seconds=time.monotonic()-t);rows.append(row);print(json.dumps(row),flush=True)
result=dict(status='PASS_SELECTED_FRESH_EXACT_ROWS_NOT_FULL_REPLAY',candidate_sha256=verify.filehash(root/'catalogue/candidate.json'),selected_rows=rows,leaves=n,global_bound_newly_verified=False,seconds=time.monotonic()-start)
Path('/workspace/scratch/6def36ddf53b/work/audit/selected-fresh-38754.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='selected_rows'}),flush=True)
