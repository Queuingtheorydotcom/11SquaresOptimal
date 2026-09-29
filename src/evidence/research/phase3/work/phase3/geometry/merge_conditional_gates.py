"""Concatenate complete per-cell proofs with identical checked premises."""
from pathlib import Path
from fractions import Fraction as F
import argparse,hashlib,json
if not __debug__:raise RuntimeError('Assertions must be enabled')
def need(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('sources',type=Path,nargs='+');p.add_argument('--output',type=Path,required=True);a=p.parse_args();docs=[json.loads(p.read_text()) for p in a.sources];base=docs[0];keys=('mask','mask_index','required_antecedent_mask','packet_sha256','cover_sha256','parent_Uplus','parent_side','ownership_premise','budget_units','threshold_sum_units','counting_surplus_units','dependencies')
 for doc in docs:
  need(all(doc[k]==base[k] for k in keys),'Mixed proof premises or checker implementations')
 chosen={};records=[];cells=[];sources=[]
 for path,doc in zip(a.sources,docs):
  for cell in doc['cells']:
   j=cell['cell']
   if j in chosen or not cell['complete']:continue
   need(not cell['pending'] and not cell['unresolved'],'Incomplete cell marked complete');cursor=F(0)
   for lo,hi in cell['accepted']:
    lo,hi=F(lo),F(hi);need(lo==cursor and lo<hi<=1,'Accepted intervals do not partition quarter turn');cursor=hi
   need(cursor==1,'Incomplete angular coverage')
   rr=[r for r in doc['records'] if r['cell']==j];accepted={tuple(map(F,r['interval'])) for r in rr if r['status'].startswith('PASS')}
   need(accepted=={tuple(map(F,x)) for x in cell['accepted']},'Accepted row records missing')
   chosen[j]=True;cells.append(cell);records.extend(rr);sources.append(dict(cell=j,source=str(path),source_sha256=sha(path)))
 complete=set(chosen)==set(base['mask']);out={k:base[k] for k in keys};out.update(status='PASS_EXACT_DERIVED_HULL_MASK_EXCLUSION' if complete else 'INCOMPLETE_DERIVED_HULL_CHARGE_COVERAGE',continuum_masks_excluded=int(complete),global_optimality_proved=False,rows=len(records),cells=cells,records=records,per_cell_proof_sources=sources,merge_checker_sha256=sha(Path(__file__)),scope='Concatenation of disjoint complete physical-cell proofs under identical full-mask ownership and charge premises. Every contributing source is retained. Global optimality is not asserted.')
 a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('cells','records','dependencies','ownership_premise')},indent=2))
if __name__=='__main__':main()
