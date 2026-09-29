#!/usr/bin/env python3
"""Two-worker fresh replay/independent-row audit and atomic frontier refresh."""
from pathlib import Path
from fractions import Fraction as F
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,json,subprocess,sys,os,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];WORK=ROOT/'work';ENTRY=HERE/'audit_entries.json'
def refresh(entries):
 tmp=ENTRY.with_suffix('.json.tmp');tmp.write_text(json.dumps(entries,indent=2)+'\n');tmp.replace(ENTRY)
 cmd=[sys.executable,str(HERE/'audit_union_registry_v3.py')]
 for e in entries:cmd+=['--entry',e['packet'],e['chain']]
 next_registry=HERE/'next-union-independent-audit.json'
 cmd+=['--output',str(next_registry)]
 with (HERE/'current-union-independent-audit.log').open('w') as f:subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
 next_registry.replace(HERE/'current-union-independent-audit.json')
 d=json.loads((HERE/'current-union-independent-audit.json').read_text())
 tmp=HERE/'remaining-mask-indices.json.tmp';tmp.write_text(json.dumps(d['remaining_canonical_mask_indices'])+'\n');tmp.replace(HERE/'remaining-mask-indices.json')
 print(json.dumps(dict(excluded=d['excluded_canonical_cases'],remaining=d['remaining_canonical_cases'])),flush=True)
def audit(entry):
 p=Path(entry['packet']);g=Path(entry.get('receipt',entry.get('gate')));packet=json.loads(p.read_text());gate=json.loads(g.read_text());idx=packet['mask_index']
 need=gate['status']=='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION'
 if not need:raise ValueError('incomplete producer '+str(g))
 interval=list(map(F,gate['records'][0]['interval']));bins=1/(interval[1]-interval[0]);assert bins.denominator==1
 digest=hashlib.sha256(p.read_bytes()).hexdigest();stem=f'mask{idx}-{digest[:12]}'
 replay=HERE/(stem+'-full-replay.json');chain=HERE/(stem+'-independent-chain-audit.json')
 cmds=[([sys.executable,str(WORK/'geometry/verify_wall_aware_mask.py'),str(p),'--output',str(replay),'--bins',str(bins.numerator),'--max-depth','14','--max-rows','30000','--seconds','300','--patch-nodes','5000'],replay.with_suffix('.log')),
 ([sys.executable,str(HERE/'audit_wall_mask_chain_v3.py'),str(p),str(g),str(replay),'--ownership-cache',str(WORK/'new_mask_audit/mask2045-minimized-independent-chain-audit.json'),'--output',str(chain)],chain.with_suffix('.log'))]
 env=dict(os.environ);env['PYTHONPATH']=str(WORK/'audit/deps')
 for cmd,log in cmds:
  with log.open('w') as f:subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 d=json.loads(chain.read_text());print(json.dumps(dict(mask=idx,status=d['status'],independent_positive_rows=d['independent_complete_positive_rows'],transferred=d['continuum_canonical_masks_excluded'])),flush=True)
 return dict(packet=str(p.resolve().relative_to(ROOT)),chain=str(chain.relative_to(ROOT)),producer_gate=str(g.resolve().relative_to(ROOT)),fresh_replay=str(replay.relative_to(ROOT)),bins=bins.numerator)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('results',nargs='*',type=Path);ap.add_argument('--refresh-only',action='store_true');args=ap.parse_args()
 entries=json.loads(ENTRY.read_text())
 if args.refresh_only:refresh(entries);return
 inputs=[]
 known={hashlib.sha256(Path(e['packet']).read_bytes()).hexdigest() for e in entries}
 for p in args.results:
  r=json.loads(p.read_text());records=r if isinstance(r,list) else [r]
  for e in records:
   if not e.get('final',True) or e.get('status','PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION')!='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION':continue
   h=hashlib.sha256(Path(e['packet']).read_bytes()).hexdigest()
   if h not in known:inputs.append(e);known.add(h)
 with ThreadPoolExecutor(max_workers=2) as pool:
  futures={pool.submit(audit,e):e for e in inputs}
  for f in as_completed(futures):
   new=f.result();idx=json.loads(Path(new['packet']).read_text())['mask_index']
   entries.append(new)
   refresh(entries)
if __name__=='__main__':main()
