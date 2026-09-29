"""Inventory explicit archived path references; never infer proof from receipts."""
from pathlib import Path,PurePosixPath
import json,hashlib,collections
base=Path(__file__).resolve().parent
root=base/'phase3'
manifest=json.loads((root/'SHA256SUMS.json').read_text())
missing=[];resolved=0
def resolve(s):
    p=PurePosixPath(s)
    if not p.is_absolute():
        q=root/str(p)
        if q.exists():return q
    for anchor in ('work','current'):
        if anchor in p.parts:
            q=root/Path(*p.parts[p.parts.index(anchor):])
            if q.exists():return q
    return None
def walk(x,key=()):
    if isinstance(x,dict):
        for k,v in x.items():yield from walk(v,key+(str(k),))
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from walk(v,key+(str(i),))
    elif isinstance(x,str):
        if (x.startswith(('work/','current/','/workspace/','/mnt/')) and x.endswith(('.json','.py','.so','.npz','.md','.txt'))):
            yield key,x
for name in manifest:
    if not name.endswith('.json') or name=='SHA256SUMS.json':continue
    try:d=json.loads((root/name).read_text())
    except (ValueError,UnicodeError):continue
    for key,s in walk(d):
        if resolve(s):resolved+=1
        else:missing.append(dict(source=name,key='.'.join(key),reference=s))
unique=collections.Counter(m['reference'] for m in missing)
accepted=json.loads((root/'PHASE3_REPLAY_MANIFEST.json').read_text())
critical=[]
for family in ['field_recipes','generic_recipes']:
    for i,e in enumerate(accepted[family]):
        for key,s in walk(e):
            if not resolve(s):critical.append(dict(family=family,index=i,key='.'.join(key),reference=s))
result=dict(scope='Syntactic file-reference inventory, including omitted failed/unaccepted research. Missing references alone do not invalidate a certificate outside their dependency chain.',
    archived_json_files=sum(n.endswith('.json') for n in manifest),resolved_reference_occurrences=resolved,
    missing_reference_occurrences=len(missing),missing_unique_references=len(unique),
    accepted_manifest_missing_references=critical,missing_references=missing,
    missing_reference_counts=dict(unique))
(base/'phase3-reference-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('missing_references','missing_reference_counts')},indent=2))
print('TARGETED MISSING')
for s,n in unique.items():
    if any(t in s for t in ['1383','1839','438']):print(n,s)
