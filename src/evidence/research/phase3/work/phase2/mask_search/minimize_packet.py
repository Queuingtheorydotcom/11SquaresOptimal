from pathlib import Path
import json,subprocess,sys,os,time,hashlib,argparse
HERE=Path(__file__).parent;TOP=HERE.parents[1];ROOT=TOP.parent/'current';ADAPTER=TOP/'geometry/verify_wall_aware_mask.py';a=argparse.ArgumentParser();a.add_argument('packet',type=Path);a.add_argument('--prefix',required=True);a.add_argument('--order',required=True);args=a.parse_args()
packet=json.loads(args.packet.read_text());owners=list(packet['mask']);positive={i for i,x in enumerate(packet['threshold_units']) if x};history=[];start=time.monotonic();env={**os.environ,'PYTHONPATH':str(TOP/'audit/deps'),'OPENBLAS_NUM_THREADS':'1'}
for drop in map(int,args.order.split(',')):
 assert drop in owners and drop not in positive
 trial=dict(packet);trial['conditional_owner_support']=[j for j in owners if j!=drop];p=HERE/f'{args.prefix}-omit{drop}-packet.json';o=HERE/f'{args.prefix}-omit{drop}-gate.json';p.write_text(json.dumps(trial,indent=2)+'\n')
 with (HERE/f'{args.prefix}-omit{drop}.log').open('w') as f:subprocess.run([sys.executable,str(ADAPTER),str(p),'--output',str(o),'--seconds','90','--max-depth','16','--max-rows','16000'],stdout=f,stderr=subprocess.STDOUT,env=env,check=True,timeout=150)
 d=json.loads(o.read_text());passed=d['status']=='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION';history.append({'dropped_owner':drop,'pass':passed,'status':d['status'],'last':d['records'][-1]['status'],'cell':d['records'][-1]['cell'],'rows':d['rows'],'packet':str(p),'receipt':str(o)})
 if passed:owners.remove(drop);packet=trial
 print(json.dumps(history[-1]),flush=True);required=sorted(positive|set(owners));(HERE/f'{args.prefix}-minimized-owners-progress.json').write_text(json.dumps({'required_cells':required,'conditional_owner_support':owners,'positive_cells':sorted(positive),'history':history,'elapsed':time.monotonic()-start},indent=2)+'\n')
(HERE/f'{args.prefix}-minimized-packet.json').write_text(json.dumps(packet,indent=2)+'\n');print('DONE',owners,flush=True)
