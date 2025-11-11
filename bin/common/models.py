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
    priority: str | None = None

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

    def to_embedding_text(self) -> str:
        """
        Convert article to text representation optimized for embeddings and LLM context.

        Includes title, journal, first/last authors, summary, and tags in a structured format.

        Returns:
            str: Formatted text suitable for embedding or LLM prompts.
        """
        # Handle journal field (direct attribute for Article, relationship for ArticleTable)
        if isinstance(self, Article):
            journal = self.journal if self.journal else "N/A"
        else:
            journal = self.journal.name if self.journal else "N/A"

        # Handle authors
        first_author = self.authors[0] if self.authors else "N/A"
        last_author = self.authors[-1] if self.authors else "N/A"

        # Handle tags
        tags_str = ", ".join(str(tag) for tag in self.tags) if self.tags else "N/A"

        return f"""
Title: {self.title}
Journal: {journal}
First Author: {first_author}
Last Author: {last_author}
Summary: {self.summary}
Tags: {tags_str}
"""


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

    journal: str
    journal_short_name: str | None = None
    authors: list["Author"] | None = None
    tags: List[str] | None = None
    embedding: List[float] | None = None
    nearest_neighbors: list["Article"] | None = None

    @classmethod
    def from_article_table(cls, article_table: "ArticleTable") -> "Article":
        """
        Convert an ArticleTable (SQLModel database object) to an Article (Pydantic model).

        Args:
            article_table: ArticleTable instance from database query.

        Returns:
            Article: Pydantic Article instance with converted relationships.
        """
        # Convert AuthorTable objects to Author objects
        authors = None
        if article_table.authors:
            authors = [
                Author(first_name=author.first_name, last_name=author.last_name)
                for author in article_table.authors
            ]

        # Convert Tag objects to strings
        tags = None
        if article_table.tags:
            tags = [str(tag.name) for tag in article_table.tags]

        # Extract journal information
        journal_name = (
            str(article_table.journal.name) if article_table.journal else None
        )
        journal_short_name = (
            str(article_table.journal.short_name)
            if (article_table.journal and article_table.journal.short_name)
            else None
        )

        return cls(
            doi=article_table.doi,
            title=article_table.title,
            summary=article_table.summary,
            url=article_table.url,
            volume=article_table.volume,
            issue=article_table.issue,
            date=article_table.date,
            language=str(article_table.language) if article_table.language else None,
            reasoning=str(article_table.reasoning) if article_table.reasoning else None,
            score=article_table.score,
            priority=str(article_table.priority) if article_table.priority else None,
            access_date=article_table.access_date,
            raw_contents=str(article_table.raw_contents),
            zotero_key=str(article_table.zotero_key)
            if article_table.zotero_key
            else None,
            journal=journal_name,
            journal_short_name=journal_short_name,
            authors=authors,
            tags=tags,
            embedding=article_table.embedding,
        )

    def prune_for_classification(self) -> "Article":
        """
        Create a pruned copy of this article with only fields needed for classification.

        Keeps: title, journal, authors (first and last only), summary, tags, doi, nearest_neighbors.
        Removes all other fields to reduce token usage in LLM prompts.
        Recursively prunes any Article objects in nearest_neighbors.

        Returns:
            Article: A pruned copy with only classification-relevant fields.
        """
        # Recursively prune nearest neighbors if present
        pruned_neighbors = None
        if self.nearest_neighbors:
            pruned_neighbors = [
                neighbor.prune_for_classification()
                for neighbor in self.nearest_neighbors
            ]

        # Keep only first and last authors if present
        pruned_authors = None
        if self.authors:
            if len(self.authors) == 1:
                pruned_authors = [self.authors[0]]
            else:
                pruned_authors = [self.authors[0], self.authors[-1]]

        return Article(
            title=self.title,
            journal=self.journal,
            journal_short_name=self.journal_short_name,
            authors=pruned_authors,
            summary=self.summary,
            tags=self.tags,
            doi=self.doi,
            url=self.url,
            date=self.date,
            access_date=self.access_date,
            raw_contents="",  # Empty string to save tokens
            nearest_neighbors=pruned_neighbors,
        )

    @classmethod
    def from_zotero_item(cls, item: dict) -> "Article":
        """
        Convert a Zotero item to an Article (Pydantic model).

        Args:
            item: Dictionary from Zotero API (with 'data' key containing item fields).

        Returns:
            Article: Pydantic Article instance with data from Zotero item.
        """
        from datetime import date as date_type, datetime

        data = item.get("data", {})

        # Parse creators/authors
        authors = None
        creators = data.get("creators", [])
        if creators:
            authors = []
            for creator in creators:
                if creator.get("creatorType") == "author":
                    # Institutional author (has 'name' field only)
                    if "name" in creator:
                        authors.append(Author(last_name=creator["name"]))
                    # Individual author (has firstName and lastName)
                    else:
                        authors.append(
                            Author(
                                first_name=creator.get("firstName"),
                                last_name=creator.get("lastName", ""),
                            )
                        )

        # Parse date - Zotero uses ISO 8601 format (YYYY-MM-DD)
        date_str = data.get("date", "")
        try:
            # Try ISO format first (most common: YYYY-MM-DD)
            article_date = (
                datetime.fromisoformat(date_str.split("T")[0]).date()
                if date_str
                else date_type.today()
            )
        except (ValueError, TypeError):
            # Fallback: try just the year if full date fails
            try:
                year = int(date_str.split("-")[0]) if date_str else None
                article_date = date_type(year, 1, 1) if year else date_type.today()
            except (ValueError, TypeError, IndexError):
                article_date = date_type.today()

        # Parse access date - Zotero uses ISO 8601 format with time
        access_date_str = data.get("accessDate", "")
        try:
            # Access date includes time, so split on 'T' to get just date part
            access_date = (
                datetime.fromisoformat(access_date_str.split("T")[0]).date()
                if access_date_str
                else date_type.today()
            )
        except (ValueError, TypeError):
            access_date = date_type.today()

        # Parse tags
        tags = None
        zotero_tags = data.get("tags", [])
        if zotero_tags:
            tags = [tag.get("tag") for tag in zotero_tags if tag.get("tag")]

        return cls(
            title=data.get("title"),
            summary=data.get("abstractNote"),
            doi=data.get("DOI"),
            url=data.get("url", ""),
            volume=int(data["volume"]) if data.get("volume") else None,
            issue=int(data["issue"]) if data.get("issue") else None,
            date=article_date,
            language=data.get("language"),
            access_date=access_date,
            raw_contents=str(item),  # Store entire Zotero item as raw contents
            zotero_key=item.get("key"),
            journal=data.get("publicationTitle", ""),
            journal_short_name=data.get("journalAbbreviation"),
            authors=authors,
            tags=tags,
        )


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

    def __str__(self) -> str:
        return self.name


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


class ClassificationResponse(BaseModel):
    """Model for LLM response containing article classification."""

    doi: str
    priority: str
    reasoning: str

    @field_validator("priority", mode="after")
    @classmethod
    def validate_priority(cls, priority: str) -> str:
        """Validate that priority is one of the allowed values."""
        allowed_values = ["high", "medium", "low"]
        if priority not in allowed_values:
            raise ValueError(
                f"Invalid priority value: {priority}. Must be one of {allowed_values}"
            )
        return priority


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
