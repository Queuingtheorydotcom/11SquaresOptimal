#!/usr/bin/env python3
"""Append twelve exact actual-side parents, deduplicating only identical rows."""
from pathlib import Path
from hashlib import sha256
import json,time
import numpy as np
from exception_charge_lp import budgets,filehash,need,dump
ROOT=Path('research/classical');prior=ROOT/'cutround8-four-exception-pair-primitive.json'
out=ROOT/'cutround8-r4-repair1-pool.rows.npy';meta=ROOT/'cutround8-r4-repair1-pool.json'
need(not out.exists() and not meta.exists(),'Use fresh immutable outputs');started=time.monotonic()
p=json.loads(prior.read_bytes());basepath=Path(p['finite_check']['rows']);basehash=p['finite_check']['rows_sha256']
need(filehash(basepath)==basehash,'Base rows changed');base=np.load(basepath,mmap_mode='r')
firstpath=Path('research/reweight/joint-known-obstruction-captures.json');first=json.loads(firstpath.read_bytes())
lastpath=Path('research/reweight/joint-known-206-exact-parent-captures.json');last=json.loads(lastpath.read_bytes())
for d in [first,last]:
    need(d['source_sha256']==p['source_sha256'],'Different geometry source')
    need(d['actual_parent_side']=='19100/19377','Wrong appended parent side')
paths=[Path(first['capture_file']),Path(last['cut9_capture_file'])]
hashes=[first['capture_sha256'],last['cut9_capture_sha256']]
blocks=[]
for path,h in zip(paths,hashes):
    need(filehash(path)==h,'Exact captures changed')
    blocks.append(np.load(path)['rows'])
need(blocks[0].shape==(5,4716) and blocks[1].shape==(7,4716),'Expected exactly five plus seven captures')
new=np.concatenate(blocks)
need(np.all((new>=0)&(new<256)) and np.all(new==new.astype(np.uint8)),'Bad capture integers');new=new.astype(np.uint8)
a=json.load(open(p['fixed_A']['certificate']));cap=budgets(a)
need(np.all(new<=cap),'New capture exceeds feature budget')
# Digests select possible equality only; actual byte equality determines deduplication.
wanted={}
for i,row in enumerate(new):wanted.setdefault(sha256(row.tobytes()).digest(),[]).append(i)
retained=[None]*len(new)
for oldidx,row in enumerate(base):
    raw=row.tobytes();key=sha256(raw).digest()
    if key in wanted:
        for i in wanted[key]:
            if retained[i] is None and raw==new[i].tobytes():retained[i]=oldidx
added=[];new_exact={}
for i,row in enumerate(new):
    if retained[i] is None:
        raw=row.tobytes()
        if raw not in new_exact:
            new_exact[raw]=len(base)+len(added);added.append(row.copy())
        retained[i]=new_exact[raw]
merged=np.lib.format.open_memmap(out,mode='w+',dtype=np.uint8,shape=(len(base)+len(added),base.shape[1]))
for start in range(0,len(base),8192):merged[start:min(start+8192,len(base))]=base[start:start+8192]
if added:merged[len(base):]=np.array(added,np.uint8)
merged.flush();del merged
records=[]
for i,index in enumerate(retained):
    original=first['records'][i] if i<5 else last['records'][199+i-5]
    records.append(dict(input_index=i,source_capture=str(paths[0 if i<5 else 1]),source_capture_index=i if i<5 else i-5,
                        retained_row_index=index,appended_distinct_row=index>=len(base),exact_parent=original))
need(filehash(basepath)==basehash,'Base changed during append')
for path,h in zip(paths,hashes):need(filehash(path)==h,'Captures changed during append')
result=dict(status='IMMUTABLE_FINITE_POOL_WITH_EXACT_PARENT_APPEND',source_certificate=p['source_certificate'],source_sha256=p['source_sha256'],
    base_rows=str(basepath),base_sha256=basehash,base_row_count=len(base),capture_inputs={str(path):h for path,h in zip(paths,hashes)},
    parent_provenance={str(firstpath):filehash(firstpath),str(lastpath):filehash(lastpath)},
    appended_input_count=12,added_distinct_rows=len(added),output_rows=str(out),output_rows_sha256=filehash(out),
    rows=len(base)+len(added),columns=4716,records=records,generator_sha256=filehash(Path(__file__)),seconds=time.monotonic()-started,
    scope='Finite heterogeneous-side coefficient pool only. The original discovery rows are unchanged; each appended exact parent is explicitly at A=19100/19377. No uniform geometric side label or continuum inference is assigned to the combined matrix.')
dump(meta,result)
print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
