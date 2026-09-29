"""Strictly integrate the frozen 76 prior extensions; no geometric replay.

Run only in the root's CPU-limited single-worker slot. This script hashes
large files and invokes strict inventory checkers; preparation does neither.
It writes only the selected output directory, never the old root ledger.
"""
if not __debug__:
    raise SystemExit('Assertions must remain enabled; -O/-OO is refused.')

import argparse
from collections import Counter
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import hashlib,json,sys,time

HERE=Path(__file__).resolve().parent
PINS={
    'strict_generic_inventory.py':'7df54d904bb5d0cc609a4765eeafc3fb57922bcb3a4b210082df9fda36266530',
    'strict_tree_inventory.py':'b6a298ccfa1a27911b3e88c832f890a983e0c6e7c374455808e42eb730626059',
    'strict-inventory-pins.json':'8a46589d35e3bbd1efce02b2a196db5ddb636a85259bf7f30d6b31daa65b01f8',
}
BASELINE_SHA='bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545'
FRESH_SHA='04fa1ebb37f5dace29946224fe8c7c5d8a1bedb4fa860c65b359f4200415de57'
SNAPSHOT_SHA='ac6d560598823e612d8d8f03be6918601456064fe7c4c52a4bec31d3bb1ada2a'
COVER_SHA='df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e'
OVERLAY_SHA='f3eefa77e6f02b977d6bfe38e5bc7e1e32fd6e355de7d226c803291b9a6ea5e1'
NECESSITY_SHA='ee942f83af21aa2ab58b080b37cc95d5064d37b0458cfd2b93c2be8ab7ba1c74'
EXPECTED_TEN=[927,998,1111,1112,1114,1115,1124,1125,1128,1143]
U=F(387708359002281417731,10**20)
B=F(191,50)/U


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())
def write(path,value):
    tmp=path.with_suffix('.writing')
    tmp.write_text(json.dumps(value,indent=2)+'\n')
    tmp.replace(path)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workspace',type=Path,default=HERE.parents[2])
    ap.add_argument('--inventory',type=Path,default=HERE/'SOURCE_INVENTORY.json')
    ap.add_argument('--inventory-sha256',required=True,help='Pin supplied by EXECUTION_PLAN.json/root review.')
    ap.add_argument('--output-dir',type=Path,default=HERE/'completed')
    args=ap.parse_args();start=time.monotonic()
    workspace=args.workspace.resolve();research=workspace/'research';output=args.output_dir.resolve()
    output.mkdir(parents=True,exist_ok=True)
    require(sha(args.inventory)==args.inventory_sha256,'Prepared package inventory changed')
    prepared=read(args.inventory)
    require(prepared['schema']=='eleven_square_prior_union_package_inventory_v1','Wrong package inventory schema')
    # The source-frozen validators contain historical absolute-path checks.
    # Do not silently fall back to those paths after package relocation.
    require(workspace==Path(prepared['original_workspace']).resolve(),
            'Relocated package: use the separately reviewed portable adapter plan; historical-path fallback is forbidden.')
    require(prepared['expected_extension_receipts']==76 and prepared['expected_union_cases']==2007,'Wrong frozen integration target')
    inventory_dir=research/'audit-lower-bound'
    for name,h in PINS.items():require(sha(inventory_dir/name)==h,'Changed strict checker: '+name)
    require(sha(research/'frontier/audit_overlay_exclusion.py')==OVERLAY_SHA,'Changed overlay adapter')
    require(sha(research/'global-math/overlay_field_halfplanes_v2.py')==NECESSITY_SHA,'Changed necessity checker')
    baseline_path=research/'phase3/work/phase3/audit/overall-union-snapshot-bc3563a0c995.json'
    fresh_path=research/'PHASE3_FRESH_REPLAY_RESULT.json'
    snapshot_path=research/'relay-handoff/frozen-frontier-count-crosscheck.json'
    cover_path=research/'phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json'
    for path,h in [(baseline_path,BASELINE_SHA),(fresh_path,FRESH_SHA),(snapshot_path,SNAPSHOT_SHA),(cover_path,COVER_SHA)]:
        require(sha(path)==h,'Changed fixed premise: '+str(path))
    baseline,fresh,snapshot,cover=map(read,[baseline_path,fresh_path,snapshot_path,cover_path])
    require(fresh['status']=='PASS_FRESH_INDEPENDENT_1931_CASE_UNION','Fresh baseline is incomplete')
    require(fresh['authoritative_snapshot_sha256']==BASELINE_SHA and fresh['cover_sha256']==COVER_SHA,'Fresh baseline premise differs')
    require(fresh['field_certificates']==59 and fresh['generic_certificates']==34 and fresh['excluded']==1931,'Fresh baseline inventory differs')
    require(fresh['excluded_canonical_mask_indices']==baseline['excluded_canonical_mask_indices'],'Fresh and saved baseline sets differ')
    require(F(fresh['parent_Uplus'])==U and F(fresh['parent_side'])==B,'Fresh baseline exact domain differs')
    # Bind every prepared large source by streaming it once. The strict
    # consumers will independently verify full JSON ancestry and dependencies.
    bindings=[];targets=set()
    for i,item in enumerate(prepared['files']):
        rel=Path(item['target']);p=(workspace/rel).resolve()
        require(not rel.is_absolute() and '..' not in rel.parts and p.is_relative_to(workspace),'Unsafe package target')
        require(item['target'] not in targets,'Duplicate package target');targets.add(item['target'])
        require(p==Path(item['source']).resolve(),'Source/target map differs')
        require(p.stat().st_size==item['bytes'],'Source size differs: '+str(p))
        actual=sha(p);require(actual==item['expected_sha256'],'Source hash differs: '+str(p))
        bindings.append(dict(source=str(p),target=item['target'],sha256=actual,bytes=item['bytes'],roles=item['roles']))
        if (i+1)%20==0:
            print(json.dumps(dict(stage='source_bindings',completed=i+1,total=len(prepared['files']))),flush=True)
    write(output/'validated-source-inventory.json',dict(status='PASS_STREAMED_SOURCE_BINDINGS',files=bindings))
    canonical=sorted({min(J,tuple(sorted(15-j for j in J))) for J in combinations(range(16),11)})
    require(len(canonical)==2184 and list(map(list,canonical))==cover['canonical_eleven_cell_subsets'],'Canonical case cover differs')
    base=set(baseline['excluded_canonical_mask_indices']);union=set(base)
    require(len(base)==1931,'Baseline count differs')
    selected=snapshot['entries'];prepared_entries=prepared['entries']
    require(len(selected)==len(prepared_entries)==76,'Missing extension receipt')
    require([(x['mask'],x['audit_sha256']) for x in selected]==[(x['mask_index'],x['audit_sha256']) for x in prepared_entries],'Frozen receipt selection differs')
    sys.path.insert(0,str(inventory_dir))
    from strict_generic_inventory import validate as validate_generic
    from strict_tree_inventory import validate as validate_tree
    sys.path.insert(0,str(research/'frontier'))
    from audit_overlay_exclusion import validate as validate_overlay
    entries=[];support_counts=Counter();case_evidence={i:['baseline:'+BASELINE_SHA] for i in base}
    for ordinal,(expected,item) in enumerate(zip(selected,prepared_entries),1):
        audit=(workspace/item['audit_target']).resolve()
        require(sha(audit)==expected['audit_sha256'],'Selected receipt changed')
        if item['kind']=='necessary_D4_cuts_and_independent_geometry':
            r=read(audit)
            actual=validate_overlay(Path(r['source']),Path(r['geometric_audit']))
            require(actual==r,'Overlay necessity/source integration differs')
            cases={r['mask_index']}
            details=dict(source=r['source'],source_sha256=r['source_sha256'],nodes=len(r['checked_ancestry']))
        elif item['kind']=='native_cached_v4_center_partition':
            proved=validate_tree(audit,tree_path=research/'endpoint-audit/mask1383-two-branch-tree.json')
            cases=proved['cases'];details={k:proved[k] for k in ['source','source_sha256','nodes','leaves']}
        else:
            proved=validate_generic(audit)
            require(proved['dependency_profile']==item['kind'],'Generic dependency profile differs')
            cases=proved['cases'];details={k:proved[k] for k in ['source','source_sha256','nodes']}
        require(cases==set(expected['cases'])==set(item['expected_cases']),'Exact transferred case set differs')
        require(cases=={expected['mask']},'Unexpected multi-case transfer in the frozen 76 extensions')
        require(not cases & base,'Extension duplicates baseline in this frozen selection')
        new=cases-union;union|=cases
        for i in cases:
            support_counts[i]+=1;case_evidence.setdefault(i,[]).append(expected['audit_sha256'])
        entries.append(dict(mask=expected['mask'],audit=str(audit),audit_sha256=expected['audit_sha256'],kind=item['kind'],cases=sorted(cases),new_cases=sorted(new),**details))
        write(output/'progress.json',dict(status='RUNNING_STRICT_PRIOR_EXTENSION_INTEGRATION',completed=ordinal,total=76,entries=entries,seconds=time.monotonic()-start))
        print(json.dumps(dict(stage='strict_receipt',completed=ordinal,total=76,mask=expected['mask'])),flush=True)
    require(len(support_counts)==76 and all(v==1 for v in support_counts.values()),'Duplicated/missing extension coverage')
    require(union==set(snapshot['excluded_cases']) and len(union)==2007,'Candidate 2007 union not established')
    remaining=sorted(set(range(2184))-union)
    require(len(remaining)==177 and all(i in remaining for i in [438,999,1462,1659]),'Remaining cases/candidates differ')
    previous_path=research/'frontier/union-snapshot-93856c2b8cd8.json'
    require(sha(previous_path)==prepared['last_strict_union_sha256'],'Previous strict checkpoint changed')
    previous=read(previous_path);prior=set(previous['excluded_canonical_mask_indices'])
    require(len(prior)==1997 and prior<=union and sorted(union-prior)==EXPECTED_TEN,'The ten-case reconciliation differs')
    result=dict(schema='eleven_square_prior_extension_integration_v1',status='PASS_STRICT_PRIOR_76_EXTENSION_INTEGRATION',
        baseline_path=str(baseline_path),baseline_sha256=BASELINE_SHA,baseline_excluded=1931,
        fresh_baseline_geometry_replay_completed=True,fresh_baseline_replay=dict(path=str(fresh_path),sha256=FRESH_SHA),
        fresh_baseline_geometry_replayed_this_run=False,prior_extension_geometry_replayed_this_run=False,
        snapshot_sha256=SNAPSHOT_SHA,prepared_inventory_sha256=args.inventory_sha256,
        validated_source_inventory_sha256=sha(output/'validated-source-inventory.json'),
        integration_checker_sha256=sha(__file__),inventory_checkers=PINS,extension_entries=entries,
        extension_receipts=76,distinct_extension_cases=76,previous_strict_cases=1997,
        new_cases_since_previous_strict=EXPECTED_TEN,excluded_canonical_mask_indices=sorted(union),
        excluded_canonical_cases=2007,remaining_canonical_mask_indices=remaining,remaining_canonical_cases=177,
        per_case_evidence={str(i):v for i,v in sorted(case_evidence.items())},global_optimality_proved=False,
        negative_control_suite_completion_claimed=False,seconds=time.monotonic()-start,
        scope='All frozen prior receipts and current source bytes bound and strict inventories/necessary antecedents checked. The already completed baseline and extension geometric replays are reused as source-bound premises; no geometry replay or final global theorem is claimed here.')
    write(output/'PRIOR_UNION_RESULT.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['extension_entries','excluded_canonical_mask_indices','remaining_canonical_mask_indices','per_case_evidence']},indent=2))


if __name__=='__main__':main()
