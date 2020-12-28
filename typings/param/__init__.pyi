import typing as ty
from .parameterized import Parameter

_T = ty.TypeVar("_T")


class String(Parameter[ty.Optional[str]]):
    def __init__(self, default: ty.Optional[str] = "", regex=None,
                 allow_None=False, **kwargs):
        ...
    ...


class Boolean(Parameter[ty.Optional[bool]]):
    def __init__(self, default: ty.Optional[bool] = False, bounds=(0, 1),
                 **params):
        ...
    ...


class Number(Parameter[ty.Union[None, int, float]]):
    def __init__(self, default: ty.Union[None, int, float] = 0.0, bounds=None,
                 softbounds=None, inclusive_bounds=(True, True), step=None,
                 **params):
        ...
    ...


class Integer(Parameter[ty.Optional[int]]):
    def __init__(self, default: ty.Optional[int] = 0, **params):
        ...
    ...


class ClassSelector(Parameter[object]):
    def __init__(self, class_, default=None, instantiate=True,
                 is_instance=True, **params):
        ...
    class_: ty.Type[object]
    ...


class List(Parameter[ty.List[object]]):
    class_: ty.Type[object]

    def __init__(self, default=[], class_=None, instantiate=True,
                 bounds=(0, None), **params):
        ...
    ...


class Tuple(Parameter[ty.Tuple[_T]]):
    length: int

    def __init__(
        self, default=(0, 0), length=None, doc=None, label=None,
        precedence=None, instantiate=False, constant=False, readonly=False,
        pickle_default_value=True, allow_None=False, per_instance=True
    ) -> None: ...
    ...


class NumericTuple(Tuple[ty.Union[float, int]]):
    ...


class Path(Parameter[ty.Optional[str]]):
    def __init__(self, default: ty.Optional[str] = None,
                 search_paths=None, **params):
        ...
    ...


class _Param:
    def objects(self) -> ty.Mapping[str, Parameter[object]]: ...
    ...


class Parameterized:
    name: String
    param: _Param

    def __init__(self, **params):
        ...
    ...
