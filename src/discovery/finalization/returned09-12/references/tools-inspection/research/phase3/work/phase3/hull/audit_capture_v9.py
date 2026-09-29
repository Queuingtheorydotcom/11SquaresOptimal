#!/usr/bin/env python3
"""Independent replay of polygon-core, branch-conditional hull induction.

The root ownership/localization premise must have a source-bound independent
root audit. Parent node files are recursively replayed, never trusted by status.
All node geometry uses separate hull/vertical-arrangement algorithms; core
containment uses endpoint derivatives and completed-square positivity.
"""
from pathlib import Path
import argparse,copy,hashlib,json,os,time
import sys
from functools import lru_cache
import rational
from rational import F
import arrangement_audit_v2 as geo
from audit_residual_kernel import verify_convex_combinations
if not __debug__:raise RuntimeError('Assertions must be enabled')
WORK=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(WORK/'phase3/collision'))
import validate_collision_kernel_v3 as collision
import own_hull_constraints as self_hull
ROOT=Path(os.environ.get('ELEVEN_PACKING_ROOT',str(WORK.parent/'current'))).resolve()
COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
DIRECTIONS=((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(x):return json.dumps(x,default=str,sort_keys=True,separators=(',',':')).encode()
def digest(x):return hashlib.sha256(canon(x)).hexdigest()
def poly(x):return [tuple(map(F,p)) for p in x]
def groups(x):return {int(i):poly(p) for i,p in x.items()}
def locate(path,relative):
    p=Path(path)
    if p.is_file():return p.resolve()
    for base in (WORK.parent,relative.parent):
        q=base/p
        if q.is_file():return q.resolve()
    if p.is_absolute() and 'work' in p.parts:
        q=WORK/Path(*p.parts[p.parts.index('work')+1:])
        if q.is_file():return q.resolve()
    q=relative.parent/p.name
    if q.is_file():return q.resolve()
    raise FileNotFoundError(path)
def polygon_equal(a,b):return geo.gift_hull(a)==geo.gift_hull(b)
def positive_quadratic(c0,c1,c2,a,b):
    if min(c0+c1*a+c2*a*a,c0+c1*b+c2*b*b)<=0:return False
    if c2>0 and c1+2*c2*a<0<c1+2*c2*b:return 4*c0*c2-c1*c1>0
    return True
def validate_core(Q,a,b,B):
    return list(_validated_core(tuple(Q),a,b,B))
@lru_cache(maxsize=8192)
def _validated_core(Q,a,b,B):
    H=geo.gift_hull(Q);assert len(H)==len(Q) and set(H)==set(Q) and geo.twice_area(H)>0
    for x,y in Q:
        for sign in (-1,1):
            assert positive_quadratic(B/2-sign*x,-2*sign*y,B/2+sign*x,a,b)
            assert positive_quadratic(B/2-sign*y,2*sign*x,B/2+sign*y,a,b)
    return tuple(H)
def clipped(domain,extra):
    if not domain:return []
    tight={}
    for nx,ny,h in bounded_rows(domain)+extra:
        nx,ny,h=F(nx),F(ny),F(h)
        if not nx and not ny:
            if h<0:return []
            continue
        scale=abs(nx) if nx else abs(ny);n=(nx/scale,ny/scale);bound=h/scale
        tight[n]=min(tight.get(n,bound),bound)
    return geo.intersection_polygon([(*n,h) for n,h in tight.items()])
def bounded_rows(P):
    H=geo.gift_hull(P);assert H
    xs=[p[0] for p in H];ys=[p[1] for p in H]
    return geo.polygon_rows(H)+[(1,0,max(xs)),(-1,0,-min(xs)),(0,1,max(ys)),(0,-1,-min(ys))]
def lower_dimensional_cover(domain,regions):
    H=geo.gift_hull(domain);assert H and len(H)<=2
    p=H[0];q=H[-1];d=(q[0]-p[0],q[1]-p[1]);intervals=[]
    for region in regions:
        if not region:continue
        lo,hi=F(0),F(1);possible=True
        for x,y,h in bounded_rows(region):
            slope=x*d[0]+y*d[1];slack=h-x*p[0]-y*p[1]
            if slope>0:hi=min(hi,slack/slope)
            elif slope<0:lo=max(lo,slack/slope)
            elif slack<0:possible=False;break
        if possible and lo<=hi:intervals.append((lo,hi))
    cursor=F(0)
    for lo,hi in sorted(intervals):
        if hi<cursor:continue
        if lo>cursor:return dict(passed=False,status='EXACT_UNCOVERED_SEGMENT',parameter=(cursor+lo)/2,accepted_slabs=0)
        cursor=max(cursor,hi)
        if cursor>=1:return dict(passed=True,status='PASS_EXACT_LOWER_DIMENSIONAL_COVER',accepted_slabs=0)
    return dict(passed=False,status='EXACT_UNCOVERED_SEGMENT',parameter=(cursor+1)/2,accepted_slabs=0)
def support_domain(vertices,world,bounds=None):
    if not vertices:
        assert not bounds
        return [],[]
    if bounds is None:
        bounds=[]
        for n in DIRECTIONS:
            m=max(n[0]*x+n[1]*y for x,y in vertices);up=F(-((-m.numerator*10**8)//m.denominator),10**8)
            bounds.append(dict(normal=n,upper=up))
    lines=[]
    for r in bounds:
        n=tuple(map(F,r['normal']));b=F(r['upper']);assert any(n)
        assert all(n[0]*x+n[1]*y<=b for x,y in vertices);lines.append((*n,b))
    return clipped(world,lines),bounds
def normalized(n,b):
    scale=next(abs(x) for x in n if x);return tuple(x/scale for x in n)+(b/scale,)
def angle_range(owner,constraints):
    lo,hi=F(0),F(1)
    for c in constraints:
        if c.get('kind')=='half_angle' and c['owner']==owner:
            t=F(c['bound_half_angle']);assert 0<=t<=1 and c['keep'] in ('le','ge')
            if c['keep']=='le':hi=min(hi,t)
            else:lo=max(lo,t)
    assert lo<hi,'Singleton or empty angular domains require a separate exact proof'
    return lo,hi
def center_conditions(owner,constraints):
    return [(*tuple(map(F,c['normal'])),F(c['upper_field'])) for c in constraints if c['owner']==owner and c.get('kind')!='half_angle']
def residual_cover(domain,prior,Q,a,b,U,residual,extra_forbidden=()):
    B=geo.L/U;h=B*min(sum(geo.cs(t)) for t in (a,b))/2
    domain=clipped(domain,[(1,0,geo.L-h),(-1,0,-h),(0,1,geo.L-h),(0,-1,-h)])
    if not domain:return dict(passed=True,accepted_slabs=0)
    negative=[(-x,-y) for x,y in Q]
    forbidden=[geo.gift_hull([(p[0]+q[0],p[1]+q[1]) for p in K for q in negative]) for K in prior.values() if K]
    forbidden.extend(geo.gift_hull(p) for p in extra_forbidden if p)
    if not geo.twice_area(domain):return lower_dimensional_cover(domain,forbidden+[geo.gift_hull(p) for p in residual if p])
    pieces=[geo.gift_hull(p) for p in residual if p and geo.twice_area(p)>0]
    return geo.union_cover(domain,forbidden+pieces)
def hulls_intersect(A,B):
    assert A and B
    normals={(F(1),F(0)),(F(0),F(1))}
    for H in (A,B):
        normals.update((b[1]-a[1],a[0]-b[0]) for i,a in enumerate(H) for b in H[i+1:])
    return not any(max(n[0]*x+n[1]*y for x,y in A)<min(n[0]*x+n[1]*y for x,y in B) or
                   max(n[0]*x+n[1]*y for x,y in B)<min(n[0]*x+n[1]*y for x,y in A) for n in normals)

class Replay:
    def __init__(self,source,audit=None,generic_mode=False):
        self.source=source;self.source_hash=sha(source);self.root=json.loads(source.read_text());self.cache={};self.records=[]
        self.generic_mode=generic_mode;self.root_audit=audit;self.seed_checks=[];self.root_dependency_files=[]
        fresh=self.root.get('schema')=='generic_wall_seed_v1'
        self.U=F(self.root['U'] if fresh else self.root['parent_Uplus']);self.B=geo.L/self.U;self.mask=self.root['mask']
        assert self.U==F(387708359002281417731,10**20)
        assert F(self.root['B'] if fresh else self.root['parent_side'])==self.B
        cover=json.loads(COVER.read_text())
        assert sha(COVER)=='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
        assert type(self.root['mask_index']) is int and 0<=self.root['mask_index']<2184
        canonical_mask=cover['canonical_eleven_cell_subsets'][self.root['mask_index']]
        assert self.mask==sorted(set(self.mask)) and 1<=len(self.mask)<=11
        if fresh:assert set(self.mask)<=set(canonical_mask)
        else:assert self.mask==canonical_mask,'Derived Phase2 ownership retains its full original antecedent'
        self.world=[[tuple(self.B/2+(geo.L-self.B)*F(x) for x in p) for p in c['vertices']] for c in cover['cells']]
        # This exact diameter condition makes every occupied cell label injective.
        assert max(sum(((x-y)/self.B)**2 for x,y in zip(p,q)) for H in self.world for p in H for q in H)<1
        self.guard_path=None;self.roles={}
        if fresh:
            assert generic_mode and audit is None,'Fresh seeds require generic unguarded mode'
            assert self.root['cover_source']['sha256']==sha(COVER)
            assert sha(locate(self.root['cover_source']['path'],source))==sha(COVER)
            assert len(self.root['world'])==16 and all(polygon_equal(poly(a),b) for a,b in zip(self.root['world'],self.world))
            sys.path.insert(0,str(WORK/'geometry'));sys.path.insert(0,str(ROOT/'research/optimality/audit'))
            import audit_wall_kernel as wall
            from audit_center_cover import audit as audit_cover
            from fractions import Fraction as PureF
            assert sha(Path(wall.__file__))=='f442d798796e6017225dea528c9bcf7b4fbeb3c2c3e6262f68de2e43ff542660'
            assert wall.U==PureF(str(self.U));audit_cover(COVER)
            self.root_dependency_files.extend([Path(wall.__file__),ROOT/'research/optimality/audit/audit_center_cover.py'])
            owned=groups(self.root['groups']);assert set(owned)==set(self.mask)
            for owner,H in owned.items():
                assert H and len(set(H))==len(H)
                cell=[tuple(PureF(str(x/self.B)) for x in p) for p in self.world[owner]]
                for p in H:
                    assert len(p)==2 and all(0<=x<=geo.L for x in p)
                    point=tuple(PureF(str(x/self.B)) for x in p)
                    md=max(sum((x-y)**2 for x,y in zip(point,q)) for q in cell)
                    if md<PureF(1,4):ans=dict(passed=True,method='exact_disk',maximum_vertex_distance_squared=str(md))
                    else:
                        ans=wall.check_point(cell,point)
                        assert ans['passed'] and PureF(str(ans['strict_projection_margin']))>0
                    self.seed_checks.append(dict(owner=owner,unit_point=list(map(str,point)),**ans))
            state=dict(groups={j:geo.gift_hull(H) for j,H in owned.items()},cells={},constraints=[])
            assert set(map(int,self.root['cells']))==set(self.mask)
            bins=self.root['bins'];assert type(bins) is int and bins>0
            for owner in self.mask:
                rows=self.root['cells'][str(owner)];assert len(rows)==bins
                rr=[]
                for k,row in enumerate(rows):
                    a,b=map(F,row['interval']);assert a==F(k,bins) and b==F(k+1,bins)
                    width=min(sum(geo.cs(t)) for t in (a,b));h=self.B*width/2
                    # 1+2t-t^2-width*(1+t^2) is concave; its endpoint
                    # minima prove the all-angle legal-wall envelope.
                    assert 1-width+2*a-(1+width)*a*a>=0 and 1-width+2*b-(1+width)*b*b>=0
                    domain=clipped(self.world[owner],[(1,0,geo.L-h),(-1,0,-h),(0,1,geo.L-h),(0,-1,-h)])
                    assert polygon_equal(domain,poly(row['outer_domain'])) and row['outer_bounds']==[]
                    residual=[poly(P) for P in row['residual_polygons']]
                    assert len(residual)==int(bool(domain)) and (not domain or polygon_equal(residual[0],domain))
                    assert row['reference']==dict(kind='wall_seed',owner=owner,row=k)
                    rr.append(dict(row,interval=[a,b],outer_domain=domain,residual_polygons=residual))
                state['cells'][owner]=rr
            self.bootstrap=dict(kind='independently_verified_wall_seed',seed_vertices=len(self.seed_checks),angle_rows=len(self.mask)*bins,full_angle_domain=['0','1'])
        else:
            assert audit is not None,'An independently audited Phase2 source is required'
            r=json.loads(audit.read_text())
            assert r['status']=='PASS_INDEPENDENT_RESIDUAL_KERNEL_AUDIT' and r['source_sha256']==self.source_hash
            assert r['mask_index']==self.root['mask_index'] and not r.get('branch_condition')
            assert not self.root.get('branch')
            assert sha(COVER)==self.root['cover_sha256']==r['cover_sha256']
            dependency_roots=[Path(__file__).parent,WORK/'phase2/hull',WORK/'geometry']
            for name,value in r['dependencies'].items():
                matched=[p/name for p in dependency_roots if (p/name).is_file() and sha(p/name)==value]
                assert matched,'Root audit dependency changed: '+name
                self.root_dependency_files.append(matched[0])
            if r.get('rational_backend')=='gmp':
                binary=next((WORK/'phase3/deps/gmpy2').glob('gmpy2*.so'));assert sha(binary)==r['rational_binary_sha256']
            assert r['angle_rows_checked']==sum(len(c['rows']) for rnd in self.root['rounds'] for c in rnd['cells'])
            state=dict(groups={j:geo.gift_hull(poly(self.root['owned_points'][j])) for j in self.mask},cells={},constraints=[])
            latest={}
            for rnd in self.root['rounds']:
                for c in rnd['cells']:
                    if c['complete']:latest[c['owner']]=(rnd['index'],c)
            assert set(latest)==set(self.mask),'Every owner requires a completed source angle cover'
            for owner,(ridx,c) in latest.items():
                rr=[];cursor=F(0)
                for i,row in enumerate(c['rows']):
                    a,b=map(F,row['interval']);assert a==cursor and a<b<=1;cursor=b
                    residual=[poly(p) for p in row['residual_polygons']];vv=[p for q in residual for p in q]
                    outer,bounds=support_domain(vv,self.world[owner])
                    rr.append(dict(interval=[a,b],residual_polygons=residual,outer_domain=outer,outer_bounds=bounds,
                                   reference=dict(kind='phase2',round=ridx,owner=owner,row=i)))
                assert cursor==1;state['cells'][owner]=rr
            self.bootstrap=dict(kind='source_bound_prior_independent_ownership_audit',root_audit_sha256=sha(audit),latest_complete_round_by_owner={str(i):r for i,(r,c) in latest.items()},source_angle_rows_checked=r['angle_rows_checked'])
            if not generic_mode:
                self.guard_path=ROOT/'research/optimality/global_capture/local-capture-guards.json'
                assert sha(self.guard_path)==self.root['local_guard_source_sha256']
                guard=next((g for g in json.loads(self.guard_path.read_text())['guards'] if g['mask']==self.mask),None)
                self.roles={r['cell']:r for r in guard['roles']} if guard else {}
        self.initial=state

    def inside_guard(self,state):
        if not self.roles:return False
        for owner in self.mask:
            role=self.roles[owner];live=[r for r in state['cells'][owner] if r['residual_polygons']]
            if not live:return False
            for row in live:
                lo,hi=map(F,row['interval'])
                if not any(F(a)<=lo<hi<=F(b) for a,b in role['half_angle_intervals']):return False
                for p in [p for q in row['residual_polygons'] for p in poly(q)]:
                    if not all(F(a)<=x/self.B-self.U/2<=F(b) for x,(a,b) in zip(p,role['centered_box'])):return False
        return True

    def replay(self,path):
        fingerprint=sha(path)
        if fingerprint in self.cache:return copy.deepcopy(self.cache[fingerprint])
        d=json.loads(path.read_text());assert d['schema'] in ('exact_branch_owned_hull_v1','exact_generic_owned_hull_v1')
        assert d['mask']==self.mask and d['mask_index']==self.root['mask_index'] and F(d['U'])==self.U and F(d['B'])==self.B
        assert d['source']['sha256']==self.source_hash and sha(locate(d['source']['path'],path))==self.source_hash
        if d['schema']=='exact_generic_owned_hull_v1':assert self.generic_mode and d['guard_source'] is None
        else:assert not self.generic_mode and d['guard_source']['sha256']==sha(self.guard_path)
        if self.root_audit is not None and 'independent_audit_sha256' in d['source']:assert d['source']['independent_audit_sha256']==sha(self.root_audit)
        if d['parent']:
            parent=locate(d['parent']['path'],path);assert sha(parent)==d['parent']['sha256'];state=self.replay(parent)
        else:state=copy.deepcopy(self.initial)
        assert groups(d['initial']['groups'])==state['groups']
        assert {int(i):x for i,x in d['initial']['cell_references'].items()}=={j:[r['reference'] for r in state['cells'][j]] for j in self.mask}
        constraints=d['constraints']
        for inherited in state['constraints']:assert inherited in constraints
        for c in constraints:
            assert c['owner'] in self.mask
            if c.get('kind')=='half_angle':
                angle_range(c['owner'],constraints);continue
            assert any(map(F,c['normal']))
            if 'axis' in c:
                assert c['axis'] in (0,1) and c['keep'] in ('le','ge')
                n=[0,0];sgn=1 if c['keep']=='le' else -1;n[c['axis']]=sgn
                assert tuple(map(F,c['normal']))==tuple(n)
                assert F(c['upper_field'])==sgn*self.B*(self.U/2+F(c['bound_centered_unit']))
        state['constraints']=constraints;slabs=0;rows_count=0;promoted=0;complete_steps=0
        for index,step in enumerate(d['steps']):
            assert step['index']==index;owner=step['owner'];assert owner in self.mask
            prior=groups(step['prior_owned_hulls']);assert prior==state['groups'] and digest(prior)==step['prior_sha256']
            oldrows=state['cells'][owner];allplanes=[];allvertices=[];newrows=[]
            allowed_lo,allowed_hi=angle_range(owner,constraints);cursor=allowed_lo
            if 'allowed_half_angle' in step:assert list(map(F,step['allowed_half_angle']))==[allowed_lo,allowed_hi]
            old_by_ref={canon(row['reference']):row for row in oldrows};assert len(old_by_ref)==len(oldrows)
            partner_covers={}
            if 'prior_partner_pose_covers' in step:
                for j,rows in step['prior_partner_pose_covers'].items():
                    j=int(j);assert j in self.mask and j!=owner
                    normalized_rows=[dict(r,interval=list(map(F,r['interval'])),domain=poly(r['domain']),core=poly(r['core'])) for r in rows]
                    partner_covers[j]=normalized_rows
                    pa,pb=angle_range(j,constraints);pcursor=pa
                    predecessors={canon(r['reference']):r for r in state['cells'][j]}
                    for r in normalized_rows:
                        a,b=r['interval'];assert a==pcursor and a<b<=pb;pcursor=b
                        old=predecessors[canon(r['reference'])];oa,ob=map(F,old['interval']);assert oa<=a<b<=ob
                        cuts=center_conditions(j,constraints)
                        if 'self_hull_cuts' in r:
                            if r['self_hull_cuts']:
                                cuts+=self_hull.validate_cuts(prior[j],a,b,self.B,r['self_hull_cuts'])
                            else:assert not clipped(poly(old['outer_domain']),cuts)
                        domain=clipped(poly(old['outer_domain']),cuts)
                        assert polygon_equal(domain,r['domain'])
                        if domain:validate_core(r['core'],a,b,self.B)
                        else:assert not r['core']
                    assert pcursor==pb
                assert digest(partner_covers)==step['prior_partner_pose_covers_sha256']
            for rowidx,row in enumerate(step['rows']):
                old=old_by_ref[canon(row['prior_reference'])];a,b=map(F,row['interval']);assert a==cursor and a<b<=allowed_hi;cursor=b
                oa,ob=map(F,old['interval']);assert oa<=a<b<=ob and row['prior_reference']==old['reference']
                conditions=center_conditions(owner,constraints)
                if 'self_hull_cuts' in row:
                    if row['self_hull_cuts']:
                        conditions+=self_hull.validate_cuts(prior[owner],a,b,self.B,row['self_hull_cuts'])
                    else:assert not clipped(poly(old['outer_domain']),conditions)
                domain=clipped(poly(old['outer_domain']),conditions)
                assert polygon_equal(poly(row['input_domain']),domain)
                Q=poly(row['core_vertices']);residual=[poly(p) for p in row['residual_polygons']]
                if domain:
                    Q=validate_core(Q,a,b,self.B)
                    extra=[]
                    for region in row.get('collision_regions',[]):
                        j=region['partner'];assert j in partner_covers
                        P=poly(region['vertices']);cover=partner_covers[j]
                        if any(r['domain'] for r in cover):
                            checked=collision.validate_collision_polygon(Q,cover,domain,P)
                            assert checked['passed'],(path.name,index,rowidx,j,checked)
                        else:
                            # Complete allowed partner cover is independently
                            # empty: this is a direct conditional contradiction,
                            # not an unchecked empty universal quantifier.
                            assert region['status']=='EMPTY_PARTNER_COVER'
                            assert all(nx*p[0]+ny*p[1]<=h for nx,ny,h in bounded_rows(domain) for p in P)
                        extra.append(P)
                    ans=residual_cover(domain,{j:H for j,H in prior.items() if j!=owner},Q,a,b,self.U,residual,extra)
                    assert ans['passed'],(path.name,index,rowidx,ans);slabs+=ans['accepted_slabs']
                else:assert not residual and not Q
                vertices=[p for q in residual for p in q];allvertices.extend(vertices)
                expected=[]
                if vertices:
                    for x,y,h in geo.polygon_rows(Q):expected.append(((x,y),h+min(x*p[0]+y*p[1] for p in vertices)))
                actual=[(tuple(map(F,h['normal'])),F(h['upper'])) for h in row['common_core_halfplanes']]
                assert {normalized(n,h) for n,h in actual}=={normalized(n,h) for n,h in expected}
                allplanes.extend(actual)
                outer,bounds=support_domain(vertices,self.world[owner],row['outer_bounds'])
                assert polygon_equal(outer,poly(row['outer_domain']))
                assert row['reference']==dict(kind='phase3',node=d['node_id'],step=index,row=rowidx)
                newrows.append(row);rows_count+=1
            kernel=poly(step['common_owned_kernel'])
            if step['complete']:
                assert cursor==allowed_hi;complete_steps+=1
                for p in kernel:
                    assert all(0<=x<=geo.L for x in p)
                    assert all(n[0]*p[0]+n[1]*p[1]<=h for n,h in allplanes)
                state['cells'][owner]=newrows
                if allvertices:
                    original=geo.gift_hull(prior[owner]+kernel);assert original==poly(step['compression_source_hull'])
                    points=verify_convex_combinations(original,step['inner_grid_compression']);promoted+=len(points)
                    state['groups'][owner]=geo.gift_hull(prior[owner]+points)
                else:assert 'inner_grid_compression' not in step
            else:
                assert not kernel and index==len(d['steps'])-1
            print(json.dumps(dict(node=d['node_id'],step=index,owner=owner,complete=step['complete'],rows=len(newrows),slabs=slabs)),flush=True)
        final=d['final_state'];assert groups(final['groups'])==state['groups']
        assert F(final['U'])==self.U and F(final['B'])==self.B
        if self.generic_mode or 'mask_index' in final:
            assert final['mask_index']==self.root['mask_index']
        assert len(final['world'])==16 and all(polygon_equal(poly(a),b) for a,b in zip(final['world'],self.world))
        assert final['source']==d['source'] and final['guard_source']==d['guard_source']
        if self.generic_mode:assert final['guard']=={}
        assert final['constraints']==constraints and final['mask']==self.mask
        for owner in self.mask:
            reported=final['cells'][str(owner)];expected=state['cells'][owner];assert len(reported)==len(expected)
            for got,want in zip(reported,expected):
                assert got['reference']==want['reference'] and list(map(F,got['interval']))==list(map(F,want['interval']))
                assert [poly(p) for p in got['residual_polygons']]==[poly(p) for p in want['residual_polygons']]
                assert polygon_equal(poly(got['outer_domain']),poly(want['outer_domain']))
        contradiction=d['contradiction']
        if contradiction:
            if contradiction['kind']=='all_parent_poses_forbidden':
                owner=contradiction['owner'];s=d['steps'][contradiction['step']]
                assert s['complete'] and s['owner']==owner and all(not r['residual_polygons'] for r in s['rows'])
            elif contradiction['kind']=='owned_hulls_intersect':
                i,j=contradiction['owners'];assert i!=j and i in self.mask and j in self.mask and hulls_intersect(state['groups'][i],state['groups'][j])
            else:raise AssertionError('Unrecognized contradiction')
        captured=self.inside_guard(state)
        assert bool(d['closed'])==(bool(contradiction) or captured)
        assert not d['mask_exclusion_proved'] and not d['global_optimality_proved']
        self.records.append(dict(path=str(path),sha256=fingerprint,node=d['node_id'],complete_steps=complete_steps,rows=rows_count,
                                 arrangement_slabs=slabs,promoted_grid_vertices=promoted,constraints=constraints,
                                 branch_exclusion_proved=bool(contradiction),inside_local_guard=captured))
        self.cache[fingerprint]=copy.deepcopy(state)
        return state

def main():
    ap=argparse.ArgumentParser();ap.add_argument('receipt',type=Path);ap.add_argument('--root-audit',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    begin=time.monotonic();d=json.loads(args.receipt.read_text());source=locate(d['source']['path'],args.receipt)
    replay=Replay(source,args.root_audit,generic_mode=d['schema']=='exact_generic_owned_hull_v1');replay.replay(args.receipt.resolve())
    assert sha(source)==replay.source_hash
    for record in replay.records:assert sha(record['path'])==record['sha256'],'Audited node changed during replay'
    final_input=json.loads(args.receipt.read_text());assert sha(args.receipt)==replay.records[-1]['sha256']
    files=[Path(__file__),Path(geo.__file__),Path(rational.__file__),Path(collision.__file__),Path(self_hull.__file__),Path(__file__).with_name('audit_residual_kernel.py'),
           Path(__file__).with_name('arrangement_audit.py'),WORK/'geometry/audit_wall_kernel.py',WORK/'geometry/audit_kernel_survivor.py',*replay.root_dependency_files]
    unconditional=bool(replay.records[-1]['branch_exclusion_proved'] and not replay.records[-1]['constraints'])
    canonical=json.loads(COVER.read_text())['canonical_eleven_cell_subsets']
    transferred=[i for i,J in enumerate(canonical) if set(replay.mask)<=set(J) or set(replay.mask)<={15-j for j in J}] if unconditional else []
    if unconditional:assert replay.root['mask_index'] in transferred
    out=dict(required_antecedent_mask=replay.mask,transferred_canonical_mask_indices=transferred,continuum_canonical_masks_excluded=len(transferred),status='PASS_INDEPENDENT_GENERIC_HULL_AUDIT' if replay.generic_mode else 'PASS_INDEPENDENT_BRANCH_HULL_AUDIT',source_sha256=sha(args.receipt),mask_index=replay.root['mask_index'],mask=replay.mask,parent_Uplus=str(replay.U),parent_side=str(replay.B),cover_sha256=sha(COVER),constraints=replay.records[-1]['constraints'],final_state_sha256=digest(final_input['final_state']),root_sha256=sha(source),root_audit_sha256=sha(args.root_audit) if args.root_audit else None,bootstrap=replay.bootstrap,seed_ownership_checks=replay.seed_checks,
             dependencies={p.name:sha(p) for p in files},rational_backend=rational.BACKEND,rational_backend_version=rational.VERSION,
             rational_binary_sha256=sha(rational.BINARY) if rational.BINARY else None,nodes=replay.records,
             branch_exclusion_proved=replay.records[-1]['branch_exclusion_proved'],inside_local_guard=replay.records[-1]['inside_local_guard'],
             mask_exclusion_proved=unconditional,global_optimality_proved=False,seconds=time.monotonic()-begin)
    args.output.write_text(json.dumps(out,default=str,indent=2)+'\n');print(json.dumps(out,default=str,indent=2))
if __name__=='__main__':main()
