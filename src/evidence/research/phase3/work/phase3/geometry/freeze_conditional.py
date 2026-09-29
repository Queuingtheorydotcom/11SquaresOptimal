"""Freeze a numerical conditional proposal; this is not a continuum proof."""
from pathlib import Path
from fractions import Fraction as F
import argparse,hashlib,json,math
import numpy as np
if not __debug__: raise RuntimeError('Assertions must be enabled')
HERE=Path(__file__).resolve().parent; WORK=HERE.parents[1]; ROOT=WORK.parent/'current'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--weights',type=Path,required=True);p.add_argument('--ownership',type=Path,required=True);p.add_argument('--seed',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--integer-ratios',action='store_true');a=p.parse_args()
 base=ROOT/'research/optimality/deficit_geometry/physical_features';family=json.loads((base/'family.json').read_text());source=json.loads(a.ownership.read_text());z=np.load(a.weights);mask=z['mask'].tolist();assert mask==source['mask']
 D=10**8;w=z['weights'];wi=[math.ceil(float(x)*D) if x>1e-10 else 0 for x in w];pos=[i for i,x in enumerate(wi) if x];M=sum(int(c)*v for c,v in zip(z['capacity'],wi));gap=11-float(z['capacity']@w);assert gap>0
 gamma=[0]*16
 for cell,g in zip(mask,z['gamma']):gamma[cell]=math.floor(max(0,float(g)-gap/22)*D)
 if a.integer_ratios:
  unit=min(w[i] for i in pos);ratios=w/unit;gg=z['gamma']/unit
  assert max(abs(ratios-np.rint(ratios)))<1e-7 and max(abs(gg-np.rint(gg)))<1e-7
  D=1;wi=np.rint(ratios).astype(int).tolist();M=sum(int(c)*v for c,v in zip(z['capacity'],wi))
  gamma=[0]*16
  for cell,g in zip(mask,gg):gamma[cell]=round(float(g))
 assert sum(gamma)>M
 used=sorted({s for i in pos for s in family['features'][i]['sites']});mapping={s:i for i,s in enumerate(used)};pw=[0]*len(used);features=[]
 for i in pos:
  f=family['features'][i]
  if f['kind']=='point':pw[mapping[f['sites'][0]]]+=wi[i]
  else:features.append(dict(kind=f['kind'],indices=[mapping[s] for s in f['sites']],threshold=f['threshold'],weight=wi[i],source_physical_feature=i))
 cert=dict(L=family['L'],coordinate_denominator=family['coordinate_denominator'],weight_denominator=D,sites=[family['sites'][s] for s in used],point_weights=pw,features=features,budget_units=M)
 generic=source.get('schema')=='exact_generic_owned_hull_v1';coverfile=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
 out=dict(status='FINITE_CONDITIONAL_DERIVED_HULL_PROPOSAL',certificate=cert,cover_sha256=sha(coverfile) if generic else source['cover_sha256'],parent_Uplus=source['U'] if generic else source['parent_Uplus'],mask_index=source['mask_index'],mask=mask,threshold_units=gamma,required_antecedent_mask=mask,conditional_ownership='verified_generic_collision_chain' if generic else 'verified_residual_kernel_chain',ownership_source_sha256=sha(a.ownership),ownership_seed_sha256=sha(a.seed),source_weights_sha256=sha(a.weights),positive_physical_features=len(pos),counting_surplus_units=sum(gamma)-M,global_optimality_proved=False,continuum_masks_excluded=0,scope='Proposal only. Conditional owned hulls require the complete independently replayed source chain under all occupied mask cells. Full continuous charge coverage remains required.')
 a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(output=str(a.output),features=len(pos),budget=M,surplus=sum(gamma)-M,thresholds=gamma)))
if __name__=='__main__':main()
