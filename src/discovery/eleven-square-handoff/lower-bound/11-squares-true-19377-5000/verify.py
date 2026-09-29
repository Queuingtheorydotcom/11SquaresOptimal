"""Verify package premises and freshly replay every exact geometry job by default."""
if not __debug__:raise SystemExit('Do not run with -O or -OO.')
import argparse,importlib.metadata,json,multiprocessing as mp,os,sys,time
from pathlib import Path
from premises import inspect_catalogue,validate_geometry_premises,need,filehash,read
ENV=None


def check_inventory(root):
 p=root/'PACKAGE.json'
 if not p.exists():return
 m=read(p);need(m['schema']=='portable-full-true-catalogue-v1','Unsupported package manifest')
 for name,h in m['files'].items():
  rel=Path(name);need(not rel.is_absolute() and '..' not in rel.parts,'Unsafe package path');need(filehash(root/rel)==h,'Package file changed: '+name)


def initialize(directory):
 global ENV
 info=inspect_catalogue(directory);staged,discrete,sweep,data,pdata,jobs=validate_geometry_premises(directory,info)
 # Replay direct source computations, never their saved PASS values. Exact
 # same-orientation core/domain inclusion then transfers these fresh bounds.
 if 'reuse' in info:jobs=info['reuse']['replay_jobs']
 ENV=(info,staged,discrete,sweep,data,pdata,jobs)


def job(index):
 info,staged,discrete,sweep,data,pdata,jobs=ENV;threshold=info['candidate']['minimum_units']
 # Positive ordinary-site weight guarantees a nonempty rectangle event list
 # for the frozen optional captured-proxy kernel. Otherwise use the TRUE
 # verifier directly, avoiding its old empty-proxy array-shape edge case.
 r=None
 if any(pdata[1]):
  minimum,cells,_=sweep.accumulate(*discrete.geometry(*pdata,*jobs[index]))
  if minimum>=threshold:r={'status':'PASS','minimum_units':int(minimum),'cells':int(cells),'stage':'fresh_captured_proxy'}
 if r is None:r=staged.verify_row(data,jobs[index],threshold)
 need(r['status']=='PASS' and type(r['minimum_units']) is int and r['minimum_units']>=threshold,'Exact geometry job failed/incomplete: '+str(index))
 return index,r['minimum_units'],r['stage']


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--catalogue',type=Path,default=Path(__file__).resolve().parent/'catalogue')
 p.add_argument('--workers',type=int,default=1);p.add_argument('--premises-only',action='store_true');p.add_argument('--output',type=Path)
 a=p.parse_args();need(a.workers>=1,'Positive worker count required');start=time.monotonic();directory=a.catalogue.resolve();check_inventory(Path(__file__).resolve().parent)
 initialize(directory);info=ENV[0]
 if a.premises_only:
  result={'status':'PASS_PREMISES_ONLY_GEOMETRY_NOT_REPLAYED','candidate_sha256':filehash(directory/'candidate.json'),'leaves':len(ENV[-1]),'source_intervals':info['source_intervals'],'global_bound_newly_verified':False}
 else:
  count=len(ENV[-1]);minimum=None;seen=set();stages={}
  if a.workers==1:iterator=map(job,range(count));pool=None
  else:
   pool=mp.get_context('spawn').Pool(a.workers,initialize,(str(directory),));iterator=pool.imap_unordered(job,range(count))
  try:
   for i,value,stage in iterator:
    need(i not in seen,'Duplicate replay job');seen.add(i);minimum=value if minimum is None else min(minimum,value);stages[stage]=stages.get(stage,0)+1
    if len(seen)%100==0 or len(seen)==count:print('FRESH_EXACT',len(seen),'/',count,flush=True)
  finally:
   if pool is not None:pool.terminate();pool.join()
  need(len(seen)==count and 11*minimum>info['candidate']['budget_units'],'Fresh replay/count gate incomplete')
  after=inspect_catalogue(directory);need(after['candidate']==info['candidate'] and after['run']==info['run'],'Inputs changed during replay');check_inventory(Path(__file__).resolve().parent)
  result={'status':'PASS_FRESH_FULL_EXACT_TRUE_REPLAY','candidate_sha256':filehash(directory/'candidate.json'),'context_sha256':info['run']['context_sha256'],
   'exact_target_side':info['candidate']['bound'],'source_intervals':info['source_intervals'],'leaf_jobs':count,'freshly_replayed_jobs':len(seen),
   'minimum_units':minimum,'budget_units':info['candidate']['budget_units'],'weight_denominator':info['candidate']['weight_denominator'],
   'counting_surplus_units':11*minimum-info['candidate']['budget_units'],'stages':stages,'receipt_cache_used':False,'global_bound_newly_verified':True}
  if 'reuse' in info:
   result.update(status='PASS_FRESH_FULL_EXACT_TRUE_PROOF_DAG',source_jobs_freshly_replayed=len(seen),
    target_jobs_monotonically_transferred=info['reuse']['monotone_jobs'],
    target_jobs_identical_to_fresh_source_jobs=count-info['reuse']['monotone_jobs'],
    origin_contexts=info['reuse']['origin_contexts'],
    target_geometry_all_freshly_swept=info['reuse']['monotone_jobs']==0)
 result['seconds']=time.monotonic()-start;result['python']=sys.version.split()[0];result['dependencies']={x:importlib.metadata.version(x) for x in ('numpy','numba','llvmlite')}
 if a.output:
  tmp=a.output.with_name(a.output.name+'.writing');tmp.write_text(json.dumps(result,indent=2)+'\n');os.replace(tmp,a.output)
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
