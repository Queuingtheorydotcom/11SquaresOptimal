"""Independent brute-force controls for finite-domain exclusion search."""
import itertools
import json
from fractions import Fraction as F
from random import Random
from pathlib import Path
from kernel import Domain
from probe import arc_consistency, clique_search
from replay import independent_exhaustion


def main():
    rng = Random(1188)
    checks = 0
    domains = [Domain(c, ((F(0), F(0)),), (F(0), F(0))) for c in range(4) for _ in range(3)]
    bycell = {c: list(range(3*c, 3*c+3)) for c in range(4)}
    for _ in range(100):
        forbidden = {(a,b) for a,b in itertools.combinations(range(12), 2)
                     if domains[a].cell != domains[b].cell and rng.randrange(100) < 65}
        adjacency = [set(b for b in range(12) if domains[a].cell != domains[b].cell and
                         (min(a,b), max(a,b)) not in forbidden) for a in range(12)]
        truth = any(all((min(a,b), max(a,b)) not in forbidden for a,b in itertools.combinations(choice,2))
                    for choice in itertools.product(*(bycell[c] for c in range(4))))
        empty, active, _ = arc_consistency(range(4), bycell, adjacency)
        result = {'status': 'EXCLUDED'} if empty else clique_search(range(4), active, adjacency, 100000)
        independent, _ = independent_exhaustion(range(4), domains, forbidden, 100000)
        assert (result['status'] == 'ABSTRACT_ASSIGNMENT') == truth
        assert (independent == 'ABSTRACT_ASSIGNMENT') == truth
        checks += 2
    full = [set(b for b in range(12) if domains[a].cell != domains[b].cell) for a in range(12)]
    result = clique_search(range(4), {c:set(v) for c,v in bycell.items()}, full, 1)
    assert result['status'] == 'NODE_LIMIT'
    checks += 1
    out = {'status': 'PASS_FINITE_CSP_CONTROLS', 'checks': checks, 'global_optimality_proved': False}
    Path(__file__).with_name('graph-controls.json').write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps(out))


if __name__ == '__main__':
    main()
