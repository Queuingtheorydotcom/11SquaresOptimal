"""Exact closed/open TRUE-family rows on contained transported Trump profiles.

Each field sign is evaluated in Q[t]/(M), using integer polynomial interval bounds.
Only Trump poses are covered. No universal charge or packing bound is asserted.
"""
from pathlib import Path
import sys,json,time,math,hashlib
from fractions import Fraction
import sympy as sp
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/construction'))
sys.path.insert(0,str(ROOT/'research/stromquist'))
from verify_trump import E,u,configuration,M,I
from fast_exact_parent import FastExactParentModel

class FieldSigns:
 def __init__(self):
  self.Q=10**70
  guess=sp.nroots(M,maxsteps=200,n=90)
  r=next(z for z in guess if abs(sp.im(z))<sp.Rational(1,10**80) and sp.Rational(36,100)<sp.re(z)<sp.Rational(37,100))
  self.lo=int(sp.floor(sp.re(r)*self.Q));self.hi=self.lo+1
  assert M.eval(sp.Rational(self.lo,self.Q))<0<M.eval(sp.Rational(self.hi,self.Q))
  self.pl=[self.lo**k*self.Q**(7-k) for k in range(8)]
  self.ph=[self.hi**k*self.Q**(7-k) for k in range(8)]
  self.count=0;self.zeros=0
 def matrix(self,*zs):
  vals=[[z.p.nth(k) for k in range(8)] for z in zs]
  den=sp.ilcm(*[x.q for row in vals for x in row])
  return [tuple(int(v*den) for v in row) for row in vals]
 def sign(self,a):
  self.count+=1
  if not any(a):self.zeros+=1;return 0
  low=sum(x*(self.pl[k] if x>0 else self.ph[k]) for k,x in enumerate(a))
  if low>0:return 1
  high=sum(x*(self.ph[k] if x>0 else self.pl[k]) for k,x in enumerate(a))
  assert high<0,('undecided interval; increase Q',a)
  return -1
 def lin(self,mat,weights):
  return self.sign([sum(v[k]*w for v,w in zip(mat,weights)) for k in range(8)])

def main():
 start=time.time();family=ROOT/'research/stromquist/candidate-true-enriched-round6.json'
 model=FastExactParentModel(family);f=FieldSigns();assert M.is_irreducible and M.count_roots(*I)==1
 squares,alpha,axes=configuration(E(u));B=E(model.L.numerator)/E(model.L.denominator)/alpha
 target=Fraction(sys.argv[1]);A=E(sp.Rational(model.L/target));L=E(sp.Rational(model.L))
 transported=[]
 for i,sq in enumerate(squares):
  oldcenter=tuple(sum((v[j] for v in sq),E(0))/4 for j in range(2))
  C,S=(E(1),E(0)) if i<6 else axes[2]
  width=C+S;ratio=(L-A*width)/(L-B*width)
  center=tuple(L/2+(B*z-L/2)*ratio for z in oldcenter)
  transported.append([(center[0]+A*(x-oldcenter[0]),center[1]+A*(y-oldcenter[1])) for x,y in sq])
 D=model.D;LD=int(model.L*D);world=[((x+LD)//2,(y+LD)//2) for x,y in model.points];assert all((x+LD)%2==0 and(y+LD)%2==0 for x,y in model.points)
 closed=np.zeros((11,model.nvar),np.uint8);opened=closed.copy();details=[]
 for i,sq in enumerate(squares):
  vs=transported[i];vm=[f.matrix(x,y,E(1)) for x,y in vs]
  em=[]
  for j in range(4):
   p,q=vs[j],vs[(j+1)%4];nx,ny=-(q[1]-p[1]),q[0]-p[0];em.append(f.matrix(nx,ny,-nx*p[0]-ny*p[1]))
  edge=np.array([[f.lin(mat,(x,y,D)) for x,y in world] for mat in em],np.int8)
  cc=np.all(edge>=0,axis=0);oc=np.all(edge>0,axis=0)
  for pid,c,o in zip(model.pids,cc,oc):closed[i,pid]+=int(c);opened[i,pid]+=int(o)
  cnt=0;zero_boundary=[];cache={}
  for gi,(inds,gid,kind,k,mx,my,normals) in enumerate(model.groups):
   hc=sum(int(cc[j]) for j in inds);ho=sum(int(oc[j]) for j in inds)
   if kind!='majority_hull':
    closed[i,gid]+=hc//k if kind=='floor' else int(hc>=k)
    opened[i,gid]+=ho//k if kind=='floor' else int(ho>=k)
    continue
   if ho>=k:closed[i,gid]+=1;opened[i,gid]+=1;continue
   cg=all(sum(int(edge[e,j]>=0) for j in inds)>=k for e in range(4))
   og=all(sum(int(edge[e,j]>0) for j in inds)>=k for e in range(4))
   if not cg:continue
   zeros=[]
   for nx,ny,median in normals:
    key=(nx,ny,median)
    if key not in cache:
     cache[key]=tuple(f.lin(mat,(2*D*nx,2*D*ny,-median-LD*(nx+ny))) for mat in vm)
    sg=cache[key];cnt+=1
    if min(sg)>0 or max(sg)<0:cg=False;og=False;break
    if min(sg)==0 or max(sg)==0:og=False;zeros.append([nx,ny,median])
   closed[i,gid]+=int(cg);opened[i,gid]+=int(og)
   if cg and not og:zero_boundary.append({'expanded_group':gi,'column':gid,'normal_boundaries':zeros})
  details.append({'square':i,'closed_capture_sum':int(closed[i].sum()),'open_capture_sum':int(opened[i].sum()),'group_fixed_normal_checks':cnt,'zero_boundary_true_groups':zero_boundary,'edge_site_zeros':int(np.count_nonzero(edge==0))})
  print(json.dumps({'square':i,'elapsed':time.time()-start,'field_signs':f.count,'closed_open_difference_columns':int(np.count_nonzero(closed[i]!=opened[i]))}),flush=True)
 # These are individually legal profiles, not claimed compatible as a packing.
 for vs in transported:
  for x,y in vs:
   for z in [x,y,L-x,L-y]:
    mat=f.matrix(z);assert f.lin(mat,(1,))>=0

 overload=np.flatnonzero(closed.sum(axis=0)>model.budget)
 proposal=ROOT/'research/stromquist/true-round6-cutround12-surplus-3.8754-rational-proposal.json'
 data=json.loads(proposal.read_text());weights=np.array([p[2] for p in data['point_orbits']]+[g['weight'] for g in data['charge_orbits']],np.int64)
 out={'status':('PASS_EXACT_TRANSPORTED_FAMILY_OBSTRUCTION' if np.all(closed.sum(axis=0)<=model.budget) else 'TRANSPORTED_PROFILES_OVERLOAD_FEATURES'),'scope':'Eleven individually contained squares transported from Trump, not a compatible packing. Componentwise profile-budget feasibility obstructs only unchanged-family charge/counting arguments. No packing bound proved.','family_sha256':hashlib.sha256(family.read_bytes()).hexdigest(),'cut12_proposal_sha256':hashlib.sha256(proposal.read_bytes()).hexdigest(),'L':str(model.L),'target_side':str(target),'side_A':str(model.L/target),'transport':'affine legal-center-box transport at unchanged Trump orientation','root_interval':[str(sp.Rational(f.lo,f.Q)),str(sp.Rational(f.hi,f.Q))],'columns':model.nvar,'field_signs':f.count,'zero_field_values':f.zeros,'overloaded_closed_columns':overload.tolist(),'overloaded_closed_columns_positive_cut12':[int(j) for j in overload if weights[j]>0],'closed_cut12_charge_units':(closed@weights).tolist(),'open_cut12_charge_units':(opened@weights).tolist(),'cut12_budget_units':int(model.budget@weights),'cut12_threshold_units':data['minimum_units'],'details':details,'elapsed_seconds':time.time()-start}
 dest=Path(__file__).parent;stem='transported-'+str(float(target));np.savez_compressed(dest/(stem+'.npz'),closed=closed,opened=opened,budget=model.budget,weights=weights)
 (dest/(stem+'.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='details'},indent=2))
if __name__=='__main__':main()
