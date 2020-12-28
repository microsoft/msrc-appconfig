from typing import IO, Union
from pathlib import Path


class YAML:
    def __init__(self, *, typ: str = '', pure: bool = False) -> None: ...
    def load(self, doc: Union[str, IO[str], Path]) -> object: ...
