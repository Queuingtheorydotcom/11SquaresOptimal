#!/usr/bin/env python3
"""Independent canonical closure/union for any number of certified fields."""
from pathlib import Path
from itertools import combinations
from fractions import Fraction as F
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[1];ROOT=HERE.parents[2]/'current'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def need(v,s):
 if not v:raise ValueError(s)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--entry',nargs=2,type=Path,action='append',required=True,metavar=('PACKET','CHAIN'));ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 coverpath=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json';cover=read(coverpath)
 turn=lambda J:tuple(sorted(15-i for i in J))
 canonical=sorted({min(J,turn(J)) for J in combinations(range(16),11)})
 need(len(canonical)==2184 and [list(J) for J in canonical]==cover['canonical_eleven_cell_subsets'],'canonical enumeration differs')
 known_checkers={sha(WORK/'new_mask_audit/audit_wall_mask_chain.py'),sha(WORK/'phase2/audit/audit_wall_mask_chain_v2.py'),sha(HERE/'audit_wall_mask_chain_v3.py')}
 sets=[];rows=[];used=set();union=set();U=None
 for packetpath,chainpath in args.entry:
  p=read(packetpath);r=read(chainpath);ph=sha(packetpath)
  need(ph not in used,'duplicate packet entry');used.add(ph)
  need(r['status']=='PASS_INDEPENDENT_COMPLETE_WALL_MASK_CHAIN_AUDIT' and r['audit_checker_sha256'] in known_checkers,'unbound chain checker')
  need(r['packet_sha256']==ph and r['cover_sha256']==sha(coverpath) and r['exact_alpha_below_U'],'unbound packet, cover, or target side')
  if U is None:U=F(r['parent_Uplus'])
  need(F(r['parent_Uplus'])==U and F(p['parent_Uplus'])==U,'different side domains')
  if 'independent_geometry_checker_sha256' in r:need(r['independent_geometry_checker_sha256'] in (sha(WORK/'phase2/audit/independent_patch_cover.py'),sha(HERE/'independent_weighted_cover.py')),'independent geometry checker changed')
  O=set(p.get('conditional_owner_support',p['mask']));gamma=p['threshold_units'];B=p['certificate']['budget_units'];P={i for i in p['mask'] if gamma[i]>0}
  need(sorted(O)==sorted(r['conditional_owner_support']) and sorted(P)==r['proved_positive_cells'] and B==r['budget_units'],'chain premises differ')
  applies=lambda J:O<=set(J) and sum(gamma[i] for i in P if i in J)>B
  allowed={j for j,J in enumerate(canonical) if applies(J) or applies(turn(J))}
  need(allowed==set(r['transferred_canonical_mask_indices']) and len(allowed)==r['continuum_canonical_masks_excluded'],'independent transfer enumeration differs')
  need(p['mask_index'] in allowed,'base case missing')
  rows.append(dict(base_mask_index=p['mask_index'],packet_path=str(packetpath),packet_sha256=ph,chain_path=str(chainpath),chain_sha256=sha(chainpath),
   required_owner_cells=sorted(O),positive_cell_thresholds={str(i):gamma[i] for i in sorted(P)},budget_units=B,
   canonical_cases=len(allowed),new_cases_in_entry_order=len(allowed-union)))
  sets.append(allowed);union|=allowed
 assignmentpath=ROOT/'research/optimality/global_capture/trump-cell-symmetric-assignments.json'
 candidate=[canonical.index(tuple(J)) for J in read(assignmentpath)['canonical_capture_masks']]
 need(len(candidate)==4 and not(set(candidate)&union),'known candidate case incorrectly excluded')
 out=dict(status='PASS_INDEPENDENT_GENERAL_PATTERN_UNION_AUDIT',checker_sha256=sha(Path(__file__)),cover_sha256=sha(coverpath),parent_Uplus=str(U),
  entries=rows,pairwise_intersection_counts=[[len(A&B) for B in sets] for A in sets],canonical_cases=2184,
  excluded_canonical_cases=len(union),remaining_canonical_cases=2184-len(union),excluded_canonical_mask_indices=sorted(union),remaining_canonical_mask_indices=sorted(set(range(2184))-union),
  known_candidate_canonical_mask_indices=candidate,known_candidate_masks_survive=True,original_mask2140_already_in_union=2140 in union,
  new_cases_beyond_original_mask2140=len(union-{2140}),global_optimality_proved=False,
  scope='Independent complete canonical containment/whole-packing half-turn union of the supplied exact field certificates. Cases outside the union remain unresolved.')
 args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('excluded_canonical_mask_indices','remaining_canonical_mask_indices')},indent=2))
if __name__=='__main__':main()
