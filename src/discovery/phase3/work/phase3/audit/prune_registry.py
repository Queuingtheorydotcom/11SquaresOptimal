#!/usr/bin/env python3
"""Remove only already audited field entries redundant in the exact union."""
from pathlib import Path
import argparse,json,os
from run_audit_batch import refresh
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def read(p):return json.loads(Path(p).read_text())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');a=ap.parse_args()
 entries=read(HERE/'audit_entries.json');original=read(HERE/'current-union-independent-audit.json')
 data=[]
 for e in entries:
  c=read(ROOT/e['chain']);data.append((e,set(c['transferred_canonical_mask_indices']),c['independent_complete_positive_rows']))
 target=set(original['excluded_canonical_mask_indices']);assert set().union(*(x[1] for x in data))==target
 removed=[]
 for x in sorted(data,key=lambda x:x[2],reverse=True):
  other=[y for y in data if y is not x]
  if other and set().union(*(y[1] for y in other))==target:
   data=other;removed.append(x[0])
 report=dict(status='REDUNDANT_AUDITED_ENTRIES_IDENTIFIED',excluded=len(target),retained=len(data),removed=len(removed),removed_entries=removed,applied=False)
 if a.apply:
  assert (HERE/'STOP_MONITOR').exists(),'Stop the monitor before applying'
  pidfile=HERE/'monitor.pid'
  if pidfile.exists():
   try:os.kill(int(pidfile.read_text()),0)
   except ProcessLookupError:pass
   else:raise RuntimeError('Monitor process is still running')
  refresh([x[0] for x in data]);current=read(HERE/'current-union-independent-audit.json')
  assert current['excluded_canonical_mask_indices']==original['excluded_canonical_mask_indices']
  report.update(status='PASS_REDUNDANT_AUDITED_REGISTRY_PRUNING',applied=True)
 (HERE/'registry-pruning-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
