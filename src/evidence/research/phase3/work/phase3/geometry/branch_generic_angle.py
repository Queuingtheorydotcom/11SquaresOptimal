"""One closed angle half-branch of a generic independently auditable pose tree."""
from pathlib import Path
import sys,argparse
if not __debug__:raise RuntimeError('Assertions must remain enabled')
WORK=Path(__file__).resolve().parents[2];sys.path.insert(0,str(WORK/'phase3/deps'));sys.path.insert(0,str(WORK/'phase3/capture'))
import capture_engine_self_v1 as E

def main():
 p=argparse.ArgumentParser();p.add_argument('parent',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--owner',type=int,required=True);p.add_argument('--bound',required=True);p.add_argument('--keep',choices=['le','ge'],required=True);p.add_argument('--seconds',type=float,default=120);p.add_argument('--passes',type=int,default=8);p.add_argument('--partners',type=int,default=10);p.add_argument('--node',required=True);a=p.parse_args();state,parent=E.load_state(a.parent);lo,hi=E.angular_range(a.owner,state['constraints']);bound=E.F(a.bound);assert a.owner in state['mask'] and lo<bound<hi;state['constraints'].append(dict(kind='half_angle',owner=a.owner,bound_half_angle=bound,keep=a.keep));E.run_node(state,a.output,a.seconds,a.passes,[a.owner],True,a.node,parent,a.partners)
if __name__=='__main__':main()
