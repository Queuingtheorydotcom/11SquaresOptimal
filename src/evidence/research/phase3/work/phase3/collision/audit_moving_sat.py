"""Independent moving-square collision audit using polynomial axis vectors.

For an axis tied to theta_i, the partner support is minimized at its angular
interval endpoints or at alignment. On each side of alignment its two absolute
dot products have fixed signs. We construct their polynomials directly from
axis-vector coefficients, rather than use the producer's trig coefficients.
"""
from pathlib import Path
import importlib.util,json,random,time,hashlib,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hull'))
from rational import F
import arrangement_audit_v2 as geo
ROOT=Path(__file__).resolve().parents[3]
AXES=(((F(1),F(0)),(F(0),F(2)),(F(-1),F(0))),
      ((F(0),F(1)),(F(-2),F(0)),(F(0),F(-1))))
def dot(a,b):return a[0]*b[0]+a[1]*b[1]
def nonnegative(c,a,b):
    c0,c1,c2=c
    if min(c0+c1*a+c2*a*a,c0+c1*b+c2*b*b)<0:return False
    if c2>0 and c1+2*c2*a<0<c1+2*c2*b:return 4*c0*c2-c1*c1>=0
    return True
def axis_family(d,I,J,b):
    lo,hi=I
    for partner in J:
        c,s=geo.cs(partner);directions=((c,s),(-s,c))
        endpoints=sorted({lo,hi}|({partner} if lo<partner<hi else set()))
        pieces=list(zip(endpoints,endpoints[1:])) if lo<hi else [(lo,hi)]
        for left,right in pieces:
            mid=(left+right)/2
            for axis in AXES:
                polynomials=[tuple(dot(v,n) for v in axis) for n in directions]
                signs=[]
                for q in polynomials:
                    value=q[0]+q[1]*mid+q[2]*mid*mid;signs.append((value>0)-(value<0))
                for sign in (-1,1):
                    slack=[b/2*(int(k!=1)+sum(s*q[k] for s,q in zip(signs,polynomials)))-sign*dot(axis[k],d) for k in range(3)]
                    if not nonnegative(slack,left,right):return False
    left,right=max(I[0],J[0]),min(I[1],J[1])
    if left<=right:
        for axis in AXES:
            for sign in (-1,1):
                slack=[b*int(k!=1)-sign*dot(axis[k],d) for k in range(3)]
                if not nonnegative(slack,left,right):return False
    return True
def universal_overlap(d,I,J,b):
    d=tuple(map(F,d));I=tuple(map(F,I));J=tuple(map(F,J));b=F(b)
    assert b>0 and 0<=I[0]<=I[1]<=1 and 0<=J[0]<=J[1]<=1
    return axis_family(d,I,J,b) and axis_family((-d[0],-d[1]),J,I,b)
def square(t,b):
    c,s=geo.cs(t)
    return [(b*(c*x-s*y)/2,b*(s*x+c*y)/2) for x,y in ((-1,-1),(1,-1),(1,1),(-1,1))]
def fixed_overlap(d,ti,tj,b):
    M=geo.gift_hull([(p[0]-q[0],p[1]-q[1]) for p in square(tj,b) for q in square(ti,b)])
    return all(x*d[0]+y*d[1]<=h for x,y,h in geo.polygon_rows(M))
def main():
    path=ROOT/'work/phase3/capture/moving_sat.py';h=hashlib.sha256(path.read_bytes()).hexdigest()
    spec=importlib.util.spec_from_file_location('moving_sat_producer',path);producer=importlib.util.module_from_spec(spec);spec.loader.exec_module(producer)
    rng=random.Random(91271);start=time.monotonic();fixed=intervals=vertices=0
    for _ in range(800):
        ti,tj=F(rng.randrange(65),64),F(rng.randrange(65),64);d=tuple(F(rng.randrange(-200,201),100) for _ in range(2))
        assert universal_overlap(d,(ti,ti),(tj,tj),F(1))==fixed_overlap(d,ti,tj,F(1));fixed+=1
    for _ in range(500):
        I=tuple(sorted((F(rng.randrange(65),64),F(rng.randrange(65),64))))
        J=tuple(sorted((F(rng.randrange(65),64),F(rng.randrange(65),64))))
        d=tuple(F(rng.randrange(-150,151),100) for _ in range(2))
        assert universal_overlap(d,I,J,F(1))==producer.universal_overlap(d,I,J,F(1));intervals+=1
    U=F(387708359002281417731,10**20);B=geo.L/U;b=B-F(1,10**12)
    for I,J in (((F(0),F(1)),(F(0),F(1))),((F(23,64),F(24,64)),(F(0),F(1,64))),((F(0),F(1,496)),(F(363,1000),F(368,1000)))):
        r=producer.relative_core(I,J,b);assert 0<F(r['strict_side'])<B
        for p in r['vertices']:assert universal_overlap(p,I,J,b);vertices+=1
    for epsilon,want in ((F(0),True),(F(1,10**50),False),(-F(1,10**50),True)):
        assert universal_overlap((F(1)+epsilon,F(0)),(F(0),F(0)),(F(0),F(0)),F(1))==want
    assert h==hashlib.sha256(path.read_bytes()).hexdigest(),'Producer changed during audit'
    out=dict(status='PASS_INDEPENDENT_MOVING_SAT_AUDIT',fixed_exact_minkowski_comparisons=fixed,full_interval_crosschecks=intervals,
             produced_core_vertices_universally_checked=vertices,boundary_mutation_checks=3,producer_sha256=h,
             checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),seconds=time.monotonic()-start,
             scope='Universal collision predicate and proposed inner cores only; no owner pose-cover antecedent or mask exclusion is proved.')
    Path(__file__).with_name('moving-sat-independent-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
