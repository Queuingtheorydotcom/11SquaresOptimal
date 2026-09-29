#!/usr/bin/env python3
"""Independent exact contact/overlap controls for the compatibility interval kernel."""
from fractions import Fraction as F
from pathlib import Path
from itertools import product
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'research/optimality/compatibility/kernel.py'
sys.path.insert(0,str(SOURCE.parent))
from kernel import Domain,possible_pair,arc_projection_upper,threshold_lower,cs

def dot(a,b):return a[0]*b[0]+a[1]*b[1]
def axes(t):
    c,s=cs(t);return ((c,s),(-s,c))
def radius(t,a):return sum(abs(dot(v,a)) for v in axes(t))/2

def exact_separated(p,t,q,u):
    delta=(q[0]-p[0],q[1]-p[1])
    return any(abs(dot(delta,a))>=radius(t,a)+radius(u,a) for a in axes(t)+axes(u))

def require(ok,message):
    if not ok:raise ValueError(message)

def run():
    total=0
    # Contact/no-contact distinction at exact eps=10^-18, every rational test angle.
    eps=F(1,10**18)
    for t,u in product([F(i,8) for i in range(9)],repeat=2):
        for a in axes(t)+axes(u):
            r=radius(t,a)+radius(u,a)
            for shift in (-eps,F(0),eps):
                p=(F(0),F(0));q=tuple((r+shift)*x for x in a)
                first=Domain(0,(p,),(t,t));second=Domain(1,(q,),(u,u))
                expected=exact_separated(p,t,q,u)
                actual=possible_pair(first,second)
                require(actual==expected,'exact contact/overlap mismatch')
                total+=1
    # Arc upper bound and support threshold checked against independently sampled
    # rational points; these are controls, not the mathematical proof of bounds.
    arc=threshold=0
    for lo in range(5):
        for hi in range(lo,5):
            iv=(F(lo,4),F(hi,4))
            for a,b in product((F(-3,2),F(-1,3),F(0),F(1,7),F(5,4)),repeat=2):
                bound=arc_projection_upper(a,b,iv)
                for j in range(11):
                    t=iv[0]+(iv[1]-iv[0])*F(j,10);c,s=cs(t)
                    require(a*c+b*s<=bound,'arc upper bound failed');arc+=1
            for lo2 in range(5):
                for hi2 in range(lo2,5):
                    iv2=(F(lo2,4),F(hi2,4));bound=threshold_lower(iv,iv2)
                    for j,k in product(range(3),repeat=2):
                        t=iv[0]+(iv[1]-iv[0])*F(j,2);u=iv2[0]+(iv2[1]-iv2[0])*F(k,2)
                        a=axes(t)[0]
                        exact=2*(radius(t,a)+radius(u,a))
                        require(bound<=exact,'threshold lower bound failed');threshold+=1
    refused=0
    for p in (((0.0,F(0)),),((F(0),F(0)),(F(1),F(1)),(F(0),F(1)),(F(1),F(0)))):
        try:Domain(0,p,(F(0),F(1)))
        except ValueError:refused+=1
        else:raise ValueError('invalid coordinate/polygon accepted')
    return {'status':'PASS_INDEPENDENT_COMPATIBILITY_KERNEL_REVIEW','scope':'Mathematical kernel review and exact controls, not full branch-controller or coverage audit','kernel_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'exact_point_contact_overlap_cases':total,'rational_arc_controls':arc,'rational_threshold_controls':threshold,'invalid_domain_refusals':refused,'new_lower_bound_proved':False,'global_optimality_proved':False,'review_findings':['All decisively excluded domains are computed in rational arithmetic.','Squared center distance and fixed-direction linear extrema over convex polygon pairs occur at vertex pairs.','The signed sinusoid has at most one interior maximum on a quarter-turn arc; derivative endpoint signs identify when its amplitude is needed.','The relative-angle threshold is unimodal in the absolute relative angle, so its interval minimum occurs at one of the absolute-angle endpoints.','All strict pair exclusions preserve exact legal touching.','Domain geometry accepts points and line segments as well as cyclic convex polygons.','The early positive return at squared center distance>=2 is only inconclusive and therefore cannot falsely exclude geometry.','Coverage, physical coordinate conventions, masks, and tree completeness remain separate controller obligations.']}

if __name__=='__main__':
    out=run();Path(__file__).with_name('compatibility-kernel-independent-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
