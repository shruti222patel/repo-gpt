from rich.console import Console
from rich.syntax import Syntax
from tqdm import tqdm as _tqdm

console = Console()

VERBOSE = False


def verbose_print(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


def tqdm(*args, **kwargs):
    # if VERBOSE:
    #     _tqdm.pandas()
    #     return _tqdm(*args, **kwargs)
    # else:
    return _tqdm(*args, **kwargs, disable=True)


def print_ai_assistant_chat_message(response: str):
    """Print the response from the OpenAI API.

    Args:
    - response (str): The response from the OpenAI API.
    """
    console.print(response)


def print_user_chat_message(message: str):
    """Print the user chat message.

    Args:
    - message (str): The user chat message.
    """
    console.print(f"[bold green]User:[/bold green] {message}")


def pretty_print_code(similar_code_df, language: str):
    n_lines = 7
    for r in similar_code_df.iterrows():
        console.rule(f"[bold red]{str(r[1].name)}")
        console.print(
            str(r[1].filepath)
            + ":"
            + str(r[1].name)
            + "  distance="
            + str(round(r[1].similarity, 3))
        )
        syntax = Syntax(
            "\n".join(r[1].code.split("\n")[:n_lines]), language
        )  # TODO: make this dynamic
        console.print(syntax)
