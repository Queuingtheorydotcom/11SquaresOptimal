"""Freeze localization metadata; this does not replay spatial coverage."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,sys
if not __debug__:raise SystemExit('Assertions must remain enabled')
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encode(x):return json.dumps(x,default=str,sort_keys=True,separators=(',',':')).encode()
sys.path.insert(0,str(HERE.parent/'hull'))
from inner_grid import verify_inner
def summarize(path):
 data=json.loads(path.read_text());seed=json.loads((HERE/'mask438-seed.json').read_text())
 groups=[[tuple(map(F,p)) for p in g] for g in seed['owned_points']]
 assert sha(HERE/'mask438-seed.json')==data['seed_sha256']
 for p,h in data['dependencies'].items():assert sha(p)==h
 rounds=[];rows=points=0
 for r in data['rounds']:
  assert hashlib.sha256(encode(groups)).hexdigest()==r['prior_snapshot_sha256']
  assert [[tuple(map(F,p)) for p in g] for g in r['prior_owned_points']]==groups
  cells=[]
  for cell in r['cells']:
   rr=cell['rows']
   if rr:assert F(rr[0]['interval'][0])==0
   else:assert not cell['complete']
   assert all(F(a['interval'][1])==F(b['interval'][0]) for a,b in zip(rr,rr[1:]))
   assert all(F(z['interval'][0])<F(z['interval'][1]) for z in rr)
   if cell['complete']:assert F(rr[-1]['interval'][1])==1
   if cell.get('inner_grid_compression'):
    c=cell['inner_grid_compression'];verify_inner(cell['compression_source_hull'],c)
    for p in c['vertices']:
     p=tuple(map(F,p));points+=1
     if p not in groups[cell['owner']]:groups[cell['owner']].append(p)
   intervals=cell['retained_angle_intervals']
   cells.append(dict(owner=cell['owner'],complete=cell['complete'],retained_rows=len(intervals),retained_half_angle_total_width=sum((F(b)-F(a) for a,b in intervals),F(0)),maximum_retained_row_width=max((F(b)-F(a) for a,b in intervals),default=F(0)),center_bounds_centered_unit=cell.get('center_bounds_centered_unit'),inside_local_guard=cell['inside_local_guard']))
   rows+=len(rr)
  rounds.append(dict(index=r['index'],complete=r.get('complete',False),cells=cells))
 assert [[tuple(map(F,p)) for p in g] for g in data['owned_points']]==groups
 return dict(receipt=str(path),sha256=sha(path),bytes=path.stat().st_size,status=data['status'],seconds=data['seconds'],complete_rounds=sum(r['complete'] for r in rounds),rounds=rounds,structural_checks=dict(status='PASS',angular_rows=rows,inner_grid_witness_points=points,seed_hash=True,direct_dependency_hashes=True,immutable_prior_snapshots=True,complete_cell_angular_partitions=True,barycentric_grid_witnesses=True,spatial_coverage_replayed=False),mask_exclusion_proved=data['mask_exclusion_proved'],global_optimality_proved=data['global_optimality_proved'],branch_exclusion_proved=data.get('branch_exclusion_proved'),local_guard_geometry_captured=data['local_guard_geometry_captured'])
out=dict(scope='Producer-exact localization with structural replay only. No new mask exclusion or local guard capture. Earlier independent geometric snapshot audit is separately cited.',receipts=[summarize(HERE/n) for n in ('mask438-compact.json','mask438-adaptive.json','mask438-far-y-branch.json')],transitive_helper_hashes={str(p):sha(p) for p in (HERE.parent/'hull'/'arrangement_audit.py',HERE.parent/'hull'/'audit_residual_kernel.py',Path(__file__))},independent_snapshot_audit=str(HERE.parent/'hull'/'mask438-compact-independent-audit.json'))
(HERE/'MASK438_TERMINAL_STATUS.json').write_text(json.dumps(out,default=str,indent=2)+'\n')
print(json.dumps([dict(status=r['status'],complete_rounds=r['complete_rounds'],seconds=r['seconds'],checks=r['structural_checks']) for r in out['receipts']],indent=2))
adaptive=out['receipts'][1]
complete=[r for r in adaptive['rounds'] if r['complete']]
first,last=complete[0],complete[-1]
def width(c):return max(F(b)-F(a) for a,b in c['center_bounds_centered_unit'])
text=f'''# Mask 438 conditional ownership and pose localization

This work proves necessary pose restrictions and additional strictly owned points under canonical occupancy mask 438. It does **not** exclude this mask, capture its poses inside a local guard, exclude the tested branch, or prove global optimality.

The frozen adaptive receipt contains {adaptive['complete_rounds']} complete rounds and {len(adaptive['rounds'])-adaptive['complete_rounds']} incomplete round(s), taking {adaptive['seconds']:.2f} seconds after resuming seven completed rounds. The maximum unit center-coordinate width decreases from {float(max(map(width,first['cells']))):.9f} in round 1 to {float(max(map(width,last['cells']))):.9f} in the last complete round {last['index']}. These are rigorous outer-range widths from the producer; later rounds have not received independent spatial replay. The local guard requires much tighter localization.

For each occupied owner, every previously certified point lies strictly inside its parent square. Therefore its finite convex hull also lies strictly inside that parent. Another parent's closed strict core cannot intersect this hull. For a fixed core Q and owned hull K, forbidden centers form the rational polygon K+(-Q). Exact convex subtraction gives an outer cover of remaining legal centers for each angle interval. Intersecting the common-core strips over this outer cover supplies additional strictly owned points. Empty common kernels never imply infeasibility.

All new ownership is promoted after an immutable prior snapshot. Earlier residual domains remain valid under refinement: child angle intervals inherit their containing predecessor, and eight outward-rounded support bounds enclose every predecessor residual vertex. Inner compression keeps at most 16 grid vertices per promotion, each carrying an exact convex-combination witness. The full resumed ancestry is retained.

Independent source-distinct geometry replay passed 1983 angular rows and 57994 exact arrangement slabs: all owners in rounds 1–2 and the first six owners in round3. It also checked 130 unconditional seeds and 217 derived points. See `../hull/mask438-compact-independent-audit.json` and its bound snapshot. Later rounds are producer-exact only. `MASK438_TERMINAL_STATUS.json` freshly checks source and seed hashes, immutable prior snapshots, complete-cell angular partitions, and all recorded barycentric grid witnesses; it deliberately does not claim spatial replay.

The single bounded branch probe used centered unit y₁₅ ≤ 5/4; together with y₁₅ ≥ 5/4 these closed children cover the original case. It timed out before processing owner 15, leaving zero complete conditional rounds and no branch exclusion. `mask438-far-y-branch-provenance.json` records its exact field halfplane, start round, receipt hash, and limited scope. The inherited global rounds remain global necessary conditions.

| Owner | Final complete-round x width | Final complete-round y width | Retained angle rows |
|---:|---:|---:|---:|
'''
for c in last['cells']:
 w=[float(F(b)-F(a)) for a,b in c['center_bounds_centered_unit']]
 text+=f"| {c['owner']} | {w[0]:.9f} | {w[1]:.9f} | {c['retained_rows']} |\n"
text+='\nFrozen adaptive SHA256: `'+adaptive['sha256']+'`.\n\nNo localization worker remains active after the terminal run. A future branch experiment should process the branched owner first. The present run is a bounded partial result, not a fixed-point impossibility theorem.\n'
(HERE/'MASK438_LOCALIZATION_REPORT.md').write_text(text)
