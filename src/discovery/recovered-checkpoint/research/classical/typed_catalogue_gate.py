#!/usr/bin/env python3
"""Assemble complete typed catalogues; only a complete exact replay proves PASS.

The existing selected probe and its dependencies are unchanged. Receipt minima
are not trusted as proofs. Assembly checks their schema and complete coverage,
then produces a frozen, explicitly pending-replay packet. The replay command
recomputes every geometric query before emitting the sole full-proof status.
"""
from fractions import Fraction as F
from pathlib import Path
from hashlib import sha256
import argparse,importlib.util,json,re,shutil,sys,time

ROOT=Path(__file__).resolve().parents[2]
APPROVED={
 'research/type_probe/probe.py':'fc5cb82d5976b612c14ac1b819943addae79308889ab15a6c666011cf9b9b050',
 'research/classical/type_domains.py':'136c13402296d1275352499296d882bfac4df1b0994cc282edd84002c4f6a5ae',
 'research/type_probe/frozen_checker/charge_geometry.py':'a2d3fccd0abbfa06928e2b9d9a1e1078d2808b40f0f49fe95fcd031bd646d577',
 'research/type_probe/frozen_checker/exact_mixed.py':'e09b349bf9b97f47e825215a5b13ccd3ccae71b05c97c6a6ea4ffbce34dac409',
 'research/type_probe/frozen_checker/integer_sweep.py':'3a2bfd8892a9693b4dfca72e4d8e547a7be8775b22306740f4e6b63d0928b34b',
}
PENDING='COMPLETE_TYPED_CATALOGUE_REPLAY_REQUIRED'
COMPLETE='PASS_EXACT_COMPLETE_TWO_SYSTEM_TYPED_CERTIFICATE'
ROLE_DOMAINS={'A':{'single'},'B':{'global','multi'}}


def need(ok,message):
    if not ok:raise ValueError(message)


def digest(path):return sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    if isinstance(value,F):return str(value)
    raise TypeError(type(value).__name__)


def canonical(value):return json.dumps(value,default=encode,sort_keys=True,separators=(',',':'))


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(value,default=encode,indent=2)+'\n');tmp.replace(path)


def local(base,relative):
    path=(base/relative).resolve()
    need(path.is_relative_to(base.resolve()),'Packet path escapes its root')
    return path


def check_dependencies(base):
    for name,expected in APPROVED.items():need(digest(local(base,name))==expected,'Unapproved dependency: '+name)


def load_probe(base):
    """Imports only the reviewed and hash-pinned source layout."""
    base=Path(base).resolve();check_dependencies(base)
    path=base/'research/type_probe/probe.py'
    # The probe itself refuses preimported dependencies from another root.
    spec=importlib.util.spec_from_file_location('typed_catalogue_pinned_probe',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def validate_vectors(vectors,probe):
    need(set(vectors)=={'A','B'},'Exactly two vector roles required')
    settings={};expanded={}
    for role,c in vectors.items():
        L,A=F(c['L']),F(c['A']);side=F(c['bound']);window=F(c['conditional_type_probe']['window_side_unit'])
        need(L==F(191,50) and 0<A<L and side==L/A,'Container, parent, or bound mismatch')
        need(type(c['weight_denominator']) is int and c['weight_denominator']>0,'Bad weight denominator')
        need(type(c['budget_units']) is int and c['budget_units']>=0,'Bad budget')
        config=c['conditional_type_probe'];gates=config['thresholds']
        need(set(config)=={'role','window_side_unit','thresholds','counting_surplus_units','global_bound_proved'}
             and config['global_bound_proved'] is False,'Unsupported typed-label schema; reference-side types are not approved')
        need(config['role']==role and set(gates)==ROLE_DOMAINS[role],'Wrong role or threshold domains')
        need(all(type(v) is int and v>=0 for v in gates.values()),'Nonintegral threshold')
        surplus=(11*gates['single'] if role=='A' else 10*gates['global']+gates['multi'])-c['budget_units']
        need(surplus>0,'Strict conditional counting gate failed')
        need(config['counting_surplus_units']==surplus,'Stored surplus differs')
        if role=='B':need(gates['multi']>=gates['global'],'Nonsingle threshold is below global baseline')
        a=A*window;W=2*a-L
        need(0<A<a<L and W>0 and W*W>2*A*A,'Corner windows do not cover every parent')
        # These extra premises match the currently approved domain helper.
        need(W<2*A and window>2 and 2*(window-2)**2<1,'Outside approved window-helper regime')
        expanded[role]=probe.checker.expand(c)
        settings[role]=(L,A,side,window)
    need(settings['A']==settings['B'],'Systems use different parent or type geometry')
    return settings['A'],expanded


def validate_node(node,role,c,certificate_hash,probe,root=True,depth=0):
    """Reconstruct all metadata and return only passing positive-width leaves."""
    need(node.get('parent_only') is False,'Point-parent diagnostics are not interval proofs')
    if root:need(node.get('role')==role and node.get('certificate_sha256')==certificate_hash,'Root vector binding differs')
    if 'role' in node:need(node['role']==role,'Child role differs')
    if 'certificate_sha256' in node:need(node['certificate_sha256']==certificate_hash,'Child vector binding differs')
    need(type(node.get('source_row')) is int and node['source_row']>=0,'Invalid source-row tag')
    need(node.get('refinement_depth')==depth,'Refinement depth differs')
    lo,hi=map(F,node['interval']);need(0<=lo<hi<1,'Angle interval has invalid width/range')
    t,B,H=probe.row_parameters(F(c['L']),F(c['A']),(lo,hi))
    need((F(node['half_angle_t']),F(node['core_side']),F(node['center_halfwidth']))==(t,B,H),'Core job differs from exact reconstruction')
    boxes=probe.covers(F(c['L']),F(c['A']),lo,hi,F(c['conditional_type_probe']['window_side_unit']))
    gates=c['conditional_type_probe']['thresholds'];records=node['domains']
    need(len(records)==len(gates) and {d['domain'] for d in records}==set(gates),'Missing or duplicate domain')
    for d in records:
        name=d['domain'];need(tuple(map(F,d['world_box']))==boxes[name],'Parent-derived domain box differs')
        need(type(d['required_units']) is int and d['required_units']==gates[name],'Domain threshold differs')
        need(type(d['minimum_units']) is int and type(d['passed']) is bool,'Invalid minimum/pass type')
        need(d['passed']==(d['minimum_units']>=d['required_units']),'Pass flag does not match its minimum')
        need(type(d['cells']) is int and d['cells']>0 and type(d['slabs']) is int and d['slabs']>0,'Empty domain query')
    status=node.get('interval_status')
    if status=='PASS_RESTRICTED_CORE_INTERVAL':
        need(not node.get('refinements') and all(d['passed'] for d in records),'Leaf does not pass every required domain')
        return [dict(role=role,source_row=node['source_row'],interval=[lo,hi],half_angle_t=t,core_side=B,
                     center_halfwidth=H,domains=[{k:d[k] for k in ('domain','world_box','required_units','minimum_units','cells','slabs')}
                                               for d in sorted(records,key=lambda x:x['domain'])])]
    need(status=='PASS_BY_REFINED_INTERVALS','Receipt is incomplete or failed')
    children=node.get('refinements',[]);need(len(children)==2,'Refined interval requires two children')
    first,last=children
    need(F(first['interval'][0])==lo and F(first['interval'][1])==F(last['interval'][0]) and F(last['interval'][1])==hi,
         'Children do not exactly partition their parent')
    need(all(child.get('source_row')==node['source_row'] for child in children),'Child source-row tag differs')
    return sum((validate_node(child,role,c,certificate_hash,probe,False,depth+1) for child in children),[])


def complete_partitions(jobs):
    need(jobs,'No interval receipts')
    reports={}
    for role in ('A','B'):
        rows=sorted((r for r in jobs if r['role']==role),key=lambda r:F(r['interval'][0]));cursor=F(0)
        need(rows,'Missing vector role '+role)
        for row in rows:
            lo,hi=map(F,row['interval']);need(lo==cursor and hi>lo,'Gap or overlap in '+role+' angle partition');cursor=hi
            need({d['domain'] for d in row['domains']}==ROLE_DOMAINS[role],'Missing typed-domain partition')
        need(cursor<1 and cursor*cursor+2*cursor>1,'Incomplete angular endpoint in '+role)
        reports[role]=dict(intervals=len(rows),angle_endpoint=str(cursor),domains=sorted(ROLE_DOMAINS[role]))
    return reports


def collect_runs(runs,probe):
    vectors={};raw_vectors={};hashes={};roots=[];jobs=[];seen=set();origins=[]
    for directory in runs:
        directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_bytes())
        need(manifest['dependencies']==APPROVED,'Run did not use the approved immutable dependencies')
        need(digest(directory/'probe_used.py')==APPROVED['research/type_probe/probe.py'],'Saved probe source changed')
        need(digest(directory/'type_domains_used.py')==APPROVED['research/classical/type_domains.py'],'Saved domain source changed')
        for role in ('A','B'):
            raw=(directory/f'vector-{role}.json').read_bytes();h=sha256(raw).hexdigest();c=json.loads(raw)
            m=manifest['vectors'][role]
            need(h==m['certificate_sha256'],'Vector hash differs from run manifest')
            need(m['thresholds']==c['conditional_type_probe']['thresholds'] and m['budget_units']==c['budget_units'],'Manifest vector metadata differs')
            need(F(manifest['side'])==F(c['bound']) and F(manifest['window_side_unit'])==F(c['conditional_type_probe']['window_side_unit']),'Run geometry differs')
            if role in hashes:need(hashes[role]==h,'Cannot combine different frozen vectors')
            else:vectors[role]=c;raw_vectors[role]=raw;hashes[role]=h
        files=sorted(directory.glob('row-*-?.json'));need(files,'Run contains no row receipts')
        for path in files:
            match=re.fullmatch(r'row-(\d+)-([AB])\.json',path.name);need(match is not None,'Unexpected receipt filename')
            raw=path.read_bytes();r=json.loads(raw);role=match[2]
            need(r.get('source_row')==int(match[1]),'Receipt row tag differs from filename')
            key=(role,r['source_row']);need(key not in seen,'Duplicate source/vector root');seen.add(key)
            jobs.extend(validate_node(r,role,vectors[role],hashes[role],probe));roots.append((raw,str(path)))
        origins.append(dict(directory=str(directory),manifest_sha256=digest(directory/'manifest.json')))
    settings,expanded=validate_vectors(vectors,probe);partitions=complete_partitions(jobs)
    return vectors,raw_vectors,hashes,roots,jobs,settings,expanded,partitions,origins


def assemble(runs,output,source_root=ROOT):
    output=Path(output);need(not output.exists() or not any(output.iterdir()),'Use a fresh empty output directory')
    probe=load_probe(source_root)
    vectors,raws,hashes,roots,jobs,settings,_,partitions,origins=collect_runs(runs,probe)
    output.mkdir(parents=True,exist_ok=True)
    for name in APPROVED:
        destination=output/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(Path(source_root)/name,destination)
    check_dependencies(output)
    gate=output/'research/classical/typed_catalogue_gate.py';shutil.copyfile(Path(__file__),gate)
    for role,raw in raws.items():(output/f'vector-{role}.json').write_bytes(raw)
    saved=[]
    for index,(raw,origin) in enumerate(roots):
        name=f'receipts/root-{index:06d}.json';path=output/name;path.parent.mkdir(exist_ok=True);path.write_bytes(raw)
        saved.append(dict(path=name,sha256=sha256(raw).hexdigest(),origin=origin))
    L,A,side,window=settings
    catalogue=dict(schema='two-system-typed-catalogue-v1',status=PENDING,global_bound_proved=False,
                   L=str(L),A=str(A),bound=str(side),window_side_unit=str(window),
                   vectors={role:dict(path=f'vector-{role}.json',sha256=hashes[role]) for role in ('A','B')},
                   dependencies=dict(APPROVED),gate_sha256=digest(gate),receipts=saved,
                   partitions=partitions,jobs=jobs,input_runs=origins,
                   scope='Complete receipt/schema/coverage assembly only. Every geometric minimum must be recomputed by the replay command before a proof PASS.')
    write(output/'catalogue.json',catalogue)
    return catalogue


def replay(bundle,output):
    bundle=Path(bundle).resolve();raw=(bundle/'catalogue.json').read_bytes();catalogue=json.loads(raw)
    need(not Path(output).exists(),'Use a fresh replay output file')
    need(catalogue.get('schema')=='two-system-typed-catalogue-v1' and catalogue.get('status')==PENDING
         and catalogue.get('global_bound_proved') is False,'Not a pending complete typed catalogue')
    need(catalogue['dependencies']==APPROVED,'Catalogue dependencies differ')
    gate=local(bundle,'research/classical/typed_catalogue_gate.py')
    need(digest(gate)==catalogue['gate_sha256']==digest(__file__),'Replay gate source changed')
    probe=load_probe(bundle);vectors={};hashes={}
    for role in ('A','B'):
        record=catalogue['vectors'][role];path=local(bundle,record['path'])
        need(digest(path)==record['sha256'],'Frozen vector changed');hashes[role]=record['sha256'];vectors[role]=json.loads(path.read_bytes())
    settings,data=validate_vectors(vectors,probe);L,A,side,window=settings
    need(tuple(map(F,(catalogue['L'],catalogue['A'],catalogue['bound'],catalogue['window_side_unit'])))==settings,'Catalogue geometry changed')
    jobs=[];seen=set()
    for record in catalogue['receipts']:
        path=local(bundle,record['path']);need(digest(path)==record['sha256'],'Frozen row receipt changed')
        node=json.loads(path.read_bytes());role=node.get('role');need(role in ('A','B'),'Bad receipt role')
        key=(role,node['source_row']);need(key not in seen,'Duplicate receipt root');seen.add(key)
        jobs.extend(validate_node(node,role,vectors[role],hashes[role],probe))
    partitions=complete_partitions(jobs)
    need(partitions==catalogue['partitions'] and canonical(jobs)==canonical(catalogue['jobs']),'Flattened jobs differ from frozen receipt trees')
    started=time.monotonic();checked=[];minima={'A':{},'B':{}}
    for index,job in enumerate(jobs):
        role=job['role'];t,B,H=(F(job[k]) for k in ('half_angle_t','core_side','center_halfwidth'))
        _,meta=probe.checker.geometry(*data[role],t,B,H,meta=True)
        for domain in job['domains']:
            poly=probe.domains.projected_box(tuple(map(F,domain['world_box'])),L,meta)
            arrays,_=probe.restricted_arrays(meta,poly);minimum,cells,_=probe.accumulate(*arrays)
            slabs=int((arrays[-2]>=0).sum());minimum=int(minimum)
            need(minimum>=domain['required_units'],'Exact typed coverage fails at job '+str(index)+' '+role+'/'+domain['domain'])
            need((minimum,int(cells),slabs)==(domain['minimum_units'],domain['cells'],domain['slabs']),'Retained minimum/cell receipt differs from exact replay')
            name=domain['domain'];minima[role][name]=min(minima[role].get(name,minimum),minimum)
            checked.append(dict(job=index,role=role,domain=name,minimum_units=minimum,cells=int(cells),slabs=slabs))
        if index%100==0:print('REPLAY',index+1,'/',len(jobs),'seconds',round(time.monotonic()-started,2),flush=True)
    # Recheck the count gates at the actual replay minima as well.
    surpluses={'A':11*minima['A']['single']-vectors['A']['budget_units'],
               'B':10*minima['B']['global']+max(minima['B']['multi'],minima['B']['global'])-vectors['B']['budget_units']}
    need(min(surpluses.values())>0,'Actual replay minima do not exclude both counting cases')
    check_dependencies(bundle)
    need(digest(bundle/'catalogue.json')==sha256(raw).hexdigest(),'Catalogue changed during replay')
    need(digest(gate)==catalogue['gate_sha256']==digest(__file__),'Gate changed during replay')
    for record in catalogue['vectors'].values():need(digest(local(bundle,record['path']))==record['sha256'],'Vector changed during replay')
    for record in catalogue['receipts']:need(digest(local(bundle,record['path']))==record['sha256'],'Receipt changed during replay')
    result=dict(status=COMPLETE,global_bound_proved=True,bound=str(side),
                catalogue_sha256=sha256(raw).hexdigest(),gate_sha256=digest(__file__),dependencies=APPROVED,
                vector_sha256=hashes,partitions=partitions,domain_minimum_units=minima,
                counting_surplus_units=surpluses,domain_queries=len(checked),rows=checked,
                seconds=time.monotonic()-started,
                scope='Complete exact replay of both immutable charge systems on all required typed domains and angular partitions. A handles all-single packings; B handles packings with at least one nonsingle.')
    write(output,result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('assemble');p.add_argument('--runs',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('replay');p.add_argument('--bundle',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=assemble(args.runs,args.output) if args.command=='assemble' else replay(args.bundle,args.output)
    print(json.dumps({k:v for k,v in result.items() if k not in ('jobs','rows','receipts')},indent=2))
