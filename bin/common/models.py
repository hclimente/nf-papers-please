from datetime import date
import re
from typing import List

from sqlmodel import Column, Field, SQLModel, Relationship

from pgvector.sqlalchemy import Vector
from pydantic import (
    BaseModel,
    field_validator,
    HttpUrl,
    TypeAdapter,
)


class ArticleAuthorLink(SQLModel, table=True):
    """Link table for many-to-many relationship between ArticleTable and Authors."""

    __tablename__ = "article_author_link"

    article_id: int = Field(default=None, foreign_key="articles.id", primary_key=True)
    author_id: int = Field(default=None, foreign_key="authors.id", primary_key=True)


class ArticleTagLink(SQLModel, table=True):
    """Link table for many-to-many relationship between ArticleTable and Tags."""

    __tablename__ = "article_tag_link"

    article_id: int = Field(default=None, foreign_key="articles.id", primary_key=True)
    tag_id: int = Field(default=None, foreign_key="tags.id", primary_key=True)


class ArticleJournalLink(SQLModel, table=True):
    """Link table for many-to-many relationship between ArticleTable and Journals."""

    __tablename__ = "article_journal_link"

    article_id: int = Field(default=None, foreign_key="articles.id", primary_key=True)
    journal_id: int = Field(default=None, foreign_key="journals.id", primary_key=True)


class ArticleBase(SQLModel):
    """Model representing a scientific article with metadata and processing results."""

    # Core metadata fields
    doi: str | None = None
    title: str | None = None
    summary: str | None = None
    url: str

    # Publication information
    volume: int | None = None
    issue: int | None = None
    date: date

    # Other metadata
    language: str | None = None

    # LLM results
    reasoning: str | None = None
    score: int | None = None

    # Raw and integration data
    access_date: date
    raw_contents: str
    zotero_key: str | None = None

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v):
        """Validate URL format using Pydantic's HttpUrl."""
        if isinstance(v, str):
            HttpUrl(v)
        return v


class ArticleTable(ArticleBase, table=True):
    """
    SQLModel for database representation of an article.
    """

    __tablename__ = "articles"

    id: int | None = Field(default=None, primary_key=True)

    journal: "JournalTable" = Relationship(
        back_populates="articles", link_model=ArticleJournalLink
    )
    authors: List["AuthorTable"] = Relationship(
        back_populates="articles", link_model=ArticleAuthorLink
    )
    tags: List["Tag"] = Relationship(
        back_populates="articles", link_model=ArticleTagLink
    )
    embedding: List[float] = Field(sa_column=Column(Vector(3072)))


class Article(ArticleBase):
    """
    Pydantic model for in-memory representation of an article.

    Adding a list["Author"] to represent authors to ArticleBase caused
    issues when ArticleBase was inherited by ArticleSQL and it couldn't map
    the type to a column type, so we define it separately.
    """

    journal_name: str
    journal_short_name: str | None = None
    authors: list["Author"] | None = None
    tags: List[str] | None = None
    embedding: List[float] | None = None


ArticleList = TypeAdapter(list[Article])


class Author(SQLModel):
    """
    Database model representing an author (individual or institutional).

    For individual authors: first_name and last_name are both provided.
    For institutional authors: only last_name is provided (first_name is None).
    """

    first_name: str | None = None
    last_name: str

    def __str__(self) -> str:
        if self.first_name:
            return f"{self.first_name} {self.last_name}"
        return self.last_name

    @property
    def is_institutional(self) -> bool:
        """Check if this is an institutional author."""
        return self.first_name is None


class AuthorTable(Author, table=True):
    """
    Database model representing an author (individual or institutional).
    """

    __tablename__ = "authors"

    id: int | None = Field(default=None, primary_key=True)
    articles: List["ArticleTable"] = Relationship(
        back_populates="authors", link_model=ArticleAuthorLink
    )


class Tag(SQLModel, table=True):
    """Model representing a tag for articles."""

    __tablename__ = "tags"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    articles: List["ArticleTable"] = Relationship(
        back_populates="tags", link_model=ArticleTagLink
    )


class JournalTable(SQLModel, table=True):
    """Model representing a journal."""

    __tablename__ = "journals"

    id: int | None = Field(default=None, primary_key=True)

    name: str = Field(index=True, unique=True)
    short_name: str | None = Field(default=None, index=True)
    articles: List["ArticleTable"] = Relationship(
        back_populates="journal", link_model=ArticleJournalLink
    )


class MetadataResponse(BaseModel):
    """Model for LLM response containing article metadata."""

    title: str
    summary: str
    url: str
    doi: str

    @field_validator("doi", mode="after")
    @classmethod
    def is_valid_doi(cls, doi: str) -> bool:
        if not re.match(r"^10\.\d{4,}/[^\s]+$", doi):
            raise ValueError(f"Invalid DOI format: {doi}")
        return doi

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v):
        """Validate URL format using Pydantic's HttpUrl."""
        if isinstance(v, str):
            HttpUrl(v)
        return v


class TaggingResponse(BaseModel):
    """Model for LLM response containing article tags."""

    doi: str
    tags: list[str]
    reasoning: str


def pprint(model: BaseModel, exclude_none: bool = True) -> str:
    """
    Pretty print a Pydantic model, list, or dict of models as JSON.

    Args:
        model (BaseModel): The Pydantic model, list, or dict to print.
        exclude_none (bool): Whether to exclude None values from output.

    Returns:
        str: JSON string representation of the model.
    """
    if isinstance(model, BaseModel):
        return model.model_dump_json(indent=2, exclude_none=exclude_none)
    elif isinstance(model, list):
        output = "[\n"
        for i, item in enumerate(model):
            output += item.model_dump_json(indent=2, exclude_none=exclude_none)
            if i < len(model) - 1:
                output += ","
            output += "\n"
        output += "]"
        return output
    elif isinstance(model, dict):
        output = "{\n"
        items = list(model.items())
        for i, (key, item) in enumerate(items):
            output += f'"{key}": ' + item.model_dump_json(
                indent=2, exclude_none=exclude_none
            )
            if i < len(items) - 1:
                output += ","
            output += "\n"
        output += "}"
        return output
    else:
        raise TypeError(
            "Input must be a Pydantic BaseModel, a list or a dict of BaseModels."
        )
