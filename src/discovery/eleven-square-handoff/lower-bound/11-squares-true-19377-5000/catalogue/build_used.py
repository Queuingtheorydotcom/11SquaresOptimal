"""Adaptive exact TRUE-charge catalogue, with frozen inputs and node receipts.

Only complete angular coverage by successful exact leaves certifies a bound.
Failed core rows are bisected; exactly deficient full parents stop that branch.
"""
if not __debug__:
    raise SystemExit('Assertions must remain enabled; remove -O/-OO.')

import argparse
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import importlib
import json
from math import lcm
import multiprocessing as mp
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_CHECKER=ROOT/'research/exact_checker'
DEFAULT_TEMPLATE=ROOT/'source/11-squares-certified-bound-main/global-certificate.json'
ENV=None


def require(test,message):
    if not test:raise ValueError(message)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest(raw):return sha256(raw).hexdigest()


def atomic_json(path,value):
    path=Path(path);temp=path.with_suffix(path.suffix+'.writing')
    temp.write_bytes(canonical(value)+b'\n');temp.replace(path)


def hashes(directory):
    return {p.name:digest(p.read_bytes()) for p in sorted(Path(directory).glob('*.py'))}


def exact_job(job):return list(map(str,job))


def template_intervals(template):
    cursor=F(0);out=[]
    for row in template['entries']:
        require(len(row)==4,'Malformed source interval')
        a,b=map(F,row[:2]);require(a==cursor and 0<=a<b<1,'Source angular gap')
        out.append((a,b));cursor=b
    require(out and cursor*cursor+2*cursor>1,'Source intervals do not cover pi/4')
    return out


def make_proxy(certificate,optional=None):
    """A pointwise smaller captured-site rule with identical weights/budgets."""
    out=deepcopy(certificate)
    if optional is not None:
        require(F(optional['L'])==F(certificate['L']),'Proxy container differs')
        require(len(optional['point_orbits'])==len(certificate['point_orbits']),'Proxy site orbit count differs')
        for p,q in zip(certificate['point_orbits'],optional['point_orbits']):
            require(all(F(p[i],certificate['coordinate_denominator'])==F(q[i],optional['coordinate_denominator'])
                        for i in (0,1)),'Proxy changes a site or its index')
        require(len(optional['charge_orbits'])==len(certificate['charge_orbits']),'Proxy feature count differs')
    for i,atom in enumerate(certificate['charge_orbits']):
        if atom.get('kind')!='majority_hull':
            if optional is not None:
                p=deepcopy(optional['charge_orbits'][i]);p['weight']=atom['weight']
                require(p==atom,'Proxy changes a non-majority rule')
            continue
        replacement=deepcopy(atom if optional is None else optional['charge_orbits'][i])
        if optional is None:replacement['kind']='threshold'
        require(replacement.get('kind','threshold') in ('threshold','convex_clique'),'Unsupported majority proxy')
        require(replacement['sets']==atom['sets'] and replacement['threshold']==atom['threshold'],
                'Proxy changes majority group or threshold')
        require(not replacement.get('multiset',False),'Majority proxy cannot repeat slots')
        replacement['weight']=atom['weight'];out['charge_orbits'][i]=replacement
    return out


def initialize(directory):
    global ENV
    directory=Path(directory);manifest=json.loads((directory/'run.json').read_text())
    checker=directory/'checker'
    require(hashes(checker)==manifest['checker_sha256'],'Frozen checker changed')
    require(digest(Path(__file__).read_bytes())==manifest['builder_sha256'],'Builder changed')
    sys.path.insert(0,str(checker))
    for filename in manifest['checker_sha256']:
        stem=filename[:-3]
        if stem in sys.modules:
            location=getattr(sys.modules[stem],'__file__',None)
            require(location is not None and Path(location).resolve()==(checker/filename).resolve(),
                    'Wrong cached checker dependency: '+stem)
    staged=importlib.import_module('majority_staged')
    probe=importlib.import_module('majority_probe')
    discrete=importlib.import_module('exact_mixed')
    sweep=importlib.import_module('integer_sweep')
    patches=importlib.import_module('majority_patches')
    for module in (staged,probe,discrete,sweep,patches):
        require(Path(module.__file__).resolve().parent==checker.resolve(),'Wrong checker import')
    for filename in manifest['checker_sha256']:
        stem=filename[:-3]
        if stem in sys.modules:
            location=getattr(sys.modules[stem],'__file__',None)
            require(location is not None and Path(location).resolve()==(checker/filename).resolve(),
                    'Wrong imported checker dependency: '+stem)
    staged.FIRST_PATCH_NODE_LIMIT=manifest['first_patch_node_limit']
    staged.FINAL_PATCH_NODE_LIMIT=manifest['final_patch_node_limit']
    c=json.loads((directory/'proposal.json').read_text())
    require(digest(canonical(c))==manifest['fixed_proposal_sha256'],'Frozen proposal changed')
    template=json.loads((directory/'template.json').read_text())
    require(digest(canonical(template))==manifest['template_sha256'],'Angular template changed')
    intervals=template_intervals(template);A,L=F(c['A']),F(c['L']);margin=F(manifest['margin'])
    entries=[]
    for a,b in intervals:
        t,B,H=probe.interval_job(A,L,a,b,margin)
        entries.append([str(a),str(b),str(t),str(B)])
    prepared=deepcopy(c);prepared['entries']=entries
    data,jobs,_=staged.validate(prepared)
    optional=None
    if manifest['proxy_sha256'] is not None:
        raw=(directory/'proxy.json').read_bytes()
        require(digest(raw)==manifest['proxy_sha256'],'Frozen captured proxy changed')
        optional=json.loads(raw)
    proxy=make_proxy(prepared,optional);proxy_data,proxy_jobs,_=discrete.validate(proxy)
    require(jobs==proxy_jobs,'Proxy has different core jobs')
    ENV=dict(directory=directory,manifest=manifest,c=c,intervals=intervals,data=data,proxy_data=proxy_data,
             staged=staged,probe=probe,discrete=discrete,sweep=sweep,true_charge=patches.true_charge,
             A=A,L=L,margin=margin,required=c['minimum_units'])


def parent_checks(center,angles):
    """Exact full-parent evaluations; absence of a deficit is not a proof."""
    e=ENV;data=e['data'];A,L=e['A'],e['L'];D=data[4];LD=int(L*D)
    scale=lcm(2*D,(A/2).denominator);factor=scale//(2*D);results=[]
    for t in sorted(set(angles)):
        p,q=t.numerator,t.denominator;C,S,R=q*q-p*p,2*p*q,q*q+p*p
        radius=A*(abs(C)+abs(S))/(2*R)
        x,y=(max(radius,min(L-radius,F(z))) for z in center)
        require(radius<=x<=L-radius and radius<=y<=L-radius,'Parent is outside walls')
        uv=[(factor*(C*(2*a-LD)+S*(2*b-LD)),factor*(-S*(2*a-LD)+C*(2*b-LD))) for a,b in data[0]]
        half=int(A*scale/2)*R
        point=(scale*(C*(x-L/2)+S*(y-L/2)),scale*(-S*(x-L/2)+C*(y-L/2)))
        charge=e['true_charge'](data,uv,half,point)
        results.append(dict(halfangle=str(t),center=[str(x),str(y)],parent_side=str(A),
                            contained=True,charge_units=charge,deficient=charge<e['required']))
    return results


def check_receipt(receipt,required):
    require(isinstance(receipt,dict) and receipt.get('status') in ('PASS','FAIL'),'Malformed exact receipt')
    for name in ('minimum_units','cells','slabs'):
        require(type(receipt.get(name)) is int and receipt[name]>=0,'Invalid exact receipt '+name)
    if receipt['status']=='PASS':require(receipt['minimum_units']>=required,'PASS is below required charge')


def evaluate(a,b):
    e=ENV;start=time.monotonic()
    job=e['probe'].interval_job(e['A'],e['L'],a,b,e['margin']);t,B,H=job
    entry=[str(a),str(b),str(t),str(B)]
    identity=dict(context_sha256=e['manifest']['context_sha256'],entry=entry,job=exact_job(job))
    key=digest(canonical(identity));path=e['directory']/'nodes'/(key+'.json')
    if path.exists():
        result=json.loads(path.read_text())
        require(all(result.get(k)==v for k,v in identity.items()),'Cached node belongs to another job')
        check_receipt(result['receipt'],e['required'])
        require((result['outcome']=='PASS')==(result['receipt']['status']=='PASS'),'Cached outcome differs')
        return result
    arrays=e['discrete'].geometry(*e['proxy_data'],*job)
    minimum,cells,_=e['sweep'].accumulate(*arrays)
    receipt=dict(status='PASS' if minimum>=e['required'] else 'FAIL',minimum_units=int(minimum),
                 cells=int(cells),slabs=int(sum(x>=0 for x in arrays[-2])),stage='captured_proxy')
    proxy_minimum=receipt['minimum_units']
    if receipt['status']!='PASS':receipt=e['staged'].verify_row(e['data'],job,e['required'])
    check_receipt(receipt,e['required']);parents=[]
    outcome='PASS' if receipt['status']=='PASS' else 'CORE_UNRESOLVED'
    if receipt['status']=='FAIL':
        for history in reversed(receipt.get('history',[])):
            answer=history.get('patches',{}).get('answer',{})
            if answer.get('status')=='COUNTEREXAMPLE' and 'world_center' in answer:
                parents=parent_checks(answer['world_center'],(a,t,b))
                if any(p['deficient'] for p in parents):outcome='PARENT_DEFICIT'
                break
    result=dict(**identity,key=key,outcome=outcome,receipt=receipt,parent_checks=parents,
                captured_proxy_minimum_units=proxy_minimum,seconds=time.monotonic()-start)
    atomic_json(path,result)
    return result


def partition(a,b,evaluator,max_depth):
    """Pure adaptive control; every accepted leaf needs its own PASS receipt."""
    stack=[(a,b,0)];accepted=[];failed=[];calls=0
    while stack:
        left,right,depth=stack.pop();record=evaluator(left,right);calls+=1
        if record['outcome']=='PASS':accepted.append(record);continue
        if record['outcome']=='PARENT_DEFICIT':
            failed.append(dict(a=str(left),b=str(right),depth=depth,reason='PARENT_DEFICIT',key=record['key']))
            failed.extend(dict(a=str(x),b=str(y),depth=d,reason='UNVISITED_AFTER_PARENT_DEFICIT') for x,y,d in stack)
            break
        if depth>=max_depth:
            failed.append(dict(a=str(left),b=str(right),depth=depth,reason='DEPTH_LIMIT',key=record['key']))
            continue
        mid=(left+right)/2
        stack.extend(((mid,right,depth+1),(left,mid,depth+1)))
    # Exact partition controls also apply to incomplete root results.
    spans=[(F(r['entry'][0]),F(r['entry'][1])) for r in accepted]+[(F(r['a']),F(r['b'])) for r in failed]
    cursor=a
    for left,right in sorted(spans):
        require(left==cursor and left<right,'Adaptive leaf partition has a gap or overlap');cursor=right
    require(cursor==b,'Adaptive leaves do not cover source interval')
    return accepted,failed,calls


def solve(index):
    e=ENV;a,b=e['intervals'][index]
    accepted,failed,calls=partition(a,b,evaluate,e['manifest']['max_depth'])
    result=dict(context_sha256=e['manifest']['context_sha256'],row=index,status='PASS' if not failed else 'INCOMPLETE',
                a=str(a),b=str(b),accepted_keys=[r['key'] for r in accepted],failed=failed,calls=calls)
    atomic_json(e['directory']/'roots'/(str(index)+'.json'),result)
    return result


def create_run(args):
    output=args.output_dir.resolve();require(not output.exists(),'Use a new output directory or --resume')
    raw=args.certificate.read_bytes();c=json.loads(raw)
    require(F(c['bound'])==F(c['L'])/F(c['A']),'Input bound differs from L/A')
    c.pop('exploratory_only',None);c['entries']=[]
    template=json.loads(args.template.read_text());intervals=template_intervals(template)
    selected=sorted(set(args.rows)) if args.rows is not None else list(range(len(intervals)))
    require(selected and all(0<=i<len(intervals) for i in selected),'Invalid selected row')
    require(args.max_depth>=0 and 0<F(args.margin)<F(c['A']),'Invalid refinement settings')
    require(args.first_patch_node_limit>=0 and args.final_patch_node_limit>=0,'Invalid patch node limits')
    output.mkdir(parents=True);(output/'nodes').mkdir();(output/'roots').mkdir();(output/'checker').mkdir()
    for path in args.checker_dir.glob('*.py'):shutil.copyfile(path,output/'checker'/path.name)
    (output/'input-proposal.json').write_bytes(raw)
    atomic_json(output/'proposal.json',c);atomic_json(output/'template.json',template)
    proxy_raw=args.captured_proxy.read_bytes() if args.captured_proxy else None
    if proxy_raw is not None:(output/'proxy.json').write_bytes(proxy_raw)
    manifest=dict(input_proposal_sha256=digest(raw),fixed_proposal_sha256=digest(canonical(c)),
                  template_sha256=digest(canonical(template)),proxy_sha256=digest(proxy_raw) if proxy_raw is not None else None,
                  checker_sha256=hashes(output/'checker'),builder_sha256=digest(Path(__file__).read_bytes()),
                  margin=str(F(args.margin)),max_depth=args.max_depth,selected_rows=selected,total_source_rows=len(intervals),
                  first_patch_node_limit=args.first_patch_node_limit,final_patch_node_limit=args.final_patch_node_limit,
                  collect_parent_deficits=args.collect_parent_deficits)
    manifest['context_sha256']=digest(canonical(manifest));atomic_json(output/'run.json',manifest)
    shutil.copyfile(Path(__file__),output/'build_used.py')
    return output


def assemble():
    e=ENV;directory=e['directory'];manifest=e['manifest'];roots={};leaves=[]
    for index in manifest['selected_rows']:
        path=directory/'roots'/(str(index)+'.json')
        if not path.exists():continue
        root=json.loads(path.read_text())
        require(root['context_sha256']==manifest['context_sha256'] and root['row']==index,'Wrong root checkpoint')
        roots[index]=root
        for key in root['accepted_keys']:
            leaf=json.loads((directory/'nodes'/(key+'.json')).read_text())
            require(leaf['key']==key and leaf['context_sha256']==manifest['context_sha256'],'Wrong leaf identity')
            check_receipt(leaf['receipt'],e['required']);require(leaf['outcome']=='PASS' and leaf['receipt']['status']=='PASS','Unproved leaf')
            leaves.append(leaf)
    complete=len(roots)==len(manifest['selected_rows']) and all(r['status']=='PASS' for r in roots.values())
    full=manifest['selected_rows']==list(range(len(e['intervals'])))
    require(hashes(directory/'checker')==manifest['checker_sha256'],'Frozen checker changed during run')
    require(digest(Path(__file__).read_bytes())==manifest['builder_sha256'],'Builder changed during run')
    parents=[]
    for index,root in roots.items():
        for failure in root['failed']:
            if failure['reason']=='PARENT_DEFICIT':
                record=json.loads((directory/'nodes'/(failure['key']+'.json')).read_text())
                parents.extend(dict(source_row=index,node_key=failure['key'],**p) for p in record['parent_checks'] if p['deficient'])
    atomic_json(directory/'parent-deficits.json',dict(context_sha256=manifest['context_sha256'],
                fixed_proposal_sha256=manifest['fixed_proposal_sha256'],parent_deficits=parents,
                scope='Exactly legal individual parents deficient for frozen weights; not a packing'))
    result=dict(status='INCOMPLETE',context_sha256=manifest['context_sha256'],completed_source_intervals=len(roots),
                selected_source_intervals=len(manifest['selected_rows']),total_source_intervals=len(e['intervals']),
                proved_leaf_intervals=len(leaves),required_units=e['required'],budget_units=e['c']['budget_units'],
                exact_target_side=str(e['L']/e['A']),
                unresolved=[dict(row=i,failed=r['failed']) for i,r in roots.items() if r['failed']],
                missing_source_intervals=[i for i in manifest['selected_rows'] if i not in roots],
                certified_minimum_units=min((r['receipt']['minimum_units'] for r in leaves),default=None),
                exact_deficient_parents=len(parents),
                minimum_interpretation='Certified lower bound on TRUE logical charge, not necessarily its exact minimum',
                root_receipt_sha256={str(i):digest((directory/'roots'/(str(i)+'.json')).read_bytes()) for i in roots},
                scope='Only complete full angular coverage with all exact leaves passing certifies the stated bound')
    if complete:
        leaves.sort(key=lambda r:F(r['entry'][0]));entries=[r['entry'] for r in leaves]
        if full:
            candidate=deepcopy(e['c']);candidate['entries']=entries
            _,jobs,margin=e['staged'].validate(candidate)
            require([exact_job(job) for job in jobs]==[r['job'] for r in leaves],'Final jobs differ from checked leaves')
            minimum=result['certified_minimum_units'];require(11*minimum>candidate['budget_units'],'No strict counting surplus')
            atomic_json(directory/'candidate.json',candidate)
            result.update(status='PASS_FULL_EXACT_ADAPTIVE_TRUE_CATALOGUE',certificate_sha256=digest((directory/'candidate.json').read_bytes()),
                          strict_core_margin=str(margin),counting_surplus_units=11*minimum-candidate['budget_units'])
        else:
            atomic_json(directory/'selected-rows.json',entries)
            result['status']='PASS_SELECTED_EXACT_INTERVALS_NOT_GLOBAL'
    atomic_json(directory/'RESULT.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('certificate',type=Path)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--checker-dir',type=Path,default=DEFAULT_CHECKER)
    p.add_argument('--template',type=Path,default=DEFAULT_TEMPLATE);p.add_argument('--captured-proxy',type=Path)
    p.add_argument('--workers',type=int,default=3);p.add_argument('--max-depth',type=int,default=20)
    p.add_argument('--first-patch-node-limit',type=int,default=5000)
    p.add_argument('--final-patch-node-limit',type=int,default=100000)
    p.add_argument('--collect-parent-deficits',action='store_true',
                   help='Diagnostic mode: continue other source intervals after a genuine parent deficit')
    p.add_argument('--margin',default='1/1000000000000');p.add_argument('--rows',type=int,nargs='+')
    p.add_argument('--resume',action='store_true');args=p.parse_args();require(args.workers>=1,'Positive worker count required')
    directory=args.output_dir.resolve()
    if not args.resume:directory=create_run(args)
    else:
        manifest=json.loads((directory/'run.json').read_text())
        require(digest(args.certificate.read_bytes())==manifest['input_proposal_sha256'],'Resume proposal differs')
    initialize(directory);manifest=ENV['manifest'];tasks=[]
    for index in manifest['selected_rows']:
        path=directory/'roots'/(str(index)+'.json')
        if not path.exists():tasks.append(index)
    start=time.monotonic()
    if args.workers==1:
        iterator=map(solve,tasks)
        for done,record in enumerate(iterator,1):
            if done%100==0 or record['status']!='PASS':print('EXACT_ROOT',record['row'],record['status'],'leaves',len(record['accepted_keys']),flush=True)
            if not manifest['collect_parent_deficits'] and any(f['reason']=='PARENT_DEFICIT' for f in record['failed']):break
    elif tasks:
        with mp.get_context('spawn').Pool(args.workers,initialize,(str(directory),)) as pool:
            for done,record in enumerate(pool.imap_unordered(solve,tasks),1):
                if done%100==0 or record['status']!='PASS':print('EXACT_ROOT',record['row'],record['status'],'leaves',len(record['accepted_keys']),flush=True)
                if not manifest['collect_parent_deficits'] and any(f['reason']=='PARENT_DEFICIT' for f in record['failed']):break
    result=assemble();result['seconds_this_invocation']=time.monotonic()-start
    atomic_json(directory/'RESULT.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('root_receipt_sha256','missing_source_intervals','unresolved')},indent=2))


if __name__=='__main__':main()
