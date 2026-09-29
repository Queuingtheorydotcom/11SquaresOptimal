"""Multiple exact single-parent deficits at selected angles; discovery only."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,time,argparse,hashlib,contextlib
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'current/research/optimality/deficit_geometry/physical_features';sys.path.insert(0,str(ROOT/'work/geometry'));from verify_wall_aware_mask import av
sys.path.insert(0,str(BASE));import add_exact_refuter as capture
HERE=Path(__file__).parent

def harvest(packet,report=None,seconds=25,limit=12):
 p=json.loads(packet.read_text());av.U=F(p['parent_Uplus']);av.PARENT=av.L/av.U;cover=json.loads(av.typed.COVER.read_text());base=av.expand(p['certificate']);owned=av.validate_owned_sites(cover,p['ownership_points_field']);mask=p['mask'];gamma=p['threshold_units'];support=p.get('conditional_owner_support',mask);eps=F(1,2**32);angles=[F(0),F(1,2048),F(1,64),F(1,8),F(1,4),F(1,3),F(2,5),F(3,7),F(1,2),F(3,4),F(15,16),F(1)]
 if report:
  d=json.loads(report.read_text());last=d['records'][-1]
  if last['status']=='REFUTED_BY_LEGAL_PARENT':
   t=F(last['parent_witness']['half_angle']);angles=[t,max(0,t-F(1,128)),min(1,t+F(1,128))]+angles
 angles=list(dict.fromkeys(angles));rows=[];paths=[];seen=set();start=time.monotonic();stem=packet.name.removesuffix('-packet.json')+'-p3priced'
 for cell in sorted((j for j in mask if gamma[j]),key=lambda j:-gamma[j]):
  data=av.conditioned_data(base,owned,support,cell,gamma[cell]);prepared=av.prepare_majority(data);world=av.field_polygon(cover,cell);found=0
  for t in angles:
   if time.monotonic()-start>seconds or len(paths)>=limit:break
   lo=max(F(0),t-eps);hi=min(F(1),t+eps);r=dict(cell=cell,depth=0,**av.verify_interval(data,prepared,world,lo,hi,gamma[cell],1000));rows.append(r)
   if r['status']!='REFUTED_BY_LEGAL_PARENT':continue
   witness=r['parent_witness'];key=str((witness['half_angle'],witness['center']))
   if key in seen:continue
   seen.add(key);path=BASE/f'{stem}-cell{cell}-w{found}-source.json';z=dict(status='EXACT_SINGLE_PARENT_DEFICIT_SELECTED_ANGLE',parent_Uplus=str(av.U),parent_side=str(av.PARENT),packet_sha256=hashlib.sha256(packet.read_bytes()).hexdigest(),mask_index=p['mask_index'],mask=mask,records=[r],geometry_coverage=False,global_optimality_proved=False);path.write_text(json.dumps(z,indent=2,default=str)+'\n');out=path.with_name(path.name.replace('-source.json','-exact.npz'));oldargv=sys.argv
   try:
    sys.argv=['add_exact_refuter.py',str(path),'--output',str(out)]
    with (HERE/(out.stem+'.log')).open('w') as log,contextlib.redirect_stdout(log):capture.main()
   finally:sys.argv=oldargv
   paths.append(str(out));found+=1;print(json.dumps(dict(mask=p['mask_index'],cell=cell,angle=str(witness['half_angle']),deficit=gamma[cell]-witness['charge_units'],new_exact_rows=8,seconds=time.monotonic()-start)),flush=True)
   if found>=3:break
  if time.monotonic()-start>seconds or len(paths)>=limit:break
 result=dict(status='FINITE_DISCOVERY_EXACT_REFUTER_BATCH',packet_sha256=hashlib.sha256(packet.read_bytes()).hexdigest(),source_packet=str(packet),seconds=time.monotonic()-start,exact_archives=paths,checked_rows=len(rows),geometry_coverage=False,global_optimality_proved=False)
 (HERE/(stem+'-result.json')).write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('packets',nargs='+',type=Path);ap.add_argument('--seconds',type=float,default=25);a=ap.parse_args()
 for packet in a.packets:harvest(packet,seconds=a.seconds)
