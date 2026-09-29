"""Small exact controls of each staged proof path; no packing-bound claim."""
from fractions import Fraction as F
from pathlib import Path
import json
import majority_staged as staged
from majority_mixed import geometry
from majority_precompute import prepare_majority
from majority_low_cells import selfcheck
from majority_geometry import require


def main():
    low_controls=selfcheck()
    points=[(191,191),(166,251),(251,216),(216,131),(131,166)]
    data=(points,[0]*5,[],[],100,[((0,1,2),2,1),((0,3,4),2,1)])
    job=(F(1,5),F(13,20),F(1,10));prepared=prepare_majority(data)
    arrays,meta=geometry(*data,*job,meta=True,prepared=prepared,domain_conditional=True)
    require(any(isinstance(x,F) and x.denominator>1 for r in meta['rect'] for x in r),
            'Conditional test must exercise nonintegral rational event coordinates')
    results=[];old1=staged.FIRST_PATCH_NODE_LIMIT;old2=staged.FINAL_PATCH_NODE_LIMIT
    try:
        for first,final,cutoff,expected in [(5000,100000,1,'PASS'),(0,100000,1,'PASS'),
                                            (5000,100000,2,'FAIL'),(0,0,1,'FAIL')]:
            staged.FIRST_PATCH_NODE_LIMIT=first;staged.FINAL_PATCH_NODE_LIMIT=final
            result=staged.verify_row(data,job,cutoff)
            require(result['status']==expected,'Unexpected staged result')
            if expected=='PASS':require(result['minimum_units']>=cutoff,'Invalid accepted lower bound')
            results.append(dict(first_node_limit=first,final_node_limit=final,cutoff=cutoff,
                                status=result['status'],stage=result['stage'],reason=result.get('reason')))
        singleton=(points,[0]*5,[],[],100,[((0,),1,1)])
        result=staged.verify_row(singleton,job,1)
        require(result['status']=='PASS' and result['stage']=='integer_staircase','Fast path failed')
        results.append(dict(status=result['status'],stage=result['stage']))
    finally:
        staged.FIRST_PATCH_NODE_LIMIT=old1;staged.FINAL_PATCH_NODE_LIMIT=old2
    out=dict(status='PASS_EXACT_STAGED_MAJORITY_CONTROLS',low_cell_controls=low_controls,
             rational_conditional_events_tested=True,paths=results,
             scope='Synthetic complementary true polygons and exact helper controls; no catalogue or new bound')
    Path(__file__).with_name('staged-majority-controls.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
