from pathlib import Path
import json,numpy as np,hashlib,sys,subprocess,os,time
HERE=Path(__file__).parent;TOP=HERE.parents[1];ROOT=TOP.parent/'current';BASE=ROOT/'research/optimality/deficit_geometry/physical_features';SCREEN=HERE.parent/'screen'
family=json.loads((BASE/'family.json').read_text());coverfile=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json';cover=json.loads(coverfile.read_text());groups=json.loads((TOP/'geometry/wall_ownership_groups.json').read_text())['groups'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
env={**os.environ,'PYTHONPATH':str(TOP/'audit/deps'),'OPENBLAS_NUM_THREADS':'1'}
def packet(mask):
 z=np.load(SCREEN/f'weights-{mask}.npz');w=z['weights'];pos=np.flatnonzero(w>1e-10);assert len(pos)==1;i=int(pos[0]);f=family['features'][i];sites=f['sites'];feat=[];pw=[0]*len(sites)
 if f['kind']=='point':pw[0]=1
 else:feat=[dict(kind=f['kind'],indices=list(range(len(sites))),threshold=f['threshold'],weight=1,source_physical_feature=i)]
 gamma=[0]*16
 for cell,x in zip(z['mask'],z['gamma']):gamma[int(cell)]=int(round(x/w[i]))
 return dict(status='FINITE_NONSYMMETRIC_PHYSICAL_PROPOSAL',certificate=dict(L=family['L'],coordinate_denominator=family['coordinate_denominator'],weight_denominator=1,sites=[family['sites'][s] for s in sites],point_weights=pw,features=feat,budget_units=f['capacity']),cover_sha256=sha(coverfile),parent_Uplus='387708359002281417731/100000000000000000000',mask_index=mask,mask=z['mask'].tolist(),threshold_units=gamma,conditional_counting_surplus_units=sum(gamma)-f['capacity'],positive_physical_features=1,source_family_sha256=sha(BASE/'family.json'),source_solution_sha256=sha(SCREEN/f'weights-{mask}.npz'),source_physical_feature_indices=[i],conditional_ownership='cell_owned_points',ownership_points_field=groups,wall_aware_ownership_extension=True,geometry_coverage=False,global_optimality_proved=False,scope='Finite LP proposal until complete exact wall-aware continuum gate succeeds.')
def run(p,label,seconds=45):
 pp=HERE/(label+'-packet.json');out=HERE/(label+'-gate.json');pp.write_text(json.dumps(p,indent=2)+'\n')
 with (HERE/(label+'.log')).open('w') as f:
  try:subprocess.run([sys.executable,str(TOP/'geometry/verify_wall_aware_mask.py'),str(pp),'--output',str(out),'--seconds',str(seconds),'--max-depth','16','--max-rows','16000','--bins','32'],stdout=f,stderr=subprocess.STDOUT,env=env,check=True,timeout=seconds+45)
  except Exception as e:return dict(status='PROCESS_ERROR',error=str(e),packet=str(pp))
 d=json.loads(out.read_text());return dict(status=d['status'],last=d['records'][-1]['status'],cell=d['records'][-1]['cell'],rows=d['rows'],seconds=d['seconds'],packet=str(pp),receipt=str(out))
def main():
 started=time.monotonic();r=[json.loads(x) for x in (SCREEN/'results.jsonl').read_text().splitlines()];r=[x for x in r if 200<=x['mask']<=700 and x['positive_features']==1 and x['finite_budget']<10.99];seen=set();todo=[]
 for x in sorted(r,key=lambda q:(q['finite_budget'],q['mask'])):
  p=packet(x['mask']);key=(tuple(p['source_physical_feature_indices']),tuple(i for i,g in enumerate(p['threshold_units']) if g))
  if key in seen:continue
  seen.add(key);todo.append((x,p))
 history=json.loads((HERE/'history.json').read_text()) if (HERE/'history.json').exists() else []
 for count,(x,p) in enumerate(todo):
  if time.monotonic()-started>560:break
  mask=x['mask']
  if any(set(h.get('required_cells',[]))<=set(p['mask']) for h in history if h.get('required_cells')):continue
  label=f'mask{mask}-p2batch{count+1}';entry=dict(mask=mask,features=p['source_physical_feature_indices'],**run(p,label));history.append(entry);(HERE/'history.json').write_text(json.dumps(history,indent=2)+'\n');print(json.dumps(entry),flush=True)
  if entry['status'].startswith('PASS_'):
   owners=list(p['mask']);positive={i for i,g in enumerate(p['threshold_units']) if g}
   for drop in [i for i in reversed(owners) if i not in positive]:
    if time.monotonic()-started>580:break
    trial=dict(p,conditional_owner_support=[i for i in owners if i!=drop]);test=run(trial,label+f'-drop{drop}',seconds=35);test.update(mask=mask,dropped=drop);history.append(test);print(json.dumps(test),flush=True)
    if test['status'].startswith('PASS_'):p=trial;owners.remove(drop);entry['minimized_packet']=test['packet'];entry['minimized_receipt']=test['receipt']
    entry['required_cells']=sorted(positive|set(owners));(HERE/'history.json').write_text(json.dumps(history,indent=2)+'\n')
 if time.monotonic()-started>560:print('TIME BUDGET COMPLETE',flush=True)
if __name__=='__main__':main()
