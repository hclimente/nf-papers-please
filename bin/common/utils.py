import logging
import os

from .models import Article, ArticleTable, Author


def get_common_variations(expected_values: list):
    """
    Generate common variations of expected values (case, quotes, punctuation).

    Args:
        expected_values (list): List of expected values.

    Returns:
        dict: Mapping of variations to normalized values.
    """
    d = {}

    for v in expected_values:
        d[v] = v
        d[v.lower()] = v
        d[v.upper()] = v
        d[v.capitalize()] = v
        d[v.title()] = v

    update = {}
    for k, v in d.items():
        update[f"'{k}'"] = v
        update[f'"{k}"'] = v
        update[f"{k}."] = v

    d.update(update)
    return d


def get_env_variable(var_name: str, raise_error: bool = False) -> str:
    """
    Retrieve the value of an environment variable.

    Args:
        var_name (str): The name of the environment variable.
        raise_error (bool): Whether to raise an error if the variable is not found.

    Returns:
        str: The value of the environment variable.

    Raises:
        ValueError: If the environment variable is not found and raise_error is True.
    """
    value = os.environ.get(var_name)

    if not value:
        error_msg = f"{var_name} environment variable not found."
        logging.error(f"❌ {error_msg}")
        if raise_error:
            raise ValueError(error_msg)
    return value


def article_to_text(article: Article | ArticleTable) -> str:
    """
    Prepare the text representation of an article for embedding.

    Args:
        article: The article object.

    Returns:
        str: The text representation of the article.
    """
    return f"""
Title: {article.title}
Journal: {article.journal if isinstance(article, Article) else article.journal}
First Author: {article.authors[0] if article.authors else "N/A"}
Last Author: {article.authors[-1] if article.authors else "N/A"}
Summary: {article.summary}
Tags: {", ".join(str(tag) for tag in article.tags) if article.tags else "N/A"}
"""


def prune_article_for_classification(article: Article) -> Article:
    """
    Create a pruned copy of an article with only fields needed for classification.

    Keeps: title, journal, authors (first and last only), summary, tags, doi, nearest_neighbors.
    Removes all other fields to reduce token usage in LLM prompts.
    Recursively prunes any Article objects in nearest_neighbors.

    Args:
        article: The full article object.

    Returns:
        Article: A pruned copy with only classification-relevant fields.
    """
    # Recursively prune nearest neighbors if present
    pruned_neighbors = None
    if article.nearest_neighbors:
        pruned_neighbors = [
            prune_article_for_classification(neighbor)
            for neighbor in article.nearest_neighbors
        ]

    # Keep only first and last authors if present
    pruned_authors = None
    if article.authors:
        if len(article.authors) == 1:
            pruned_authors = [article.authors[0]]
        else:
            pruned_authors = [article.authors[0], article.authors[-1]]

    return Article(
        title=article.title,
        journal=article.journal,
        journal_short_name=article.journal_short_name,
        authors=pruned_authors,
        summary=article.summary,
        tags=article.tags,
        doi=article.doi,
        url=article.url,
        date=article.date,
        access_date=article.access_date,
        raw_contents="",  # Empty string to save tokens
        nearest_neighbors=pruned_neighbors,
    )


def article_table_to_article(article_table: ArticleTable) -> Article:
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
    journal_name = str(article_table.journal.name) if article_table.journal else None
    journal_short_name = (
        str(article_table.journal.short_name)
        if (article_table.journal and article_table.journal.short_name)
        else None
    )

    return Article(
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
        relevance=str(article_table.relevance) if article_table.relevance else None,
        access_date=article_table.access_date,
        raw_contents=str(article_table.raw_contents),
        zotero_key=str(article_table.zotero_key) if article_table.zotero_key else None,
        journal=journal_name,
        journal_short_name=journal_short_name,
        authors=authors,
        tags=tags,
        embedding=article_table.embedding,
    )
