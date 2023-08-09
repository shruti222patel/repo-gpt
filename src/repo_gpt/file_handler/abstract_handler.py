from abc import ABC, abstractmethod
from collections import namedtuple
from typing import List, TypeVar

FileHandler = TypeVar("FileHandler", bound="AbstractHandler")

# code_type is either "function" or "class"
CodeBlock = namedtuple(
    "CodeBlock", ["code", "code_type", "name", "filepath", "file_checksum"]
)

ParsedCode = namedtuple("ParsedCode", ["name", "code_type", "code"])

CODE_TYPE_FUNCTION = "function"
CODE_TYPE_CLASS = "class"


class AbstractHandler(ABC):
    @abstractmethod
    def extract_code(self, filepath) -> List[ParsedCode]:
        pass
