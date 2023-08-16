# Set your OpenAI API key as an environment variable
import ast
import os
import time
from typing import Any, Callable

import numpy as np
import openai as openai
from tenacity import (  # for exponential backoff
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

openai.api_key = os.environ["OPENAI_API_KEY"]
MAX_RETRIES = 3

GPT_MODEL = "gpt-3.5-turbo"  # "gpt-3.5-turbo-16k"
EMBEDDING_MODEL = "text-embedding-ada-002"
TEMPERATURE = (
    0.4  # temperature = 0 can sometimes get stuck in repetitive loops, so we use 0.4
)


class OpenAIService:
    GENERAL_SYSTEM_PROMPT = "You are a world-class software engineer and technical writer specializing in understanding code + architecture + tradeoffs and explaining them clearly and in detail. You are helpful and answer questions the user asks. You organize your explanations in markdown-formatted, bulleted lists."
    ANALYSIS_SYSTEM_PROMPT = "You are a world-class Python developer with an eagle eye for unintended bugs and edge cases. You carefully explain code with great detail and accuracy. You organize your explanations in markdown-formatted, bulleted lists."

    @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def get_answer(
        self, query: str, code: str, system_prompt: str = GENERAL_SYSTEM_PROMPT
    ):
        query = f"""Use the code below to answer the subsequent question. If the answer cannot be found, write "I don't know."
        ```
        {code}
        ```
        Question: {query}"""

        response = openai.ChatCompletion.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": query},
            ],
            model=GPT_MODEL,
            temperature=TEMPERATURE,
        )
        return response.choices[0]["message"]["content"]

    def _retry_on_exception(self, func: Callable[..., Any], *args, **kwargs):
        for retry in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception:
                if retry < MAX_RETRIES - 1:  # if it's not the last retry
                    sleep_time = 2**retry  # exponential backoff
                    time.sleep(sleep_time)
                else:  # if it's the last retry, re-raise the exception
                    raise

    @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def get_embedding(self, text: str):
        response = openai.Embedding.create(input=[text], model=EMBEDDING_MODEL)

        if (
            "data" not in response
            or len(response["data"]) == 0
            or "embedding" not in response["data"][0]
        ):
            raise ValueError(
                "Invalid response from OpenAI API: 'data' field missing or empty, or 'embedding' field missing"
            )

        return np.asarray(response["data"][0]["embedding"], dtype=np.float32)

    color_prefix_by_role = {
        "system": "\033[0m",  # gray
        "user": "\033[0m",  # gray
        "assistant": "\033[92m",  # green
    }

    def print_messages(
        self, messages, color_prefix_by_role=color_prefix_by_role
    ) -> None:
        """Prints messages sent to or from GPT."""
        for message in messages:
            role = message["role"]
            color_prefix = color_prefix_by_role[role]
            content = message["content"]
            print(f"{color_prefix}\n[{role}]\n{content}")

    def print_message_delta(
        self, delta, color_prefix_by_role=color_prefix_by_role
    ) -> None:
        """Prints a chunk of messages streamed back from GPT."""
        if "role" in delta:
            role = delta["role"]
            color_prefix = color_prefix_by_role[role]
            print(f"{color_prefix}\n[{role}]\n", end="")
        elif "content" in delta:
            content = delta["content"]
            print(content, end="")
        else:
            pass

    # example of a function that uses a multi-step prompt to write unit tests
    def unit_tests_from_function(
        self,
        function_to_test: str,  # Python function to test, as a string
        language: str = "python",  # programming language of the function
        unit_test_package: str = "pytest",
        # unit testing package; use the name as it appears in the import statement
        approx_min_cases_to_cover: int = 7,  # minimum number of test case categories to cover (approximate)
        print_text: bool = False,  # optionally prints text; helpful for understanding the function & debugging
        explain_model: str = GPT_MODEL,  # model used to generate text plans in step 1
        plan_model: str = GPT_MODEL,  # model used to generate text plans in steps 2 and 2b
        execute_model: str = GPT_MODEL,  # model used to generate code in step 3
        temperature: float = TEMPERATURE,
        reruns_if_fail: int = 1,
        # if the output code cannot be parsed, this will re-run the function up to N times
    ) -> str:
        """Returns a unit test for a given Python function, using a 3-step GPT prompt."""

        # Step 1: Generate an explanation of the function

        # create a markdown-formatted message that asks GPT to explain the function, formatted as a bullet list
        explain_system_message = {
            "role": "system",
            "content": "You are a world-class Python developer with an eagle eye for unintended bugs and edge cases. You carefully explain code with great detail and accuracy. You organize your explanations in markdown-formatted, bulleted lists.",
        }
        explain_user_message = {
            "role": "user",
            "content": f"""Please explain the following Python function. Review what each element of the function is doing precisely and what the author's intentions may have been. Organize your explanation as a markdown-formatted, bulleted list.

```{language}
{function_to_test}
```""",
        }
        explain_messages = [explain_system_message, explain_user_message]
        if print_text:
            self.print_messages(explain_messages)
        print("Generating explanation...")
        explanation_response = openai.ChatCompletion.create(
            model=explain_model,
            messages=explain_messages,
            temperature=temperature,
            stream=True,
        )
        explanation = ""
        for chunk in explanation_response:
            delta = chunk["choices"][0]["delta"]
            if print_text:
                self.print_message_delta(delta)
            if "content" in delta:
                explanation += delta["content"]
        explain_assistant_message = {"role": "assistant", "content": explanation}

        # Step 2: Generate a plan to write a unit test

        # Asks GPT to plan out cases the units tests should cover, formatted as a bullet list
        plan_user_message = {
            "role": "user",
            "content": f"""A good unit test suite should aim to:
- Test the function's behavior for a wide range of possible inputs
- Test edge cases that the author may not have foreseen
- Take advantage of the features of `{unit_test_package}` to make the tests easy to write and maintain
- Be easy to read and understand, with clean code and descriptive names
- Be deterministic, so that the tests always pass or fail in the same way

To help unit test the function above, list diverse scenarios that the function should be able to handle (and under each scenario, include a few examples as sub-bullets).""",
        }
        plan_messages = [
            explain_system_message,
            explain_user_message,
            explain_assistant_message,
            plan_user_message,
        ]
        if print_text:
            self.print_messages([plan_user_message])
        plan_response = openai.ChatCompletion.create(
            model=plan_model,
            messages=plan_messages,
            temperature=temperature,
            stream=True,
        )
        plan = ""
        for chunk in plan_response:
            delta = chunk["choices"][0]["delta"]
            if print_text:
                self.print_message_delta(delta)
            if "content" in delta:
                plan += delta["content"]
        plan_assistant_message = {"role": "assistant", "content": plan}

        # Step 2b: If the plan is short, ask GPT to elaborate further
        # this counts top-level bullets (e.g., categories), but not sub-bullets (e.g., test cases)
        num_bullets = max(plan.count("\n-"), plan.count("\n*"))
        elaboration_needed = num_bullets < approx_min_cases_to_cover
        if elaboration_needed:
            elaboration_user_message = {
                "role": "user",
                "content": f"""In addition to those scenarios above, list a few rare or unexpected edge cases (and as before, under each edge case, include a few examples as sub-bullets).""",
            }
            elaboration_messages = [
                explain_system_message,
                explain_user_message,
                explain_assistant_message,
                plan_user_message,
                plan_assistant_message,
                elaboration_user_message,
            ]
            if print_text:
                self.print_messages([elaboration_user_message])
            print("Generating elaboration...")
            elaboration_response = openai.ChatCompletion.create(
                model=plan_model,
                messages=elaboration_messages,
                temperature=temperature,
                stream=True,
            )
            elaboration = ""
            for chunk in elaboration_response:
                delta = chunk["choices"][0]["delta"]
                if print_text:
                    self.print_message_delta(delta)
                if "content" in delta:
                    elaboration += delta["content"]
            elaboration_assistant_message = {
                "role": "assistant",
                "content": elaboration,
            }

            # Step 3: Generate the unit test

            # create a markdown-formatted prompt that asks GPT to complete a unit test
            package_comment = ""
            if unit_test_package == "pytest":
                package_comment = "# below, each test case is represented by a tuple passed to the @pytest.mark.parametrize decorator"
            execute_system_message = {
                "role": "system",
                "content": "You are a world-class Python developer with an eagle eye for unintended bugs and edge cases. You write careful, accurate unit tests. When asked to reply only with code, you write all of your code in a single block.",
            }
            execute_user_message = {
                "role": "user",
                "content": f"""Using {language} and the `{unit_test_package}` package, write a suite of unit tests for the function, following the cases above. Include helpful comments to explain each line. Reply only with code, formatted as follows:

```{language}
# imports
import {unit_test_package}  # used for our unit tests
{{insert other imports as needed}}

# function to test
{function_to_test}

# unit tests
{package_comment}
{{insert unit test code here}}
```""",  # TODO: update so it work for all languages
            }
            execute_messages = [
                execute_system_message,
                explain_user_message,
                explain_assistant_message,
                plan_user_message,
                plan_assistant_message,
            ]
            if elaboration_needed:
                execute_messages += [
                    elaboration_user_message,
                    elaboration_assistant_message,
                ]
            execute_messages += [execute_user_message]
            if print_text:
                self.print_messages([execute_system_message, execute_user_message])

            print("Generating unit tests...")
            execute_response = openai.ChatCompletion.create(
                model=execute_model,
                messages=execute_messages,
                temperature=temperature,
                stream=True,
            )
            execution = ""
            for chunk in execute_response:
                delta = chunk["choices"][0]["delta"]
                if print_text:
                    self.print_message_delta(delta)
                if "content" in delta:
                    execution += delta["content"]

            # check the output for errors
            code = execution.split(f"```{language}")[1].split("```")[0].strip()
            try:
                ast.parse(code)  # TODO use treesitter instead
            except SyntaxError as e:
                print(f"Syntax error in generated code: {e}")
                if reruns_if_fail > 0:
                    print("Rerunning...")
                    return self.unit_tests_from_function(
                        function_to_test=function_to_test,
                        language=language,
                        unit_test_package=unit_test_package,
                        approx_min_cases_to_cover=approx_min_cases_to_cover,
                        print_text=print_text,
                        explain_model=explain_model,
                        plan_model=plan_model,
                        execute_model=execute_model,
                        temperature=temperature,
                        reruns_if_fail=reruns_if_fail
                        - 1,  # decrement rerun counter when calling again
                    )

            # return the unit test as a string
            return code
