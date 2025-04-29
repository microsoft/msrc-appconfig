"""Defines abstract Schema which holds attributes of configuration elements.

An Element has a 'name', 'type', optional description ('help')
and flags 'has_default' and 'is_secret'.
A type is either an atomic type, a enum, or a homogenious tuple of these.
A tuple can either have fixed length, or be any length, including zero.

A plugin module must define function 'inspect' which examines specific schema
and returns abstract Schema.
"""
from typing import Any, Mapping, Tuple, List, Type, Dict, Iterable, Generator
from typing import Match, Union, NamedTuple, Optional, Generic, TypeVar, cast
from typing_extensions import get_origin, get_args
from types import ModuleType
from enum import Enum, IntEnum, auto
import re
from functools import lru_cache
import numbers

from msrc.appconfig.logger import logger
from msrc.appconfig.decl import get_installed_decl

# Matches an element of a space delimited list.
# It is either a string without spaces, or a string in double quotes.
# The quoted string may contain escaped double quote '\"'
# and escaped bacl slash '\\'.
_re_e = re.compile("(?:^|\\s+)(\"((?:\\\\[\"\\\\]|[^\"\\\\])*)\"|\\S+)")
# An escape sequence: '\"' or '\\'
_re_q = re.compile("\\\\([\"\\\\])")


def str_to_tuple(value: str) -> Tuple[str, ...]:
    def match_to_str(
        match: Match[str]
    ) -> str:
        quoted = match.group(2)
        if quoted is not None:
            return _re_q.sub("\\1", quoted)
        else:
            return match.group(1)
    return tuple(map(match_to_str, _re_e.finditer(value)))


# Supported value types for configuration element
ConfigValueType = Union[
    str, Tuple[str, ...], List[str],
    int, Tuple[int, ...], List[int],
    float, Tuple[float, ...], List[float],
    bool, Tuple[bool, ...], List[bool],
    Enum, Tuple[Enum, ...], List[Enum],
]


DeepSchemaKey = Tuple[str, ...]


class ConfigValue(NamedTuple):
    """Individual value from one of configuration sources."""
    name: DeepSchemaKey
    value: ConfigValueType
    provenance: Tuple[str, ...]

    def __str__(self) -> str:
        n = ".".join(self.name)
        p = " > ".join(self.provenance)
        return f"{n} = {self.value!r} from {p}"


ConfigMapping = Mapping[str, "ConfigMappingValueType"]
ConfigMappingValueType = Union[ConfigValueType, ConfigMapping]
ConfigDict = Dict[str, "ConfigDictValueType"]
ConfigDictValueType = Union[ConfigValueType, ConfigDict]


def _deep_set_value(
    store: ConfigDict,
    name: DeepSchemaKey,
    value: ConfigValueType
) -> None:
    n0 = name[0]
    if len(name) > 1:
        if n0 not in store:
            store[n0] = {}
        nested = store[n0]
        assert isinstance(nested, dict)
        _deep_set_value(nested, name[1:], value)
    else:
        store[n0] = value


def as_dict(
    source: Iterable[ConfigValue]
) -> ConfigMapping:
    store: ConfigDict = dict()
    for config_value in source:
        _deep_set_value(
            store,
            config_value.name,
            config_value.value)
    return store


# Internal representation after retrospection
# ===========================================


class AtomicType(IntEnum):
    """Supported atomic types for configuration elements."""
    STR = auto()
    INT = auto()
    FLOAT = auto()
    BOOL = auto()


class TupleType:
    """Supported array types for configuration elements.

    All array elements must be of the same atomic type or Enum.
    Array length can by fixed (e.g. a pair) or unbounded.
    By default, an array is a Python tuple, but can also be a Python list.
    """

    def __init__(self,
                 baseType: Union[AtomicType, Type[Enum]],
                 length: int,
                 parse_to_list: bool = False
                 ):
        self.length: int = int(length)
        if self.length < 0:
            raise ValueError(
                "Tuple length must be 0 (unrestricted) or a positive integer.")
        assert isinstance(baseType, AtomicType) or issubclass(baseType, Enum)
        self.baseType = baseType
        self.parse_to_list = parse_to_list

    def __repr__(self) -> str:
        b = self.baseType
        s = b.name if isinstance(b, Enum) else str(b)
        if self.parse_to_list:
            return "Tuple/List[%s]" % s
        if self.length == 0:
            return "Tuple[%s, ...]" % s
        else:
            g = ", ".join((s,)*self.length)
            return "Tuple[%s]" % g


ElementType = Union[AtomicType, Type[Enum], TupleType, "Schema[object]"]


def _validate_element_type(element_type: object) -> None:
    if isinstance(element_type, type) and issubclass(element_type, Enum):
        return
    if isinstance(element_type, (AtomicType, TupleType, Schema)):
        return
    raise TypeError(
        f"Invalid ConfigValueType {element_type!r}, must be an AtomicType, "
        "a TupleType, a Enum or a Schema.")


class Element:
    """Describes one configuration element"""

    def __init__(
        self,
        element_type: ElementType,
        has_default: bool = False,
        default_value: Union[ConfigValueType, object] = 0,
        help: Optional[str] = None,
        is_secret: bool = False
    ):
        self.help: Optional[str] = help
        _validate_element_type(element_type)
        self.element_type: ElementType = element_type
        self.is_secret: bool = is_secret
        self.has_default: bool = has_default
        if has_default and not self.type_check(default_value):
            raise ValueError("Element default value %r must have type %r."
                             % (default_value, element_type))
        if isinstance(element_type, Schema) and has_default:
            # substitute schema elements taking defaults from the default value
            for name in element_type.keys():
                i = element_type[name]
                element_type[name] = Element(
                    i.element_type,
                    True,
                    getattr(default_value, name),
                    i.help,
                    i.is_secret)
        self.default_value = default_value

    def type_check(self, value: object) -> bool:
        """Checks type of the value against element type."""
        def type_check_atomic(
            element_type: Union[AtomicType, Type[Enum]],
            value: object
        ) -> bool:
            if isinstance(element_type, AtomicType):
                if element_type == AtomicType.STR:
                    return isinstance(value, str)
                if element_type == AtomicType.INT:
                    return isinstance(value, numbers.Integral)
                if element_type == AtomicType.FLOAT:
                    return isinstance(value, numbers.Real)
                assert element_type == AtomicType.BOOL
                return isinstance(value, bool)
            return isinstance(value, element_type)  # Enum

        def type_check_all_atomic(
            element_type: Union[AtomicType, Type[Enum]],
            value: Iterable[object]
        ) -> bool:
            return all(type_check_atomic(element_type, item) for item in value)

        element_type = self.element_type
        if isinstance(element_type, Schema):
            return element_type.type_check(value)
        if isinstance(element_type, TupleType):
            if (isinstance(value, tuple)):
                t_value = cast(Tuple[object], value)
                t_length = element_type.length
                if t_length > 0 and t_length != len(t_value):
                    return False
                return type_check_all_atomic(element_type.baseType, t_value)
            if (isinstance(value, list)):
                if not element_type.parse_to_list or element_type.length > 0:
                    return False
                return type_check_all_atomic(element_type.baseType,
                                             cast(List[object], value))
            return False
        return type_check_atomic(element_type, value)

    def parse(self, value: object) -> ConfigValueType:
        """Converts a value to the element_type.

        Raises ValueError if the convertion cannot be done.
        Raises TypeError if the element base type is a schema.
        Raises TypeError in attempt to convert improper type
        to an int or a float.
        """
        def parseAtomic(
            t: AtomicType,
            value: object
        ) -> Union[str, int, float, bool]:
            if t == AtomicType.STR:
                return str(value)
            if t == AtomicType.INT:
                return int(value)  # type: ignore
            if t == AtomicType.FLOAT:
                return float(value)  # type: ignore
            assert t == AtomicType.BOOL
            if isinstance(value, str):
                u = value.lower()
                if u.startswith(('t', 'y')):
                    return True
                if u.startswith(('f', 'n')):
                    return False
                else:
                    raise ValueError(
                        "Cannot parse the string as a bool value: "
                        + value)
            else:
                return bool(value)

        def parseEnum(t: Type[Enum], value: object) -> Enum:
            strvalue = str(value)
            if isinstance(value, t):
                return value
            for e in t:  # first check keys
                if strvalue == e.name:
                    return e
            for e in t:  # next check values
                if strvalue == str(e.value):
                    return e
            raise ValueError(
                "Cannot parse the string as a value of {0}: {1!r}"
                .format(t.__name__, strvalue))

        def parseTuple(
            t: TupleType,
            value: object
        ) -> ConfigValueType:
            values: Tuple[object, ...]
            if isinstance(value, str):
                values = str_to_tuple(value)
            else:
                try:
                    values = tuple(
                        item for item in cast(Iterable[object], value))
                except TypeError:
                    # value is not iterable
                    values = (value,)
            if t.length > 0 and len(values) != t.length:
                raise ValueError(
                    "Expect a tuple of {0} values, but given {1}."
                    .format(t.length, len(values)))

            def parseBase(v: object) -> object:
                if isinstance(t.baseType, AtomicType):
                    return parseAtomic(t.baseType, v)
                else:
                    return parseEnum(t.baseType, v)
            generator = map(parseBase, values)
            if t.parse_to_list:
                return cast(ConfigValueType, list(generator))
            return cast(ConfigValueType, tuple(generator))
        if isinstance(self.element_type, AtomicType):
            return parseAtomic(self.element_type, value)
        elif isinstance(self.element_type, TupleType):
            return parseTuple(self.element_type, value)
        elif isinstance(self.element_type, Schema):
            raise TypeError("Cannot parse Schema type.")
        else:
            return parseEnum(self.element_type, value)

    def type_str(self) -> str:
        """Returns string representation of element_type"""
        if self.element_type == AtomicType.BOOL:
            return "[BOOL]"
        count = 1
        base_type = self.element_type
        if isinstance(base_type, TupleType):
            count = base_type.length
            base_type = base_type.baseType
        type_name = (
            base_type.name if isinstance(base_type, AtomicType)
            else base_type.appconfig.__name__ if isinstance(base_type, Schema)
            else base_type.__name__
        )
        if count:
            return ' '.join(type_name for _ in range(count))
        else:
            return "[%s ...]" % type_name


SchemaSource = Tuple[Tuple[str, Element], ...]

AppConfig = TypeVar("AppConfig", covariant=True)


class Schema(Dict[str, Element], Generic[AppConfig]):
    """Standardized representation of a class suitable for appconfig."""

    def __init__(self, appconfig: Type[AppConfig]):
        self.appconfig = appconfig
        schema_mapping = get_schema(appconfig)
        super().__init__(schema_mapping)

    def from_dict(self, data: ConfigMapping) -> AppConfig:
        """Instantiate appconfig object from a data dictionary."""
        def args_generator() -> Iterable[Tuple[str, object]]:
            for n, v in data.items():
                if n not in self.keys():
                    raise ValueError("invalid name %s" % n)
                else:
                    el = self[n]
                    elt = el.element_type
                    if isinstance(elt, Schema):
                        if not isinstance(v, Mapping):
                            raise ValueError(
                                f"invalid value {v!r} for {n!r}")
                        if el.has_default:
                            v = dict(elt.to_dict(el.default_value, True), **v)
                        yield n, elt.from_dict(v)
                    else:
                        yield n, el.parse(v)
        args = dict(args_generator())
        return self.appconfig(**args)

    def to_dict(
        self,
        instance: object,
        include_defaults: bool = False
    ) -> Dict[str, ConfigMappingValueType]:
        if not isinstance(instance, self.appconfig):
            raise TypeError("Need an instance of the class the schema is for.")

        def data_generator(
        ) -> Iterable[Tuple[str, ConfigMappingValueType]]:
            for name, element in self.items():
                value: ConfigValueType = getattr(instance, name)
                if (include_defaults or not element.has_default
                        or element.default_value != value):
                    if isinstance(element.element_type, Schema):
                        yield name, element.element_type.to_dict(
                            value, include_defaults)
                    else:
                        yield name, value
        return dict(data_generator())

    def type_check(self, instance: object) -> bool:
        """Checks all attributes of the instance against element types."""
        if isinstance(instance, self.appconfig):
            return all(el.type_check(getattr(instance, name))
                       for name, el in self.items())
        return False

    def deep_items(
        self
    ) -> Generator[Tuple[DeepSchemaKey, Element], None, None]:
        for key, el in self.items():
            if isinstance(el.element_type, Schema):
                for deep_key, deep_el in el.element_type.deep_items():
                    yield ((key,) + deep_key, deep_el)
            else:
                yield ((key, ), el)


def interpret_type(t: Union[type, Any]) -> Optional[ElementType]:
    """Tries to interpret a type t as one of the supported types.

    Returns a type label or None for unsupported types."""
    def tryAtomic(t: type) -> Optional[
            Union[AtomicType, Type[Enum], Schema[Any]]]:
        try:
            if issubclass(t, Enum):
                return t
            if issubclass(t, str):
                return AtomicType.STR
            if issubclass(t, bool):
                return AtomicType.BOOL
            if issubclass(t, int):
                return AtomicType.INT
            if issubclass(t, float):
                return AtomicType.FLOAT
            return Schema(t)  # type: ignore
            # Schema constructor raises runtime  exceptions for improper types
        except (TypeError, ValueError):
            return None

    if get_origin(t) is tuple:
        type_args = get_args(t)
        if len(type_args) > 0:
            base = type_args[0]
            baseType = tryAtomic(base)
            if isinstance(baseType, Schema):
                return None
            if baseType is not None:
                if all(map(lambda x: x == base, type_args)):
                    return TupleType(baseType, len(type_args))
                elif len(type_args) == 2 and type_args[1] == Ellipsis:
                    return TupleType(baseType, 0)
        return None
    return tryAtomic(t)


@lru_cache(maxsize=None)
def get_schema(appconfig: type) -> Mapping[str, Element]:
    # deliberate excessive runtime check
    if not isinstance(appconfig, type):  # type: ignore
        raise TypeError("argument must be a class.")
    installed_decl: Mapping[str, ModuleType] = get_installed_decl()
    logger.debug("using installed plugins %r.", installed_decl.keys())
    schema: Optional[Mapping[str, Element]] = None
    for name, plugin in installed_decl.items():
        if hasattr(plugin, "inspect"):
            schema = getattr(plugin, "inspect")(appconfig)
            if schema is not None:
                logger.info(
                    "schema '%r' has been recognized by plugin '%s'.",
                    appconfig, name)
                break
    if schema is not None:
        return schema
    else:
        raise ValueError(
            f"The schema {appconfig} hasn't been recognized by any of the "
            f"installed extensions: {list(installed_decl.keys())!r}")
