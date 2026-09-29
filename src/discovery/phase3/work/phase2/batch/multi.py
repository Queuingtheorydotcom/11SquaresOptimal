import run_batch as b
import json,numpy as np,hashlib,time

def packet(mask):
 z=np.load(b.SCREEN/f'weights-{mask}.npz');w=z['weights'];pos=np.flatnonzero(w>1e-10);scale=float(w[pos].min());wi=np.rint(w[pos]/scale).astype(int);assert np.max(abs(w[pos]/scale-wi))<1e-7 and wi.max()<=32
 used=sorted({s for i in pos for s in b.family['features'][int(i)]['sites']});remap={s:i for i,s in enumerate(used)};pw=[0]*len(used);features=[];budget=0
 for i,k in zip(pos,wi):
  f=b.family['features'][int(i)];budget+=int(k)*f['capacity']
  if f['kind']=='point':pw[remap[f['sites'][0]]]+=int(k)
  else:features.append(dict(kind=f['kind'],indices=[remap[s]for s in f['sites']],threshold=f['threshold'],weight=int(k),source_physical_feature=int(i)))
 gamma=[0]*16
 for i,g in zip(z['mask'],z['gamma']):
  v=float(g/scale);assert abs(v-round(v))<1e-7;gamma[int(i)]=round(v)
 assert sum(gamma)>budget
 return dict(status='FINITE_NONSYMMETRIC_PHYSICAL_PROPOSAL',certificate=dict(L=b.family['L'],coordinate_denominator=b.family['coordinate_denominator'],weight_denominator=1,sites=[b.family['sites'][s]for s in used],point_weights=pw,features=features,budget_units=budget),cover_sha256=b.sha(b.coverfile),parent_Uplus='387708359002281417731/100000000000000000000',mask_index=mask,mask=z['mask'].tolist(),threshold_units=gamma,conditional_counting_surplus_units=sum(gamma)-budget,positive_physical_features=len(pos),source_physical_feature_indices=pos.tolist(),conditional_ownership='cell_owned_points',ownership_points_field=b.groups,wall_aware_ownership_extension=True,geometry_coverage=False,global_optimality_proved=False,scope='Finite LP proposal until complete exact wall-aware continuum gate succeeds.')
def main():
 patterns=[[1,2,4,5,8,9,13],[1,2,4,5,6,7,11],[0,1,2,3,6],[0,4,8,12],[0,1,2,4,5,6,7,10],[1,2,4,5,6,8,9,10,11,14]];patterns=[set(x)for p in patterns for x in[p,[15-i for i in p]]]
 rs=[json.loads(x)for x in(b.SCREEN/'results.jsonl').read_text().splitlines()];rs=[x for x in rs if 200<=x['mask']<=700 and x['mask']not in [232,235] and x.get('positive_features',0)==3 and x.get('finite_budget',11)<10.99 and not any(p<=set(b.cover['canonical_eleven_cell_subsets'][x['mask']])for p in patterns)];seen=set();hist=json.loads((b.HERE/'multi-history.json').read_text()) if (b.HERE/'multi-history.json').exists() else [];start=time.monotonic()
 for x in sorted(rs,key=lambda x:(x['finite_budget'],x['mask'])):
  if time.monotonic()-start>500:break
  if any(e.get('mask')==x['mask'] and 'drop' not in e for e in hist):continue
  try:p=packet(x['mask'])
  except AssertionError:continue
  key=(tuple(p['source_physical_feature_indices']),tuple(p['threshold_units']))
  if key in seen:continue
  seen.add(key);mask=x['mask'];e=dict(mask=mask,**b.run(p,f'mask{mask}-p2batchmulti',seconds=60));hist.append(e);print(json.dumps(e),flush=True);(b.HERE/'multi-history.json').write_text(json.dumps(hist,indent=2)+'\n')
  if e['status'].startswith('PASS_'):
   owners=p['mask'].copy();positive={i for i,g in enumerate(p['threshold_units'])if g}
   for drop in reversed(owners.copy()):
    if drop in positive:continue
    trial=dict(p,conditional_owner_support=[i for i in owners if i!=drop]);ee=b.run(trial,f'mask{mask}-p2batchmulti-drop{drop}',seconds=50);ee.update(mask=mask,drop=drop);hist.append(ee);print(json.dumps(ee),flush=True)
    if ee['status'].startswith('PASS_'):p=trial;owners.remove(drop);e['minimized_packet']=ee['packet'];e['minimized_receipt']=ee['receipt']
    e['required_cells']=sorted(positive|set(owners));(b.HERE/'multi-history.json').write_text(json.dumps(hist,indent=2)+'\n')
   patterns.extend([set(e['required_cells']),{15-i for i in e['required_cells']}])
if __name__=='__main__':main()
