"""Exact outward halfspaces from the union of angular-row center prisms.

Qhull proposes facet normals. Exact cross products reconstruct each proposed
normal and exact maximization over every rational prism vertex validates its
support. Thus no Qhull tolerance is part of the resulting inequality.
"""
from scipy.spatial import ConvexHull, QhullError
import numpy as np
import exact_angle_contract as C
F=C.F

def add(model):
    cuts=[];N=len(model['midpoints'])
    for ix,owner in enumerate(model['mask']):
        box=[[model['midpoints'][3*ix+k]-model['radii'][3*ix+k],model['midpoints'][3*ix+k]+model['radii'][3*ix+k]] for k in range(3)]
        points=[]
        for row in model['pose_covers'][owner]:
            domain=row['domain']
            for k in (0,1):
                n=[0,0];n[k]=1;domain=C.E.geo.clip_linear(domain,n,box[k][1])
                n[k]=-1;domain=C.E.geo.clip_linear(domain,n,-box[k][0])
            for a,b in C.fold_at_empty_gap(*row['interval']):
                a,b=max(a,box[2][0]),min(b,box[2][1])
                if a<=b:
                    points.extend((x,y,t) for x,y in domain for t in (a,b))
        points=list(dict.fromkeys(points));assert points
        if len(points)<4:continue
        try:hull=ConvexHull(np.array([[float(v) for v in p] for p in points]))
        except QhullError:continue
        normals=set()
        for ids,eq in zip(hull.simplices,hull.equations):
            p,q,r=(points[i] for i in ids)
            a=[q[k]-p[k] for k in range(3)];b=[r[k]-p[k] for k in range(3)]
            n=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
            scale=max(map(abs,n))
            if not scale:continue
            if sum(float(v)*eq[k] for k,v in enumerate(n))<0:n=[-v for v in n]
            n=tuple(v/scale for v in n)
            if n in normals:continue
            normals.add(n)
            h=max(sum(v*x for v,x in zip(n,p)) for p in points)
            coeff=[F(0)]*N
            for k,v in enumerate(n):coeff[3*ix+k]=v
            upper=h-sum(n[k]*model['midpoints'][3*ix+k] for k in range(3))
            row=dict(coefficients=coeff,upper=upper,kind='certified_pose_prism_support',owner=owner,
                     normal=n,absolute_upper=h,prism_vertex_count=len(points))
            model['inequalities'].append(row);cuts.append(row)
    return cuts
