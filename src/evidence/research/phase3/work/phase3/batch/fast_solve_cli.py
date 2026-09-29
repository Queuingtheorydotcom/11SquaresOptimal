"""Compatibility CLI for the shared finite-only warm LP solver."""
from pathlib import Path
import sys,argparse,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shared'))
import fast_solver
p=argparse.ArgumentParser();p.add_argument('--mask',type=int,required=True);p.add_argument('--tag',required=True);p.add_argument('--seconds',type=float,default=60);p.add_argument('--extra',type=Path,action='append',default=[]);p.add_argument('--dataset');p.add_argument('--ownership');a=p.parse_args();d=fast_solver.solve(a.mask,a.tag,seconds=a.seconds,extra=a.extra);print(json.dumps({k:v for k,v in d.items()if k not in ['history','cell_lower_bounds','retained_poses_by_cell','additional_exact_capture_files']}))
