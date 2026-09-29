#!/usr/bin/env python3
"""Modular independent node replay with explicit source-bound proof premises."""
from pathlib import Path
import argparse,json,time
import audit_capture_v6 as a
import audit_tree_batch as cache
if not __debug__:raise RuntimeError('Assertions must be enabled')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('receipt',type=Path);ap.add_argument('--root-audit',type=Path);ap.add_argument('--certified-cache',type=Path,action='append',default=[]);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    begin=time.monotonic();d=json.loads(args.receipt.read_text());source=a.locate(d['source']['path'],args.receipt)
    replay=a.Replay(source,args.root_audit,generic_mode=d['schema']=='exact_generic_owned_hull_v1')
    premises=cache.load_cache(replay,args.certified_cache);input_hash=a.sha(args.receipt)
    replay.replay(args.receipt.resolve());assert a.sha(args.receipt)==input_hash and a.sha(source)==replay.source_hash
    for r in replay.records:assert a.sha(r['path'])==r['sha256']
    final=next(r for r in replay.records if r['sha256']==input_hash)
    unconditional=bool(final['branch_exclusion_proved'] and not final['constraints'])
    canonical=json.loads(a.COVER.read_text())['canonical_eleven_cell_subsets']
    transferred=[i for i,J in enumerate(canonical) if set(replay.mask)<=set(J) or set(replay.mask)<={15-j for j in J}] if unconditional else []
    files=[Path(__file__),Path(cache.__file__),Path(a.__file__),Path(a.geo.__file__),Path(a.collision.__file__),Path(a.rational.__file__),
           Path(__file__).with_name('audit_residual_kernel.py'),Path(__file__).with_name('arrangement_audit.py'),a.WORK/'geometry/audit_wall_kernel.py',
           a.WORK/'geometry/audit_kernel_survivor.py',*replay.root_dependency_files]
    out=dict(status='PASS_INDEPENDENT_GENERIC_HULL_AUDIT' if replay.generic_mode else 'PASS_INDEPENDENT_BRANCH_HULL_AUDIT',
             source_sha256=input_hash,root_sha256=replay.source_hash,root_audit_sha256=a.sha(args.root_audit) if args.root_audit else None,
             required_antecedent_mask=replay.mask,mask=replay.mask,mask_index=replay.root['mask_index'],parent_Uplus=str(replay.U),parent_side=str(replay.B),
             cover_sha256=a.sha(a.COVER),constraints=final['constraints'],final_state_sha256=a.digest(d['final_state']),bootstrap=replay.bootstrap,
             seed_ownership_checks=replay.seed_checks,premise_audits=premises,nodes=replay.records,
             dependencies={p.name:a.sha(p) for p in files},rational_backend=a.rational.BACKEND,rational_backend_version=a.rational.VERSION,
             rational_binary_sha256=a.sha(a.rational.BINARY) if a.rational.BINARY else None,
             branch_exclusion_proved=final['branch_exclusion_proved'],inside_local_guard=final['inside_local_guard'],mask_exclusion_proved=unconditional,
             transferred_canonical_mask_indices=transferred,continuum_canonical_masks_excluded=len(transferred),global_optimality_proved=False,
             rows_replayed_this_run=sum(r['rows'] for r in replay.records if 'cached_from_audit_sha256' not in r),
             rows_in_cached_premises=sum(r['rows'] for r in replay.records if 'cached_from_audit_sha256' in r),seconds=time.monotonic()-begin)
    args.output.write_text(json.dumps(out,default=str,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('nodes','seed_ownership_checks')},default=str,indent=2))
if __name__=='__main__':main()
