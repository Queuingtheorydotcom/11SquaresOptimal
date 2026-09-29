"""Discovery of exact triangle witnesses for convex-union coverage.

This is a producer, not a coverage verifier.  Acceptance requires a separate
checker to validate each triangle's region membership and the oriented boundary
chain.  No area-only equality is used as a coverage assertion.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'capture/gmp'))
import fast_convex_v2 as geo

def fan(poly,index):
    result=[]
    for k in range(1,len(poly)-1):
        triangle=[poly[0],poly[k],poly[k+1]]
        orientation=geo.cross(*triangle)
        assert orientation>=0
        if orientation>0:result.append(dict(vertices=triangle,region_index=index))
    return result

def partition(poly,region):
    """Return (pieces outside the region, their convex intersection)."""
    if geo.box_disjoint(geo.bbox(poly),geo.bbox(region)):return [poly],[]
    inside=poly;outside=[]
    for n,b in geo.rows(region):
        piece=geo.clip_linear(inside,n,b,False)
        if geo.twice_area(piece)>0:outside.append(piece)
        inside=geo.clip_linear(inside,n,b,True)
        if geo.twice_area(inside)==0:return outside,[]
    return outside,inside

def make_mesh(domain,regions,max_triangles=100000,max_pieces=10000):
    domain=geo.hull(domain)
    if geo.twice_area(domain)==0:
        return dict(status='DEGENERATE_DOMAIN_NEEDS_SEPARATE_CHECK',triangles=[],remaining=[domain])
    pieces=[domain];triangles=[];used=[]
    for index,region in enumerate(regions):
        region=geo.hull(region)
        if geo.twice_area(region)==0:continue
        rest=[];new=0
        for p in pieces:
            outside,inside=partition(p,region);rest.extend(outside)
            if inside:
                additions=fan(inside,index);triangles.extend(additions);new+=len(additions)
        pieces=rest
        if new:used.append(index)
        if not pieces:
            return dict(status='COMPLETE_TRIANGLE_COVER_PROPOSAL',triangles=triangles,remaining=[],regions_used=used)
        if len(triangles)>max_triangles or len(pieces)>max_pieces:
            return dict(status='RESOURCE_LIMIT',triangles=triangles,remaining=pieces,regions_used=used)
    return dict(status='UNCOVERED_REGION',triangles=triangles,remaining=pieces,regions_used=used)

if __name__=='__main__':
    sq=[(0,0),(1,0),(1,1),(0,1)]
    a=make_mesh(sq,[[(0,0),(1,0),(0,1)],[(1,1),(0,1),(1,0)]])
    assert a['status']=='COMPLETE_TRIANGLE_COVER_PROPOSAL' and len(a['triangles'])==2
    b=make_mesh(sq,[[(0,0),(1,0),(0,1)]])
    assert b['status']=='UNCOVERED_REGION'
    print(dict(producer_controls='PASS',checks=2))
