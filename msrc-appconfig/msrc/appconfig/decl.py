import importlib
import pkgutil
from functools import lru_cache
import typing as ty
from types import ModuleType
import msrc.appconfig_decl


@lru_cache(maxsize=1)
def get_installed_decl() -> ty.Mapping[str, ModuleType]:
    prefix = getattr(msrc.appconfig_decl, "__name__", '') + '.'
    path: ty.Iterable[str] = getattr(msrc.appconfig_decl, "__path__", [])
    return {
        name: importlib.import_module(name)
        for _, name, _ in pkgutil.iter_modules(path, prefix)
    }
