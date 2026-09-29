#!/usr/bin/env python3
"""Extend the frozen weighted cover checker to closed points and segments.

Positive-area domains use the separately reviewed convex subtraction proof.
A segment is parametrized on [0,1]. Every convex region yields one exact closed
parameter interval. Intervals are united within each atom before a weighted
endpoint sweep, so overlapping pieces of an atom are never counted twice.
"""
from fractions import Fraction as F
from collections import defaultdict
import hashlib,json
from pathlib import Path
import independent_weighted_cover as weighted

def exact(x):
    if isinstance(x,float):raise TypeError('Floating coordinates forbidden')
    if hasattr(x,'numerator') and hasattr(x,'denominator'):
        return F(int(x.numerator),int(x.denominator))
    return F(x)
def parameter_interval(P,Q,rows):
    lo,hi=F(0),F(1)
    for a,b,h in rows:
        a,b,h=map(exact,(a,b,h));s=a*(Q[0]-P[0])+b*(Q[1]-P[1]);r=h-a*P[0]-b*P[1]
        if not s:
            if r<0:return None
        elif s>0:hi=min(hi,r/s)
        else:lo=max(lo,r/s)
        if lo>hi:return None
    return lo,hi
def merge(intervals):
    out=[]
    for lo,hi in sorted(intervals):
        if out and lo<=out[-1][1]:out[-1]=(out[-1][0],max(hi,out[-1][1]))
        else:out.append((lo,hi))
    return out
def closed_weighted_cover(domain,atoms,threshold,max_pieces=200000):
    weighted.need(type(threshold)is int and threshold>=0,'Invalid threshold')
    atoms=list(atoms)
    for _,_,w in atoms:weighted.need(type(w)is int and w>=0,'Invalid weight')
    pts=sorted(set(tuple(map(exact,p)) for p in domain))
    if not pts:return dict(passed=True,status='PASS_EMPTY_DOMAIN',dimension=-1)
    if len(pts)==1:
        p=pts[0];charge=sum(w for _,regions,w in atoms if any(all(exact(a)*p[0]+exact(b)*p[1]<=exact(h) for a,b,h in rows) for rows in regions))
        return dict(passed=charge>=threshold,status='PASS_POINT_CHARGE' if charge>=threshold else 'UNCOVERED_POINT',dimension=0,charge=charge)
    hull=weighted.convex_hull(pts)
    if weighted.area2(hull)>0:return dict(dimension=2,**weighted.weighted_cover(hull,atoms,threshold,max_pieces))
    P,Q=pts[0],pts[-1]
    weighted.need(all((Q[0]-P[0])*(p[1]-P[1])==(Q[1]-P[1])*(p[0]-P[0]) for p in pts),'Noncollinear degenerate domain')
    starts=defaultdict(int);ends=defaultdict(int)
    for _,regions,w in atoms:
        intervals=[I for rows in regions if (I:=parameter_interval(P,Q,rows)) is not None]
        for lo,hi in merge(intervals):starts[lo]+=w;ends[hi]+=w
    events=sorted(set(starts)|set(ends)|{F(0),F(1)});active=0;minimum=None
    for k,t in enumerate(events):
        charge=active+starts[t];minimum=charge if minimum is None else min(minimum,charge)
        if charge<threshold:return dict(passed=False,status='UNCOVERED_SEGMENT_POINT',dimension=1,parameter=str(t),charge=charge)
        active+=starts[t]-ends[t]
        if k+1<len(events):
            minimum=min(minimum,active)
            if active<threshold:return dict(passed=False,status='UNCOVERED_SEGMENT_INTERVAL',dimension=1,interval=[str(t),str(events[k+1])],charge=active)
    return dict(passed=True,status='PASS_CLOSED_WEIGHTED_SEGMENT',dimension=1,events=len(events),minimum_charge=minimum)
def controls():
    seg=[(0,0),(1,0)];box=lambda lo,hi:[(1,0,hi),(-1,0,-lo)]
    assert closed_weighted_cover([],[],9)['passed']
    assert closed_weighted_cover([(0,0)],[('x',[box(0,0)],2)],2)['passed']
    assert not closed_weighted_cover([(0,0)],[('x',[box(0,0),box(0,0)],1)],2)['passed']
    assert closed_weighted_cover(seg,[('x',[box(0,F(1,2)),box(F(1,2),1)],3)],3)['passed']
    assert not closed_weighted_cover(seg,[('x',[box(0,F(1,2)),box(F(1,2)+F(1,10**50),1)],3)],3)['passed']
    assert not closed_weighted_cover(seg,[('x',[box(0,1),box(0,1)],1)],2)['passed']
    assert closed_weighted_cover(seg,[('x',[box(0,1)],1),('y',[box(0,1)],1)],2)['passed']
    assert not closed_weighted_cover(seg,[('x',[box(F(1,10**50),1)],2)],2)['passed']
    assert not closed_weighted_cover(seg,[('x',[box(0,1-F(1,10**50))],2)],2)['passed']
    assert closed_weighted_cover([(0,0),(0,1)],[('x',[[(0,1,1),(0,-1,0)]],1)],1)['passed']
    assert not closed_weighted_cover(seg,[('x',[[(0,0,-1)]],3)],1)['passed']
    return dict(status='PASS_CLOSED_WEIGHTED_COVER_CONTROLS',checks=11)
if __name__=='__main__':
    r=controls();r.update(checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),weighted_checker_sha256=hashlib.sha256(Path(weighted.__file__).read_bytes()).hexdigest())
    Path(__file__).with_name('closed-weighted-cover-controls.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))
