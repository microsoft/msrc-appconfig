from typing import Generic, Optional, TypeVar

_T = TypeVar("_T")


class Parameter(Generic[_T]):
    name: str
    default: _T
    readonly: bool
    doc: Optional[str]
    
    def _validate(self, val: object) -> None: ...
    ...
