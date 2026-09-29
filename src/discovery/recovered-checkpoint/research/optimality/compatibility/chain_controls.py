"""Soundness controls for the new multi-neighbor longitudinal contraction."""
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path
from kernel import Domain, cs
from chain import gap_lower, contract


def main():
    count = 0
    # Every exact rotated edge contact must respect the claimed gap lower bound.
    for n in range(41):
        t = F(n,40); c,s = cs(t)
        assert gap_lower((t,t),(t,t),abs(s)) <= c
        assert gap_lower((t,t),(t,t),abs(c)) <= s
        count += 2
    # Four ordered centers in a horizontal span below three cannot carry
    # four axis-aligned unit squares at the same transverse coordinate.
    p = ((F(1,2),F(1,2)),(F(33,10),F(1,2)))
    domains = [Domain(k,p,(F(0),F(0))) for k in range(4)]
    bycell = {k:[k] for k in range(4)}
    adj = [set(range(4))-{k} for k in range(4)]
    orders = [{'left':k,'right':k+1,'axis':0} for k in range(3)]
    assert contract(list(range(4)),domains,bycell,adj,orders)['status'] == 'EXCLUDED'
    count += 1
    # Equality at side four must remain possible.
    p = ((F(1,2),F(1,2)),(F(7,2),F(1,2)))
    domains = [Domain(k,p,(F(0),F(0))) for k in range(4)]
    assert contract(list(range(4)),domains,bycell,adj,orders)['status'] != 'EXCLUDED'
    count += 1
    # Nonempty rectangular uncertainty around a feasible 3x3 grid.
    ds = []
    for i,j in product(range(3), repeat=2):
        x,y = F(i)+F(1,2),F(j)+F(1,2); e = F(1,1000)
        poly = ((x-e,y-e),(x+e,y-e),(x+e,y+e),(x-e,y+e))
        ds.append(Domain(len(ds),poly,(F(0),F(0))))
    by = {k:[k] for k in range(9)};adj = [set(range(9))-{k} for k in range(9)]
    oo = []
    for i in range(3):
        for j in range(2):
            oo += [{'left':3*j+i,'right':3*(j+1)+i,'axis':0},
                   {'left':3*i+j,'right':3*i+j+1,'axis':1}]
    assert contract(list(range(9)),ds,by,adj,oo)['status'] != 'EXCLUDED'
    count += 1
    out = {'status':'PASS_LONGITUDINAL_CONTROLS','checks':count,'global_optimality_proved':False}
    Path(__file__).with_name('chain-controls.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out))


if __name__ == '__main__':
    main()
