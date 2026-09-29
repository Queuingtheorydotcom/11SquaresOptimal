"""Conditional D4 reduction: assumes all noncandidate cases are excluded."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,time
ROOT=Path(__file__).resolve().parents[3];H=ROOT/'work/phase2/geometry';OUT=Path(__file__).parent;COVER=ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads(COVER.read_text());o=json.loads((H/'cover_overlay_exact.json').read_text());d=json.loads((H/'overlay_distance_pairs.json').read_text());assert o['cover_sha256']==sha(COVER) and d['overlay_sha256']==sha(H/'cover_overlay_exact.json')
labels=[r['labels'] for r in o['regions']];domains=[[i for i,r in enumerate(labels) if r[0]==j] for j in range(16)];ban=[set() for _ in labels]
for p in d['pairs']:
 assert F(p['maximum_squared_center_distance'])<1;i,j=p['regions'];ban[i].add(j);ban[j].add(i)
bits=lambda J:sum(1<<j for j in J)
allowed0=[c['canonical_eleven_cell_subsets'][i] for i in [999,1462,1659]];allowed=[bits(J) for J in allowed0]+[bits([15-j for j in J]) for J in allowed0]
records=[]
for idx in [999,1462,1659]:
 mask=c['canonical_eleven_cell_subsets'][idx];nodes=0;proof=[];memo=set();start=time.monotonic()
 def dfs(remain,used,chosen):
  global nodes
  nodes+=1
  if nodes>2000000:raise TimeoutError('node budget exhausted')
  if not remain:return list(chosen)
  valid=[]
  for owner in remain:
   candidates=[]
   for r in domains[owner]:
    if any(r in ban[s] for s in chosen):continue
    lab=labels[r]
    if any(used[g]&(1<<lab[g]) or not any(((used[g]|(1<<lab[g]))&a)==(used[g]|(1<<lab[g])) for a in allowed) for g in range(4)):continue
    candidates.append(r)
   if not candidates:return None
   valid.append((len(candidates),owner,candidates))
  _,owner,candidates=min(valid)
  for r in candidates:
   result=dfs([j for j in remain if j!=owner],[used[g]|(1<<labels[r][g]) for g in range(4)],chosen+[r])
   if result is not None:return result
  return None
 try:result=dfs(mask,[0]*4,[]);status='ABSTRACT_ASSIGNMENT_SURVIVES' if result else 'CONDITIONAL_ORBIT_CAPTURE_PROVED'
 except TimeoutError:result=None;status='UNKNOWN_NODE_LIMIT'
 record=dict(mask_index=idx,status=status,nodes=nodes,seconds=time.monotonic()-start,region_assignment=result);records.append(record);print(json.dumps(record),flush=True)
result=dict(status='CONDITIONAL_REDUCTION_EXPERIMENT',assumption='Every feasible packing has a canonical occupied mask among438,999,1462,1659.',target_mask=438,records=records,cover_sha256=sha(COVER),overlay_sha256=sha(H/'cover_overlay_exact.json'),distance_receipt_sha256=sha(H/'overlay_distance_pairs.json'),checker_sha256=sha(Path(__file__)),global_optimality_proved=False)
(OUT/'candidate-orbit-result.json').write_text(json.dumps(result,indent=2)+'\n')
