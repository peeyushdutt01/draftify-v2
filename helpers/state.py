from pydantic import BaseModel ,Field
from typing import Any, Optional, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class Article(BaseModel):
    title: str
    url: str
    content: str


class Plan(BaseModel):
    topic: str
    audience: str
    medium: str
    search_queries: list[str]
    sections: list[str]


class State(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(default_factory=list)
    user_request: str = ""
    plan: Plan | None = None
    fetched_knowledge: list[Article] = Field(default_factory=list)
    ranked_articles: list[Article] = Field(default_factory=list)
    draft_article: str = ""
    review_notes: list[str] = Field(default_factory=list)
    review_passed: bool = False
    exports: dict[str, str] = Field(default_factory=dict)
    current_step: str = ""
    errors: list[str] = Field(default_factory=list)

