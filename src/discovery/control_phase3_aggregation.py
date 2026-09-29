"""Negative controls for baseline proof inventory and immutable snapshot binding.

Only small in-memory metadata are mutated; proof artifacts are never changed.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

base = Path(__file__).resolve().parent
path = base / 'aggregate_phase3_fresh.py'
spec = importlib.util.spec_from_file_location('phase3_aggregate', path)
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
manifest = a.read(a.ROOT / 'PHASE3_REPLAY_MANIFEST.json')
controls = []


def reject(label, operation):
    try:
        operation()
    except (AssertionError, KeyError):
        controls.append(dict(control=label, rejected=True))
    else:
        raise RuntimeError('Negative control accepted: ' + label)


for kind, key, digest, count in [('field', 'packet', 'packet_sha256', 59), ('generic', 'source', 'source_sha256', 34)]:
    recipes = manifest[kind + '_recipes']
    result = a.read(base / ('phase3-fresh-' + ('fields' if kind == 'field' else 'generic')) / 'RESULT.json')
    records = result['records']
    a.validate_inventory(recipes, records, count, key, digest)
    reject(kind + '_missing_last_record', lambda: a.validate_inventory(recipes, records[:-1], count, key, digest))
    reject(kind + '_missing_last_recipe', lambda: a.validate_inventory(recipes[:-1], records, count, key, digest))
    duplicate = copy.deepcopy(records)
    duplicate[-1] = copy.deepcopy(duplicate[0])
    duplicate[-1]['index'] = count-1
    reject(kind + '_duplicate_record_with_adjusted_index', lambda: a.validate_inventory(recipes, duplicate, count, key, digest))
    reordered = copy.deepcopy(records)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    for i, record in enumerate(reordered):
        record['index'] = i
    reject(kind + '_reordered_records_with_adjusted_indices', lambda: a.validate_inventory(recipes, reordered, count, key, digest))
    duplicated_recipe = copy.deepcopy(recipes)
    duplicated_recipe[-1] = copy.deepcopy(duplicated_recipe[0])
    reject(kind + '_duplicate_manifest_recipe', lambda: a.validate_inventory(duplicated_recipe, records, count, key, digest))
    reused_output = copy.deepcopy(records)
    reused_output[-1]['output'] = reused_output[0]['output']
    reject(kind + '_same_output_twice', lambda: a.validate_inventory(recipes, reused_output, count, key, digest))

a.validate_snapshot_binding(manifest)
for key, value in [('overall_union', 'work/phase3/audit/overall-union-independent-audit.json'), ('overall_union_sha256', '0'*64), ('field_registry', 'other.json'), ('field_registry_sha256', '0'*64)]:
    changed = copy.deepcopy(manifest)
    changed[key] = value
    reject('wrong_' + key, lambda: a.validate_snapshot_binding(changed))

for label, command, extra_env in [('optimized_flag', [sys.executable, '-O', str(path)], {}), ('optimized_environment', [sys.executable, str(path)], {'PYTHONOPTIMIZE': '1'})]:
    env = os.environ.copy()
    env.update(extra_env)
    result = subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode != 0 and 'Assertions must be enabled' in result.stderr
    controls.append(dict(control=label, rejected=True, exit_code=result.returncode))

result = dict(status='PASS_AGGREGATION_NEGATIVE_CONTROLS', aggregation_checker_sha256=a.sha(path), control_checker_sha256=a.sha(__file__), controls=controls, proof_artifacts_modified=False)
(base / 'phase3-aggregate-controls.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
