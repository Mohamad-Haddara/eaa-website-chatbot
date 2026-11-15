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
# Passing Pydantic model directly in our API call to an LLM providers. This will get us more reliable and strucutre response
# Use Pydantic to get structure that we want in response
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from openai import OpenAI

