"""Decode the public, deduplicated certificate store. Python standard library only."""
from pathlib import Path
import gzip, hashlib, json, zipfile

ROOT = Path(__file__).resolve().parents[1]

def load_index():
    index = json.loads((ROOT / 'data/INDEX.json').read_text())
    if index['schema'] != 'eleven-square-public-content-v1':
        raise ValueError('Unsupported content index')
    return index

def confined(root, name):
    p = Path(name)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Unsafe relative name')
    target = root / p
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path escapes destination')
    return target

def read_blob(record):
    path = confined(ROOT, record['object'])
    encoded = path.read_bytes()
    if encoded.startswith(b'version https://git-lfs.github.com/spec/v1'):
        raise RuntimeError('Certificate data are Git LFS pointers. Install Git LFS and run git lfs pull.')
    data = gzip.decompress(encoded)
    if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError('Content integrity failure: ' + record['object'])
    return data

class StreamingSink:
    """Always non-seekable, making ZIP output independent of destination type."""
    def __init__(self, output=None):
        self.output = output
        self.hash = hashlib.sha256()
        self.pos = 0
    def write(self, data):
        self.hash.update(data)
        self.pos += len(data)
        if self.output is not None:
            self.output.write(data)
        return len(data)
    def tell(self):
        return self.pos
    def flush(self):
        if self.output is not None:
            self.output.flush()

def write_record(record, objects, output):
    sink = StreamingSink(output)
    if record['kind'] == 'blob':
        sink.write(read_blob(record))
    elif record['kind'] == 'zip':
        with zipfile.ZipFile(sink, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
            names = set()
            for member in record['members']:
                name = member['name']
                confined(Path('/publication'), name)
                if name in names:
                    raise ValueError('Duplicate archive member')
                names.add(name)
                child = objects[member['source']]
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.external_attr = member['mode'] << 16
                info.create_system = 3
                z.writestr(info, read_blob(child))
    else:
        raise ValueError('Unknown object encoding')
    if sink.pos != record['bytes'] or sink.hash.hexdigest() != record['sha256']:
        raise ValueError('Reconstructed content differs from public index')


def materialize(index, destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for i, (name, key) in enumerate(index['files'].items(), 1):
        record = index['objects'][key]
        target = confined(destination, name)
        if target.exists():
            with target.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if digest == record['sha256']:
                continue
            raise ValueError('Existing workspace file differs; choose an empty workspace: ' + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + '.partial')
        with partial.open('wb') as stream:
            write_record(record, index['objects'], stream)
        partial.replace(target)
        if i % 100 == 0:
            print(f'Prepared {i}/{len(index["files"])} files', flush=True)
    (destination / 'evidence/.work').mkdir(exist_ok=True)
