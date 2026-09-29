#!/usr/bin/env python3
"""Independent symmetric-cover and exact local-center assignment audit."""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import hashlib,json
from audit_center_cover import audit,require,dot,norm2
from audit_endpoint_rows import E,u,configuration,HornerSigns

HERE=Path(__file__).resolve().parent

def ef(x):
    q=F(x)
    return E(q.numerator)/q.denominator

def main():
    coverfile=HERE.parent/'global_capture/center-cover-symmetric-exact.json'
    source=HERE.parent/'global_capture/trump-cell-symmetric-assignments.json'
    cover=json.loads(coverfile.read_text());data=json.loads(source.read_text())
    geometry=audit(coverfile)
    sites=[tuple(map(F,cell['center'])) for cell in cover['cells']]
    for i in range(16):
        require(tuple(1-x for x in sites[i])==sites[15-i],'site half turn mismatch')
        require({tuple(F(x) for x in v) for v in cover['cells'][i]['vertices']}==
                {tuple(1-F(x) for x in v) for v in cover['cells'][15-i]['vertices']},'cell half turn mismatch')
    turn=lambda J:tuple(sorted(15-i for i in J))
    allmasks=list(combinations(range(16),11))
    require(all(J!=turn(J) for J in allmasks),'an odd mask is invariant')
    canonical=sorted({min(J,turn(J)) for J in allmasks})
    require(len(canonical)==2184,'wrong orbit count')
    require([list(J) for J in canonical]==cover['canonical_eleven_cell_subsets'],'canonical list differs')
    # Independent signs use the much narrower certified endpoint bracket.
    endpoint=json.loads((HERE.parent/'endpoint_charge/exact-trump-endpoint-rows.json').read_text())
    sign=HornerSigns(endpoint['root_interval'])
    squares,alpha,_=configuration(E(u))
    centers=[(sum(x for x,y in square)/4-alpha/2,sum(y for x,y in square)/4-alpha/2) for square in squares]
    scale=F(cover['side_upper'])-1;rho=F(1,248)
    rows=[];minrooms=[];checks=0
    for swap in (False,True):
        for sx in (False,True):
            for sy in (False,True):
                cells=[]
                for center in centers:
                    x,y=center
                    if swap:x,y=y,x
                    if sx:x=-x
                    if sy:y=-y
                    point=(x/ef(scale)+ef(F(1,2)),y/ef(scale)+ef(F(1,2)))
                    matched=[]
                    for i,p in enumerate(sites):
                        inside=True
                        for j,q in enumerate(sites):
                            if i==j:continue
                            a=(2*(q[0]-p[0]),2*(q[1]-p[1]));b=norm2(q)-norm2(p)
                            room=(ef(b)-ef(a[0])*point[0]-ef(a[1])*point[1])*ef(scale)-ef(rho*(abs(a[0])+abs(a[1])))
                            checks+=1
                            if sign.element(room)<=0:inside=False;break
                        if inside:matched.append(i)
                    require(len(matched)==1,'local center box lacks unique strict site')
                    cells.append(matched[0])
                require(len(set(cells))==11,'cell assignment is not injective')
                rows.append({'symmetry':{'swap':swap,'reflect_x':sx,'reflect_y':sy},'label_to_cell':cells,'selection':sorted(cells)})
    require(len(rows)==len(data['eight_D4_images'])==8,'symmetry enumeration differs')
    for r,expected in zip(rows,data['eight_D4_images']):
        require(all(r[key]==expected[key] for key in r),'local assignment differs')
    capture=sorted({min(tuple(r['selection']),turn(r['selection'])) for r in rows})
    require(len(capture)==4,'capture masks do not have four orbits')
    require([list(J) for J in capture]==data['canonical_capture_masks'],'capture mask list differs')
    result={'status':'PASS_INDEPENDENT_SYMMETRIC_COVER_AND_LOCAL_CENTER_ASSIGNMENT_AUDIT',
            'cover_sha256':hashlib.sha256(coverfile.read_bytes()).hexdigest(),
            'assignments_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'geometry_audit':geometry,'canonical_masks':2184,
            'endpoint_D4_images':8,'capture_canonical_masks':4,'other_canonical_masks':2180,
            'independent_field_sign_evaluations':checks,'local_center_radius':str(rho),
            'coordinate_interpretation':'Translate centered containers by alpha/2 to apply the fixed [0,alpha]^2 local theorem; this preserves center displacements and angles exactly.',
            'boundary_interpretation':'Only feasible points of each local center box lie in the clipped cover domain; all points of the box satisfy strict nearest-site inequalities.',
            'halfturn_boundary_interpretation':'Canonical cases use closed cells, so halfturn acts on case membership even where the least-index tie assignment does not commute with reflection.',
            'global_optimality_proved':False}
    (HERE/'symmetric-capture-independent-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
