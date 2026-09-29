"""Run unchanged archived checkers with the native exact GMP backend preloaded.

Only import resolution changes: the supplied Linux binary cannot run on macOS.
Every certificate/checker remains byte-identical. Fresh receipts record the
native binary hash. Existing archive path resolvers map original work/current
paths to the extracted archive, without altering certificate strings.
"""
from pathlib import Path
import hashlib,json,os,importlib.util,sys
import gmpy2

if not __debug__:
    raise RuntimeError('Assertions must be enabled')
root=Path(__file__).resolve().parent/'phase3'
script=(root/sys.argv[1]).resolve()
if not script.is_relative_to(root):
    raise ValueError('Checker must belong to the extracted archive')
print(json.dumps(dict(portability='Native GMP preload; source unchanged',
    binary=str(gmpy2.gmpy2.__file__),
    binary_sha256=hashlib.sha256(Path(gmpy2.gmpy2.__file__).read_bytes()).hexdigest(),
    checker=str(script), checker_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
    extraction_root=str(root))),flush=True)
os.environ['ELEVEN_RATIONAL_BACKEND']='gmp'
os.environ['ELEVEN_PACKING_ROOT']=str(root/'current')
os.chdir(root)
sys.argv=[str(script),*sys.argv[2:]]
sys.path.insert(0,str(script.parent))
spec=importlib.util.spec_from_file_location('phase3_portable_checker',script)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if hasattr(module,'locate'):
    original_locate=module.locate
    mapped=set()
    def portable_locate(path,relative):
        try:return original_locate(path,relative)
        except FileNotFoundError:
            parts=Path(path).parts
            if Path(path).is_absolute() and parts.count('current')==1:
                q=(root/Path(*parts[parts.index('current'):])).resolve()
                if q.is_relative_to(root/'current') and q.is_file():
                    if str(path) not in mapped:
                        print(json.dumps(dict(path_mapping_from=str(path),path_mapping_to=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest())),flush=True)
                        mapped.add(str(path))
                    return q
            raise
    module.locate=portable_locate
module.main()
