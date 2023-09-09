# Repo GPT

Repo-GPT is a Python CLI tool designed to utilize the power of OpenAI's GPT-3 model. It facilitates the process of code analysis and search within your repositories.

![Repo-GPT in action](./imgs/example_output.png)

## Features

- Code extraction and processing from your repositories.
- Semantic search within your codebase through natural language queries.
- Response generation to natural language queries about your code.
- Specific file analysis within your codebase.

## Installation

Repo-GPT can be installed via [pip](https://pip.pypa.io/en/stable/):

```bash
pip install repo-gpt
```

Alternatively, you can clone and install from the source code:

```bash
git clone https://github.com/yourusername/repo-gpt.git
cd repo-gpt
poetry install
```

## Setting Up

Before starting, make sure to set up your OpenAI key in your environment variables.

```shell
export OPENAI_API_KEY=<insert your openai key>
```

To set up Repo-GPT, run the following command at the root of the project you want to search. This will create a `.repo_gpt` directory and store the code embeddings there:

```shell
repo-gpt setup
```

Repo-GPT will only add or update embeddings for new files or changed files. You can rerun the setup command as many times as needed.

## Usage

After setup, you can perform various tasks:

- **Semantic Search**: Find semantically similar code snippets in your codebase:

  ```shell
  repo-gpt search <text/question>
  ```

- **Codebase Query**: Ask questions about your codebase:

  ```shell
  repo-gpt query <text/question>
  ```

- **File Analysis**: Analyze a specific file:

  ```shell
  repo-gpt analyze <file_path>
  ```

- **Help**: Access the help guide:

  ```shell
  repo-gpt help
  ```

- **Generate tests**: Generate tests for a function:
Note: this assumes the function name is unique in the codebase, otherwise, it will pick the first function it finds with that name.

   ```shell
   repo-gpt add-test <unique function name> --test_save_file_path <absolute filepath to add tests to> --testing_package <testing package to use e.g. pytest>
   ```

Example:

```bash
repo-gpt setup --root_path ./my_project
repo-gpt search "extract handler"
repo-gpt query "What does the function `calculate_sum` do?"
repo-gpt analyze ./my_project/main.py
repo-gpt add-test function_name --test_save_file_path $PWD/test.py --testing_package pytest
```

## Contributing

We welcome your contributions! Before starting, please make sure to install Python `3.11` and the latest version of [poetry](https://python-poetry.org/docs/#installing-with-pipx). [Pyenv](https://github.com/pyenv/pyenv) is a convenient tool to manage multiple Python versions on your computer.

Here are the steps to set up your development environment:

1. Export your OpenAI key to your environment variables:

   ```shell
   export OPENAI_API_KEY=<insert your openai key>
   ```

2. Install dependencies:

   ```shell
   poetry install --no-root
   ```

3. Install pre-commit hooks:

   ```shell
   poetry run pre-commit install
   ```

4. Seed data:

   ```shell
   poetry run python cli.py setup
   ```

5. Query data:

   ```shell
   poetry run python cli.py search <text/question>
   ```

### Debugging

You can view the output of the `code_embeddings.pkl` using the following command:

```shell
poetry shell
python
pd.read_pickle('./.repo_gpt/code_embeddings.pkl', compression='infer')
```

#### Interpreter
```shell
poetry shell
ipython
%load_ext autoreload
%autoreload 2
```

## Roadmap

Here are the improvements we are currently considering:

- [X] Publishing to PyPi
- [X] Test suite addition
- [X] Add CI/CD
- [X] Prettify output
- [ ] Add readme section about how folks can contribute parsers for their own languages
- [ ] Save # of tokens each code snippet has so we can ensure we don't pass too many tokens to GPT
- [X] Add SQL file handler
- [ ] Add DBT file handler -- this may be a break in pattern as we'd want to use the manifest.json file
- [X] Create VSCode extension
- [ ] Ensure files can be added & deleted and the indexing picks up on the changes.
- [ ] Add .repogptignore file to config & use it in the indexing command
- [ ] Use pygments library for prettier code formatting
