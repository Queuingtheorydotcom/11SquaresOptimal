#!/usr/bin/env python3
"""Exact, standard-library certificate for a 16-cell capacity-one center cover.

This certifies only a necessary finite reduction, not square-packing infeasibility.
Numerical search is not imported. All coordinates and comparisons are rational.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import hashlib,json,math

CENTERS=[(105103,132829),(373241,46499),(633483,138703),(865533,102741),
 (103618,399843),(371544,313340),(634935,416808),(890400,335003),
 (108644,663951),(364421,584763),(629233,687474),(897437,599085),
 (134410,897133),(366240,861191),(626837,955493),(895121,866992)]
DEN=10**6
SIDE_UPPER=F(969271,250000) # 3.877084
RADIUS=F(169475,10**6)

def require(ok,message):
    if not ok: raise ValueError(message)

def dot(x,y): return sum(a*b for a,b in zip(x,y))
def norm2(x): return dot(x,x)
def diff(x,y): return tuple(a-b for a,b in zip(x,y))
def cross(a,b): return a[0]*b[1]-a[1]*b[0]

def clip(poly,a,b):
    """Intersect closed convex polygon with a.x <= b by exact line clipping."""
    answer=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        fp=dot(a,p)-b; fq=dot(a,q)-b
        if fp<=0: answer.append(p)
        if (fp<0<fq) or (fq<0<fp):
            t=fp/(fp-fq)
            answer.append(tuple(p[k]+t*(q[k]-p[k]) for k in range(2)))
    dedup=[]
    for p in answer:
        if not dedup or p!=dedup[-1]: dedup.append(p)
    if len(dedup)>1 and dedup[0]==dedup[-1]: dedup.pop()
    return dedup

def polygon_for(centers,i):
    p=centers[i]
    poly=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
    for j,q in enumerate(centers):
        if i!=j: poly=clip(poly,tuple(2*d for d in diff(q,p)),norm2(q)-norm2(p))
    return poly

def area2(poly): return sum(cross(p,q) for p,q in zip(poly,poly[1:]+poly[:1]))

def verify(centers=None, radius=RADIUS):
    centers=centers or [tuple(F(v,DEN) for v in p) for p in CENTERS]
    require(len(centers)==16 and len(set(centers))==16,'sixteen distinct centers required')
    polys=[polygon_for(centers,i) for i in range(16)]
    rows=[]
    for i,poly in enumerate(polys):
        require(len(poly)>=3 and area2(poly)>0,'empty or invalid cell')
        for v in poly:
            require(all(0<=x<=1 for x in v),'cell vertex outside domain')
            d=norm2(diff(v,centers[i]))
            require(d<=radius*radius,'rational radius bound failed')
            require(all(d<=norm2(diff(v,c)) for c in centers),'nearest-center inequality failed')
        maximum=max(norm2(diff(v,centers[i])) for v in poly)
        diameter=max(norm2(diff(v,w)) for v,w in combinations(poly,2))
        require(diameter*(SIDE_UPPER-1)**2<1,'capacity-one diameter not strict')
        rows.append({'index':i,'center':[str(v) for v in centers[i]],'vertices':[[str(v) for v in p] for p in poly],'twice_area':str(area2(poly)),'maximum_radius_squared':str(maximum),'maximum_diameter_squared':str(diameter),'physical_diameter_squared':str(diameter*(SIDE_UPPER-1)**2)})
    require(sum(area2(p) for p in polys)==2,'cell areas do not sum to unit area')
    require(4*radius**2*(SIDE_UPPER-1)**2<1,'common radius diameter bound not strict')
    return {'status':'PASS_EXACT_16_CELL_CENTER_COVER','global_optimality_proved':False,'new_lower_bound_proved':False,'scope':'All independently rotated unit-square packings in [0,S]^2 for S<=3.877084','side_upper':str(SIDE_UPPER),'unit_square_cover_radius_bound':str(radius),'common_physical_diameter_bound':str(2*radius*(SIDE_UPPER-1)),'maximum_physical_diameter_squared':str(max(F(row['physical_diameter_squared']) for row in rows)),'centers_denominator':math.lcm(*(v.denominator for p in centers for v in p)),'number_of_cells':16,'eleven_cell_selections':math.comb(16,11),'previous_twenty_cell_selections':math.comb(20,11),'selection_reduction_factor':str(F(math.comb(20,11),math.comb(16,11))),'boundary_assignment':'Assign a point tied between nearest centers to the least index. Closure cells are used for all geometric checks.','cover_argument':f'Every point has a nearest center. Its Voronoi inequalities place it in at least one enumerated closed cell. Each cell has radius at most {radius} about its listed center.','capacity_argument':'Map [0,1]^2 to [1/2,S_upper-1/2]^2. Each cell has diameter<1. Two unit-square centers at distance<1 have intersecting open radius1/2 inscribed disks.','cells':rows,'all_eleven_cell_subsets':[list(v) for v in combinations(range(16),11)]}

def controls():
    count=0
    bad=[tuple(F(v,DEN) for v in p) for p in CENTERS]
    bad[0]=(F(1,2),F(1,2))
    try: verify(bad)
    except ValueError: count+=1
    else: raise ValueError('bad-radius mutation accepted')
    bad=[tuple(F(v,DEN) for v in p) for p in CENTERS]
    bad[0]=bad[1]
    try: verify(bad)
    except ValueError: count+=1
    else: raise ValueError('duplicate mutation accepted')
    # The familiar 4x4 rectangular grid is an explicit rejected control.
    bad=[(F(2*i+1,8),F(2*j+1,8)) for j in range(4) for i in range(4)]
    try: verify(bad)
    except ValueError: count+=1
    else: raise ValueError('4x4 grid incorrectly accepted at requested radius')
    return count

if __name__=='__main__':
    out=verify();out['rejected_mutations']=controls();out['verifier_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    Path(__file__).with_name('center-cover-exact.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('cells','all_eleven_cell_subsets')},indent=2))
