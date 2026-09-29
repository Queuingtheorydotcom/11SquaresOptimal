#!/usr/bin/env python3
"""Exhaustive exact controls for all supported logical charge families."""
import argparse
from itertools import combinations
from math import comb
import json
from pathlib import Path
from exact_mixed import feature_coefficients


def require(value,message):
    if not value:raise ValueError(message)


def owner_patterns(n):
    """All ownership patterns up to owner relabeling, with 0 unassigned."""
    def recurse(prefix,maximum):
        if len(prefix)==n:
            yield prefix
            return
        for label in range(maximum+2):
            yield from recurse(prefix+(label,),max(maximum,label))
    yield from recurse((),0)


def verify():
    records=[];total_patterns=0;total_owners=0
    expected_owner_counts={1:2,2:5,3:15,4:52,5:203,6:877,7:4140}
    for n in range(1,8):
        subset_masks={j:[sum(1<<i for i in subset)
                         for subset in combinations(range(n),j)]
                      for j in range(n+1)}
        assignments=list(owner_patterns(n))
        require(len(assignments)==expected_owner_counts[n],
                'Canonical ownership enumeration count')
        for k in range(1,n+1):
            for kind in ('threshold','floor'):
                coefficients=feature_coefficients(n,k,kind)
                expected_value=(lambda h:int(h>=k)) if kind=='threshold' else (lambda h:h//k)
                # An independently stated Mobius transform for both kinds.
                direct=tuple(sum((-1)**(j-h)*comb(j,h)*expected_value(h)
                                 for h in range(j+1)) for j in range(n+1))
                require(coefficients==direct,'Binomial inversion disagreement')
                if kind=='floor':
                    summed_thresholds=tuple(sum((-1)**(j-q*k)*comb(j-1,q*k-1)
                                                for q in range(1,j//k+1))
                                            for j in range(n+1))
                    require(coefficients==summed_thresholds,'Floor decomposition disagreement')
                for captured in range(1<<n):
                    charge=sum(coefficients[j]
                               for j,masks in subset_masks.items()
                               for subset in masks if subset & captured == subset)
                    require(charge==expected_value(captured.bit_count()),
                            'Boolean capture identity failed')
                for owners in assignments:
                    counts=[owners.count(label) for label in range(1,max(owners)+1)]
                    total=sum(expected_value(h) for h in counts)
                    require(total<=n//k,'Global ownership budget failed')
                total_patterns+=1<<n;total_owners+=len(assignments)
                records.append({
                    'sites':n,'threshold':k,'kind':kind,
                    'coefficients':list(coefficients),
                    'budget_per_unit_weight':n//k,
                    'boolean_capture_patterns':1<<n,
                    'canonical_owner_patterns':len(assignments),
                    'absolute_expansion_sum':sum(comb(n,j)*abs(coefficients[j])
                                                 for j in range(n+1)),
                })
    return {'status':'PASS_EXHAUSTIVE_CHARGE_IDENTITIES_AND_BUDGETS',
            'supported_sizes':[1,2,3,4,5,6,7],
            'supported_kinds':['threshold','floor'],
            'models':len(records),'boolean_patterns_checked':total_patterns,
            'canonical_owner_patterns_checked':total_owners,
            'maximum_absolute_expansion_sum':max(r['absolute_expansion_sum'] for r in records),
            'records':records}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=verify()
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))


if __name__=='__main__':main()
