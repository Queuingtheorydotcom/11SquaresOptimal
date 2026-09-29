#!/usr/bin/env python3
"""Independently enumerate the union of exact conditional-pattern exclusions."""
from pathlib import Path
from itertools import combinations
from fractions import Fraction as F
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]/'current'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def need(v,s):
 if not v:raise ValueError(s)
def main():
 coverpath=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json';cover=read(coverpath)
 turn=lambda J:tuple(sorted(15-i for i in J))
 allmasks=list(combinations(range(16),11));canonical=sorted({min(J,turn(J)) for J in allmasks})
 need([list(J) for J in canonical]==cover['canonical_eleven_cell_subsets'] and len(canonical)==2184,'canonical cases mismatch')
 receipts=[];sets=[];patterns=[]
 for stem in ('mask2045','mask2147'):
  path=HERE/(stem+'-minimized-independent-chain-audit.json');r=read(path)
  need(r['status']=='PASS_INDEPENDENT_COMPLETE_WALL_MASK_CHAIN_AUDIT' and r['audit_checker_sha256']==sha(HERE/'audit_wall_mask_chain.py'),'chain audit absent or stale')
  need(r['cover_sha256']==sha(coverpath) and r['exact_alpha_below_U'],'unbound cover or target domain')
  O=set(r['conditional_owner_support']);P=set(r['proved_positive_cells'])
  need(P<=O and len(O)==7 and r['budget_units']==2 and r['threshold_sum_units']==3,'unexpected minimal pattern')
  # The receipt certifies unit thresholds on precisely these three cells.
  need(len(P)==3,'positive-cell count changed')
  allowed={i for i,J in enumerate(canonical) if O<=set(J) or O<=set(turn(J))}
  need(allowed==set(r['transferred_canonical_mask_indices']),'independent containment count mismatch')
  physical=[J for J in allmasks if O<=set(J)]
  need(len(physical)==126 and len(allowed)==126,'seven-cell extension count mismatch')
  need(len(O|set(turn(O)))>11,'same pattern occurs twice in a half-turn orbit')
  sets.append(allowed);patterns.append(sorted(O));receipts.append(dict(path=str(path),sha256=sha(path),canonical_cases=len(allowed),physical_extensions=len(physical)))
 union=sets[0]|sets[1];intersection=sets[0]&sets[1]
 need(len(union)==240 and len(intersection)==12,'union count differs')
 assignmentpath=ROOT/'research/optimality/global_capture/trump-cell-symmetric-assignments.json';assignment=read(assignmentpath)
 candidate_indices=[canonical.index(tuple(J)) for J in assignment['canonical_capture_masks']]
 need(len(candidate_indices)==4 and not (set(candidate_indices)&union),'known candidate orbit incorrectly excluded')
 need(2140 in union and 2045 in union and 2147 in union,'expected old or new base case missing')
 out=dict(status='PASS_INDEPENDENT_TWO_PATTERN_UNION_AUDIT',checker_sha256=sha(Path(__file__)),
  cover_sha256=sha(coverpath),source_chain_receipts=receipts,patterns=patterns,
  canonical_cases=2184,each_pattern_cases=[len(x) for x in sets],intersection_cases=len(intersection),
  excluded_canonical_cases=len(union),remaining_canonical_cases=2184-len(union),
  excluded_canonical_mask_indices=sorted(union),candidate_assignment_source_sha256=sha(assignmentpath),
  known_candidate_canonical_mask_indices=candidate_indices,known_candidate_masks_survive=True,
  original_mask2140_already_in_union=True,new_cases_beyond_original_mask2140=len(union)-1,
  scope='The two independently checked conditional patterns exclude 240 canonical continuum cases at S <= U, including S <= alpha. 1944 cases remain; no global optimum follows.',
  global_optimality_proved=False)
 (HERE/'two-pattern-union-independent-audit.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({k:v for k,v in out.items() if k!='excluded_canonical_mask_indices'},indent=2))
if __name__=='__main__':main()
