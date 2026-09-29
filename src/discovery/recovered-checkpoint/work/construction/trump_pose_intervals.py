"""Rational enclosures for the eleven algebraic Trump poses.

Centers use unit-square coordinates. The centered convention subtracts half
of the exact construction side from both coordinates. Translating those
centers by S_outer/2 places the construction concentrically in an outer box.
The angle is measured counterclockwise from the positive horizontal edge,
modulo pi/2. This export proves no localization statement.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse,json
import sympy as sp
from verify_trump import M,I,E,u,configuration,polynomial_interval


def atan_partial(x,terms):
    x=F(x);return sum(((-1)**j*x**(2*j+1)/F(2*j+1) for j in range(terms)),F(0))


def pose_intervals(bits=80):
    if bits<16:raise ValueError('Use at least16 root-isolation bisections')
    if M.count_roots(*I)!=1 or not M.eval(I[0])<0<M.eval(I[1]):
        raise ValueError('Root-isolation premise failed')
    a,b=I
    for _ in range(bits):
        mid=(a+b)/2
        if M.eval(mid)<0:a=mid
        else:b=mid
    E.root_interval=(a,b)
    if not 0<a<b<1:raise ValueError('Arctangent-series domain premise failed')
    squares,side,axes=configuration(E(u))
    def enclosure(z):
        lo,hi=polynomial_interval(z.p,(a,b));return [str(lo),str(hi)]
    # atan is increasing; even-length alternating truncations are lower
    # bounds and odd-length truncations are upper bounds on (0,1).
    # 64 terms are already more accurate than the default root interval.
    angle=[str(2*atan_partial(str(a),64)),str(2*atan_partial(str(b),65))]
    poses=[]
    for i,square in enumerate(squares):
        center=[sum((vertex[j] for vertex in square),E(0))/4 for j in (0,1)]
        poses.append({'index':i,'center_absolute':[enclosure(z) for z in center],
          'centered_center':[enclosure(z-side/2) for z in center],
          'angle_radians':angle if i>=6 else ['0','0']})
    return {'status':'EXACT_RATIONAL_TRUMP_POSE_ENCLOSURES','root_interval':[str(a),str(b)],
      'side_interval':enclosure(side),'unit_square_side':'1','poses':poses,
      'center_convention':'centered_center subtracts the exact construction side/2 in both coordinates',
      'angle_convention':'Counterclockwise orientation of first edge modulo pi/2; first6 zero, last5 2atan(root)',
      'method':'Rational root bisection, rational Horner interval arithmetic, alternating arctangent series',
      'global_localization_proved':False}


def approximate_poses(digits=60):
    """High-precision exploratory values: (side, [(theta,cx,cy),...])."""
    t=sp.N(sp.CRootOf(M,1),digits+20);squares,side,_=configuration(t)
    poses=[(sp.N(0 if i<6 else 2*sp.atan(t),digits),
            sp.N(sum(v[0] for v in square)/4-side/2,digits),
            sp.N(sum(v[1] for v in square)/4-side/2,digits))
           for i,square in enumerate(squares)]
    return sp.N(side,digits),poses


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--bits',type=int,default=80)
    args=p.parse_args();result=pose_intervals(args.bits);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('Exact pose intervals:',len(result['poses']),'; root bisections:',args.bits)
if __name__=='__main__':main()
