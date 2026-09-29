from pathlib import Path
from fractions import Fraction as F
import json,argparse,hashlib
import numpy as np
HERE=Path(__file__).resolve().parent;BASE=Path('/workspace/scratch/6def36ddf53b/current/research/optimality/deficit_geometry/physical_features');COVER=BASE.parents[3]/'research/optimality/global_capture/center-cover-symmetric-exact.json'
def make(idx,out):
 z=np.load(HERE/f'weights-{idx}.npz');w=z['weights'];g=z['gamma'];mask=list(map(int,z['mask']));positive=np.flatnonzero(w>1e-8);base=float(w[positive].min());rat=w[positive]/base
 if max(abs(rat-np.rint(rat)))>1e-6 or max(rat)>100:raise ValueError('not simpleintegerweights')
 wi=np.zeros(len(w),dtype=np.int64);wi[positive]=np.rint(rat).astype(int);gamma=[0]*16
 for i,gg in zip(mask,g/base):gamma[i]=int(np.floor(gg+1e-6))
 family=json.loads((BASE/'family.json').read_text());used=sorted({s for i in positive for s in family['features'][int(i)]['sites']});lookup={s:i for i,s in enumerate(used)};pw=[0]*len(used);features=[]
 for i in positive:
  f=family['features'][int(i)]
  if f['kind']=='point':pw[lookup[f['sites'][0]]]+=int(wi[i])
  else:features.append(dict(kind=f['kind'],indices=[lookup[s] for s in f['sites']],threshold=f['threshold'],weight=int(wi[i]),source_physical_feature=int(i)))
 budget=sum(pw)+sum(f['weight']*(1 if f['kind']=='majority_hull' else len(f['indices'])//f['threshold']) for f in features)
 if sum(gamma[i] for i in mask)<=budget:raise ValueError('Nointegergap')
 groups=json.loads((HERE.parents[1]/'geometry/wall_ownership_groups.json').read_text())
 packet=dict(status='FINITE_SCREEN_PROPOSAL_NOT_PROOF',certificate=dict(L=family['L'],coordinate_denominator=family['coordinate_denominator'],weight_denominator=1,sites=[family['sites'][i] for i in used],point_weights=pw,features=features,budget_units=budget),cover_sha256=hashlib.sha256(COVER.read_bytes()).hexdigest(),parent_Uplus=groups['parent_Uplus'],mask_index=idx,mask=mask,threshold_units=gamma,conditional_ownership='cell_owned_points',ownership_points_field=groups['groups'],positive_physical_features=len(positive),source_physical_feature_indices=list(map(int,positive)),finite_weights_sha256=hashlib.sha256((HERE/f'weights-{idx}.npz').read_bytes()).hexdigest(),geometry_coverage=False,global_optimality_proved=False)
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(packet,indent=2)+'\n');return packet
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('mask',type=int);ap.add_argument('output',type=Path);a=ap.parse_args();p=make(a.mask,a.output);print(json.dumps({'mask':a.mask,'budget':p['certificate']['budget_units'],'positive_cells':[i for i,g in enumerate(p['threshold_units']) if g],'features':p['source_physical_feature_indices']}))
