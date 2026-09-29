"""Selectable exact rational arithmetic; no numerical tolerances are used."""
import os,sys
from pathlib import Path
BACKEND=os.environ.get('ELEVEN_RATIONAL_BACKEND','fraction')
if BACKEND=='fraction':
    from fractions import Fraction as F
    VERSION='python-fractions'
    BINARY=None
elif BACKEND=='gmp':
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'deps'))
    import gmpy2
    F=gmpy2.mpq
    VERSION=gmpy2.version()
    BINARY=Path(gmpy2.gmpy2.__file__)
else:raise RuntimeError('ELEVEN_RATIONAL_BACKEND must be fraction or gmp')
