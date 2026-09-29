#!/usr/bin/env python3
"""Independent rectangle inclusion and exact coordinate-dual isolation replay.

The source state is a conditional geometric premise, to be proved separately.
No source capture or whole-mask conclusion is inferred by this checker.
"""
from pathlib import Path
from fractions import Fraction as F
from math import isqrt
import sys,json,hashlib,time,argparse
if not __debug__:raise SystemExit('Assertions must remain enabled in imported algebra.')
D=Path(__file__).resolve().parent;R=D.parent
CLASS=R/'recovered-checkpoint/research/classical';SOURCE=R/'recovered-checkpoint/research/jlevy/packing'
sys.path[:0]=[str(SOURCE),str(SOURCE/'src')]
from cases.trump11 import isolation_radius as ir
from cases.trump11 import tangent_cones as tc
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(b,s):
 if not b:raise ValueError(s)
def rounded_upper(x,N=10**10):return F(-((-x.numerator*N)//x.denominator),N)
def sqrt_upper(x,N=10**15):
 need(x>=0,'Negative square')
 n=(x.numerator*N*N+x.denominator-1)//x.denominator;k=isqrt(n)
 if k*k<n:k+=1
 return F(k,N)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('proposal',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();start=time.monotonic()
 p=json.loads(a.proposal.read_text());source=Path(p['source']);d=json.loads(source.read_text());s=d['final_state']
 need(sha(source)==p['source_sha256'],'Changed pose source')
 oldpath=CLASS/'trump-local-weighted-coordinate-radius.json';old=json.loads(oldpath.read_text())
 freshpath=R/'local-radius/fresh-weighted-coordinate-radius.json';fresh=json.loads(freshpath.read_text())
 need(fresh['status']=='PASS_INDEPENDENT_WEIGHTED_COORDINATE_RADIUS_AUDIT' and fresh['proposal_sha256']==sha(oldpath),'Missing audited coordinate-dual premise')
 for path,h in fresh['source_hashes'].items():need(sha(SOURCE/path)==h,'Algebra source drift')
 lo,hi=map(F,fresh['root_interval']);q=F(old['sqrt2_upper']);iq=F(old['inverse_sqrt2_upper']);box=F(old['box_radius']);den=old['coefficient_denominator']
 need(q*q>2 and 2*iq*iq>1,'Radical bound failed')
 w=ir.load_witness();cache={}
 def interval(v):
  key=tuple(v.coeffs)
  if key not in cache:
   aa=bb=F(0)
   for c in reversed(key):
    t=(aa*lo,aa*hi,bb*lo,bb*hi);aa,bb=min(t)+c,max(t)+c
   cache[key]=(aa,bb)
  return cache[key]
 U=F(s['U']);B=F(s['B']);need(U==F(387708359002281417731,10**20) and U*B==F(191,50),'Wrong field frame')
 guards_path=R/'phase3/current/research/optimality/global_capture/local-capture-guards.json';guards=json.loads(guards_path.read_text())
 guard=next(g for g in guards['guards'] if g['mask']==s['mask'])
 need(s['mask']==[0,1,2,3,4,8,9,10,11,13,15] and d['mask_index']==438,'Only mask438 chart is established here')
 need(guard['symmetry']=={'swap':True,'reflect_x':True,'reflect_y':False},'Expected quarter-turn chart')
 roles=guard['roles'];need(sorted(r['label'] for r in roles)==list(range(11)) and sorted(r['cell'] for r in roles)==s['mask'],'Nonbijective role assignment')
 need(guard['label_to_cell']==[next(r['cell'] for r in roles if r['label']==i) for i in range(11)],'Role mismatch')
 need(set(s['cells'])==set(map(str,s['mask'])),'Missing source owner')
 radii=list(map(lambda x:rounded_upper(F(x)),p['radius_by_coordinate']))
 need(len(radii)==33 and all(0<r<=box for r in radii),'Invalid rectangular chart')
 alpha=w.field.alpha;one=w.field.one
 ca=(one-alpha*alpha)/(one+alpha*alpha);sa=2*alpha/(one+alpha*alpha)
 inclusion=[];pose_rows=0;vertices=0
 for role in roles:
  i=role['label'];owner=role['cell'];rows=s['cells'][str(owner)];live=[r for r in rows if r['residual_polygons']]
  need(live,'Empty source owner does not need a local theorem')
  # The quarter-turn chart preserves angles modulo pi/2. Verify witness axes.
  e=(w.squares[i][1][0]-w.squares[i][0][0],w.squares[i][1][1]-w.squares[i][0][1])
  target=(one,w.field.zero) if i<6 else (ca,sa)
  need(all((v-z).is_zero() for v,z in zip(e,target)),'Witness square orientation mismatch')
  center_bounds=[interval(w.centres[i][k]-w.side/2) for k in (0,1)]
  required=[F(0)]*3
  for row in live:
   aa,bb=map(F,row['interval']);need(0<=aa<=bb<=1,'Invalid half-angle row')
   if i<6:
    need(bb<=F(1,2) or aa>=F(1,2),'Axis chart straddles remote angles')
    if bb<=F(1,2):angle_bound=2*bb
    else:angle_bound=2*(1-aa)/(1+aa)
   else:
    need(bb<F(2,3),'Slanted chart crosses artificial quarter-turn cut')
    angle_bound=2*max(abs(aa-hi),abs(bb-lo))/(1+min(aa,lo)**2)
   required[2]=max(required[2],angle_bound)
   for P in row['residual_polygons']:
    need(P,'Empty residual polygon')
    for x,y in P:
     # Invert transformed centered point (-Y,X) directly.
     original=(F(y)/B-U/2,U/2-F(x)/B)
     for k in (0,1):required[k]=max(required[k],abs(original[k]-center_bounds[k][0]),abs(original[k]-center_bounds[k][1]))
     vertices+=1
   pose_rows+=1
  need(all(required[k]<=radii[3*i+k] for k in range(3)),'Pose domain exceeds proposed rounded rectangle')
  inclusion.append({'label':i,'owner':owner,'radii':list(map(str,radii[3*i:3*i+3])),'pose_rows':len(live)})
 functions=ir.elementary_functions(w,box);tied={};by_subject={f.subject:f for f in functions};reach_cache={}
 def curvature(f):
  if f.kind=='wall':return iq*radii[3*f.subject[0]+2]**2
  i,j,owner=f.subject[:3];other=j if owner==i else i
  pair=(i,j)
  if pair not in reach_cache:
   reach=f.curvature-6*q
   d0=reach-2*q*box;dx=w.centres[i][0]-w.centres[j][0];dy=w.centres[i][1]-w.centres[j][1]
   need(d0>0 and d0*d0>=interval(dx*dx+dy*dy)[1],'Pair center reach is not certified')
   reach_cache[pair]=reach
  dx=radii[3*i]+radii[3*j];dy=radii[3*i+1]+radii[3*j+1];wo=radii[3*owner+2];wp=radii[3*other+2]
  return reach_cache[pair]*wo*wo+2*sqrt_upper(dx*dx+dy*dy)*wo+iq*(wo+wp)**2
 for f in functions:
  if f.value.is_zero():
   key=tuple(tuple(v.coeffs) for v in f.gradient);tied[key]=max(tied.get(key,F(0)),curvature(f))
 branch_ids=set();worst=F(0);worst_record=None;coordinate_count=0;maxradius=max(radii)
 for branch in old['branches']:
  index=branch['branch'];need(index not in branch_ids,'Duplicate branch');branch_ids.add(index);rows=w.branches[index]['rows']
  K=[tied[tuple(tuple(v.coeffs) for v in row.coefficients)] for row in rows]
  seen=set()
  for cert in branch['certificates']:
   j,sign=cert['coordinate'],cert['sign'];need((j,sign) not in seen,'Duplicate coordinate');seen.add((j,sign))
   coeffs=cert['coefficients'];need(len(coeffs)==len(K) and all(type(x)is int and x>=0 for x in coeffs),'Bad nonnegative dual')
   mass=sum(F(v,den)*kk for v,kk in zip(coeffs,K));margin=radii[j]-F(cert['residual_upper'])*maxradius
   need(margin>0 and mass<2*margin,'Rectangle dual inequality fails')
   ratio=mass/(2*margin)
   if ratio>worst:worst=ratio;worst_record={'branch':index,'coordinate':j,'sign':sign}
   coordinate_count+=1
  need(seen=={(j,sgn) for j in range(33) for sgn in (-1,1)},'Incomplete signed-coordinate inventory')
 need(branch_ids==set(range(128)) and coordinate_count==8448,'Incomplete branch inventory')
 contact_pairs={c.pair for c in w.contacts};feature_groups={}
 for f in functions:
  if f.kind=='pair' and f.subject[:2] in contact_pairs:feature_groups.setdefault(f.subject[:5],[]).append(f)
 impossible={key for key,fs in feature_groups.items() if any(interval(f.value)[1]<0 for f in fs)}
 need(impossible=={tuple(v['feature']) for v in old['unavailable_feature_proofs']} and len(impossible)==88,'Incomplete actual unavailable-feature inventory')
 gaps=[];seen=set()
 for record in old['unavailable_feature_proofs']:
  subject=tuple(record['feature'])+(record['negative_corner'],);need(subject not in seen,'Duplicate unavailable feature');seen.add(subject);f=by_subject[subject]
  gap=F(record['negative_gap_lower']);need(gap>0 and interval(f.value)[1]<=-gap,'Unavailable feature gap not certified')
  linear=sum(max(abs(z) for z in interval(v))*radii[j] for j,v in enumerate(f.gradient));K=curvature(f);margin=gap-linear-K/2
  need(margin>0,'Unavailable feature can activate in rectangle')
  gaps.append({'subject':list(subject),'strict_gap_after_Taylor':str(margin)})
 need(len(gaps)==88,'Incomplete unavailable-feature inventory')
 out={'status':'PASS_INDEPENDENT_FOCUSED_RECTANGLE_LOCAL_ISOLATION','checker_sha256':sha(__file__),'proposal':str(a.proposal.resolve()),'proposal_sha256':sha(a.proposal),'source':str(source.resolve()),'source_sha256':sha(source),'final_state_sha256':hashlib.sha256(json.dumps(s,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'prior_coordinate_packet_sha256':sha(oldpath),'prior_independent_replay_sha256':sha(freshpath),'guard_assignment_source_sha256':sha(guards_path),'radius_rounding_denominator':10**10,'radii':list(map(str,radii)),'inverse_chart':'(x_field,y_field) -> (y_field/B-U/2, U/2-x_field/B); angles modulo pi/2','inclusion':inclusion,'pose_rows_checked':pose_rows,'vertices_checked':vertices,'coordinate_certificates_checked':coordinate_count,'unavailable_features_checked':len(gaps),'worst_dual_ratio':str(worst),'worst_coordinate':worst_record,'feature_stability':gaps,'source_hashes':fresh['source_hashes'],'conditional_on_source_pose_domains':True,'local_rectangle_isolation_proved':True,'source_capture_proved':False,'global_optimality_proved':False,'scope':'At the exact Trump side or smaller, the rectangle contains only the exact labelled Trump packing in the fixed centered chart. Every point of the supplied final pose domains lies in this rectangle, conditional on those domains being independently established. The source ancestry and its branch assumptions are not audited here.','seconds':time.monotonic()-start}
 a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['status','checker_sha256','source_sha256','pose_rows_checked','vertices_checked','coordinate_certificates_checked','unavailable_features_checked','worst_coordinate','seconds']}));print('worst ratio',float(worst))
if __name__=='__main__':main()
