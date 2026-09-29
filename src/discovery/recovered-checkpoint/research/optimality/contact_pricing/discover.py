#!/usr/bin/env python3
"""Bounded floating discovery of algebraic endpoint contact charges.

Not a certificate. All new site/group references retain exact source provenance.
"""
import os
os.environ.setdefault('NUMBA_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from pathlib import Path
import sys,json,hashlib,time,argparse,itertools
from fractions import Fraction as Q
import numpy as np
from scipy.optimize import linprog,differential_evolution
from scipy.sparse import csr_matrix,vstack
from scipy.stats import qmc
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/stromquist'))
from true_majority_model import TrueMajorityModel,full_true_capture
sys.path.insert(0,str(ROOT/'work/construction'))
from verify_trump import configuration
FAMILY=ROOT/'research/stromquist/candidate-true-enriched-round6.json'
CONTACT=ROOT/'research/optimality/endpoint_charge/endpoint-contact-sites.json'
OUT=Path(__file__).parent
L=3.82
T=.365769307604677293388545018143311315
SQ,ALPHA,_=configuration(T)
B=L/ALPHA

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def d4pt(x,y,k):
 if k>=4:x,y=y,x
 if k%4>=2:x=L-x
 if k%2:y=L-y
 return x,y

def build(ngroups=600,seed=811,pool_per_contact=45,cardinalities=(3,5)):
 m=TrueMajorityModel(FAMILY);c=json.loads(CONTACT.read_text());rng=np.random.default_rng(seed)
 D=m.c['coordinate_denominator'];LD=int(Q(m.c['L'])*D)
 old_integer=[]
 for x,y,_ in m.c['point_orbits']:old_integer.extend(sorted({(a,b) for p,q in ((x,y),(y,x)) for a in (p,LD-p) for b in (q,LD-q)}))
 oldids={p:i for i,p in enumerate(old_integer)}
 maps=np.zeros((8,len(old_integer)+sum(o['size'] for o in c['orbits'])),np.int32)
 for k in range(8):
  for i,(x,y) in enumerate(old_integer):
   if k>=4:x,y=y,x
   if k%4>=2:x=LD-x
   if k%2:y=LD-y
   maps[k,i]=oldids[(x,y)]
 cps=[];cpids=[];refs=[];keys=[]
 for oi,o in enumerate(c['orbits']):
  for mi,p in enumerate(o['members_coefficients']):
   coeff=tuple(tuple(Q(a) for a in xy) for xy in p);keys.append(coeff)
   cps.append([sum(float(a)*T**j for j,a in enumerate(xy)) for xy in coeff]);cpids.append(m.nvar+oi)
   refs.append({'contact_orbit':oi,'member':mi})
 keyids={p:len(old_integer)+i for i,p in enumerate(keys)}
 for k in range(8):
  for j,(x,y) in enumerate(keys):
   if k>=4:x,y=y,x
   if k%4>=2:x=(Q('3.82')-x[0],)+tuple(-a for a in x[1:])
   if k%2:y=(Q('3.82')-y[0],)+tuple(-a for a in y[1:])
   maps[k,len(old_integer)+j]=keyids[(x,y)]
 points=np.vstack([m.points,cps]);centered=points-L/2
 contactids=np.arange(len(old_integer),len(points),dtype=int)
 # Generate contact-containing groups using exact site references. Nearest sites
 # are selected numerically, but no coordinates are rounded in the saved source.
 bases={}
 # All nearby contact triples, plus old rational points on opposite sides of p.
 for p in contactids:
  near_c=contactids[np.argsort(np.linalg.norm(points[contactids]-points[p],axis=1))[1:15]]
  near_old=np.argsort(np.linalg.norm(m.points-points[p],axis=1))[:70]
  pool=np.r_[near_c,near_old]
  for _ in range(pool_per_contact):
   cardinality=cardinalities[0] if rng.random()<.8 else cardinalities[1]
   qs=rng.choice(pool,cardinality-1,replace=False)
   ids=tuple(sorted([int(p),*map(int,qs)]))
   # Avoid nearly degenerate groups; collinear triples are a point charge.
   z=points[list(ids)]
   if max(np.linalg.norm(z-z[0],axis=1))<.03:continue
   orbit=tuple(sorted({tuple(sorted(maps[k,list(ids)])) for k in range(8)}))
   if orbit not in bases:bases[orbit]=ids
 candidates=list(bases.items());rng.shuffle(candidates);candidates=candidates[:ngroups]
 new_groups=[];new_gids=[];new_lens=[];groupmeta=[];newbudget=[]
 for gi,(orbit,ids) in enumerate(candidates):
  gid=m.nvar+len(c['orbits'])+gi
  for g in orbit:new_groups.append(list(g)+[-1]*(m.groups.shape[1]-len(g)));new_gids.append(gid);new_lens.append(len(g))
  groupmeta.append({'base_sites':[{'old_point_index':int(p)} if p<len(old_integer) else refs[p-len(old_integer)] for p in ids], 'orbit_sets':[list(map(int,g)) for g in orbit], 'kind':'majority_hull','cardinality':len(ids),'budget':len(orbit)})
  newbudget.append(len(orbit))
 groups=np.vstack([m.groups,np.asarray(new_groups,np.int32)]);gids=np.r_[m.gids,new_gids].astype(np.int32)
 lens=np.r_[m.length,new_lens].astype(np.int32);kinds=np.r_[m.kinds,np.full(len(new_groups),3)].astype(np.int32)
 th=np.r_[m.thresh,(np.array(new_lens)+1)//2].astype(np.int32)
 ns=np.zeros((len(groups),21,2));med=np.zeros((len(groups),21));cnt=np.zeros(len(groups),np.int32);wm=np.zeros((len(groups),2))
 ns[:len(m.groups)]=m.true_normals;med[:len(m.groups)]=m.true_medians;cnt[:len(m.groups)]=m.true_counts;wm[:len(m.groups)]=m.world_medians
 for j in range(len(m.groups),len(groups)):
  pts=centered[groups[j,:lens[j]]];wm[j]=np.median(pts,axis=0);nn=[]
  for a,b in itertools.combinations(pts,2):
   d=a-b;n=np.array([d[1],-d[0]]);scale=max(abs(n))
   if scale<1e-13:continue
   n/=scale
   if n[0]<-1e-13 or (abs(n[0])<1e-13 and n[1]<0):n=-n
   if not any(np.linalg.norm(n-v)<1e-11 for v in nn):nn.append(n)
  cnt[j]=len(nn);ns[j,:len(nn)]=nn;med[j,:len(nn)]=np.median(pts@np.array(nn).T,axis=0)
 model=dict(points=centered,pids=np.r_[m.pids,cpids].astype(np.int32),groups=groups,gids=gids,kinds=kinds,thresholds=th,length=lens,nvar=m.nvar+len(c['orbits'])+len(candidates),normals=ns,medians=med,normalcounts=cnt,world_medians=wm)
 budget=np.r_[m.budget,[o['size'] for o in c['orbits']],newbudget]
 metadata={'scope':'FLOATING DISCOVERY ONLY; no continuum or exact coverage claim','family_sha256':digest(FAMILY),'contact_sites_sha256':digest(CONTACT),'side':'(191/50)/alpha','root_float':T,'side_float':B,'seed':seed,'old_columns':m.nvar,'contact_columns':len(c['orbits']),'new_groups':groupmeta}
 return model,budget,metadata

def capture(model,poses,tol=0):
 poses=np.asarray(poses,float);rots=np.column_stack([np.cos(poses[:,0]),np.sin(poses[:,0])])
 return full_true_capture(B+tol,L,poses,rots,**model)

def thin(model,weights):
 on=weights>1e-10;gkeep=on[model['gids']];pkeep=on[model['pids']].copy()
 for g,l in zip(model['groups'][gkeep],model['length'][gkeep]):pkeep[g[:l]]=True
 pi=np.flatnonzero(pkeep);lookup=np.full(len(pkeep),-1,np.int32);lookup[pi]=np.arange(len(pi))
 out={}
 for k,v in model.items():
  if k in ('points','pids'):out[k]=v[pi]
  elif k=='nvar':out[k]=v
  elif k=='groups':
   out[k]=v[gkeep].copy();valid=out[k]>=0;out[k][valid]=lookup[out[k][valid]]
  else:out[k]=v[gkeep]
 return out

def legal_poses(z):
 z=np.atleast_2d(z);a=z[:,0]*np.pi/4;r=B/2*(np.cos(a)+np.sin(a));x=r+(L-2*r)*z[:,1];y=r+(L-2*r)*z[:,2]
 return np.column_stack([a,x,y])

def initial(n=2048):
 z=qmc.Sobol(3,scramble=True,seed=92).random_base2(int(np.ceil(np.log2(n))))[:n]
 poses=list(legal_poses(z));tags=['sobol']*n
 # All wall/corner positions at regular angles.
 for theta in np.linspace(0,np.pi/4,65):
  r=B/2*(np.cos(theta)+np.sin(theta))
  for x,y in itertools.product([r,(L-r+r)/2,L-r],repeat=2):poses.append([theta,x,y]);tags.append('wall_grid')
 templates=[]
 for sq in SQ:
  sq=np.array(sq)*B;center=sq.mean(axis=0);d=sq[1]-sq[0];theta=np.arctan2(d[1],d[0])%(np.pi/2)
  templates.append([theta,*center])
 # D4 isn't needed for complete family, but preserve exact configuration labels.
 for i,(theta,x,y) in enumerate(templates):
  poses.append([theta,x,y]);tags.append('trump_exact_'+str(i))
  for eps in [1e-9,1e-6,1e-4,.001]:
   for da,dx,dy in itertools.product([-1,0,1],repeat=3):
    if da==dx==dy==0:continue
    aa=theta+eps*da;rr=B/2*(abs(np.cos(aa))+abs(np.sin(aa)))
    xx=np.clip(x+eps*dx,rr,L-rr);yy=np.clip(y+eps*dy,rr,L-rr)
    poses.append([aa,xx,yy]);tags.append('trump_perturb')
 return np.array(poses),tags

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--groups',type=int,default=600);ap.add_argument('--rounds',type=int,default=4);ap.add_argument('--sobol',type=int,default=2048);ap.add_argument('--label',default='pilot1');args=ap.parse_args();start=time.time()
 model,budget,meta=build(args.groups);poses,tags=initial(args.sobol)
 assert len(poses)<=5000
 dest=OUT/args.label;dest.mkdir(exist_ok=True)
 (dest/'model.json').write_text(json.dumps(meta,indent=2)+'\n')
 np.savez_compressed(dest/'model.npz',budget=budget,**model)
 rows=capture(model,poses)
 # Closed boundary noise for exact templates is addressed by a tiny expansion
 # only on those 11 rows. This cannot be used as exact evidence.
 exactids=[i for i,t in enumerate(tags) if t.startswith('trump_exact_')]
 rows[exactids]=capture(model,poses[exactids],2e-12)
 old=np.load(ROOT/'research/optimality/endpoint_charge/exact-trump-endpoint-rows.npz')['closed']
 contacts=np.load(ROOT/'research/optimality/endpoint_charge/endpoint-contact-sites.npz')['closed']
 rows[np.ix_(exactids,np.arange(old.shape[1]))]=old
 rows[np.ix_(exactids,np.arange(old.shape[1],old.shape[1]+contacts.shape[1]))]=contacts
 history=[]
 for iteration in range(args.rounds):
  # Deterministic distinct profiles, one bounded LP at a time.
  unique,ui=np.unique(rows,axis=0,return_index=True);mat=csr_matrix(unique,dtype=float)
  with threadpool_limits(limits=1):sol=linprog(budget,A_ub=-mat,b_ub=-np.ones(len(unique)),bounds=(0,None),method='highs')
  if not sol.success:raise RuntimeError(sol.message)
  w=sol.x;active=thin(model,w)
  # Universal obligation tested against fresh legal random + low-row perturbations.
  z=qmc.Sobol(3,scramble=True,seed=500+iteration).random_base2(13)
  adversary=legal_poses(z)
  scores=np.concatenate([capture(active,adversary[j:j+512])@w for j in range(0,len(adversary),512)])
  order=np.argsort(scores);seedposes=adversary[order[:30]]
  local=[]
  for theta,x,y in seedposes:
   for da,dx,dy in itertools.product([-1,0,1],repeat=3):
    aa=theta+da*.0005;r=B/2*(abs(np.cos(aa))+abs(np.sin(aa)));local.append([aa,np.clip(x+dx*.0005,r,L-r),np.clip(y+dy*.0005,r,L-r)])
  local=np.array(local);ls=capture(active,local)@w
  allposes=np.vstack([adversary,local]);allscores=np.r_[scores,ls];bad=np.argsort(allscores)[:240]
  newposes=allposes[bad];newrows=capture(model,newposes)
  report={'round':iteration,'rows':len(rows),'distinct_rows':len(unique),'columns':len(budget),'mass':float(sol.fun),'positive_columns':int(sum(w>1e-9)),'positive_new_groups':int(sum(w[4716+15:]>1e-9)),'adversarial_minimum':float(allscores.min()),'adversarial_failures':int(sum(allscores<1-1e-8)),'elapsed':time.time()-start}
  history.append(report);print(json.dumps(report),flush=True)
  np.savez_compressed(dest/'state.npz',rows=rows,poses=poses,weights=w,budget=budget,dual=sol.ineqlin.marginals,unique_indices=ui,adversary_poses=newposes,adversary_rows=newrows)
  (dest/'RESULT.json').write_text(json.dumps({'status':'FLOATING_FINITE_LP_AND_ADVERSARIAL_SEARCH_ONLY','global_bound_proved':False,'history':history,'model_sha256':digest(dest/'model.json'),'side_B':B,'initial_rows':len(tags),'exact_template_rows':exactids,'latest_positive_weights':[{'column':int(j),'weight':float(w[j]),'budget':float(budget[j])} for j in np.flatnonzero(w>1e-9)]},indent=2)+'\n')
  if sol.fun>=11-1e-9 or allscores.min()>=1-1e-9:break
  rows=np.vstack([rows,newrows]);poses=np.vstack([poses,newposes])
if __name__=='__main__':main()
