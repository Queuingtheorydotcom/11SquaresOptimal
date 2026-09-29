#!/usr/bin/env python3
"""Audit useful completed generic contradictions; refresh the combined union."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,hashlib,subprocess,sys,os,time,traceback
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];PHASE=ROOT/'work/phase3'
ENTRIES=HERE/'generic_audit_entries.json';RESERVATIONS=HERE/'generic_audit_reservations.json'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def store(p,x):
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)
def refresh():
 with (HERE/'overall-union-independent-audit.log').open('w') as f:
  subprocess.run([sys.executable,str(HERE/'audit_overall_union.py')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
 d=read(HERE/'overall-union-independent-audit.json');print(json.dumps(dict(overall_excluded=d['excluded_canonical_cases'],remaining=d['remaining_canonical_cases'],generic_beyond_fields=d['generic_cases_beyond_fields'])),flush=True)
def audit(item):
 p,h,mask,idx,nrows,ncollisions=item
 stem=p.stem+'-'+h[:12];out=PHASE/'hull'/('audit-'+stem+'.json');log=out.with_suffix('.log')
 if out.exists():
  try:
   r=read(out)
   if r.get('status')=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT' and r.get('mask_exclusion_proved') and r.get('source_sha256')==h:return dict(source=str(p.relative_to(ROOT)),audit=str(out.relative_to(ROOT)))
  except json.JSONDecodeError:pass
 checker=PHASE/'hull/audit_capture_v6.py';cmd=[sys.executable,str(checker),str(p),'--output',str(out)]
 d=read(p)
 if d['source'].get('independent_audit_path'):cmd+=['--root-audit',d['source']['independent_audit_path']]
 env=dict(os.environ,ELEVEN_RATIONAL_BACKEND='gmp',PYTHONPATH=str(PHASE/'deps')+':'+str(ROOT/'work/audit/deps'))
 with log.open('w') as f:subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 r=read(out);assert r['mask_exclusion_proved'] and r['source_sha256']==h
 return dict(source=str(p.relative_to(ROOT)),audit=str(out.relative_to(ROOT)))
def main():
 (HERE/'generic-monitor.pid').write_text(str(os.getpid())+'\n');cache={};failed=set(read(HERE/'generic-monitor-status.json').get('failed_packet_sha256',[])) if (HERE/'generic-monitor-status.json').exists() else set();futures={};last_binding=None;start=time.monotonic()
 cover=read(ROOT/'current/research/optimality/global_capture/center-cover-symmetric-exact.json')['canonical_eleven_cell_subsets']
 with ThreadPoolExecutor(max_workers=2) as pool:
  while time.monotonic()-start<14400:
   stop=HERE/'STOP_GENERIC_MONITOR'
   stopping=stop.exists() and stop.read_text().strip()!='RESUME'
   entries=read(ENTRIES);known={sha(ROOT/e['source']) for e in entries};changed=False
   for f,item in list(futures.items()):
    if not f.done():continue
    del futures[f]
    try:e=f.result();entries.append(e);known.add(item[1]);changed=True;print(json.dumps(dict(passed=e)),flush=True)
    except Exception as error:failed.add(item[1]);print(json.dumps(dict(audit_failure=str(item[0]),error=str(error))),flush=True)
   reservations=read(RESERVATIONS) if RESERVATIONS.exists() else [];active_external=[]
   for e in reservations:
    ph=sha(ROOT/e['source'])
    if ph in known:continue
    p=ROOT/e['audit']
    try:r=read(p)
    except (FileNotFoundError,json.JSONDecodeError):active_external.append(e);continue
    if r.get('status')=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT' and r.get('mask_exclusion_proved') and r.get('source_sha256')==ph:
     entries.append(e);known.add(ph);changed=True;print(json.dumps(dict(adopted_external=e)),flush=True)
    else:active_external.append(e)
   if changed:store(ENTRIES,entries)
   binding=(sha(HERE/'current-union-independent-audit.json'),sha(ENTRIES),sha(HERE/'audit_overall_union.py'))
   if binding!=last_binding:refresh();last_binding=binding
   overall=read(HERE/'overall-union-independent-audit.json');covered=set(overall['excluded_canonical_mask_indices']);running={item[1] for item in futures.values()};reserved={sha(ROOT/e['source']) for e in active_external}
   candidates=[]
   folders=[p for p in PHASE.rglob('generic') if p.is_dir()]
   for folder in folders:
    for p in folder.glob('mask*.json'):
     stat=p.stat();key=(stat.st_size,stat.st_mtime_ns)
     if p not in cache or cache[p][0]!=key:
      try:
       content=p.read_bytes();d=json.loads(content)
       good=d.get('schema')=='exact_generic_owned_hull_v1' and d.get('terminal') and d.get('contradiction') and d.get('constraints')==[]
       nrows=sum(len(step.get('rows',[])) for step in d.get('steps',[]))
       ncollisions=sum(len(row.get('collision_regions',[])) for step in d.get('steps',[]) for row in step.get('rows',[]))
       cache[p]=(key,(p,hashlib.sha256(content).hexdigest(),d['mask'],d['mask_index'],nrows,ncollisions) if good else None)
      except (json.JSONDecodeError,KeyError):continue
     item=cache[p][1]
     if item is None or item[1] in known|running|reserved|failed:continue
     mask=set(item[2]);cases={i for i,J in enumerate(cover) if mask<=set(J) or mask<={15-j for j in J}};gain=len(cases-covered)
     if gain:candidates.append((gain,item,cases))
   candidates.sort(key=lambda x:(x[0],x[1][5]==0,-x[1][4],len(x[2]),-len(x[1][2])),reverse=True)
   if stopping and not futures:break
   slots=0 if stopping else max(0,2-len(futures)-len(active_external))
   for gain,item,cases in candidates:
    if not slots:break
    if not(cases-covered):continue
    print(json.dumps(dict(starting=str(item[0]),prospective_new=len(cases-covered),rows=item[4],collision_regions=item[5])),flush=True)
    futures[pool.submit(audit,item)]=item;covered|=cases;slots-=1
   store(HERE/'generic-monitor-status.json',dict(overall_excluded=overall['excluded_canonical_cases'],remaining=overall['remaining_canonical_cases'],running=[str(x[0]) for x in futures.values()],external=active_external,failed_packet_sha256=sorted(failed)))
   time.sleep(10)
if __name__=='__main__':main()
