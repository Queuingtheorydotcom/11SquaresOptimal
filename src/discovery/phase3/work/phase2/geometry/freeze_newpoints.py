from pathlib import Path
import numpy as np,json,math,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2]/'current';BASE=ROOT/'research/optimality/deficit_geometry/physical_features';idx=1383
z=np.load(H/f'mask{idx}_newpoints_weights.npz');family=json.loads((BASE/'family.json').read_text());cover=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text());nbase=len(family['features']);w=z['weights'];D=10**8;wi=np.array([math.ceil(float(v)*D) if v>1e-10 else 0 for v in w],np.int64)
positive=np.flatnonzero(wi);used=sorted({s for i in positive if i<nbase for s in family['features'][int(i)]['sites']});sites=[family['sites'][s] for s in used];remap={s:i for i,s in enumerate(used)};pw=[0]*len(used);features=[]
for i in positive:
 if i>=nbase:
  sites.append(z['sites'][i-nbase].tolist());pw.append(int(wi[i]));continue
 f=family['features'][int(i)]
 if f['kind']=='point':pw[remap[f['sites'][0]]]+=int(wi[i])
 else:features.append(dict(kind=f['kind'],indices=[remap[s] for s in f['sites']],threshold=f['threshold'],weight=int(wi[i]),source_physical_feature=int(i)))
# Deduplicate site coordinates while preserving resource supports.
lookup={};compact=[];cpw=[];convert={}
for i,p in enumerate(sites):
 pp=tuple(p)
 if pp not in lookup:lookup[pp]=len(compact);compact.append(p);cpw.append(0)
 j=lookup[pp];convert[i]=j;cpw[j]+=pw[i]
for f in features:f['indices']=[convert[i] for i in f['indices']]
M=int(z['capacity']@wi);gap=11-float(z['capacity']@w);threshold=[0]*16
for cell,g in zip(z['mask'],z['gamma']):threshold[int(cell)]=math.floor(max(0,float(g)-gap/22)*D)
assert sum(threshold)-M>0
certificate=dict(L=family['L'],coordinate_denominator=10**10,weight_denominator=D,sites=compact,point_weights=cpw,features=features,budget_units=M)
groups=json.loads((H.parents[1]/'geometry/wall_ownership_groups.json').read_text());mask=list(map(int,z['mask']))
p=dict(status='FINITE_NEWPOINT_PHYSICAL_PROPOSAL',certificate=certificate,cover_sha256='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e',parent_Uplus=groups['parent_Uplus'],mask_index=idx,mask=mask,threshold_units=threshold,conditional_ownership='cell_owned_points',ownership_points_field=groups['groups'],positive_physical_features=len(positive),physical_newpoint_resources=int(sum(i>=nbase for i in positive)),source_weights_sha256=hashlib.sha256((H/f'mask{idx}_newpoints_weights.npz').read_bytes()).hexdigest(),scope='Finite candidate with novel ordinary point resources; no continuum claim before complete exact gate.')
(H/f'mask{idx}_newpoints_packet.json').write_text(json.dumps(p,indent=2));print('budget',M,'surplus',sum(threshold)-M,'features',len(positive),'newpoints',p['physical_newpoint_resources'])
