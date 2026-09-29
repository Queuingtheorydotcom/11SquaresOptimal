"""Exact controls and timings for cached majority normals and medians."""
from fractions import Fraction as F
from pathlib import Path
from math import gcd
import argparse,json,time
from majority_mixed import validate,geometry
from majority_precompute import prepare_majority,row_strips
from majority_geometry import median_strips,require
from integer_sweep import accumulate


def normalized(strips):
    result=set()
    for a,b,lo,hi in strips:
        g=gcd(abs(a),abs(b));require(lo%g==hi%g==0,'Unexpected strip scale')
        a,b,lo,hi=a//g,b//g,lo//g,hi//g
        if a<0 or (a==0 and b<0):a,b,lo,hi=-a,-b,-hi,-lo
        result.add((a,b,lo,hi))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--conditional',action='store_true',help='Also compare one conditional row')
    args=parser.parse_args();root=Path(__file__).resolve().parents[2]
    c=json.loads((root/'source/11-squares-certified-bound-main/global-certificate.json').read_text())
    for atom in c['charge_orbits']:
        if len(atom['sets'][0])==2*atom['threshold']-1:atom['kind']='majority_hull'
    data,jobs,margin=validate(c);start=time.monotonic();prepared=prepare_majority(data)
    preparation_seconds=time.monotonic()-start;results=[];checks=0
    for row,conditional in [(0,False),(6000,False),(12027,False)]+([(0,True)] if args.conditional else []):
        timings=[];objects=[]
        for cache in (None,prepared):
            start=time.monotonic();arrays,meta=geometry(*data,*jobs[row],meta=True,
                                                       domain_conditional=conditional,prepared=cache)
            timings.append(time.monotonic()-start);objects.append((arrays,meta))
        old,new=objects[0][1],objects[1][1]
        require(dict(zip(old['rect'],old['weights']))==dict(zip(new['rect'],new['weights'])),
                'Precomputed normals changed exact rectangles')
        factor=new['scale']//(2*data[4])
        for feature,(group,k,w) in zip(prepared,data[-1]):
            points=[new['uv'][i] for i in group]
            first=median_strips(points,new['half'])
            second=row_strips(feature,points,new['half'],new['C'],new['S'],new['R'],factor)
            require(normalized(first)==normalized(second),'Precomputed strip mismatch')
            checks+=1
        minimum,cells,winner=accumulate(*objects[1][0])
        require(minimum>=c['minimum_units'],'Majority proxy lost certified threshold coverage')
        entry=dict(row=row,conditional=conditional,original_seconds=timings[0],
                   prepared_seconds=timings[1],minimum_units=int(minimum),rectangles=len(new['rect']))
        results.append(entry);print(json.dumps(entry),flush=True)
    out=dict(status='PASS_EXACT_PRECOMPUTED_MAJORITY_CONTROLS',physical_feature_strip_comparisons=checks,
             preparation_seconds=preparation_seconds,features=len(prepared),rows=results,
             scope='Selected known-baseline rows and an exact strip identity; no new bound')
    Path(__file__).with_name('precomputed-majority-controls.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
