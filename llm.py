
import asyncio


from collections.abc import AsyncGenerator
from openai import  AsyncOpenAI
from typing import Protocol
from dotenv import load_dotenv



# load environment variables
load_dotenv()


# Our Protocol (Interface)
class ChatModel(Protocol):
    """What the code needs from a model. AzureChatModel provide it."""

    async def complete(self, user_prompt: str, messages: list[dict] = None, max_tokens: int = None) -> str:
        """
        Return one short completion as plain text (used to rewrite follow-up questions)
        """


# Our implementation
class AzureChatModel:
    """
    ChatModel in Microsoft Foundry
    """

    def __init__(self):
        self._client = AsyncOpenAI(
            timeout=60.0, # Maximum time to wait for a response before rasing error.
            max_retries=2 # Number of automatic retries on transit errors (408, 409, 429 rate limits, and 5xx server error)
        )


    async def complete(self, user_prompt:str, messages: list[dict] = None, max_tokens: int = None) -> str:
        """
        Return the text as non-streamed completion (if the model returned none).
        """

        response = await self._client.chat.completions.create(
            model="gpt-4o-mini",
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



