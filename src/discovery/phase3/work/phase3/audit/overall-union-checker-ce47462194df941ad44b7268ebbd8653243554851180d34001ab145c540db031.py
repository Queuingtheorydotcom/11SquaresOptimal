#!/usr/bin/env python3
"""Independent union of audited charge fields and unconditional hull patterns."""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import json,hashlib,argparse
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
COVER=ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'
U=F(387708359002281417731,10**20)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def need(x,m):
 if not x:raise ValueError(m)
def resolve(p):
 p=Path(p)
 if p.is_file():return p.resolve()
 if not p.is_absolute():
  q=ROOT/p
  if q.is_file():return q.resolve()
 else:
  for anchor in ('work','current'):
   indices=[i for i,v in enumerate(p.parts) if v==anchor]
   if len(indices)==1:
    q=ROOT/Path(*p.parts[indices[0]:])
    if q.is_file():return q.resolve()
 raise FileNotFoundError(p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--fields',type=Path,default=HERE/'current-union-independent-audit.json');ap.add_argument('--generic-entries',type=Path,default=HERE/'generic_audit_entries.json');ap.add_argument('--output',type=Path,default=HERE/'overall-union-independent-audit.json');a=ap.parse_args()
 cover=read(COVER);turn=lambda J:tuple(sorted(15-i for i in J));canonical=sorted({min(J,turn(J)) for J in combinations(range(16),11)})
 need(len(canonical)==2184 and list(map(list,canonical))==cover['canonical_eleven_cell_subsets'],'canonical cover enumeration differs')
 need(sha(COVER)=='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e','changed exact cover')
 for i in range(16):
  need({tuple(1-F(v) for v in p) for p in cover['cells'][i]['vertices']}=={tuple(map(F,p)) for p in cover['cells'][15-i]['vertices']},'cell half-turn vertex geometry differs')
 field_bytes=a.fields.read_bytes();field_hash=hashlib.sha256(field_bytes).hexdigest();fields=json.loads(field_bytes);field_snapshot=HERE/f'field-union-snapshot-{field_hash[:12]}.json';field_snapshot.write_bytes(field_bytes);need(fields['status']=='PASS_INDEPENDENT_GENERAL_PATTERN_UNION_AUDIT' and fields['checker_sha256']==sha(HERE/'audit_union_registry_v3.py'),'unbound field union')
 need(fields['cover_sha256']==sha(COVER) and F(fields['parent_Uplus'])==U,'field domain differs')
 known_field={sha(ROOT/'work/new_mask_audit/audit_wall_mask_chain.py'),sha(ROOT/'work/phase2/audit/audit_wall_mask_chain_v2.py'),sha(HERE/'audit_wall_mask_chain_v3.py')}
 field_union=set()
 for e in fields['entries']:
  pp=resolve(e['packet_path']);cp=resolve(e['chain_path']);p=read(pp);c=read(cp)
  need(sha(pp)==e['packet_sha256']==c['packet_sha256'] and sha(cp)==e['chain_sha256'],'field packet/chain changed')
  need(c['status']=='PASS_INDEPENDENT_COMPLETE_WALL_MASK_CHAIN_AUDIT' and c['audit_checker_sha256'] in known_field and c['exact_alpha_below_U'],'unbound field chain')
  O=set(p.get('conditional_owner_support',p['mask']));g=p['threshold_units'];P={i for i in p['mask'] if g[i]>0};budget=p['certificate']['budget_units']
  applies=lambda J:O<=set(J) and sum(g[i] for i in P if i in J)>budget
  cases={i for i,J in enumerate(canonical) if applies(J) or applies(turn(J))}
  need(cases==set(c['transferred_canonical_mask_indices']),'field transfer differs');field_union|=cases
 need(sorted(field_union)==fields['excluded_canonical_mask_indices'],'field union differs')
 generic_rows=[];union=set(field_union);generic_union=set();seen=set()
 for e in read(a.generic_entries) if a.generic_entries.exists() else []:
  source=resolve(e['source']);receipt=resolve(e['audit']);d=read(source);r=read(receipt)
  need(r['source_sha256']==sha(source) and sha(source) not in seen,'duplicate/changed generic source');seen.add(sha(source))
  need(r['status']=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT' and r['mask_exclusion_proved'] and r['branch_exclusion_proved'],'generic result is not an exclusion')
  need(r['constraints']==d['constraints']==[] and d['contradiction'],'branch-dependent or absent generic contradiction')
  need(F(r['parent_Uplus'])==F(d['U'])==U and F(r['parent_side'])==F(d['B'])==F(191,50)/U and r['cover_sha256']==sha(COVER),'generic domain differs')
  mask=r['mask'];idx=r['mask_index'];need(mask==d['mask'] and idx==d['mask_index'] and mask==sorted(set(mask)) and set(mask)<=set(canonical[idx]),'generic antecedent mismatch')
  root=resolve(d['source']['path']);need(sha(root)==r['root_sha256']==d['source']['sha256'],'generic root changed')
  prior=read(root);need(prior['mask']==mask and prior['mask_index']==idx,'root mask differs')
  node=r['nodes'][-1];need(node['sha256']==sha(source) and node['constraints']==[] and node['branch_exclusion_proved'],'generic terminal audit differs')
  for n in r['nodes']:need(sha(resolve(n['path']))==n['sha256'],'generic ancestor changed')
  deps=r['dependencies'];checkers=[name for name in deps if name.startswith('audit_capture_v') and name.endswith('.py')]
  need(len(checkers)==1 and checkers[0] in ('audit_capture_v4.py','audit_capture_v5.py','audit_capture_v6.py','audit_capture_v7.py','audit_capture_v8.py','audit_capture_v9.py'),'unknown generic checker')
  roots=[ROOT/'work/phase3/hull',ROOT/'work/phase3/collision',ROOT/'work/geometry',ROOT/'current/research/optimality/audit',ROOT/'work/phase2/hull']
  for name,h in deps.items():need(any((p/name).is_file() and sha(p/name)==h for p in roots),'generic checker dependency changed: '+name)
  if r.get('rational_backend')=='gmp':need(any(sha(p)==r['rational_binary_sha256'] for p in (ROOT/'work/phase3/deps/gmpy2').glob('*.so')),'exact rational binary changed')
  if prior.get('schema')=='generic_wall_seed_v1':need(r['root_audit_sha256'] is None and r['bootstrap']['kind']=='independently_verified_wall_seed','fresh seed bootstrap mismatch')
  else:
   need(r['root_audit_sha256'] and r['bootstrap']['kind']=='source_bound_prior_independent_ownership_audit','missing derived-root antecedent')
   need(mask==list(canonical[idx]),'derived root cannot reduce its original antecedent')
   need(d['source'].get('independent_audit_sha256')==r['root_audit_sha256'] and sha(resolve(d['source']['independent_audit_path']))==r['root_audit_sha256'],'derived-root independent audit changed')
  cases={i for i,J in enumerate(canonical) if set(mask)<=set(J) or set(mask)<=set(turn(J))}
  if 'transferred_canonical_mask_indices' in r:need(cases==set(r['transferred_canonical_mask_indices']),'generic transfer differs')
  need(idx in cases,'generic base case absent')
  generic_rows.append(dict(base_mask_index=idx,required_owner_cells=mask,source=str(source.relative_to(ROOT)),source_sha256=sha(source),audit=str(receipt.relative_to(ROOT)),audit_sha256=sha(receipt),canonical_cases=len(cases),new_cases_in_entry_order=len(cases-union),rows=sum(n['rows'] for n in r['nodes'])))
  generic_union|=cases;union|=cases
 candidates=[438,999,1462,1659];need(not(set(candidates)&union),'known candidate case incorrectly excluded')
 out=dict(status='PASS_INDEPENDENT_OVERALL_EXCLUSION_UNION',checker_sha256=sha(__file__),cover_sha256=sha(COVER),parent_Uplus=str(U),field_registry_sha256=field_hash,field_registry=str(field_snapshot.relative_to(ROOT)),field_cases=len(field_union),generic_cases=len(generic_union),generic_cases_beyond_fields=len(generic_union-field_union),generic_entries=generic_rows,canonical_cases=2184,excluded_canonical_cases=len(union),remaining_canonical_cases=2184-len(union),excluded_canonical_mask_indices=sorted(union),remaining_canonical_mask_indices=sorted(set(range(2184))-union),known_candidate_canonical_mask_indices=candidates,known_candidate_masks_survive=True,global_optimality_proved=False,scope='Union of source-bound independently audited ordinary charge-field exclusions and unconditional generic ownership/collision pattern exclusions at fixed rational U. Conditional guards, incomplete geometry, and branch-only contradictions are excluded from this registry.')
 temporary=a.output.with_suffix('.json.'+str(__import__('os').getpid())+'.tmp');temporary.write_text(json.dumps(out,indent=2)+'\n');temporary.replace(a.output)
 temporary=HERE/('overall-remaining-mask-indices.'+str(__import__('os').getpid())+'.json.tmp');temporary.write_text(json.dumps(out['remaining_canonical_mask_indices'])+'\n');temporary.replace(HERE/'overall-remaining-mask-indices.json')
 print(json.dumps({k:v for k,v in out.items() if k not in ('excluded_canonical_mask_indices','remaining_canonical_mask_indices','generic_entries')},indent=2))
if __name__=='__main__':main()
