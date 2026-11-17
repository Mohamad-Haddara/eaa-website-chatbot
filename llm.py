"""
Job: Talk to the model

Input/Output: messages -> text pieces (str)

Knows about: Azure endpoint, key, deployment, retries, timeouts

- I can swap model provide from AzureOpenAI to vLLM or OpenRouter ~ changes only llm.py, and chat.py remain the same
- Testing is easier. You can test ChatService with a fake LLM, so there are no API calls and no cost.
- You can reuse the LLM class. Other services, like a summarizer, can use the same class.
- Debugging is easier. If streaming from Azure breaks, look in llm.py. If the prompt or the SSE format is wrong, look in chat.py.



"""


import asyncio


from openai import AsyncOpenAI, BadRequestError
from typing import Protocol
from dotenv import load_dotenv
from typing import AsyncIterator
from models import TokenUsage



# load environment variables
load_dotenv()


class ContentFilteredError(Exception):
    """
    Raised when the Azure content filter blocks the question or the answer.
    """

# Our Protocol (Interface)
class ChatModel(Protocol):
    """What the code needs from a model. AzureChatModel provide it."""

    async def chat_stream(self, user_prompt: str, model: str = "gpt-4o-mini") -> AsyncIterator[str]:
        """
        Yield the answers as text pieces; fill 'usage' when the stream end
        """

    async def complete(self, user_prompt: str, model: str = "gpt-4o-mini", messages: list[dict] = None, max_tokens: int = None) -> str:
        """
        Return one short completion as plain text (used to rewrite follow-up questions)
        """

    # async def close(self):
    #     """
    #     Close network connections.
    #     """



  

# Our implementation
# Create instnace of AzureOpenAI on the Azure portal.
# Create asynchronous AzureOpenAIChatClient to interact with the Azure OpenAI API.
# The chat client requires an API endpoint, deployment name, key, and version to function.
class AzureChatModel:
    """
    ChatModel in Microsoft Foundry
    """
    # Creates self._client = AsyncAzureOpenAI(...)
    # set: api_key, api_version, azure_endpoint, azure_deployment (using os.environ)
    def __init__(self):
        self._aclient = AsyncOpenAI(
            timeout=60.0, # Maximum time to wait for a response before rasing error.
            max_retries=2 # Number of automatic retries on transit errors (408, 409, 429 rate limits, and 5xx server error)
        )

        # Set deployment name, not model name (load from setting)

        # Set the max output tokens

        # Set the effort (low)

        # Set the temperature

    # Define chat stream asynchronous generator method that yields each output token from the API.
    async def chat_stream(self, user_prompt, usage: TokenUsage, model: str = "gpt-4o-mini") -> AsyncIterator[str]:
        """
        Yield (output token) answer text as it is generated, and fill 'usage' from the last chunk.

        Raises ContentFiltered Error if the filter blocks the prompt (before any text) or stops the answer part-way (after the text so far has been yielded)
        """

        try:
            stream = await self._aclient.chat.completions.create(
                messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
                ],
                model=model,
                # Set the stream = True to recieve output stream from the API instead of the full response at once
                stream=True,
                # Config parameter used during streaming requests to control how stream behaves - To append an extra, final chunk in the Server-Sent Events (SSE) stream. 
                stream_options= {"include_usage": True}
                )

        # BadRequestError ~ HTTP 400 ~ occurs when OpenAI rejects our request because the input data, parameters, or formatting do not meet requirements. (Ex: exceeding context window, invalid parameter, content policy violation)
        except BadRequestError as exc:
            raise ContentFilteredError() from exc


        try:
            # Loop over the stream and yield each output token or return an empty string if delta.content is empty. 
            async for chunk in stream:
                if chunk.usage: # only the final chunk contain usage. In final chunk the usage field contains the total token usage for the entire request (prompt tokens, completion tokens, and total tokens)
                    usage.prompt_tokens = chunk.usage.prompt_tokens
                    usage.completion_tokens = chunk.usage.completion_tokens
                    details = chunk.usage.completion_tokens_details
                    usage.reasoning_tokens = (details.reasoning_tokens or 0) if details else 0

                for choice in chunk.choices: 
                    # after looping over data stream and yield token
                    #yield f"data: {chunk.choices[0].delta.content or ''}\n\n"
                    #await asyncio.sleep(0.2) # slow down the streaming rate to reduce back pressure to the client

                    if choice.delta and choice.delta.content:
                        yield choice.delta.content

                    if choice.finish_reason:
                        usage.finish_reason = choice.finish_reason


            yield "[Done]\n\n"

        finally:
            await stream.close()

        if usage.finish_reason == "content_filter":
            raise ContentFilteredError()

    async def complete(self, user_prompt: str, model: str = "gpt-4o-mini", messages: list[dict] = None, max_tokens: int = None) -> str:
        """
        Return the text as non-streamed completion (if the model returned none).
        """

        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content':" You are a helpful assistant"
                },

                {
                    'role':'user',
                    'content': user_prompt

                }
            ]
        )        

        return response.choices[0].message.content


    async def close(self) -> None:
        """
        Close the HTTP connection pool.
        """

        await self._aclient.close()

if __name__ == "__main__":
    client = AzureChatModel()
    print(asyncio.run(client.complete(user_prompt="What is python?")))



