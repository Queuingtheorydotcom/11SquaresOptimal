#!/usr/bin/env python3
"""Standalone exact upper-charge rejection for an algebraic endpoint proposal.

Requires SymPy and NumPy only for discovery. --verify replays the saved witness
using SymPy and exact integers/rationals; it performs no numerical geometry.
"""
import sys,json,hashlib,time,argparse
from pathlib import Path
from fractions import Fraction
import sympy as sp

T=sp.Symbol('t')
POLY=sp.Poly(5*T**8-10*T**7-2*T**6+14*T**5+12*T**4-6*T**3+2*T**2+2*T-1,T,domain=sp.QQ)

class Field:
 def __init__(self,lo,hi):
  self.lo,self.hi=map(Fraction,(lo,hi));assert Fraction(36,100)<self.lo<self.hi<Fraction(37,100)
  assert POLY.is_irreducible and POLY.count_roots(sp.Rational(self.lo),sp.Rational(self.hi))==1
  assert POLY.eval(sp.Rational(self.lo))<0<POLY.eval(sp.Rational(self.hi))
  self.den=sp.ilcm(self.lo.denominator,self.hi.denominator);a=int(self.lo*self.den);b=int(self.hi*self.den)
  self.pl=[a**k*int(self.den)**(7-k) for k in range(8)];self.ph=[b**k*int(self.den)**(7-k) for k in range(8)]
  self.sign_count=0
 def sign(self,z):
  self.sign_count+=1;c=[z.p.nth(k) for k in range(8)];d=sp.ilcm(*[x.q for x in c]);a=[int(x*d) for x in c]
  if not any(a):return 0
  low=sum(v*(self.pl[k] if v>0 else self.ph[k]) for k,v in enumerate(a))
  if low>0:return 1
  high=sum(v*(self.ph[k] if v>0 else self.pl[k]) for k,v in enumerate(a))
  assert high<0, 'Increase exact root bracket precision; no sign was certified'
  return -1

class K:
 def __init__(self,x=0):self.p=x.p if isinstance(x,K) else sp.Poly(x,T,domain=sp.QQ).rem(POLY)
 def __add__(self,x):return K(self.p+K(x).p)
 __radd__=__add__
 def __neg__(self):return K(-self.p)
 def __sub__(self,x):return self+-K(x)
 def __rsub__(self,x):return K(x)+-self
 def __mul__(self,x):return K(self.p*K(x).p)
 __rmul__=__mul__
 def __truediv__(self,x):return K(self.p*sp.invert(K(x).p,POLY))
 def coefficients(self):return [str(self.p.nth(k)) for k in range(8)]

def decode(v):
 assert len(v)==8
 return K(sum(sp.Rational(a)*T**k for k,a in enumerate(v)))

def setup(packet,pose):
 assert packet['B']=='(191/50)/alpha' and packet['alpha_expression']=='(6*t+4)/(1+2*t-t^2)' and packet['L']=='191/50'
 assert packet['field_minimal_polynomial_ascending']==[int(POLY.nth(k)) for k in range(9)]
 f=Field(*packet['field_root_interval']);L=K(sp.Rational(packet['L']));z=K(T);alpha=(6*z+4)/(1+2*z-z*z);B=L/alpha;half=B/2
 q=sp.Rational(pose['half_angle']);a=sp.Rational(pose['normalized_x']);b=sp.Rational(pose['normalized_y']);assert 0<=q<=1 and 0<=a<=1 and 0<=b<=1
 C=K((1-q*q)/(1+q*q));S=K(2*q/(1+q*q));assert f.sign(C)>=0 and f.sign(S)>=0
 r=half*(C+S);x=r+a*(L-2*r);y=r+b*(L-2*r)
 assert f.sign(B)>0 and f.sign(L-2*r)>0
 verts=[(x+half*(dx*C-dy*S),y+half*(dx*S+dy*C)) for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
 for vx,vy in verts:
  for gap in [vx,vy,L-vx,L-vy]:assert f.sign(gap)>=0
 points=[tuple(decode(c) for c in p['coordinates_coefficients']) for p in packet['sites']]
 assert len({tuple(tuple(c) for c in p['coordinates_coefficients']) for p in packet['sites']})==len(points)
 captured=[]
 for px,py in points:
  U=C*(px-x)+S*(py-y);V=-S*(px-x)+C*(py-y)
  captured.append(all(f.sign(gap)>=0 for gap in [half-U,half+U,half-V,half+V]))
 return f,L,B,half,C,S,x,y,points,captured

def normal_from(proof,C,S,points):
 if proof['normal_kind']=='axis_u':return C,S
 if proof['normal_kind']=='axis_v':return -S,C
 assert proof['normal_kind']=='site_pair'
 p,q=proof['normal_pair'];assert p!=q
 return points[p][1]-points[q][1],points[q][0]-points[p][0]

def verify_separator(proof,inds,k,ctx):
 f,L,B,half,C,S,x,y,points,captured=ctx
 subset=proof['separated_subset'];assert len(subset)==k and len(set(subset))==k and set(subset)<=set(inds)
 if proof['normal_kind']=='site_pair':assert set(proof['normal_pair'])<=set(inds)
 nx,ny=normal_from(proof,C,S,points);assert f.sign(nx)!=0 or f.sign(ny)!=0
 nu=nx*C+ny*S;nv=-nx*S+ny*C
 support=half*((nu if f.sign(nu)>=0 else -nu)+(nv if f.sign(nv)>=0 else -nv))
 side=proof['side'];assert side in [-1,1]
 boundary=nx*x+ny*y+side*support
 for j in subset:
  gap=side*(nx*points[j][0]+ny*points[j][1]-boundary)
  assert f.sign(gap)>0, 'Claimed strict separating witness fails'
 return True

def compute_upper(packet,proofs,ctx):
 f,*_=ctx;captured=ctx[-1];upper=0;budget=0;table=[];proof_lookup={tuple(p['member_key']):p for p in proofs};assert len(proof_lookup)==len(proofs)
 used=set()
 for fi,feature in enumerate(packet['features']):
  weight=feature['weight_units'];assert isinstance(weight,int) and weight>0
  kind=feature['kind'];value=0;cap=0
  if kind=='ordinary_point_orbit':
   inds=feature['members'];assert len(inds)==len(set(inds)) and all(isinstance(j,int) and 0<=j<len(captured) for j in inds);value=sum(captured[j] for j in inds);cap=len(inds)
  else:
   assert kind in ['floor','majority_hull'];k=feature['threshold'];assert isinstance(k,int) and k>0
   for mi,inds in enumerate(feature['sets']):
    assert len(inds)==len(set(inds)) and all(isinstance(j,int) and 0<=j<len(captured) for j in inds);cap+=len(inds)//k
    if kind=='floor':value+=sum(captured[j] for j in inds)//k
    else:
     assert len(inds)==2*k-1
     key=(fi,mi)
     if key in proof_lookup:
      verify_separator(proof_lookup[key],inds,k,ctx);used.add(key)
     else:value+=1
  assert cap==feature['budget'];upper+=weight*value;budget+=weight*cap
  table.append({'feature':fi,'column':feature['column'],'upper_capture':value,'weight_units':weight,'upper_charge_units':weight*value})
 assert used==set(proof_lookup) and budget==packet['budget_units']
 return upper,budget,table

def produce(source,poses,destination):
 import numpy as np
 start=time.time();raw=source.read_bytes();packet=json.loads(raw);pose=json.loads(poses.read_text())['witnesses'][0];ctx=setup(packet,pose)
 f,L,B,half,C,S,x,y,points,captured=ctx
 midpoint=float((f.lo+f.hi)/2)
 def fl(z):
  out=0.
  for a in z.p.all_coeffs():out=out*midpoint+float(a)
  return out
 P=np.array([(fl(px),fl(py)) for px,py in points]);center=np.array([fl(x),fl(y)]);uv=np.array([[fl(C),fl(S)],[-fl(S),fl(C)]]);hf=fl(half);proofs=[]
 for fi,feature in enumerate(packet['features']):
  if feature['kind']!='majority_hull':continue
  k=feature['threshold']
  for mi,inds in enumerate(feature['sets']):
   if sum(captured[j] for j in inds)>=k:continue
   coords=P[inds];directions=[('axis_u',None,uv[0]),('axis_v',None,uv[1])]
   for a in range(len(inds)):
    for b in range(a):
     dx,dy=coords[b]-coords[a];directions.append(('site_pair',[inds[a],inds[b]],np.array([-dy,dx])))
   done=False
   for kind,pair,n in directions:
    scale=np.max(abs(n))
    if scale<1e-15:continue
    n=n/scale;projection=(coords-center)@n;radius=hf*(abs(n@uv[0])+abs(n@uv[1]));order=np.argsort(projection)
    for side,selected in [(1,order[-k:]),(-1,order[:k])]:
     if min(side*projection[selected]-radius)<1e-12:continue
     proof={'member_key':[fi,mi],'normal_kind':kind,'side':side,'separated_subset':[inds[int(z)] for z in selected]}
     if pair is not None:proof['normal_pair']=pair
     try:verify_separator(proof,inds,k,ctx)
     except AssertionError:continue
     proofs.append(proof);done=True;break
    if done:break
  if fi%20==0:print(json.dumps({'feature':fi,'separators':len(proofs),'elapsed':time.time()-start}),flush=True)
 upper,budget,table=compute_upper(packet,proofs,ctx);threshold=packet['threshold_units_on_numerical_training_rows']
 assert upper<threshold and 11*upper<budget
 witness={'status':'PASS_EXACT_DEFICIENT_ENDPOINT_CORE_UPPER_BOUND','scope':'One individually contained endpoint core refutes this frozen charge vector. This is not a packing and not a new bound.','proposal_sha256':hashlib.sha256(raw).hexdigest(),'pose_source_sha256':hashlib.sha256(poses.read_bytes()).hexdigest(),'proposal_source_json':raw.decode(),'pose':{k:pose[k] for k in ['half_angle','normalized_x','normalized_y']},'center_coefficients':[x.coefficients(),y.coefficients()],'side_coefficients':B.coefficients(),'separation_proofs':proofs,'feature_upper_bounds':table,'charge_upper_bound_units':upper,'threshold_units':threshold,'budget_units':budget,'threshold_deficit_units':threshold-upper,'budget_minus_eleven_upper_units':budget-11*upper,'field_sign_tests':f.sign_count,'elapsed_seconds':time.time()-start,'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 destination.write_text(json.dumps(witness,indent=2)+'\n');print(json.dumps({k:v for k,v in witness.items() if k not in ['proposal_source_json','separation_proofs','feature_upper_bounds','center_coefficients','side_coefficients']},indent=2))

def replay(path):
 start=time.time();w=json.loads(path.read_text());raw=w['proposal_source_json'].encode();assert hashlib.sha256(raw).hexdigest()==w['proposal_sha256'];packet=json.loads(raw);ctx=setup(packet,w['pose']);upper,budget,table=compute_upper(packet,w['separation_proofs'],ctx)
 assert upper==w['charge_upper_bound_units'] and budget==w['budget_units'] and table==w['feature_upper_bounds']
 threshold=packet['threshold_units_on_numerical_training_rows'];assert upper<threshold and 11*upper<budget
 assert [ctx[6].coefficients(),ctx[7].coefficients()]==w['center_coefficients'] and ctx[2].coefficients()==w['side_coefficients']
 print(json.dumps({'status':'PASS_FRESH_REPLAY_OF_SAVED_EXACT_UPPER_WITNESS','charge_upper_bound_units':upper,'threshold_units':threshold,'budget_units':budget,'separators':len(w['separation_proofs']),'elapsed_seconds':time.time()-start,'field_sign_tests':ctx[0].sign_count},indent=2))

if __name__=='__main__':
 if not __debug__:raise SystemExit('Refuse -O: assertions are verification gates')
 p=argparse.ArgumentParser();p.add_argument('--verify',type=Path);p.add_argument('--proposal',type=Path);p.add_argument('--poses',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
 if a.verify:replay(a.verify)
 else:produce(a.proposal,a.poses,a.output)
