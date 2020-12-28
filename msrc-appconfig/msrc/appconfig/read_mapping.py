"""Configuration elements source: in-memory mapping."""
from typing import Generator, Mapping, Tuple, cast

from msrc.appconfig.schema import Schema, DeepSchemaKey, ConfigValue


def from_mapping(
        schema: Schema[object],
        data: Mapping[str, object],
        provenance: Tuple[str, ...]
) -> Generator[ConfigValue, None, None]:
    """Takes configuration elements from a mapping.

    `schema` is an appconfig schema.

    `data` is the mapping to take configuration elements from.

    `provenance` is a prefix that identifies source of configuration
    elements.

    Yields a sequence of `ConfigValue` tuples.

    The function ignores entries of the mapping that do not match schema
    elements. For example, the following code
    ```python
    class AppConfig(NamedTuple):
        a: str
        b: int

    from_mapping(Schema(AppConfig), dict(b=5, c="ignored"), ())
    ```
    will yield a single value for entry `b`.
    """
    def try_yield(
            path: DeepSchemaKey,
            name: DeepSchemaKey,
            data: Mapping[str, object]
    ) -> Generator[Tuple[object, DeepSchemaKey], None, None]:
        n0 = name[0]
        if n0 in data:
            value = data[n0]
            path += (n0, )
            if len(name) > 1:
                if isinstance(value, Mapping):
                    nested = cast(Mapping[str, object], value)
                    assert all(isinstance(key, str) for key in nested.keys())
                    yield from try_yield(path, name[1:], nested)
                else:
                    raise ValueError(f"{path!r} is not a mapping: {value!r}")
            else:
                yield value, path

    for name, el in schema.deep_items():
        for v, _ in try_yield((), name, data):
            yield ConfigValue(name, el.parse(v), provenance)
