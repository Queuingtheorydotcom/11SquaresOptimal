from pathlib import Path
import sys,time,json
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/phase3/capture'))
import capture_engine_v2 as E
from collision_kernel import PartnerCover
start=time.monotonic()
s=E.root_state(ROOT/'work/phase2/conditional/mask438-adaptive.json')
covers={};prepared={}
for owner,rows in s['cells'].items():
    prepared[owner]=[dict(core=E.stronger.polygon_core(*r['interval'],s['U'])['vertices'],
                      domain=E.clip_constraints(r['outer_domain'],owner,s['constraints']),reference=r['reference'])
                    for r in rows]
    covers[owner]=PartnerCover(prepared[owner])
print(json.dumps(dict(stage='prepared',seconds=time.monotonic()-start,rows={i:len(p) for i,p in prepared.items()})),flush=True)
results=[]
for i in [i for i in [4,5,15,13] if i in prepared]:
    rr=prepared[i]
    for ix in sorted(set([0,len(rr)//4,len(rr)//2,3*len(rr)//4,len(rr)-1])):
        r=rr[ix];t=time.monotonic()
        owned=[E.geo.minkowski(h,[(-x,-y) for x,y in r['core']]) for j,h in s['groups'].items() if j!=i]
        before=E.geo.union_cover(r['domain'],owned)['remaining']
        additions=[];partners=[]
        for j,cover in covers.items():
            if i==j:continue
            ans=cover.kernel(r['core'],r['domain'])
            if E.geo.twice_area(ans['vertices'])>0:
                additions.append(ans['vertices']);partners.append(j)
        after=E.geo.union_cover(r['domain'],owned+additions)['remaining']
        item=dict(owner=i,row=ix,partners=partners,area_before=str(sum(E.geo.twice_area(p) for p in before)),
                  area_after=str(sum(E.geo.twice_area(p) for p in after)),seconds=time.monotonic()-t)
        item['ratio']=float(E.F(item['area_after'])/E.F(item['area_before'])) if E.F(item['area_before']) else None
        results.append(item);print(json.dumps({k:v for k,v in item.items() if not k.startswith('area_')}),flush=True)
E.save(ROOT/'work/phase3/shared/collision-benchmark.json',dict(results=results,seconds=time.monotonic()-start,
       producer_sha256=E.sha(Path(__file__).with_name('collision_kernel.py'))))
