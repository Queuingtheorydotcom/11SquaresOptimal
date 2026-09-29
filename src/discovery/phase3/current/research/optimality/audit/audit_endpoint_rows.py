#!/usr/bin/env python3
"""Independent feature expansion and integer-Horner endpoint replay.

Only the previously audited algebraic construction / field arithmetic is shared.
No endpoint evaluator, FastExactParentModel, or floating root solver is imported.
"""
from pathlib import Path
from fractions import Fraction as F
from math import gcd, lcm
import hashlib, json, sys, time
import numpy as np
import sympy as sp

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'work/construction'))
from verify_trump import E, u, M, I, configuration

def require(x,msg):
    if not x: raise ValueError(msg)

class HornerSigns:
    def __init__(self, endpoints):
        a,b=map(F,endpoints)
        require(F(I[0])<a<b<F(I[1]),'root bracket not strictly within isolating interval')
        require(M.count_roots(*I)==1 and M.is_irreducible,'root isolation / field failed')
        require(M.eval(sp.Rational(a.numerator,a.denominator))<0 and
                M.eval(sp.Rational(b.numerator,b.denominator))>0,'bracket signs failed')
        self.D=lcm(a.denominator,b.denominator)
        self.a=int(a*self.D);self.b=int(b*self.D)
        self.calls=0;self.zero=0
    def coefficients(self,*elements):
        rows=[[F(x.p.nth(j)) for j in range(8)] for x in elements]
        scale=lcm(*(x.denominator for row in rows for x in row))
        return [[int(x*scale) for x in row] for row in rows]
    def sign(self, coeff):
        self.calls+=1
        if not any(coeff):self.zero+=1;return 0
        lo=hi=coeff[-1];den=1
        for c in reversed(coeff[:-1]):
            candidates=(lo*self.a,lo*self.b,hi*self.a,hi*self.b)
            den*=self.D
            lo=min(candidates)+c*den;hi=max(candidates)+c*den
        if lo>0:return 1
        if hi<0:return -1
        raise ValueError('Horner interval does not decide a nonzero field element')
    def linear(self,rows,weights):
        return self.sign([sum(row[j]*w for row,w in zip(rows,weights)) for j in range(8)])
    def element(self,x):return self.sign(self.coefficients(x)[0])

def audit(transported_source=None):
    started=time.monotonic()
    family=ROOT/'research/stromquist/candidate-true-enriched-round6.json'
    source=transported_source or HERE.parent/'endpoint_charge/exact-trump-endpoint-rows.json'
    npz=source.with_suffix('.npz')
    data=json.loads(family.read_text()); receipt=json.loads(source.read_text())
    checker=HornerSigns(receipt['root_interval'])
    D=data['coordinate_denominator']; L=F(data['L']); LD=int(L*D)
    require(F(LD,D)==L,'site denominator incompatible with frame')
    points=[];point_columns=[];budgets=[]
    for column,(x,y,unused) in enumerate(data['point_orbits']):
        images=sorted({(a,b) for p,q in [(x,y),(y,x)] for a in [p,LD-p] for b in [q,LD-q]})
        require(all(0<=p<=LD and 0<=q<=LD for p,q in images),'site outside frame')
        points.extend(images);point_columns.extend([column]*len(images));budgets.append(len(images))
    groups=[];npointcols=len(budgets)
    for j,atom in enumerate(data['charge_orbits']):
        kind=atom.get('kind','threshold'); k=atom['threshold']
        require(kind in ('majority_hull','floor','threshold') and k>0,'unrecognized kind')
        arity=len(atom['sets'][0])
        require(all(len(inds)==arity and len(set(inds))==arity for inds in atom['sets']),'bad arity or duplicate support index')
        if kind=='majority_hull':require(arity==2*k-1,'not an odd majority')
        if kind=='threshold':require(arity<2*k,'threshold capacity-one rule invalid')
        budgets.append(len(atom['sets'])*(arity//k))
        for inds in atom['sets']:
            require(all(0<=a<len(points) for a in inds),'site index outside array')
            normals=[]
            if kind=='majority_hull':
                p=[points[a] for a in inds];directions=set()
                for ia in range(len(p)):
                    for ib in range(ia):
                        nx=p[ia][1]-p[ib][1];ny=p[ib][0]-p[ia][0];g=gcd(nx,ny)
                        if not g:continue
                        nx//=g;ny//=g
                        if nx<0 or (nx==0 and ny<0):nx=-nx;ny=-ny
                        directions.add((nx,ny))
                normals=[(nx,ny,sorted(nx*x+ny*y for x,y in p)[k-1]) for nx,ny in sorted(directions)]
            groups.append((inds,npointcols+j,kind,k,normals))
    squares,alpha,axes=configuration(E(u)); B=E(L.numerator)/E(L.denominator)/alpha
    require(checker.element(alpha-E(F(969271,250000).numerator)/F(969271,250000).denominator)<0,'endpoint exceeds center-cover scope')
    poses=[]
    for i,square in enumerate(squares):
        if transported_source is None:
            vertices=[(B*x,B*y) for x,y in square]
        else:
            target=F(receipt['target_side']); A=E(L.numerator)/E(L.denominator)/E(target.numerator)*E(target.denominator)
            require(F(receipt['side_A'])==L/target,'transported parent side differs')
            oldcenter=tuple(sum(p[k] for p in square)/4 for k in range(2))
            C,S=(E(1),E(0)) if i<6 else axes[2]
            width=C+S;oldhalf=B*width/2;newhalf=A*width/2;frame=E(L.numerator)/L.denominator
            # Independently interpolate between the two new allowed endpoints.
            position=tuple((B*v-oldhalf)/(frame-2*oldhalf) for v in oldcenter)
            center=tuple(newhalf+v*(frame-2*newhalf) for v in position)
            vertices=[tuple(center[k]+A*(p[k]-oldcenter[k]) for k in range(2)) for p in square]
        poses.append(vertices)
    closed=np.zeros((11,len(budgets)),np.int64);opened=closed.copy()
    for i,vertices in enumerate(poses):
        matrices=[checker.coefficients(x,y,E(1)) for x,y in vertices]
        normals=[]
        for p,q in zip(vertices,vertices[1:]+vertices[:1]):
            nx=-(q[1]-p[1]);ny=q[0]-p[0]
            normals.append(checker.coefficients(nx,ny,-nx*p[0]-ny*p[1]))
        edge=np.asarray([[checker.linear(normal,(x,y,D)) for x,y in points] for normal in normals])
        weak=np.all(edge>=0,axis=0);strict=np.all(edge>0,axis=0)
        for j,c,o in zip(point_columns,weak,strict):closed[i,j]+=int(c);opened[i,j]+=int(o)
        cache={}
        for indices,column,kind,k,normals in groups:
            count=sum(int(weak[a]) for a in indices); open_count=sum(int(strict[a]) for a in indices)
            if kind!='majority_hull':
                closed[i,column]+=count//k if kind=='floor' else int(count>=k)
                opened[i,column]+=open_count//k if kind=='floor' else int(open_count>=k)
                continue
            if open_count>=k:closed[i,column]+=1;opened[i,column]+=1;continue
            yes=all(sum(int(edge[e,a]>=0) for a in indices)>=k for e in range(4))
            inside=all(sum(int(edge[e,a]>0) for a in indices)>=k for e in range(4))
            if not yes:continue
            for nx,ny,median in normals:
                key=(nx,ny,median)
                if key not in cache:cache[key]=[checker.linear(mat,(D*nx,D*ny,-median)) for mat in matrices]
                signs=cache[key]
                if min(signs)>0 or max(signs)<0:yes=False;inside=False;break
                if min(signs)==0 or max(signs)==0:inside=False
            closed[i,column]+=int(yes);opened[i,column]+=int(inside)
    expected=np.load(npz)
    require(np.array_equal(closed,expected['closed']),'closed rows differ')
    require(np.array_equal(opened,expected['opened']),'open rows differ')
    require(np.array_equal(budgets,expected['budget']),'budgets differ')
    require(np.array_equal(closed,opened),'open / closed rows differ')
    slack=np.asarray(budgets)-closed.sum(axis=0)
    require(np.all(slack>=0),'column budget exceeded')
    require(checker.zero==0,'some evaluated feature forms vanish')
    require(hashlib.sha256(family.read_bytes()).hexdigest()==receipt['family_sha256'],'family hash differs')
    require((closed@expected['weights']).tolist()==receipt['closed_cut12_charge_units'],'weighted rows differ')
    result={'status':'PASS_INDEPENDENT_EXACT_ENDPOINT_ROW_AUDIT',
            'method':'Independent raw-family expansion and raw-world median normals; exact integer Horner sign bounds at the rational isolating bracket; no endpoint evaluator or FastExactParentModel imported.',
            'family_sha256':hashlib.sha256(family.read_bytes()).hexdigest(),
            'source_json_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'source_npz_sha256':hashlib.sha256(npz.read_bytes()).hexdigest(),
            'rows':11,'columns':len(budgets),'expanded_groups':len(groups),
            'field_sign_evaluations':checker.calls,'zero_evaluations':checker.zero,
            'open_closed_identical':True,'columnwise_budget_feasible':True,
            'saturated_columns':int(np.count_nonzero(slack==0)),
            'endpoint_within_center_cover_side':True,
            'strict_fixed_family_endpoint_reweighting_impossible':True,
            'global_optimality_proved':False}
    if transported_source is not None:
        containment=0;wallcontacts=0
        frame=E(L.numerator)/L.denominator
        for vs in poses:
            for p,q,r in zip(vs,vs[1:]+vs[:1],vs[2:]+vs[:2]):
                edge=tuple(q[k]-p[k] for k in range(2));nextedge=tuple(r[k]-q[k] for k in range(2))
                require((sum(v*v for v in edge)-A*A).iszero(),'transported side identity fails')
                require(sum(x*y for x,y in zip(edge,nextedge)).iszero(),'transported angle is not right')
                for value in [p[0],p[1],frame-p[0],frame-p[1]]:
                    s=checker.element(value);require(s>=0,'transported vertex outside frame')
                    containment+=1;wallcontacts+=int(s==0)
        endpoint=np.load(HERE.parent/'endpoint_charge/exact-trump-endpoint-rows.npz')
        require(np.array_equal(closed,endpoint['closed']),'transported rows are not endpoint rows')
        result.update(status='PASS_INDEPENDENT_EXACT_TRANSPORTED_FAMILY_OBSTRUCTION_AUDIT',
                      target_side=str(target),parent_side=str(L/target),
                      containment_inequalities=containment,wall_contacts=wallcontacts,
                      transported_rows_identical_to_endpoint=True,
                      all_parent_edge_lengths_and_right_angles_checked=True,
                      field_sign_evaluations_including_containment=checker.calls,
                      scope='Individually legal row types block unchanged-family nonnegative charge/counting at S>=target_side by monotonicity; no compatible packing is claimed.')
    result['elapsed_seconds']=time.monotonic()-started
    return result

def main():
    transported=len(sys.argv)>1 and sys.argv[1]=='--transported'
    source=HERE.parent/'endpoint_charge/transported-3.87708.json' if transported else None
    result=audit(source)
    filename='transported-3.87708-independent-audit.json' if transported else 'endpoint-rows-independent-audit.json'
    (HERE/filename).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
