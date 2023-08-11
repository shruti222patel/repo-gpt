from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, TypeVar

FileHandler = TypeVar("FileHandler", bound="AbstractHandler")


class CodeType(Enum):
    FUNCTION = "function"
    CLASS = "class"


@dataclass(frozen=True)
class CodeBlock:  # TODO add ParsedCode as a field so fields aren't repeated
    code: str
    code_type: CodeType
    name: str
    inputs: Tuple[str, ...]
    filepath: str
    file_checksum: str


@dataclass(frozen=True)
class ParsedCode:
    name: str
    code_type: CodeType
    code: str
    inputs: Tuple[str, ...]


class AbstractHandler(ABC):
    @abstractmethod
    def extract_code(self, filepath) -> List[ParsedCode]:
        pass
