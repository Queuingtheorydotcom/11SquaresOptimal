from pathlib import Path
import hashlib, json, subprocess
root=Path(__file__).resolve().parents[1]/"recovered-checkpoint"
source=root/"research/jlevy/packing"
inputs=json.loads((root/"research/classical/trump-local-conservative-radius.json").read_text())["source_hashes"]
inputs["campaign/series/series-000-smoke-and-calibration/results/exp-013-h-026-trump-tangent.json"]="60a4b7c48034b37063509a8a641974ed5eae86dccd056e9cbc6cf2fd7f2f0661"
ref="c55726e1e885227f63110131c0a914665175ff89"
for name,expected in inputs.items():
 url=f"https://raw.githubusercontent.com/jlevy/squares/{ref}/packing/{name}"
 data=subprocess.check_output(['curl','-fsSL','--max-time','30',url])
 assert hashlib.sha256(data).hexdigest()==expected,(name,"source differs")
 target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 print(name,len(data),expected,flush=True)
