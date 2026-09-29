#!/usr/bin/env python3
"""Exact controls for the orientation-polygon square-fitting criterion."""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
from hashlib import sha256
import json
import square_fit_polygon as polygon
from square_variance_support import moment


def main():
    controls=[]
    def check(name,points,A,expected):
        certificate=polygon.fit_certificate(points,A)
        polygon.need(certificate['fits']==expected,name+' has wrong fit status')
        controls.append(dict(name=name,support=points,certificate=certificate))
        return certificate
    check('singleton',[(0,0)],1,True)
    check('repeated singleton',[(3,7),(3,7)],1,True)
    boundary=check('diagonal equality',[(0,0),(1,1)],1,True)
    polygon.need(boundary['maximum_squared_radius']==1,'diagonal equality changed')
    check('pair exceeds maximum diagonal',[(0,0),(F(3,2),0)],1,False)
    rectangle=[(x,y) for x in (F(-3,5),F(3,5)) for y in (F(-1,5),F(1,5))]
    rect=check('rectangle beyond diameter and every unweighted variance',rectangle,1,False)
    polygon.need(rect['maximum_squared_radius']==F(25,32),'rectangle exact maximum differs')
    triangle=[(F(0),F(0)),(F(6,5),F(0)),(F(3,5),F(26,25))]
    tri=check('near equilateral triangle beyond diameter and every unweighted variance',triangle,1,False)
    variance_checks=0
    for points in (rectangle,triangle):
        for size in range(2,len(points)+1):
            for subset in combinations(points,size):
                polygon.need(moment(subset)[1]<=F(1,2),'example already rejected by subset variance')
                variance_checks+=1
    for index,t in enumerate((F(0),F(1,9),F(1,3),F(2,3),F(1))):
        co=(1-t*t)/(1+t*t);si=2*t/(1+t*t)
        for side in (F(1,2),F(1)):
            points=[(co*x-si*y+F(7,3),si*x+co*y-F(2,7))
                    for x in (-side/2,side/2) for y in (-side/2,side/2)]
            cert=check('constructed rational square '+str(index)+' side '+str(side),points,1,True)
            if side==1:polygon.need(cert['maximum_squared_radius']==1,'unit square orientation boundary differs')
    # Translation, rational scaling, duplication, and ordering preserve fit.
    for scale in (F(1,10),F(7,3),F(11)):
        moved=[(scale*x+17,scale*y-F(1,7)) for x,y in rectangle]
        cert=check('scaled translated rectangle '+str(scale),moved[::-1]+moved,scale,False)
        polygon.need(cert['maximum_squared_radius']==rect['maximum_squared_radius'],'scale invariance failed')
    result=dict(status='PASS_EXACT_ORIENTATION_POLYGON_CONTROLS',
                controls=len(controls),all_subset_variance_controls=variance_checks,
                rectangle_maximum_squared_radius=rect['maximum_squared_radius'],
                triangle_maximum_squared_radius=tri['maximum_squared_radius'],
                module_sha256=sha256(Path(polygon.__file__).read_bytes()).hexdigest(),
                cases=controls,
                scope='Exact clipping controls and strict examples; theorem is proved separately. No new charge or packing certificate.')
    path=Path(__file__).with_name('square-fit-polygon-controls.json')
    path.write_text(json.dumps(result,default=lambda x:str(x) if isinstance(x,F) else x,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},default=str,indent=2))


if __name__=='__main__':main()
