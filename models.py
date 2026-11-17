"""
First - Define Pydantic model

Data shapes shared by the API

- Create Pydantic models to validate user input data
- Handle validation errors with proper error handling
- Use optional fields and field constraints in our model
- Work with JSON data validation methods

Data Models:

- ChatRequest - ChatTurn: What the widget sends to POST /api/chat (validated by Pydantic)

"""

from pydantic import BaseModel, Field, ValidationError
from typing import Literal
import json 
from dataclasses import dataclass, field


Lang = Literal['en', 'ar']

class ChatTurn(BaseModel):
    """
    One earlier message of the conversation, sent back by the widget.
    """
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


# Validating User Input
class ChatRequest(BaseModel):
    """
    Body of POST /api/chat

    Example: {"question": "What does EAA do?", "history": []}
    """
    question: str = Field(min_length=1, max_length=2000) # Adding some constraints. The real limit is the MAX_QUESTION_CHARS
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)




@dataclass
class TokenUsage:
    """
    Token counts for one answer. The chat model fills this when the stream ends.
    """
    prompt_tokens: int = 0
    completion_tokens: int = 0  # includes reasoning tokens on reasoning model
    reasoning_tokens: int = 0
    finish_reason: str | None = None # "stop", "length" or "content filter"


# -------------------- Testing & Validation --------------------

# Create model instance
user_input = ChatRequest(
    question="What does EAA do",
    history=[]
)

print(user_input)
print(type(user_input))


# Define a function for error handling and try different inputs
def validate_user_input(input_data):
    try:
        # Create a ChatRequest model instance from user input data
        user_input = ChatRequest(**input_data) # unpacking dict into model
        print(f"✅ Valid user input created:")
        print(f"{user_input.model_dump_json(indent=2)}") # serializes a pydantic model directly into a JSON-encoded string. It converts our model data into a JSON string
        print(type(user_input.model_dump_json(indent=2)))
        return user_input

    except ValidationError as e:
        # Capture and display validation errors in a readable format
        print(f"❌ Validation error occurred:")
        for error in e.errors():
            print(f"- {error['loc'][0]}: {error['msg']}")

        return None

input_data = {
    "question": "What does EAA do", 
    "history": []
}

user_input = validate_user_input(input_data)
print(type(user_input))


# Trying with JSON data as input

# Define user input as JSON data
json_data = '''
{
    "question":"What does EAA do?",
    "history":[]
}


'''

# Parse the JSON string into a Python dictionary
input_data = json.loads(json_data)
print("Parsed JSON:", input_data)
print(type(input_data))

# We can know validate user input after parsing the JSON ~ deserialize
valid_user_input = validate_user_input(input_data)
print(f"Valid user input: {valid_user_input}")

# Best approach to parse JSON and validate user input in one step using model_validate_json method
user_input = ChatRequest.model_validate_json(json_data)
print(user_input.model_dump_json(indent=2))


# -------------------- Validation LLM responses --------------------
# Using Pydantic Models for Structured LLM Output
# Passing Pydantic model directly in our API call to an LLMs providers. This will get us more reliable and strucutre response
# Use Pydantic to get structure that we want in response
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from openai import OpenAI
import anthropic
from datetime import date
from dotenv import load_dotenv



# Define our Pydantic models for user input and LLM output

# Define the UserInput model
class UserInput(BaseModel):
    name: str
    email: EmailStr
    query: str
    order_id: Optional[int] = Field(
        None,
        description="5-digit order number (cannot start with 0)",
        ge=10000,
        le=99999
    )

    purchase_date: Optional[date] = None

# Define the CustomerQuery model that inherits from UserInput
class CustomerQuery(UserInput):
    priority: str = Field(..., description="Priority level: low, medium, high")
    category: Literal['refund_request', 'information_request', 'other'] = Field(..., description="Query category")
    is_complaint: bool = Field(..., description="Whether this is a complaint")
    tags: List[str] = Field(..., description="Relevant keyword tags")

# Define our input data as JSON string and validate it using our model
user_input_json = '''
                    {
                    "name": "joe",
                    "email": "joe@example.com",
                    "query": "I ordered a new computer monitor and it arrived with screen cracked. This is the second time this has happened. I need a replacement ASAP.",
                    "ordered_id": "12345",
                    "purchase_date": "2025-12-31"

                    }
'''

# Validate the user_input_json by creating UserInput instance
user_input = UserInput.model_validate_json(user_input_json)
print("="*60)
print(f"User input validation: {user_input}")


# Build prompt and anthropic API 
prompt = (
    f"Analyze the following customer query: {user_input}"
    f"and provide a structured response."
)


# Load environment variables
load_dotenv()

client = OpenAI()


response = client.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[{
        'role': 'user',
        'content': prompt
    }],
    response_format=CustomerQuery # applying pydantic directly to an API call
)

print("="*100)
response_content = response.choices[0].message.content
# Inspect the returned structured data
print(f"type: {type(response_content)}") # class <str>.
print("*"*100)
print(response_content) # return json string, but not guaranteed to be valid instance of our data model



# Advanced usage and inspection
# Validate the response I got from the LLM
print("^"*100)
valid_data = CustomerQuery.model_validate_json(response_content)
print(f"Type: {type(valid_data)}\n\n")
print(valid_data.model_dump_json(indent=2)) # convert Pydantic V2 model into JSON-ecoded string


# Note: LLM providers are returning a pydantic model to us as a response type. LLM providers are makking data validation in their end before sending back a response.


# Better approach -  no need validation required from our end 
response_content_2 = client.responses.parse(
    model="gpt-4o-mini",
    input=[
        {'role':'user', 'content':prompt}
    ],
    text_format=CustomerQuery
)
# check response APU call
print("#"*100)
print(f"type: {type(response_content_2.output_parsed)}") # instance of CustomerQuery model ~API return a valid data
print(response_content_2.model_dump_json(indent=2)) # OpenAI handling construction of JSON + handling data validation before response to us

# I use pydantic data directly to API calls to LLM providers
# I use Pydantic model models to validate output directly from LLM
# By defining expected output schema with Pydantic and passing directly to the API
# I can eliminate manual parsing and receive well-formatted responses in a single API call  
# I can use pydantic model on tool calling that pass to an LLM in an API call which allow LLM to give back the exact parameters I need to call the tool uses function or API

