"""Resume finite proposals followed by exact whole-cell gates; never promote partials."""
from pathlib import Path
import subprocess,sys,os,time,json,hashlib,argparse
ROOT=Path('/workspace/scratch/6def36ddf53b/current')
OUT=ROOT/'research/optimality/deficit_geometry/physical_features'
GATE=ROOT/'research/optimality/asymmetric_coverage/verify.py'
ap=argparse.ArgumentParser();ap.add_argument('--mask',type=int,required=True);ap.add_argument('--seconds',type=int,default=600);ap.add_argument('--rounds',type=int,default=15);args=ap.parse_args()
start=time.monotonic();history=[]
extras=[OUT/f'owned{i}-exact.npz' for i in [2,3,4]]
env={**os.environ,'PYTHONPATH':'/workspace/scratch/6def36ddf53b/work/audit/deps','OPENBLAS_NUM_THREADS':'1'}
def run(params,path,timeout=200):
 with path.open('w') as f: subprocess.run([sys.executable,*map(str,params)],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=timeout)
for i in range(1,args.rounds+1):
 if time.monotonic()-start>args.seconds:break
 tag=f'sep27r{i}';stem=f'mask{args.mask}-{tag}';packet=OUT/(stem+'-packet.json')
 if not (OUT/(stem+'-result.json')).exists():
  run([OUT/'solve.py','--mask',args.mask,'--tag',tag,'--dataset',OUT/'owned-tight','--ownership','cell_fivepoints','--seconds',120,*[v for p in extras for v in ['--extra',p]]],OUT/(stem+'-solve.log'))
 finite=json.loads((OUT/(stem+'-result.json')).read_text())
 if finite.get('best_budget',12)>=11:
  history.append({'round':i,'status':'NO_FINITE_GAP'});break
 run([OUT/'freeze.py','--mask',args.mask,'--tag',tag],OUT/(stem+'-freeze.log'))
 p=json.loads(packet.read_text())
 if p['positive_physical_features']>100:
  history.append({'round':i,'status':'FEATURE_BUDGET'});break
 result=OUT/(stem+'-gate.json')
 run([GATE,packet,'--output',result,'--bins',64,'--max-depth',14,'--max-rows',12000,'--seconds',90],OUT/(stem+'-gate.log'))
 d=json.loads(result.read_text());last=d['records'][-1]
 entry={'round':i,'status':d['status'],'last':last['status'],'cell':last['cell'],'rows':d['rows'],'seconds':d['seconds'],'packet_sha256':hashlib.sha256(packet.read_bytes()).hexdigest(),'features':p['positive_physical_features'],'budget':p['certificate']['budget_units'],'thresholds':p['threshold_units']}
 history.append(entry);print(json.dumps(entry),flush=True)
 Path('/workspace/scratch/6def36ddf53b/work/continuation',f'mask{args.mask}-progress.json').write_text(json.dumps({'history':history,'elapsed':time.monotonic()-start},indent=2)+'\n')
 if last['status']!='REFUTED_BY_LEGAL_PARENT':break
 exact=OUT/(stem+'-refuter.npz');jitter=OUT/(stem+'-jitter.npz')
 run([OUT/'add_exact_refuter.py',result,'--output',exact],OUT/(stem+'-refuter.log'))
 run([OUT/'jitter_refuter.py',exact,'--output',jitter],OUT/(stem+'-jitter.log'))
 extras += [exact,jitter]
print('FINISHED',time.monotonic()-start,flush=True)
