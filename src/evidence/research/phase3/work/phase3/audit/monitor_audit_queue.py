#!/usr/bin/env python3
"""Monitor finalized producer fields, audit useful ones, refresh exact frontier.

Projected coverage is used only to prioritize audits, never to change the
registry. Every registry addition is made by the independent chain runner.
"""
from pathlib import Path
import argparse,json,hashlib,subprocess,sys,time,os
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
SOURCES=[ROOT/'work/phase3'/a/'patterns.json' for a in ('root','batch','mask_search','batch_subset')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def selection():
 r=json.loads((HERE/'current-union-independent-audit.json').read_text());covered=set(r['excluded_canonical_mask_indices']);known={x['packet_sha256'] for x in r['entries']}
 c=json.loads((ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json').read_text())['canonical_eleven_cell_subsets'];pending=[]
 for fp in sorted((ROOT/'work/phase3').glob('*/patterns.json')):
  if not fp.exists():continue
  for x in json.loads(fp.read_text()):
   if not x.get('final',x.get('minimization_complete',False)):continue
   if x.get('status')!='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION':continue
   ph=sha(x['packet'])
   if ph in known:continue
   known.add(ph);p=json.loads(Path(x['packet']).read_text())
   O=set(p.get('conditional_owner_support',p['mask']));g=p['threshold_units'];b=p['certificate']['budget_units'];P={i for i in p['mask'] if g[i]>0}
   def good(J):return O<=set(J) and sum(g[i] for i in P if i in J)>b
   cases={j for j,J in enumerate(c) if good(J) or good([15-i for i in J])};pending.append((x,cases))
 chosen=[];deferred=[]
 while pending:
  pending.sort(key=lambda v:len(v[1]-covered),reverse=True);x,s=pending.pop(0);n=len(s-covered)
  if n:chosen.append(x);covered|=s
  else:deferred.append(dict(mask=x.get('mask',x.get('mask_index')),packet=x['packet'],packet_sha256=sha(x['packet']),transferred_cases=sorted(s)))
 return chosen,deferred,r

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--seconds',type=int,default=7200);ap.add_argument('--once',action='store_true');a=ap.parse_args();begin=time.monotonic()
 (HERE/'monitor.pid').write_text(str(os.getpid())+'\n');iteration=0
 while time.monotonic()-begin<a.seconds and not (HERE/'STOP_MONITOR').exists():
  chosen,deferred,r=selection();iteration+=1
  if chosen:
   q=HERE/f'queue-monitor-{int(time.time())}-{iteration}.json';q.write_text(json.dumps(chosen,indent=2)+'\n')
   print(json.dumps(dict(iteration=iteration,queued=[x.get('mask',x.get('mask_index')) for x in chosen],excluded=r['excluded_canonical_cases'])),flush=True)
   cmd=[sys.executable,str(HERE/'run_audit_batch.py'),str(q)]
   subprocess.run(cmd,cwd=ROOT,check=True)
  else:
   report=dict(status='NO_NEW_NEEDED_FINAL_FIELDS',current_registry_sha256=sha(HERE/'current-union-independent-audit.json'),excluded=r['excluded_canonical_cases'],remaining=r['remaining_canonical_cases'],redundant_final_producer_fields=deferred,scope='Scheduling receipt only; redundant fields need no separate proof because their entire transfer sets already lie in the independently audited union.')
   (HERE/'queue-monitor-status.json').write_text(json.dumps(report,indent=2)+'\n')
  if a.once:break
  time.sleep(15)
if __name__=='__main__':main()
