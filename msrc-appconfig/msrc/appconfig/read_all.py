from __future__ import annotations
"""Orchestrates configuration from files, shell and command line args."""
import typing as ty
import argparse
from os import PathLike
import pathlib
import logging
import logging.config
import itertools

from msrc.appconfig.logger import logger
import msrc.appconfig.schema as _s
from msrc.appconfig.read_files import from_file as _from_file
from msrc.appconfig.read_mapping import from_mapping as _from_mapping
from msrc.appconfig.read_environ import from_environ as _from_environ
from msrc.appconfig.read_argv import from_argv as _from_argv


AppConfig = ty.TypeVar('AppConfig')


def gather(
    config_type: ty.Type[AppConfig],
    override_defaults: _s.ConfigMapping = {},
    config_files: ty.Sequence[ty.Union[str, PathLike[str]]] = [],
    config_files_dir: ty.Union[str, PathLike[str], None] = None,
    env_var_prefix: ty.Optional[str] = None,
    argv: ty.Optional[ty.Sequence[str]] = None,
    arg_aliases: ty.Mapping[str, str] = {},
    log_level: int = logging.INFO
) -> ty.Tuple[AppConfig, ty.List[str]]:
    """Gathers configuration values from files, shell and command line.

    The function is a main tool to build application configuration object.

    `config_type` is the only required argument. Must be is a class object.
    The `config_type` can be a `typing.NamedTuple` or a class supported by
    one of the package extensions.

    `override_defaults` is a mapping that allows to override the defaults
    in the `config_type` class.

    `config_files` is a sequence of configuration file paths, strings
    or `PathLike` objects. The function reads the files in sequence.
    See also `-c` command line option below.

    `config_files_dir` is a base directory to resolve relative paths
    in `config_files` list. The default is current working directory.

    `env_var_prefix` is a prefix to look for shell environment variables
    that override configuration values. If not set, or is a single dash `-`,
    the function will not look at environment. See also `-e` command line
    option below.

    `argv` is an optional list of command line arguments to be used instead
    of `sys.argv`.

    `arg_aliases` is a mapping `{short_option: long_option}`, where
    `short_option` must be a string of length one, and `long_option` can be
    a configuration element path. E.g. `arg_aliases=dict(b="foo.bar")`
    allows to use `-b` option as an alias of `--foo.bar` option to set the
    `config.foo.bar` value with command line arguments. `arg_aliases` override
    the built-in short options (see below).

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

    Returns a tuple of an instance of `config_type` and a list of unknown
    command line arguments.

    Raises `RuntimeError` if there is not enough information to create
    an instance of `config_type`."""

    schema = _s.Schema(config_type)
    # 1. parse base arguments, set up logger
    arg_parser = argparse.ArgumentParser(add_help=False)
    help_options = (([] if ("h" in arg_aliases) else ["-h"])
                    + ([] if "help" in schema else ["--help"]))
    if help_options:
        arg_parser.add_argument(
            *help_options, nargs='?', const='h',
            metavar="OPTION", dest="_hlp",
            help="Prints this help message "
            "and optionally a description of the option.")
    loghelp = "Either logging level " \
        "or a path to a logging configuration file."
    if log_level > logging.NOTSET:
        loghelp += f" The default is {logging.getLevelName(log_level)}."
    if "l" not in arg_aliases:
        arg_parser.add_argument(
            '-l', help=loghelp, metavar='LEVEL|FILE', dest="_log")
    if "c" not in arg_aliases:
        arg_parser.add_argument(
            '-c', nargs='+', metavar='CONF_FILE', default=[], dest="_cfg",
            help="Additional configuration files. Allowed formats are JSON "
            "or YAML.")
    if "e" not in arg_aliases:
        arg_parser.add_argument(
            '-e', metavar='PREFIX', default=env_var_prefix, dest="_env",
            help=("Prefix for shell variables to look at. If environment "
                  "contains <PREFIX>_<ELEMENT_NAME>=VALUE "
                  "the VALUE overrides corresponding configuration element."
                  " The default prefix is %(default)s. A prefix of sole dash"
                  " disables the environment lookup."))
    args, config_args = arg_parser.parse_known_args(argv)
    if getattr(args, "_hlp", False):

        def option_line(keys: _s.DeepSchemaKey, el: _s.Element) -> str:
            tstr = ' ' + el.type_str()
            option = '.'.join(keys)
            short = [
                '-' + short_opt + tstr
                for short_opt, long_opt in arg_aliases.items()
                if long_opt == option]
            dashed = (["--" + option.replace('_', '-') + tstr]
                      if '_' in option else [])
            h = "  (*)" if el.help else ''
            line = short + ["--" + option + tstr] + dashed
            return ", ".join(line) + h

        if args._hlp != "h":
            khelp = tuple(args._hlp.replace('-', '_').split('.'))
            el = next((el for k, el in schema.deep_items() if k == khelp),
                      None)
            if el:
                print(option_line(khelp, el))
                if el.help:
                    print(el.help)
                else:
                    print("(No more help for the option)")
            else:
                print("No such option:", args._hlp)
            print()
        arg_parser.print_help()
        print("Additionally, you may specify the following options. Use "
              "'--help OPTION_NO_DASHES' to get help on an option marked (*).")
        for k, e in schema.deep_items():
            print(option_line(k, e))
        arg_parser.exit()
    if getattr(args, "_log", False):
        v = args._log
        level = v.upper()
        if (level in vars(logging)
                and type(getattr(logging, level)) is int):
            log_level = getattr(logging, level)
        elif pathlib.Path(v).is_file():
            log_level = logging.NOTSET
            logging.config.fileConfig(v)
            logger.info("configure logging from %s", v)
        else:
            raise ValueError(loghelp)
    if log_level > logging.NOTSET:
        if logger.hasHandlers():
            # The logging system has already been set up, just:
            logger.setLevel(log_level)
        else:
            logging.basicConfig(level=log_level)
        logger.info("logging level set to %s.",
                    logging.getLevelName(log_level))
    # 2. enumerate configuration sources

    def log_discovered(
        values: ty.Iterable[_s.ConfigValue]
    ) -> ty.Generator[_s.ConfigValue, None, None]:
        for v in values:
            logger.debug("discovered %s", v)
            yield v
    # 2.0 defaults
    override_values = tuple(log_discovered(_from_mapping(
        schema, override_defaults, ("overidden defaults",))))
    # 2.1 files
    file_values: ty.Tuple[_s.ConfigValue, ...] = ()
    if config_files:
        if config_files_dir is None:
            config_files_dir = pathlib.Path.cwd()
        file_values = tuple(log_discovered(itertools.chain.from_iterable(
            _from_file(schema, pathlib.Path(config_files_dir, file))
            for file in config_files
        )))
    if getattr(args, "_cfg", False):
        file_values = tuple(log_discovered(itertools.chain.from_iterable(
            _from_file(schema, pathlib.Path(file).resolve())
            for file in args._cfg
        )))
    # 2.2 environ
    if getattr(args, "_env", False):
        env_var_prefix = args._env
    environ_values: ty.Tuple[_s.ConfigValue, ...] = ()
    if env_var_prefix is not None and env_var_prefix != '-':
        environ_values = tuple(_from_environ(
            schema, env_var_prefix))
    # 2.3 argv
    arg_values, unknown_args = _from_argv(
        schema, config_args, arg_aliases)
    arg_values = tuple(log_discovered(arg_values))
    # summary
    discovered: ty.Dict[_s.DeepSchemaKey, _s.ConfigValue] = dict(
        (cv.name, cv)
        for cv in override_values + file_values + environ_values + arg_values
    )
    for v in discovered.values():
        logger.info("final %s", v)
    # check required fileds
    missing_fileds: ty.Set[str] = set()
    for name, el in schema.deep_items():
        if not el.has_default:
            if name not in discovered.keys():
                missing_fileds.add(".".join(name))
    if missing_fileds:
        raise RuntimeError(
            "no values discovered for the following elements: "
            + ', '.join(missing_fileds))
    # can now instantiate the schema
    return schema.from_dict(_s.as_dict(discovered.values())), unknown_args
