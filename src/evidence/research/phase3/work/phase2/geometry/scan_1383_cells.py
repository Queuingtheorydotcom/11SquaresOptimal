from pathlib import Path
import subprocess,sys,os,json,time,concurrent.futures,shutil
H=Path(__file__).resolve().parent;AD=H.parents[1]/'geometry/verify_wall_aware_mask.py';PACKET=H/'mask1383_newpoints_packet.json';CHUNKS=H/'cellscan';CHUNKS.mkdir(exist_ok=True)
shutil.copy2(H/'mask1383_newpoints_gate.json',CHUNKS/'initial_cells0_1.json')
def one(cell):
 out=CHUNKS/f'cell{cell}.json';log=CHUNKS/f'cell{cell}.log'
 with log.open('w') as f:r=subprocess.run([sys.executable,str(AD),str(PACKET),'--output',str(out),'--cells',str(cell),'--seconds','600','--bins','32','--max-rows','20000'],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'OPENBLAS_NUM_THREADS':'1'})
 if r.returncode:return {'cell':cell,'error':r.returncode}
 d=json.loads(out.read_text());last=d['records'][-1];answer=dict(cell=cell,complete=all(c['complete'] for c in d['cells']),rows=d['rows'],seconds=d['seconds'],last_status=last['status']);print(answer,flush=True);return answer
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 results=list(pool.map(one,[1,4,6,8,9,10,11,13,3,15]))
(H/'cellscan_summary.json').write_text(json.dumps(results,indent=2))
