import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
lib = __import__(str(pathlib.Path(sys.argv[1]).with_suffix("")))
default_url = "http://example.com"
res = lib.test(*sys.argv[2:]) if sys.argv[2:] else lib.test(default_url)
print("Test: %s:" % lib.__name__, ("ERROR: %d" % res) if res else "OK")
