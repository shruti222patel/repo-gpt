from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, TypeVar

FileHandler = TypeVar("FileHandler", bound="AbstractHandler")


class CodeType(Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"


@dataclass
class ParsedCode:
    name: str
    code_type: CodeType
    code: str
    summary: str | None
    inputs: Tuple[str, ...] | None
    outputs: Tuple[str, ...] | str
    filepath: str = None
    file_checksum: str = None

    def __lt__(self, other: "ParsedCode"):
        return self.name < other.name


class AbstractHandler(ABC):
    @abstractmethod
    def extract_code(self, filepath) -> List[ParsedCode]:
        pass

    @abstractmethod
    def is_valid_code(self, code: str) -> bool:
        pass
