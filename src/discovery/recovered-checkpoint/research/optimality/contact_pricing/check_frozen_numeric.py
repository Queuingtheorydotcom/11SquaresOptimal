"""Independent floating round-trip of the standalone proposal; not exact geometry."""
from pathlib import Path
import json,time,math,hashlib
from fractions import Fraction
import numpy as np
P=Path(__file__).parent/'frozen';packet=json.loads((P/'endpoint-contact-proposal.json').read_text());witnesses=json.loads((P/'known-adversarial-poses.json').read_text())['witnesses'][:5];t=.365769307604677293388545018143311315;L=3.82;alpha=(6*t+4)/(1+2*t-t*t);B=L/alpha
points=np.array([[sum(float(Fraction(a))*t**k for k,a in enumerate(xy)) for xy in p['coordinates_coefficients']] for p in packet['sites']]);features=packet['features'];budget=sum(f['budget']*f['weight_units'] for f in features);assert budget==packet['budget_units'];out=[]
for witness in witnesses:
 theta,x,y=witness['float_original_pose'];c=math.cos(theta);s=math.sin(theta);center=np.array([x,y]);dx=points-center;U=points@np.array([c,s]);V=points@np.array([-s,c]);inside=(abs(dx@np.array([c,s]))<=B/2)&(abs(dx@np.array([-s,c]))<=B/2);total=0
 for f in features:
  if f['kind']=='ordinary_point_orbit':count=int(inside[f['members']].sum())
  else:
   count=0;k=f['threshold']
   for inds in f['sets']:
    captured=int(inside[inds].sum())
    if f['kind']=='floor':count+=captured//k;continue
    if f['kind']=='threshold':count+=int(captured>=k);continue
    if captured>=k:count+=1;continue
    if abs(c*x+s*y-np.median(U[inds]))>B/2 or abs(-s*x+c*y-np.median(V[inds]))>B/2:continue
    ps=points[inds];good=True
    for i in range(len(ps)):
     for j in range(i):
      d=ps[i]-ps[j];n=np.array([d[1],-d[0]]);radius=B/2*(abs(n@np.array([c,s]))+abs(n@np.array([-s,c])))
      if abs(n@center-np.median(ps@n))>radius:good=False;break
     if not good:break
    count+=int(good)
  total+=count*f['weight_units']
 assert total==witness['numerical_charge_units'],(total,witness['numerical_charge_units'])
 out.append(total)
report={'status':'PASS_INDEPENDENT_FLOATING_EXPORT_ROUNDTRIP','scope':'Five known deficient poses only. Does not certify any exact algebraic geometry.','proposal_sha256':hashlib.sha256((P/'endpoint-contact-proposal.json').read_bytes()).hexdigest(),'budget_units':budget,'charges_units':out,'threshold_units':packet['threshold_units_on_numerical_training_rows']};(P/'roundtrip-numeric.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
