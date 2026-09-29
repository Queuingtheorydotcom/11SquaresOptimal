#!/usr/bin/env python3
"""Read-only availability audit; never turns historical prose into a proof."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'research/jlevy'
EXPECTED={
'new_work/configuration_patterns_stage5/remaining_masks.json':'a668db70fefc3e12ba4b53944ed8633686b0dfaf1e2e6d641f4195a660b697fa',
'new_work/configuration_patterns_stage5/independent_audit.json':'0a70957c2489bd599e52df5abd5653bb962663111ac5ff70cbd0ad528f3c589a',
'new_work/configuration_root_screen/independent_terminal_proofs.json':'6ef99aa7566bf0688dc0710094d7752d004c4784faeb549f7bf274bb9e3c8a22',
'new_work/configuration_adaptive_chain/':None,
'new_work/configuration_five_column/':None,
'new_work/global_configuration_frontier/':None,
}

def main():
    paths=[p for p in REPO.rglob('*') if '.git' not in p.relative_to(REPO).parts]
    rows=[]
    for expected,digest in EXPECTED.items():
        suffix=expected.rstrip('/')
        found=[p for p in paths if p.as_posix().endswith('/'+suffix)]
        rows.append({'historical_path':expected,'expected_sha256':digest,'available_matching_paths':[str(p.relative_to(ROOT)) for p in found]})
    handoff=ROOT/'upload/ELEVEN_SQUARE_PACKING_LLM_HANDOFF.md'
    out={'status':'MISSING_HISTORICAL_FRONTIER_PROOF_OBJECTS','scope':'Imported local jlevy checkout only; no claim about inaccessible prior workspaces or external archives','source_checkout':str(REPO.relative_to(ROOT)),'checkout_commit':subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),'paths_examined':len(paths),'historical_handoff_sha256':hashlib.sha256(handoff.read_bytes()).hexdigest(),'historical_claim':{'canonical_masks':42116,'excluded':35904,'remaining':6212},'expected_objects':rows,'proof_transfer_permitted':False,'reason':'The named remaining-mask registry, complete-case proof receipts, and earlier pattern/chain proof directories are absent. Counts and hash strings cannot establish any geometric nogood without those objects.','allowed_next_step':'Reconstruct and verify fresh geometric exclusions or recover the exact missing objects; do not import historical exclusions as axioms.'}
    if any(r['available_matching_paths'] for r in rows):out['status']='SOME_HISTORICAL_PATHS_FOUND_REVIEW_REQUIRED'
    Path(__file__).with_name('old-frontier-availability.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
