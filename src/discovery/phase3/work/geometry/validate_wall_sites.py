"""Exact universal wall-aware ownership with rational interval envelopes.
No float result or pose sampling participates in acceptance.
"""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,argparse,time,os
if not __debug__:
    raise SystemExit('Exact verifier requires assertions; do not use python -O.')
ROOT=Path(os.environ.get('ELEVEN_PACKING_ROOT', str(Path(__file__).resolve().parents[2]/'current')))
COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
EXPECTED_COVER='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
U=F(387708359002281417731,10**20);L=F(191,50);B=L/U

def trig(t):return (1-t*t)/(1+t*t),2*t/(1+t*t)
def clip(poly,axis,bound,greater):
 out=[]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  a=p[axis]-bound;b=q[axis]-bound
  ina=a>=0 if greater else a<=0;inb=b>=0 if greater else b<=0
  if ina:out.append(p)
  if ina!=inb:
   r=a/(a-b);out.append(tuple(p[j]+r*(q[j]-p[j]) for j in range(2)))
 clean=[]
 for p in out:
  if not clean or p!=clean[-1]:clean.append(p)
 if len(clean)>1 and clean[0]==clean[-1]:clean.pop()
 return clean

def envelope(poly,a,b):
 h=min(sum(trig(a)),sum(trig(b)))/2
 for axis in (0,1):
  poly=clip(poly,axis,h,True);poly=clip(poly,axis,U-h,False)
 return poly

def trig_strict(A,D,a,b):
 ca,sa=trig(a);cb,sb=trig(b)
 fa=A*ca+D*sa;fb=A*cb+D*sb
 if max(fa*fa,fb*fb)>=F(1,4):return False
 # On 0<=theta<=pi/2 each nonzero derivative has at most one zero.
 # Interior critical |f| equals sqrt(A^2+D^2); endpoints already checked.
 da=D*ca-A*sa;db=D*cb-A*sb
 if da*db<0 and A*A+D*D>=F(1,4):return False
 return True

def interval_ok(point,poly,a,b):
 world=envelope(poly,a,b)
 for q in world:
  dx,dy=point[0]-q[0],point[1]-q[1]
  if not trig_strict(dx,dy,a,b) or not trig_strict(dy,-dx,a,b):return False
 return True

def validate(point,poly,max_depth=20,bins=16):
 accepted=[];pending=[(F(i,bins),F(i+1,bins),0) for i in reversed(range(bins))];checks=0
 while pending:
  a,b,d=pending.pop();checks+=1
  if interval_ok(point,poly,a,b):accepted.append((a,b))
  elif d>=max_depth:return dict(status='UNRESOLVED',failed_interval=[a,b],checks=checks)
  else:
   m=(a+b)/2;pending.extend([(m,b,d+1),(a,m,d+1)])
 assert accepted[0][0]==0 and accepted[-1][1]==1
 assert all(p[1]==q[0] for p,q in zip(accepted,accepted[1:]))
 return dict(status='PASS_EXACT_WALL_OWNERSHIP',partition=accepted,checks=checks)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 assert hashlib.sha256(COVER.read_bytes()).hexdigest()==EXPECTED_COVER
 cover=json.loads(COVER.read_text());inp=json.loads(args.input.read_text());records=[]
 for r in inp['sites']:
  j=r['owner'];point=tuple(map(F,r['unit_point']));assert len(point)==2 and 0<=j<16
  poly=[tuple(F(1,2)+(U-1)*F(x) for x in p) for p in cover['cells'][j]['vertices']]
  result=validate(point,poly)
  rr=dict(owner=j,unit_point=point,field_point=[B*x for x in point],maximum_vertex_distance_squared=max(sum((x-y)**2 for x,y in zip(point,v)) for v in poly),**result)
  print(j,result['status'],'checks',result['checks'],flush=True);records.append(rr)
 out=dict(status='PASS_EXACT_WALL_OWNED_SITES' if all(r['status'].startswith('PASS') for r in records) else 'INCOMPLETE',cover_sha256=EXPECTED_COVER,checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),U=U,parent_side=B,records=records,global_optimality_proved=False,continuum_masks_excluded=0)
 args.output.write_text(json.dumps(out,indent=2,default=str))
if __name__=='__main__':main()
