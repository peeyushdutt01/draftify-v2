from pydantic import BaseModel
from typing import Any, Optional, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class Article(BaseModel):
    title : str
    url : str
    content : str

class Plan(BaseModel):
    topic : str
    audience : str
    medium : str
    search_queries : list[str]
    sections : list[str]

class State(BaseModel):
    messages = Annotated[Sequence[BaseMessage],add_messages]
    user_request = str
    plan = Plan
    fetched_knowledge = list[Article]
    ranked_articles = list[Article]
    draft_article = list
    review_notes = list[str]
    review_passed = bool
    exports = dict[str,str]
    current_step = str
    errors = list[str]



