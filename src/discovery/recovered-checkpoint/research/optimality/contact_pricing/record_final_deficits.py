from discover import *
st=np.load(OUT/'deep-adversarial1/state.npz');z=np.load(OUT/'hard-poses1/model.npz');model={k:z[k].item() if k=='nvar' else z[k] for k in z.files if k!='budget'};active=thin(model,st['weights']);ids=np.flatnonzero(st['weights']>1e-10);lookup=np.zeros(len(st['weights']),np.int32);lookup[ids]=np.arange(1,len(ids)+1);active['pids']=lookup[active['pids']];active['gids']=lookup[active['gids']];active['nvar']=len(ids)+1;aw=np.r_[0.,st['weights'][ids]]
ap=legal_poses(qmc.Sobol(3,scramble=True,seed=7303).random_base2(16));scores=np.concatenate([capture(active,ap[i:i+1024])@aw for i in range(0,len(ap),1024)]);fp=list(ap[scores<1-1e-8]);fs=list(scores[scores<1-1e-8])
def objective(z):
 p=legal_poses(z.T);q=capture(active,p)@aw
 if len(fp)<10000:
  for pp,v in zip(p,q):
   if v<1-1e-8:fp.append(pp.copy());fs.append(float(v))
 return q
for seed in range(5):differential_evolution(objective,[(0,1)]*3,seed=8841+seed,popsize=20,maxiter=100,tol=1e-8,atol=0,polish=False,vectorized=True,updating='deferred')
fp=np.array(fp);fs=np.array(fs);ca=np.vstack([capture(active,fp[i:i+512]) for i in range(0,len(fp),512)]);_,ix=np.unique(ca,axis=0,return_index=True);ix=ix[np.argsort(fs[ix])[:100]];p=fp[ix];rows=capture(model,p)
assert np.max(np.abs(rows@st['weights']-fs[ix]))<1e-10
np.savez_compressed(OUT/'deep-adversarial1/final-failures.npz',poses=p,rows=rows,scores=fs[ix]);print(json.dumps({'known_distinct_failures':len(p),'minimum':float(min(fs)),'all_training_rows_retained':len(st['rows'])}))
