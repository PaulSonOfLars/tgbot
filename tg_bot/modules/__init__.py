from os.path import dirname, basename, isfile
import glob

# This generates a list of modules in this folder for the * in __main__ to work.
modules = glob.glob(dirname(__file__)+"/*.py")
all_modules = [basename(f)[:-3] for f in modules if isfile(f) and f.endswith(".py") and not f.endswith('__init__.py')]
__all__ = all_modules + ["all_modules"]
