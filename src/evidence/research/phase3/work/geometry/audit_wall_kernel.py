#!/usr/bin/env python3
"""Independent rational interval proof of wall-aware owned points.

No producer geometry, stationary-point routine, or numerical arithmetic is used.
For t in [a,b] subset [0,1], c(t) decreases and s(t) increases. We clip the
center cell to the legal-wall outer envelope at min(h(a),h(b)), then enclose
each of the two body-coordinate projections by ordinary interval arithmetic.
Strict bounds at every vertex extend over the clipped convex polygon.
"""
from fractions import Fraction as F
from pathlib import Path
import json, os

if not __debug__:
    raise RuntimeError('Run with Python assertions enabled; -O is unsupported')
ROOT = Path(os.environ.get('ELEVEN_PACKING_ROOT',
            str(Path(__file__).resolve().parents[2] / 'current'))).resolve()
COVER = ROOT / 'research/optimality/global_capture/center-cover-symmetric-exact.json'
U = F(387708359002281417731, 10**20)
B = F(191,50) / U

def read_cells():
    data = json.loads(COVER.read_text())
    assert U <= F(data['side_upper'])
    return [[tuple(F(1,2)+(U-1)*F(x) for x in p) for p in cell['vertices']]
            for cell in data['cells']]

def cs(t):
    return (1-t*t)/(1+t*t), 2*t/(1+t*t)

def clip(poly, axis, bound, upper):
    if not poly:
        return []
    out=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        dp=p[axis]-bound; dq=q[axis]-bound
        ip=(dp<=0 if upper else dp>=0)
        iq=(dq<=0 if upper else dq>=0)
        if ip:
            out.append(p)
        if ip != iq:
            lam=dp/(dp-dq)
            out.append(tuple(p[k]+lam*(q[k]-p[k]) for k in range(2)))
    return out

def projection_interval(A, D, cl, ch, sl, sh):
    ac=(A*cl,A*ch)
    ds=(D*sl,D*sh)
    return min(ac)+min(ds), max(ac)+max(ds)

def check_point(poly, point, max_depth=20):
    stack=[(F(0),F(1),0)]
    leaves=0; empty=0; margin=F(1,2); deepest=0
    while stack:
        a,b,depth=stack.pop()
        ca,sa=cs(a); cb,sb=cs(b)
        # c+s has one interior maximum, hence the endpoint minimum is safe.
        h=min(ca+sa,cb+sb)/2
        outer=poly
        for axis in (0,1):
            outer=clip(outer,axis,h,False)
            outer=clip(outer,axis,U-h,True)
        if not outer:
            leaves+=1; empty+=1; deepest=max(deepest,depth)
            continue
        local=F(1,2)
        for x,y in outer:
            dx=point[0]-x; dy=point[1]-y
            for A,D in ((dx,dy),(dy,-dx)):
                lo,hi=projection_interval(A,D,cb,ca,sa,sb)
                local=min(local,F(1,2)-max(-lo,hi))
        if local>0:
            leaves+=1; margin=min(margin,local); deepest=max(deepest,depth)
        elif depth < max_depth:
            mid=(a+b)/2
            stack.append((mid,b,depth+1)); stack.append((a,mid,depth+1))
        else:
            return dict(passed=False,unresolved_interval=[str(a),str(b)],
                        depth=depth,accepted_leaves=leaves)
    return dict(passed=True,leaves=leaves,empty_leaves=empty,max_depth=deepest,
                strict_projection_margin=str(margin))

if __name__=='__main__':
    import argparse, hashlib
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path,help='JSON list of {owner, unit_point} records')
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--witness',type=Path,help='Optional exact-gate parent refuter to check')
    args=ap.parse_args()
    cells=read_cells(); records=json.loads(args.input.read_text()); results=[]
    if isinstance(records,dict):
        records=records['sites']
    witness=None
    if args.witness:
        source=json.loads(args.witness.read_text())
        row=[r for r in source['records'] if 'parent_witness' in r][-1]
        pose=row['parent_witness']
        assert F(source['parent_Uplus'])==U and F(pose['side'])==B
        q=tuple(map(F,pose['center'])); ct,st=cs(F(pose['half_angle']))
        halfwidth=B*(ct+st)/2
        assert all(halfwidth<=x<=F(191,50)-halfwidth for x in q)
        unitq=tuple(x/B for x in q)
        poly=cells[row['cell']]
        signs=[(v[0]-u[0])*(unitq[1]-u[1])-(v[1]-u[1])*(unitq[0]-u[0])
               for u,v in zip(poly,poly[1:]+poly[:1])]
        assert all(s>=0 for s in signs) or all(s<=0 for s in signs)
        witness=dict(source_sha256=hashlib.sha256(args.witness.read_bytes()).hexdigest(),
                     cell=row['cell'],half_angle=pose['half_angle'],
                     legal_parent_containment=True,legal_closed_cell_membership=True,
                     captures=[])
    for rec in records:
        owner=int(rec['owner']); point=tuple(map(F,rec['unit_point']))
        result=check_point(cells[owner],point)
        maxdist=max(sum((point[k]-v[k])**2 for k in range(2)) for v in cells[owner])
        results.append(dict(owner=owner,unit_point=[str(x) for x in point],
                            maximum_vertex_distance_squared=str(maxdist),
                            outside_disk_kernel=maxdist>F(1,4),**result))
        if witness is not None:
            dx,dy=(B*point[k]-q[k] for k in range(2))
            projection=max(abs(ct*dx+st*dy),abs(-st*dx+ct*dy))
            active=owner in source['mask'] and owner!=row['cell']
            witness['captures'].append(dict(owner=owner,other_occupied_owner=active,
                         strict_parent_capture=projection<B/2,
                         parent_capture_margin=str(B/2-projection),
                         reported_core_capture=projection<=F(row['core_side'])/2,
                         reported_core_capture_margin=str(F(row['core_side'])/2-projection)))
        print(owner,result,flush=True)
    passed=all(r['passed'] for r in results)
    if witness is not None:
        witness['conditionally_impossible_parent']=passed and any(
            c['other_occupied_owner'] and c['strict_parent_capture']
            for c in witness['captures'])
    out=dict(status='PASS' if passed else 'INCOMPLETE',
             statement='Each listed point is strictly interior to every unit square with center in its owner cell and contained in the tight rational container.',
             global_optimality_proved=False,new_mask_exclusion_proved=False,
             U=str(U),cover_sha256=hashlib.sha256(COVER.read_bytes()).hexdigest(),
             input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
             checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             witness=witness,results=results)
    args.output.write_text(json.dumps(out,indent=2)+'\n')
    raise SystemExit(0 if passed else 1)
