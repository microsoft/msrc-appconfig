import logging

import pytest

import msrc.appconfig.read_all

from common import AllTypes, WithDefaults
from common import all_json, all_types_instance, all_values, all_args
from common import all_env, mk_class

# Normal usage
# ============


def test_builtin_defaults():
    "No data required when all values have defaults."
    config, _ = msrc.appconfig.read_all.gather(WithDefaults)
    assert (999,) == config
    with pytest.raises(RuntimeError):
        msrc.appconfig.read_all.gather(AllTypes)


def test_override_defaults():
    "All values can come from `override_defaults`."
    loaded, _ = msrc.appconfig.read_all.gather(
        AllTypes, override_defaults=all_values)
    assert loaded == all_types_instance


def test_override_builtin_defaults():
    "`override_defaults` override built-in defaults."
    config, _ = msrc.appconfig.read_all.gather(
        WithDefaults,
        override_defaults=dict(a=1))
    assert (1,) == config


def test_config_file(tmp_path):
    "All values come from a configuration file in `config_files`."
    (tmp_path/"conf.json").write_text(all_json)
    path = (tmp_path/"conf.json").as_posix()
    config, _ = msrc.appconfig.read_all.gather(AllTypes, config_files=[path])
    assert all_types_instance == config


def test_config_file_argv(tmp_path):
    "All values come from a configuration file in `argv`."
    (tmp_path/"conf.json").write_text(all_json)
    path = (tmp_path/"conf.json").as_posix()
    config, _ = msrc.appconfig.read_all.gather(AllTypes, argv=["-c", path])
    assert all_types_instance == config


def test_config_file_sysargv(tmp_path, mocker):
    "All values come from a configuration file in `sys.argv`."
    (tmp_path/"conf.json").write_text(all_json)
    path = (tmp_path/"conf.json").as_posix()
    mocker.patch("sys.argv", new=["script", "-c", path])
    config, _ = msrc.appconfig.read_all.gather(AllTypes)
    assert all_types_instance == config


def test_config_file_combines_argv(mocker):
    "Option in `argv` adds to paths in `config_files`."
    from_file = mocker.patch("msrc.appconfig.read_all._from_file")
    config, _ = msrc.appconfig.read_all.gather(
        WithDefaults,
        config_files=["a"],
        argv=["-c", "b"])
    assert from_file.call_count == 2
    # assert call_arg_list


def test_argv_overrides_sysargv(tmp_path, mocker):
    "Option in `argv` prevents looking at `sys.argv`."
    (tmp_path/"conf.json").write_text(all_json)
    path = (tmp_path/"conf.json").as_posix()
    mocker.patch("sys.argv", new=["script", "-c", "nofile.yml"])
    config, _ = msrc.appconfig.read_all.gather(AllTypes, argv=["-c", path])
    assert all_types_instance == config


def test_config_file_overrides_builtin(tmp_path):
    "Values from `config_files` override built-in defaults."
    (tmp_path/"conf.yaml").write_text("a: 2")
    path = (tmp_path/"conf.yaml").as_posix()
    config, _ = msrc.appconfig.read_all.gather(
        WithDefaults, config_files=[path])
    assert (2,) == config


def test_config_file_overrides_defaults(tmp_path):
    "Values from `config_files` override built-in defaults."
    (tmp_path/"conf.yaml").write_text("a: 2")
    path = (tmp_path/"conf.yaml").as_posix()
    config, _ = msrc.appconfig.read_all.gather(
        WithDefaults,
        override_defaults=dict(a=1),
        config_files=[path])
    assert (2,) == config


def test_env(mocker):
    "All values come from shell environment."
    mocker.patch("os.environ", new=all_env)
    config, _ = msrc.appconfig.read_all.gather(AllTypes, env_var_prefix="PRE_")
    assert all_types_instance == config


def test_env_overrides_config_file(tmp_path, mocker):
    "Values from env override config files."
    (tmp_path/"conf.yaml").write_text("a: 2")
    path = (tmp_path/"conf.yaml").as_posix()
    mocker.patch("sys.argv", new=["script", "-c", path])
    mocker.patch("os.environ", new=dict(_a="3"))
    config, _ = msrc.appconfig.read_all.gather(
        WithDefaults,
        override_defaults=dict(a=1),
        env_var_prefix="_")
    assert (3,) == config


def test_argv():
    "All values come from argv."
    config, _ = msrc.appconfig.read_all.gather(AllTypes, argv=all_args)
    assert all_types_instance == config


def test_arg_overrides_env(tmp_path, mocker):
    "Values from env override config files."
    (tmp_path/"conf.yaml").write_text("a: 2")
    path = (tmp_path/"conf.yaml").as_posix()
    mocker.patch("sys.argv", new=["script", "-c", path, "--a", "4"])
    mocker.patch("os.environ", new=dict(_a="3"))
    config, _ = msrc.appconfig.read_all.gather(
        WithDefaults,
        override_defaults=dict(a=1),
        env_var_prefix="_")
    assert (4,) == config

# Exceptions
# ==========


def test_gather_invalid_schema():
    "First parameter must be a class."
    with pytest.raises(TypeError):
        msrc.appconfig.read_all.gather(WithDefaults())  # type: ignore
    with pytest.raises(ValueError):
        msrc.appconfig.read_all.gather(dict)


def test_gather_invalid_defaults():
    "Data in `override_defailts` must be parseable."
    with pytest.raises(ValueError):
        msrc.appconfig.read_all.gather(
            AllTypes,
            override_defaults=dict(nested=0))


def test_config_file_not_found():
    "Config file must exist."
    with pytest.raises(FileNotFoundError):
        msrc.appconfig.read_all.gather(AllTypes, config_files=["nofile.yml"])

# Help
# =====


def test_help(capsys, mocker):
    mocker.patch("sys.argv", new=["script", "-h", "--a", "4"])
    with pytest.raises(SystemExit):
        msrc.appconfig.read_all.gather(AllTypes, arg_aliases=dict(o="option"))
    captured = capsys.readouterr()
    assert captured.err == ''
    expected = [
        "--string STR",
        "--integer INT",
        "--fractional FLOAT",
        "--boolean [BOOL]",
        "-o En, --option En",
        "--strings STR STR",
        "--integers INT INT",
        "--fractionals FLOAT FLOAT",
        "--nested.booleans BOOL BOOL  (*)",
        "--nested.options En En"
    ]
    actual = captured.out.strip('\r\n').splitlines()
    assert actual[-len(expected):] == expected


def test_help_arg(capsys, mocker):
    mocker.patch("sys.argv", new=["script", "-h", "nested.booleans"])
    with pytest.raises(SystemExit):
        msrc.appconfig.read_all.gather(AllTypes)
    captured = capsys.readouterr()
    assert captured.err == ''
    actual = captured.out.strip('\r\n').splitlines()
    assert actual[1] == AllTypes.__annotations__[
        "nested"]._field_help["booleans"]


def test_nohelp_arg(capsys, mocker):
    mocker.patch("sys.argv", new=["script", "-h", "string"])
    with pytest.raises(SystemExit):
        msrc.appconfig.read_all.gather(AllTypes)
    captured = capsys.readouterr()
    assert captured.err == ''
    actual = captured.out.strip('\r\n').splitlines()
    assert actual[0] == "--string STR"
    assert actual[1].startswith('(')


def test_help_noarg(capsys, mocker):
    mocker.patch("sys.argv", new=["script", "-h", "nested.b"])
    with pytest.raises(SystemExit):
        msrc.appconfig.read_all.gather(AllTypes)
    captured = capsys.readouterr()
    assert captured.err == ''
    actual = captured.out.strip('\r\n').splitlines()
    assert actual[0].index("nested.b") > 0


def test_no_help(mocker):
    schema = mk_class(("help", str), ("hero", bool))
    mocker.patch("sys.argv", new=["script", "-h", "--help", "test"])
    actual, _ = msrc.appconfig.read_all.gather(
        schema, arg_aliases=dict(h="hero"))
    assert actual.hero
    assert actual.help == "test"

# Logging
# ========


def test_log_default(mocker):
    """By default logging set to INFO using basicConfig."""
    mock = mocker.patch("logging.basicConfig")
    mocker.patch("msrc.appconfig.read_all.logger.hasHandlers",
                 return_value=False)
    c, _ = msrc.appconfig.read_all.gather(
        mk_class(("a", int)), argv=["--a", "34"])
    mock.assert_called_once_with(level=logging.INFO)
    assert c.a == 34


def test_log_preconfigured(mocker):
    """If logging is set up just set level for the package logger."""
    mock = mocker.patch("msrc.appconfig.read_all.logger.setLevel")
    mocker.patch("msrc.appconfig.read_all.logger.hasHandlers",
                 return_value=True)
    c, _ = msrc.appconfig.read_all.gather(
        mk_class(("a", int)), argv=["--a", "34"])
    mock.assert_called_once_with(logging.INFO)
    assert c.a == 34


def test_log_override_log_level(mocker):
    """By default logging set to INFO using basicConfig."""
    mock = mocker.patch("logging.basicConfig")
    mocker.patch("msrc.appconfig.read_all.logger.hasHandlers",
                 return_value=False)
    c, _ = msrc.appconfig.read_all.gather(
        mk_class(("a", int)), argv=["--a", "34"], log_level=logging.WARN)
    mock.assert_called_once_with(level=logging.WARN)
    assert c.a == 34


def test_log_override_argv(mocker):
    """By default logging set to INFO using basicConfig."""
    mock = mocker.patch("logging.basicConfig")
    mocker.patch("msrc.appconfig.read_all.logger.hasHandlers",
                 return_value=False)
    c, _ = msrc.appconfig.read_all.gather(
        mk_class(("a", int)), argv=["--a", "34", "-l", "warn"])
    mock.assert_called_once_with(level=logging.WARN)
    assert c.a == 34


def test_log_file_config(tmp_path, mocker):
    (tmp_path/"conf.json").write_text(all_json)
    path = (tmp_path/"conf.json").as_posix()
    mock = mocker.patch("logging.config.fileConfig")
    c, _ = msrc.appconfig.read_all.gather(
        mk_class(("a", int)),
        argv=["--a", "37", "-l", path])
    mock.assert_called_once_with(path)
    assert c.a == 37


def test_log_invalid(mocker):
    with pytest.raises(ValueError):
        msrc.appconfig.read_all.gather(
            mk_class(("a", int)),
            argv=["--a", "38", "-l", "information"])
