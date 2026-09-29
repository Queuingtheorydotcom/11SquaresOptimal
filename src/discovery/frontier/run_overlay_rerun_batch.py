"""Bounded two-worker D4 reruns of fully completed unresolved plain cases."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
import argparse,subprocess,sys,json,time,threading,hashlib
HERE=Path(__file__).resolve().parent
STATUS=HERE/'overlay-rerun-status.json'
LOCK=threading.Lock()
EXCLUDED={2175,2176,438,999,1462,1659,1383,1839}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(path):
 try:return json.loads(path.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return []

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--max-cases',type=int,default=8);ap.add_argument('--seconds',type=int,default=120);ap.add_argument('--workers',type=int,default=2);a=ap.parse_args()
 assert 1<=a.workers<=2
 records=read(STATUS);assert isinstance(records,list)
 done={r['mask_index'] for r in records};reserved=set(done)
 def publish(row):
  with LOCK:
   for i,old in enumerate(records):
    if old['mask_index']==row['mask_index']:records[i]=dict(row);break
   else:records.append(dict(row))
   temp=STATUS.with_suffix('.writing');temp.write_text(json.dumps(records,indent=2)+'\n');temp.replace(STATUS)
 def eligible():
  candidates={}
  for status in ['batch-status.json','all-batch-status.json']:
   for r in read(HERE/status):
    m=r['mask_index']
    if m in EXCLUDED or m in reserved:continue
    if r.get('independent_audit_passed') is not False or r.get('contradiction') is not None or r.get('producer_returncode')!=0 or r.get('terminal') is not True:continue
    source=Path(r['producer'])
    if not source.is_file():continue
    d=read(source)
    if not isinstance(d,dict) or d.get('terminal') is not True or d.get('contradiction') is not None:continue
    if (HERE/f'mask{m}-overlay-v1.json').exists() or (HERE/f'mask{m}-overlay-exclusion.json').exists():continue
    candidates[m]=(source,status)
  return sorted(candidates.items())
 def job(m,plain):
  source,status=plain;producer=HERE/f'mask{m}-overlay-v1.json';audit=HERE/f'mask{m}-overlay-independent.json';exclusion=HERE/f'mask{m}-overlay-exclusion.json'
  row={'mask_index':m,'phase':'producer_running','plain_source':str(source),'plain_source_sha256':sha(source),'eligibility_status_file':status,'producer':str(producer),'independent_audit_passed':False,'exclusion_transfer_passed':False,'started_at':time.time()};publish(row)
  with (HERE/f'mask{m}-overlay-producer.log').open('w') as log:
   result=subprocess.run([sys.executable,str(HERE/'run_overlay_case.py'),str(m),'--seconds',str(a.seconds)],stdout=log,stderr=subprocess.STDOUT)
  row['producer_returncode']=result.returncode
  if result.returncode:row['phase']='producer_failed';publish(row);return row
  d=read(producer);row['terminal']=d['terminal'];row['contradiction']=d['contradiction'];row['producer_sha256']=sha(producer)
  if not d['terminal'] or not d['contradiction']:
   row['phase']='unresolved_after_overlay';row['finished_at']=time.time();publish(row);return row
  row['phase']='independent_audit_running';publish(row)
  with (HERE/f'mask{m}-overlay-independent.log').open('w') as log:
   result=subprocess.run([sys.executable,str(HERE/'audit_case.py'),str(producer),'--output',str(audit)],stdout=log,stderr=subprocess.STDOUT)
  row['audit_returncode']=result.returncode
  if result.returncode:row['phase']='independent_audit_failed';publish(row);return row
  r=read(audit)
  row['independent_audit_passed']=r.get('status')=='PASS_INDEPENDENT_GENERIC_HULL_AUDIT' and r.get('branch_exclusion_proved') is True
  row['audit']=str(audit);row['audit_sha256']=sha(audit)
  if not row['independent_audit_passed']:row['phase']='independent_audit_not_excluded';publish(row);return row
  row['phase']='necessity_transfer_running';publish(row)
  with (HERE/f'mask{m}-overlay-transfer.log').open('w') as log:
   result=subprocess.run([sys.executable,str(HERE/'audit_overlay_exclusion.py'),str(producer),str(audit),'--output',str(exclusion)],stdout=log,stderr=subprocess.STDOUT)
  row['transfer_returncode']=result.returncode
  if result.returncode:row['phase']='necessity_transfer_failed';publish(row);return row
  r=read(exclusion);row['exclusion_transfer_passed']=r.get('status')=='PASS_D4_ANTECEDENTS_DISCHARGED_EXACT_MASK_EXCLUSION' and r.get('mask_exclusion_proved') is True
  row['exclusion']=str(exclusion);row['exclusion_sha256']=sha(exclusion);row['phase']='fully_audited_exclusion' if row['exclusion_transfer_passed'] else 'transfer_not_excluded';row['finished_at']=time.time();publish(row);return row
 launched=0;futures={}
 with ThreadPoolExecutor(max_workers=a.workers) as pool:
  while True:
   for m,plain in eligible():
    if len(futures)>=a.workers or launched>=a.max_cases:break
    reserved.add(m);launched+=1;futures[pool.submit(job,m,plain)]=m;print(json.dumps({'started_mask':m,'launched_in_batch':launched}),flush=True)
   if not futures:break
   finished,_=wait(futures,timeout=30,return_when=FIRST_COMPLETED)
   for f in finished:
    m=futures.pop(f)
    try:r=f.result();print(json.dumps({k:r.get(k) for k in ['mask_index','phase','contradiction','independent_audit_passed','exclusion_transfer_passed']}),flush=True)
    except Exception as e:
     publish({'mask_index':m,'phase':'orchestration_failed','error':repr(e),'independent_audit_passed':False,'exclusion_transfer_passed':False});print(json.dumps({'mask_index':m,'error':repr(e)}),flush=True)
 print(json.dumps({'batch_complete':True,'launched':launched,'total_owned_cases':len(records),'fully_audited_exclusions':sum(r.get('exclusion_transfer_passed') is True for r in records)}),flush=True)

if __name__=='__main__':main()
