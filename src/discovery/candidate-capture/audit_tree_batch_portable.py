#!/usr/bin/env python3
"""Source-bound tree partitions and shared-cache independent leaf replay.

Optional prior independent audit receipts are explicit proof premises. Their
node files and executable dependencies must still match their recorded hashes.
Without --certified-cache, every requested leaf's ancestry is replayed anew.
"""
from pathlib import Path
import argparse,copy,json,time
import audit_capture_portable as a
F=a.F
if not __debug__:raise RuntimeError('Assertions must be enabled')

def dependencies_match(proof,path,seen=None):
    seen=set() if seen is None else seen
    fingerprint=a.sha(path)
    if fingerprint in seen:return
    seen.add(fingerprint)
    roots=[Path(__file__).resolve().parent,a.WORK/'phase3/hull',a.WORK/'phase3/collision',a.WORK/'phase2/hull',a.WORK/'geometry',a.ROOT/'research/optimality/audit']
    for name,h in proof['dependencies'].items():
        assert any((p/name).is_file() and a.sha(p/name)==h for p in roots),'Cached checker dependency changed: '+name
    if proof.get('rational_backend')=='gmp':
        binary=a.rational.BINARY;assert binary is not None
        assert a.sha(binary)==proof['rational_binary_sha256']
    for premise in proof.get('premise_audits',[]):
        p=a.locate(premise['path'],path);assert a.sha(p)==premise['sha256']
        prior=json.loads(p.read_text());assert prior['root_sha256']==proof['root_sha256'] and prior['root_audit_sha256']==proof['root_audit_sha256']
        assert prior['status'] in ('PASS_INDEPENDENT_BRANCH_HULL_AUDIT','PASS_INDEPENDENT_GENERIC_HULL_AUDIT','PASS_INDEPENDENT_PARTIAL_TREE_AUDIT','RUNNING_INDEPENDENT_TREE_AUDIT')
        dependencies_match(prior,p,seen)

def load_cache(replay,paths):
    loaded=[]
    for path in paths:
        proof=json.loads(path.read_text())
        assert proof['status'] in ('PASS_INDEPENDENT_BRANCH_HULL_AUDIT','PASS_INDEPENDENT_GENERIC_HULL_AUDIT','PASS_INDEPENDENT_PARTIAL_TREE_AUDIT','RUNNING_INDEPENDENT_TREE_AUDIT')
        assert proof['root_sha256']==replay.source_hash and proof['root_audit_sha256']==(a.sha(replay.root_audit) if replay.root_audit else None)
        dependencies_match(proof,path)
        for record in proof['nodes']:
            p=a.locate(record['path'],path);h=a.sha(p);assert h==record['sha256']
            if h in replay.cache:continue
            d=json.loads(p.read_text());assert d['source']['sha256']==replay.source_hash and d['mask']==replay.mask
            assert F(d['U'])==replay.U and F(d['B'])==replay.B
            final=d['final_state'];state=dict(groups=a.groups(final['groups']),cells={},constraints=final['constraints'])
            assert state['constraints']==d['constraints']
            for owner,rows in final['cells'].items():
                state['cells'][int(owner)]=[dict(r,interval=list(map(F,r['interval'])),outer_domain=a.poly(r['outer_domain']),residual_polygons=[a.poly(P) for P in r['residual_polygons']]) for r in rows]
            assert set(state['groups'])==set(state['cells'])==set(replay.mask)
            replay.cache[h]=state
            replay.records.append(dict(record,cached_from_audit_sha256=a.sha(path)))
        loaded.append(dict(path=str(path),sha256=a.sha(path),scope='Only fully completed node induction records are imported; any unfinished tree coverage is not imported.'))
    return loaded

def semantic(c):
    if c.get('kind')=='half_angle':return ('angle',c['owner'],c['keep'],F(c['bound_half_angle']))
    return ('center',c['owner'],tuple(map(F,c['normal'])),F(c['upper_field']))

def check_partition(tree,path,replay):
    nodes=tree['nodes'];seen=set();closed=[];unresolved=[]
    def visit(name,conditions,parent):
        assert name in nodes and name not in seen;seen.add(name);node=nodes[name];assert node['parent']==parent
        status=node['status']
        if status=='SPLIT':
            s=node['split'];owner=s['owner'];assert owner in replay.mask and set(s['children'])=={'le','ge'}
            assert s['children']['le']!=s['children']['ge']
            angle=s.get('kind')=='half_angle'
            if angle:
                t=F(s['bound_half_angle']);lo,hi=a.angle_range(owner,conditions);assert lo<t<hi
            else:
                axis=s['axis'];assert axis in (0,1);bound=F(s['bound_centered_unit'])
            for side,child in s['children'].items():
                assert nodes[child]['side']==side
                if angle:extra=dict(kind='half_angle',owner=owner,bound_half_angle=t,keep=side)
                else:
                    sign=1 if side=='le' else -1;n=[0,0];n[axis]=sign
                    extra=dict(owner=owner,axis=axis,keep=side,normal=n,bound_centered_unit=bound,upper_field=sign*replay.B*(replay.U/2+bound))
                visit(child,conditions+[extra],name)
        elif status in ('CLOSED_BY_CONTRADICTION','CAPTURED_BY_LOCAL_GUARD'):
            ref=node['receipt'];p=a.locate(ref['path'],path);assert a.sha(p)==ref['sha256']
            d=json.loads(p.read_text());assert d['source']['sha256']==replay.source_hash
            assert list(map(semantic,d['constraints']))==list(map(semantic,conditions))
            closed.append(dict(id=name,status=status,path=p,sha256=ref['sha256']))
        else:unresolved.append(name)
    assert 'r' in nodes and nodes['r']['parent'] is None
    visit('r',[],None);assert seen==set(nodes)
    return closed,unresolved

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tree',type=Path);ap.add_argument('--root-audit',type=Path,required=True);ap.add_argument('--certified-cache',type=Path,action='append',default=[]);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    begin=time.monotonic();treebytes=args.tree.read_bytes();tree=json.loads(treebytes)
    source=a.locate(tree['root_source']['path'],args.tree);assert a.sha(source)==tree['root_source']['sha256']
    replay=a.Replay(source,args.root_audit,generic_mode=False);premises=load_cache(replay,args.certified_cache)
    closed,unresolved=check_partition(tree,args.tree,replay);checked=[]
    def save():
        all_closed=len(checked)==len(closed);complete=all_closed and not unresolved
        excluded=complete and all(r['branch_exclusion_proved'] for r in checked)
        import hashlib
        files=[Path(__file__),Path(a.__file__),Path(a.geo.__file__),Path(a.collision.__file__),Path(a.rational.__file__),Path(a.self_hull.__file__),
               a.WORK/'phase3/hull/audit_residual_kernel.py',a.WORK/'phase3/hull/arrangement_audit.py',
               a.WORK/'geometry/audit_wall_kernel.py',a.WORK/'geometry/audit_kernel_survivor.py',*replay.root_dependency_files]
        assert a.sha(source)==replay.source_hash
        for r in replay.records:assert a.sha(r['path'])==r['sha256']
        out=dict(status='PASS_INDEPENDENT_PARTIAL_TREE_AUDIT' if all_closed else 'RUNNING_INDEPENDENT_TREE_AUDIT',tree_sha256=hashlib.sha256(treebytes).hexdigest(),
                 root_sha256=replay.source_hash,root_audit_sha256=a.sha(args.root_audit),premise_audits=premises,dependencies={p.name:a.sha(p) for p in files},
                 rational_backend=a.rational.BACKEND,rational_backend_version=a.rational.VERSION,rational_binary_sha256=a.sha(a.rational.BINARY) if a.rational.BINARY else None,
                 nodes=replay.records,checked_leaves=checked,rows_replayed_this_run=sum(r['rows'] for r in replay.records if 'cached_from_audit_sha256' not in r),
                 rows_in_cached_premises=sum(r['rows'] for r in replay.records if 'cached_from_audit_sha256' in r),closed_leaves_in_snapshot=len(closed),unresolved_leaf_ids=unresolved,
                 complete=complete,mask_exclusion_proved=excluded,mask_reduced_to_local_guard=complete,global_optimality_proved=False,seconds=time.monotonic()-begin)
        tmp=args.output.with_suffix('.writing');tmp.write_text(json.dumps(out,default=str,indent=2)+'\n');tmp.replace(args.output)
    original_replay=replay.replay
    def checkpoint_replay(path):
        ans=original_replay(path)
        save()
        return ans
    replay.replay=checkpoint_replay
    for leaf in closed:
        replay.replay(leaf['path']);record=next(r for r in replay.records if r['sha256']==leaf['sha256'])
        if leaf['status']=='CLOSED_BY_CONTRADICTION':assert record['branch_exclusion_proved']
        else:assert record['inside_local_guard']
        checked.append(dict(id=leaf['id'],receipt_sha256=leaf['sha256'],branch_exclusion_proved=record['branch_exclusion_proved'],inside_local_guard=record['inside_local_guard']))
        save();print(json.dumps(dict(checked_leaf=leaf['id'],completed_leaves=len(checked),snapshot_closed_leaves=len(closed),seconds=time.monotonic()-begin)),flush=True)
    save()
if __name__=='__main__':main()
