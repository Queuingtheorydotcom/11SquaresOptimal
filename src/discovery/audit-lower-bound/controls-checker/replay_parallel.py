"""Full exact all-centre replay at the certificate's final parent side."""

if not __debug__:
    raise SystemExit("Verification requires Python assertions; remove -O/-OO and unset PYTHONOPTIMIZE.")
from exact_mixed import *
import multiprocessing as mp,argparse
DATA=None;REQUIRED=None

def initialise(c):
 global DATA,REQUIRED
 DATA,jobs,margin=validate(c);REQUIRED=c['minimum_units']

def replay(task):
 index,job=task;ar=geometry(*DATA,*job);z,cells,win=accumulate(*ar);need(z>=REQUIRED,'coverage fails at '+str(index));return {'row':index,'minimum_units':int(z),'cells':int(cells),'slabs':int(np.count_nonzero(ar[-2]>=0))}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('certificate');ap.add_argument('--output',required=True);ap.add_argument('--jobs',type=int,default=4);a=ap.parse_args();raw=Path(a.certificate).read_bytes();c=json.loads(raw);data,jobs,margin=validate(c);start=time.monotonic();rows=[]
 with mp.get_context('spawn').Pool(a.jobs,initialise,(c,)) as pool:
  for row in pool.imap_unordered(replay,enumerate(jobs)):
   rows.append(row)
   if len(rows)%500==0:print('REPLAY',len(rows),'of',len(jobs),'seconds',time.monotonic()-start,flush=True)
 rows.sort(key=lambda r:r['row']);assert [r['row'] for r in rows]==list(range(len(jobs)));hist={}
 for row in rows:hist[str(row['minimum_units'])]=hist.get(str(row['minimum_units']),0)+1
 result={'status':'PASS_FULL_EXACT_PYTHON_REPLAY','certificate_sha256':hashlib.sha256(raw).hexdigest(),'parent_side':c['A'],'bound':str(F(c['L'])/F(c['A'])),'intervals':len(rows),'budget_units':c['budget_units'],'minimum_units':min(r['minimum_units'] for r in rows),'strict_core_margin':str(margin),'counting_surplus_units':11*min(r['minimum_units'] for r in rows)-c['budget_units'],'slabs':sum(r['slabs'] for r in rows),'cells':sum(r['cells'] for r in rows),'histogram':hist,'rows':rows,'seconds':time.monotonic()-start};Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['histogram','rows']},indent=2),flush=True)
if __name__=='__main__':main()
