"""Universal collision kernel using exact-validated moving square cores.

This is an optional strengthening. Complete prior center/angle cover premises
are supplied externally. Positive results contain every supporting relative
core needed for an independent replay; early empty results supply no exclusion.
"""
from pathlib import Path
import sys
import moving_sat_fast as proposal
import moving_sat as exact
F=exact.F;geo=exact.geo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shared'))
from collision_kernel import clip,normals,support,polygon,dot

class MovingPartnerCover:
 def __init__(self,rows,b):
  self.rows=[dict(interval=tuple(map(F,r['interval'])),domain=polygon(r['domain']),reference=r.get('reference'),core=polygon(r.get('core',[]))) for r in rows if r['domain']]
  self.b=F(b)
 def kernel(self,I,query_domain,query_core=None):
  I=tuple(map(F,I));p=list(polygon(query_domain));used=[]
  if not self.rows:return dict(vertices=p,status='EMPTY_PARTNER_COVER',relative_cores=[])
  qi=polygon(exact.square(I[0],self.b))
  # Necessary fixed-endpoint collision strips cheaply reject distant partners.
  for row in self.rows:
   qj=polygon(exact.square(row['interval'][0],self.b));D=row['domain']
   for n in set(normals(qi)+normals(qj)):
    h=support(qi,n)+support(qj,n)+min(dot(n,c) for c in D)
    p=clip(p,n,h)
    if not p:return dict(vertices=[],status='EMPTY_NECESSARY_MOVING_COLLISION_REGION',relative_cores=[])
  for row in self.rows:
   core=proposal.relative_core(I,row['interval'],self.b);R=polygon(core['vertices']);D=row['domain']
   if query_core and row['core']:
    old=geo.hull([(x-u,y-v) for x,y in row['core'] for u,v in query_core])
    accepted=[q for q in old if exact.universal_overlap(q,I,row['interval'],self.b)]
    R=polygon(geo.hull(list(R)+accepted))
   used.append(dict(interval=row['interval'],reference=row['reference'],vertices=R))
   for n in normals(R):
    h=support(R,n)+min(dot(n,c) for c in D);p=clip(p,n,h)
    if not p:return dict(vertices=[],status='EMPTY_INNER_MOVING_COLLISION_REGION',relative_cores=used)
  return dict(vertices=p,status='INNER_UNIVERSAL_MOVING_COLLISION_REGION',relative_cores=used,strict_side=self.b,query_interval=I)
