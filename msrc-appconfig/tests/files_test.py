from typing import Iterable
import pytest
from pathlib import Path

from msrc.appconfig import schema as s, read_files as f
from common import all_types_schema, all_values, all_yaml, all_json, En


def get_nested(d: dict, k: tuple):
    return get_nested(d[k[0]], k[1:]) if len(k) > 1 else d[k[0]]


def count_nested(d: dict):
    return sum(
        (count_nested(v) if isinstance(v, dict) else 1) for v in d.values()
    )


def check_dict_with_provenance(
    expected: dict,
    observed: Iterable[s.ConfigValue],
    provenance
):
    for observed_value in observed:
        expected_value = get_nested(expected, observed_value.name)
        assert observed_value.value == expected_value
        assert len(observed_value.provenance) == len(provenance) + 1
        for i, p in enumerate(provenance):
            assert observed_value.provenance[i+1].endswith(p)


def test_yaml_single(tmp_path):
    fn = "conf.yaml"
    (tmp_path/fn).write_text(all_yaml)
    loaded = list(f.from_file(all_types_schema, tmp_path/fn))
    assert len(loaded) == count_nested(all_values)
    check_dict_with_provenance(all_values, loaded, [fn])


def test_json_single(tmp_path):
    fn = "conf.json"
    (tmp_path/fn).write_text(all_json)
    loaded = list(f.from_file(all_types_schema, tmp_path/fn))
    assert len(loaded) == count_nested(all_values)
    check_dict_with_provenance(all_values, loaded, [fn])


def test_ini_single(tmp_path):
    fp = tmp_path / "conf.ini"
    fp.write_text("""[nested]
    booleans = false true
    options = Option2 Option1""")
    loaded = f.from_file(all_types_schema, fp.as_posix())
    check_dict_with_provenance(dict(nested=dict(
        booleans=(False, True),
        options=(En.Option2, En.Option1)
    )), loaded, ["conf.ini"])


def test_incl(tmp_path):
    (tmp_path/"sub").mkdir()
    (tmp_path/"sub"/"conf.yaml").write_text(all_yaml)
    (tmp_path/"inc.json").write_text(
        "{\"_include\":\"sub/conf.yaml\"}")
    loaded = list(f.from_file(all_types_schema, tmp_path/"inc.json"))
    assert len(loaded) == count_nested(all_values)
    check_dict_with_provenance(all_values, loaded, ["inc.json", "conf.yaml"])


def test_nested_incl(tmp_path):
    (tmp_path/"sub").mkdir()
    (tmp_path/"sub"/"conf.yaml").write_text("booleans: [true, false]")
    (tmp_path/"inc.yml").write_text("""
        int: 34
        nested:
            _include: sub/conf.yaml""")
    loaded = f.from_file(all_types_schema, tmp_path/"inc.yml")
    check_dict_with_provenance(
        dict(int=34, nested=dict(booleans=(True, False))),
        loaded,
        ["inc.yml", "conf.yaml"])


def test_multi_incl(tmp_path):
    (tmp_path/"sub").mkdir()
    (tmp_path/"sub"/"conf.yaml").write_text("integer: -1")
    (tmp_path/"sub"/"conf2.yaml").write_text("fractional: 3.1415926")
    (tmp_path/"inc.json").write_text(
        "{\"_include\":[\"sub/conf.yaml\",\"sub/conf2.yaml\"]}")
    loaded = s.as_dict(f.from_file(all_types_schema, tmp_path/"inc.json"))
    assert loaded == dict(integer=-1, fractional=3.1415926)


def test_raise_parse_errors(tmp_path):
    (tmp_path/"conf.yaml").write_text("""
integer: nonnumber
fractional: 3.1415926
""")
    with pytest.raises(ValueError):
        tuple(f.from_file(all_types_schema, tmp_path/"conf.yaml"))


def test_wrong_incl(tmp_path):
    (tmp_path/"sub").mkdir()
    (tmp_path/"sub"/"conf.yaml").write_text(all_yaml)
    (tmp_path/"inc.json").write_text(
        "{\"_include\":true}")
    with pytest.raises(TypeError,
                       match="must be a string or a list of strings."):
        tuple(f.from_file(all_types_schema, tmp_path/"inc.json"))


def test_wrong_multi_incl(tmp_path):
    (tmp_path/"inc.json").write_text(
        "{\"_include\":[true]}")
    with pytest.raises(TypeError,
                       match="must be a string or a list of strings."):
        tuple(f.from_file(all_types_schema, tmp_path/"inc.json"))


def test_nonexisting():
    with pytest.raises(FileNotFoundError):
        tuple(f.from_file(all_types_schema, "nonexisting.json"))


def test_unknown_ext(tmp_path):
    (tmp_path/"conf.y").write_text(all_yaml)
    with pytest.raises(ValueError):
        tuple(f.from_file(all_types_schema, tmp_path/"conf.y"))


def test_yaml_not_dict(tmp_path):
    (tmp_path/"conf.yaml").write_text("[1, 2, 3]")
    with pytest.raises(ValueError):
        tuple(f.from_file(all_types_schema, tmp_path/"conf.yaml"))


def test_json_not_dict(tmp_path):
    (tmp_path/"conf.json").write_text("123")
    with pytest.raises(ValueError):
        tuple(f.from_file(all_types_schema, tmp_path/"conf.json"))


def test_raise_yaml_format_error(tmp_path):
    (tmp_path/"conf.yaml").write_text("[1, 2, 3")
    with pytest.raises(Exception):
        tuple(f.from_file(all_types_schema, tmp_path/"conf.yaml"))


def test_raise_json_format_error(tmp_path):
    (tmp_path/"conf.json").write_text("[1, 2, 3")
    with pytest.raises(Exception):
        tuple(f.from_file(all_types_schema, tmp_path/"conf.json"))


def test_optional_file(tmp_path: Path):
    file_path = tmp_path/"conf.json"
    assert f.optional_file(file_path) == []
    file_path.write_text('')
    assert f.optional_file(file_path) == [file_path]


def test_config_files_in_parents(tmp_path: Path, mocker):
    file_name = "conf.json"
    base_path = tmp_path/"foo"/"bar"
    base_path.mkdir(parents=True)
    assert f.config_files_in_parents(file_name, base_path) == []
    p1 = tmp_path/file_name
    p1.write_text('')
    assert f.config_files_in_parents(file_name, base_path) == [p1]
    p2 = base_path/file_name
    p2.write_text('')
    assert f.config_files_in_parents(file_name, base_path) == [p1, p2]
    main_script = mocker.patch("msrc.appconfig.read_files.main_script")
    main_script.dir = base_path
    assert f.config_files_in_parents(file_name) == [p1, p2]


def test_script_config_file(tmp_path: Path, mocker):
    main_script = mocker.patch("msrc.appconfig.read_files.main_script")
    main_script.path = tmp_path/"script.py"
    assert f.script_config_file() == []
    file_path = tmp_path/"script.json"
    file_path.write_text('')
    assert f.script_config_file() == [file_path]
    assert f.script_config_file(".json") == [file_path]
    assert f.script_config_file(".yaml") == []
    with pytest.raises(ValueError):
        f.script_config_file(".txt")
    main_script.path = None
    with pytest.raises(RuntimeError):
        f.script_config_file()


def test_get_main_script(mocker):
    gsf = mocker.patch("msrc.appconfig.read_files.getsourcefile")
    # Ordinary script
    my_path = Path(__file__).resolve()
    assert my_path.stem == "files_test"
    gsf.return_value = str(my_path)
    assert f._get_main_script() == f.MainScriptConfig(
        my_path, my_path.parent, "files_test")
    # Module
    module_path = Path("/usr/pkg/__main__.py").resolve()
    gsf.return_value = str(module_path)
    assert f._get_main_script() == f.MainScriptConfig(
        module_path, Path.cwd(), "pkg")
    # None
    gsf.return_value = None
    assert f._get_main_script() == f.MainScriptConfig(
        None, Path.cwd(), '')


def test_get_main_script_nomain(mocker):
    mocker.patch.dict("sys.modules", __main__=None)
    assert f._get_main_script() == f.MainScriptConfig(
        None, Path.cwd(), '')
    # emulate interactive
    mocker.patch.dict("sys.modules", __main__="main")
    assert f._get_main_script() == f.MainScriptConfig(
        None, Path.cwd(), '')
