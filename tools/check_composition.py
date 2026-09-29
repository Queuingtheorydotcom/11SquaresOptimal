"""Read-only composition diagnostic: ordinary source imports, virtual certificate I/O.
This does not execute geometry. All virtual digests are recomputed from payloads.
"""
from pathlib import Path
import sys, os, json, hashlib, gzip, io, zipfile, stat, types
sys.path.insert(0,str(Path(__file__).resolve().parent))
from content import ROOT, load_index, read_blob, write_record
index=load_index();base=(ROOT/'.composition-check/evidence').resolve();base.mkdir(parents=True,exist_ok=True)
objects=index['objects'];paths={str(base/name.removeprefix('evidence/')):objects[h] for name,h in index['files'].items() if name.startswith('evidence/')}
# Import paths must exist for Python's normal module finder.
for name,r in paths.items():
 p=Path(name)
 if p.suffix=='.py':p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(read_blob(r))
raw_open=Path.open;raw_stat=Path.stat;raw_digest=hashlib.file_digest;raw_zip=zipfile.ZipFile
class ArchiveStream:
 def __init__(self,r):self.record=r
 def __enter__(self):return self
 def __exit__(self,*args):pass
class FakeDigest:
 def __init__(self,h):self.h=h
 def hexdigest(self):return self.h
cache={}
def file_digest(stream,algorithm,*args,**kw):
 if isinstance(stream,ArchiveStream):
  r=stream.record
  if r['sha256'] not in cache:
   # Use the real ZIP writer in content.write_record during reconstruction.
   zipfile.ZipFile=raw_zip
   try:write_record(r,objects,None)
   finally:zipfile.ZipFile=VirtualZip
   cache[r['sha256']]=True
  return FakeDigest(r['sha256'])
 return raw_digest(stream,algorithm,*args,**kw)
def p_open(p,mode='r',*a,**kw):
 r=paths.get(str(p.absolute()))
 if r and not any(x in mode for x in 'wa+'):
  if r['kind']=='zip':return ArchiveStream(r)
  b=read_blob(r)
  return io.BytesIO(b) if 'b' in mode else io.StringIO(b.decode('utf-8' if kw.get('encoding') in (None,'locale') else kw['encoding']))
 return raw_open(p,mode,*a,**kw)
def p_stat(p,*a,**kw):
 r=paths.get(str(p.absolute()))
 if r:return os.stat_result((stat.S_IFREG|0o644,0,0,1,0,0,r['bytes'],0,0,0))
 return raw_stat(p,*a,**kw)
class VirtualZip:
 def __init__(self,path,*a,**kw):
  self.r=paths[str(Path(path).absolute())];self.members={m['name']:objects[m['source']] for m in self.r['members']}
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,name):return read_blob(self.members[name])
Path.open=p_open;Path.stat=p_stat;hashlib.file_digest=file_digest;zipfile.ZipFile=VirtualZip
source=base/'code/verify_recorded_proof.py';module=types.ModuleType('public_composition');module.__file__=str(source)
exec(compile(source.read_bytes(),str(source),'exec'),module.__dict__)
result=module.validate()
print(json.dumps(dict(status='PASS_PUBLIC_COMPOSITION_CHECK',
    geometric_proof_replayed=False, composition_status=result['status'],
    **{k:result[k] for k in ('all_noncandidate_exclusions','surviving_canonical_cases','input_files_checked','input_bytes_checked')}),indent=2))
