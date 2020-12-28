import argparse
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple, Union, cast

from msrc.appconfig.schema import Schema, AtomicType, TupleType
from msrc.appconfig.schema import ConfigValue, ConfigMapping
from msrc.appconfig.logger import logger


def from_argv(
        schema: Schema[object],
        argv: Sequence[str],
        arg_aliases: Mapping[str, str] = {}
) -> Tuple[Tuple[ConfigValue, ...], List[str]]:
    """Reads configuration values from command line arguments."""
    parser = argparse.ArgumentParser(add_help=False)
    for name, e in schema.deep_items():
        pathname = ".".join(name)
        opts: List[str] = ["--"+pathname]
        if '_' in pathname:
            opts.append("--"+pathname.replace('_', '-'))
        for short_opt, long_opt in arg_aliases.items():
            if pathname == long_opt:
                if type(short_opt) is str and len(short_opt) == 1:
                    opts.append("-"+short_opt)
                else:
                    logger.warning(
                        "arg_aliases{%r: %r} ignored. "
                        "Short option is not a single char.",
                        short_opt, long_opt)
        if e.element_type == AtomicType.BOOL:
            parser.add_argument(*opts, help=e.help,
                                nargs='?',
                                const=True, default=argparse.SUPPRESS)
        elif not isinstance(e.element_type, TupleType):
            parser.add_argument(*opts, help=e.help,
                                default=argparse.SUPPRESS)
        elif e.element_type.length == 0:
            parser.add_argument(*opts, help=e.help,
                                nargs='*', default=argparse.SUPPRESS)
        else:
            parser.add_argument(*opts, help=e.help,
                                nargs=e.element_type.length,
                                default=argparse.SUPPRESS)
    result, unknown_args = parser.parse_known_args(argv)

    def result_generator():
        for name, element in schema.deep_items():
            pathname = ".".join(name)
            if hasattr(result, pathname):
                yield ConfigValue(name,
                                  element.parse(getattr(result, pathname)),
                                  ("argv", ))
    return tuple(result_generator()), unknown_args


def to_arg_dict(
    data: ConfigMapping
) -> Dict[str, Union[str, Tuple[str, ...]]]:
    """Returns dictionary of cmdline options for the deep config mapping."""

    def to_str(v: object) -> str:
        if isinstance(v, Enum):
            return v.name
        elif isinstance(v, float) and v < 0:
            # Prepend space or else argparse treats it as an option
            return " "+str(v)
        else:
            # Union[str, int, float, bool]
            return str(v)

    def iter_deep(
        prefix: str,
        data: ConfigMapping
    ) -> Iterable[Tuple[str, Union[str, Tuple[str, ...]]]]:
        for option in data.keys():
            value = data[option]
            if isinstance(value, Mapping):
                yield from iter_deep(
                    prefix+option+'.',
                    value)
            else:
                key = "--" + prefix + option
                if isinstance(value, str):
                    yield key, value
                else:
                    try:
                        yield key, tuple(
                            to_str(i) for i in cast(Iterable[object], value))
                    except TypeError:
                        yield key, to_str(value)

    return dict(iter_deep('', data))
