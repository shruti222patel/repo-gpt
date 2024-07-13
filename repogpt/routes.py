import asyncio
import json
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from aiocache import Cache
from aiocache.serializers import JsonSerializer
from fastapi import (
    BackgroundTasks,
    Body,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    WebSocket,
)
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from repogpt.agents.autogen.repo_qna import FINISHED
from repogpt.code_manager.code_vscode_file_extractor import CodeVscodeFileExtractor
from repogpt.logging_config import VERBOSE_INFO, configure_logging
from repogpt.openai_service import OpenAIService, is_openai_api_key_valid
from repogpt.prompt_service import PromptService
from repogpt.search_service import SearchService
from repogpt.service import make_query, perform_search, setup_code_manager

CODE_ROOT_PATH = Path("/app/code_root")
CODE_EMBEDDING_FILE_PATH = CODE_ROOT_PATH / ".repogpt/code_embeddings.pkl"
# docker build -t repogpt:latest .
# docker run --rm -p 8000:8000 -v /Users/shrutipatel/projects/work/repo-gpt:/app/code_root repogpt:latest --reload


app = FastAPI()

cache = Cache(Cache.MEMORY, serializer=JsonSerializer())

configure_logging(VERBOSE_INFO)


# Global variable to track the time of the last request
last_request_time = datetime.now()


def update_last_request_time():
    global last_request_time
    last_request_time = datetime.now()


@app.middleware("http")
async def track_activity(request: Request, call_next):
    if not request.url.path.startswith("/health"):
        update_last_request_time()
    response = await call_next(request)
    return response


async def check_inactivity_and_shutdown():
    global last_request_time
    inactivity_timeout = timedelta(minutes=10)

    while True:
        await asyncio.sleep(60)  # Check every 60 seconds
        if datetime.now() - last_request_time > inactivity_timeout:
            print("Shutting down due to inactivity.")
            os._exit(0)  # Forcefully stops the server


# Add the background task in the startup event
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_inactivity_and_shutdown())


# Dependency function to validate OpenAI API Key
# Updated Dependency function to validate OpenAI API Key
async def validate_openai_api_key(
    openai_api_key_header: str = Header(None, alias="OpenAI-API-Key"),
    openai_api_key_query: str = Query(None, alias="openai-api-key"),
) -> str:
    # Check if the API key is provided in headers or query parameters
    openai_api_key = openai_api_key_header or openai_api_key_query

    if openai_api_key is None:
        raise HTTPException(status_code=400, detail="Missing OpenAI-API-Key")

    is_valid_key = is_openai_api_key_valid(openai_api_key)

    if is_valid_key:
        return openai_api_key
    else:
        raise HTTPException(status_code=401, detail="Invalid OpenAI API key")


# async def validate_repogpt_key(
#     repogpt_api_key_header: str = Header(None, alias="RepoGPT-Key"),
#     repogpt_api_key_query: str = Query(None, alias="repogpt-key"),
# ) -> str:
#     # Check if the API key is provided in headers or query parameters
#     repogpt_api_key = repogpt_api_key_header or repogpt_api_key_query
#
#     if repogpt_api_key is None:
#         raise HTTPException(status_code=400, detail="Missing RepoGPT-Key")
#
#     is_valid_key = is_repogpt_api_key_valid(repogpt_api_key)
#
#     if is_valid_key:
#         return repogpt_api_key
#     else:
#         raise HTTPException(status_code=401, detail="Invalid RepoGPT key")
#
# async def is_repogpt_api_key_valid(repogpt_api_key: str) -> bool:
#     return True
#


@app.get("/setup")
async def setup_endpoint(
    openai_api_key: str = Depends(validate_openai_api_key),
    embedding_path: str = CODE_EMBEDDING_FILE_PATH,
    code_root_path: str = CODE_ROOT_PATH,
):
    try:
        await setup_code_manager(embedding_path, code_root_path, openai_api_key)
        return {"data": "Setup completed successfully."}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def search_endpoint(
    question: str = Query(..., description="The question to ask the model"),
    openai_api_key: str = Depends(validate_openai_api_key),
    embedding_path: str = CODE_EMBEDDING_FILE_PATH,
    code_root_path: str = CODE_ROOT_PATH,
):
    if openai_api_key is None:
        raise HTTPException(status_code=400, detail="Missing OpenAI-API-Key header")
    try:
        response_generator = await perform_search(
            question, embedding_path, code_root_path, openai_api_key
        )
        return StreamingResponse(response_generator, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/query")
#  curl -X GET "http://localhost:8000/query?question=What%20testing%20framework%20does%20this%20repo%20use%3F&openai-api-key=sk-xxx"
async def query_endpoint(
    question: str = Query(..., description="The question to ask the model"),
    openai_api_key: str = Depends(validate_openai_api_key),
    # repogpt_key: str = Depends(validate_repogpt_key),
    embedding_path: str = CODE_EMBEDDING_FILE_PATH,
    code_root_path: str = CODE_ROOT_PATH,
):
    if openai_api_key is None:
        raise HTTPException(status_code=400, detail="Missing Openai-API-Key header")
    try:
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        # code_root_path = Path("/Users/shrutipatel/projects/work/repo-gpt")
        # embedding_path = Path(
        #     code_root_path / ".repogpt" / "code_embeddings.pkl"
        # )
        # openai_api_key = "sk-xxx"
        # question = "test framework"

        # threading.Thread(target=make_query, args=(queue, question, CODE_EMBEDDING_FILE_PATH, CODE_ROOT_PATH, openai_api_key, loop)).start()
        threading.Thread(
            target=make_query,
            args=(
                queue,
                question,
                embedding_path,
                code_root_path,
                openai_api_key,
                loop,
            ),
        ).start()
        print("Started thread")
        return StreamingResponse(queue_to_sse(queue), media_type="text/event-stream")
    except asyncio.CancelledError as e:
        print("CancelledError")
        raise HTTPException(status_code=408, detail=str(e))
    except asyncio.TimeoutError as e:
        print("TimeoutError")
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


async def queue_to_sse(queue: asyncio.Queue):
    print("starting queue_to_sse")
    is_first = True
    while True:
        item = await queue.get()

        if is_first:
            is_first = False
        else:
            print(item)
            yield f"data: {json.dumps(item)}\n\n"

        queue.task_done()

        if item.get("sender", "") == FINISHED:
            break


@app.get("/health")
async def health_endpoint():
    try:
        # Implement any logic here to check the health of your app.
        # For example, check database connectivity, external service availability, etc.

        # If everything is fine
        return {"status": "healthy"}
    except Exception as e:
        # If there's any issue, you can raise an HTTPException with appropriate status code
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/validate-llm-key")
async def validate_openai_api_key_endpoint(
    openai_api_key: str = Depends(validate_openai_api_key),
):
    return {"status": "valid"}


class CodeLensRequest(BaseModel):
    file_path: Optional[str] = None
    file_data: Optional[str] = None
    language: str


@app.post("/extract-codelens")
async def extract_codelens(request: CodeLensRequest):
    try:
        if request.file_path:
            parsed_codelens_code = (
                CodeVscodeFileExtractor().extract_functions_from_file(request.file_path)
            )
        elif request.file_data and request.language:
            parsed_codelens_code = (
                CodeVscodeFileExtractor().extract_functions_from_file_data(
                    file_data=request.file_data, language=request.language
                )
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either file_path or file_data and language must be provided",
            )
        return parsed_codelens_code
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


# Update the /explain endpoint to use GET and query parameters
# curl -X GET "http://localhost:8000/explain?language=python&code=%20%20%20%20def%20_transformers(self%2C%20value)%3A%0A%20%20%20%20%20%20%20%20%22%22%22DO%20NOT%20USE%3A%20This%20is%20for%20the%20implementation%20of%20set_params%20via%0A%20%20%20%20%20%20%20%20BaseComposition._get_params%20which%20gives%20lists%20of%20tuples%20of%20len%202.%0A%20%20%20%20%20%20%20%20%22%22%22%0A%20%20%20%20%20%20%20%20try%3A%0A%20%20%20%20%20%20%20%20%20%20%20%20self.transformers%20%3D%20%5B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20(name%2C%20trans%2C%20col)%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20for%20((name%2C%20trans)%2C%20(_%2C%20_%2C%20col))%20in%20zip(value%2C%20self.transformers)%0A%20%20%20%20%20%20%20%20%20%20%20%20%5D%0A%20%20%20%20%20%20%20%20except%20(TypeError%2C%20ValueError)%3A%0A%20%20%20%20%20%20%20%20%20%20%20%20self.transformers%20%3D%20value%0A&openai-api-key=sk-xxx"
@app.get("/explain")
async def explain_endpoint(
    code: str = Query(..., description="The source code to be analyzed"),
    language: str = Query(
        ..., description="The programming language of the source code"
    ),
    openai_api_key: str = Depends(validate_openai_api_key),
):
    try:
        # print(f"OpenAI API Key: {openai_api_key}")
        openai_service = OpenAIService(openai_api_key)
        search_service = SearchService(openai_service, language=language)
        response_generator = await search_service.explain(code, output_html=False)

        return StreamingResponse(response_generator, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Update the /refactor endpoint to use GET and query parameters
@app.get("/refactor")
# curl -X GET "http://localhost:8000/refactor?language=python&code=%20%20%20%20def%20_transformers(self%2C%20value)%3A%0A%20%20%20%20%20%20%20%20%22%22%22DO%20NOT%20USE%3A%20This%20is%20for%20the%20implementation%20of%20set_params%20via%0A%20%20%20%20%20%20%20%20BaseComposition._get_params%20which%20gives%20lists%20of%20tuples%20of%20len%202.%0A%20%20%20%20%20%20%20%20%22%22%22%0A%20%20%20%20%20%20%20%20try%3A%0A%20%20%20%20%20%20%20%20%20%20%20%20self.transformers%20%3D%20%5B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20(name%2C%20trans%2C%20col)%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20for%20((name%2C%20trans)%2C%20(_%2C%20_%2C%20col))%20in%20zip(value%2C%20self.transformers)%0A%20%20%20%20%20%20%20%20%20%20%20%20%5D%0A%20%20%20%20%20%20%20%20except%20(TypeError%2C%20ValueError)%3A%0A%20%20%20%20%20%20%20%20%20%20%20%20self.transformers%20%3D%20value%0A&openai-api-key=sk-xxx"
async def refactor_endpoint(
    language: str = Query(
        ..., description="The programming language of the source code"
    ),
    code: str = Query(..., description="The source code to be refactored"),
    instructions: str = Query(..., description="Refactoring instructions"),
    openai_api_key: str = Depends(validate_openai_api_key),
):
    try:
        openai_service = OpenAIService(openai_api_key)
        prompt_service = PromptService(openai_service, language=language)
        response_generator = await prompt_service.refactor_code(
            code, additional_instructions=instructions
        )

        return StreamingResponse(response_generator, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         try:
#             # Receive JSON data
#             json_data = await websocket.receive_text()
#             update_last_request_time()
#
#             # Deserialize JSON to Pydantic Model (WSMessage)
#             ws_message = WSMessage.model_validate_json(json_data)
#
#             cache_key = f"conversation_id_{ws_message.conversation_id}"
#             conversation = await cache.get(cache_key)
#             if not conversation:
#                 # create new conversation
#                 conversation = Conversation(ws_message)
#                 await cache.set(cache_key, conversation)
#
#             conversation.receive_message(ws_message)
#
#             # Process the message and prepare a response (example)
#             response = f"Received message of type: {ws_message.message_type}"
#             await websocket.send_text(response)
#
#         except ValueError as e:
#             # Handle validation errors from Pydantic
#             await websocket.send_text(f"Error: Invalid data format - {str(e)}")
#         except Exception as e:
#             await websocket.send_text(f"Error: {str(e)}")
#
# class WSMessageType(Enum):
#     INITIAL_MESSAGE = "INITIAL_MESSAGE"
#     IN_PROGRESS = "IN_PROGRESS"
#     FINISHED = "FINISHED"
# class ConversationType(Enum):
#     EXPLAIN = "explain"
#     REFACTOR = "refactor"
# class WSMessage(BaseModel):
#     conversation_id: str
#     message_type: WSMessageType
#     conversation_type: ConversationType
#     message: str
#     data: Any
#     openai_api_key: str
#
#
# class ActionType(Enum):
#     SHOW = "SHOW"
#     ASK = "ASK"
#     UPDATE_CODE = "UPDATE_CODE"
#
# class Action(BaseModel):
#     type: ActionType
#     data: Any
#
# class UpdateCodeAction(Action):
#     type: ActionType = ActionType.UPDATE_CODE
#     data: Any
#
# class UpdateCodeActionData(BaseModel):
#     code: str
#     language: str
#     functionName: str
#     functionBody: str
#     functionStartLine: int
#     functionEndLine: int
#     functionFilePath: str
#
# class WSResponseType(Enum):
#     STREAM_IN_PROGRESS = "STREAM_IN_PROGRESS"
#     STREAM_FINISHED = "STREAM_FINISHED"
#     FULL_RESPONSE = "FULL_RESPONSE"
# class WSResponse(BaseModel):
#     conversation_id: str
#     response_id: str
#     conversation_type: ConversationType
#     message_type: WSResponseType
#     message: str
#     actions: List[Action]
#
# class Conversation:
#
#     messages: List[WSMessage] = []
#     def __init__(self, ws_message: WSMessage):
#         self.id = ws_message.conversation_id
#         self.initial_message = ws_message.message
#         self.type = ws_message.conversation_type
#         self.openai_api_key = ws_message.openai_api_key
#         self.initial_data = ws_message.data
#         self.code = self.initial_data.get("code", "")
#         self.language = self.initial_data.get("language", "")
#         self.start
#
#
#     def receive_message(self, message: WSMessage):
#         self.messages.append(message)
#         if message.message_type == WSMessageType.INITIAL_MESSAGE:
#             return WSResponse(
#                 conversation_id=self.id,
#                 conversation_type=self.type,
#                 message_type=WSMessageType.IN_PROGRESS,
#                 message="Is there something specific you'd like to refactor?",
#             )
#
#         elif message.message_type == WSMessageType.IN_PROGRESS:
#             # Ask ChatGPT to refactor
#             openai_service = OpenAIService(self.openai_api_key)
#             prompt_service = PromptService(openai_service, language=self.language)
#             response_id = str(uuid.uuid4())
#             response_generator = await prompt_service.refactor_code(
#                 self.code, additional_instructions=message.message
#             )
#             return response_generator
#         elif message.message_type == WSMessageType.FINISHED:
#             pass
#         else:
#             raise Exception("Invalid message type")


# The __name__ == "__main__" block is not needed when using uvicorn to run the app
# RUN this when debugging: uvicorn repogpt.routes:app --port 8000 --reload
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
"""
