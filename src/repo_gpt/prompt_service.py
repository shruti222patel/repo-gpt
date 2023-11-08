from repo_gpt.openai_service import OpenAIService
from repo_gpt.utils import Singleton


class PromptService(metaclass=Singleton):
    def __init__(self, openai_service: OpenAIService, language: str):
        self.language = language
        self.openai_service = openai_service

    def analyze_file(self, file_path: str, output_html: bool = False):
        with open(file_path, "r") as f:
            code = f.read()

        self.explain(code, output_html=output_html)

    def explain(self, code: str, output_html: bool = False):
        format = "html" if output_html else "markdown"
        try:
            explanation = self.openai_service.query_stream(
                f"""Please explain the following {self.language} function.

```{self.language}
{code}
```""",
                system_prompt=f"""You are a world-class {self.language} developer and you are explaining the following code to a junior developer. Be concise. Organize your explanation in {format}.""",
            )
            return explanation
        except Exception as e:
            return e.message

    def refactor_code(self, code: str, additional_instructions: str):
        addition_instruction_query = (
            f" Additional instructions: {additional_instructions}"
            if additional_instructions
            else ""
        )
        self.openai_service.query_stream(
            f"""Please refactor the following {self.language} function.{addition_instruction_query}

```{self.language}
{code}
```""",
            system_prompt=f"""You are a world-class {self.language} developer and you are refactoring code. You always use best practices when coding.
When you edit or add code, you respect and use existing conventions, libraries, etc. Only output all refactored code in the following format:
```{self.language}
<your refactored code>
```""",
        )

    def query_code(self, question: str, code: str = ""):
        self.openai_service.query_stream(
            f"""Use the code below to answer the subsequent question. If the answer cannot be found, write "I don't know."
```
{code}
```
Question: {question}
Output the answer in well organized markdown."""
        )

    def _extract_code(self, response: str):
        split = response.split("```{self.language}")
        if len(split) < 2:
            raise Exception("No code found in response")
        code = split[1].split("```")[0]

        return code
