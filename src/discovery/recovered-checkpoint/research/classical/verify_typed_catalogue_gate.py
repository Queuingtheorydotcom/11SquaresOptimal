#!/usr/bin/env python3
"""Small schema/coverage controls, deliberately distinct from geometric proof.

Positive synthetic receipts contain untrusted invented minima. Assembly must
remain pending, and an actual replay must reject them. No positive packing
certificate is manufactured by this test.
"""
from pathlib import Path
from fractions import Fraction as F
from tempfile import TemporaryDirectory
import copy,json,os,shutil,subprocess,sys
import typed_catalogue_gate as gate


def fixture_vectors():
    vectors={}
    for role in ('A','B'):
        gates={'single':1} if role=='A' else {'global':1,'multi':1}
        vectors[role]=dict(L='191/50',A='15280/15501',bound='15501/4000',coordinate_denominator=100,
                           weight_denominator=1,budget_units=1,minimum_units=0,entries=[],
                           point_orbits=[[191,191,1]],charge_orbits=[],
                           conditional_type_probe=dict(role=role,window_side_unit='13229/5000',thresholds=gates,
                                                       counting_surplus_units=10,global_bound_proved=False))
    return vectors


def receipt(probe,c,role,source,lo,hi,certificate_hash,depth=0):
    lo,hi=map(F,(lo,hi));t,B,H=probe.row_parameters(F(c['L']),F(c['A']),(lo,hi))
    boxes=probe.covers(F(c['L']),F(c['A']),lo,hi,F('13229/5000'))
    return dict(role=role,source_row=source,certificate_sha256=certificate_hash,parent_only=False,
                refinement_depth=depth,interval=[str(lo),str(hi)],half_angle_t=str(t),core_side=str(B),
                center_halfwidth=str(H),interval_status='PASS_RESTRICTED_CORE_INTERVAL',
                domains=[dict(domain=name,world_box=list(map(str,boxes[name])),required_units=value,
                              minimum_units=value,passed=True,cells=1,slabs=1)
                         for name,value in c['conditional_type_probe']['thresholds'].items()])


def fixture(path,probe,refined=False):
    path.mkdir();vectors=fixture_vectors();manifest=dict(dependencies=gate.APPROVED,side='15501/4000',window_side_unit='13229/5000',vectors={})
    for role,c in vectors.items():
        target=path/f'vector-{role}.json';gate.write(target,c);h=gate.digest(target)
        manifest['vectors'][role]=dict(certificate_sha256=h,thresholds=c['conditional_type_probe']['thresholds'],budget_units=1)
        for source,(lo,hi) in enumerate(((F(0),F(1,4)),(F(1,4),F(1,2)))):
            row=receipt(probe,c,role,source,lo,hi,h)
            if refined and role=='A' and source==0:
                row['interval_status']='PASS_BY_REFINED_INTERVALS'
                row['refinements']=[receipt(probe,c,role,source,lo,F(1,8),h,1),receipt(probe,c,role,source,F(1,8),hi,h,1)]
            gate.write(path/f'row-{source:05d}-{role}.json',row)
    gate.write(path/'manifest.json',manifest)
    shutil.copyfile(gate.ROOT/'research/type_probe/probe.py',path/'probe_used.py')
    shutil.copyfile(gate.ROOT/'research/classical/type_domains.py',path/'type_domains_used.py')
    return vectors


def main():
    probe=gate.load_probe(gate.ROOT);checks=[]
    with TemporaryDirectory(prefix='typed-gate-controls-') as directory:
        base=Path(directory)
        for refined in (False,True):
            run=base/('positive-refined' if refined else 'positive-flat');fixture(run,probe,refined)
            bundle=base/('bundle-refined' if refined else 'bundle-flat')
            result=gate.assemble([run],bundle)
            gate.need(result['status']==gate.PENDING and result['global_bound_proved'] is False,'Assembly falsely claimed proof')
            checks.append(dict(name='positive schema '+('refined' if refined else 'flat'),result='PENDING_ONLY',jobs=len(result['jobs'])))
        env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='1')
        output=base/'fake-proof.json'
        process=subprocess.run([sys.executable,str(base/'bundle-flat/research/classical/typed_catalogue_gate.py'),
                                'replay','--bundle',str(base/'bundle-flat'),'--output',str(output)],
                               text=True,capture_output=True,env=env,timeout=30)
        gate.need(process.returncode!=0 and 'Exact typed coverage fails' in process.stderr and not output.exists(),
                  'Invented receipt minima passed the mandatory geometric replay: '+process.stderr[-1500:])
        checks.append(dict(name='synthetic full coverage is not a geometric proof',result='REPLAY_REJECTED'))
        mutations={
            'missing terminal A interval':lambda p:(p/'row-00001-A.json').unlink(),
            'missing entire B partition':lambda p:[q.unlink() for q in p.glob('row-*-B.json')],
            'tampered frozen vector':lambda p:(p/'vector-A.json').write_text((p/'vector-A.json').read_text()+' '),
            'tampered frozen probe':lambda p:(p/'probe_used.py').write_text((p/'probe_used.py').read_text()+'\n'),
        }
        edits={
            'point-only diagnostic':lambda r:r.update(parent_only=True),
            'missing elevated domain':lambda r:r['domains'].pop(),
            'false minimum pass':lambda r:r['domains'][0].update(minimum_units=0),
            'changed core side':lambda r:r.update(core_side=str(F(r['core_side'])/2)),
            'wrong parent box':lambda r:r['domains'][0]['world_box'].__setitem__(0,'0'),
            'unproved refinement':lambda r:r.update(interval_status='PASS_BY_REFINED_INTERVALS',refinements=[copy.deepcopy(r)]),
            'failed status':lambda r:r.update(interval_status='FAIL_GENUINE_TYPED_PARENT'),
            'zero interval width':lambda r:r['interval'].__setitem__(1,r['interval'][0]),
            'wrong vector hash':lambda r:r.update(certificate_sha256='0'*64),
            'wrong required threshold':lambda r:r['domains'][0].update(required_units=0),
        }
        for name,edit in edits.items():
            def mutate(path,edit=edit):
                target=path/'row-00000-B.json';r=json.loads(target.read_bytes());edit(r);gate.write(target,r)
            mutations[name]=mutate
        for name in ('angular gap','angular overlap'):
            def mutate(path,name=name):
                c=json.loads((path/'vector-A.json').read_bytes());h=gate.digest(path/'vector-A.json')
                lo=F(3,8) if name=='angular gap' else F(1,8)
                gate.write(path/'row-00001-A.json',receipt(probe,c,'A',1,lo,F(1,2),h))
            mutations[name]=mutate
        for index,(name,mutate) in enumerate(mutations.items()):
            path=base/f'negative-{index}';fixture(path,probe);mutate(path)
            try:gate.assemble([path],base/f'rejected-{index}')
            except (ValueError,KeyError) as error:checks.append(dict(name=name,result='REJECTED',reason=str(error)))
            else:raise ValueError('Invalid workflow accepted: '+name)
        vector_mutations={
            'strict A counting gate':lambda v:v['A']['conditional_type_probe'].update(thresholds={'single':0},counting_surplus_units=-1),
            'B elevated below baseline':lambda v:v['B']['conditional_type_probe'].update(thresholds={'global':2,'multi':1},counting_surplus_units=20),
            'unsupported reference-side labels':lambda v:v['B']['conditional_type_probe'].update(reference_parent_side='1'),
            'changed budget':lambda v:(v['A'].update(budget_units=2),v['A']['conditional_type_probe'].update(counting_surplus_units=9)),
            'nonintegral threshold':lambda v:v['A']['conditional_type_probe']['thresholds'].update(single=True),
            'noncovering corner windows':lambda v:[c['conditional_type_probe'].update(window_side_unit='12/5') for c in v.values()],
        }
        for role in ('A','B'):
            def equality(v,role=role):
                v[role]['budget_units']=11;v[role]['point_orbits'][0][2]=11
                v[role]['conditional_type_probe']['counting_surplus_units']=0
            vector_mutations['equality in '+role+' counting gate']=equality
        for name,mutate in vector_mutations.items():
            vectors=fixture_vectors();mutate(vectors)
            try:gate.validate_vectors(vectors,probe)
            except ValueError as error:checks.append(dict(name=name,result='REJECTED',reason=str(error)))
            else:raise ValueError('Invalid vector premise accepted: '+name)
        real=gate.ROOT/'research/type_probe/window26458-repair2-selected'
        try:gate.assemble([real],base/'rejected-current-selected')
        except ValueError as error:checks.append(dict(name='current selected-only run',result='REJECTED',reason=str(error)))
        else:raise ValueError('Current selected-only run was accepted')
    result=dict(status='PASS_TYPED_CATALOGUE_WORKFLOW_CONTROLS',controls=len(checks),
                gate_sha256=gate.digest(Path(gate.__file__)),dependencies=gate.APPROVED,checks=checks,
                global_bound_proved=False,
                scope='Synthetic positive schema/coverage controls remain pending; exact replay rejects their invented minima. Current selected run and malformed workflows are rejected. No positive global packing proof was attempted.')
    gate.write(Path(__file__).with_name('typed-catalogue-gate-controls.json'),result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
