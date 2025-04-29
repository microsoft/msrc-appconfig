from __future__ import annotations
from typing import Dict, Generator, List, Mapping, Optional
from typing import Sequence, Tuple, Type, TypeVar, Union
"""Flexible typed application configuration."""
import itertools
import threading
from os import PathLike
import logging

from msrc.appconfig.schema import Schema as _Schema
from msrc.appconfig.schema import ConfigMapping as _ConfigMapping
from msrc.appconfig.schema import ConfigMappingValueType as _ConfigValue
from msrc.appconfig.schema import as_dict as _as_dict
from msrc.appconfig.schema import get_schema as _get_schema
from msrc.appconfig.read_files import from_file as _from_file
from msrc.appconfig.read_files import optional_file
from msrc.appconfig.read_files import script_config_file
from msrc.appconfig.read_files import config_files_in_parents
from msrc.appconfig.read_files import main_script as _main_script
from msrc.appconfig.read_environ import from_environ as _from_environ
from msrc.appconfig.read_argv import from_argv as _from_argv
from msrc.appconfig.read_argv import to_arg_dict as _to_arg_dict
from msrc.appconfig.read_all import gather as _gather

__all__ = [
    "gather_config",
    "set_global",
    "get_global",
    "from_files",
    "from_environ",
    "from_argv",
    "from_dict",
    "to_dict",
    "optional_file",
    "script_config_file",
    "config_files_in_parents",
    "to_arg_dict",
    "to_argv"
]

AppConfig = TypeVar('AppConfig')


class _SharedInstance:
    appconfig = None
    lock = threading.Lock()

    @classmethod
    def get_config(cls) -> object:
        return cls.appconfig

    @classmethod
    def set_config(cls, value: object) -> None:
        with cls.lock:
            if cls.appconfig is None:
                cls.appconfig = value
            else:
                raise RuntimeError(
                    "Global configuration has already been set up."
                )


def gather_config(
    config_type: Type[AppConfig],
    override_defaults: _ConfigMapping = {},
    config_files: Sequence[Union[str, PathLike[str]]] = [],
    env_var_prefix: Optional[str] = None,
    argv: Optional[Sequence[str]] = None,
    arg_aliases: Mapping[str, str] = {},
    set_global: bool = False,
    log_level: int = logging.INFO
) -> AppConfig:
    """Gathers configuration values from files, shell and command line.

    The function is a main tool to build application configuration object
    for a script.

    `config_type` is the only required argument. Must be is a class object.
    The `config_type` can be a `typing.NamedTuple` or a class supported by
    one of the package extensions.

    `override_defaults` is a mapping that allows to override the defaults
    in the `config_type` class.

    `config_files` is a sequence of configuration file paths, strings
    or `PathLike` objects. The function reads the files in sequence.
    See also utility functions that help build the list for certain
    use cases: `script_config_file()`, `config_files_in_parents()`,
    `optional_file()`.
    See also `-c` command line option below.

    `env_var_prefix` is a prefix to look for shell environment variables
    that override configuration values. The default is main script file name
    followed by underscore. For example, if you run a script in `script.py`
    then by default environment variables `SCRIPT_<config-element>=<value>`
    override values from `config_type` class, `override_defaults` mapping
    and configuration files.
    See also `-e` command line option below.

    `argv` is an optional list of command line arguments to be used instead
    of `sys.argv`.

    `arg_aliases` is a mapping `{short_option: long_option}`, where
    `short_option` must be a string of length one, and `long_option` can be
    a configuration element path. E.g. `arg_aliases=dict(b="foo.bar")`
    allows to use `-b` option as an alias of `--foo.bar` option to set the
    `config.foo.bar` value with command line arguments. `arg_aliases` override
    the built-in short options (see below).

    `set_global` allows to set up global application configuration object.
    The default value is `False`. See `set_global()` function for details.

    `log_level` sets logging level for the package. The default is `INFO`.
    To log more details set `log_level` to `DEBUG`, to reduce the amount of
    logging set `log_level` to `WARN` or `ERROR`. Set it to `NOTSET`to prevent
    setting up the logging system by the package: `log_level=logging.NOTSET`.
    See also `-l` command line option below.

    The function uses standard argparser module to parse command line
    arguments. Four options amend configuration process, others override
    configuration values obtained from other sources.
    `-h [ELEMENT]` option prints general help or description of a
    confuguration element.
    `-l LEVEL|FILE` option sets up logging level overriding `log_level`
    argument. If file path is provided instead, the `logging.fileConfig()`
    function is called.
    `-c FILE ...` option specifies which configuration files to read. The files
    are appended to the list given in `config_files` argument`.
    See `msrc.config_type.read_files.from_file` function for details.
    `-e PREFIX` option overrides a prefix for environment variables to look up.
    See `msrc.config_type.read_environ.from_environ function for details.

    To prevent looking up shell variables set `env_var_prefix` to `"-"`.
    To prevent reading from `sys.argv` set `argv` to `()`.
    To prevent setting up logging set `log_level` to `logging.NOTSET` value.

    If `set_global==True`, sets up the collected configuration as
    a global object for current process. The shared object is easily accessible
    in other modules with `get_global()` function.

    Returns the collected configuration."""

    if env_var_prefix is None and _main_script.name:
        env_var_prefix = _main_script.name.upper() + '_'
    try:
        config, unknown_args = _gather(
            config_type=config_type,
            override_defaults=override_defaults,
            config_files=config_files,
            config_files_dir=_main_script.dir,
            env_var_prefix=env_var_prefix,
            argv=argv,
            arg_aliases=arg_aliases,
            log_level=log_level
        )
    except RuntimeError as err:
        print(err)
        exit(1)
    if unknown_args:
        print("Unknown arguments: ", ' '.join(unknown_args))
        exit(1)
    if set_global:
        _SharedInstance.set_config(config)
    return config


def get_global(
    appconfig: Type[AppConfig],
    default: Optional[AppConfig] = None
) -> AppConfig:
    """Get global application configuration object.

    `appconfig` must be a type. `appconfig` argument ensures an object
    returned by the function is an instance of this type, or `ValueError`
    is raised.

    `default` object must be an instance of `appconfig` type. The function
    returns `default` if no global application configuration has been set up.

    Raises `RuntimeError` if no global application configuration has been
    set up by `set_global()` or `gather_config(set_global=True)` and
    the `default` is `None`.

    For example, if `AppConfig` is an appconfig schema where all elements
    have default values, then the following line never raises `RuntimeError`:
    ```python
    value = msrc.appconfig.get_global(AppConfig, AppConfig()).parameter
    ```
    In contrast this line:
    ```python
    value = msrc.appconfig.get_global(AppConfig).parameter
    ```
    raises `RuntimeError` if global configuration hasn't been set up.
    The following code never raises exceptions and can be used to safely
    check for a generic configuration:
    ```python
    cfg_none = object()
    cfg = msrc.appconfig.get_global(object, cfg_none)
    if cfg is cfg_none:
        ...
    ```"""

    shared = _SharedInstance.get_config()
    if shared is None:
        if default is None:
            raise RuntimeError(
                "Global application configuration hasn't been set up.")
        if isinstance(default, appconfig):
            return default
        raise ValueError(f"The 'default' argument is not of type {appconfig}.")
    if isinstance(shared, appconfig):
        return shared  # type: ignore  #
    raise ValueError("The global application configuration object "
                     f"is not of type {appconfig}.")


def set_global(appconfig: object) -> None:
    """Designates the `appconfig` as global application configuration object.

    The configuration becomes available with 'get_global()' throughout the
    application code base. Must be called only once per process.

    Raises `RuntimeError` if a configuration has already been set up.
    Meant to be used primarily behind `if __name__=="__main__"` guards.

    Raises `TypeError` if type of appconfig is not a valid configuration
    schema."""

    # the value type must be recognized by one of extensions
    _get_schema(type(appconfig))  # type: ignore
    _SharedInstance.set_config(appconfig)


def from_files(
    config_schema: Type[object],
    *files: Union[str, PathLike[str]]
) -> _ConfigMapping:
    """Collects configuration values from the specified files.

    Accepts files with the following extensions: .ini, .json, .yaml, .yml.
    Given a file with a different extension, tries to look up a file
    with the same name and one of recognized extensions.

    Each .json or .yaml/.yml  file must represent a JSON or YAML dictionary.
    The function ignores keys that are not in schema.
    A special key '_include' may contain a path or a list of paths to read.
    The function reads included files before processing the rest of the keys,
    i.e. values in the file may override values from included files.

    In case the same key is present in multiple files, the resulting dictionary
    contains a value from the last file."""

    schema = _Schema(config_schema)
    return _as_dict(itertools.chain.from_iterable(
        _from_file(schema, file) for file in files))


def from_environ(
    config_schema: Type[object],
    env_var_prefix: str = ""
) -> _ConfigMapping:
    """Collects configuration values from shell variables.

    For a configuration element <element_name> takes value from an environment
    variable <env_var_prefix><element_name> if one exists."""

    schema = _Schema(config_schema)
    return _as_dict(_from_environ(schema, env_var_prefix))


def from_argv(
    config_schema: Type[object],
    argv: Sequence[str],
    arg_aliases: Mapping[str, str] = {}
) -> _ConfigMapping:
    """Collects configuration values from command line arguments.

    The function employs standard module argparse to parse arguments.
    If a configuration element has underscores in its name the option may use
    either underscores or dashes.

    The optional `arg_aliases` argument allows to add short options to the
    command line interface. Aliases key must be a configuration element name,
    and corresponding value must be a single letter of the short option.

    Unrecognized `argv` elements, if any, are under `_unknown_args` key in
    the returned mapping."""

    schema = _Schema(config_schema)
    values, unknown_args = _from_argv(schema, argv, arg_aliases)
    result = _as_dict(values)
    if unknown_args:
        copy = dict(result)
        copy["_unknown_args"] = unknown_args
        result = copy
    return result


def from_dict(
    config_schema: Type[AppConfig],
    data: _ConfigMapping
) -> AppConfig:
    """Instantiates configuration object from a dictionary of values."""
    return _Schema(config_schema).from_dict(data)


def to_dict(
    instance: object,
    include_defaults: bool = False
) -> Dict[str, _ConfigValue]:
    """Extracts data from a configuration object.

    Returns a nested dictionary of configuration values.

    When `include_defaults` is False (the default value) the resulting
    dictionary doesn't contain elements with built-in default values."""
    schema = _Schema(type(instance))
    return schema.to_dict(instance, include_defaults=include_defaults)


def to_arg_dict(
    instance: object
) -> Dict[str, Union[str, Tuple[str, ...]]]:
    """Generates a dictionary of cmdline options to reproduce the instance."""
    return _to_arg_dict(to_dict(instance))


def to_argv(instance: object) -> List[str]:
    """Generates a flat list of cmdline options to reproduce the instance."""
    def generator() -> Generator[str, None, None]:
        for option, value in to_arg_dict(instance).items():
            yield option
            if isinstance(value, str):
                yield value
            else:
                yield from value
    return list(generator())
