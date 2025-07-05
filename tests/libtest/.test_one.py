import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
module = __import__(str(pathlib.Path(sys.argv[1]).with_suffix("")))
default_url = "http://example.com"
res = module.test(*(sys.argv[2:] if sys.argv[2:] else [default_url]))
print(f"Test: {module.__name__}:", f"ERROR: {res}" if res else "OK")
