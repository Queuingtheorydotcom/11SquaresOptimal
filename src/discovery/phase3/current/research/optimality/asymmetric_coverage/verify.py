"""Exact mask-specific physical-feature charge coverage, without field symmetry.

The global half-turn quotient chooses a canonical mask, but no rotated cell
coverage is transferred inside an asymmetric charge field.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import argparse, hashlib, importlib.util, json, math, sys, time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/exact_checker'))
BASE=ROOT/'research/optimality/typed_coverage/verify.py'
BASE_SHA='1e56f02ee9201ac93f289cbe1c777abc3f9fa9a72345a711b91381b33aa4e7a3'
if hashlib.sha256(BASE.read_bytes()).hexdigest()!=BASE_SHA:
    raise ValueError('Audited typed geometry dependency changed')
spec=importlib.util.spec_from_file_location('audited_typed_geometry',BASE)
typed=importlib.util.module_from_spec(spec);spec.loader.exec_module(typed)
from exact_mixed import feature_coefficients
from majority_mixed import geometry
from majority_precompute import prepare_majority
from majority_low_cells import extract_low_cells
from majority_staged import patch_boxes
from majority_patches import true_charge
from integer_sweep import accumulate,need,trig
L,U,PARENT=typed.L,typed.U,typed.PARENT

def row_parameters(lo,hi):
    need(F(0)<=lo<hi<=F(1),'Angles must lie in the full quarter turn')
    t=(lo+hi)/2; c,s=trig(t); widths=[]; factors=[]
    for u in (lo,hi):
        cu,su=trig(u); dot=c*cu+s*su; cross=abs(c*su-s*cu)
        need(dot>0 and dot>=cross,'Angle interval too wide')
        widths.append(cu+su); factors.append(dot+cross)
    core=(PARENT-F(1,10**12))/max(factors)
    H=L/2-PARENT*min(widths)/2
    need(0<core<PARENT and PARENT-core*max(factors)>0,'Core not strict')
    need(core*(c+s)/2<=L/2-H<L/2,'Core escapes parent envelope')
    return t,core,H

def field_polygon(cover,cell):
    return [tuple(L/2+PARENT*(U-1)*(F(x)-F(1,2)) for x in p)
            for p in cover['cells'][cell]['vertices']]

def owned_generators(cover):
    """Every cell's generator is strictly inside every assigned unit parent.

    Convexity extends the exact vertex bound to the entire closed cell.
    Its generator's distance from the parent center is strictly below 1/2,
    so it belongs to the open inscribed disk, at every orientation.
    """
    result=[]
    for i,cell in enumerate(cover['cells']):
        need(cell['index']==i,'Misindexed ownership cell')
        center=tuple(map(F,cell['center']))
        radii=[(U-1)**2*sum((F(v)-g)**2 for v,g in zip(vertex,center))
               for vertex in cell['vertices']]
        need(radii and max(radii)<F(1,4),'Generator not strictly owned')
        result.append(tuple(L/2+PARENT*(U-1)*(v-F(1,2)) for v in center))
    need(len(result)==16 and len(set(result))==16,'Bad generator count')
    return result

def owned_points(cover,generators,offsets):
    """Rational points in every parent, certified against every cell vertex."""
    need(type(offsets) is list and 1<=len(offsets)<=33,'Bad ownership offsets')
    offsets=[tuple(map(F,p)) for p in offsets]
    need(all(len(p)==2 for p in offsets) and len(set(offsets))==len(offsets),
         'Malformed or duplicate ownership offsets')
    result=[]
    for cell,generator in zip(cover['cells'],generators):
        center=tuple(map(F,cell['center'])); group=[]
        for offset in offsets:
            radii=[sum(((U-1)*(F(v)-g)-z)**2 for v,g,z in zip(vertex,center,offset))
                   for vertex in cell['vertices']]
            need(radii and max(radii)<F(1,4),'Offset point is not strictly owned')
            group.append(tuple(g+PARENT*z for g,z in zip(generator,offset)))
        result.append(group)
    return result

def validate_owned_sites(cover,groups):
    need(type(groups) is list and len(groups)==16,'Expected sixteen owner groups')
    result=[]
    for cell,group in enumerate(groups):
        need(type(group) is list and 1<=len(group)<=65,'Bad owner point count')
        need(all(type(p) is list and len(p)==2 for p in group),'Malformed owned point')
        points=[tuple(map(F,p)) for p in group]
        need(len(set(points))==len(points),'Repeated owned point')
        for p in points:
            need(all(0<=v<=L for v in p),'Owned point outside field')
            for vertex in field_polygon(cover,cell):
                need(sum(((v-q)/PARENT)**2 for v,q in zip(vertex,p))<F(1,4),
                     'Owner point not strictly inside every assigned parent')
        result.append(points)
    return result

def conditioned_data(data,generators,mask,cell,threshold):
    """Zero-budget masks: all OTHER occupied generators are forbidden.

    A point in a strict subcore is in the actual parent's interior. Such a
    point cannot be owned by another parent in an interior-disjoint packing.
    The added point weights therefore vanish on every feasible packing.
    """
    points,pw,subsets,coefficients,D,majority=data
    owners=[j for j in mask if j!=cell]
    need(len(owners)<=10 and len(set(owners))==len(owners),'Invalid conditional owner subset')
    # Legacy one-point input is retained for independent replay controls.
    forbidden=[p for j in owners for p in
               ([generators[j]] if isinstance(generators[j][0],F) else generators[j])]
    new_D=math.lcm(D,*(v.denominator for p in forbidden for v in p))
    new_points=[tuple(v*(new_D//D) for v in p) for p in points]
    new_pw=list(pw); lookup={p:i for i,p in enumerate(new_points)}
    for p in forbidden:
        point=tuple(int(v*new_D) for v in p)
        if point not in lookup:
            lookup[point]=len(new_points);new_points.append(point);new_pw.append(0)
        new_pw[lookup[point]]+=threshold
    need(sum(new_pw)+sum(map(abs,coefficients))+sum(w for g,k,w in majority)<2**50,
         'Unsafe conditioned coefficient sum')
    return new_points,new_pw,subsets,coefficients,new_D,majority

def expand(c):
    need(F(c['L'])==L,'Wrong fixed field')
    D=c['coordinate_denominator']; W=c['weight_denominator']
    need(type(D) is int and D>0 and (L*D).denominator==1,'Bad coordinate denominator')
    need(type(W) is int and W>0,'Bad weight denominator')
    points=c['sites']; pw=c['point_weights']; LD=int(L*D)
    need(points and len(points)==len(pw),'Site/point-weight mismatch')
    need(all(len(p)==2 and all(type(x) is int and 0<=x<=LD for x in p) for p in points),'Bad physical site')
    need(len(set(map(tuple,points)))==len(points),'Duplicate physical sites')
    need(all(type(w) is int and w>=0 for w in pw),'Bad physical point weight')
    subsets=[]; coefficients=[]; majority=[]; budget=sum(pw)
    for atom in c['features']:
        group=atom['indices']; k=atom['threshold']; w=atom['weight']; kind=atom['kind']
        need(kind in ('floor','threshold','majority_hull'),'Unsupported physical feature')
        need(type(w) is int and w>=0,'Bad physical feature weight')
        need(1<=len(group)<=7 and type(k) is int and 1<=k<=len(group),'Bad support/threshold')
        need(len(set(group))==len(group) and all(type(i) is int and 0<=i<len(points) for i in group),'Bad or repeated support index')
        need(not atom.get('multiset',False),'Repeated slots are not supported here')
        if kind=='majority_hull':
            need(len(group)==2*k-1 and k<=4,'TRUE support must have 2k-1 distinct sites')
            budget+=w
            if w: majority.append((tuple(group),k,w))
        else:
            budget+=(len(group)//k)*w
            basis=feature_coefficients(len(group),k,kind)
            if w:
                for j in range(k,len(group)+1):
                    coefficient=basis[j]*w
                    if coefficient:
                        for part in combinations(group,j):
                            subsets.append(tuple(part)); coefficients.append(coefficient)
    need(type(c['budget_units']) is int and budget==c['budget_units'],'Physical budget mismatch')
    need(sum(pw)+sum(map(abs,coefficients))+sum(w for g,k,w in majority)<2**50,'Unsafe coefficient sum')
    return list(map(tuple,points)),list(pw),subsets,coefficients,D,majority

def verify_interval(data,prepared,world,lo,hi,threshold,node_limit):
    t,core,H=row_parameters(lo,hi); poly=world
    for axis in (0,1):
        poly=typed.clip(poly,axis,L/2-H,True)
        poly=typed.clip(poly,axis,L/2+H,False)
    if not poly:return dict(status='PASS_EMPTY',interval=[lo,hi])
    if not typed.twice_area(poly):return dict(status='UNRESOLVED_DEGENERATE_DOMAIN',interval=[lo,hi])
    # The majority geometry engine handles an empty event table and provides
    # full projection metadata. A zero-weight singleton activates that engine
    # for discrete-only fields without adding any charge or budget.
    geometry_data=data if data[-1] else (*data[:5],[((0,),1,0)])
    geometry_prepared=prepared if data[-1] else [()]
    arrays,meta=geometry(*geometry_data,t,core,H,meta=True,subdivisions=4,
                         domain_conditional=False,prepared=geometry_prepared)
    C,S,R,scale=(meta[k] for k in ('C','S','R','scale'))
    local=[(scale*(C*(x-L/2)+S*(y-L/2)),scale*(-S*(x-L/2)+C*(y-L/2))) for x,y in poly]
    arrays,meta=typed.restrict_arrays(meta,local)
    minimum,cells,winner=map(int,accumulate(*arrays))
    out=dict(interval=[lo,hi],core_side=core,reference_half_angle=t,
             parent_center_halfwidth=H,proxy_minimum=minimum,generic_cells=cells)
    if minimum>=threshold:return dict(out,status='PASS_STAIRCASE')
    boxes=extract_low_cells(arrays,meta,threshold).merged_boxes()
    patched=patch_boxes(data,meta,boxes,threshold,prepared,node_limit)
    if patched['status']=='PASS':return dict(out,status='PASS_TRUE_PATCH',patches=patched)
    if patched['status']=='COUNTEREXAMPLE':
        answer=patched['answer']; x,y=map(F,answer['world_center']); c,s=trig(t)
        radius=PARENT*(c+s)/2
        if radius<=x<=L-radius and radius<=y<=L-radius:
            point=tuple(map(F,answer['point'])); half=PARENT*scale*R/2; d=half.denominator
            charge=true_charge(data,[(u*d,v*d) for u,v in meta['uv']],int(half*d),tuple(v*d for v in point))
            if charge<threshold:
                return dict(out,status='REFUTED_BY_LEGAL_PARENT',patches=patched,
                            parent_witness=dict(center=[x,y],half_angle=t,side=PARENT,
                                                charge_units=charge,required_units=threshold))
    return dict(out,status='UNRESOLVED_'+patched['status'],patches=patched)

def run(args):
    global U,PARENT
    packet=json.loads(args.packet.read_text()); c=packet['certificate']
    cover=json.loads(typed.COVER.read_text())
    need(packet['cover_sha256']==typed.sha(typed.COVER)==typed.COVER_SHA256,'Audited cover changed')
    U=F(packet['parent_Uplus'])
    need(F(19377,5000)<=U<=typed.U,'Parent container outside audited contraction range')
    PARENT=L/U
    index=packet['mask_index']; mask=packet['mask']; gamma=packet['threshold_units']
    need(type(index) is int and 0<=index<len(cover['canonical_eleven_cell_subsets'])
         and mask==cover['canonical_eleven_cell_subsets'][index],'Wrong canonical mask')
    need(len(gamma)==16 and all(type(v) is int and v>=0 for v in gamma),'Bad cell thresholds')
    need(len(mask)==11 and len(set(mask))==11,'Bad occupied mask')
    data=expand(c)
    ownership=packet.get('conditional_ownership','none')
    need(ownership in ('none','cell_generators','cell_owned_points'),'Unsupported conditioning')
    need(('ownership_offsets_unit' not in packet and 'ownership_points_field' not in packet)
         or ownership=='cell_owned_points',
         'Offsets require explicit owned-point conditioning')
    generators=owned_generators(cover) if ownership!='none' else None
    if ownership=='cell_owned_points':
        need(('ownership_offsets_unit' in packet)!=('ownership_points_field' in packet),
             'Specify exactly one owned-point representation')
        owned=(owned_points(cover,generators,packet['ownership_offsets_unit'])
               if 'ownership_offsets_unit' in packet else
               validate_owned_sites(cover,packet['ownership_points_field']))
    else: owned=generators
    owner_support=packet.get('conditional_owner_support',mask)
    need(type(owner_support) is list and len(set(owner_support))==len(owner_support)
         and all(type(i) is int for i in owner_support) and set(owner_support)<=set(mask),
         'Conditional owners must be an occupied subset')
    need('conditional_owner_support' not in packet or ownership!='none',
         'Owner support requires ownership conditioning')
    surplus=sum(gamma[i] for i in mask)-c['budget_units']; need(surplus>0,'No conditional contradiction')
    selected=mask if args.cells is None else list(map(int,args.cells.split(',')))
    need(selected and len(set(selected))==len(selected) and set(selected)<=set(mask),'Bad physical cell selection')
    need(args.bins>=2 and args.max_depth>=0 and args.max_rows>0 and args.seconds>0,'Bad resource bound')
    start=time.monotonic(); records=[]; done=[]; stopped=False
    def snapshot():
        complete=set(selected)==set(mask) and len(done)==11 and all(x['complete'] for x in done)
        out=dict(status='PASS_EXACT_ASYMMETRIC_MASK_EXCLUSION' if complete else 'INCOMPLETE_ASYMMETRIC_COVERAGE',
                 global_optimality_proved=False,continuum_masks_excluded=int(complete),
                 mask_index=index,mask=mask,packet_sha256=typed.sha(args.packet),cover_sha256=typed.COVER_SHA256,
                 parent_Uplus=U,parent_side=PARENT,
                 conditional_ownership=ownership,owned_generators=generators,owned_points=owned,
                 conditional_owner_support=owner_support,
                 budget_units=c['budget_units'],threshold_sum_units=sum(gamma[i] for i in mask),
                 counting_surplus_units=surplus,within_field_symmetry_transfer=False,full_quarter_turn=True,
                 rows=len(records),seconds=time.monotonic()-start,cells=done,records=records,
                 dependencies={str(p.relative_to(ROOT)):typed.sha(p) for p in
                               [Path(__file__),BASE,*sorted((ROOT/'research/exact_checker').glob('*.py'))]},
                 scope='Only complete coverage of all eleven physical occupied cells excludes this mask at the reported rational parent_Uplus. Partial rows and counterexamples are not exclusions. Any transfer to the algebraic target requires a separate exact upper-bound comparison.')
        typed.save(args.output,out);return out
    for cell in selected:
        world=field_polygon(cover,cell)
        cell_data=conditioned_data(data,owned,owner_support,cell,gamma[cell]) if generators else data
        prepared=prepare_majority(cell_data)
        pending=[(F(i,args.bins),F(i+1,args.bins),0) for i in reversed(range(args.bins))]
        accepted=[]; unresolved=[]
        while pending:
            if len(records)>=args.max_rows or time.monotonic()-start>=args.seconds:
                stopped=True;break
            lo,hi,depth=pending.pop(); begin=time.monotonic()
            answer=verify_interval(cell_data,prepared,world,lo,hi,gamma[cell],args.patch_nodes)
            records.append(dict(cell=cell,depth=depth,seconds=time.monotonic()-begin,**answer))
            if answer['status'].startswith('PASS'):accepted.append((lo,hi))
            elif answer['status']=='REFUTED_BY_LEGAL_PARENT':
                unresolved.append((lo,hi));stopped=True;break
            elif depth<args.max_depth:
                mid=(lo+hi)/2;pending.extend([(mid,hi,depth+1),(lo,mid,depth+1)])
            else:unresolved.append((lo,hi))
            if len(records)%50==0:
                snapshot()
                print(json.dumps(dict(cell=cell,rows=len(records),accepted=len(accepted),pending=len(pending),
                                      unresolved=len(unresolved),seconds=time.monotonic()-start)),flush=True)
        cursor=F(0)
        for lo,hi in sorted(accepted):
            if lo!=cursor:break
            cursor=hi
        done.append(dict(cell=cell,threshold_units=gamma[cell],complete=not pending and not unresolved and cursor==1,
                         accepted=sorted(accepted),pending=pending,unresolved=unresolved))
        snapshot()
        if stopped:break
    out=snapshot()
    print(json.dumps({k:v for k,v in out.items() if k not in ('cells','records','dependencies','owned_generators','owned_points')},default=str,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('packet',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cells');p.add_argument('--bins',type=int,default=32)
    p.add_argument('--max-depth',type=int,default=14);p.add_argument('--max-rows',type=int,default=4000)
    p.add_argument('--seconds',type=float,default=600);p.add_argument('--patch-nodes',type=int,default=5000)
    run(p.parse_args())
