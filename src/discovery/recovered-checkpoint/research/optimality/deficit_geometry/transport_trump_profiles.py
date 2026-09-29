"""Fifty-five numerical transported Trump profiles; finite-family diagnostic."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,math,hashlib
import numpy as np
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/stromquist'))
from true_majority_model import TrueMajorityModel
OUT=Path(__file__).parent
SOURCE=ROOT/'research/true_catalogue/round6-cutround12-surplus-3.8754-full/proposal.json'

def main():
    model=TrueMajorityModel(SOURCE); L=model.L
    data=json.loads((ROOT/'work/construction/trump-pose-intervals.json').read_text())
    alpha=float(sum(map(F,data['side_interval']))/2); B=L/alpha
    poses=[]
    for p in data['poses']:
        theta=float(sum(map(F,p['angle_radians']))/2)
        center=np.array([float(sum(map(F,z))/2) for z in p['centered_center']])
        poses.append([theta,*(L/2+B*center)])
    poses=np.array(poses); cs=np.cos(poses[:,0])+np.sin(poses[:,0]);targets=['3.8755','3.876','3.8765','3.877','3.87708']
    reports=[];allrows=[];allposes=[]
    for target in targets:
        A=L/float(target);P=poses.copy();P[:,1:]=L/2+(P[:,1:]-L/2)*((L-A*cs)/(L-B*cs))[:,None]
        rows=model.capture(A,P); sums=rows.astype(np.int64).sum(axis=0);over=np.flatnonzero(sums>model.budget)
        reports.append(dict(target=target,A=str(F(model.c['L'])/F(target)),overloaded_columns=len(over),columns=over.tolist(),maximum_overload=int((sums-model.budget).max()),all_column_budgets_respected=not len(over)))
        allrows.append(rows);allposes.append(P)
    np.savez_compressed(OUT/'transported-trump-profiles.npz',rows=np.array(allrows),poses=np.array(allposes),targets=np.array(targets),budget=model.budget.astype(np.int64))
    report=dict(status='NUMERICAL_FINITE_FEATURE_BARRIER_SCREEN_ONLY',source=str(SOURCE.relative_to(ROOT)),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),pose_count=55,report=reports,global_geometry=False,exact_rational_followup_required=True,scope='Each individual transported pose is contained numerically. No nonoverlap among the11 parents is asserted. Column sums satisfying all budgets obstruct a scalar nonnegative reweighting of this finite family only, after exact certification.')
    (OUT/'transported-trump-profiles.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':
    with threadpool_limits(limits=1):main()
