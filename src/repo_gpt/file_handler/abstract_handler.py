from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Tuple, TypeVar, Union

from repo_gpt.openai_service import EMBEDDING_MODEL

FileHandler = TypeVar("FileHandler", bound="AbstractHandler")


class CodeType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    GLOBAL = "global"

    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class ParsedCode:
    function_name: Union[str, None]
    class_name: Union[str, None]
    code_type: CodeType
    code: str
    summary: Union[str, None]
    inputs: Union[Tuple[str, ...], None]
    outputs: Union[Tuple[str, ...], str, None]
    filepath: str = None
    file_checksum: str = None
    embedding_model: str = EMBEDDING_MODEL

    def __lt__(self, other: "ParsedCode"):
        return self.code < other.code


@dataclass(frozen=True)
class VSCodeExtCodeLensCode:
    name: str
    start_line: int
    end_line: int

    def __lt__(self, other: "VSCodeExtCodeLensCode"):
        return self.start_line < other.start_line


class AbstractHandler(ABC):
    @abstractmethod
    def extract_code(self, filepath: Path) -> List[ParsedCode]:
        pass

    @abstractmethod
    def is_valid_code(self, code: str) -> bool:
        pass

    @abstractmethod
    def extract_vscode_ext_codelens(
        self, filepath: Path
    ) -> List[VSCodeExtCodeLensCode]:
        pass
