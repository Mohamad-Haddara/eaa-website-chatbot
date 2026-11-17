"""
Build the FastAPI app: routes, CORS, security headers, start-up and shut-down of the Azure Client

"""
from fastapi import FastAPI, status, Request
from models import ChatRequest
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable
from llm import ChatModel, AzureChatModel
from chat import ChatService
from prompts import detect_language
import uuid
from starlette.responses import StreamingResponse
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)



# LifeSpan: Create shared object once at startup
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]: # async generator: code before yield = startup, after = shutdown
    """
    Create the service clients once at start-up and close them at shutdown.
    """
    
    chat_model = AzureChatModel() # createad once, shared by all requests

    app.state.chat = ChatService(llm=chat_model)    # ChatService what our endpoint reads

    try:
        yield       # the app serves requests while paused here

    finally:
        await chat_model.close()    # shutdown: closes the client



app = FastAPI(
    title="EAA website chatbot API",
    lifespan=lifespan,
    docs_url="/docs"

)


# Middelware: runs for every requests
@app.middleware("http")
async def time_request(request: Request, call_next: Callable):
    # Start timing
    start = time.perf_counter()

    # Handle request
    response: StreamingResponse = await call_next(request)

    # Finish timing request
    duration_ms = (time.perf_counter() - start) * 1000

    logger.info(f"RESP {response.status_code} ({duration_ms}) @{request.url.path} {request.url.query}")

    # Parse the header and return response
    response.headers['X-Process-Time'] = str(duration_ms * 1000)
    return response



@app.middleware("http")
async def add_request_id(request: Request, call_next: Callable) -> StreamingResponse:
    # correlation id a unique identifier attached to an HTTP incoming request
    #request.state.correlation_id = uuid.uuid4().hex
    #return await call_next(request)

    # str: reuse the incoming header if present, otherwise create a new UUID4 string
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    request.state.request_id = request_id           # endpoints read it from request.state

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id   # sends the ID back to the client  

    return response
    

@app.get("/health")
async def health() -> dict[str, str]:
    """ """
    return {
        "status": "healthy"
    }


# Implementing SSE (POST) endpoint on the server
@app.post("/api/chat")
async def chat(body:ChatRequest, request: Request):
    """
    Answer a question as a stream of SSE events (SSE), or return a JSON error

    - Before streaming starts: JSON error with status code (400, 403, 413, 429, 503)
    - After streaming starts: errors arrive as an 'error' SSE event
    

    Note: /api/chat
        - SSE stream 
        - JSON error ~ 400, 403, 413, 429 or 503 (busy) before streaming start; error events start

    Intial: Validate question -> detect language -> stream
    """
    # Detect language
    lang = detect_language(body.question)

    # allow the origin list

    # get the origin and raise an error for any failure
    origin = (request.headers.get("origin") or "").rstrip("/")
    logger.info(f"Origin: {origin}")
    

    # Extract question
    question = body.question.strip()  
    logger.info(f"USer Question: {question}")
    # If empty question ~ return error 400

    # if question is longer than limit ~ return error 400

    # Peer 
    peer = request.client.host if request.client else None
    logger.info(f"Peer: {peer}")

    
    # Read the request_id that is created in the middleware
    request_id = request.state.request_id
    logger.info(f"Request-ID: {request_id}")

    # Create a chat service to return response as SSE
    service: ChatService = request.app.state.chat

    # Pass the chat stream generator to the StreamResponse to forward the output stream as it is being generated to the client
    # Set the media_type: "text/event-stream" as per SSE specifications so that the browsers can handle the response correctly 
    return StreamingResponse(
        content=service.stream(body, request_id, lang),
        media_type="text/event-stream; charset=utf-8",
    )

if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, reload=True)
