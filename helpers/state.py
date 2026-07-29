from pydantic import BaseModel ,Field,HttpUrl
from typing import Any, Optional, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from enum import Enum
from datetime import datetime

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

class SearchSource(str,Enum):
    WEB = "web"
    NEWS = "news"
    RESEARCH = "research"
    SOCIAL = "social"

class SearchProvider(str,Enum):
    DDGS = "ddgs"
    DDGS_NEWS = "ddgs_news"
    RSS = "rss"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    OPENALEX = "openalex"
    REDDIT = "reddit"
    HACKERNEWS = "hackernews"
    GITHUB = "github"

class SearchResult(BaseModel):
    title : str
    url : HttpUrl
    snippet : str
    source : SearchSource
    provider : SearchProvider
    query : str
    published_at : datetime | None = None 

class SearchResponse(BaseModel):
    results : list[SearchResult]

class State(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(default_factory=list)
    user_request: str = ""
    plan: Plan | None = None
    search_results: list[SearchResult] = Field(default_factory=list)
    scraped_articles: list[Article] = Field(default_factory=list)
    ranked_articles: list[Article] = Field(default_factory=list)
    draft_article: str = ""
    review_comments: list[str] = Field(default_factory=list)
    review_passed: bool = False
    exports: dict[str, str] = Field(default_factory=dict)
    current_step: str = ""
    errors: list[str] = Field(default_factory=list)
