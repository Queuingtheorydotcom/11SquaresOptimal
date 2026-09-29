#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,random,sys,time
from rational import F
import rational
import own_hull_constraints as check
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shared'))
import self_hull_domain as producer
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def satisfies(z,cuts):return all(sum(x*y for x,y in zip(r['normal'],z))<=r['upper'] for r in cuts)
def main():
 start=time.monotonic();B=F(1);K=[(-F(2,5),-F(2,5)),(F(2,5),-F(2,5)),(F(2,5),F(2,5)),(-F(2,5),F(2,5))]
 intervals=[(F(k,64),F(k+1,64)) for k in range(64)]+[(F(0),F(1)),(F(0),F(1,2)),(F(1,2),F(1)),(F(0),F(0)),(F(1),F(1))]
 for a,b in intervals:
  cuts=producer.necessary_cuts(K,a,b,B)['cuts'];check.validate_cuts(K,a,b,B,cuts)
  bad=[dict(r) for r in cuts];bad[0]=dict(bad[0],upper=bad[0]['upper']-F(1,10**50))
  try:check.validate_cuts(K,a,b,B,bad)
  except AssertionError:pass
  else:raise AssertionError('Incorrect cut accepted')
 cuts=check.necessary_cuts(K,F(0),F(0),B)
 assert satisfies((F(1,10),F(0)),cuts)
 assert not satisfies((F(1,10)+F(1,10**50),F(0)),cuts)
 assert check.support_bound_valid((F(1),F(0)),F(1,2),F(0),F(0),B)
 assert not check.support_bound_valid((F(1),F(0)),F(1,2)-F(1,10**50),F(0),F(0),B)
 rng=random.Random(12478)
 for _ in range(200):
  a,b=sorted([F(rng.randrange(129),128),F(rng.randrange(129),128)])
  theta=a+(b-a)*F(rng.randrange(65),64);c,s=check.cs(theta);z=(F(rng.randrange(-100,100),50),F(rng.randrange(-100,100),50))
  inside=[(z[0]+F(9,20)*(u*c-v*s),z[1]+F(9,20)*(u*s+v*c)) for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  cuts=check.necessary_cuts(inside,a,b,B);assert satisfies(z,cuts)
 out=dict(status='PASS_INDEPENDENT_OWN_HULL_CUTS',checker_sha256=sha(check.__file__),producer_sha256=sha(producer.__file__),
          interval_envelopes_verified_by_complete_quadratics=len(intervals),mutated_cut_rejections=len(intervals),
          analytic_boundary_controls=4,feasible_parent_controls=200,seconds=time.monotonic()-start,
          scope='Necessary center-domain restriction from an already independently proved owned hull; no new packing exclusion.')
 Path(__file__).with_name('own-hull-constraints-independent-controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
