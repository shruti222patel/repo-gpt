from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Generator, TypeVar

FileHandler = TypeVar("FileHandler", bound="AbstractHandler")

CodeBlock = namedtuple("CodeBlock", ["code", "function_name", "filepath", "checksum"])


class AbstractHandler(ABC):
    @abstractmethod
    def extract_code(self, filepath) -> Generator[CodeBlock, None, None]:
        pass
