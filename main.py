"""
Build the FastAPI app: routes, CORS, security headers, start-up and shut-down of the Azure Client

"""
from fastapi import FastAPI, status
from models import ChatRequest
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator
from llm import ChatModel, AzureChatModel
from chat import ChatService




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

@app.get("/health")
async def health() -> dict[str, str]:
    """ """
    return {
        "status": "healthy"
    }


@app.post("/api/chat")
async def chat(body:ChatRequest):
    """
    Answer a question as a stream of SSE events (SSE), or return a JSON error

    Errors before streaming starts are JSON with a status code (400, 403, 429);
    errors after it starts arrive as an 'error' event.
    

    Note: /api/chat
        - SSE stream 
        - JSON error ~ 400, 403, 413, 429 or 503 (busy) before streaming start; error events start
    """
    # Detect language

    # allow the origin list

    # get the origin and raise an error for any failure

    # Extract question  

    # If empty question ~ return error 400

    # if question is longer than limit ~ return error 400

    # Create a chat service to return response as SSE


if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, reload=True)
