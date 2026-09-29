"""Exact premises/Boolean audit for captured-pattern candidates, not coverage."""
from hashlib import sha256
from pathlib import Path
from math import comb
import argparse,json,time
from exact_mixed import expand,feature_coefficients
from charge_geometry import clique_coefficients,require


def structural_fingerprint(c):
    keys=('kind','threshold','sets','edge_sets','support_sets','multiset')
    structure={'L':c['L'],'coordinate_denominator':c['coordinate_denominator'],
               'point_orbits':[p[:2] for p in c['point_orbits']],
               'charge_orbits':[{k:a[k] for k in keys if k in a} for a in c['charge_orbits']]}
    return sha256(json.dumps(structure,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def audit(path,output):
    start=time.monotonic();raw=Path(path).read_bytes();c=json.loads(raw);data=expand(c)
    models=patterns=0
    for atom in c['charge_orbits']:
        kind=atom.get('kind','threshold');k=atom.get('threshold')
        for gi,group in enumerate(atom['sets']):
            n=len(group)
            if kind in ('threshold','floor'):
                coefficients=feature_coefficients(n,k,kind)
                for mask in range(1<<n):
                    h=mask.bit_count();direct=int(h>=k) if kind=='threshold' else h//k
                    require(sum(comb(h,j)*coefficients[j] for j in range(h+1))==direct,
                            'Binomial captured-charge disagreement')
            else:
                require(kind in ('convex_clique','edge_or'),'Unexpected feature kind')
                local={site:i for i,site in enumerate(group)}
                edges=[tuple(local[i] for i in support)
                       for support in atom.get('edge_sets',[[] for _ in atom['sets']])[gi]]
                supports=[tuple(local[i] for i in support)
                          for support in atom.get('support_sets',[[] for _ in atom['sets']])[gi]]
                threshold=k if kind=='convex_clique' else None
                values=list(clique_coefficients(n,edges,threshold,supports))
                for bit in range(n):
                    for mask in range(1<<n):
                        if mask&(1<<bit):values[mask]+=values[mask^(1<<bit)]
                for mask,value in enumerate(values):
                    captured={i for i in range(n) if mask&(1<<i)}
                    direct=int((threshold is not None and len(captured)>=threshold)
                               or any(all(i in captured for i in support) for support in edges+supports))
                    require(value==direct,'Captured-support Boolean disagreement')
            models+=1;patterns+=1<<n
    result=dict(status='PASS_EXACT_CAPTURED_PROXY_PREMISES_AND_BOOLEAN_IDENTITIES',
                certificate_sha256=sha256(raw).hexdigest(),feature_structure_sha256=structural_fingerprint(c),
                physical_sites=len(data[0]),physical_feature_models=models,boolean_patterns=patterns,
                signed_terms=len(data[2]),budget_units=c['budget_units'],weight_denominator=c['weight_denominator'],
                absolute_expanded_units=sum(data[1])+sum(map(abs,data[3])),
                catalogue_rows=len(c.get('entries',[])),catalogue_containment_checked=False,
                scope='Feature geometry, D4, budgets, overflow, and Boolean identities only; no charge sweep or new bound',
                seconds=time.monotonic()-start)
    Path(output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('certificate',type=Path)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    audit(args.certificate,args.output)
