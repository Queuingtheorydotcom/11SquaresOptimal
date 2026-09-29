#!/usr/bin/env python3
"""Compose source-bound geometry inductions, a finite partition, and local isolation.

This checker does not replace the independent rational geometry or local-dual
replays. It checks their premise bindings and the complete implication between
them. Its conclusion is for mask 438 only, never global optimality.
"""
from pathlib import Path
from fractions import Fraction as F
from functools import lru_cache
import argparse, hashlib, json, sys, time

if not __debug__:
    raise RuntimeError('Imported exact algebra requires assertions enabled')
HERE=Path(__file__).resolve().parent
R=HERE.parent
ROOT=R.parent
PH=R/'phase3'
OLD=R/'recovered-checkpoint'
ALG=OLD/'research/jlevy/packing'
MASK=[0,1,2,3,4,8,9,10,11,13,15]
U=F(387708359002281417731,10**20)
B=F(191,50)/U

def need(test,message):
    if not test: raise ValueError(message)

@lru_cache(None)
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path): return json.loads(Path(path).read_text())
def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def resolve(path):
    p=Path(path)
    if not p.is_absolute():p=ROOT/p
    need(p.is_file(),'Missing file: '+str(p))
    return p.resolve()

DEPENDENCY_ROOTS=[HERE,PH/'work/phase3/hull',PH/'work/phase3/collision',
 PH/'work/phase2/hull',PH/'work/geometry',PH/'current/research/optimality/audit']

def geometry_dependencies(proof,root=False):
    if root:
        expected={'audit_residual_kernel_v2.py','arrangement_audit.py','audit_wall_kernel.py',
                  'rational.py','audit_kernel_survivor.py'}
    else:
        expected={'audit_capture_portable.py','arrangement_audit_v2.py','rational.py',
                  'validate_collision_kernel_v3.py','own_hull_constraints.py',
                  'audit_residual_kernel.py','arrangement_audit.py','audit_wall_kernel.py',
                  'audit_kernel_survivor.py','audit_residual_kernel_v2.py'}
        if 'premise_audits' in proof:
            expected|={'audit_cached_node_portable.py','audit_tree_batch_portable.py'}
    need(set(proof['dependencies'])==expected,'Incomplete checker dependency inventory')
    for name,h in proof['dependencies'].items():
        need(any((d/name).is_file() and sha(d/name)==h for d in DEPENDENCY_ROOTS),
             'Geometry checker dependency drift: '+name)
    need(proof['rational_backend']=='gmp','Expected audited rational backend')
    binaries=list((HERE/'deps/gmpy2').glob('gmpy2*.so'))
    need(any(sha(p)==proof['rational_binary_sha256'] for p in binaries),'GMP binary drift')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,default=HERE/'complete-capture438-audit.json')
    ap.add_argument('--root-audit',type=Path,default=HERE/'root14-independent-audit.json')
    for name,default in [('far15','far15y'),('far13','far13'),('far2','far2'),('near','near1024')]:
        ap.add_argument('--'+name+'-audit',type=Path,default=HERE/(default+'-independent-audit.json'))
    ap.add_argument('--local-audit',type=Path,default=R/'global-math/focused1024-local-box-independent.json')
    args=ap.parse_args();start=time.monotonic();bound={}
    def bind(path,want=None):
        p=resolve(path);h=sha(p)
        need(want is None or h==want,'Premise hash mismatch: '+str(p))
        bound[str(p.relative_to(ROOT))]=h
        return read(p)

    rootpath=PH/'work/phase2/conditional/mask438-adaptive.json'
    root=bind(rootpath)
    root_audit_path=resolve(args.root_audit)
    root_audit=bind(root_audit_path)
    need(root_audit['status']=='PASS_INDEPENDENT_RESIDUAL_KERNEL_AUDIT','Missing root geometry audit')
    need(root_audit['source_sha256']==sha(rootpath),'Wrong root audit source')
    need(root['mask']==MASK and root['mask_index']==root_audit['mask_index']==438,'Wrong root mask')
    need(F(root['parent_Uplus'])==U and F(root['parent_side'])==B,'Wrong root frame')
    need(root_audit['seed_sha256']==root['seed_sha256'],'Wrong ownership seed')
    need(root_audit['cover_sha256']==root['cover_sha256'],'Wrong cover premise')
    bind(PH/'current/research/optimality/global_capture/center-cover-symmetric-exact.json',root['cover_sha256'])
    need(not any(root.get(k) for k in ('constraints','branch','branch_condition','branch_conditions','condition','conditions')),'Root has extra branch assumptions')
    need(not any(root_audit.get(k) for k in ('constraints','branch','branch_condition','branch_conditions','condition','conditions')),'Root audit has extra branch assumptions')
    geometry_dependencies(root_audit,root=True)
    # The ownership audit establishes every complete root round, including 14.
    latest={i:0 for i in MASK}
    for c in root_audit['cells']:
        if c['complete']:latest[c['owner']]=max(latest[c['owner']],c['round'])
    need(set(latest.values())=={14},'Root induction is incomplete')

    visited={};visiting=set();node_hashes={};node_metadata={}
    def node_info(path,h):
        if h not in node_metadata:
            d=read(path)
            node_metadata[h]={k:d[k] for k in ('node_id','source','parent','mask','mask_index','U','B','constraints','contradiction')}
            node_metadata[h]['final_constraints']=d['final_state']['constraints']
            node_metadata[h]['final_state_sha256']=digest(d['final_state'])
        return node_metadata[h]
    def check_geometry(path):
        path=resolve(path);h=sha(path)
        if h in visited:return visited[h]
        need(h not in visiting,'Cycle in geometric premise audits');visiting.add(h)
        a=bind(path)
        need(a['status']=='PASS_INDEPENDENT_BRANCH_HULL_AUDIT','Unfinished geometric premise')
        need(a['root_sha256']==sha(rootpath) and a['root_audit_sha256']==sha(root_audit_path),'Root induction mismatch')
        need(a['mask']==a['required_antecedent_mask']==MASK and a['mask_index']==438,'Geometry mask mismatch')
        need(F(a['parent_Uplus'])==U and F(a['parent_side'])==B,'Geometry frame mismatch')
        need(a['cover_sha256']==root['cover_sha256'],'Geometry cover mismatch')
        geometry_dependencies(a)
        premise_records={}
        for prem in a.get('premise_audits',[]):
            p=resolve(prem['path']);need(sha(p)==prem['sha256'],'Cached audit drift')
            prior,_=check_geometry(p);premise_records[prem['sha256']]={n['sha256']:n for n in prior['nodes']}
        positions={};paths=set();records={}
        for index,n in enumerate(a['nodes']):
            p=resolve(n['path']);need(sha(p)==n['sha256'],'Geometry node drift')
            need(n['sha256'] not in positions and p not in paths,'Duplicate geometry induction record')
            positions[n['sha256']]=index;paths.add(p);records[n['sha256']]=n
            node_hashes[str(p.relative_to(ROOT))]=n['sha256']
            d=node_info(p,n['sha256'])
            need(d['node_id']==n['node'],'Node identity mismatch')
            need(d['mask']==MASK and d['mask_index']==438 and F(d['U'])==U and F(d['B'])==B,'Intermediate node frame mismatch')
            need(resolve(d['source']['path'])==rootpath.resolve() and d['source']['sha256']==sha(rootpath),'Intermediate node root mismatch')
            need(n['constraints']==d['constraints']==d['final_constraints'],'Intermediate node assumption mismatch')
            need(n['branch_exclusion_proved']==bool(d['contradiction']),'Intermediate contradiction mismatch')
            if 'cached_from_audit_sha256' in n:
                ph=n['cached_from_audit_sha256'];need(ph in premise_records and n['sha256'] in premise_records[ph],'Unproved cached sibling node')
                clean=lambda x:{k:v for k,v in x.items() if k!='cached_from_audit_sha256'}
                need(clean(n)==clean(premise_records[ph][n['sha256']]),'Cached induction record changed')
        for nh,n in records.items():
            d=node_metadata[nh];parent=d['parent']
            if parent is None:
                need(d['constraints']==[],'Unparented node has hidden assumptions')
            else:
                ph=parent['sha256'];need(ph in positions and positions[ph]<positions[nh],'Missing, cyclic, or out-of-order source parent')
                need(resolve(parent['path'])==resolve(records[ph]['path']) and sha(resolve(parent['path']))==ph,'Wrong source parent path')
                prior=node_metadata[ph]
                need(not prior['contradiction'],'Continuation from an already impossible node')
                need(d['constraints'][:len(prior['constraints'])]==prior['constraints'],'Inherited branch condition dropped')
                need(len(d['constraints'])<=len(prior['constraints'])+1,'Unexpected combined branch assumption')
        need(a['source_sha256'] in positions,'Final geometry source absent')
        ancestry=set();cursor=a['source_sha256']
        while cursor is not None:
            need(cursor not in ancestry,'Source parent cycle');ancestry.add(cursor)
            parent=node_metadata[cursor]['parent'];cursor=None if parent is None else parent['sha256']
        need(all(nh in ancestry or 'cached_from_audit_sha256' in n for nh,n in records.items()),'Unaudited sibling outside selected ancestry')
        chosen=[n for n in a['nodes'] if n['sha256']==a['source_sha256']]
        need(len(chosen)==1,'Missing final geometric induction')
        n=chosen[0];d=bind(n['path'],a['source_sha256'])
        need(d['source']['sha256']==sha(rootpath) and d['mask']==MASK,'Wrong leaf root')
        need(a['constraints']==n['constraints']==d['constraints']==d['final_state']['constraints'],'Leaf assumption drift')
        need(a['final_state_sha256']==digest(d['final_state']),'Final pose state drift')
        need(a['branch_exclusion_proved']==n['branch_exclusion_proved'],'Contradiction mismatch')
        visiting.remove(h);visited[h]=(a,d);return a,d

    # These are the leaves of a complete three-split binary decision tree.
    specs=[('far15','far15y-independent-audit.json',[(15,'center',F(5,4),'le')]),
           ('far13','far13-independent-audit.json',[(15,'center',F(5,4),'ge'),(13,'angle',F(147,512),'le')]),
           ('far2','far2-independent-audit.json',[(15,'center',F(5,4),'ge'),(13,'angle',F(147,512),'ge'),(2,'angle',F(183,512),'le')]),
           ('near','near1024-independent-audit.json',[(15,'center',F(5,4),'ge'),(13,'angle',F(147,512),'ge'),(2,'angle',F(183,512),'ge')])]
    leaves=[];near=None
    def canonical_constraint(c):
        need(c['owner'] in MASK and c['keep'] in ('le','ge'),'Invalid branch predicate')
        if c.get('kind')=='half_angle':
            t=F(c['bound_half_angle']);need(0<t<1,'Angle cut outside full chart')
            return c['owner'],'angle',t,c['keep']
        need(c['axis']==1,'Unexpected center axis')
        sign=1 if c['keep']=='le' else -1
        need(c['normal']==[0,sign],'Center cut normal mismatch')
        b=F(c['bound_centered_unit'])
        need(F(c['upper_field'])==sign*B*(U/2+b),'Field/unit center cut mismatch')
        return c['owner'],'center',b,c['keep']
    for name,filename,conditions in specs:
        audit_path=resolve(getattr(args,name+'_audit'))
        a,d=check_geometry(audit_path)
        need([canonical_constraint(c) for c in a['constraints']]==conditions,'Leaf assumptions do not match binary partition')
        if name!='near':need(a['branch_exclusion_proved'],'Far leaf is not excluded')
        else:
            need(not a['branch_exclusion_proved'],'Expected nonempty near leaf');near=(a,d)
        leaves.append({'name':name,'audit':str(audit_path),
            'audit_sha256':sha(audit_path),'source_sha256':a['source_sha256'],
            'predicates':[(i,k,str(t),s) for i,k,t,s in conditions],
            'closure':'CONTRADICTION' if name!='near' else 'FOCUSED_LOCAL_RECTANGLE'})
    # <= and >= overlap at equality, and their union is the whole real line.
    # Explicit paths below must therefore cover every sign choice at all cuts.
    paths=[tuple(v[-1] for v in conditions) for _,_,conditions in specs]
    for a in ('le','ge'):
        for b in ('le','ge'):
            for c in ('le','ge'):
                full=(a,b,c);need(sum(full[:len(p)]==p for p in paths)==1,'Partition has a gap or duplicated decision path')

    local_path=resolve(args.local_audit)
    local=bind(local_path)
    need(local['status']=='PASS_INDEPENDENT_FOCUSED_RECTANGLE_LOCAL_ISOLATION','Missing local box audit')
    need(local['checker_sha256']==sha(R/'global-math/audit_focused_local_box.py'),'Local checker drift')
    bind(local['proposal'],local['proposal_sha256'])
    need(local['source_sha256']==near[0]['source_sha256'] and local['final_state_sha256']==near[0]['final_state_sha256'],'Local theorem is for a different pose domain')
    need(local['local_rectangle_isolation_proved'] and local['conditional_on_source_pose_domains'],'Wrong local theorem scope')
    need(local['coordinate_certificates_checked']==8448 and local['unavailable_features_checked']==88,'Incomplete local proof inventory')
    need(len(local['feature_stability'])==88 and len({tuple(g['subject']) for g in local['feature_stability']})==88,'Incomplete or duplicate unavailable feature inventory')
    need(0<=F(local['worst_dual_ratio'])<1 and all(F(g['strict_gap_after_Taylor'])>0 for g in local['feature_stability']),'Non-strict local inequality')
    weightedpath=OLD/'research/classical/trump-local-weighted-coordinate-radius.json'
    bind(weightedpath,local['prior_coordinate_packet_sha256'])
    fresh=bind(R/'local-radius/fresh-weighted-coordinate-radius.json',local['prior_independent_replay_sha256'])
    need(fresh['status']=='PASS_INDEPENDENT_WEIGHTED_COORDINATE_RADIUS_AUDIT' and fresh['proposal_sha256']==sha(weightedpath),'Wrong dual premise')
    need(fresh['audit_script_sha256']==sha(OLD/'work/continuation/audit_weighted_coordinate_radius.py'),'Prior dual checker drift')
    need(fresh['source_hashes']==local['source_hashes'],'Local algebra mismatch')
    for name,h in local['source_hashes'].items():
        need(sha(ALG/name)==h,'Algebra source drift');bound[str((ALG/name).relative_to(ROOT))]=h
    baseline=bind(OLD/'work/continuation/local-radius-independent-audit.json',fresh['baseline_audit_sha256'])
    algebra=bind(OLD/'research/classical/trump-local-independent-replay.json',fresh['prior_algebra_replay_sha256'])
    fresh_baseline=bind(R/'local-radius/fresh-baseline-radius.json')
    fresh_algebra=bind(R/'local-radius/fresh-local-algebra.json')
    def core(x,skip):return {k:v for k,v in x.items() if k not in skip}
    need(core(algebra,{'seconds','python_version'})==core(fresh_algebra,{'seconds','python_version'}),'Fresh algebra replay disagrees')
    need(core(baseline,{'seconds','proof_sha256'})==core(fresh_baseline,{'seconds','proof_sha256'}),'Fresh radius replay disagrees')
    # A proof prose hash changed; bind the fresh prose without ignoring arithmetic.
    need(fresh_baseline['proof_sha256']==sha(OLD/'research/classical/TRUMP-LOCAL-RADIUS.md'),'Local analytic note drift')
    guards=bind(PH/'current/research/optimality/global_capture/local-capture-guards.json',local['guard_assignment_source_sha256'])
    guard=next(g for g in guards['guards'] if g['mask']==MASK)
    need(guard['symmetry']=={'swap':True,'reflect_x':True,'reflect_y':False},'Wrong inverse symmetry')
    roles=guard['roles'];need(sorted(x['label'] for x in roles)==list(range(11)) and sorted(x['cell'] for x in roles)==MASK,'Role mapping is not bijective')
    need(len(local['inclusion'])==11 and len({(x['label'],x['owner']) for x in local['inclusion']})==11,'Incomplete or duplicate local inclusion inventory')
    need({(x['label'],x['owner']) for x in local['inclusion']}=={(x['label'],x['cell']) for x in roles},'Local role mapping drift')
    need(len(local['radii'])==33 and all(0<F(r)<=F(fresh['box_radius']) for r in local['radii']),'Local box exceeds declared chart')

    # Independently expose the exact endpoint and fixed-container bridge.
    sys.path[:0]=[str(ALG),str(ALG/'src')]
    from cases.trump11 import isolation_radius as ir
    w=ir.load_witness();lo,hi=map(F,fresh['root_interval'])
    def interval(v):
        aa=bb=F(0)
        for c in reversed(v.coeffs):
            z=(aa*lo,aa*hi,bb*lo,bb*hi);aa,bb=min(z)+c,max(z)+c
        return aa,bb
    Tlo,Thi=interval(w.side)
    need(0<Tlo<=Thi<U,'Exact side not strictly below the rational field cap')
    walls=[]
    for axis in (0,1):
        for value,name in ((w.field.zero,'lower'),(w.side,'upper')):
            contacts=[(i,j) for i,P in enumerate(w.squares) for j,p in enumerate(P) if (p[axis]-value).is_zero()]
            need(contacts,'Exact construction does not span each container axis')
            walls.append({'axis':axis,'wall':name,'exact_corner_contacts':contacts})
    state=near[1]['final_state']
    need(F(state['U'])==U and F(state['B'])==B,'Final field scale mismatch')
    # Actual source rows include endpoints 0 and 1; the local audit includes
    # their whole closed angular intervals and identifies them modulo pi/2.
    endpoints=set();live=vertices=0
    for owner,rows in state['cells'].items():
        for row in rows:
            if not row['residual_polygons']:continue
            a,b=map(F,row['interval']);need(0<=a<=b<=1,'Invalid closed angle interval')
            if a==0:endpoints.add(0)
            if b==1:endpoints.add(1)
            live+=1;vertices+=sum(map(len,row['residual_polygons']))
    need(live==local['pose_rows_checked'] and vertices==local['vertices_checked'],'Local inclusion inventory mismatch')
    need(endpoints=={0,1},'Expected chart endpoint checks missing')
    out={'status':'PASS_COMPLETE_CANDIDATE438_CAPTURE_COMPOSITION',
         'checker_sha256':sha(__file__),'mask_index':438,'required_antecedent_mask':MASK,
         'parent_Uplus':str(U),'parent_side':str(B),'exact_side_interval':[str(Tlo),str(Thi)],
         'closed_leaves':leaves,'partition_covers_all_real_center_values_and_closed_half_angles':True,
         'coordinate_bridge':{
           'field_to_centered_unit':'c = p/B - (U/2,U/2)',
           'inverse_symmetry':'Q^{-1}(c_x,c_y)=(c_y,-c_x)',
           'anchored_chart':'z_center = Q^{-1} c + (T/2,T/2)',
           'embedding':'Any packing centered in a square of side S<=T remains contained after this rigid map in [0,T]^2.',
           'U_to_T_translation_accounted_for':True,
           'angles':'Full closed intervals; t=0 and t=1 identify the same square orientation modulo pi/2. Axis rows near 1 use (t-1)/(t+1).',
           'angle_endpoints_checked':sorted(endpoints),'roles':roles,'witness_wall_contacts':walls},
         'pose_rows_covered':live,'vertices_covered':vertices,
         'local_rectangle_audit_sha256':sha(local_path),'local_worst_dual_ratio':local['worst_dual_ratio'],
         'bound_premises':bound,'geometry_nodes':node_hashes,
         'candidate_mask_capture_proved':True,'no_smaller_packing_for_this_mask':True,
         'global_optimality_proved':False,
         'scope':'Conditional on the exact occupied-cell antecedent mask 438 in the centered U-cap cover, every packing at side S<=T is the known exact construction after the displayed quarter-turn and label map, and therefore S=T. Other mask cases are outside this theorem.',
         'seconds':time.monotonic()-start}
    args.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ['status','mask_index','pose_rows_covered','vertices_covered','candidate_mask_capture_proved','global_optimality_proved','seconds']},indent=2))

if __name__=='__main__':main()
