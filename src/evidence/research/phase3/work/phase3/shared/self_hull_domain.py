"""Necessary center strips from containment of a square's OWN proved hull.

All owned points must already be proved strictly inside this parent. We use
closed necessary inequalities. B is the actual parent side, never a strict
inner-core side. Complete orientation intervals use t=tan(theta/2) in[0,1].
"""
from gmpy2 import mpq as F
from functools import lru_cache
from collision_kernel import clip,polygon,dot
if not __debug__:raise RuntimeError('Assertions must remain enabled')
def cs(t):return (1-t*t)/(1+t*t),2*t/(1+t*t)
@lru_cache(maxsize=100000)
def envelope(lo,hi,B):
 lo,hi,B=F(lo),F(hi),F(B);assert 0<=lo<=hi<=1 and B>0
 t=(lo+hi)/2;c,s=cs(t);relations=[]
 for a in (lo,hi):
  ca,sa=cs(a);relations.append(dict(dot=c*ca+s*sa,cross=c*sa-s*ca))
 # The reference lies between endpoints. If endpoint |delta|<=pi/4,
 # cos(delta)+|sin(delta)| increases with |delta| throughout each side.
 narrow=all(r['dot']>=abs(r['cross']) for r in relations)
 M=max(r['dot']+abs(r['cross']) for r in relations) if narrow else F(3,2)
 return dict(reference_half_angle=t,axes=((c,s),(-s,c)),endpoint_relations=relations,
             support_factor=M,projection_extent=B*M/2,
             support_bound_method='EXACT_ENDPOINT_MAXIMUM' if narrow else 'RATIONAL_GLOBAL_3_OVER_2')
def necessary_cuts(owned,lo,hi,B):
 K=polygon(owned);assert K,'Owned hull premise must be nonempty'
 info=dict(envelope(F(lo),F(hi),F(B)));E=info['projection_extent'];cuts=[]
 for n in info['axes']:
  pp=[dot(n,p) for p in K]
  cuts.append(dict(normal=n,upper=min(pp)+E))
  cuts.append(dict(normal=(-n[0],-n[1]),upper=-max(pp)+E))
 info['cuts']=cuts;return info

def restrict(domain,owned,lo,hi,B):
 info=necessary_cuts(owned,lo,hi,B);p=list(polygon(domain))
 for h in info['cuts']:p=clip(p,h['normal'],h['upper'])
 return dict(info,domain=p)

def controls():
 K=[(-F(2,5),-F(2,5)),(F(2,5),-F(2,5)),(F(2,5),F(2,5)),(-F(2,5),F(2,5))]
 domain=[(-F(2),-F(2)),(F(2),-F(2)),(F(2),F(2)),(-F(2),F(2))]
 for t in (F(0),F(1)):
  r=restrict(domain,K,t,t,F(1));assert set(r['domain'])=={(-F(1,10),-F(1,10)),(F(1,10),-F(1,10)),(F(1,10),F(1,10)),(-F(1,10),F(1,10))}
 assert restrict([(F(1,10),F(0))],K,F(0),F(0),F(1))['domain']
 assert not restrict([(F(1,10)+F(1,10**40),F(0))],K,F(0),F(0),F(1))['domain']
 assert envelope(F(0),F(1),F(1))['support_bound_method']=='RATIONAL_GLOBAL_3_OVER_2'
 for k in range(64):
  e=envelope(F(k,64),F(k+1,64),F(1));assert e['support_bound_method']=='EXACT_ENDPOINT_MAXIMUM'
  for m in range(9):
   t=F(k,64)+F(m,512);a,b=cs(t);c,s=e['axes'][0];assert c*a+s*b+abs(c*b-s*a)<=e['support_factor']
 return dict(status='PASS_SELF_HULL_CONTROLS',exact_boundary_controls=5,sampled_envelope_checks=576)
if __name__=='__main__':
 import json
 print(json.dumps(controls()))
