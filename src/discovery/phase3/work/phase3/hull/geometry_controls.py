"""Cross-check the independent optimized arrangement against frozen Phase2."""
from pathlib import Path
import hashlib,importlib.util,json,random,time,sys
import rational
import arrangement_audit as new
F=rational.F
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('frozen_geometry',ROOT/'work/phase2/hull/arrangement_audit.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def parse(poly):return [tuple(map(F,p)) for p in poly]
def main():
    start=time.monotonic();rng=random.Random(314159);records=[]
    for i in range(100):
        points=[(F(rng.randrange(-12,13),rng.randrange(1,8)),F(rng.randrange(-12,13),rng.randrange(1,8))) for _ in range(30)]
        assert old.gift_hull([tuple(old.F(str(x)) for x in p) for p in points])==new.gift_hull(points)
    source=ROOT/'work/phase2/geometry/mask1383_conditional_filter_checkpoint.json'
    d=json.loads(source.read_text());times={'frozen':0.,'optimized':0.}
    for ri in (0,2,6,10):
        rnd=d['rounds'][ri];prior=[parse(group) for group in rnd['prior_owned_points']];cell=rnd['cells'][0]
        other={j:new.gift_hull(prior[j]) for j in d['mask'] if j!=cell['owner']}
        for row in cell['rows'][:15]:
            lo,hi=map(F,row['interval']);domain=parse(row['input_domain']);residual=[parse(p) for p in row['residual_polygons']]
            answers=[]
            for label,mod in (('frozen',old),('optimized',new)):
                if label=='frozen':
                    cv=lambda poly:[tuple(old.F(str(x)) for x in p) for p in poly]
                    aa=(cv(domain),{j:cv(p) for j,p in other.items()},old.F(str(lo)),old.F(str(hi)),old.F(d['parent_Uplus']),[cv(p) for p in residual])
                else:aa=(domain,other,lo,hi,F(d['parent_Uplus']),residual)
                t=time.monotonic();a=mod.audit_residual_cover(*aa);times[label]+=time.monotonic()-t;answers.append(a)
            assert answers[0]==answers[1] and answers[1]['passed']
            records.append(answers[1])
    sq=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
    tri=sq[:3]
    assert not new.union_cover(sq,[tri])['passed']
    canonical=json.dumps(records,sort_keys=True,default=str,separators=(',',':')).encode()
    out=dict(status='PASS',backend=rational.BACKEND,version=rational.VERSION,random_hull_cases=100,real_rows=len(records),
             trace_sha256=hashlib.sha256(canonical).hexdigest(),seconds=times,speedup=times['frozen']/times['optimized'],elapsed=time.monotonic()-start)
    path=Path(sys.argv[1]);path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
