"""Exact capture propagation retaining residual-hull facet directions.

The archive rounded every center cover to eight fixed directions. Here each
residual convex-hull facet proposes another rational normal. Its exact support
over every residual vertex, rounded outward, is independently checkable by the
unchanged capture checker. This changes strength, not the proof rule.
"""
from pathlib import Path
import argparse
from run_capture import E
F=E.F

def outer(vertices,world,grid=10**12):
    if not vertices:return [],[]
    normals=set(tuple(map(F,n)) for n in E.DIRECTIONS)
    for n,_ in E.geo.rows(E.geo.hull(vertices)):
        scale=max(map(abs,n))
        if not scale:continue
        n=tuple(F(round(v/scale*10**6),10**6) for v in n)
        if any(n):normals.add(n)
    result=world;bounds=[]
    for n in sorted(normals):
        m=max(n[0]*x+n[1]*y for x,y in vertices)
        b=F(-((-m.numerator*grid)//m.denominator),grid)
        assert all(n[0]*x+n[1]*y<=b for x,y in vertices)
        bounds.append(dict(normal=n,upper=b));result=E.geo.clip_linear(result,n,b)
    return result,bounds

E.outer=outer
old_inner=E.inner_grid.inner_grid
def inner_grid(points,denominator=10**8,directions=16):
    return old_inner(points,denominator=denominator,directions=32)
E.inner_grid.inner_grid=inner_grid
old_save=E.save
def save(p,d):
    if 'dependencies' in d:d['dependencies'][str(Path(__file__).resolve())]=E.sha(__file__)
    return old_save(p,d)
E.save=save

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--seconds',type=float,default=180);ap.add_argument('--passes',type=int,default=10)
    ap.add_argument('--owner',type=int,default=15);ap.add_argument('--partners',type=int,default=0)
    a=ap.parse_args();state,parent=E.load_state(a.source)
    E.run_node(state,a.output,a.seconds,a.passes,[a.owner],True,a.output.stem,parent,a.partners)

if __name__=='__main__':main()
