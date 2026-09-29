#!/usr/bin/env python3
"""Independent center-cover audit by all boundary-line intersections.

Does not import the proposed polygon clipper or trust its reported vertices.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import hashlib, json, math

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'global_capture/center-cover-exact.json'

def require(x, message):
    if not x: raise ValueError(message)

def dot(p,q): return p[0]*q[0]+p[1]*q[1]
def sub(p,q): return (p[0]-q[0],p[1]-q[1])
def cross(p,q): return p[0]*q[1]-p[1]*q[0]
def norm2(p): return dot(p,p)

def hull(points):
    ps=sorted(set(points))
    def half(ps):
        result=[]
        for p in ps:
            while len(result)>1 and cross(sub(result[-1],result[-2]),sub(p,result[-1]))<=0:
                result.pop()
            result.append(p)
        return result
    return half(ps)[:-1]+half(ps[::-1])[:-1]

def audit(source=SOURCE):
    data=json.loads(source.read_text())
    centers=[tuple(map(F,c['center'])) for c in data['cells']]
    require(len(set(centers))==16,'sixteen distinct centers')
    S=F(data['side_upper']); R=F(data['unit_square_cover_radius_bound'])
    area=F(0); largest=F(0); counts=[]
    for i,p in enumerate(centers):
        inequalities=[((F(-1),F(0)),F(0)),((F(1),F(0)),F(1)),
                      ((F(0),F(-1)),F(0)),((F(0),F(1)),F(1))]
        inequalities += [((2*(q[0]-p[0]),2*(q[1]-p[1])),norm2(q)-norm2(p))
                         for j,q in enumerate(centers) if j!=i]
        vertices=set()
        for (a,b),(c,d) in combinations(inequalities,2):
            det=cross(a,c)
            if not det: continue
            v=((b*c[1]-a[1]*d)/det,(a[0]*d-b*c[0])/det)
            if all(dot(x,v)<=y for x,y in inequalities): vertices.add(v)
        reported={tuple(map(F,v)) for v in data['cells'][i]['vertices']}
        require(vertices==reported, f'cell {i} vertex mismatch')
        poly=hull(vertices)
        a=sum(cross(v,w) for v,w in zip(poly,poly[1:]+poly[:1]))
        require(a==F(data['cells'][i]['twice_area']) and a>0, 'area mismatch')
        area+=a
        radius=max(norm2(sub(v,p)) for v in poly)
        diameter=max(norm2(sub(v,w)) for v,w in combinations(poly,2))
        require(radius<=R*R, 'radius bound fails')
        physical=diameter*(S-1)**2
        require(physical<1, 'strict physical diameter bound fails')
        require(physical==F(data['cells'][i]['physical_diameter_squared']), 'diameter mismatch')
        largest=max(largest,physical); counts.append(len(poly))
    require(area==2,'partition area fails')
    masks=list(combinations(range(16),11))
    require([list(x) for x in masks]==data['all_eleven_cell_subsets'],'mask enumeration differs')
    require(len(masks)==4368 and len(set(masks))==4368,'mask count fails')
    # Ordinary 4x4 midpoint cells have physical diagonal greater than one.
    require((S-1)**2/F(8)>1, 'grid negative control unexpectedly passes')
    result={'status':'PASS_INDEPENDENT_EXACT_CENTER_COVER_AUDIT',
            'method':'All feasible pairwise boundary intersections, then monotone-chain convex hull; no proposed clipping routine imported.',
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'cells':16,'vertex_counts':counts,'twice_total_area':str(area),
            'maximum_physical_diameter_squared':str(largest),
            'maximum_physical_diameter_approximate':math.sqrt(float(largest)),
            'eleven_cell_masks':len(masks),'negative_controls':1,
            'scope':'Exact necessary reduction for S<=3.877084; neither infeasibility nor optimality follows.'}
    return result

def main():
    result=audit()
    (HERE/'center-cover-independent-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
