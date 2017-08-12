def __list_all_modules():
    from os.path import dirname, basename, isfile, join
    import glob
    # This generates a list of modules in this folder for the * in __main__ to work.
    mod_paths = glob.glob(dirname(__file__)+"/*.py")

    # load modules from the order in this file.
    try:
        with open(join(dirname(__file__), "loadorder.txt")) as f:
            contents = f.read().split()

        if contents:
            if all(any(mod == basename(path)[:-3] for path in mod_paths) for mod in contents):
                return contents
            else:
                print("Invalid loadorder names. Quitting.")
                quit(1)
    except FileNotFoundError:
        pass

    return [basename(f)[:-3] for f in mod_paths if isfile(f) and f.endswith(".py") and not f.endswith('__init__.py')]

ALL_MODULES = __list_all_modules()
__all__ = ALL_MODULES + ["ALL_MODULES"]
