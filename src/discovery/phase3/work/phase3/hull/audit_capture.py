#!/usr/bin/env python3
"""Independent replay of polygon-core, branch-conditional hull induction.

The root ownership/localization premise must have a source-bound independent
root audit. Parent node files are recursively replayed, never trusted by status.
All node geometry uses separate hull/vertical-arrangement algorithms; core
containment uses endpoint derivatives and completed-square positivity.
"""
from pathlib import Path
import argparse,copy,hashlib,json,os,time
import rational
from rational import F
import arrangement_audit as geo
from audit_residual_kernel import verify_convex_combinations
if not __debug__:raise RuntimeError('Assertions must be enabled')
WORK=Path(__file__).resolve().parents[2]
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
    H=geo.gift_hull(Q);assert len(H)==len(Q) and set(H)==set(Q) and geo.twice_area(H)>0
    for x,y in Q:
        for sign in (-1,1):
            assert positive_quadratic(B/2-sign*x,-2*sign*y,B/2+sign*x,a,b)
            assert positive_quadratic(B/2-sign*y,2*sign*x,B/2+sign*y,a,b)
    return H
def clipped(domain,extra):
    if not domain:return []
    return geo.intersection_polygon(geo.polygon_rows(geo.gift_hull(domain))+extra)
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
def residual_cover(domain,prior,Q,a,b,U,residual):
    B=geo.L/U;h=B*min(sum(geo.cs(t)) for t in (a,b))/2
    domain=clipped(domain,[(1,0,geo.L-h),(-1,0,-h),(0,1,geo.L-h),(0,-1,-h)])
    if not domain:return dict(passed=True,accepted_slabs=0)
    assert geo.twice_area(domain)>0,'Nonempty degenerate domain requires a separate line audit'
    negative=[(-x,-y) for x,y in Q]
    forbidden=[geo.gift_hull([(p[0]+q[0],p[1]+q[1]) for p in K for q in negative]) for K in prior.values() if K]
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
    def __init__(self,source,audit):
        self.source=source;self.source_hash=sha(source);self.root=json.loads(source.read_text());self.cache={};self.records=[]
        r=json.loads(audit.read_text())
        assert r['status']=='PASS_INDEPENDENT_RESIDUAL_KERNEL_AUDIT' and r['source_sha256']==self.source_hash
        assert r['mask_index']==self.root['mask_index'] and not r.get('branch_condition')
        self.root_audit=audit;self.U=F(self.root['parent_Uplus']);self.B=geo.L/self.U;self.mask=self.root['mask']
        cover=json.loads(COVER.read_text());assert sha(COVER)==self.root['cover_sha256']==r['cover_sha256']
        assert self.mask==cover['canonical_eleven_cell_subsets'][self.root['mask_index']]
        self.world=[[tuple(self.B/2+(geo.L-self.B)*F(x) for x in p) for p in c['vertices']] for c in cover['cells']]
        self.guard_path=ROOT/'research/optimality/global_capture/local-capture-guards.json'
        assert sha(self.guard_path)==self.root['local_guard_source_sha256']
        guard=next((g for g in json.loads(self.guard_path.read_text())['guards'] if g['mask']==self.mask),None)
        self.roles={r['cell']:r for r in guard['roles']} if guard else {}
        last=self.root['rounds'][-1];assert last['complete'] and len(last['cells'])==len(self.mask)
        state=dict(groups={j:geo.gift_hull(poly(self.root['owned_points'][j])) for j in self.mask},cells={},constraints=[])
        for c in last['cells']:
            rr=[]
            for i,row in enumerate(c['rows']):
                residual=[poly(p) for p in row['residual_polygons']];vv=[p for q in residual for p in q]
                outer,bounds=support_domain(vv,self.world[c['owner']])
                rr.append(dict(interval=list(map(F,row['interval'])),residual_polygons=residual,outer_domain=outer,outer_bounds=bounds,
                               reference=dict(kind='phase2',round=last['index'],owner=c['owner'],row=i)))
            state['cells'][c['owner']]=rr
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
        d=json.loads(path.read_text());assert d['schema']=='exact_branch_owned_hull_v1'
        assert d['mask']==self.mask and d['mask_index']==self.root['mask_index'] and F(d['U'])==self.U and F(d['B'])==self.B
        assert d['source']['sha256']==self.source_hash and sha(locate(d['source']['path'],path))==self.source_hash
        assert d['guard_source']['sha256']==sha(self.guard_path)
        if d['parent']:
            parent=locate(d['parent']['path'],path);assert sha(parent)==d['parent']['sha256'];state=self.replay(parent)
        else:state=copy.deepcopy(self.initial)
        assert groups(d['initial']['groups'])==state['groups']
        assert {int(i):x for i,x in d['initial']['cell_references'].items()}=={j:[r['reference'] for r in state['cells'][j]] for j in self.mask}
        constraints=d['constraints']
        for inherited in state['constraints']:assert inherited in constraints
        for c in constraints:
            assert c['owner'] in self.mask and any(map(F,c['normal']))
            if 'axis' in c:
                assert c['axis'] in (0,1) and c['keep'] in ('le','ge')
                n=[0,0];sgn=1 if c['keep']=='le' else -1;n[c['axis']]=sgn
                assert tuple(map(F,c['normal']))==tuple(n)
                assert F(c['upper_field'])==sgn*self.B*(self.U/2+F(c['bound_centered_unit']))
        state['constraints']=constraints;slabs=0;rows_count=0;promoted=0;complete_steps=0
        for index,step in enumerate(d['steps']):
            assert step['index']==index;owner=step['owner'];assert owner in self.mask
            prior=groups(step['prior_owned_hulls']);assert prior==state['groups'] and digest(prior)==step['prior_sha256']
            oldrows=state['cells'][owner];allplanes=[];allvertices=[];newrows=[];cursor=F(0)
            for rowidx,row in enumerate(step['rows']):
                old=oldrows[rowidx];a,b=map(F,row['interval']);assert a==cursor and a<b<=1;cursor=b
                assert [a,b]==list(map(F,old['interval'])) and row['prior_reference']==old['reference']
                conditions=[(*tuple(map(F,c['normal'])),F(c['upper_field'])) for c in constraints if c['owner']==owner]
                domain=clipped(poly(old['outer_domain']),conditions)
                assert polygon_equal(poly(row['input_domain']),domain)
                Q=poly(row['core_vertices']);residual=[poly(p) for p in row['residual_polygons']]
                if domain:
                    Q=validate_core(Q,a,b,self.B)
                    ans=residual_cover(domain,{j:H for j,H in prior.items() if j!=owner},Q,a,b,self.U,residual)
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
                assert len(newrows)==len(oldrows) and cursor==1;complete_steps+=1
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
    ap=argparse.ArgumentParser();ap.add_argument('receipt',type=Path);ap.add_argument('--root-audit',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    begin=time.monotonic();d=json.loads(args.receipt.read_text());source=locate(d['source']['path'],args.receipt)
    replay=Replay(source,args.root_audit);replay.replay(args.receipt.resolve())
    files=[Path(__file__),Path(geo.__file__),Path(rational.__file__),Path(__file__).with_name('audit_residual_kernel.py')]
    out=dict(status='PASS_INDEPENDENT_BRANCH_HULL_AUDIT',source_sha256=sha(args.receipt),root_sha256=sha(source),root_audit_sha256=sha(args.root_audit),
             dependencies={p.name:sha(p) for p in files},rational_backend=rational.BACKEND,rational_backend_version=rational.VERSION,
             rational_binary_sha256=sha(rational.BINARY) if rational.BINARY else None,nodes=replay.records,
             branch_exclusion_proved=replay.records[-1]['branch_exclusion_proved'],inside_local_guard=replay.records[-1]['inside_local_guard'],
             mask_exclusion_proved=False,global_optimality_proved=False,seconds=time.monotonic()-begin)
    args.output.write_text(json.dumps(out,default=str,indent=2)+'\n');print(json.dumps(out,default=str,indent=2))
if __name__=='__main__':main()
