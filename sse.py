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


# Format sse
def sse_event(event: str, data: Mapping[str, Any]) -> str:
    """
    Return one SSE event as text, ready to write to the response.

    Example: sse_event("delta", {"text":"Hi"})  -> 'event: delta\\ndata: {"text": "Hi"}\n\n'
    json.dumps escapes newlines, so 'data' fits on one line.

    
    Wire format per the SSE spec: ''event: <channel>\\ndata: <json>\\n\n''
    The JSON payload carries ''content'' and ''metadata'' only -- the ''channel'' is hoisted onto the ''event:'' line
    so EventSource clients can dispatch by channel without parsing the body.

    """

    payload = json.dumps(data, ensure_ascii=False)
    
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


