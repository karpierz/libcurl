import sys, pathlib, runpy
py_path = pathlib.Path(sys.argv[1]).resolve()
sys.argv = [None] + (sys.argv[2:] if sys.argv[2:] else [])
try: res = 0 ; runpy.run_path(py_path, run_name="__main__")
except SystemExit as exc: res = exc.code
print(f"Run: {py_path.name}:", f"ERROR: {res}" if res else "OK")
