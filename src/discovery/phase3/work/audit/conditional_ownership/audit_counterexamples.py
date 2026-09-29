"""Independent exact checks of isolated-parent refutation and mask-parent capture."""
from pathlib import Path
from fractions import Fraction as F
from hashlib import sha256
import json
if not __debug__:raise SystemExit('Assertions must remain enabled.')
HERE=Path(__file__).parent
coverp=Path('/workspace/scratch/6def36ddf53b/current/research/optimality/global_capture/center-cover-symmetric-exact.json')
assert sha256(coverp.read_bytes()).hexdigest()=='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
cover=json.loads(coverp.read_text());proof=json.loads((HERE/'mask2045-owner6.json').read_text());unconditioned=json.loads((HERE/'mask2045-owner6-unconditioned.json').read_text());p=tuple(map(F,proof['point']));L=F(191,50);U=F(proof['parent_Uplus']);B=L/U
r=unconditioned['records'][-1];assert r['status']=='REFUTED_BY_LEGAL_PARENT';w=r['parent_witness'];q=tuple(map(F,w['center']));t=F(w['half_angle']);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
radius=B*(c+s)/2;assert all(radius<=x<=L-radius for x in q)
poly=[tuple(L/2+B*(U-1)*(F(x)-F(1,2)) for x in v) for v in cover['cells'][proof['owner']]['vertices']]
turns=[(v[0]-u[0])*(q[1]-u[1])-(v[1]-u[1])*(q[0]-u[0]) for u,v in zip(poly,poly[1:]+poly[:1])];assert all(x>=0 for x in turns) or all(x<=0 for x in turns)
def margin(point):
 dx,dy=[x-y for x,y in zip(point,q)];return B/2-max(abs(c*dx+s*dy),abs(-s*dx+c*dy))
missing=margin(p);assert missing<0
hits=[]
for j in proof['prior_owner_support']:
 for index,point in enumerate(proof['prior_owned_points'][j]):
  m=margin(tuple(map(F,point)))
  if m>0:hits.append(dict(owner=j,index=index,strict_margin=str(m)))
assert hits
out=dict(status='PASS_INDEPENDENT_EXACT_CONDITIONAL_DISTINCTION',owner=proof['owner'],point=proof['point'],isolated_parent_legal=True,isolated_parent_center_in_owner_cell=True,point_outside_parent_margin=str(-missing),therefore_not_unconditionally_owned=True,other_owned_sites_strictly_captured=hits,scope='This exact isolated parent refutes unconditional ownership but is impossible under the occupied-mask ownership premises. This check does not independently prove the conditional all-pose theorem.',source_proof_sha256=sha256((HERE/'mask2045-owner6.json').read_bytes()).hexdigest(),source_counterexample_sha256=sha256((HERE/'mask2045-owner6-unconditioned.json').read_bytes()).hexdigest())
(HERE/'conditional-distinction-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
