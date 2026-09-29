#!/usr/bin/env python3
"""Independent exact arithmetic replay of rectangular local-isolation proposals."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,hashlib,time
if not __debug__:raise SystemExit('Exact source dependencies require assertions.')
D=Path(__file__).resolve().parent;R=D.parent
CLASS=R/'recovered-checkpoint/research/classical';SOURCE=R/'recovered-checkpoint/research/jlevy/packing'
sys.path[:0]=[str(SOURCE),str(SOURCE/'src')]
from cases.trump11 import isolation_radius as ir
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
P=R/'candidate-capture/anisotropic-local-radii.json';OLD=CLASS/'trump-local-weighted-coordinate-radius.json';FRESH=R/'local-radius/fresh-weighted-coordinate-radius.json'
p=json.load(open(P));old=json.load(open(OLD));fresh=json.load(open(FRESH));start=time.time()
if p['input_sha256']!=sha(OLD) or fresh['proposal_sha256']!=sha(OLD):raise ValueError('Old coordinate-proof binding mismatch')
if fresh['status']!='PASS_INDEPENDENT_WEIGHTED_COORDINATE_RADIUS_AUDIT':raise ValueError('Missing prior independent audit')
for path,h in fresh['source_hashes'].items():
 if sha(SOURCE/path)!=h:raise ValueError('Exact algebra source drift')
lo,hi=map(F,fresh['root_interval']);q=F(old['sqrt2_upper']);iq=F(old['inverse_sqrt2_upper']);box=F(old['box_radius']);den=old['coefficient_denominator']
if q*q<=2 or 2*iq*iq<=1:raise ValueError('Bad radical bounds')
w=ir.load_witness();fn={v.subject:v for v in ir.elementary_functions(w,box)}
cache={}
def interval(value):
 key=tuple(value.coeffs)
 if key not in cache:
  a=b=F(0)
  for coefficient in reversed(key):
   v=(a*lo,a*hi,b*lo,b*hi);a,b=min(v)+coefficient,max(v)+coefficient
  cache[key]=(a,b)
 return cache[key]
oldbranches={r['branch']:r for r in old['branches']}
oldgaps={tuple(r['feature'])+(r['negative_corner'],):r for r in old['unavailable_feature_proofs']}
if len(oldbranches)!=128 or len(oldgaps)!=88:raise ValueError('Incomplete old inventory')
results=[];totalcert=totalgaps=0
for proposed in p['results']:
 a=F(proposed['angle_to_center_radius_ratio']);radius=F(proposed['center_radius'])
 if not 0<a<=1 or not 0<radius<=box or F(proposed['angle_radius'])!=a*radius:raise ValueError('Wrong rectangular chart')
 branches={r['branch']:r for r in proposed['branch_certificates']}
 if len(branches)!=128 or set(branches)!=set(oldbranches):raise ValueError('Incomplete branch inventory')
 caps=[]
 for index,branch in branches.items():
  prior=oldbranches[index];curv=[]
  for oldK in map(F,prior['row_curvature_upper']):
   if oldK==iq:curv.append(iq*a*a)
   else:
    reach=oldK-6*q
    if reach<=0:raise ValueError('Invalid pair reach')
    curv.append(reach*a*a+4*q*a+4*iq*a*a)
  coefficients={(r['coordinate'],r['sign']):r for r in prior['certificates']}
  certs={(r['coordinate'],r['sign']):r for r in branch['certificates']}
  if len(certs)!=66 or set(certs)!={(j,sgn) for j in range(33) for sgn in [-1,1]}:raise ValueError('Incomplete coordinate inventory')
  for key,r in certs.items():
   original=coefficients[key];weights=original['coefficients'];epsilon=F(original['residual_upper']);shape=a if key[0]%3==2 else F(1)
   if len(weights)!=len(curv) or any(v<0 for v in weights) or not shape>epsilon:raise ValueError('Invalid coordinate-dual data')
   mass=sum(F(v,den)*K for v,K in zip(weights,curv));cap=2*(shape-epsilon)/mass
   if mass!=F(r['curvature_mass']) or cap!=F(r['radius_cap']) or not radius<cap:raise ValueError('Bad coordinate radius arithmetic')
   caps.append(cap);totalcert+=1
 if min(caps)!=F(proposed['coordinate_dual_radius_cap']):raise ValueError('Wrong minimum cap')
 gaps={tuple(r['subject']):r for r in proposed['unavailable_feature_checks']}
 if len(gaps)!=88 or set(gaps)!=set(oldgaps):raise ValueError('Incomplete feature inventory')
 margin=None
 for subject,r in gaps.items():
  f=fn[subject];gap=F(r['negative_gap_lower']);G=F(r['weighted_gradient_upper']);K=F(r['directional_curvature_upper'])
  if f.kind!='pair' or gap!=F(oldgaps[subject]['negative_gap_lower']):raise ValueError('Gap premise mismatch')
  if interval(f.value)[1]>-gap:raise ValueError('Uncertified negative feature gap')
  actualG=sum(max(abs(x) for x in interval(v))*(a if j%3==2 else 1) for j,v in enumerate(f.gradient))
  if actualG>G:raise ValueError('Gradient underestimate')
  reach=f.curvature-6*q
  # Check the inferred reach independently against squared center distance.
  i,j=subject[:2];dx=w.centres[i][0]-w.centres[j][0];dy=w.centres[i][1]-w.centres[j][1];distance=reach-2*q*box
  if distance<=0 or distance*distance<interval(dx*dx+dy*dy)[1]:raise ValueError('Pair reach underestimate')
  expectedK=reach*a*a+4*q*a+4*iq*a*a
  if K!=expectedK:raise ValueError('Wrong directional pair curvature')
  remainder=gap-G*radius-K*radius*radius/2
  if remainder<=0:raise ValueError('Feature not stable throughout rectangle')
  margin=remainder if margin is None else min(margin,remainder);totalgaps+=1
 results.append({'angle_to_center_radius_ratio':str(a),'center_radius':str(radius),'angle_radius':str(a*radius),'coordinate_checks':len(caps),'feature_checks':len(gaps),'minimum_stability_margin':str(margin)})
if len(results)!=6 or {r['angle_to_center_radius_ratio'] for r in results}!={'1','1/2','1/4','1/8','1/16','1/32'}:raise ValueError('Unexpected result inventory')
out={'status':'PASS_INDEPENDENT_RECTANGULAR_LOCAL_RADIUS_ARITHMETIC','proposal_sha256':sha(P),'prior_coordinate_packet_sha256':sha(OLD),'prior_independent_replay_sha256':sha(FRESH),'checker_sha256':sha(Path(__file__)),'coordinate_certificates_checked':totalcert,'feature_stability_checks':totalgaps,'results':results,'source_hashes':fresh['source_hashes'],'seconds':time.time()-start,'scope':'Local labelled anchored chart only. Independently checks all new rational masses/caps and radius inequalities, gradient bounds on a separately refined interval, and every negative-feature remainder. Relies on freshly audited old coordinate vectors and the analytically reviewed anisotropic Hessian formula. No global capture or optimality.'}
(D/'anisotropic-local-radii-independent-replay.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['source_hashes','results']},indent=2))
for r in results:print({k:v for k,v in r.items() if k!='minimum_stability_margin'})
