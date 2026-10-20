from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("sorted")
except PackageNotFoundError:
    # package is not installed
    pass
