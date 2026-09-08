"""7.2.2 — LangChain: force the model to answer in a fixed shape.

Run from the vibe-chat folder:   python agent/demo_structured.py
"""

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config import BASE_URL, MODEL, HEADERS, API_KEY


class Destination(BaseModel):
    name: str = Field(description="Name of the place")
    city: str = Field(description="City or region")
    access: str = Field(description="How to get there from central Mumbai")
    highlight: str = Field(description="What makes it worth the trip")


prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a travel adviser for Mumbai."),
    ("human", "Suggest one place to visit within about one hour of central Mumbai."),
])

model = ChatOpenAI(base_url=BASE_URL, api_key=API_KEY, model=MODEL, temperature=0,
                   default_headers=HEADERS)
structured_model = model.with_structured_output(Destination, method="function_calling")

# Prompt -> Model -> Destination
chain = prompt | structured_model
result = chain.invoke({})

print("Place:    ", result.name)
print("City:     ", result.city)
print("Access:   ", result.access)
print("Highlight:", result.highlight)
