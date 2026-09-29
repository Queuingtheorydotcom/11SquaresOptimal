"""Exact conservative center domains for single/double/all-four membership.

Coordinates use a containing square [0,L]^2 and parents of side A. Parent
half-angle tangents may vary throughout a closed rational interval. Returned
type covers overlap deliberately; they are not an exact partition.
"""
from fractions import Fraction as F


def require(ok, message):
    if not ok:raise ValueError(message)


def trig(t):
    t=F(t);return (1-t*t)/(1+t*t),2*t/(1+t*t)


def halfwidth(A,t):
    c,s=trig(t);return F(A)*(c+s)/2


def halfwidth_bounds(A,lo,hi,sqrt2_upper=F(14142135623730951,10**16)):
    """r_min is exact; r_max is exact except at an interior irrational maximum."""
    A,lo,hi=map(F,(A,lo,hi))
    require(A>0 and 0<=lo<=hi<=1,'Invalid parent/angle interval')
    ends=(halfwidth(A,lo),halfwidth(A,hi));lower=min(ends)
    # d[(1+2t-t²)/(1+t²)]/dt has the sign of 1-2t-t².
    crosses=(lo*lo+2*lo<=1 and hi*hi+2*hi>=1)
    if crosses:
        u=F(sqrt2_upper);require(u>0 and u*u>=2,'Invalid sqrt(2) upper bound')
        upper=A*u/2;kind='rational_upper_bound_at_stationary_maximum'
    else:
        upper=max(ends);kind='exact_endpoint_maximum'
    return lower,upper,kind


def rotate_box(box,L):
    """Counterclockwise quarter-turn about the container center."""
    x0,x1,y0,y1=box
    return F(L)-y1,F(L)-y0,x0,x1


def type_boxes(L,A,lo,hi,a_unit=F(1353553,500000)):
    L,A,a_unit=map(F,(L,A,a_unit));a=A*a_unit;W=2*a-L
    require(0<A<a<L,'Invalid scaled corner windows')
    require(W>0 and W*W>2*A*A,'Corner windows do not cover every parent')
    require(W<2*A,'Central-window capacity-one premise does not hold')
    rmin,rmax,kind=halfwidth_bounds(A,lo,hi)
    require(2*rmax<L,'Empty containing-center envelope')
    bmin=L-a+rmin;bmax=L-a+rmax;cmax=a-rmin
    # Actual b(r)=L-a+r increases; c(r)=a-r decreases with r.
    representatives={
        'single':(rmin,bmax,rmin,bmax),
        'double':(bmin,cmax,rmin,bmax),
        'all4':(bmin,cmax,bmin,cmax),
    }
    boxes={}
    for name,box in representatives.items():
        require(box[0]<=box[1] and box[2]<=box[3],'Invalid type cover')
        boxes[name]=[box]
        if name!='all4':
            for _ in range(3):boxes[name].append(rotate_box(boxes[name][-1],L))
    return {'L':L,'A':A,'scaled_window_side':a,'r_min':rmin,'r_max':rmax,
            'r_max_kind':kind,'representatives':representatives,'boxes':boxes}


def actual_type(L,A,t,center,a_unit=F(1353553,500000)):
    """Exact closed-window membership of one exactly contained parent."""
    L,A,a_unit=map(F,(L,A,a_unit));a=A*a_unit;r=halfwidth(A,t)
    x,y=map(F,center);require(r<=x<=L-r and r<=y<=L-r,'Parent not contained')
    count=sum(int(x0<=x-r and x+r<=x0+a and y0<=y-r and y+r<=y0+a)
              for x0,y0 in ((0,0),(L-a,0),(0,L-a),(L-a,L-a)))
    require(count in (1,2,4),'Unexpected window-membership count')
    return {1:'single',2:'double',4:'all4'}[count]


def in_box(point,box):
    x,y=point;x0,x1,y0,y1=box
    return x0<=x<=x1 and y0<=y<=y1


def projected_box(box,L,meta):
    """Map a world-coordinate box into majority_mixed's exact sweep lattice."""
    x0,x1,y0,y1=map(F,box);L=F(L)
    C,S,scale=(meta[k] for k in ('C','S','scale'))
    return [(scale*(C*(x-L/2)+S*(y-L/2)),
             scale*(-S*(x-L/2)+C*(y-L/2)))
            for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1))]


def controls():
    """Boundary-rich rational examples supplement the symbolic domain proof."""
    L=F(191,50);A=F(7640,7751);a=A*F(1353553,500000)
    intervals=[(F(0),F(0)),(F(0),F(1,100)),(F(1,10),F(1,5)),
               (F(2,5),F(21,50)),(F(41,100),F(207107,500000)),
               (F(1,2),F(3,4)),(F(0),F(1))]
    checks=0;boundary_checks=0
    for lo,hi in intervals:
        d=type_boxes(L,A,lo,hi)
        for j in range(17):
            t=lo+(hi-lo)*j/16;r=halfwidth(A,t)
            require(d['r_min']<=r<=d['r_max'],'Halfwidth escaped enclosure')
            b=L-a+r;c=a-r
            coords=sorted({r,b,c,L-r,(r+b)/2,(b+c)/2,(c+L-r)/2})
            for x in coords:
                for y in coords:
                    name=actual_type(L,A,t,(x,y))
                    require(any(in_box((x,y),box) for box in d['boxes'][name]),
                            'Actual type escaped its interval cover')
                    require(actual_type(L,A,t,(L-y,x))==name,'Quarter-turn changed type')
                    if x in (b,c) or y in (b,c):boundary_checks+=1
                    checks+=1
            # Closed inner boundaries are both-window positions, never outer-only.
            require(actual_type(L,A,t,(b,c))=='all4','Closed boundary misclassified')
    return {'status':'PASS_EXACT_TYPE_DOMAIN_CONTROLS','parent_placements':checks,
            'inner_boundary_placements':boundary_checks,
            'scope':'Exact rational controls plus the separate symbolic cover proof; not a packing certificate'}


if __name__=='__main__':
    import json
    from pathlib import Path
    result=controls();Path(__file__).with_name('type-domain-controls.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
