"""Frozen-snapshot selected-row timings; never a complete packing certificate."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
from io import BytesIO
from math import ceil
from pathlib import Path
import json,time
import numpy as np
import exact_mixed
import majority_staged
from majority_probe import load_probe,target_job
from charge_geometry import require
from integer_sweep import accumulate


def main():
    root=Path(__file__).resolve().parents[2];outdir=Path(__file__).with_name('benchmarks-safe-round3')
    outdir.mkdir(exist_ok=True)
    weights_path=root/'research/reweight/fast_3.8755_root_conditional_round3_safe.npz'
    archive=weights_path.read_bytes();weights=np.load(BytesIO(archive))['weights'].copy()
    np.save(outdir/'frozen-weights.npy',weights)
    true_path=root/'research/features/candidate-majority-round3.json'
    proxy_path=root/'research/stromquist/candidate-round3-captured-proxy.json'
    true_raw=true_path.read_bytes();proxy_raw=proxy_path.read_bytes()
    c=json.loads(true_raw);p=json.loads(proxy_raw);den=10**10
    require(len(weights)==len(c['point_orbits'])+len(c['charge_orbits']),'Weight-vector length mismatch')
    require(c['coordinate_denominator']==p['coordinate_denominator'] and c['L']==p['L'],'Proxy lattice mismatch')
    require([a[:2] for a in c['point_orbits']]==[a[:2] for a in p['point_orbits']],'Proxy point mismatch')
    require(len(c['charge_orbits'])==len(p['charge_orbits']),'Proxy feature count mismatch')
    for first,second in zip(c['charge_orbits'],p['charge_orbits']):
        require(first['sets']==second['sets'] and first['threshold']==second['threshold'],'Proxy group mismatch')
        if first.get('kind')=='majority_hull':
            require(second.get('kind')=='convex_clique' and len(first['sets'][0])==2*first['threshold']-1,
                    'Captured feature does not correspond to a true majority')
        else:
            require(first.get('kind','threshold')==second.get('kind','threshold'),'Other feature changed')
            require(all(first.get(k)==second.get(k) for k in ('edge_sets','support_sets','multiset')),
                    'Other feature support changed')
    integer_weights=[ceil(F(float(w))*den) for w in weights]
    require(all(w>=0 for w in integer_weights),'Negative frozen weight')
    LD=int(F(c['L'])*c['coordinate_denominator']);budget=0
    for i,(first,second) in enumerate(zip(c['point_orbits'],p['point_orbits'])):
        first[2]=second[2]=integer_weights[i];x,y,w=first
        budget+=w*len({(a,b) for u,v in ((x,y),(y,x)) for a in (u,LD-u) for b in (v,LD-v)})
    offset=len(c['point_orbits'])
    for i,(first,second) in enumerate(zip(c['charge_orbits'],p['charge_orbits'])):
        first['weight']=second['weight']=integer_weights[offset+i]
        budget+=len(first['sets'])*(len(first['sets'][0])//first['threshold'])*first['weight']
    threshold=budget//11+1
    for candidate in (c,p):
        candidate.update(weight_denominator=den,budget_units=budget,minimum_units=threshold,
                         A=str(F(candidate['L'])/F('3.8754')),bound='3.8754',entries=[],
                         exploratory_only='Frozen selected-row timing/coverage probe; no complete catalogue')
    true_frozen=outdir/'true-probe.json';proxy_frozen=outdir/'captured-probe.json'
    true_frozen.write_text(json.dumps(c,separators=(',',':'))+'\n')
    proxy_frozen.write_text(json.dumps(p,separators=(',',':'))+'\n')
    c,old,data,oldjobs,margin=load_probe(true_frozen)
    # This checks every listed captured support against every disjoint majority
    # subset. Hence the captured proxy is a pointwise lower bound on true charge.
    captured=exact_mixed.expand(p)
    majority_staged.FIRST_PATCH_NODE_LIMIT=2000
    majority_staged.FINAL_PATCH_NODE_LIMIT=10000
    report=dict(status='SELECTED_ROW_BENCHMARK_IN_PROGRESS',source_archive=str(weights_path),
                source_archive_sha256=sha256(archive).hexdigest(),source_true_sha256=sha256(true_raw).hexdigest(),
                source_proxy_sha256=sha256(proxy_raw).hexdigest(),budget_units=budget,weight_denominator=den,
                threshold_units=threshold,positive_variables=sum(w>0 for w in integer_weights),
                exact_ceiling_of_binary_float_weights=True,first_patch_node_limit=2000,
                final_patch_node_limit=10000,rows=[],scope='Selected rigorously contained intervals only; no full catalogue or new bound')
    destination=outdir/'benchmark.json';test45=False
    tasks=[(row,F('3.8754')) for row in (0,1000,4000,6000,9000,11000,12027)]
    for row,target in tasks:
        candidate=deepcopy(c);candidate['A']=str(F(c['L'])/target)
        job=target_job(candidate,old,oldjobs,margin,row);start=time.monotonic()
        arrays=exact_mixed.geometry(*captured,*job);minimum,cells,winner=accumulate(*arrays)
        first_seconds=time.monotonic()-start
        if minimum>=threshold:
            result=dict(status='PASS',minimum_units=int(minimum),cells=int(cells),
                        slabs=int(sum(v>=0 for v in arrays[-2])),stage='captured_pattern_proxy')
        else:result=majority_staged.verify_row(data,job,threshold)
        result.update(row=row,target_side=str(target),core_halfangle=str(job[0]),
                      captured_proxy_minimum_units=int(minimum),captured_proxy_seconds=first_seconds,
                      total_seconds=time.monotonic()-start)
        report['rows'].append(result)
        if target==F('3.8754') and result['status']=='PASS' and result['minimum_units']>=threshold+10**6 and not test45:
            tasks.append((row,F('3.87545')));test45=True
        destination.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('row','target_side','status','stage','minimum_units',
                                              'captured_proxy_minimum_units','total_seconds')}),flush=True)
    report['status']='SELECTED_ROW_BENCHMARK_COMPLETE_NOT_A_GLOBAL_PROOF'
    destination.write_text(json.dumps(report,indent=2)+'\n')
    print('SAVED',str(destination),flush=True)


if __name__=='__main__':main()
