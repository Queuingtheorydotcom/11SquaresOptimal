"""Portable fresh exact verification; deliberately does not assert full optimality."""
from pathlib import Path
from fractions import Fraction as F
import argparse,json,os,subprocess,sys,time
if not __debug__:raise SystemExit('Assertions must be enabled.')
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args()
out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
manifest=json.loads((ROOT/'proof_registry.json').read_text());env=dict(os.environ,ELEVEN_PACKING_ROOT=str(ROOT/'current'),OPENBLAS_NUM_THREADS='1');start=time.monotonic();entries=[];cache=None
adapter=ROOT/'work/geometry/verify_wall_aware_mask.py';auditor=ROOT/'work/phase2/audit/audit_wall_mask_chain_v2.py'
def run(args,log):
 with log.open('w') as f:subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
for e in manifest['entries']:
 p=ROOT/e['packet'];reference=ROOT/e['reference_gate'];old=json.loads(reference.read_text());lo,hi=map(F,old['records'][0]['interval']);bins=1/(hi-lo)
 if bins.denominator!=1:raise ValueError('Unsupported starting partition')
 stem=f"mask{e['mask_index']}";fresh=out/(stem+'-fresh.json');chain=out/(stem+'-independent.json')
 run([adapter,p,'--output',fresh,'--bins',bins.numerator,'--max-depth',18,'--max-rows',50000,'--seconds',1800],fresh.with_suffix('.log'))
 args=[auditor,p,reference,fresh,'--output',chain]
 if cache:args+=['--ownership-cache',cache]
 run(args,chain.with_suffix('.log'));r=json.loads(chain.read_text())
 if r['status']!='PASS_INDEPENDENT_COMPLETE_WALL_MASK_CHAIN_AUDIT':raise ValueError('Incomplete chain')
 cache=chain;entries.append((p,chain));print('PASS',stem,flush=True)
args=[ROOT/'work/phase2/audit/audit_union_registry_v2.py']
for p,c in entries:args+=['--entry',p,c]
args+=['--output',out/'union.json'];run(args,out/'union.log');d=json.loads((out/'union.json').read_text())
if d['excluded_canonical_mask_indices']!=manifest['excluded_canonical_mask_indices']:raise ValueError('Different exclusion union')
result=dict(status='PASS_FRESH_EXACT_EXCLUSION_REGISTRY',excluded=d['excluded_canonical_cases'],remaining=d['remaining_canonical_cases'],global_optimality_proved=False,seconds=time.monotonic()-start)
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
