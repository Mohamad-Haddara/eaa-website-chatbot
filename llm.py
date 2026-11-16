
import asyncio


from collections.abc import AsyncGenerator
from openai import  AsyncOpenAI
from typing import Protocol
from dotenv import load_dotenv
from typing import AsyncIterator



# load environment variables
load_dotenv()


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

  

# Our implementation
# Create instnace of AzureOpenAI on the Azure portal.
# Create asynchronous AzureOpenAIChatClient to interact with the Azure OpenAI API.
# The chat client requires an API endpoint, deployment name, key, and version to function.
class AzureChatModel:
    """
    ChatModel in Microsoft Foundry
    """

    # set: api_key, api_version, azure_endpoint, azure_deployment (using os.environ)
    def __init__(self):
        self._aclient = AsyncOpenAI(
            timeout=60.0, # Maximum time to wait for a response before rasing error.
            max_retries=2 # Number of automatic retries on transit errors (408, 409, 429 rate limits, and 5xx server error)
        )


    # Define chat stream asynchronous generator method that yields each output token from the API.
    async def chat_stream(self, user_prompt, model: str = "gpt-4o-mini") -> AsyncIterator[str]:
        """
        Yield (output token) answer text as it is generated, and fill 'usage' from the last chunk.

        Raises ContentFiltered Error if the filter blocks the prompt (before any text) or stops the answer part-way (after the text so far has been yielded)
        """

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
        )

        # Loop over the stream and yield each output token or return an empty string if delta.content is empty. 
        async for chunk in stream:
            # after looping over data stream and yield token
            yield f"data: {chunk.choices[0].delta.content or ''}\n\n"

            await asyncio.sleep(0.2) # slow down the streaming rate to reduce back pressure to the client

        yield "[Done]\n\n"


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


if __name__ == "__main__":
    client = AzureChatModel()
    print(asyncio.run(client.complete(user_prompt="What is python?")))



