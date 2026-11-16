"""
The whole bot: greeting check --> follow-up rewrite --> search --> group --> answer

Returns: 
    - ChatService.stream() --> yield SSE event strings

    
The question-answering chain: (rewrite) -> search -> group -> answer, streamed as SSE

`ChatService.stream()` is a whole bot. It is an async generator of SSE strings, so the route in main.py only has to pass it to a StreamResponse.

"""


import asyncio
import logging
import time

from collections.abc import AsyncGenerator
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
from llm import ChatModel, AzureChatModel
from dataclasses import dataclass, field
from collections.abc import AsyncIterator
from models import ChatRequest, Lang
from sse import sse_event


logger = logging.getLogger("eaa_chat.chat")



# load environment variables
load_dotenv()


@dataclass
class ChatTrace:
    """What happened during one question. Logged once, as 'chat_completed', at the end."""

    request_id: str
    lang: str
    outcome: str = "started"    # answered / not_found / small_talk / filtered / empty / error / cancelled
    rewritten: bool = False
    passages: int = 0
    sources: int = 0
    cited: int = 0
    top_score: float | None = None
    search_ms: int = 0
    first_token_ms: int | None = None
    total_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    finish_reason: str | None = None
    question: str | None = field(default=None, repr=False) # Only when LOG_QUESTIONS = true



class ChatService:
    """
    Answers one question at a time; shared by all requests (it holds no per-request state).
    """

    def __init__(self, llm: ChatModel):
        self.llm = llm # points to the abstract protocol



    # consumes chat_stream and return tokens to the caller
    #async def stream(self, request: ChatRequest, request_id: str, lang: Lang) -> AsyncIterator[str]:
    async def stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """
        Yield the SSE events for one question (see app/sse.py for the event list)

        Never raises for expected failures: search or model errors become an 'error' event.
        
        """

        # started = time.perf_counter()
        # trace = ChatTrace(request_id=request_id, lang=lang)

        # Extract a question
        question = request.question.strip()

        parts: list[str] = []
        async for pieces in self.llm.chat_stream(user_prompt = question):
            parts.append(pieces)
            yield sse_event("delta", {"text":pieces})


async def main():

    llm = AzureChatModel()
    chat = ChatService(llm=llm) #ChatModel is a protocol, then self.llm just points to the abstract protocol
    
    req = ChatRequest(question="hello, tell me about python?")


    
    async for event in chat.stream(request=req):
        print(event)



if __name__ == "__main__":
    asyncio.run(main())