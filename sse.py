"""
Server-Sent Events (SSE): the streaming format between the chat API and the widget.

Each event is two lines and a blank line:

    event: delta
    data: {"text": "Education Above All"}

    
Events, in the order the API sends them:
    meta    {"request_id": str, "lang": "en" | "ar"}                        always first
    status  {"stage": "searching" | "answering"}                            progress hints
    sources {"sources": [{"n", "title", "type", "url"}, ...]}               before the answers
    delta   {"text": str}                                                   a piece of answer
    done    {"request_id": str, "answered": bool, "cited": [int, ...]}      always last on success
    error   {"code": str, "message": str}                                   replace 'done' on failure

"""


import json
from collections.abc import Mapping
from typing import Any

def sse_event(event: str, data: Mapping[str, Any]) -> str:
    """
    Return one SSE event as text, ready to write to the response.

    Example: sse_event("delta", {"text":"Hi"})  -> 'event: delta\\ndata: {"text": "Hi"}\n\n'
    json.dumps escapes newlines, so 'data' fits on one line.
    """

    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


