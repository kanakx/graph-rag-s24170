from fastapi import APIRouter
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .graph_transformer import get_llm

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[dict]


class ChatResponse(BaseModel):
    response: str


@router.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    llm = get_llm()

    langchain_messages = []
    for msg in request.messages:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))
        elif msg["role"] == "system":
            langchain_messages.append(SystemMessage(content=msg["content"]))

    response = llm.invoke(langchain_messages)
    return ChatResponse(response=response.content)
