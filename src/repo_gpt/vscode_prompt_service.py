import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Union

from repo_gpt.openai_service import OpenAIService
from repo_gpt.prompt_service import PromptService


class Status(Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


@dataclass()
class VscodeMessage:
    # Note this will be read using Typescript in Vscode
    status: str
    code: Union[str, None]
    message: Union[str, None]
    error: Union[str, None]

    def __init__(
        self,
        status: Status = Status.ERROR,
        code: Union[str, None] = None,
        message: Union[str, None] = None,
        error: Union[Exception, str, None] = None,
    ):
        self.status = status.value
        self.code = code
        self.message = message
        self.error = str(error) if isinstance(error, Exception) else error

    def __str__(self):
        """
        This ensures printed strings are valid JSON, which is necessary for the Vscode extension to read the output.
        :return:
        """

        return json.dumps(asdict(self))


class VscodePromptService(PromptService):
    def __init__(self, openai_service: OpenAIService, language: str):
        super().__init__(openai_service, language)

    def refactor_code(
        self, input_code_file_path: str, additional_instructions: str = ""
    ):
        # try:
        with open(input_code_file_path, "r") as f:
            code = f.read()
        super().refactor_code(code, additional_instructions)
        # return VscodeMessage(status=Status.SUCCESS,code=refactored_code)
        # except Exception as e:
        #     return VscodeMessage(status= Status.ERROR, error=e)
