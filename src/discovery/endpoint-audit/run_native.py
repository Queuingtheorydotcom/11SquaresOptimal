"""Run unchanged Phase3 scripts using the installed native GMP library.

Preloading gmpy2 prevents archived Linux-only dependency directories from
shadowing the native package. All mathematical source files stay unchanged.
"""
import os
from pathlib import Path
import runpy
import sys
import gmpy2

os.environ['ELEVEN_RATIONAL_BACKEND'] = 'gmp'
script = Path(sys.argv[1]).resolve()
sys.argv = sys.argv[1:]
sys.path.insert(0, str(script.parent))
runpy.run_path(str(script), run_name='__main__')
