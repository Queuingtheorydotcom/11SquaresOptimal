from pathlib import Path
import json,subprocess,concurrent.futures,time
D=Path(__file__).resolve().parent
R=D.parent/'phase3'
o=json.load(open(R/'work/phase2/geometry/cover_overlay_exact.json'))
c=json.load(open(R/'current/research/optimality/global_capture/center-cover-symmetric-exact.json'))
out=D/'candidate-overlay-support-253';out.mkdir(exist_ok=True)
queries=[(idx,r) for idx in [438,999,1462,1659] for r,reg in enumerate(o['regions']) if reg['labels'][0] in c['canonical_eleven_cell_subsets'][idx]]
def check(q):
 idx,r=q;path=out/f'mask{idx}-region{r}.txt'
 subprocess.run([str(D/'overlay_forced_csp'),str(D/'overlay-253-input.txt'),str(path),'2000000',str(idx),str(idx+1),str(r)],check=True,capture_output=True,text=True)
 line=path.read_text().splitlines()[0];parts=line.split()
 return {'mask':idx,'region':r,'cell':o['regions'][r]['labels'][0],'status':parts[0],'nodes':int(parts[2]),'witness':[int(v) for v in parts[3:]]}
start=time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 rows=list(ex.map(check,queries))
result={'status':'CONDITIONAL_DISCOVERY_REQUIRES_REPLAY','rows':rows,'seconds':time.time()-start}
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
for idx in [438,999,1462,1659]:
 rr=[r for r in rows if r['mask']==idx]
 print(idx,{s:sum(r['status']==s for r in rr) for s in ['SURVIVES','EXCLUDED','UNKNOWN']},flush=True)
 for cell in c['canonical_eleven_cell_subsets'][idx]:
  base=sum(r['cell']==cell for r in rr); live=[r['region'] for r in rr if r['cell']==cell and r['status']!='EXCLUDED']
  print(' ',cell,base,'->',len(live),live,flush=True)
print('seconds',time.time()-start)
