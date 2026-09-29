"""Refine angular rows to width<=1/1024, retaining exact facet supports."""
from pathlib import Path
import argparse
import run_capture as R
import run_facet_capture as P
import capture_engine_refined as E

E.sha=R.mapped_sha
E.outer=P.outer
old_inner=E.inner_grid.inner_grid
# run_facet_capture already installed the certified32-direction compression.
old_save=E.save
def save(p,d):
    if 'dependencies' in d:
        for f in (Path(__file__),Path(P.__file__),Path(R.__file__)):
            d['dependencies'][str(f.resolve())]=E.sha(f)
    return old_save(p,d)
E.save=save

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--seconds',type=float,default=180);ap.add_argument('--passes',type=int,default=10);ap.add_argument('--partners',type=int,default=3)
    a=ap.parse_args();state,parent=E.load_state(a.source)
    E.run_node(state,a.output,a.seconds,a.passes,[13],True,a.output.stem,parent,a.partners)

if __name__=='__main__':main()
