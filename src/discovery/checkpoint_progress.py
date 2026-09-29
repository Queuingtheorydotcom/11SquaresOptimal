"""Save a concrete scientific checkpoint without promoting incomplete work."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys

ROOT=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(ROOT/'frontier/extend_union.py')],stdout=subprocess.DEVNULL,check=True)
source=ROOT/'frontier/extended-union.json';raw=source.read_bytes();d=json.loads(raw)
h=hashlib.sha256(raw).hexdigest();snap=ROOT/'frontier'/f'union-snapshot-{h[:12]}.json'
snap.write_bytes(raw)
new=sorted({m for e in d['extension_entries'] for m in e['new_cases']})
def stage(name):
    path=ROOT/f'phase3-fresh-{name}/progress.json'
    if not path.exists():return 'not started'
    a=json.loads(path.read_text());return f"{a['completed']}/{a['total']} completed"
now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
lower_note=('Its full replay was left unfinished after 1,900 of 12,269 jobs passed, '
            'to prioritize the endpoint proof; this is not a fresh full verification.'
            if (ROOT/'audit-lower-bound/fresh-replay-unfinished.json').exists()
            else 'The full 12,269-job replay is running separately.')
text=rf'''# Eleven-square research checkpoint

**Global optimality is not proved. The goal remains active.**

Saved {now}. The supplied global bracket is still

\[
3.8754<s(11)\le T=3.87708359002281417730789706010096\ldots.
\]

## Concrete endpoint progress

The fixed, source-complete baseline contains 1,931 excluded canonical cases.
Its archive integrity and case union have been freshly reconstructed. Complete
new independent geometry replays add **{len(new)} cases**, giving
**{d['excluded_canonical_cases']} excluded and {d['remaining_canonical_cases']} remaining**.
These counts refer to the 2,184-case half-turn quotient of the exact 16-cell cover.
They are unions, not sums of overlapping certificates. All four construction
cases (438, 999, 1462, 1659) remain.

New cases in this frozen checkpoint: {', '.join(map(str,new))}.

The exact membership and source/receipt hashes are in
[{snap.name}]({snap}), SHA-256 `{h}`. This checker binds receipts; individual
geometric replay remains the proof obligation behind each entry.

## Checks completed and ongoing

* The continuation ZIP passed its complete file manifest and the independently
  reconstructed baseline union is byte-identical to the saved 1,931-case snapshot.
* Fresh re-execution of that baseline is ongoing: fields {stage('fields')};
  generic geometry {stage('generic')}. No uncompleted replay is counted as fresh.
* The 3.8754 lower-bound package has passed source review and finite controls.
  {lower_note}
* All three local-isolation replay stages passed, including 128 exact tangent
  branches and 8,448 weighted coordinate witnesses for the closed radius 1/248.
  See [local replay]({ROOT/'local-radius/REPLAY.md'}).
* A new D4 support calculation independently removed 14,565 center-region
  alternatives across the baseline's 253 unresolved cases. Every derived cut
  is checked against the original supported region vertices. Its use in new
  geometric proofs requires a separately checked necessity adapter.

## Remaining mathematical gap

Every surviving noncandidate case still needs a complete contradiction or
another rigorous global reduction. Case438 needs a complete capture proof into
the local theorem's neighborhood. Local rigidity, a closed search branch,
or a nearly feasible numerical layout cannot discharge that global obligation.

The mutable newer 1,955/229 registry in the attached ZIP is not source-complete:
19 geometric terminal files and three charge packets are absent. Its additional
claims are not imported. New proofs above were generated and independently
checked from available sources.

Original reference inputs and all `sources/` material are unchanged. Work is
kept under this `research/` directory so it can be continued without depending
on historical numerical summaries.
'''
(ROOT/'PROGRESS.md').write_text(text)
print(json.dumps(dict(snapshot=str(snap),new=len(new),excluded=d['excluded_canonical_cases'],remaining=d['remaining_canonical_cases'])))
