"""Exact propagation of one explicitly recorded closed angular branch."""
from pathlib import Path
import argparse
from run_capture import E

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--owner',type=int,required=True);p.add_argument('--bound',required=True);p.add_argument('--keep',choices=['le','ge'],required=True)
    p.add_argument('--seconds',type=float,default=180);p.add_argument('--passes',type=int,default=20);p.add_argument('--partners',type=int,default=0)
    a=p.parse_args();state,parent=E.load_state(a.source)
    state['constraints'].append(dict(kind='half_angle',owner=a.owner,bound_half_angle=E.F(a.bound),keep=a.keep))
    E.run_node(state,a.output,a.seconds,a.passes,[a.owner],True,a.output.stem,parent,a.partners)

if __name__=='__main__':main()
