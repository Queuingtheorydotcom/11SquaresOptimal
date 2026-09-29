"""Source-independent collision-region controls against the root producer."""
from pathlib import Path
import importlib.util,json,random,time,hashlib
import validate_collision_kernel as audit
F=audit.F;geo=audit.geo
ROOT=Path(__file__).resolve().parents[3]
def main():
    path=ROOT/'work/phase3/shared/collision_kernel.py'
    producer_sha=hashlib.sha256(path.read_bytes()).hexdigest()
    spec=importlib.util.spec_from_file_location('root_collision_producer',path);producer=importlib.util.module_from_spec(spec);spec.loader.exec_module(producer)
    rng=random.Random(271828);start=time.monotonic();positive=empty=degenerate=facets=0
    query=[(-F(4),-F(4)),(F(4),-F(4)),(F(4),F(4)),(-F(4),F(4))]
    def random_hull(count,offset=0):
        return geo.gift_hull([(F(rng.randrange(-8,9)+offset,4),F(rng.randrange(-8,9),4)) for _ in range(count)])
    for case in range(200):
        Qi=random_hull(10);rows=[]
        for j in range(1+case%4):
            Qj=random_hull(10);D=random_hull(1+case%7)
            rows.append(dict(core=Qj,domain=D,reference=[case,j]))
        ans=producer.PartnerCover(rows).kernel(Qi,query);P=ans['vertices']
        checked=audit.validate_collision_polygon(Qi,rows,query,P);assert checked['passed'],(case,checked)
        facets+=checked['facet_vertex_checks']
        lines=audit.bounded_rows(query)+[(*c['normal'],c['upper']) for c in audit.collision_halfplanes(Qi,rows)]
        exact=geo.intersection_polygon(lines)
        assert geo.gift_hull(P)==exact,(case,P,exact)
        if not P:empty+=1
        elif not geo.twice_area(P):degenerate+=1
        else:positive+=1
    square=[(-F(1),-F(1)),(F(1),-F(1)),(F(1),F(1)),(-F(1),F(1))]
    for centers in ([(-2,0),(2,0)], [(-2,-2),(2,2)]):
        rows=[dict(core=square,domain=[p],reference=i) for i,p in enumerate(centers)]
        P=producer.PartnerCover(rows).kernel(square,query)['vertices']
        assert audit.validate_collision_polygon(square,rows,query,P)['passed']
        assert P and not geo.twice_area(P);degenerate+=1
    assert producer_sha==hashlib.sha256(path.read_bytes()).hexdigest(),'Producer changed during cross-check'
    result=dict(status='PASS_INDEPENDENT_COLLISION_PRODUCER_CROSSCHECK',random_cases=200,explicit_degenerate_cases=2,
                positive_regions=positive,empty_regions=empty,degenerate_regions=degenerate,facet_vertex_checks=facets,
                producer_sha256=producer_sha,validator_sha256=hashlib.sha256(Path(audit.__file__).read_bytes()).hexdigest(),seconds=time.monotonic()-start)
    output=Path(__file__).with_name('producer-independent-crosscheck.json');output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
