#!/usr/bin/env python3
"""Source-bound controls and producer cross-checks for the chain verifier."""
from pathlib import Path
import copy,hashlib,json,random,sys,time
from rational import F
import rational
import coverage_chain as check
import arrangement_audit_v2 as geo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shared'))
import coverage_mesh as producer
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def P(ps):return [tuple(map(F,p)) for p in ps]
def rect(x0,y0,x1,y1):return P([(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
def fan(poly,k):return [dict(vertices=[poly[0],poly[j],poly[j+1]],region_index=k) for j in range(1,len(poly)-1)]
def main():
    start=time.monotonic();controls=[];square=rect(0,0,1,1)
    def run(name,D,R,M,want):
        ans=check.validate_mesh(D,R,M);assert ans['passed']==want,(name,ans)
        controls.append(dict(name=name,expected_pass=want,result=ans))
    tr=fan(square,0)
    run('two_triangles',square,[square],tr,True)
    run('hole_missing_triangle',square,[square],tr[:1],False)
    run('overlap_equal_area_hole',square,[square],[tr[0],tr[0]],False)
    run('duplicate_triangle',square,[square],tr+[tr[0]],False)
    reversed_tri=copy.deepcopy(tr);reversed_tri[0]['vertices'].reverse()
    run('reversed_triangle',square,[square],reversed_tri,False)
    line_tri=[dict(vertices=P([(0,0),(F(1,2),0),(1,0)]),region_index=0)]
    run('zero_area_triangle',square,[square],tr+line_tri,False)
    left=rect(0,0,F(1,2),1);rightlow=rect(F(1,2),0,1,F(1,2));righthigh=rect(F(1,2),F(1,2),1,1)
    regions=[left,rightlow,righthigh];tj=sum((fan(r,k) for k,r in enumerate(regions)),[])
    run('hanging_t_junction',square,regions,tj,True)
    tiny=F(1,10**50);gap=[rect(0,0,F(1,2),1),rect(F(1,2)+tiny,0,1,1)]
    run('ten_to_minus_50_gap',square,gap,fan(gap[0],0)+fan(gap[1],1),False)
    wrong=[copy.deepcopy(tr[0]),copy.deepcopy(tr[1])];wrong[0]['region_index']=1
    run('assignment_outside_region',square,[square,rightlow],wrong,False)
    outer=rect(2,2,3,3)
    run('disconnected_extra_cycle',square,[square,outer],tr+fan(outer,1),False)
    run('point_covered',P([(F(1,2),F(1,2))]),[square],[],True)
    run('point_not_covered',P([(2,2)]),[square],[],False)
    line=P([(0,0),(1,0)])
    run('segment_closed_join',line,[rect(0,-1,F(1,2),1),rect(F(1,2),-1,1,1)],[],True)
    run('segment_tiny_gap',line,[rect(0,-1,F(1,2),1),rect(F(1,2)+tiny,-1,1,1)],[],False)
    rng=random.Random(8241);crosschecks=0
    for k in range(100):
        xs=sorted({F(0),F(1)}|{F(rng.randint(1,99),100) for _ in range(4)})
        rs=[rect(a,0,b,1) for a,b in zip(xs,xs[1:])]
        # Independent chain verification accepts randomly subdivided meshes.
        mesh=producer.make_mesh(square,rs);ans=check.validate_mesh(square,rs,mesh)
        assert ans['passed'];assert geo.union_cover(square,rs)['passed'];crosschecks+=1
        # Delete a complete positive-width strip; producer status is ignored.
        rs.pop(rng.randrange(len(rs)));mesh=producer.make_mesh(square,rs)
        ans=check.validate_mesh(square,rs,mesh)
        assert not ans['passed'];assert not geo.union_cover(square,rs)['passed'];crosschecks+=1
    d=dict(status='PASS',checker_sha256=sha(check.__file__),producer_sha256=sha(producer.__file__),
           geometry_sha256=sha(geo.__file__),arithmetic_sha256=sha(rational.__file__),
           controls=controls,random_producer_and_arrangement_crosschecks=crosschecks,
           seconds=time.monotonic()-start,scope='Coverage lemma and controls only; no packing exclusion asserted.')
    out=Path(__file__).with_name('coverage-chain-controls.json');out.write_text(json.dumps(d,default=str,indent=2)+'\n')
    print(json.dumps({k:v for k,v in d.items() if k!='controls'},indent=2))
if __name__=='__main__':main()
