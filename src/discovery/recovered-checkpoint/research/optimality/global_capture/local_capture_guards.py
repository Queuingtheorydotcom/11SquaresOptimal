#!/usr/bin/env python3
"""Rational inner guards for the four canonical Trump capture masks.

Acceptance is conditional on actual packing feasibility and a proved S<=alpha
premise. This checker never asserts that arbitrary global cases reach a guard.
"""
from fractions import Fraction as F
from pathlib import Path
from copy import deepcopy
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'work/construction'))
from verify_trump import E,u,M,I,configuration,polynomial_interval
from verify_center_cover import SIDE_UPPER

RHO=F(1,248)
RELATIVE=RHO/2
DEN=10**12
SOURCE_PATHS=['work/construction/verify_trump.py',
 'research/classical/trump-local-weighted-coordinate-radius.json',
 'work/continuation/weighted-coordinate-radius-independent-audit.json',
 'research/optimality/global_capture/trump-chart-identity.json',
 'research/optimality/global_capture/trump-cell-symmetric-assignments.json',
 'research/optimality/global_capture/center-cover-symmetric-exact.json']

def need(ok,message):
    if not ok:raise ValueError(message)

def ef(x):return E(str(x))
def q(x):return F(int(x.p),int(x.q))
def floor_tick(x):return F((x*DEN).numerator//(x*DEN).denominator,DEN)
def ceil_tick(x):return -floor_tick(-x)
def bounds(x):return tuple(q(v) for v in polynomial_interval(x.p,E.root_interval))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def refine_root():
    need(M.count_roots(*I)==1 and M.eval(I[0])<0<M.eval(I[1]),'defining root is not isolated')
    while E.root_interval[1]-E.root_interval[0]>F(1,10**30):
        lo,hi=E.root_interval;mid=(lo+hi)/2
        if M.eval(lo)*M.eval(mid)<0:E.root_interval=(lo,mid)
        else:E.root_interval=(mid,hi)

def targets():
    """Reconstruct all four exact canonical images in fixed centered coordinates."""
    data=json.loads((HERE/'trump-cell-symmetric-assignments.json').read_text())
    need(data['status']=='PASS_EXACT_TRUMP_16_CELL_ASSIGNMENTS','wrong cell-assignment status')
    need(data['number_of_canonical_capture_masks']==4,'wrong capture-mask inventory')
    masks={tuple(x) for x in data['canonical_capture_masks']}
    squares,alpha,_=configuration(E(u));centers=[tuple(sum(p[k] for p in sq)/4 for k in range(2)) for sq in squares]
    result=[]
    for row in data['eight_D4_images']:
        mask=tuple(row['selection'])
        if mask not in masks:continue
        sym=row['symmetry'];sign=(-1)**(sym['swap']+sym['reflect_x']+sym['reflect_y'])
        image=[]
        for x,y in centers:
            if sym['swap']:x,y=y,x
            if sym['reflect_x']:x=alpha-x
            if sym['reflect_y']:y=alpha-y
            image.append((x-alpha/2,y-alpha/2))
        angle=E(u) if sign==1 else (1-E(u))/(1+E(u))
        result.append({'mask':mask,'symmetry':sym,'label_to_cell':tuple(row['label_to_cell']),'centers':image,'tilted_half_angle':angle})
    need(len(result)==4 and len({r['mask'] for r in result})==4,'incomplete canonical images')
    return sorted(result,key=lambda row:row['mask']),alpha

def center_inner(value):
    lo,hi=bounds(value)
    return ceil_tick(hi-RHO),floor_tick(lo+RHO)

def tilt_inner(value):
    lo,hi=bounds(value)
    # Monotone inverse of (t-value)/(1+t*value), safely using opposite root bounds.
    return ceil_tick((hi-RELATIVE)/(1+hi*RELATIVE)),floor_tick((lo+RELATIVE)/(1-lo*RELATIVE))

def build():
    refine_root();images,alpha=targets()
    proof=json.loads((ROOT/SOURCE_PATHS[1]).read_text())
    need(proof['status']=='PASS_FULL_EXACT_WEIGHTED_COORDINATE_RADIUS' and F(proof['radius_closed'])==RHO,'banked local radius mismatch')
    chart=json.loads((ROOT/SOURCE_PATHS[3]).read_text())
    need(chart['status']=='PASS_EXACT_LABELLED_TRUMP_CHART_IDENTITY' and chart['label_permutation']==list(range(11)),'chart identity mismatch')
    guards=[]
    for row in images:
        tilt=tilt_inner(row['tilted_half_angle']);roles=[]
        for label,cell in enumerate(row['label_to_cell']):
            center=[center_inner(z) for z in row['centers'][label]]
            angle=[(F(0),RELATIVE),((1-RELATIVE)/(1+RELATIVE),F(1))] if label<6 else [tilt]
            roles.append({'label':label,'cell':cell,'centered_box':[[str(v) for v in ab] for ab in center],
                          'positive_uplus_box':[[str(v+SIDE_UPPER/2) for v in ab] for ab in center],
                          'half_angle_intervals':[[str(v) for v in ab] for ab in angle]})
        guards.append({'mask':list(row['mask']),'symmetry':row['symmetry'],'label_to_cell':list(row['label_to_cell']),'roles':roles})
    packet={'schema':'rational_trump_inner_capture_guards_v1','status':'EXACT_INNER_GUARDS_REPLAY_REQUIRED','global_optimality_proved':False,
            'radius_closed':str(RHO),'relative_half_angle_limit':str(RELATIVE),'side_upper_for_cover':str(SIDE_UPPER),
            'required_packing_side_upper':'alpha=(6*t+4)/(1+2*t-t^2), where M(t)=0 and .36<t<.37',
            'primary_coordinates':'Fixed origin at center of every container: [-S/2,S/2]^2. Guard centers are measured from that origin.',
            'positive_uplus_coordinates':'Add U_plus/2 to each centered coordinate; actual containment is [(U_plus-S)/2,(U_plus+S)/2]^2.',
            'source_sha256':{p:sha(ROOT/p) for p in SOURCE_PATHS},'root_interval':[str(x) for x in E.root_interval],
            'tick_denominator':DEN,'guards':guards}
    verify(packet)
    return packet

def verify(packet):
    need(packet.get('schema')=='rational_trump_inner_capture_guards_v1','wrong guard schema')
    need(F(packet['radius_closed'])==RHO and F(packet['relative_half_angle_limit'])==RELATIVE,'wrong radius')
    need(F(packet['side_upper_for_cover'])==SIDE_UPPER,'cover coordinate convention drift')
    need(packet['source_sha256']=={p:sha(ROOT/p) for p in SOURCE_PATHS},'source premise drift')
    refine_root();images,alpha=targets();lookup={r['mask']:r for r in images}
    guards=packet['guards'];need(len(guards)==4,'four guards required')
    seen=set();center_checks=angle_checks=0
    for guard in guards:
        mask=tuple(guard['mask']);need(mask in lookup and mask not in seen,'wrong or duplicate capture mask');seen.add(mask)
        row=lookup[mask]
        need(guard['symmetry']==row['symmetry'] and tuple(guard['label_to_cell'])==row['label_to_cell'],'symmetry or label map drift')
        need(len(guard['roles'])==11,'missing roles')
        roles_seen=set()
        for role in guard['roles']:
            label=role['label'];cell=role['cell']
            need(type(label) is int and 0<=label<11 and label not in roles_seen,'invalid role label');roles_seen.add(label)
            need(cell==row['label_to_cell'][label],'wrong role cell')
            need(len(role['centered_box'])==2 and len(role['positive_uplus_box'])==2,'center dimension mismatch')
            for k in range(2):
                lo,hi=map(F,role['centered_box'][k]);target=row['centers'][label][k]
                need(lo<=hi,'empty center interval')
                need((ef(lo)-target+ef(RHO)).sign()>=0 and (target+ef(RHO)-ef(hi)).sign()>=0,'center guard exceeds local radius')
                need((target-ef(lo)).sign()>=0 and (ef(hi)-target).sign()>=0,'guard misses target center')
                need(list(map(F,role['positive_uplus_box'][k]))==[lo+SIDE_UPPER/2,hi+SIDE_UPPER/2],'positive coordinate offset drift')
                center_checks+=2
            intervals=[tuple(map(F,iv)) for iv in role['half_angle_intervals']]
            need(intervals and all(len(iv)==2 and 0<=iv[0]<=iv[1]<=1 for iv in intervals),'invalid angular intervals')
            if label<6:
                need(len(intervals)==2 and intervals[0][0]==0 and intervals[1][1]==1,'axis guard must retain both angle endpoints')
                need(intervals[0][1]<=RELATIVE,'low endpoint guard too broad')
                need((1-intervals[1][0])/(1+intervals[1][0])<=RELATIVE,'high endpoint guard too broad')
                need(intervals[0][1]<intervals[1][0],'axis branches must not meet through the interior')
                angle_checks+=4
            else:
                need(len(intervals)==1,'tilted role must use one ordinary interval')
                target=row['tilted_half_angle'];lo,hi=intervals[0]
                need((target-ef(lo)).sign()>=0 and (ef(hi)-target).sign()>=0,'guard misses target angle')
                for endpoint in (lo,hi):
                    delta=(ef(endpoint)-target)/(1+ef(endpoint)*target)
                    need((ef(RELATIVE)-delta).sign()>=0 and (ef(RELATIVE)+delta).sign()>=0,'angle guard exceeds local radius')
                    angle_checks+=2
    return {'status':'PASS_EXACT_RATIONAL_INNER_CAPTURE_GUARDS','guards':4,'roles':44,'center_endpoint_inequalities':center_checks,'relative_angle_inequalities':angle_checks,'radius_closed':str(RHO),'global_optimality_proved':False,'required_external_premises':['Actual unit squares have disjoint interiors and are contained in the stated concentric container.','The side domain is proved to lie at or below the exact algebraic alpha.','The banked local theorem and labelled chart identity apply.'],'packet_sha256':hashlib.sha256(json.dumps(packet,sort_keys=True,separators=(',',':')).encode()).hexdigest()}

class CheckedGuards:
    """Check a packet once, then test many whole center/angle domains cheaply."""
    def __init__(self,packet):
        self.receipt=verify(packet);self.rows={}
        for guard in packet['guards']:
            self.rows[tuple(guard['mask'])]=(guard['symmetry'],tuple(guard['label_to_cell']),{
                r['cell']:(tuple(tuple(map(F,v)) for v in r['centered_box']),tuple(tuple(map(F,v)) for v in r['half_angle_intervals'])) for r in guard['roles']})
        _,self.alpha=targets()
    def accept(self,mask,center_bounds,angle_intervals,*,side_upper,frame='centered'):
        """Return a conditional capture receipt or None. side_upper is mandatory.

        side_upper='alpha' explicitly names the exact target premise. A rational
        upper bound is checked algebraically. The caller must bind its global
        side domain to this parameter; U_plus is rejected because U_plus>alpha.
        """
        if side_upper!='alpha':
            need(isinstance(side_upper,F),'side bound must be exact Fraction or literal alpha')
            need((self.alpha-ef(side_upper)).sign()>=0,'side bound exceeds alpha')
        need(frame in ('centered','positive_uplus'),'unknown coordinate frame')
        need(len(mask)==11 and len(set(mask))==11,'eleven unique cells required')
        mask=tuple(sorted(mask))
        if mask not in self.rows:return None
        sym,labels,roles=self.rows[mask]
        need(set(center_bounds)==set(mask) and set(angle_intervals)==set(mask),'domain cells do not match mask')
        offset=SIDE_UPPER/2 if frame=='positive_uplus' else F(0)
        for cell in mask:
            target_center,target_angle=roles[cell]
            center=center_bounds[cell];angles=angle_intervals[cell]
            need(len(center)==2 and all(len(v)==2 and all(isinstance(x,F) for x in v) and v[0]<=v[1] for v in center),'malformed rational center box')
            need(angles and all(len(v)==2 and all(isinstance(x,F) for x in v) and 0<=v[0]<=v[1]<=1 for v in angles),'malformed rational angle domain')
            if any(lo-offset<a or hi-offset>b for (lo,hi),(a,b) in zip(center,target_center)):return None
            if any(not any(a<=lo<=hi<=b for a,b in target_angle) for lo,hi in angles):return None
        return {'status':'PASS_WHOLE_DOMAIN_LOCAL_CAPTURE_GUARD','mask':list(mask),'symmetry':sym,'label_to_cell':list(labels),'radius_closed':str(RHO),'conclusion_if_packing_feasible':'The side equals alpha and the configuration is the stated Trump image.','global_optimality_proved':False}

def controls(packet):
    checked=CheckedGuards(packet);count=0
    for guard in packet['guards']:
        center={r['cell']:tuple(tuple(map(F,v)) for v in r['centered_box']) for r in guard['roles']}
        angles={r['cell']:tuple(tuple(map(F,v)) for v in r['half_angle_intervals']) for r in guard['roles']}
        need(checked.accept(guard['mask'],center,angles,side_upper='alpha') is not None,'closed inner guard rejected');count+=1
        positive={c:tuple(tuple(v+SIDE_UPPER/2 for v in ab) for ab in box) for c,box in center.items()}
        need(checked.accept(guard['mask'],positive,angles,side_upper='alpha',frame='positive_uplus') is not None,'equivalent positive-coordinate guard rejected');count+=1
        bad=deepcopy(angles);axis=guard['label_to_cell'][0];bad[axis]=((F(0),F(1)),)
        need(checked.accept(guard['mask'],center,bad,side_upper='alpha') is None,'whole angle arc falsely captured');count+=1
        bad=deepcopy(center);cell=guard['label_to_cell'][0];bad[cell]=((center[cell][0][0]-RHO,center[cell][0][1]),center[cell][1])
        need(checked.accept(guard['mask'],bad,angles,side_upper='alpha') is None,'expanded center box falsely captured');count+=1
        try:checked.accept(guard['mask'],center,angles,side_upper=SIDE_UPPER)
        except ValueError:count+=1
        else:raise ValueError('U_plus side falsely accepted by local alpha theorem')
    for mode in ('center','angle','label','offset','side','source'):
        bad=deepcopy(packet);role=bad['guards'][0]['roles'][0]
        if mode=='center':role['centered_box'][0][0]=str(F(role['centered_box'][0][0])-RHO)
        if mode=='angle':role['half_angle_intervals'][0][1]='1/10'
        if mode=='label':role['cell']=(role['cell']+1)%16
        if mode=='offset':role['positive_uplus_box'][0][0]=str(F(role['positive_uplus_box'][0][0])+1)
        if mode=='side':bad['side_upper_for_cover']='4'
        if mode=='source':bad['source_sha256'][SOURCE_PATHS[0]]='0'*64
        try:verify(bad)
        except ValueError:count+=1
        else:raise ValueError('guard packet mutation accepted: '+mode)
    return count

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',type=Path)
    args=parser.parse_args()
    if args.verify:packet=json.loads(args.verify.read_text())
    else:
        packet=build();(HERE/'local-capture-guards.json').write_text(json.dumps(packet,indent=2)+'\n')
    result=verify(packet);result['controls_passed']=controls(packet);result['checker_sha256']=sha(Path(__file__))
    (HERE/'local-capture-guards-verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
