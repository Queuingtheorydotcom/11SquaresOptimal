"""Generate exact D4 contact-site orbits at the Trump endpoint.

Contacts repair one necessary obstruction to an endpoint certificate. They do
not give universal coverage or an optimality proof.
"""
import sys,json,time,hashlib
from fractions import Fraction
from pathlib import Path
import sympy as sp
import numpy as np
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/construction'))
from verify_trump import E,u,configuration
from exact_trump_rows import FieldSigns

def key(p):return tuple(tuple(str(z.p.nth(k)) for k in range(8)) for z in p)
def coeff(p):return [[str(z.p.nth(k)) for k in range(8)] for z in p]
def main():
 start=time.time();sgn=FieldSigns();squares,alpha,_=configuration(E(u));L=E(sp.Rational(191,50));B=L/alpha;vertices=[[(B*x,B*y) for x,y in sq] for sq in squares]
 edges=[]
 for sq in vertices:
  edges.append([])
  for j in range(4):
   p,q=sq[j],sq[(j+1)%4];nx,ny=-(q[1]-p[1]),q[0]-p[0];edges[-1].append((nx,ny,-nx*p[0]-ny*p[1]))
 def captures(point,open=False):
  out=[]
  for es in edges:
   signs=[sgn.sign([int(z.p.nth(k)*d) for k in range(8)]) for z in [a*point[0]+b*point[1]+c for a,b,c in es] for d in [sp.ilcm(*[z.p.nth(k).q for k in range(8)])]]
   out.append(int(min(signs)>0 if open else min(signs)>=0))
  return out
 contacts={}
 for sq in vertices:
  for p in sq:
   row=captures(p)
   if sum(row)>=2:contacts[key(p)]=(p,row)
 seen=set();orbits=[];closed=[];opened=[]
 for ky,(p,source_row) in sorted(contacts.items()):
  if ky in seen:continue
  orbit={key((a,b)):(a,b) for x,y in [p,p[::-1]] for a in [x,L-x] for b in [y,L-y]}
  seen.update(orbit);ps=[orbit[k] for k in sorted(orbit)];c=np.array([captures(v) for v in ps],int).sum(axis=0);o=np.array([captures(v,True) for v in ps],int).sum(axis=0)
  orbits.append({'representative_coefficients':coeff(p),'size':len(ps),'members_coefficients':[coeff(v) for v in ps],'closed_trump_counts':c.tolist(),'open_trump_counts':o.tolist(),'closed_total':int(c.sum()),'endpoint_budget':len(ps),'closed_budget_excess':int(c.sum())-len(ps)})
  closed.append(c);opened.append(o)
 closed=np.array(closed).T;opened=np.array(opened).T;budgets=np.array([o['size'] for o in orbits]);assert np.all(opened.sum(axis=0)<=budgets)
 old=np.load(Path(__file__).with_name('exact-trump-endpoint-rows.npz'));C=np.column_stack([old['closed'],closed]);budget=np.r_[old['budget'],budgets]
 with threadpool_limits(limits=1):r=linprog(budget,A_ub=-C.astype(float),b_ub=-np.ones(11),bounds=(0,None),method='highs')
 assert r.success
 rw=[Fraction(float(w)).limit_denominator(1000) for w in r.x]
 assert all(sum(Fraction(int(a))*w for a,w in zip(row,rw))>=1 for row in C)
 exact_budget=sum(Fraction(int(b))*w for b,w in zip(budget,rw));assert exact_budget==Fraction(26,3)
 family=json.loads((ROOT/'research/stromquist/candidate-true-enriched-round6.json').read_text());D=family['coordinate_denominator'];LD=int(sp.Rational(family['L'])*D)
 weighted_sites=[]
 for j,w in enumerate(rw):
  if not w:continue
  if j<4716:
   assert j<len(family['point_orbits'])
   x,y,_=family['point_orbits'][j];pts=sorted({(a,b) for p,q in [(x,y),(y,x)] for a in [p,LD-p] for b in [q,LD-q]})
   weighted_sites.extend((E(sp.Rational(a,D)),E(sp.Rational(b,D)),w) for a,b in pts)
  else:
   weighted_sites.extend((E(sum(sp.Rational(a)*u**k for k,a in enumerate(p[0]))),E(sum(sp.Rational(a)*u**k for k,a in enumerate(p[1]))),w) for p in orbits[j-4716]['members_coefficients'])
 def signE(z):
  den=sp.ilcm(*[z.p.nth(k).q for k in range(8)])
  return sgn.sign([int(z.p.nth(k)*den) for k in range(8)])
 central=sum(w for x,y,w in weighted_sites if min(signE(B/2+x-L/2),signE(B/2-x+L/2),signE(B/2+y-L/2),signE(B/2-y+L/2))>=0)
 out={'status':'EXACT_ENDPOINT_CONTACT_SITE_ORBITS_WITH_FINITE_LP_DIAGNOSTIC','scope':'Contact points and eleven-template rows are exact; the LP covers only those eleven templates, not arbitrary poses. No bound proved.','contact_vertex_sites_before_D4':len(contacts),'orbits':orbits,'positive_excess_orbits':[j for j,o in enumerate(orbits) if o['closed_budget_excess']>0],'finite_eleven_template_lp_budget':r.fun,'exact_eleven_template_budget':str(exact_budget),'exact_positive_weights':[{'column':j,'weight':str(w)} for j,w in enumerate(rw) if w],'exact_centered_axis_square_charge':str(central),'central_pose_refutes_universal_coverage':central<1,'finite_lp_positive_columns':[{'column':int(j),'weight':float(r.x[j]),'budget':int(budget[j])} for j in np.flatnonzero(r.x>1e-10)],'elapsed_seconds':time.time()-start}
 dest=Path(__file__).parent;(dest/'endpoint-contact-sites.json').write_text(json.dumps(out,indent=2)+'\n');np.savez_compressed(dest/'endpoint-contact-sites.npz',closed=closed,opened=opened,budget=budgets,finite_lp_weights=r.x)
 print(json.dumps({k:v for k,v in out.items() if k!='orbits'},indent=2))
if __name__=='__main__':main()
