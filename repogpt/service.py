from pathlib import Path

from repogpt.agents.autogen.repo_qna import RepoQnA
from repogpt.code_manager.code_manager import CodeManager
from repogpt.openai_service import OpenAIService
from repogpt.search_service import SearchService


async def setup_code_manager(embedding_path, code_root_path, openai_api_key):
    openai_service = OpenAIService(openai_api_key)
    manager = CodeManager(embedding_path, code_root_path, openai_service)
    await manager.setup()


async def perform_search(query, embedding_path, code_root_path, openai_api_key):
    openai_service = OpenAIService(openai_api_key)
    search_service = SearchService(openai_service, embedding_path)
    await update_code_embedding_file(search_service, code_root_path, embedding_path)
    return search_service.question_answer(query)


def make_query(queue, question, embedding_path, code_root_path, openai_api_key, loop):
    print("starting make query")
    openai_service = OpenAIService(openai_api_key)
    # TODO undo comment
    # search_service = SearchService(openai_service, embedding_path)
    # asyncio.run_coroutine_threadsafe(
    #     update_code_embedding_file(search_service, code_root_path, embedding_path), loop
    # )
    print("updated code embedding file")
    repo_qna = RepoQnA(
        queue, loop, question, code_root_path, embedding_path, openai_api_key
    )
    print("created repo qna")
    return repo_qna.initiate_chat()


async def update_code_embedding_file(
    search_service, root_file_path: str, code_embedding_file_path: str
):
    manager = CodeManager(Path(code_embedding_file_path), Path(root_file_path))
    await manager.setup()
    search_service.refresh_df()
