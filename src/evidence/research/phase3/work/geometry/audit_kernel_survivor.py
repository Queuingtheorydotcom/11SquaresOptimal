#!/usr/bin/env python3
"""Independent complete mandatory-kernel obstruction via exact vertex LP.

Checks each necessary cut against an actual legal owner parent, then proves
the bounded 2D inequality system empty by enumerating intersections of all
pairs of boundary lines. No producer clipping or ownership code is imported.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import argparse, hashlib, json, os
if not __debug__:raise RuntimeError('Assertions must be enabled')
ROOT=Path(os.environ.get('ELEVEN_PACKING_ROOT',str(Path(__file__).resolve().parents[2]/'current'))).resolve()
COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cs(t):return (1-t*t)/(1+t*t),2*t/(1+t*t)
def inside(p,poly):
    s=[(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]) for a,b in zip(poly,poly[1:]+poly[:1])]
    return all(x>=0 for x in s) or all(x<=0 for x in s)
def feasible_vertices(rows):
    count=0;possible=[]
    for (n,a),(m,b) in combinations(rows,2):
        det=n[0]*m[1]-n[1]*m[0]
        if not det:continue
        count+=1;p=((a*m[1]-b*n[1])/det,(n[0]*b-m[0]*a)/det)
        if all(dot(v,p)<=z for v,z in rows):possible.append(p)
    return count,possible
def hull_intersects(A,B):
    normals={(F(1),F(0)),(F(0),F(1))}
    for points in (A,B):
        normals|={(b[1]-a[1],a[0]-b[0]) for a,b in combinations(points,2)}
    for n in normals:
        x=[dot(n,p) for p in A];y=[dot(n,p) for p in B]
        if max(x)<min(y) or max(y)<min(x):return False
    return True
def run(receipt,packet_path):
    d=json.loads(receipt.read_text());cover=json.loads(COVER.read_text());assert d['cover_sha256']==sha(COVER)
    sourcepath=receipt.parent/Path(d['witness_source']).name
    assert sha(sourcepath)==d['witness_source_sha256']
    source=json.loads(sourcepath.read_text());last=[r for r in source['records'] if 'parent_witness' in r][-1]
    assert d['witness']==last['parent_witness'] and d['witness_cell']==last['cell']
    packet=json.loads(packet_path.read_text());assert sha(packet_path)==source['packet_sha256']
    U=F(d['U']);B=F(191,50)/U;assert B==F(d['parent_side'])==F(d['witness']['side'])
    assert U==F(packet['parent_Uplus']) and packet['mask']==source['mask']
    assert source['mask']==cover['canonical_eleven_cell_subsets'][source['mask_index']]
    polys=[[tuple(F(1,2)+(U-1)*F(x) for x in p) for p in cell['vertices']] for cell in cover['cells']]
    pose=d['witness'];q=tuple(F(x)/B for x in pose['center']);t=F(pose['half_angle']);c,s=cs(t)
    assert F(0)<=t<=1 and inside(q,polys[d['witness_cell']])
    assert all((c+s)/2<=x<=U-(c+s)/2 for x in q)
    axes=((c,s),(-c,-s),(-s,c),(s,-c))
    witness_rows=[(n,dot(n,q)+F(1,2)) for n in axes]
    witness_vertices=[(q[0]+a*c/2-b*s/2,q[1]+a*s/2+b*c/2) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
    assert {r['owner'] for r in d['records']}==set(source['mask'])-{d['witness_cell']}
    checks=[]
    for r in d['records']:
        rows=witness_rows[:]
        for cut in r['cuts']:
            tc=F(cut['half_angle']); assert 0<=tc<=1
            cc,ss=cs(tc);p=tuple(map(F,cut['legal_center']));n=tuple(map(F,cut['normal']));b=F(cut['bound'])
            assert inside(p,polys[r['owner']])
            assert all((cc+ss)/2<=x<=U-(cc+ss)/2 for x in p)
            assert n in ((cc,ss),(-cc,-ss),(-ss,cc),(ss,-cc))
            assert b==dot(n,p)+F(1,2)
            rows.append((n,b))
        tried,vertices=feasible_vertices(rows);assert not vertices
        checks.append(dict(owner=r['owner'],legal_parent_cuts=len(r['cuts']),line_intersections_checked=tried,empty=True))
    cert=packet['certificate'];sites=[tuple(F(x,cert['coordinate_denominator'])/B for x in p) for p in cert['sites']]
    charge=sum(w for p,w in zip(sites,cert['point_weights']) if all(dot(n,p)<=b for n,b in witness_rows))
    active=[]
    for i,feat in enumerate(cert['features']):
        assert feat['kind']=='majority_hull' and 2*feat['threshold']>len(feat['indices'])
        yes=all(hull_intersects(witness_vertices,[sites[j] for j in inds]) for inds in combinations(feat['indices'],feat['threshold']))
        if yes:charge+=feat['weight'];active.append(i)
    required=packet['threshold_units'][d['witness_cell']]
    assert charge<required
    return dict(status='PASS_INDEPENDENT_COMPLETE_KERNEL_OBSTRUCTION',checker_sha256=sha(Path(__file__)),
                source_sha256=sha(receipt),cover_sha256=sha(COVER),packet_sha256=sha(packet_path),
                mask_index=source['mask_index'],witness_cell=d['witness_cell'],witness_half_angle=pose['half_angle'],
                physical_parent_charge=charge,required_charge=required,active_true_features=active,
                records=checks,total_legal_parent_cuts=sum(r['legal_parent_cuts'] for r in checks),
                total_line_intersections_checked=sum(r['line_intersections_checked'] for r in checks),
                global_optimality_proved=False,packing_exists_proved=False,mask_exclusion_proved=False,
                scope='This legal deficit parent avoids every unconditional mandatory-point kernel of the other occupied cells. No extra such point penalties repair the frozen field/threshold. Conditional ownership derived from other occupied cells is outside this obstruction.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('receipt',type=Path);p.add_argument('--packet',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=run(a.receipt,a.packet);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))
