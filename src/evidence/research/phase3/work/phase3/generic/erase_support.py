"""Propose smaller-support certificates by erasure; full independent replay required.

Only fresh wall-seed roots without parents/branch constraints are accepted.
No geometric conclusion is trusted: a transformed residual cover generally
fails, and is a certificate only if the independent generic auditor accepts it.
"""
from pathlib import Path
import sys,json,hashlib,argparse,copy
sys.path.insert(0,str(Path(__file__).parents[1]/'capture'))
import capture_engine_v2 as E
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def transform(source,drop,output):
    d=json.loads(source.read_text());assert d['schema']=='exact_generic_owned_hull_v1'
    assert not d['parent'] and not d['constraints'] and d['contradiction']
    seedpath=Path(d['source']['path']);assert sha(seedpath)==d['source']['sha256']
    seed=json.loads(seedpath.read_text());assert seed['schema']=='generic_wall_seed_v1'
    assert set(drop)<set(d['mask']);retained=sorted(set(d['mask'])-set(drop))
    terminal=d['contradiction']
    assert terminal.get('owner') not in drop and not set(terminal.get('owners',[]))&set(drop)
    oldnode=d['node_id'];newnode=output.stem
    oldsteps=d['steps'];mapping={s['index']:k for k,s in enumerate(s for s in oldsteps if s['owner'] in retained)}
    def keep_map(m):return {i:v for i,v in m.items() if int(i) in retained}
    def rewrite_refs(obj):
        if isinstance(obj,list):
            for x in obj:rewrite_refs(x)
        elif isinstance(obj,dict):
            if obj.get('kind')=='phase3' and obj.get('node')==oldnode:
                assert obj['step'] in mapping
                obj['node']=newnode;obj['step']=mapping[obj['step']]
            for v in obj.values():rewrite_refs(v)
    seed['mask']=retained;seed['groups']=keep_map(seed['groups']);seed['cells']=keep_map(seed['cells'])
    provenance=dict(original_receipt_path=str(source.resolve()),original_receipt_sha256=sha(source),
                    original_seed_sha256=sha(seedpath),removed_owners=sorted(drop),
                    transformer_sha256=sha(Path(__file__)),requires_independent_replay=True)
    seed['support_erasure']=provenance
    newseed=output.with_name(output.stem+'-seed.json');E.save(newseed,seed)
    d['source']=dict(path=str(newseed.resolve()),sha256=sha(newseed));d['mask']=retained;d['node_id']=newnode
    d['initial']['groups']=keep_map(d['initial']['groups']);d['initial']['cell_references']=keep_map(d['initial']['cell_references'])
    d['steps']=[s for s in oldsteps if s['owner'] in retained]
    for s in d['steps']:
        s['index']=mapping[s['index']]
        s['prior_owned_hulls']=keep_map(s['prior_owned_hulls'])
        s['prior_sha256']=E.digest({int(i):E.poly(p) for i,p in s['prior_owned_hulls'].items()})
        s['prior_partner_pose_covers']=keep_map(s.get('prior_partner_pose_covers',{}))
        for r in s['rows']:r['collision_regions']=[p for p in r.get('collision_regions',[]) if p['partner'] in retained]
    f=d['final_state'];f['mask']=retained;f['source']=d['source'];f['groups']=keep_map(f['groups']);f['cells']=keep_map(f['cells'])
    if 'step' in terminal:terminal['step']=mapping[terminal['step']]
    rewrite_refs(d)
    for s in d['steps']:
        pc={int(j):[dict(r,interval=list(map(E.F,r['interval'])),core=E.poly(r['core']),domain=E.poly(r['domain'])) for r in rows]
            for j,rows in s['prior_partner_pose_covers'].items()}
        s['prior_partner_pose_covers_sha256']=E.digest(pc)
    d['support_erasure']=provenance;d['summary']=dict(all_inside_guard=False,scope='Proposed support erasure; independent replay required')
    E.save(output,d)
    return dict(output=str(output),source_sha256=sha(output),required_owners=retained,independently_audited=False)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--drop',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    print(json.dumps(transform(a.source,[int(x) for x in a.drop.split(',')],a.output)))
