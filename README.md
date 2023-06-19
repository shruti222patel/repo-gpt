# Repo GPT
Search your code repository using GPT3.5.

![image](./imgs/example_output.png)

## Usage
Ensure you've exported your openai key to your environment variables.
```shell
export OPENAI_API_KEY=<insert your openai key>
```

In the repo, run the following in the root of the project you want to search.
It will create a folder called `.repo_gpt` and save the code embeddings there.
```shell
repo-gpt setup
```
Also, you can re-run the command above as many times as you want and repo-gpt will only add/update embeddings for new files or changed files.

Then, you can search for semantically similar code in your codebase using the following command:
```shell
repo-gpt search <text/question>
```

You can even ask questions about your codebase:
```shell
repo-gpt query <text/question>
```


## Contributing
### Setup
1. Install python `3.11` and latest version of [poetry](https://python-poetry.org/docs/#installing-with-pipx)
   1. `pyenv` is a good way to manage python versions if you need to have more than 1 on your computer
2. Add your openai key to your environment variables
```shell
export OPENAI_API_KEY=<insert your openai key>
```
4. Install dependencies: `poetry install --no-root`
5. Install pre-commit hooks: `poetry run pre-commit install`
6. Seed data: `poetry run python cli.py setup`
7. Query data: `poetry run python cli.py search <text/question>`

### Debugging
* View the output of the code_embeddings pkl: `pd.read_pickle('./.repo_gpt/code_embeddings.pkl', compression='infer')`

## TODO
* [ ] Publish to pypi
* [ ] Add tests
* [X] Add CI/CD
* [ ] Prettify output
* [ ] Add readme section about how folks can contribute parsers for their own languages
* [ ] Save # of tokens each code snippet has so we can ensure we don't pass too many tokens to GPT
* [ ] Add SQL file handler
* [ ] Add DBT file handler -- this may be a break in pattern as we'd want to use the manifest.json file
