#!/usr/bin/env python3
"""Verify a nonexcluded target matching for every remaining source/D4 pair.

A matching is only a witness that this combinatorial relaxation survives;
it is not a geometric packing. No producer DFS or executable is imported.
"""
from pathlib import Path
from itertools import combinations
import hashlib,json
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[1];ROOT=HERE.parents[2]/'current'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def need(v,s):
 if not v:raise ValueError(s)
def main():
 coverpath=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json';cover=read(coverpath)
 graphpath=WORK/'phase2/geometry/cover_d4_intersections.json';graph=read(graphpath)
 auditpath=HERE/'rotated-cover-independent-audit.json';audit=read(auditpath)
 registry_path=WORK/'new_mask_audit/two-pattern-union-independent-audit.json';registry=read(registry_path)
 source=WORK/'phase2/geometry/matching_transfer_receipt.txt'
 need(audit['status']=='PASS_INDEPENDENT_EXACT_D4_CLOSED_INTERSECTION_AUDIT' and audit['producer_sha256']==sha(graphpath) and audit['checker_sha256']==sha(HERE/'audit_rotated_cover.py'),'unbound graph audit')
 need(audit['cover_sha256']==registry['cover_sha256']==sha(coverpath),'cover mismatch')
 need(registry['status']=='PASS_INDEPENDENT_TWO_PATTERN_UNION_AUDIT' and registry['checker_sha256']==sha(WORK/'new_mask_audit/audit_union_registry.py'),'unbound original exclusion union')
 turn=lambda J:tuple(sorted(15-i for i in J))
 canonical=sorted({min(J,turn(J)) for J in combinations(range(16),11)})
 need([list(J) for J in canonical]==cover['canonical_eleven_cell_subsets'],'canonical enumeration mismatch')
 index={J:i for i,J in enumerate(canonical)};excluded=set(registry['excluded_canonical_mask_indices'])
 patterns=[set(O) for O in registry['patterns']]
 independently_excluded={i for i,J in enumerate(canonical) if any(O<=set(J) or O<=set(turn(J)) for O in patterns)}
 need(excluded==independently_excluded and len(excluded)==240,'original forbidden patterns differ')
 remaining=set(range(2184))-excluded
 rows={};initial=rounds=final=0
 for number,line in enumerate(source.read_text().splitlines(),1):
  tokens=line.split();need(bool(tokens),'empty receipt line')
  if tokens[0]=='initial':
   need(tokens==['initial','240'],'wrong initial case count');initial+=1
  elif tokens[0]=='survivor':
   need(len(tokens)==16,'malformed survivor line '+str(number))
   roundno,idx,sym,target=map(int,tokens[1:5]);need(roundno==1 and idx in remaining and 0<=sym<8 and 0<=target<2**16,'bad witness scope')
   key=(idx,sym);need(key not in rows,'duplicate source/symmetry witness')
   pairs=[tuple(map(int,t.split(':'))) for t in tokens[5:]]
   need(all(len(p)==2 for p in pairs),'bad matching edge')
   ss=[s for s,t in pairs];tt=[t for s,t in pairs]
   need(len(set(ss))==len(set(tt))==11 and set(ss)==set(canonical[idx]),'not a bijection from all source cells')
   need(all(0<=t<16 and t in graph['symmetries'][sym]['edges'][s] for s,t in pairs),'matching uses an absent exact graph edge')
   need(sum(1<<t for t in tt)==target,'target mask bit encoding differs')
   J=tuple(sorted(tt));j=index[min(J,turn(J))]
   need(j not in excluded,'survivor target already excluded')
   need(not any(O<=set(J) or O<=set(turn(J)) for O in patterns),'survivor contains a forbidden pattern')
   rows[key]=j
  elif tokens[0]=='round':
   need(len(tokens)==6 and tokens[:5]==['round','1','added','0','states'] and int(tokens[5])>0,'wrong terminal round');rounds+=1
  elif tokens[0]=='new_excluded':
   need(tokens==['new_excluded','0'],'producer claims new exclusions');final+=1
  else:raise ValueError('unrecognized receipt row '+str(number))
 need(initial==rounds==final==1,'missing/duplicate header or termination')
 need(set(rows)=={(i,s) for i in remaining for s in range(8)},'some source/D4 pair lacks a survivor witness')
 out=dict(status='PASS_INDEPENDENT_MATCHING_RELAXATION_SURVIVOR_AUDIT',checker_sha256=sha(Path(__file__)),
  cover_sha256=sha(coverpath),graph_sha256=sha(graphpath),graph_independent_audit_sha256=sha(auditpath),
  exclusion_registry_sha256=sha(registry_path),matching_witness_source_sha256=sha(source),
  original_excluded_canonical_masks=len(excluded),remaining_source_masks=len(remaining),symmetries=8,
  injective_matching_witnesses=len(rows),distinct_nonexcluded_target_masks=len(set(rows.values())),
  new_exclusions_possible_by_this_one_map_matching_rule=0,global_optimality_proved=False,
  scope='For all 1944 remaining canonical source cases and all eight D4 maps, an exact-graph matching to a nonexcluded target case survives. Therefore closed-cell bipartite matching against the present 240 exclusions yields no additional case. These matchings are not geometric packings.')
 (HERE/'matching-survivors-independent-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
