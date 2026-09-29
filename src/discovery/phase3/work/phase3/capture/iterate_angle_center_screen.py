"""Heuristic iteration of exact-model LP bounds; NO proof until dual replay."""
from pathlib import Path
import angle_center_screen as S
import argparse,json,math,time

def main():
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--rounds',type=int,default=20);a=ap.parse_args();state,parent=S.E.load_state(a.source);override=None;rounds=[];start=time.monotonic()
 for k in range(a.rounds):
  model=S.build(state,override);answer=S.solve(model,state);rounds.append(dict(index=k,model=model,discovery=answer))
  S.E.save(a.output,dict(source=parent,rounds=rounds,certified=False,mask_capture_proved=False,global_optimality_proved=False,seconds=time.monotonic()-start))
  print(json.dumps(dict(round=k,status=answer['status'],maxwidth=answer.get('max_center_width_unit'),seconds=time.monotonic()-start)),flush=True)
  if answer['status']!=0:break
  old=override;override=[]
  for (lo,hi),m,r in zip(answer['field_center_halfangle_bounds'],model['midpoints'],model['radii']):
   # This padding is discovery-only and is not promoted as an exact premise.
   x=max(m-r,S.F(math.floor((lo-1e-7)*10**9),10**9));y=min(m+r,S.F(math.ceil((hi+1e-7)*10**9),10**9));override.append([x,y])
  if override==old:break
if __name__=='__main__':main()
