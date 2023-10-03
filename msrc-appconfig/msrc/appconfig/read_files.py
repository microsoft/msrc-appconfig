from __future__ import annotations
"""Configuration elements source: configuration files."""
import sys
import configparser
import json
from inspect import getsourcefile
from os import PathLike, fsdecode
from pathlib import Path
from typing import Callable, Generator, Iterable, List, Mapping, NamedTuple
from typing import Optional, Tuple, Union, cast

from ruamel.yaml import YAML

from msrc.appconfig.schema import Schema, DeepSchemaKey, ConfigValue
from msrc.appconfig.read_mapping import from_mapping
from msrc.appconfig.logger import logger


def read_json(path: str) -> Mapping[str, object]:
    with open(path, 'r') as json_file:
        loaded = json.load(json_file)
    if isinstance(loaded, Mapping):
        conf = cast(Mapping[str, object], loaded)
        assert all(isinstance(key, str) for key in conf.keys())
        return conf
    else:
        raise ValueError(f"The file doesn't represent a dictionary: {path}")


_yaml = YAML(typ='safe')


def read_yaml(path: str) -> Mapping[str, object]:
    with open(path, 'r') as yaml_file:
        loaded = _yaml.load(yaml_file)
    if isinstance(loaded, Mapping):
        conf = cast(Mapping[str, object], loaded)
        assert all(isinstance(key, str) for key in conf.keys())
        return conf
    else:
        raise ValueError(f"The file doesn't represent a dictionary: {path}")


def read_ini(path: str) -> Mapping[str, object]:
    config = configparser.ConfigParser()
    config.read(path)
    return config


config_readers: Mapping[str, Callable[[str], Mapping[str, object]]] = {
    ".ini": read_ini,
    ".json": read_json,
    ".yaml": read_yaml,
    ".yml": read_yaml
}


def from_file(
        schema: Schema[object],
        file_path: Union[str, PathLike[str]],
        provenance: Tuple[str, ...] = ("file",)
) -> Generator[ConfigValue, None, None]:
    """Reads configuration elements from a file.

    `schema` is an appconfig schema.

    `file_path` is the file to read. Must have one of supported file
    extensions or `ValueError` is raised.
    The file must exist or `FileNotFoundError` is raised.

    `provenance` is a prefix that identifies source of configuration
    elements.

    Yields a sequence of `ConfigValue` tuples.

    The configuration file content must represent a mapping.
    The function ignores entries of the mapping that do not match schema
    elements.

    A special entry `_include` may be used to reference other configuration
    files. The value of `_include` is a path or an array of paths of
    existing files. Non-absolute `_include` paths are resolved relative to
    the location of the current file.
    """

    config_path = Path(file_path).resolve()
    logger.debug("start processing config file %s", config_path)
    config_reader = config_readers.get(
        config_path.suffix.lower(),
        None
    )
    if config_reader is None:
        raise ValueError("The file must have an extension from "
                         f"{list(config_readers.keys())!r}: {file_path}.")
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file doesn't exist: {config_path}.")
    conf = config_reader(fsdecode(config_path))
    logger.debug("successfully loaded %s", config_path)
    provenance += (fsdecode(config_path),)
    base_path = config_path.parent

    def deep_include(
        schema: Schema[object],
        path: DeepSchemaKey,
        conf: Mapping[str, object]
    ) -> Generator[ConfigValue, None, None]:
        # deep first
        for key, el in schema.items():
            if (key in conf
                    and isinstance(el.element_type, Schema)):
                nested_path = path + (key, )
                if isinstance(conf[key], Mapping):
                    mapping = cast(Mapping[str, object], conf[key])
                    for config_value in deep_include(
                        el.element_type, nested_path, mapping
                    ):
                        yield ConfigValue(
                            nested_path + config_value.name,
                            config_value.value,
                            config_value.provenance
                        )
                else:
                    raise TypeError(
                        f"{'.'.join(nested_path)} must be a mapping.")
        # next at level
        include_key = "_include"
        if include_key in conf:
            include = conf[include_key]
            logger.debug("processing %r._include = %r", path, include)
            if isinstance(include, str):
                inc_path = Path(base_path, include)
                yield from from_file(schema, inc_path, provenance)
            elif isinstance(include, Iterable):
                include_list = cast(Iterable[object], include)
                # if it is an iterable
                for include_item in include_list:
                    if isinstance(include_item, str):
                        inc_path = Path(base_path, include_item)
                        yield from from_file(schema, inc_path, provenance)
                    else:
                        nested_key = '.'.join(path + (include_key,))
                        raise TypeError(
                            nested_key
                            + " must be a string or a list of strings.")
            else:
                nested_key = '.'.join(path + (include_key,))
                raise TypeError(
                    nested_key + " must be a string or a list of strings.")
    yield from deep_include(schema, (), conf)
    yield from from_mapping(schema, conf, provenance)
    logger.debug("end processing conf file %s", config_path)


def optional_file(file_path: Union[str, PathLike[str]]) -> List[Path]:
    """Returns a list with the file `Path` if the file exists.

    Returns an empty list if `file_path` doesn't reference an existing file.

    Useful to build a list of configuration files, e.g.:
    ```python
    cfg = gather_config(
        AppConfig,
        config_files=optional_file('config.yml')
    )
    ```
    """

    probe = Path(file_path)
    if probe.is_file():
        return [probe]
    else:
        return []


class MainScriptConfig(NamedTuple):
    path: Optional[Path]
    dir: Path
    name: str


def _get_main_script() -> MainScriptConfig:
    main_module = sys.modules.get('__main__', None)
    if main_module is None:
        return MainScriptConfig(None, Path.cwd(), '')
    try:
        main_script_path: Optional[str] = getsourcefile(main_module)
    except TypeError:
        main_script_path = None
    if main_script_path is None:
        return MainScriptConfig(None, Path.cwd(), '')
    script_path = Path(main_script_path).resolve()
    script_name = script_path.stem
    script_dir = script_path.parent
    if script_name == "__main__":
        script_name = script_path.parent.stem
        script_dir = Path.cwd()
    return MainScriptConfig(
        path=script_path,
        dir=script_dir,
        name=script_name
    )


main_script: MainScriptConfig = _get_main_script()


def script_config_file(ext: Optional[str] = None) -> List[Path]:
    """Returns a list with the default script configuration file.

    `ext` is an optional configuration file extension. Must be one of
    supported extensions. If `ext` not specified, the function tries
    all supported extensions.

    A default configuration file has a name of a main script file or
    a package name if a package is being run. The function lookes for
    the file in the main script directory, or in current directory if
    a package is being run.

    Useful to build a list of configuration files, e.g.:
    ```python
    cfg = gather_config(
        AppConfig,
        config_files=script_config_file('.yml')
    )
    ```
    """

    if main_script.path is None:
        raise RuntimeError("Couldn't identify main script path."
                           " Use optional_path() instead.")
    if ext is None:
        for ext in config_readers.keys():
            probe = main_script.path.with_suffix(ext)
            if probe.is_file():
                return [probe]
        return []
    else:
        if ext not in config_readers:
            raise ValueError("configuration file extension must be one of "
                             f"{tuple(config_readers.keys())!r}.")
        return optional_file(main_script.path.with_suffix(ext))


def config_files_in_parents(
    file_name: str,
    base_path: Union[None, str, Path] = None
) -> List[Path]:
    """Returns a list of configuration files in parent directories.

    `file_name` must be a file name with one of supported extensions.

    `base_path` is an optional final path. The default is main script
    directory, or current directory if a package is being run.

    Returns a list of all files found along the `base_path` starting
    from the root.

    Useful to build a list of configuration files, e.g.:
    ```python
    cfg = gather_config(
        AppConfig,
        config_files=config_files_in_parents('config.yml')
    )
    ```
    """
    if base_path is None:
        base_path = main_script.dir
    else:
        base_path = Path(base_path)
    files = optional_file(Path(base_path, file_name))
    for parent in base_path.parents:
        files = optional_file(Path(parent, file_name)) + files
    return files
