"""Numerical contact diagnostic; no proof or exclusion claim is made."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
from pathlib import Path
from fractions import Fraction
import argparse
import hashlib
import json
import math
import time
import numpy as np
from scipy.optimize import minimize, least_squares


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--trials', type=int, default=4)
    args = ap.parse_args()
    start = time.monotonic()
    raw = args.source.read_bytes()
    doc = json.loads(raw)
    state = doc['final_state']
    value = lambda x: float(Fraction(x))
    U, B = value(state['U']), value(state['B'])
    mask = doc['mask']
    lo, hi = [], []
    for owner in mask:
        rows = [r for r in state['cells'][str(owner)] if r['residual_polygons']]
        vertices = np.array([[value(x)/B-U/2 for x in p]
                             for r in rows for P in r['residual_polygons'] for p in P])
        angles = [2*math.atan(value(t)) for r in rows for t in r['interval']]
        # Normalize a neighborhood crossing the square's quarter-turn seam.
        if max(angles)-min(angles) > math.pi/4:
            angles = [x-math.pi/2 if x > math.pi/4 else x for x in angles]
        lo.extend([min(angles), *vertices.min(axis=0)])
        hi.extend([max(angles), *vertices.max(axis=0)])
    lower, upper = np.array(lo), np.array(hi)
    first, second = np.triu_indices(len(mask), 1)

    def inequalities(flat, side):
        pose = flat.reshape((-1, 3))
        c, s = np.cos(pose[:, 0]), np.sin(pose[:, 0])
        e, f = np.column_stack((c, s)), np.column_stack((-s, c))
        delta = pose[second, 1:]-pose[first, 1:]
        axes = np.stack((e[first], f[first], e[second], f[second]), axis=1)
        distance = np.abs((axes*delta[:, None, :]).sum(axis=2))
        radii = .5*sum(np.abs((axes*axis[:, None, :]).sum(axis=2))
                       for axis in (e[first], f[first], e[second], f[second]))
        gap_axes = distance-radii
        gaps = gap_axes.max(axis=1)
        extent = (np.abs(c)+np.abs(s))/2
        walls = np.column_stack((side/2-pose[:, 1]-extent,
                                 side/2+pose[:, 1]-extent,
                                 side/2-pose[:, 2]-extent,
                                 side/2+pose[:, 2]-extent))
        return np.r_[gaps, walls.ravel()], gap_axes

    records = []
    rng = np.random.default_rng(doc['mask_index'])
    for trial in range(args.trials):
        seed = (lower+upper)/2 if trial == 0 else rng.uniform(lower, upper)
        fit = least_squares(lambda x: np.minimum(0, inequalities(x, U)[0]),
                            seed, bounds=(lower, upper), max_nfev=500,
                            ftol=1e-12, xtol=1e-12, gtol=1e-12)
        fixed_gap, axes = inequalities(fit.x, U)
        initial = np.r_[fit.x, U+.03]
        constraints = dict(type='ineq', fun=lambda x: inequalities(x[:-1], x[-1])[0])
        opt = minimize(lambda x: x[-1], initial, method='SLSQP',
                       bounds=list(zip(np.r_[lower, U-.05], np.r_[upper, U+.2])),
                       constraints=constraints,
                       options=dict(maxiter=1000, ftol=1e-12))
        gap, axes = inequalities(opt.x[:-1], opt.x[-1])
        contacts = [dict(owners=[mask[i], mask[j]], gap=float(gap[k]),
                         winning_axis=int(axes[k].argmax()),
                         all_axis_gaps=axes[k].tolist())
                    for k, (i, j) in enumerate(zip(first, second)) if gap[k] < 1e-6]
        records.append(dict(trial=trial, fixed_side_sum_squared_overlap=float(np.minimum(0, fixed_gap) @ np.minimum(0, fixed_gap)),
                            fixed_side_maximum_violation=float(max(0, -fixed_gap.min())),
                            side=float(opt.x[-1]), side_minus_U=float(opt.x[-1]-U),
                            minimum_constraint=float(gap.min()), success=bool(opt.success),
                            message=opt.message, poses=opt.x[:-1].reshape((-1, 3)).tolist(),
                            contacts=contacts, wall_gaps=gap[len(first):].reshape((-1, 4)).tolist()))
        print(json.dumps({k:v for k,v in records[-1].items() if k not in ('poses','contacts','wall_gaps')}), flush=True)
    result = dict(status='NUMERICAL_CONTACT_DIAGNOSTIC_ONLY', source=str(args.source.resolve()),
                  source_sha256=hashlib.sha256(raw).hexdigest(), mask_index=doc['mask_index'],
                  mask=mask, U=U, angle_center_lower_bounds=lower.reshape((-1,3)).tolist(),
                  angle_center_upper_bounds=upper.reshape((-1,3)).tolist(), trials=records,
                  mask_exclusion_proved=False, global_optimality_proved=False,
                  seconds=time.monotonic()-start)
    args.output.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
