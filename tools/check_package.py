"""Integrity and privacy checks for the publication, not a geometric verifier."""
from pathlib import Path
import ast, hashlib, json, re, sys
from content import ROOT, load_index, read_blob, write_record

PRIVATE = [re.compile(rb'\buser_authorized_cpu_limit\b|user.{0,10}CPU limit|parent.authorized.{0,40}agreed CPU'),
           re.compile(rb'/Users/[^/\s\"\x27]+'),
           re.compile(rb'g-p-[0-9a-f]{20,}'),
           re.compile(rb'/(?:private/)?var/folders/'),
           re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'),
           re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),
           re.compile(rb'github_pat_[A-Za-z0-9_]{40,}')]

def scan(data, label):
    for pattern in PRIVATE:
        if pattern.search(data):
            raise ValueError('Possible private identifier in ' + label)


def main():
    index = load_index()
    scan((ROOT/'data/INDEX.json').read_bytes(), 'content index')
    count = 0
    for key, record in index['objects'].items():
        if record['kind'] == 'blob':
            scan(read_blob(record), 'object ' + record['sha256'])
        else:
            write_record(record, index['objects'], None)
        count += 1
        if count % 250 == 0:
            print(f'Checked {count}/{len(index["objects"])} content objects', flush=True)
    source_count = 0
    for name, key in index['files'].items():
        if name.endswith(('.log','.pyc')) or 'run-history/' in name:
            raise ValueError('Execution log or bytecode in published inventory')
        exposed = ROOT/'src'/name
        if exposed.is_file():
            data = exposed.read_bytes()
            if hashlib.sha256(data).hexdigest() != index['objects'][key]['sha256']:
                raise ValueError('Browsable source differs from encoded source: ' + name)
            if name.endswith('.py'):
                ast.parse(data, filename=name)
                source_count += 1
    for p in ROOT.rglob('*'):
        if not p.is_file() or any(x in p.relative_to(ROOT).parts for x in ('.git','work','.venv','data','.composition-check')):
            continue
        # The scanner's own expressions describe identifiers and aren't secrets.
        if p == Path(__file__).resolve():
            continue
        scan(p.read_bytes(), p.relative_to(ROOT).as_posix())
    report = dict(status='PASS_PUBLICATION_INTEGRITY_AND_PRIVACY',
                  geometric_proof_replayed=False, content_objects=count,
                  decoded_files=len(index['files']), parsed_python_sources=source_count,
                  scope='Content hashes, archive reconstruction, source copies and listed private-identifier patterns; not a proof of mathematical soundness or exhaustive personal-data detection.')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
