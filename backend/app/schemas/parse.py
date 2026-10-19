from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    url: str = Field(min_length=1)


class ParseResult(BaseModel):
    supported: bool
    source_url: str
    platform: str | None = None
    normalized_url: str | None = None
    title: str | None = None
    author: str | None = None
    duration: int | None = None
    thumbnail_url: str | None = None
    description: str | None = None
    error: str | None = None
