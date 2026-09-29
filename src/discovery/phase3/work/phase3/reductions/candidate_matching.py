from pathlib import Path
from functools import lru_cache
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];H=ROOT/'work/phase2/geometry';OUT=Path(__file__).parent
cover=json.loads((ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json').read_text());data=json.loads((H/'cover_d4_intersections.json').read_text());ids=[438,999,1462,1659];masks={i:cover['canonical_eleven_cell_subsets'][i] for i in ids};records=[]
def match(source,target,edges):
 T=set(target);domains=[sorted(set(edges[j])&T) for j in source];order=sorted(range(11),key=lambda j:len(domains[j]));
 @lru_cache(None)
 def dfs(k,used):
  if k==11:return True
  return any(not used&(1<<j) and dfs(k+1,used|(1<<j)) for j in domains[order[k]])
 return dfs(0,0)
for idx in [999,1462,1659]:
 for si,sym in enumerate(data['symmetries']):
  possible=[j for j in ids if any(match(masks[idx],T,sym['edges']) for T in [masks[j],[15-k for k in masks[j]]])];records.append(dict(source=idx,symmetry=si,possible_candidates=possible));print(idx,si,possible)
result=dict(status='CONDITIONAL_MATCHING_REDUCTION',assumption='Only438,999,1462,1659canoccur.',records=records,global_optimality_proved=False)
(OUT/'candidate-matching-result.json').write_text(json.dumps(result,indent=2)+'\n')
