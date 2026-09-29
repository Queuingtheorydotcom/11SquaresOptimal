"""Exact local true-majority polygon arrangement over surrogate-low cells.

Each input box must have a constant generic TOTAL surrogate charge. Individual
feature changes may cancel inside it; the recursion then splits their proxy
boundaries as necessary. It proves a lower bound on true charge or returns an
exactly checked deficient center.
Closed facet boundaries are handled by upper semicontinuity, not counted as
additional arrangement faces. No floating arithmetic is used.
"""
from fractions import Fraction as F
from majority_geometry import median_strips,clip_axis,require
from majority_precompute import row_strips


def signed_area(poly):
    return sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(poly,poly[1:]+poly[:1]))


def clean(poly):
    out=[]
    for p in poly:
        if not out or out[-1]!=p:out.append(p)
    if len(out)>1 and out[0]==out[-1]:out.pop()
    return out if len(out)>=3 and signed_area(out) else []


def clip(poly,line):
    """Intersect a cyclic convex polygon with a*x+b*y<=rhs exactly."""
    if not poly:return []
    a,b,rhs=line;out=[]
    vals=[a*p[0]+b*p[1]-rhs for p in poly]
    for i,(p,q) in enumerate(zip(poly,poly[1:]+poly[:1])):
        vp,vq=vals[i],vals[(i+1)%len(poly)]
        if vp<=0:out.append(p)
        if (vp<0 and vq>0) or (vp>0 and vq<0):
            ratio=F(vp)/F(vp-vq)
            out.append((p[0]+ratio*(q[0]-p[0]),p[1]+ratio*(q[1]-p[1])))
    return clean(out)


def centroid(poly):
    # Vertex average is strictly interior to every positive-area convex polygon.
    return tuple(sum(p[j] for p in poly)/len(poly) for j in range(2))


def feature_status(poly,lines):
    """1=everywhere true, 0=false on interior, 2=crossing; return split line."""
    partial=[]
    for line in lines:
        a,b,rhs=line;v=[a*p[0]+b*p[1]-rhs for p in poly]
        if min(v)>=0 and max(v)>0:return 0,None
        if max(v)>0:partial.append(line)
    if not partial:return 1,None
    intersection=poly
    for line in partial:
        intersection=clip(intersection,line)
        if not intersection:return 0,None
    return 2,partial[0]


def true_charge(data,uv,half,point):
    """Direct logical charge of one closed square, using raw-site strips."""
    x,y=point
    captured=[abs(x-u)<=half and abs(y-v)<=half for u,v in uv]
    z=sum(w for w,hit in zip(data[1],captured) if hit)
    z+=sum(w for group,w in zip(data[2],data[3]) if all(captured[i] for i in group))
    z+=sum(w for group,k,w in data[-1]
           if all(lo<=a*x+b*y<=hi for a,b,lo,hi in
                  median_strips([uv[i] for i in group],half)))
    return z


class PatchVerifier:
    def __init__(self,data,meta,threshold,max_nodes=100000,prepared=None):
        self.data=data;self.meta=meta;self.threshold=threshold;self.max_nodes=max_nodes
        self.features=[]
        for feature_index,((group,k,w),rectangles) in enumerate(zip(data[-1],meta['feature_rectangles'])):
            points=[meta['uv'][i] for i in group]
            if prepared is None:strips=median_strips(points,meta['half'])
            else:
                factor=meta['scale']//(2*data[4])
                strips=row_strips(prepared[feature_index],points,meta['half'],
                                  meta['C'],meta['S'],meta['R'],factor)
            lines=[line for a,b,lo,hi in strips for line in ((a,b,hi),(-a,-b,-lo))]
            xs=sorted(meta['uv'][i][0] for i in group);ys=sorted(meta['uv'][i][1] for i in group)
            h=meta['half'];mid=len(group)//2
            bbox=(xs[mid]-h,xs[mid]+h,ys[mid]-h,ys[mid]+h)
            self.features.append((w,lines,rectangles,bbox))
        self.stats=dict(cells=0,empty_cells=0,nodes=0,max_depth=0,pruned=0,splits=0,
                        feature_classifications=0,generic_facet_retries=0)
        self.avoid_facets=None
        h=meta['half']
        self.avoid_x={u+s*h for u,v in meta['uv'] for s in (-1,1)}
        self.avoid_y={v+s*h for u,v in meta['uv'] for s in (-1,1)}
        for w,lines,rectangles,bbox in self.features:
            self.avoid_x.update(x for r in rectangles for x in r[:2])
            self.avoid_y.update(y for r in rectangles for y in r[2:])

    def charge(self,point):
        """Independent direct evaluation of the true logical charge."""
        # Recompute raw-site strips rather than reuse precomputed normals: this
        # also independently checks any candidate deficient witness.
        return true_charge(self.data,self.meta['uv'],self.meta['half'],point)

    def verify_cell(self,box,surrogate):
        x0,x1,y0,y1=map(F,box);require(x0<x1 and y0<y1,'Invalid raw cell')
        poly=[tuple(map(F,p)) for p in self.meta['poly']]
        for axis,bound,high in [(0,x0,True),(0,x1,False),(1,y0,True),(1,y1,False)]:
            poly=clip_axis(poly,axis,bound,high)
        poly=clean(poly);self.stats['cells']+=1
        if not poly:self.stats['empty_cells']+=1;return dict(status='PASS_EMPTY')
        inactive=[]
        for i,(w,lines,rectangles,bbox) in enumerate(self.features):
            if bbox[1]<=x0 or bbox[0]>=x1 or bbox[3]<=y0 or bbox[2]>=y1:continue
            inactive.append(i)
        result=self._verify(poly,int(surrogate),inactive,0)
        if result['status']=='COUNTEREXAMPLE':
            point=result['point'];actual=self.charge(point)
            require(actual<self.threshold,'Counterexample failed direct charge check')
            require(x0<point[0]<x1 and y0<point[1]<y1,'Counterexample on a cell boundary')
            result['true_charge_units']=actual
        return result

    def generic_point(self,poly,avoid_facets=False):
        # A rational polynomial path through strictly interior points avoids
        # the finite site-capture and proxy event lines after finitely many t.
        if avoid_facets and self.avoid_facets is None:
            self.avoid_facets=set(line for w,lines,rectangles,bbox in self.features for line in lines)
        t=1
        while True:
            weights=[t**j for j in range(len(poly))];total=sum(weights)
            point=tuple(sum(w*p[j] for w,p in zip(weights,poly))/total for j in range(2))
            if point[0] not in self.avoid_x and point[1] not in self.avoid_y:
                if not avoid_facets or all(a*point[0]+b*point[1]!=rhs for a,b,rhs in self.avoid_facets):
                    return point
            t+=1

    def gain_status(self,poly,feature):
        """Classify G - staircase_proxy on generic legal centers of poly."""
        w,lines,rectangles,bbox=feature
        xmin=min(p[0] for p in poly);xmax=max(p[0] for p in poly)
        ymin=min(p[1] for p in poly);ymax=max(p[1] for p in poly)
        crossings=[]
        for x0,x1,y0,y1 in rectangles:
            if x0<=xmin and xmax<=x1 and y0<=ymin and ymax<=y1:return 0,None
            if x1<=xmin or x0>=xmax or y1<=ymin or y0>=ymax:continue
            rlines=[(1,0,x1),(-1,0,-x0),(0,1,y1),(0,-1,-y0)]
            intersection=poly
            for line in rlines:
                intersection=clip(intersection,line)
                if not intersection:break
            if intersection:
                for line in rlines:
                    a,b,rhs=line;values=[a*x+b*y-rhs for x,y in poly]
                    if min(values)<0<max(values):crossings.append(line)
        status,line=feature_status(poly,lines)
        if status==0:return 0,None
        if not crossings:return status,line
        return 2,crossings[0]

    def gain_at(self,index,point):
        x,y=point;w,lines,rectangles,bbox=self.features[index]
        if not all(a*x+b*y<=rhs for a,b,rhs in lines):return 0
        if any(a<x<b and c<y<d for a,b,c,d in rectangles):return 0
        return w

    def _verify(self,poly,base,indices,depth):
        self.stats['nodes']+=1;self.stats['max_depth']=max(self.stats['max_depth'],depth)
        if self.stats['nodes']>self.max_nodes:return dict(status='INCOMPLETE_NODE_LIMIT')
        if base>=self.threshold:self.stats['pruned']+=1;return dict(status='PASS',lower_bound=base)
        uncertain=[]
        for i in indices:
            w,lines,rectangles,bbox=self.features[i]
            status,line=self.gain_status(poly,self.features[i]);self.stats['feature_classifications']+=1
            if status==1:base+=w
            elif status==2:uncertain.append((i,line))
        if base>=self.threshold:self.stats['pruned']+=1;return dict(status='PASS',lower_bound=base)
        point=self.generic_point(poly)
        atpoint=base+sum(self.gain_at(i,point) for i,line in uncertain)
        if atpoint<self.threshold and self.charge(point)>=self.threshold:
            # A true feature dismissed as zero-area may still contain this
            # sample on a slanted facet. Choose a point generic for every true
            # facet too; the polynomial path avoids finitely many lines.
            self.stats['generic_facet_retries']+=1
            point=self.generic_point(poly,avoid_facets=True)
            atpoint=base+sum(self.gain_at(i,point) for i,line in uncertain)
        if atpoint<self.threshold:return dict(status='COUNTEREXAMPLE',point=point,
                                               lower_bound=base,proxy_plus_gains=atpoint)
        require(uncertain,'A deficient constant face has no counterexample')
        i,line=max(uncertain,key=lambda z:self.features[z[0]][0]);a,b,rhs=line
        first=clip(poly,line);second=clip(poly,(-a,-b,-rhs))
        require(first and second,'Selected feature facet does not split the polygon')
        self.stats['splits']+=1;remaining=[i for i,line in uncertain]
        results=[]
        for part in (first,second):
            result=self._verify(part,base,remaining,depth+1)
            if not result['status'].startswith('PASS'):return result
            results.append(result)
        return dict(status='PASS',lower_bound=min(r['lower_bound'] for r in results))
