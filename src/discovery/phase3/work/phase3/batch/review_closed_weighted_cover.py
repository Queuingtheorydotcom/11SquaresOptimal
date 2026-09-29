"""Exact direct-charge oracle for the new closed point/segment wrapper."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,random,sys,time
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'audit'))
import independent_closed_weighted_cover as c
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=sha(c.__file__);rng=random.Random(271126);records=[];started=time.monotonic()
def region(P,Q,lo,hi,off=False):
 dx,dy=Q[0]-P[0],Q[1]-P[1];D=dx*dx+dy*dy;b=dx*P[0]+dy*P[1]
 rows=[(dx,dy,b+D*hi),(-dx,-dy,-b-D*lo)]
 if off:
  nx,ny=-dy,dx;rows.append((nx,ny,nx*P[0]+ny*P[1]-F(1,10**50)))
 return rows
for case in range(120):
 P=(F(rng.randrange(-5,6),3),F(rng.randrange(-5,6),7))
 dx,dy=rng.randrange(-4,5),rng.randrange(-4,5)
 if not dx and not dy:dy=1
 Q=(P[0]+dx,P[1]+dy);spec=[];atoms=[];breaks={F(0),F(1)}
 for j in range(rng.randrange(1,7)):
  intervals=[];regions=[]
  for k in range(rng.randrange(1,5)):
   lo,hi=F(rng.randrange(-2,8),5),F(rng.randrange(-2,8),5)
   if rng.randrange(3):lo,hi=min(lo,hi),max(lo,hi)
   if rng.randrange(8)==0:hi=lo
   if rng.randrange(7)==0:lo+=F(1,10**50)
   off=rng.randrange(15)==0
   intervals.append((lo,hi,off));regions.append(region(P,Q,lo,hi,off))
   breaks.update(t for t in [lo,hi] if 0<=t<=1)
  if rng.randrange(2):intervals.append(intervals[0]);regions.append(regions[0])
  w=rng.randrange(6);spec.append((intervals,w));atoms.append(('test',regions,w))
 gamma=rng.randrange(14)
 def charge(t):return sum(w for intervals,w in spec if any(not off and lo<=t<=hi for lo,hi,off in intervals))
 cuts=sorted(breaks);samples=cuts+[(a+b)/2 for a,b in zip(cuts,cuts[1:])]
 expected=min(map(charge,samples))>=gamma
 actual=c.closed_weighted_cover([P,Q],atoms,gamma)
 assert actual['passed']==expected,(case,actual)
 for t in [F(0),F(1,2),F(1)]:
  pt=(P[0]+t*dx,P[1]+t*dy);r=c.closed_weighted_cover([pt,pt],atoms,gamma)
  assert r['passed']==(charge(t)>=gamma),(case,t,r,charge(t))
 records.append(dict(case=case,passed=actual['passed'],oracle_samples=len(samples),point_checks=3))
existing=c.controls();assert before==sha(c.__file__),'helper changed during review'
out=dict(status='PASS_CLOSED_WEIGHTED_COVER_SOURCE_REVIEW',checker_sha256=before,reviewer_sha256=sha(__file__),weighted_checker_sha256=sha(c.weighted.__file__),existing_controls=existing,segment_cases=len(records),point_cases=3*len(records),segment_covers=sum(r['passed']for r in records),segment_noncovers=sum(not r['passed']for r in records),seconds=time.monotonic()-started,scope='Source review plus independent direct-charge oracle for exact points and slanted/vertical/horizontal closed segments. Includes duplicate unions, zero weights, reversed or isolated intervals, off-line regions, and 10^-50 offsets. Positive-area domains delegate to the previously reviewed frozen weighted checker. This is not a standalone packing exclusion.',findings=['Correct sign handling for parameter bounds.','Per-atom interval merge prevents duplicate charge.','Endpoint charge includes both ending and starting closed intervals; the following open interval removes endings.','Degenerate points and empty domains are handled explicitly; thresholds and weights are validated.'],cases=records)
(HERE/'closed-weighted-cover-source-review.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items()if k not in ['cases','findings','scope']}))
