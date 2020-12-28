import typing as ty
from enum import Enum
import math
import msrc.appconfig.schema as s


class En(Enum):
    Option1 = 1
    Option2 = 2


class Nested(ty.NamedTuple):
    booleans: ty.Tuple[bool, bool]
    options: ty.Tuple[En, En] = (En.Option1, En.Option2)


setattr(Nested, "_field_help", dict(
        booleans="A pair of Boolean values."
        ))


class AllTypes(ty.NamedTuple):
    string: str
    integer: int
    fractional: float
    boolean: bool
    option: En
    strings: ty.Tuple[str, str]
    integers: ty.Tuple[int, int]
    fractionals: ty.Tuple[float, float]
    nested: Nested


all_types_schema = s.Schema(AllTypes)

all_values = dict(
    string="string",
    integer=-1,
    fractional=3.1415926,
    boolean=True,
    option=En.Option2,
    strings=("one", "two"),
    integers=(1, 2),
    fractionals=(-math.inf, math.inf),
    nested=dict(
        booleans=(True, False),
        options=(En.Option2, En.Option1)
    ),
)

all_types_instance = AllTypes(
    nested=Nested(**all_values["nested"]),  # type: ignore
    **dict(i for i in all_values.items() if i[0] != "nested"))  # type:ignore

all_yaml = """
string: "string"
integer: -1
fractional: 3.1415926
boolean: true
option: Option2
strings: ["one", "two"]
integers: [1, 2]
fractionals: [-Infinity, Infinity]
nested:
  booleans: [true, false]
  options: [Option2, Option1]
"""

all_json = """{
"string": "string",
"integer": -1,
"fractional": 3.1415926,
"boolean": true,
"option": "Option2",
"strings": ["one", "two"],
"integers": [1, 2],
"fractionals": ["-Infinity", "Infinity"],
"nested": {
    "booleans": [true, false],
    "options": ["Option2", "Option1"]
    }
}"""

all_args = [
    "--string", "string",
    "--integer", "-1",
    "--fractional", "3.1415926",
    "--boolean", "true",
    "--option", "Option2",
    "--strings", "one", "two",
    "--integers", "1", "2",
    "--fractionals", " -Infinity", "Infinity",
    "--nested.booleans", "true", "false",
    "--nested.options", "Option2", "Option1"
]

all_env = {
    "PRE_string": "string",
    "PRE_integer": "-1",
    "PRE_fractional": "3.1415926",
    "PRE_boolean": "true",
    "PRE_option": "Option2",
    "PRE_strings": "one two",
    "PRE_integers": "1 2",
    "PRE_fractionals": "-Infinity Infinity",
    "PRE_nested.booleans": "true false",
    "PRE_nested.options": "Option2 Option1"
}


def mk_class(*fields):
    return ty.NamedTuple("_", fields)


def mk_schema(*fields):
    return s.Schema(mk_class(*fields))


class WithDefaults(ty.NamedTuple):
    a: int = 999


class WithNestedDefaults(ty.NamedTuple):
    nested: WithDefaults = WithDefaults()
