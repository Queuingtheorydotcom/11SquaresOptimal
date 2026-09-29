#!/usr/bin/env python3
"""Complete parallel replay for discrete plus majority-hull charges."""
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
import argparse,hashlib,json,multiprocessing as mp,time
import numpy as np
from majority_mixed import validate,geometry
from integer_sweep import accumulate,need

DATA=None;REQUIRED=None;SUBDIVISIONS=None;DOMAIN_CONDITIONAL=True


def initialize(c,subdivisions,domain_conditional):
    global DATA,REQUIRED,SUBDIVISIONS,DOMAIN_CONDITIONAL
    DATA,jobs,margin=validate(c);REQUIRED=c['minimum_units'];SUBDIVISIONS=subdivisions
    DOMAIN_CONDITIONAL=domain_conditional


def replay(task):
    index,job=task
    arrays=geometry(*DATA,*job,subdivisions=SUBDIVISIONS,domain_conditional=DOMAIN_CONDITIONAL)
    value,cells,winner=accumulate(*arrays)
    need(value>=REQUIRED,'Coverage fails at row '+str(index))
    return {'row':index,'minimum_units':int(value),'cells':int(cells),
            'slabs':int(np.count_nonzero(arrays[-2]>=0))}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certificate',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--jobs',type=int,default=3)
    parser.add_argument('--subdivisions',type=int)
    parser.add_argument('--unconditional',action='store_true')
    args=parser.parse_args();raw=args.certificate.read_bytes();c=json.loads(raw)
    subdivisions=args.subdivisions if args.subdivisions is not None else c.get('majority_subdivisions',4)
    need(type(subdivisions) is int and subdivisions>=1,'Invalid subdivision count')
    data,jobs,margin=validate(c)
    need(1<=args.jobs<=len(jobs),'Invalid worker count')
    rows=[];start=time.monotonic()
    with mp.get_context('spawn').Pool(args.jobs,initialize,(c,subdivisions,not args.unconditional)) as pool:
        for row in pool.imap_unordered(replay,enumerate(jobs)):
            rows.append(row)
            if len(rows)%100==0:
                print('MAJORITY_REPLAY',len(rows),'of',len(jobs),'seconds',time.monotonic()-start,flush=True)
    rows.sort(key=lambda row:row['row'])
    need([row['row'] for row in rows]==list(range(len(jobs))),'Incomplete row coverage')
    minimum=min(row['minimum_units'] for row in rows)
    result={'status':'PASS_FULL_EXACT_MAJORITY_HULL_REPLAY',
            'certificate_sha256':hashlib.sha256(raw).hexdigest(),
            'full_catalogue_scanned':True,'parent_side':c['A'],'bound':str(F(c['L'])/F(c['A'])),
            'intervals':len(rows),'minimum_units':minimum,'budget_units':c['budget_units'],
            'counting_surplus_units':11*minimum-c['budget_units'],
            'strict_core_margin':str(margin),'majority_subdivisions':subdivisions,
            'domain_conditional_rectangles':not args.unconditional,
            'histogram':dict(Counter(str(row['minimum_units']) for row in rows)),
            'slabs':sum(row['slabs'] for row in rows),'cells':sum(row['cells'] for row in rows),
            'rows':rows,'seconds':time.monotonic()-start}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','histogram')},indent=2))


if __name__=='__main__':main()
