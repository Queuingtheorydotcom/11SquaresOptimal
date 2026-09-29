#!/usr/bin/env python3
"""Independent algebraic audit of rational whole-domain local capture guards."""
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,sys
from audit_endpoint_rows import E,u,configuration,HornerSigns,require

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
DOMAIN=HERE.parent/'global_capture';RHO=F(1,248);REL=RHO/2;UP=F(969271,250000)

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ef(x):q=F(x);return E(q.numerator)/q.denominator

def main():
    packet_path=DOMAIN/'local-capture-guards.json';packet=json.loads(packet_path.read_text())
    bracket=json.loads((HERE.parent/'endpoint_charge/exact-trump-endpoint-rows.json').read_text())['root_interval']
    sign=HornerSigns(bracket)
    squares,alpha,_=configuration(E(u))
    # Execute the retained build_in AST itself with the audited field adapter,
    # avoiding dependence on a handwritten transcription of that function.
    external=ROOT/'research/jlevy/packing/cases/trump11/packing.py'
    tree=ast.parse(external.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_in')
    E.is_zero=E.iszero
    namespace={};exec(compile(ast.Module(body=[function],type_ignores=[]),str(external),'exec'),namespace)
    retained,side=namespace['build_in'](SimpleNamespace(rational=E),E(u))
    require((side-alpha).iszero(),'retained chart side differs')
    require(all((a-b).iszero() for sq,rsq in zip(squares,retained) for p,q in zip(sq,rsq) for a,b in zip(p,q)),'retained chart labelled vertices differ')
    local=ROOT/'research/classical/trump-local-weighted-coordinate-radius.json'
    localdata=json.loads(local.read_text())
    previous=json.loads((ROOT/'work/continuation/weighted-coordinate-radius-independent-audit.json').read_text())
    require(localdata['status']=='PASS_FULL_EXACT_WEIGHTED_COORDINATE_RADIUS' and F(localdata['radius_closed'])==RHO,'local theorem radius/status differs')
    require(previous['status']=='PASS_INDEPENDENT_WEIGHTED_COORDINATE_RADIUS_AUDIT' and previous['proposal_sha256']==digest(local) and F(previous['closed_radius'])==RHO,'local audit binding differs')
    require(all(digest(ROOT/path)==sha for path,sha in packet['source_sha256'].items()),'guard input hash differs')
    assignments=json.loads((DOMAIN/'trump-cell-symmetric-assignments.json').read_text())
    canonical={tuple(x) for x in assignments['canonical_capture_masks']}
    require(len(packet['guards'])==4 and {tuple(g['mask']) for g in packet['guards']}==canonical,'guard masks differ')
    centers=[tuple(sum(p[k] for p in sq)/4-alpha/2 for k in range(2)) for sq in squares]
    center_tests=0;angle_tests=0
    for guard in packet['guards']:
        sym=guard['symmetry'];mapping=guard['label_to_cell']
        require(sorted(r['label'] for r in guard['roles'])==list(range(11)),'guard labels missing or repeated')
        image=[]
        for x,y in centers:
            if sym['swap']:x,y=y,x
            if sym['reflect_x']:x=-x
            if sym['reflect_y']:y=-y
            image.append((x,y))
        # Derive the tilted reference from the transformed edge, not parity.
        c=(1-E(u)**2)/(1+E(u)**2);s=2*E(u)/(1+E(u)**2)
        if sym['swap']:c,s=s,c
        if sym['reflect_x']:c=-c
        if sym['reflect_y']:s=-s
        options=[(c,s),(-s,c),(-c,-s),(s,-c)]
        first=[(a,b) for a,b in options if sign.element(a)>0 and sign.element(b)>0]
        require(len(first)==1,'nonaxis orientation lacks unique first-quadrant representative')
        a,b=first[0];tilt=b/(1+a)
        for role in guard['roles']:
            label=role['label'];require(role['cell']==mapping[label],'role cell mismatch')
            for k,ab in enumerate(role['centered_box']):
                lo,hi=map(F,ab);target=image[label][k]
                require(lo<=hi,'empty coordinate guard')
                for value in [target-ef(lo),ef(hi)-target,ef(lo)+ef(RHO)-target,target+ef(RHO)-ef(hi)]:
                    require(sign.element(value)>=0,'center guard target/radius inequality fails');center_tests+=1
                require(list(map(F,role['positive_uplus_box'][k]))==[lo+UP/2,hi+UP/2],'positive-frame offset differs')
            iv=[tuple(map(F,p)) for p in role['half_angle_intervals']]
            if label<6:
                require(len(iv)==2 and iv[0][0]==0 and iv[1][1]==1,'axis endpoint branches missing')
                require(0<=iv[0][1]<=REL and 0<iv[1][0]<=1 and (1-iv[1][0])/(1+iv[1][0])<=REL,'axis arc exceeds local angle radius')
                angle_tests+=4
            else:
                require(len(iv)==1 and 0<=iv[0][0]<=iv[0][1]<=1,'tilted branch invalid')
                lo,hi=iv[0]
                require(sign.element(tilt-ef(lo))>=0 and sign.element(ef(hi)-tilt)>=0,'tilted target omitted')
                for endpoint in (lo,hi):
                    denominator=1+ef(endpoint)*tilt;require(sign.element(denominator)>0,'relative-angle denominator not positive')
                    delta=(ef(endpoint)-tilt)/denominator
                    require(sign.element(ef(REL)-delta)>=0 and sign.element(ef(REL)+delta)>=0,'relative half angle exceeds radius')
                    angle_tests+=2
    # Exercise whole-domain acceptance, coordinate conversion and side premise.
    source=DOMAIN/'local_capture_guards.py';source_sha=digest(source)
    sys.path.insert(0,str(DOMAIN));spec=importlib.util.spec_from_file_location('local_capture_guards_under_audit',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    checked=module.CheckedGuards(packet);controls=0
    for guard in packet['guards']:
        bounds={r['cell']:tuple(tuple(map(F,v)) for v in r['centered_box']) for r in guard['roles']}
        angles={r['cell']:tuple(tuple(map(F,v)) for v in r['half_angle_intervals']) for r in guard['roles']}
        require(checked.accept(guard['mask'],bounds,angles,side_upper='alpha') is not None,'valid centered guard rejected');controls+=1
        positive={i:tuple(tuple(x+UP/2 for x in ab) for ab in box) for i,box in bounds.items()}
        require(checked.accept(guard['mask'],positive,angles,side_upper='alpha',frame='positive_uplus') is not None,'valid translated guard rejected');controls+=1
        require(checked.accept(guard['mask'],positive,angles,side_upper='alpha') is None,'wrong frame accepted');controls+=1
        broad=copy.deepcopy(angles);broad[guard['label_to_cell'][0]]=((F(0),F(1)),)
        require(checked.accept(guard['mask'],bounds,broad,side_upper='alpha') is None,'broad angle arc accepted');controls+=1
        try:checked.accept(guard['mask'],bounds,angles,side_upper=UP)
        except ValueError:controls+=1
        else:raise ValueError('rational side exceeding alpha accepted')
    require(digest(source)==source_sha,'guard checker changed during audit')
    result={'status':'PASS_INDEPENDENT_RATIONAL_CAPTURE_GUARD_AUDIT','guard_packet_sha256':digest(packet_path),
            'guard_checker_sha256':source_sha,'retained_construction_sha256':digest(external),
            'retained_labelled_vertex_identities':88,'guards':4,'roles':44,
            'independent_center_target_and_radius_inequalities':center_tests,
            'relative_angle_guard_checks':angle_tests,'api_controls':controls,
            'angle_argument':'|tan(delta_theta/2)|<=rho/2 implies |delta_theta|<=2 atan(rho/2)<rho; axis guards use representatives on both sides of zero modulo pi/2.',
            'coordinate_argument':'Translate centered candidates by alpha/2 to apply the anchored fixed-side local theorem with unchanged displacement norm.',
            'scope':'Whole-domain local capture conditional on actual feasibility, S<=alpha, and the banked local isolation theorem. No remote case is proved to enter a guard.',
            'global_optimality_proved':False}
    (HERE/'local-capture-guards-independent-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
