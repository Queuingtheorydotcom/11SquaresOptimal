"""Exact conditional charge coverage for the symmetric sixteen-cell cover.

An accepted mask is a genuine exclusion, but is not global optimality.
All unfinished intervals and lower-dimensional domains remain unresolved.
The existing uniform-count validator is intentionally not applicable: this
module checks a different, explicitly cell-dependent counting inequality.
"""
from pathlib import Path
from fractions import Fraction as F
from bisect import bisect_left, bisect_right
from collections import defaultdict
from itertools import combinations
from math import comb
import argparse, copy, hashlib, json, sys, time
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
KERNEL = ROOT/'research/exact_checker'
sys.path.insert(0, str(KERNEL))
from exact_mixed import expand as expand_discrete
from majority_mixed import geometry
from majority_precompute import prepare_majority
from majority_low_cells import extract_low_cells
from majority_staged import patch_boxes
from majority_patches import true_charge
from integer_sweep import accumulate, trig, need

L = F(191,50)
U = F(969271,250000)
PARENT = L/U
COVER = ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
COVER_SHA256 = 'df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value, indent=2, default=str)+'\n'); tmp.replace(path)

def twice_area(poly):
    return sum(x*v-y*u for (x,y),(u,v) in zip(poly,poly[1:]+poly[:1])) if poly else 0

def clip(poly, axis, bound, greater):
    out=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        a=p[axis]-bound; b=q[axis]-bound
        ina=a>=0 if greater else a<=0
        inb=b>=0 if greater else b<=0
        if ina: out.append(p)
        if ina != inb:
            r=a/(a-b); out.append(tuple(p[j]+r*(q[j]-p[j]) for j in range(2)))
    clean=[]
    for p in out:
        if not clean or clean[-1]!=p: clean.append(p)
    if len(clean)>1 and clean[0]==clean[-1]: clean.pop()
    return clean

def expand_features(c):
    """Validate orbit budgets, then replace threshold proxies by TRUE charges.

    This is the algebraic expansion used in majority_mixed.validate, without
    asserting the unrelated uniform inequality 11*minimum > budget.
    """
    need(F(c['L'])==L, 'Wrong fixed field')
    need(type(c['weight_denominator']) is int and c['weight_denominator']>0,
         'Invalid weight denominator')
    proxy=copy.deepcopy(c); majority=[]; remove=[]
    for atom in proxy['charge_orbits']:
        if atom.get('kind')!='majority_hull': continue
        groups=atom['sets']; k=atom['threshold']; w=atom['weight']
        need(groups and type(k) is int and 1<=k<=4, 'Invalid majority threshold')
        need(not atom.get('multiset',False), 'TRUE groups cannot have repeated sites')
        need(all(len(g)==2*k-1 and len(set(g))==len(g) for g in groups),
             'Wrong TRUE group size')
        atom['kind']='threshold'
        if w:
            for group in groups:
                majority.append((tuple(group),k,w))
                for j in range(k,len(group)+1):
                    coefficient=(-1)**(j-k)*comb(j-1,k-1)*w
                    remove.extend((tuple(sorted(part)),coefficient)
                                  for part in combinations(group,j))
    points,pw,subsets,coefficients,D=expand_discrete(proxy)
    totals=defaultdict(int)
    for g,w in zip(subsets,coefficients): totals[tuple(sorted(g))]+=w
    for g,w in remove: totals[g]-=w
    surviving=[(g,w) for g,w in totals.items() if w]
    return points,pw,[g for g,w in surviving],[w for g,w in surviving],D,majority

def restrict_arrays(meta, poly):
    """Conservative slab queries, with every polygon x vertex inserted."""
    poly=[tuple(map(F,p)) for p in poly]
    need(len(poly)>=3 and twice_area(poly)!=0, 'Non-full-dimensional polygon')
    rect=meta['rect']; weights=meta['weights']
    xe=sorted(set(meta['xe'])|{p[0] for p in poly})
    ye=sorted(set(meta['ye'])|{p[1] for p in poly})
    xi={v:i for i,v in enumerate(xe)}; yi={v:i for i,v in enumerate(ye)}
    events=np.array(sorted([(xi[r[0]],i,1) for i,r in enumerate(rect)]+
                           [(xi[r[1]],i,-1) for i,r in enumerate(rect)]),dtype=np.int64).reshape((-1,3))
    yl=np.array([yi[r[2]] for r in rect],dtype=np.int64)
    yh=np.array([yi[r[3]] for r in rect],dtype=np.int64)
    first=np.full(len(xe)-1,-1,dtype=np.int64); last=first.copy(); edges=[]
    for (x,y),(u,v) in zip(poly,poly[1:]+poly[:1]):
        if x==u: continue
        if u<x: x,y,u,v=u,v,x,y
        slope=(v-y)/(u-x); edges.append((x,u,slope,y-slope*x))
    left=min(p[0] for p in poly); right=max(p[0] for p in poly)
    for k,(a,b) in enumerate(zip(xe,xe[1:])):
        if a<left or b>right: continue
        values=[]
        for x,u,m,n in edges:
            if x<=a and b<=u: values.extend((m*a+n,m*b+n))
        need(len(values)==4, 'Unexpected polygon edge count')
        first[k]=bisect_right(ye,min(values))-1
        last[k]=bisect_left(ye,max(values))
        need(0<=first[k]<last[k]<=len(ye)-1, 'Invalid restricted query range')
    arrays=(len(ye)-1,events[:,0],events[:,1],events[:,2],yl,yh,
            np.array(weights,dtype=np.int64),first,last)
    return arrays,dict(meta,poly=poly,xe=xe,ye=ye)

def row_parameters(lo,hi):
    need(F(0)<=lo<hi<=F(1), 'Angles must lie in the full quarter turn')
    t=(lo+hi)/2; c,s=trig(t); widths=[]; factors=[]
    for u in (lo,hi):
        cu,su=trig(u); dot=c*cu+s*su; cross=abs(c*su-s*cu)
        need(dot>0 and dot>=cross, 'Angle interval too wide')
        widths.append(cu+su); factors.append(dot+cross)
    # |delta|<=pi/4: cos(delta)+|sin(delta)| maximizes at an endpoint.
    core=(PARENT-F(1,10**12))/max(factors)
    H=L/2-PARENT*min(widths)/2
    need(0<core<PARENT and PARENT-core*max(factors)>0, 'Core not strict')
    need(core*(c+s)/2<=L/2-H<L/2, 'Core escapes parent envelope')
    return t,core,H

def field_polygon(cover,cell):
    # q=(U-1)*(u-1/2), x_field=L/2+PARENT*q; PARENT is fixed.
    return [tuple(L/2+PARENT*(U-1)*(F(x)-F(1,2)) for x in p)
            for p in cover['cells'][cell]['vertices']]

def verify_interval(data,prepared,world,lo,hi,threshold,node_limit):
    t,core,H=row_parameters(lo,hi)
    poly=world
    for axis in (0,1):
        poly=clip(poly,axis,L/2-H,True)
        poly=clip(poly,axis,L/2+H,False)
    if not poly: return dict(status='PASS_EMPTY',interval=[lo,hi])
    if not twice_area(poly): return dict(status='UNRESOLVED_DEGENERATE_DOMAIN',interval=[lo,hi])
    arrays,meta=geometry(*data,t,core,H,meta=True,subdivisions=4,
                         domain_conditional=False,prepared=prepared)
    C,S,scale=(meta[k] for k in ('C','S','scale'))
    local=[(scale*(C*(x-L/2)+S*(y-L/2)),
            scale*(-S*(x-L/2)+C*(y-L/2))) for x,y in poly]
    arrays,meta=restrict_arrays(meta,local)
    minimum,cells,winner=map(int,accumulate(*arrays))
    out=dict(interval=[lo,hi],core_side=core,reference_half_angle=t,
             parent_center_halfwidth=H,proxy_minimum=minimum,generic_cells=cells)
    if minimum>=threshold: return dict(out,status='PASS_STAIRCASE')
    low=extract_low_cells(arrays,meta,threshold); boxes=low.merged_boxes()
    # Discrete-only queries use the same patch mechanism with an empty TRUE list.
    if not data[-1]:
        return dict(out,status='UNRESOLVED_DISCRETE_PROXY',low_boxes=len(boxes))
    patched=patch_boxes(data,meta,boxes,threshold,prepared,node_limit)
    if patched['status']=='PASS': return dict(out,status='PASS_TRUE_PATCH',patches=patched)
    if patched['status']=='COUNTEREXAMPLE':
        answer=patched['answer']; x,y=map(F,answer['world_center'])
        c,s=trig(t); radius=PARENT*(c+s)/2
        if radius<=x<=L-radius and radius<=y<=L-radius:
            point=tuple(map(F,answer['point']))
            parent_half=PARENT*meta['scale']*meta['R']/2
            denominator=parent_half.denominator
            parent_uv=[(u*denominator,v*denominator) for u,v in meta['uv']]
            parent_point=tuple(v*denominator for v in point)
            parent_charge=true_charge(data,parent_uv,int(parent_half*denominator),parent_point)
            if parent_charge<threshold:
                return dict(out,status='REFUTED_BY_LEGAL_PARENT',patches=patched,
                            parent_witness=dict(center=[x,y],half_angle=t,
                                                side=PARENT,charge_units=parent_charge,
                                                required_units=threshold))
    return dict(out,status='UNRESOLVED_'+patched['status'],patches=patched)

def run(args):
    packet=json.loads(args.packet.read_text()); c=packet['certificate']
    cover=json.loads(COVER.read_text())
    need(packet['cover_sha256']==sha(COVER)==COVER_SHA256, 'Audited cover digest mismatch')
    need(F(packet['parent_Uplus'])==U, 'Unexpected containing square')
    index=packet['mask_index']; mask=packet['mask']
    need(type(index) is int and 0<=index<len(cover['canonical_eleven_cell_subsets'])
         and mask==cover['canonical_eleven_cell_subsets'][index], 'Mask mismatch')
    need(len(mask)==11 and len(set(mask))==11, 'Invalid occupied cells')
    gamma=packet['threshold_units']
    need(len(gamma)==16 and all(type(x) is int and x>=0 for x in gamma), 'Invalid thresholds')
    data=expand_features(c); prepared=prepare_majority(data)
    surplus=sum(gamma[i] for i in mask)-c['budget_units']
    need(surplus>0, 'No conditional counting contradiction')
    original_cells=list(range(16)) if args.all_cells else mask
    representatives={i:min(i,15-i) for i in original_cells}
    required={r:max(gamma[i] for i in original_cells if representatives[i]==r)
              for r in set(representatives.values())}
    # expand_features verifies equal-weight complete D4 orbits. The pinned
    # cover has exact cell involution i -> 15-i. Half-turn leaves t unchanged
    # modulo the square's quarter-turn symmetry, hence this transfer is exact.
    selected=sorted(required) if args.cells is None else list(map(int,args.cells.split(',')))
    need(selected and len(set(selected))==len(selected) and set(selected)<=set(required), 'Invalid selected representatives')
    need(args.bins>=2 and args.max_depth>=0 and args.max_rows>0 and args.seconds>0, 'Invalid resource bound')
    start=time.monotonic(); records=[]; row_count=0; done=[]; stopped=False
    for cell in selected:
        pending=[(F(i,args.bins),F(i+1,args.bins),0) for i in reversed(range(args.bins))]
        accepted=[]; unresolved=[]; world=field_polygon(cover,cell)
        while pending:
            if row_count>=args.max_rows or time.monotonic()-start>=args.seconds:
                stopped=True; break
            lo,hi,depth=pending.pop(); begin=time.monotonic()
            answer=verify_interval(data,prepared,world,lo,hi,required[cell],args.patch_nodes)
            row_count+=1
            records.append(dict(cell=cell,depth=depth,seconds=time.monotonic()-begin,**answer))
            if answer['status'].startswith('PASS'): accepted.append((lo,hi))
            elif answer['status']=='REFUTED_BY_LEGAL_PARENT':
                unresolved.append((lo,hi)); stopped=True; break
            elif depth<args.max_depth:
                mid=(lo+hi)/2; pending.extend([(mid,hi,depth+1),(lo,mid,depth+1)])
            else: unresolved.append((lo,hi))
            if row_count%25==0:
                print(json.dumps(dict(cell=cell,rows=row_count,accepted=len(accepted),pending=len(pending),
                                      unresolved=len(unresolved),seconds=time.monotonic()-start)),flush=True)
        covered=sorted(accepted); cursor=F(0)
        for lo,hi in covered:
            if lo!=cursor: break
            cursor=hi
        complete=not pending and not unresolved and cursor==1
        done.append(dict(cell=cell,required_units=required[cell],complete=complete,
                         accepted=covered,unresolved=unresolved,pending=pending))
        if stopped: break
    full=set(selected)==set(required) and len(done)==len(required) and all(x['complete'] for x in done)
    excluded=[index] if full else []
    if full and args.all_cells:
        excluded=[j for j,m in enumerate(cover['canonical_eleven_cell_subsets'])
                  if sum(gamma[i] for i in m)>c['budget_units']]
    result=dict(status='PASS_EXACT_MASK_EXCLUSION' if full else 'INCOMPLETE_CONDITIONAL_COVERAGE',
                global_optimality_proved=False,continuum_masks_excluded=len(excluded),
                excluded_mask_indices=excluded,
                mask_index=index,mask=mask,parent_Uplus=U,packet_sha256=sha(args.packet),
                cover_sha256=sha(COVER),budget_units=c['budget_units'],
                threshold_sum_units=sum(gamma[i] for i in mask),counting_surplus_units=surplus,
                full_quarter_turn=True,half_turn_transfer=representatives,
                representative_threshold_units=required,all_sixteen_cells_requested=args.all_cells,
                rows=row_count,seconds=time.monotonic()-start,
                cells=done,records=records,
                dependencies={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),*sorted(KERNEL.glob('*.py'))]},
                scope='Each PASS row covers every center in its closed cell and all orientations in its interval. Only complete eleven-cell coverage excludes this mask.')
    save(args.output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','cells','dependencies')},default=str,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('packet',type=Path); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cells'); p.add_argument('--bins',type=int,default=32)
    p.add_argument('--all-cells',action='store_true',help='Cover all 16 cells via 8 half-turn representatives')
    p.add_argument('--max-depth',type=int,default=12)
    p.add_argument('--max-rows',type=int,default=2000)
    p.add_argument('--seconds',type=float,default=300)
    p.add_argument('--patch-nodes',type=int,default=5000)
    run(p.parse_args())
